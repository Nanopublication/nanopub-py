import re

from rdflib import Dataset, URIRef, Literal, Namespace, Graph

from nanopub import Nanopub
from nanopub.definitions import NP_PREFIX, NP_TEMP_PREFIX
from nanopub.namespaces import NPX
from nanopub.sign_utils import add_signature
from nanopub.trustyuri.rdf import RdfUtils
from tests.conftest import profile_test, testsuite_conf


ARTIFACTCODE_PLAIN_TRIG = """\
@prefix this: <http://purl.org/nanopub/temp/1029384756/> .
@prefix np: <http://www.nanopub.org/nschema#> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix npx: <http://purl.org/nanopub/x/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix orcid: <https://orcid.org/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix ex: <https://example.org/ns/> .

this:Head {
  this: a np:Nanopublication;
    np:hasAssertion this:assertion;
    np:hasProvenance this:provenance;
    np:hasPublicationInfo this:pubinfo .
}

this:assertion {
  <https://example.org/ns/~~~ARTIFACTCODE~~~> a ex:Concept;
    rdfs:label "a concept minted in a custom namespace" .
}

this:provenance {
  this:assertion prov:wasAttributedTo orcid:0000-0002-1267-0234 .
}

this:pubinfo {
  this: dct:created "2024-09-18T11:19:06.183Z"^^xsd:dateTime;
    dct:creator orcid:0000-0002-1267-0234;
    npx:introduces <https://example.org/ns/~~~ARTIFACTCODE~~~> .
}
"""


def test_sign_artifactcode_placeholder_in_custom_namespace():
    """Signing a nanopub that mints a concept in a custom namespace via the
    ``~~~ARTIFACTCODE~~~`` placeholder gives that concept the same trusty code
    as the nanopub itself, and the result is valid (see issue #232)."""
    ds = Dataset()
    ds.parse(data=ARTIFACTCODE_PLAIN_TRIG, format="trig")
    np = Nanopub(conf=testsuite_conf, rdf=ds)
    np.sign()

    assert np.has_valid_signature
    assert np.has_valid_trusty
    assert np.is_valid

    artifact_code = str(np.source_uri).removeprefix(NP_PREFIX)
    assert re.fullmatch(r"RA[A-Za-z0-9\-_]{43}", artifact_code)

    # The placeholder must be gone and the concept must carry the nanopub's code.
    concept = URIRef(f"https://example.org/ns/{artifact_code}")
    subjects = {s for s, _, _, _ in np.rdf.quads((None, None, None, None))}
    objects = {o for _, _, o, _ in np.rdf.quads((None, None, None, None))}
    assert concept in subjects
    assert concept in objects  # still referenced by npx:introduces
    for term in subjects | objects:
        assert "~~~ARTIFACTCODE~~~" not in str(term)


class TestVerifyTrusty:

    def test_real_uri_returns_true(self):
        np = Nanopub(source_uri="https://w3id.org/np/RAAwn-ONPeKgxxWJNBDtVotYfZcFyppCy_z8ASy2mJLKY")
        assert np.has_valid_trusty

    def test_get_quads_preserves_named_graph_context_identifier(self):
        ds = Dataset()
        graph_uri = URIRef("https://example.org/g")
        ds.add((URIRef("https://example.org/s"), URIRef("https://example.org/p"), Literal("x"), graph_uri))

        quads = RdfUtils.get_quads(ds)
        assert len(quads) == 1
        assert quads[0][0] == graph_uri  # context should not collapse to None


class TestAddSignature:

    def test_add_signature(self):
        input_g = Dataset()
        dummy_namespace = Namespace(NP_TEMP_PREFIX)
        pubinfo_uri = URIRef(f"{dummy_namespace}pubinfo")
        pubinfo_g = Graph(store=input_g.store, identifier=pubinfo_uri)

        output_g = add_signature(input_g, profile_test, dummy_namespace, pubinfo_g)

        # Find the generated signature subject
        sig_subjects = [s for s, _, _, _ in output_g.quads((None, NPX.hasSignature, None, None))]
        assert len(sig_subjects) == 1
        sig_subject = sig_subjects[0]

        # Use hasAlgorithm to pin the graph context used for signature metadata
        matches = list(output_g.quads((sig_subject, NPX.hasAlgorithm, Literal("RSA"), None)))
        assert len(matches) == 1
        _, _, _, found_graph = matches[0]
        assert found_graph is not None
        ctx_graph = output_g.graph(found_graph)
        assert (sig_subject, NPX.hasPublicKey, Literal(profile_test.public_key)) in ctx_graph
        assert (sig_subject, NPX.signedBy, URIRef(profile_test.orcid_id))

        sig_values = [o for _, _, o, _ in output_g.quads((sig_subject, NPX.hasSignature, None, None))]
        assert len(sig_values) == 1
        assert isinstance(sig_values[0], Literal)
        assert str(sig_values[0]).strip() != ""

        # Signature target must be the nanopub URI (same namespace, no fragment)
        targets = [o for _, _, o, _ in output_g.quads((sig_subject, NPX.hasSignatureTarget, None, None))]
        assert len(targets) == 1
        target_uri = str(targets[0])
        assert target_uri.startswith(NP_PREFIX)
        artifact_code = target_uri.removeprefix(NP_PREFIX)
        assert re.fullmatch(r"RA[A-Za-z0-9\-_]{43}", artifact_code)

        # Ensure temp namespace was replaced everywhere in URIRefs
        for s, p, o, c in output_g.quads((None, None, None, None)):
            for term in (s, p, o, c):
                if isinstance(term, URIRef):
                    assert not str(term).startswith(NP_TEMP_PREFIX)
