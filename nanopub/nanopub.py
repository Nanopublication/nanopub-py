"""
This module holds code for representing the RDF of nanopublications, as well as helper functions to
make handling RDF easier.
"""
import re
import warnings
from datetime import datetime
from typing import List, Optional, Union

import rdflib
from rdflib import BNode, ConjunctiveGraph, Graph, Namespace, URIRef
from rdflib.namespace import DC, DCTERMS, FOAF, PROV, RDF, XSD

from nanopub.config import NanopubConfig
from nanopub.definitions import DUMMY_NAMESPACE, DUMMY_NANOPUB_URI, MAX_TRIPLES_PER_NANOPUB, NANOPUB_TEST_SERVER, log
from nanopub.namespaces import HYCL, NP, NPX, NTEMPLATE, ORCID, PAV
from nanopub.signer import add_signature, publish_graph


class Nanopub:
    """
    Representation of the rdf that comprises a nanopublication

    Attributes:
        rdf (rdflib.ConjunctiveGraph): The full RDF graph of this nanopublication
        assertion (rdflib.Graph): The part of the graph describing the assertion.
        pubinfo (rdflib.Graph): The part of the graph describing the publication information.
        provenance (rdflib.Graph): The part of the graph describing the provenance.
        source_uri (str): The URI of the nanopublication that this Publication represents (if applicable)
        introduces_concept (rdflib.BNode): The concept that is introduced by this Publication.
        signed_with_public_key: The public key that this Publication is signed with.
        is_test_publication: Whether this is a test publication
        profile (Profile): Nanopub profile of the user
        config (NanopubConfig): Config for the nanopub
    """

    def __init__(
        self,
        # *args,
        assertion: Graph = Graph(),
        provenance: Graph = Graph(),
        pubinfo: Graph = Graph(),
        rdf: ConjunctiveGraph = None,
        source_uri: str = None,
        introduces_concept: BNode = None,
        config: NanopubConfig = NanopubConfig(),
        # **kwargs
    ) -> None:
        # print(config.profile)
        self._profile = config.profile
        self._source_uri = source_uri
        self._concept_uri = None
        self._config = config
        self._published = False
        self._dummy_namespace = DUMMY_NAMESPACE

        # TODO: extract dummy namespace from given RDF
        if rdf:
            self.extract_dummy_namespace(rdf)

        if self._config.use_test_server:
            self._config.use_server = NANOPUB_TEST_SERVER

        if rdf:
            self._rdf = self._preformat_graph(rdf)
        else:
            self._rdf = self._preformat_graph(ConjunctiveGraph())

        # print(self._dummy_namespace)
        # print(self._rdf.serialize(format='trig'))

        self.head = Graph(self._rdf.store, self._dummy_namespace.Head)
        self.assertion = Graph(self._rdf.store, self._dummy_namespace.assertion)
        self.provenance = Graph(self._rdf.store, self._dummy_namespace.provenance)
        self.pubinfo = Graph(self._rdf.store, self._dummy_namespace.pubinfo)

        self.head.add((self._dummy_namespace[""], RDF.type, NP.Nanopublication))
        self.head.add(
            (self._dummy_namespace[""], NP.hasAssertion, self._dummy_namespace.assertion)
        )
        self.head.add(
            (
                self._dummy_namespace[""],
                NP.hasProvenance,
                self._dummy_namespace.provenance,
            )
        )
        self.head.add(
            (
                self._dummy_namespace[""],
                NP.hasPublicationInfo,
                self._dummy_namespace.pubinfo,
            )
        )

        self.assertion += assertion
        self.provenance += provenance
        self.pubinfo += pubinfo

        self._validate_from_assertion_arguments(
            introduces_concept=introduces_concept,
            derived_from=self._config.derived_from,
            assertion_attributed_to=self._config.assertion_attributed_to,
            attribute_assertion_to_profile=self._config.attribute_assertion_to_profile,
            # publication_attributed_to=publication_attributed_to,
        )
        self._handle_generated_at_time(
            self._config.add_pubinfo_generated_time,
            self._config.add_prov_generated_time
        )
        assertion_attributed_to = self._config.assertion_attributed_to
        if self._config.attribute_assertion_to_profile:
            assertion_attributed_to = rdflib.URIRef(self.profile.orcid_id)
        self._handle_assertion_attributed_to(assertion_attributed_to)
        self._handle_publication_attributed_to(
            self._config.attribute_publication_to_profile,
            self._config.publication_attributed_to
        )
        self._handle_derived_from(derived_from=self._config.derived_from)

        # Concatenate prefixes declarations from all provided graphs in the main graph
        for user_rdf in [assertion, provenance, pubinfo]:
            if user_rdf is not None:
                for prefix, namespace in user_rdf.namespaces():
                    self._rdf.bind(prefix, namespace)
                # cls._replace_blank_nodes(rdf=user_rdf)

        # Extract the Head, pubinfo, provenance and assertion graphs from the assigned nanopub rdf
        # self._graphs = {}
        # for c in rdf.contexts():
        #     graphid = urldefrag(c.identifier).fragment.lower()
        #     self._graphs[graphid] = c
        # Check all four expected graphs are provided
        # expected_graphs = ["head", "pubinfo", "provenance", "assertion"]
        # for expected in expected_graphs:
        #     if expected not in self._graphs.keys():
        #         raise ValueError(
        #             f"Expected to find {expected} graph in nanopub rdf, "
        #             f"but not found. Graphs found: {list(self._graphs.keys())}."
        #         )

    def extract_dummy_namespace(self, g: ConjunctiveGraph) -> str:
        np_contexts = ['head', 'assertion', 'provenance', 'pubinfo']
        dummy_uri = None
        dummy_separator = None
        found_contexts: List[str] = []
        for c in g.contexts():
            extract_fragment = re.search(r'^(.*)(\/|#)(.*)$', str(c.identifier), re.IGNORECASE)
            if extract_fragment:
                base_uri = extract_fragment.group(1)
                separator_char = extract_fragment.group(2)
                fragment = extract_fragment.group(3)
                if dummy_uri and dummy_uri != base_uri:
                    raise ValueError(f"2 Nanopublications are defined in this graph: {dummy_uri} and {base_uri}"
                        "This tool only handles 1 nanopublication at a time")
                if fragment.lower() in np_contexts:
                    dummy_uri = base_uri
                    dummy_separator = separator_char
                    found_contexts.append(fragment)
        if dummy_uri and dummy_separator:
            self._dummy_namespace = Namespace(dummy_uri + dummy_separator)
        elif len(g) > 1:
            log.warn("No contexts related to nanopublications have been found in the RDF provided (head, assertion, provenance, pubinfo)")


    def _preformat_graph(self, g: ConjunctiveGraph) -> ConjunctiveGraph:
        """Add a few default namespaces"""
        # Add default namespaces
        g.bind("", None, replace=True)
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
        print(g.serialize(format='trig'))
        # g = self._replace_blank_nodes(g)
        return g


    def _replace_blank_nodes(self, rdf: ConjunctiveGraph) -> ConjunctiveGraph:
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
        for s, p, o in rdf:
            if isinstance(s, BNode):
                rdf.remove((s, p, o))
                s = self._dummy_namespace[str(s)]
                rdf.add((s, p, o))
            if isinstance(o, BNode):
                rdf.remove((s, p, o))
                o = self._dummy_namespace[str(o)]
                rdf.add((s, p, o))
        return rdf


    def _validate_from_assertion_arguments(
        self,
        derived_from: Optional[str],
        assertion_attributed_to: Optional[str],
        attribute_assertion_to_profile: bool,
        introduces_concept: Optional[BNode],
        # publication_attributed_to,
    ) -> None:
        """
        Validate arguments for `from_assertion` method.
        """
        if assertion_attributed_to and attribute_assertion_to_profile:
            raise ValueError(
                "If you pass a URI for the assertion_attributed_to argument, you cannot pass "
                "attribute_assertion_to_profile=True, because the assertion will already be "
                "attributed to the value passed in assertion_attributed_to argument. Set "
                "attribute_assertion_to_profile=False or do not pass the assertion_attributed_to "
                "argument."
            )

        if introduces_concept and not isinstance(introduces_concept, BNode):
            raise ValueError(
                "If you want a nanopublication to introduce a concept, you need to "
                'pass it as an rdflib.term.BNode("concept_name"). This will make '
                "sure it is referred to from the nanopublication uri namespace upon "
                "publishing."
            )

        if self.provenance:
            if (
                derived_from
                and (None, PROV.wasDerivedFrom, None) in self.provenance
            ):
                raise ValueError(
                    "The provenance_rdf that you passed already contains the "
                    "prov:wasDerivedFrom predicate, so you cannot also use the "
                    "derived_from argument"
                )
            if (
                assertion_attributed_to
                and (None, PROV.wasAttributedTo, None) in self.provenance
            ):
                raise ValueError(
                    "The provenance_rdf that you passed already contains the "
                    "prov:wasAttributedTo predicate, so you cannot also use the "
                    "assertion_attributed_to argument"
                )
            if (
                attribute_assertion_to_profile
                and (None, PROV.wasAttributedTo, None) in self.provenance
            ):
                raise ValueError(
                    "The provenance_rdf that you passed already contains the "
                    "prov:wasAttributedTo predicate, so you cannot also use the "
                    "attribute_assertion_to_profile argument"
                )
        if self.pubinfo:
            if (
                introduces_concept
                and (None, NPX.introduces, None) in self.pubinfo
            ):
                raise ValueError(
                    "The pubinfo_rdf that you passed already contains the "
                    "npx:introduces predicate, so you cannot also use the "
                    "introduces_concept argument"
                )
            if (None, PROV.wasAttributedTo, None) in self.pubinfo:
                raise ValueError(
                    "The pubinfo_rdf that you passed should not contain the "
                    "prov:wasAttributedTo predicate. If you wish to change "
                    "who the publication is attributed to, please use the "
                    "publication_attributed_to argument instead. By default "
                    "this is the ORCID set in your profile, but you can set "
                    "it to another URI if desired."
                )



    def _handle_generated_at_time(
        self, add_pubinfo_generated_time: bool, add_prov_generated_time: bool
    ) -> None:
        """Handler for `from_assertion` method."""
        creationtime = rdflib.Literal(datetime.now(), datatype=XSD.dateTime)
        if add_pubinfo_generated_time:
            self.pubinfo.add(
                (self._dummy_namespace[""], PROV.generatedAtTime, creationtime)
            )
        if add_prov_generated_time:
            self.provenance.add(
                (
                    self._dummy_namespace.assertion,
                    PROV.generatedAtTime,
                    creationtime,
                )
            )


    def _handle_assertion_attributed_to(self, assertion_attributed_to: Optional[str]) -> None:
        """Handler for `from_assertion` method."""
        if assertion_attributed_to:
            assertion_attributed_to = URIRef(assertion_attributed_to)
            self.provenance.add(
                (
                    self._dummy_namespace.assertion,
                    PROV.wasAttributedTo,
                    assertion_attributed_to,
                )
            )


    def _handle_publication_attributed_to(
        self,
        attribute_publication_to_profile: bool,
        publication_attributed_to: Optional[str],
    ) -> None:
        """Handler for `from_assertion` method."""
        if attribute_publication_to_profile:
            if not self._profile:
                raise ValueError("No nanopub profile provided, but attribute_publication_to_profile is enabled")
            if publication_attributed_to is None:
                publication_attributed_to = rdflib.URIRef(self._profile.orcid_id)
            else:
                publication_attributed_to = rdflib.URIRef(publication_attributed_to)
            self.pubinfo.add(
                (
                    self._dummy_namespace[""],
                    PROV.wasAttributedTo,
                    publication_attributed_to,
                )
            )


    def _handle_derived_from(self, derived_from: Optional[str]):
        """Handler for `from_assertion` method."""
        if derived_from:
            if isinstance(derived_from, list):
                list_of_uris = derived_from
            else:
                list_of_uris = [derived_from]

            for derived_from_uri in list_of_uris:
                derived_from_uri = rdflib.URIRef(derived_from_uri)
                self.provenance.add(
                    (
                        self._dummy_namespace.assertion,
                        PROV.wasDerivedFrom,
                        derived_from_uri,
                    )
                )


    def _handle_introduces_concept(self, introduces_concept: Union[BNode, URIRef]):
        """Handler for `from_assertion` method."""
        if introduces_concept:
            introduces_concept = self._dummy_namespace[str(introduces_concept)]
            self.pubinfo.add(
                (self._dummy_namespace[""], NPX.introduces, introduces_concept)
            )


    def update_from_signed(self, signed_g: ConjunctiveGraph) -> None:
        """Update the pub RDF to the signed one"""
        self._rdf = signed_g
        self._source_uri = self.get_source_uri_from_graph
        self.head = Graph(self._rdf.store, self._dummy_namespace.Head)
        self.assertion = Graph(self._rdf.store, self._dummy_namespace.assertion)
        self.provenance = Graph(self._rdf.store, self._dummy_namespace.provenance)
        self.pubinfo = Graph(self._rdf.store, self._dummy_namespace.pubinfo)



    def sign(self) -> None:
        """Sign a Nanopub object.

        Sign Publication object. It uses nanopub_java commandline tool to sign
        the nanopublication RDF with the RSA key in the profile and then publish.

        Args:
            np: Publication object to sign.

        Returns:
            dict of str: Publication info with: 'nanopub_uri': the URI of the signed
            nanopublication, 'concept_uri': the URI of the introduced concept (if applicable)
        """
        if len(self.rdf) > MAX_TRIPLES_PER_NANOPUB:
            raise ValueError(f"Nanopublication contains {len(self.rdf)} triples, which is more than the {MAX_TRIPLES_PER_NANOPUB} authorized")
        if not self._config.profile:
            raise ValueError("Profile not available, cannot sign the nanopub")

        # Sign the nanopub
        signed_g = add_signature(self.rdf, self._config.profile, self._dummy_namespace)
        self.update_from_signed(signed_g)
        log.info(f"Signed {self.source_uri}")


    def publish(self) -> None:
        """Publish a Nanopub object.

        Publish Publication object to the nanopub server. It uses nanopub_java commandline tool to
        sign the nanopublication RDF with the RSA key in the profile and then publish.

        Args:
            publication (Publication): Publication object to publish.

        Returns:
            dict of str: Publication info with: 'nanopub_uri': the URI of the published
            nanopublication, 'concept_uri': the URI of the introduced concept (if applicable)

        """
        if not self.source_uri:
            self.sign()

        publish_graph(self.rdf, use_server=self._config.use_server)

        if self.introduces_concept:
            concept_uri = str(self.introduces_concept)
            # Replace the DUMMY_NANOPUB_URI with the actually published nanopub uri. This is
            # necessary if a blank node was passed as introduces_concept. In that case the
            # Nanopub.from_assertion method replaces the blank node with the base nanopub's URI
            # and appends a fragment, given by the 'name' of the blank node. For example, if a
            # blank node with name 'step' was passed as introduces_concept, the concept will be
            # published with a URI that looks like [published nanopub URI]#step.
            concept_uri = concept_uri.replace(
                DUMMY_NANOPUB_URI, self.source_uri
            )
            self.concept_uri = concept_uri
            log.info(f"Published concept to {concept_uri}")


    @property
    def rdf(self) -> ConjunctiveGraph:
        return self._rdf

    # @property
    # def assertion(self):
    #     return self._assertion

    # @property
    # def pubinfo(self):
    #     return self._pubinfo

    # @property
    # def provenance(self):
    #     return self._provenance

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        self._config = value

    @property
    def source_uri(self):
        return self._source_uri

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
    def introduces_concept(self):
        concepts_introduced = list()
        for s, p, o in self.pubinfo.triples((None, NPX.introduces, None)):
            concepts_introduced.append(o)

        if len(concepts_introduced) == 0:
            return None
        elif len(concepts_introduced) == 1:
            return concepts_introduced[0]
        else:
            raise ValueError("Nanopub introduces multiple concepts")

    @property
    def get_source_uri_from_graph(self) -> str:
        """Get the source URI of the nanopublication from the header.

        This is usually something like:
        http://purl.org/np/RAnksi2yDP7jpe7F6BwWCpMOmzBEcUImkAKUeKEY_2Yus
        """
        return str(list(
            self._rdf.subjects(
                predicate=rdflib.RDF.type, object=NP.Nanopublication
            )
        )[0])

    @property
    def signed_with_public_key(self) -> Optional[str]:
        if not self._source_uri:
            return None
        public_keys = list(
            self._rdf.objects(URIRef(self.get_source_uri_from_graph + "#sig"), NPX.hasPublicKey)
        )
        if len(public_keys) > 0:
            public_key = str(public_keys[0])
            if len(public_keys) > 1:
                warnings.warn(
                    f"Nanopublication is signed with multiple public keys, we will use "
                    f"this one: {public_key}"
                )
            return public_key
        else:
            return None

    @property
    def is_test_publication(self) -> bool:
        if self._source_uri is None:
            return True
        else:
            return False


    def __str__(self) -> str:
        s = f"Original source URI = {self._source_uri}\n"
        s += self._rdf.serialize(format="trig")
        return s

    # @property
    # def signed_file_rdf(self) -> ConjunctiveGraph:
    #     if not self.signed_file:
    #         raise ValueError("No signed file available for this Nanopublication")
    #     g = ConjunctiveGraph()
    #     g.parse(self.signed_file, format="trig")
    #     return g


def replace_in_rdf(rdf: Graph, oldvalue, newvalue):
    """Replace values in RDF.

    Replace all subjects or objects matching `oldvalue` with `newvalue`. Replaces in place.

    Args:
        rdf (rdflib.Graph): The RDF graph in which we want to replace nodes
        oldvalue: The value to be replaced
        newvalue: The value to replace with
    """
    for s, p, o in rdf:
        if s == oldvalue:
            rdf.remove((s, p, o))
            rdf.add((newvalue, p, o))
        elif o == oldvalue:
            rdf.remove((s, p, o))
            rdf.add((s, p, newvalue))
