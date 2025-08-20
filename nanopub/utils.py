import logging
import re
from dataclasses import asdict, dataclass
from typing import Any, Optional

from rdflib import Dataset, Namespace, URIRef

from nanopub.definitions import DUMMY_NAMESPACE, DUMMY_URI

log = logging.getLogger()


class MalformedNanopubError(ValueError):
    """Error to be raised if a Nanopub is not formed correctly."""


@dataclass
class NanopubMetadata:
    """Represents the different URIs and namespace used for a nanopub."""

    namespace: Namespace = DUMMY_NAMESPACE
    np_uri: URIRef = DUMMY_URI

    head: URIRef = DUMMY_NAMESPACE["Head"]
    assertion: URIRef = DUMMY_NAMESPACE["assertion"]
    provenance: URIRef = DUMMY_NAMESPACE["provenance"]
    pubinfo: URIRef = DUMMY_NAMESPACE["pubinfo"]

    sig_uri: URIRef = DUMMY_NAMESPACE["sig"]
    signature: Optional[str] = None
    public_key: Optional[str] = None
    algorithm: Optional[str] = None

    trusty: Optional[str] = None

    dict = asdict


def extract_np_metadata(g: Dataset) -> NanopubMetadata:
    """Extract a nanopub URI, namespace and head/assertion/prov/pubinfo contexts from a Graph"""
    get_np_query = """prefix np: <http://www.nanopub.org/nschema#>

SELECT DISTINCT ?np ?head ?assertion ?provenance ?pubinfo ?sigUri ?signature ?pubkey ?algo
WHERE {
    GRAPH ?head {
        ?np a np:Nanopublication ;
            np:hasAssertion ?assertion ;
            np:hasProvenance ?provenance ;
            np:hasPublicationInfo ?pubinfo .
    }
    GRAPH ?pubinfo {
        OPTIONAL {
            ?sigUri npx:hasSignatureTarget ?np ;
                npx:hasPublicKey ?pubkey ;
                npx:hasAlgorithm ?algo ;
                npx:hasSignature ?signature .
        }
    }
}
"""
    qres: Any = g.query(get_np_query)
    if len(qres) < 1:
        raise MalformedNanopubError(
            "\033[1mNo nanopublication\033[0m has been found in the provided RDF. "
            "It should contain a np:Nanopublication object in a Head graph, pointing to 3 graphs: assertion, provenance and pubinfo"
        )
    if len(qres) > 1:
        np_found: list = []
        for row in qres:
            np_found.append(row.np)
        raise MalformedNanopubError(
            f"\033[1mMultiple nanopublications\033[0m are defined in this graph: {', '.join(np_found)}. "
            "The Nanopub object can only handles 1 nanopublication at a time"
        )
    np_meta = NanopubMetadata()
    for row in qres:
        np_meta.head = row.head
        np_meta.assertion = row.assertion
        np_meta.provenance = row.provenance
        np_meta.pubinfo = row.pubinfo
        np_meta.np_uri = row.np
        np_meta.sig_uri = row.sigUri
        np_meta.signature = row.signature
        np_meta.public_key = row.pubkey
        np_meta.algorithm = row.algo

    # Check if the nanopub URI has a trusty artefact:
    separator_char = '/'
    # Regex to extract base URI, separator and trusty URI (if any)
    extract_trusty = re.search(r'^(.*?)(\/|#)?(RA.*)?$', str(np_meta.np_uri))
    if extract_trusty:
        base_uri = extract_trusty.group(1)
        if extract_trusty.group(2):
            separator_char = extract_trusty.group(2)
        np_meta.namespace = Namespace(base_uri + separator_char)

        if extract_trusty.group(3):
            np_meta.trusty = extract_trusty.group(3)
            # TODO: improve as the signed np namespace might be using / or # or .
            np_meta.namespace = Namespace(np_meta.np_uri + '#')

    return np_meta
