from rdflib import Dataset, URIRef, Literal

from nanopub import Nanopub
from nanopub.trustyuri.rdf import RdfUtils


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
