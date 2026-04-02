import re
from base64 import decodebytes, encodebytes

import requests
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from rdflib import BNode, Dataset, Graph, Literal, Namespace, URIRef

from nanopub.definitions import NANOPUB_REGISTRY_URLS, NP_PREFIX, NP_TEMP_PREFIX
from nanopub.namespaces import NPX
from nanopub.profile import Profile
from nanopub.trustyuri.rdf import RdfHasher, RdfUtils
from nanopub.trustyuri.rdf.RdfPreprocessor import transform
from nanopub.utils import MalformedNanopubError, log


def add_signature(g: Dataset, profile: Profile, dummy_namespace: Namespace, pubinfo_g: Graph) -> Dataset:
    """Implementation in python of the process to sign a nanopub with a RSA private key"""
    g.add((
        dummy_namespace["sig"],
        NPX["hasPublicKey"],
        Literal(profile.public_key),
        pubinfo_g,
    ))
    g.add((
        dummy_namespace["sig"],
        NPX["hasAlgorithm"],
        Literal("RSA"),
        pubinfo_g,
    ))
    g.add((
        dummy_namespace["sig"],
        NPX["hasSignatureTarget"],
        dummy_namespace[""],
        pubinfo_g,
    ))
    g.add((
        dummy_namespace["sig"],
        NPX["signedBy"],
        URIRef(profile.orcid_id),
        pubinfo_g,
    ))
    # Normalize RDF
    quads = RdfUtils.get_quads(g)
    normed_rdf = RdfHasher.normalize_quads(
        quads,
        baseuri=str(dummy_namespace),
        hashstr=" "
    )
    # Note: normed_rdf needs to end with a newline
    # print(f"NORMED RDF STARTS\n{normed_rdf}\nNORMED RDF ENDS")

    # Sign the normalized RDF with the private RSA key
    private_key = RSA.import_key(decodebytes(profile.private_key.encode()))
    signer = PKCS1_v1_5.new(private_key)
    signature_b = signer.sign(SHA256.new(normed_rdf.encode()))
    signature = encodebytes(signature_b).decode().replace("\n", "")
    log.debug(f"Nanopub signature: {signature}")

    # Add the signature to the graph
    g.add((
        dummy_namespace["sig"],
        NPX["hasSignature"],
        Literal(signature),
        pubinfo_g,
    ))

    # Generate the trusty URI
    quads = RdfUtils.get_quads(g)
    trusty_artefact = RdfHasher.make_hash(
        quads,
        baseuri=str(dummy_namespace),
        hashstr=" "
    )
    log.debug(f"Trusty artefact: {trusty_artefact}")

    g = replace_trusty_in_graph(trusty_artefact, str(dummy_namespace), g)
    return g


def replace_trusty_in_graph(trusty_artefact: str, dummy_ns: str, graph: Dataset):
    """Replace all references to the dummy namespace by the Trusty artefact in a Graph"""
    if str(dummy_ns).startswith(NP_TEMP_PREFIX):
        # Replace with http://purl.org/np/ if the http://purl.org/nanopub/temp/
        # prefix is used in the dummy nanopub URI
        np_uri = NP_PREFIX + trusty_artefact
    else:
        np_uri = dummy_ns + trusty_artefact

    graph.bind("this", Namespace(np_uri))
    graph.bind("sub", Namespace(np_uri + "/"))
    graph.bind("", None, replace=True)

    # Iterate quads in the graph, and replace by the transformed value
    bnodemap: dict = {}
    for s, p, o, c in graph.quads(None):
        if c:
            g = c
        else:
            raise Exception(
                "Found a nquads without graph when replacing dummy URIs with trusty URIs. Something went wrong.")
        # new_g = Graph(identifier=str(transform(g, trusty_artefact, dummy_ns, bnodemap)))
        # Fails and make the nanopub empty
        new_g = URIRef(transform(g, trusty_artefact, dummy_ns, bnodemap))
        new_s = URIRef(transform(s, trusty_artefact, dummy_ns, bnodemap))
        new_p = URIRef(transform(p, trusty_artefact, dummy_ns, bnodemap))
        new_o = o
        if isinstance(o, URIRef) or isinstance(o, BNode):
            new_o = URIRef(transform(o, trusty_artefact, dummy_ns, bnodemap))

        graph.remove((s, p, o, c))
        graph.add((new_s, new_p, new_o, new_g))  # type: ignore

    return graph


def publish_graph(g: Dataset, use_server: str = NANOPUB_REGISTRY_URLS[0]) -> bool:
    """Publish a signed nanopub to the given nanopub server.
    """
    log.info(f"Publishing to the nanopub server {use_server}")
    headers = {'Content-Type': 'application/trig'}
    # NOTE: nanopub-java uses {'Content-Type': 'application/x-www-form-urlencoded'}
    data = g.serialize(format="trig")
    r = requests.post(use_server, headers=headers, data=data.encode('utf-8'))
    r.raise_for_status()
    return True


def verify_trusty(g: Dataset, source_uri: str, source_namespace: Namespace) -> bool:
    """Verify Trusty URI in a nanopub Graph"""
    if not source_uri:
        raise ValueError("source_uri must not be None")
    _m = re.search(r'RA[A-Za-z0-9_\-]{40,}', source_uri)
    source_trusty = _m.group(0) if _m else source_uri.split('/')[-1]
    quads = RdfUtils.get_quads(g)
    expected_trusty = RdfHasher.make_hash(
        quads,
        baseuri=str(source_namespace),
        hashstr=" "
    )
    if expected_trusty != source_trusty:
        raise MalformedNanopubError(
            f"The Trusty artefact of the nanopub {source_trusty} is not valid. It should be {expected_trusty}")
    else:
        return True


def verify_signature(g: Dataset, source_uri: str, source_namespace: Namespace) -> bool:
    """Verify RSA signature in a nanopub Graph"""
    # Get signature and public key from the triples
    np_signature_target = [s for s, _, _, _ in g.quads((None, NPX.hasSignatureTarget, URIRef(source_uri), None))]
    if not np_signature_target:
        raise MalformedNanopubError("No Signature targeting the '{source_uri}' nanopublication")

    np_signature_target = np_signature_target[0]

    np_sign = [o for _, _, o, _ in g.quads((np_signature_target, NPX.hasSignature, None, None))]
    if not np_sign:
        raise MalformedNanopubError("No Signature found in the nanopublication RDF")

    np_sign = np_sign[0]

    np_algo = [o for _, _, o, _ in g.quads((np_signature_target, NPX.hasAlgorithm, None, None))][0]
    if np_algo and str(np_algo).upper() != "RSA":
        if np_algo and str(np_algo).upper() == "DSA":
            # TODO implement DSA signature verification
            log.info("DSA signature algorithm is not supported yet, skipping signature verification")
            return True
        else:
            raise MalformedNanopubError(
                f"Signature algorithm '{np_algo}' is not supported, only RSA is supported"
            )

    # Normalize RDF
    quads = RdfUtils.get_quads(g)
    normed_rdf = RdfHasher.normalize_quads(
        quads,
        baseuri=str(source_namespace),
        hashstr=" "
    )
    np_pubkey = [o for _, _, o, _ in g.quads((np_signature_target, NPX.hasPublicKey, None, None))][0]
    # Verify signature using the normalized RDF
    key = RSA.import_key(decodebytes(str(np_pubkey).encode()))
    hash_value = SHA256.new(normed_rdf.encode())
    verifier = PKCS1_v1_5.new(key)
    try:
        verifier.verify(hash_value, decodebytes(str(np_sign).encode()))
    except Exception as e:
        raise MalformedNanopubError(e)

    np_signedBy = [o for _, _, o, _ in g.quads((np_signature_target, NPX.signedBy, None, None))]
    if not np_signedBy:
        raise MalformedNanopubError("No signedBy found in the nanopublication RDF")
    np_signedBy = np_signedBy[0]
    # TODO improve this by checking that the ORCID is a valid one
    if not str(np_signedBy).startswith("https://orcid.org/"):
        raise MalformedNanopubError(
            f"Invalid signedBy value '{np_signedBy}' in the nanopublication RDF, it should be an ORCID iD starting with 'https://orcid.org/'")
    return True
