"""
This module holds code for representing the RDF of nanopublications, as well as helper functions to
sign, publish, and make handling RDF easier.
"""
import logging
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Union, Tuple

import rdflib
import requests
from rdflib import BNode, Dataset, Graph, URIRef
from rdflib import RDF, Literal
from rdflib.namespace import DC, DCTERMS, FOAF, PROV, XSD

from nanopub.definitions import (
    DEFAULT_HTTP_TIMEOUT,
    MAX_TRIPLES_PER_NANOPUB,
    NANOPUB_FETCH_FORMAT,
    TEST_NANOPUB_REGISTRY_URL,
)
from nanopub.namespaces import HYCL, KPXL_GRLC, NP, NPX, NTEMPLATE, ORCID, PAV
from nanopub.nanopub_conf import NanopubConf
from nanopub.profile import ProfileError
from nanopub.serialize import serialize_nanopub_trig
from nanopub.sign_utils import add_signature, publish_graph, verify_signature, verify_trusty
from nanopub.sparql import sparql_syntax_error
from nanopub.utils import MalformedNanopubError, NanopubMetadata, extract_np_metadata

logger = logging.getLogger(__name__)


class Nanopub:

    def __init__(
            self,
            source_uri: str = None,
            assertion: Optional[Graph] = None,
            provenance: Optional[Graph] = None,
            pubinfo: Optional[Graph] = None,
            rdf: Union[Dataset, Path] = None,
            introduces_concept: BNode = None,
            conf: Optional[NanopubConf] = None,
    ) -> None:
        """A Nanopub object, containing: the RDF that defines the nanopublication;
            configuration for formatting and publishing the nanopub; functions for validating, signing, publishing

            Attributes:
                source_uri (str): The URI of the nanopublication that this Publication represents (if applicable)
                assertion (rdflib.Graph): The part of the graph describing the assertion.
                provenance (rdflib.Graph): The part of the graph describing the provenance.
                pubinfo (rdflib.Graph): The part of the graph describing the publication information.
                rdf (rdflib.Dataset): The full RDF graph of this nanopublication (quads)
                introduces_concept (rdflib.BNode): The concept that is introduced by this Publication (if applicable)
                conf (NanopubConfig): Config for the nanopub
            """

        if assertion is None:
            assertion = Graph()
        if provenance is None:
            provenance = Graph()
        if pubinfo is None:
            pubinfo = Graph()
        if conf is None:
            conf = NanopubConf()
        self._profile = conf.profile
        self._source_uri = source_uri
        self._introduces_concept = introduces_concept
        self._concept_uri: Optional[str] = None
        self._conf = deepcopy(conf)
        self._metadata = NanopubMetadata()
        self._published = False
        if self._conf.use_test_server:
            self._conf.use_server = TEST_NANOPUB_REGISTRY_URL
        if self._conf.use_server == TEST_NANOPUB_REGISTRY_URL:
            self._conf.use_test_server = True

        self._bnode_count = 0

        # Get the nanopub RDF depending on how it is provided:
        # source URI, rdflib graph, or file
        if source_uri:
            # If source URI provided we retrieve the nanopub from the servers
            r = requests.get(
                source_uri + "." + NANOPUB_FETCH_FORMAT, timeout=DEFAULT_HTTP_TIMEOUT
            )
            if not r.ok and self._conf.use_test_server:
                nanopub_id = source_uri.rsplit("/", 1)[-1]
                uri_test = TEST_NANOPUB_REGISTRY_URL + nanopub_id
                r = requests.get(
                    uri_test + "." + NANOPUB_FETCH_FORMAT, timeout=DEFAULT_HTTP_TIMEOUT
                )
            r.raise_for_status()
            self._rdf = self._preformat_graph(Dataset())
            self._rdf.parse(data=r.text, format=NANOPUB_FETCH_FORMAT)

            self._metadata = extract_np_metadata(self._rdf)
        else:
            # if provided as rdflib graph, or file
            if isinstance(rdf, Dataset):
                logger.debug("Dataset provided by caller; making deepcopy to avoid mutating caller's store")
                self._rdf = self._preformat_graph(deepcopy(rdf))
                logger.debug("Deepcopied dataset quads: %d", sum(1 for _ in self._rdf.quads((None, None, None, None))))
                self._metadata = extract_np_metadata(self._rdf)
            elif isinstance(rdf, Path):
                self._rdf = self._preformat_graph(Dataset())
                self._rdf.parse(rdf)
                self._metadata = extract_np_metadata(self._rdf)
            elif rdf is None:
                self._rdf = self._preformat_graph(Dataset())
            else:
                raise TypeError(
                    f"The 'rdf' argument must be an rdflib Dataset or a pathlib.Path, "
                    f"but got {type(rdf).__name__}. If you have the nanopublication as a "
                    f"string (a file path or inline RDF), wrap it first: pass "
                    f"Path('your_file.trig'), or parse the RDF into a Dataset."
                )

        # Instantiate the different graph from the provided RDF (trig/nquads)
        self._head = Graph(self._rdf.store, self._metadata.head)
        self._assertion = Graph(self._rdf.store, self._metadata.assertion)
        self._provenance = Graph(self._rdf.store, self._metadata.provenance)
        self._pubinfo = Graph(self._rdf.store, self._metadata.pubinfo)

        self._check_named_graphs()

        self._assertion += assertion
        self._provenance += provenance
        self._pubinfo += pubinfo

        # Concatenate prefixes declarations from all provided graphs in the main graph
        for user_rdf in [assertion, provenance, pubinfo]:
            if user_rdf is not None:
                for prefix, namespace in user_rdf.namespaces():
                    self._rdf.bind(prefix, namespace)

        if self._metadata.trusty:
            self._source_uri = str(self._metadata.np_uri)
            # if the newly created nanopub is trusty it means was fetched or read from a file therefore we need to ensure is a valid one and not taking that for granted
            _ = self.is_valid

        # Add Head graph if the nanopub was not provided as trig/nquads
        if not rdf and not source_uri:
            self._head.add((
                self._metadata.namespace[""],
                RDF.type,
                NP.Nanopublication
            ))
            self._head.add((
                self._metadata.namespace[""],
                NP.hasAssertion,
                self._assertion.identifier,
            ))
            self._head.add((
                self._metadata.namespace[""],
                NP.hasProvenance,
                self._provenance.identifier,
            ))
            self._head.add((
                self._metadata.namespace[""],
                NP.hasPublicationInfo,
                self._pubinfo.identifier,
            ))

            # Add triples to the nanopub depending on the provided NanopuConf (e.g. creator, date)
            self._validate_nanopub_arguments(
                introduces_concept=introduces_concept,
                derived_from=self._conf.derived_from,
                assertion_attributed_to=self._conf.assertion_attributed_to,
                attribute_assertion_to_profile=self._conf.attribute_assertion_to_profile,
                # publication_attributed_to=publication_attributed_to,
            )
            self._handle_generated_at_time(
                self._conf.add_pubinfo_generated_time,
                self._conf.add_prov_generated_time
            )
            assertion_attributed_to = self._conf.assertion_attributed_to
            if self._conf.attribute_assertion_to_profile:
                assertion_attributed_to = URIRef(self.profile.agent_id)
            self._handle_assertion_attributed_to(assertion_attributed_to)
            self._handle_publication_attributed_to(
                self._conf.attribute_publication_to_profile,
                self._conf.publication_attributed_to
            )
            self._handle_derived_from(derived_from=self._conf.derived_from)

    def _preformat_graph(self, g: Dataset) -> Dataset:
        """Add a few default namespaces"""
        logger.debug("Preformat graph: incoming quads=%d", sum(1 for _ in g.quads((None, None, None, None))))
        g.bind("np", NP)
        g.bind("npx", NPX)
        g.bind("prov", PROV)
        g.bind("pav", PAV)
        g.bind("hycl", HYCL)
        g.bind("dc", DC)
        g.bind("dcterms", DCTERMS)
        g.bind("orcid", ORCID)
        g.bind("ntemplate", NTEMPLATE)
        g.bind("foaf", FOAF)
        g = self._replace_blank_nodes(g)
        logger.debug("Preformat graph: after replace_blank_nodes quads=%d",
                     sum(1 for _ in g.quads((None, None, None, None))))
        return g

    def update_from_signed(self, signed_g: Dataset) -> None:
        """Update the pub RDF to the signed one"""
        logger.info("Updating Nanopub instance from signed graph; previous np_uri=%s",
                    getattr(self._metadata, "np_uri", None))
        self._metadata = extract_np_metadata(signed_g)
        logger.info("New metadata: namespace=%s, np_uri=%s, trusty=%s", self._metadata.namespace, self._metadata.np_uri,
                    self._metadata.trusty)
        if self._metadata.trusty:
            self._source_uri = str(self._metadata.np_uri)
        # self._source_uri = self.get_source_uri_from_graph
        self._rdf = signed_g
        self._head = Graph(self._rdf.store, self._metadata.head)
        self._assertion = Graph(self._rdf.store, self._metadata.assertion)
        self._provenance = Graph(self._rdf.store, self._metadata.provenance)
        self._pubinfo = Graph(self._rdf.store, self._metadata.pubinfo)

    def sign(self) -> None:
        """Sign a Nanopub object"""
        if len(self.rdf) > MAX_TRIPLES_PER_NANOPUB:
            raise MalformedNanopubError(
                f"Nanopublication contains {len(self.rdf)} triples, which is more than the {MAX_TRIPLES_PER_NANOPUB} authorized")
        if not self._conf.profile:
            raise ProfileError("Profile not available, cannot sign the nanopub")
        if self._metadata.signature:
            raise MalformedNanopubError(f"The nanopub have already been signed: {self.source_uri}")
        self._check_ill_typed_literals()
        self._check_invalid_sparql()

        if self.is_valid:
            logger.info("Signing nanopub %s (quads=%d)", self.source_uri or "<unpublished>",
                        sum(1 for _ in self.rdf.quads((None, None, None, None))))
            logger.debug("Calling _replace_blank_nodes prior to signing (bnode_count=%d)", self._bnode_count)
            self._replace_blank_nodes(self._rdf)
            logger.debug("Calling add_signature on dataset...")
            signed_g = add_signature(self.rdf, self._conf.profile, self._metadata.namespace, self._pubinfo)
            self.update_from_signed(signed_g)
            logger.info("Nanopub signed; new source_uri=%s", self.source_uri)
        else:
            raise MalformedNanopubError("The nanopub is not valid, cannot sign it")

    def publish(self) -> Tuple[str, str, str | None]:
        """Publish a Nanopub object"""
        if not self.source_uri:
            # sign() validates the nanopub before signing it
            self.sign()
        else:
            if not self.is_valid:
                raise MalformedNanopubError("The nanopub is not valid, cannot publish it")
            self._check_ill_typed_literals()
            self._check_invalid_sparql()

        publish_graph(self.rdf, use_server=self._conf.use_server)
        logger.info(f'Published {self.source_uri} to {self._conf.use_server}')
        self.published = True

        if self._introduces_concept:
            # introduces_concept is always a blank node.
            # If a blank node with name 'step' was passed as introduces_concept, the concept will be
            # published with a URI that looks like [published nanopub URI]#step.
            self._concept_uri = f"{self.source_uri}#{str(self._introduces_concept)}"
            logger.info(f"Published concept to {self._concept_uri}")
            return self.source_uri, self._conf.use_server, self._concept_uri

        return self.source_uri, self._conf.use_server

    def update(self, publish=True) -> None:
        """Re-publish an updated Nanopub object"""
        self._pubinfo.add((
            URIRef(self.source_uri),
            NPX.supersedes,
            URIRef(self.source_uri),
        ))
        self._pubinfo.remove((
            self._metadata.sig_uri,
            None,
            None,
        ))
        self._metadata = extract_np_metadata(self._rdf)
        if publish:
            self.publish()
        else:
            self.sign()

    def serialize(self, destination: Optional[Path] = None, format: str = 'trig', **kwargs) -> Any:
        """Serialize the Nanopub, returning it as a string if no destination is given.

        TriG output lists the graphs in the conventional Head, assertion, provenance,
        pubinfo order; other formats are serialized by rdflib as-is.
        """
        if format == 'trig':
            return serialize_nanopub_trig(self._rdf, destination, metadata=self._metadata, **kwargs)
        return self._rdf.serialize(destination, format=format, **kwargs)

    def store(self, filepath: Path, format: str = 'trig') -> None:
        """Store the Nanopub object at the given path"""
        self.serialize(filepath, format=format)

    @property
    def has_valid_signature(self) -> bool:
        verify_signature(self._rdf, self.source_uri, self._metadata.namespace)
        return True

    @property
    def has_valid_trusty(self) -> bool:
        verify_trusty(self._rdf, self.source_uri, self._metadata.namespace)
        return True

    @property
    def is_valid(self) -> bool:
        """Check if a nanopublication is valid"""
        # Check if any of the graph is empty
        if len(self._head) < 1:
            raise MalformedNanopubError("The Head graph is empty")
        if len(self._assertion) < 1:
            raise MalformedNanopubError("The assertion graph is empty")
        if len(self._provenance) < 1:
            raise MalformedNanopubError("The provenance graph is empty")
        if len(self._pubinfo) < 1:
            raise MalformedNanopubError("The pubinfo graph is empty")

        # Check exactly 4 graphs
        graph_count = 0
        for c in self._rdf.contexts():
            if len(list(self._rdf.quads((None, None, None, c)))) > 0:
                graph_count += 1
        if graph_count != 4:
            raise MalformedNanopubError(
                f"\033[1mToo many graphs found\033[0m in the provided RDF: {graph_count}. A Nanopub should have only 4 graphs (Head, assertion, provenance, pubinfo)")

        found_prov = False
        for s, p, o in self._provenance:
            if str(s) == str(self._assertion.identifier):
                found_prov = True
                break
        if not found_prov:
            raise MalformedNanopubError(
                f"The provenance graph should contain at least one triple with the assertion graph URI as subject: \033[1m{self._assertion}\033[0m")

        found_pubinfo = False
        np_uri_str = str(self._metadata.np_uri)
        for s, p, o in self._pubinfo:
            if str(s) in (str(self._source_uri), str(self._metadata.namespace), np_uri_str):
                found_pubinfo = True
                break
        if not found_pubinfo:
            raise MalformedNanopubError(
                f"The pubinfo graph should contain at least one triple that has the nanopub URI as subject: \033[1m{self._source_uri}\033[0m")

        # An already signed or trusty nanopub is immutable and, if it is out there, has to
        # stay readable and verifiable, so its ill-typed literals are only reported. One that
        # is still plain is on its way to being signed, so they make it invalid right away.
        ill_typed = self.ill_typed_literals
        if ill_typed:
            if self._metadata.signature or self._metadata.trusty:
                logger.warning(
                    "Ill-typed literal(s) found in %s: %s. The lexical form of a literal must be "
                    "valid for its datatype; this nanopub may be missing from strict RDF stores",
                    self._source_uri or self._metadata.np_uri,
                    ", ".join(o.n3() for o, _ in ill_typed),
                )
            else:
                self._check_ill_typed_literals()

        # Same for a grlc query whose SPARQL does not parse: it can never run, and a
        # nanopub cannot be corrected after the fact, so only a new one can fix it.
        invalid_sparql = self.invalid_sparql
        if invalid_sparql:
            if self._metadata.signature or self._metadata.trusty:
                logger.warning(
                    "Invalid SPARQL found in %s: %s. This grlc query cannot be run, and "
                    "the only remedy is publishing a corrected version",
                    self._source_uri or self._metadata.np_uri,
                    "; ".join(description for _, _, description in invalid_sparql),
                )
            else:
                self._check_invalid_sparql()

        if self._metadata.signature:
            if not self.has_valid_signature:
                raise MalformedNanopubError("The nanopub is not valid")
        if self._metadata.trusty:
            if not self.has_valid_trusty:
                raise MalformedNanopubError("The trusty nanopub is not valid")
        return True

    @property
    def ill_typed_literals(self) -> List[Tuple[Literal, URIRef]]:
        """The literals whose lexical form is not valid for their declared datatype.

        Returns a list of ``(literal, graph)`` pairs, empty when the nanopub is fine.
        Literals without a datatype, with a language tag, or with a datatype rdflib does
        not recognize cannot be checked and are never reported.
        """
        return [
            (o, c)
            for s, p, o, c in self._rdf.quads((None, None, None, None))
            if isinstance(o, Literal) and o.ill_typed
        ]

    @property
    def invalid_sparql(self) -> List[Tuple[Literal, URIRef, str]]:
        """The grlc queries carried by this nanopub whose SPARQL does not parse.

        Returns a list of ``(literal, graph, description)`` triples, empty when the
        nanopub carries no grlc query or every query it carries parses. Which literal
        holds a query is knowable from the statement that carries it: the predicate is
        ``https://w3id.org/kpxl/grlc/sparql``.
        """
        found = []
        for _, _, o, c in self._rdf.quads((None, KPXL_GRLC.sparql, None, None)):
            if not isinstance(o, Literal):
                continue
            description = sparql_syntax_error(str(o))
            if description:
                found.append((o, c, description))
        return found

    @property
    def rdf(self) -> Dataset:
        return self._rdf

    @property
    def head(self):
        return self._head

    @property
    def assertion(self):
        return self._assertion

    @property
    def provenance(self):
        return self._provenance

    @property
    def pubinfo(self):
        return self._pubinfo

    @property
    def metadata(self):
        return self._metadata

    @property
    def conf(self):
        return self._conf

    @conf.setter
    def conf(self, value):
        self._conf = value

    @property
    def source_uri(self):
        if self._source_uri:
            return self._source_uri
        else:
            return self.get_source_uri_from_graph

    @source_uri.setter
    def source_uri(self, value):
        self._source_uri = value

    @property
    def published(self):
        return self._published

    @published.setter
    def published(self, value):
        self._published = value

    @property
    def concept_uri(self):
        return self._concept_uri

    @concept_uri.setter
    def concept_uri(self, value):
        self._concept_uri = value

    @property
    def profile(self):
        return self._profile

    @profile.setter
    def profile(self, value):
        self._profile = value

    @property
    def namespace(self):
        return self._metadata.namespace

    @property
    def introduces_concept(self):
        concepts_introduced = list()
        for s, p, o in self._pubinfo.triples((None, NPX.introduces, None)):
            concepts_introduced.append(o)

        if len(concepts_introduced) == 0:
            return None
        elif len(concepts_introduced) == 1:
            return concepts_introduced[0]
        else:
            raise MalformedNanopubError("Nanopub introduces multiple concepts")

    @property
    def get_source_uri_from_graph(self) -> Optional[str]:
        """Get the source URI of the nanopublication from the header.

        This is usually something like: http://purl.org/np/RAnksi2yDP7jpe7F6BwWCpMOmzBEcUImkAKUeKEY_2Yus
        """
        for s, _, _, _ in self._rdf.quads((None, RDF.type, NP.Nanopublication, None)):
            extract_trusty = re.search(
                r'^[a-z0-9+.-]+:\/\/[a-zA-Z0-9\/._-]+\/(RA.*)$',
                str(s),
                re.IGNORECASE
            )
            if extract_trusty:
                return str(s)
        return None

    @property
    def signed_with_public_key(self) -> Optional[str]:
        np_pubkey = [o for _, _, o, _ in self._rdf.quads((self.namespace.sig, NPX.hasPublicKey, None, None))]
        if np_pubkey:
            return str(np_pubkey[0])
        return None

    @property
    def is_test_publication(self) -> bool:
        return self._conf.use_test_server

    def __str__(self) -> str:
        s = ""
        if self._source_uri:
            s += f"Nanopub URI: \033[1m{self._source_uri}\033[0m\n"
        s += self.serialize(format='trig')
        return s

    def _handle_generated_at_time(
            self, add_pubinfo_generated_time: bool, add_prov_generated_time: bool
    ) -> None:
        """Handler for `Nanopub` constructor."""
        creation_time = Literal(datetime.now().astimezone(), datatype=XSD.dateTime)
        if add_pubinfo_generated_time:
            self._pubinfo.add(
                (self._metadata.namespace[""], PROV.generatedAtTime, creation_time)
            )
        if add_prov_generated_time:
            self._provenance.add(
                (
                    self._assertion.identifier,
                    PROV.generatedAtTime,
                    creation_time,
                )
            )

    def _handle_assertion_attributed_to(self, assertion_attributed_to: Optional[str]) -> None:
        """Handler for `Nanopub` constructor."""
        if assertion_attributed_to:
            assertion_attributed_to = URIRef(assertion_attributed_to)
            self._provenance.add(
                (
                    self._assertion.identifier,
                    PROV.wasAttributedTo,
                    assertion_attributed_to,
                )
            )

    def _handle_publication_attributed_to(
            self,
            attribute_publication_to_profile: bool,
            publication_attributed_to: Optional[str],
    ) -> None:
        """Handler for `Nanopub` constructor."""
        if attribute_publication_to_profile:
            if not self._profile:
                raise MalformedNanopubError(
                    "No nanopub profile provided, but attribute_publication_to_profile is enabled")
            if publication_attributed_to is None:
                publication_attributed_to = URIRef(self._profile.agent_id)
            else:
                publication_attributed_to = URIRef(publication_attributed_to)
            self._pubinfo.add(
                (
                    self._metadata.namespace[""],
                    PROV.wasAttributedTo,
                    publication_attributed_to,
                )
            )

    def _handle_derived_from(self, derived_from: Optional[str]):
        """Handler for `Nanopub` constructor."""
        if derived_from:
            if isinstance(derived_from, list):
                list_of_uris = derived_from
            else:
                list_of_uris = [derived_from]

            for derived_from_uri in list_of_uris:
                derived_from_uri = URIRef(derived_from_uri)
                self._provenance.add((
                    self._assertion.identifier,
                    PROV.wasDerivedFrom,
                    derived_from_uri,
                ))

    def _handle_introduces_concept(self, introduces_concept: Union[BNode, URIRef]):
        """Handler for `Nanopub` constructor."""
        if introduces_concept:
            introduces_concept = self._metadata.namespace[str(introduces_concept)]
            self._pubinfo.add(
                (self._metadata.namespace[""], NPX.introduces, introduces_concept)
            )

    def _validate_nanopub_arguments(
            self,
            derived_from: Optional[str],
            assertion_attributed_to: Optional[str],
            attribute_assertion_to_profile: bool,
            introduces_concept: Optional[BNode],
    ) -> None:
        """
        Validate arguments method.
        """
        if assertion_attributed_to and attribute_assertion_to_profile:
            raise MalformedNanopubError(
                "If you pass a URI for the assertion_attributed_to argument, you cannot pass "
                "attribute_assertion_to_profile=True, because the assertion will already be "
                "attributed to the value passed in assertion_attributed_to argument. Set "
                "attribute_assertion_to_profile=False or do not pass the assertion_attributed_to "
                "argument."
            )

        if introduces_concept and not isinstance(introduces_concept, BNode):
            raise MalformedNanopubError(
                "If you want a nanopublication to introduce a concept, you need to "
                'pass it as an rdflib.term.BNode("concept_name"). This will make '
                "sure it is referred to from the nanopublication uri namespace upon "
                "publishing."
            )

        if self._provenance:
            if (
                    derived_from
                    and (None, PROV.wasDerivedFrom, None) in self._provenance
            ):
                raise MalformedNanopubError(
                    "The provenance_rdf that you passed already contains the "
                    "prov:wasDerivedFrom predicate, so you cannot also use the "
                    "derived_from argument"
                )
            if (
                    assertion_attributed_to
                    and (None, PROV.wasAttributedTo, None) in self._provenance
            ):
                raise MalformedNanopubError(
                    "The provenance_rdf that you passed already contains the "
                    "prov:wasAttributedTo predicate, so you cannot also use the "
                    "assertion_attributed_to argument"
                )
            if (
                    attribute_assertion_to_profile
                    and (None, PROV.wasAttributedTo, None) in self._provenance
            ):
                raise MalformedNanopubError(
                    "The provenance_rdf that you passed already contains the "
                    "prov:wasAttributedTo predicate, so you cannot also use the "
                    "attribute_assertion_to_profile argument"
                )
        if self._pubinfo:
            if (
                    introduces_concept
                    and (None, NPX.introduces, None) in self._pubinfo
            ):
                raise MalformedNanopubError(
                    "The pubinfo_rdf that you passed already contains the "
                    "npx:introduces predicate, so you cannot also use the "
                    "introduces_concept argument"
                )

    def _replace_blank_nodes(self, g: Dataset) -> Dataset:
        """Replace blank nodes.
          Replace any blank nodes in the supplied RDF with a corresponding uri in the
        dummy_namespace.'Blank nodes' here refers specifically to rdflib.term.BNode objects. When
        publishing, the dummy_namespace is replaced with the URI of the actual nanopublication.
          For example, if the nanopub's URI is www.purl.org/ABC123 then the blank node will be
        replaced with a concrete URIRef of the form www.purl.org/ABC123#blanknodename where
        'blanknodename' is the name of the rdflib.term.BNode object.
          This is to solve the problem that a user may wish to use the nanopublication to introduce
        a new concept. This new concept needs its own URI (it cannot simply be given the
        nanopublication's URI), but it should still lie within the space of the nanopub.
        Furthermore, the URI the nanopub is published to is not known ahead of time.
        """
        bnode_map: dict = {}
        for s, p, o, c in g.quads(None):
            if isinstance(s, BNode):
                g.remove((s, p, o, c))
                if str(s) not in bnode_map:
                    if re.match(r'^[Na-zA-Z0-9]{33}$', str(s)):
                        # Unnamed BNode looks like N2c21867a547345d9b8a203a7c1cd7e0c
                        self._bnode_count += 1
                        bnode_map[str(s)] = self._bnode_count
                    else:
                        bnode_map[str(s)] = str(s)
                s = self._metadata.namespace[f"_{bnode_map[str(s)]}"]
                g.add((s, p, o, c))

            if isinstance(o, BNode):
                g.remove((s, p, o, c))
                if str(o) not in bnode_map:
                    # if str(o).startswith("N") and len(str(o)) == 33:
                    if re.match(r'^[Na-zA-Z0-9]{33}$', str(o)):
                        self._bnode_count += 1
                        bnode_map[str(o)] = self._bnode_count
                    else:
                        bnode_map[str(o)] = str(o)
                old_o = o
                o = self._metadata.namespace[f"_{bnode_map[str(o)]}"]

                g.add((s, p, o, c))
                logger.debug("Replaced object BNode %s -> %s (graph=%s, subj=%s, pred=%s)", old_o, o, c, s, p)
        logger.debug("Blank node mapping: %s", bnode_map)
        return g

    def _check_ill_typed_literals(self) -> None:
        """Refuses an ill-typed literal in a nanopub that is not signed yet.

        Such literals (e.g. ``"not-a-number"^^xsd:integer``) are accepted by rdflib, but
        strict RDF stores reject the whole nanopub, so it would end up published yet
        invisible in the SPARQL endpoint.
        """
        ill_typed = self.ill_typed_literals
        if ill_typed:
            details = ", ".join(f"{o.n3()} in graph {c}" for o, c in ill_typed)
            raise MalformedNanopubError(
                f"\033[1mIll-typed literal(s) found\033[0m: {details}. "
                "The lexical form of a literal must be valid for its datatype"
            )

    def _check_invalid_sparql(self) -> None:
        """Refuses a grlc query whose SPARQL does not parse.

        A nanopub cannot be edited after the fact, so such a query is broken permanently:
        it can never run, and the only remedy is publishing a corrected version.
        """
        invalid = self.invalid_sparql
        if invalid:
            details = "; ".join(
                f"{description} (in graph {c})" for _, c, description in invalid
            )
            raise MalformedNanopubError(
                f"\033[1mInvalid SPARQL found\033[0m in the grlc query of this "
                f"nanopub: {details}"
            )

    def _check_named_graphs(self) -> None:
        """Ensures that names graphs are not using the same URI, and that they have the nanopub namespace as base URI"""
        identifiers = [str(g.identifier) for g in (
            self._head,
            self._assertion,
            self._provenance,
            self._pubinfo,
        )]

        if len(identifiers) != len(set(identifiers)):
            raise MalformedNanopubError(
                f"All four nanopub graphs must have distinct identifiers; found {identifiers}"
            )

        for g in (
                self._head,
                self._assertion,
                self._provenance,
                self._pubinfo,
        ):
            gid = str(g.identifier)
            if not gid.startswith(self.namespace):
                raise MalformedNanopubError(
                    f"The graph identifier must start with '{self.namespace}'; found {gid}"
                )
