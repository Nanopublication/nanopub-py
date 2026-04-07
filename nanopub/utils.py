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

        np_uri_str = str(np_meta.np_uri)
        if np_uri_str.endswith(("#", "/")):
            default_separator_char = np_uri_str[-1]
        else:
            # Determine separator from the character immediately after the trusty
            # code in the head graph URI (handles non-standard names like _head).
            # Extract trusty code from np_uri first to avoid greedy regex matching
            # the local suffix (e.g. "130_head") as part of the trusty code.
            extract_trusty_pre = re.search(r'^(.*?)([/#])?(RA[A-Za-z0-9_\-]+)([/#])?', np_uri_str)
            head_str = str(np_meta.head)
            if extract_trusty_pre:
                trusty_code_tmp = extract_trusty_pre.group(3)
                if trusty_code_tmp in head_str:
                    idx = head_str.index(trusty_code_tmp) + len(trusty_code_tmp)
                    sep = head_str[idx] if idx < len(head_str) else "/"
                    default_separator_char = sep if sep in ("#", "/") else ""
                else:
                    default_separator_char = head_str.rsplit("Head", 1)[0][-1]
            else:
                if head_str.startswith(np_uri_str):
                    suffix = head_str[len(np_uri_str):]
                    default_separator_char = suffix[0]

        # Check if the nanopub URI has a trusty artifact:
        # Regex to extract base URI, and trusty URI (if any)
        extract_trusty = re.search(r'^(.*?)([/#])?(RA[A-Za-z0-9_\-]+)([/#])?', np_uri_str)
        if extract_trusty:
            np_meta.trusty = extract_trusty.group(3)
            np_meta.namespace = Namespace(
                np_uri_str.split(np_meta.trusty)[0] + np_meta.trusty + default_separator_char)
        else:
            # No trusty code present (e.g. temp namespace)
            np_meta.trusty = None
            if np_uri_str.endswith(("#", "/")):
                np_meta.namespace = Namespace(np_uri_str)
            else:
                np_meta.namespace = Namespace(np_uri_str + default_separator_char)

    return np_meta
