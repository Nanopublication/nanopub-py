import inspect
import json
from unittest.mock import MagicMock, patch

import pytest
from nanopub_testsuite_connector import TestSuiteSubfolder
from rdflib import BNode, Graph, Literal, URIRef, Dataset, DC, RDF, Namespace, DCTERMS, PROV

from nanopub import (
    Nanopub,
    NanopubConf,
    namespaces,
)
from nanopub.profile import ProfileError
from nanopub.utils import MalformedNanopubError
from tests.conftest import (
    default_conf,
    profile_test,
    skip_if_nanopub_server_unavailable, testsuite,
)


def _make_dataset_from_trig(testsuite) -> Dataset:
    ds = Dataset()
    ds.parse(testsuite.get_valid(TestSuiteSubfolder.PLAIN)[0].path, format="trig")
    return ds


def _make_ok_response(text: str) -> MagicMock:
    resp = MagicMock()
    resp.ok = True
    resp.text = text
    resp.raise_for_status = MagicMock()
    return resp


def _make_fail_response() -> MagicMock:
    resp = MagicMock()
    resp.ok = False
    resp.raise_for_status = MagicMock(side_effect=Exception("404 Not Found"))
    return resp


def _simple_assertion() -> Graph:
    g = Graph()
    g.add((URIRef("http://test"), namespaces.HYCL.claims, Literal("test claim")))
    return g


class TestCreationDefault:

    def test_nanopub_init_has_no_mutable_defaults(self):
        sig = inspect.signature(Nanopub.__init__)
        assert sig.parameters["assertion"].default is None
        assert sig.parameters["provenance"].default is None
        assert sig.parameters["pubinfo"].default is None

    def test_nanopub_constructor_default_objects_not_reused(self):
        # This directly checks the function defaults tuple, not instance fields.
        defaults = Nanopub.__init__.__defaults__
        # current order in your signature:
        # source_uri, assertion, provenance, pubinfo, rdf, introduces_concept, conf
        assertion_default = defaults[1]
        provenance_default = defaults[2]
        pubinfo_default = defaults[3]

        assert assertion_default is None
        assert provenance_default is None
        assert pubinfo_default is None

    def test_nanopub_default_inputs_are_isolated_objects(self):
        np1 = Nanopub()
        np2 = Nanopub()

        # Distinct internal graph objects
        assert np1.assertion is not np2.assertion
        assert np1.provenance is not np2.provenance
        assert np1.pubinfo is not np2.pubinfo

        # Distinct config objects
        assert np1.conf is not np2.conf

    def test_no_parameters(self):
        np = Nanopub()
        assert np.source_uri is None
        assert len(np.head) > 0
        assert len(list(np.head.triples((None, RDF.type, namespaces.NP.Nanopublication)))) == 1
        assert len(list(np.head.triples((None, namespaces.NP.hasProvenance, None)))) == 1
        assert len(list(np.head.triples((None, namespaces.NP.hasPublicationInfo, None)))) == 1

    def test_head_is_created(self):
        """A freshly constructed Nanopub should have a non-empty Head graph."""
        np = Nanopub(conf=NanopubConf())
        assert len(np.head) > 0

    def test_head_declares_nanopublication_type(self):
        """Head should declare the np:Nanopublication type triple."""
        np = Nanopub(conf=NanopubConf())
        assert len(list(np.head.triples((None, RDF.type, namespaces.NP.Nanopublication)))) == 1

    def test_head_links_assertion(self):
        np = Nanopub(conf=NanopubConf())
        assert len(list(np.head.triples((None, namespaces.NP.hasAssertion, None)))) == 1

    def test_head_links_provenance(self):
        np = Nanopub(conf=NanopubConf())
        assert len(list(np.head.triples((None, namespaces.NP.hasProvenance, None)))) == 1

    def test_head_links_pubinfo(self):
        np = Nanopub(conf=NanopubConf())
        assert len(list(np.head.triples((None, namespaces.NP.hasPublicationInfo, None)))) == 1

    def test_assertion_accepts_added_triples(self):
        """Triples added to assertion post-construction should be stored."""
        np = Nanopub(conf=NanopubConf())
        np.assertion.add((URIRef("http://another"), namespaces.HYCL.claims, Literal("hello")))
        assert len(np.assertion) == 1

    def test_assertion_graph_passed_at_construction(self):
        """An assertion Graph passed at construction time should populate the graph."""
        np = Nanopub(assertion=_simple_assertion(), conf=NanopubConf())
        assert len(np.assertion) == 1

    def test_source_uri_is_none_before_signing(self):
        np = Nanopub(conf=NanopubConf())
        assert np.source_uri is None

    def test_not_published_by_default(self):
        np = Nanopub(conf=NanopubConf())
        assert not np.published

    def test_is_valid_empty_graphs_and_graph_count(self):
        np = Nanopub(conf=NanopubConf())
        # Empty head
        np._head.remove((None, None, None))
        with pytest.raises(MalformedNanopubError):
            np.is_valid
        # Too many graphs
        np2 = Nanopub(conf=NanopubConf())
        extra = Graph()
        extra.add((URIRef("http://s"), URIRef("http://p"), Literal("o")))
        np2._rdf.add_graph(extra)
        with pytest.raises(MalformedNanopubError):
            np2.is_valid
        # Missing provenance triple
        np3 = Nanopub(conf=NanopubConf())
        np3._provenance.remove((None, None, None))
        with pytest.raises(MalformedNanopubError):
            np3.is_valid
        # Missing pubinfo triple
        np4 = Nanopub(conf=NanopubConf())
        np4._pubinfo.remove((None, None, None))
        with pytest.raises(MalformedNanopubError):
            np4.is_valid

    def test_get_source_uri_from_graph_none(self):
        np = Nanopub(conf=NanopubConf())
        # No matching regex, should return None
        assert np.get_source_uri_from_graph is None

    def test_signed_with_public_key_none(self):
        np = Nanopub(conf=NanopubConf())
        assert np.signed_with_public_key is None

    def test_introduces_concept_multiple_error(self):
        np = Nanopub(conf=NanopubConf())
        np._pubinfo.add(
            (URIRef("http://s"), namespaces.NPX.introduces, URIRef("http://c1"))
        )
        np._pubinfo.add(
            (URIRef("http://s"), namespaces.NPX.introduces, URIRef("http://c2"))
        )
        with pytest.raises(MalformedNanopubError):
            np.introduces_concept


class TestCreationFromSourceUri:

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_nanopub_fetch(self):
        """Check that creating Nanopub from source URI (fetch) works for a few known nanopub URIs."""
        known_nps = [
            "https://w3id.org/np/RAQUd7PYws4Hh5pCpvLRbHfh0piLS5PyfOQXnSGD5JctY",
            "https://w3id.org/np/RAO0soO0mUWTqqMaz1QcGbdIt90MJ55RXJck8w8wGGc0U",
        ]
        for np_uri in known_nps:
            np = Nanopub(source_uri=np_uri, conf=NanopubConf(use_test_server=True))
            assert len(np.rdf) > 0
            assert np.assertion is not None
            assert np.pubinfo is not None
            assert np.provenance is not None
            assert np.is_valid

    def test_invalid_fetch(self):
        with pytest.raises(Exception):
            Nanopub(source_uri="http://a-real-server/example")

    def test_http_error_raises(self):
        """raise_for_status propagating should surface as an exception."""
        with patch("nanopub.nanopub.requests.get", return_value=_make_fail_response()):
            with pytest.raises(Exception, match="404"):
                Nanopub(source_uri="https://purl.org/np/nonExistingNp", conf=NanopubConf())

    def test_fallback_to_test_server_on_first_failure(self, testsuite):
        """When use_test_server=True and primary request fails, a second GET is issued."""
        fail = _make_fail_response()
        fail.raise_for_status = MagicMock()  # don't raise on first call, just ok=False

        with patch(
                "nanopub.nanopub.requests.get", side_effect=[fail, _make_ok_response(
                    testsuite.get_by_nanopub_uri("http://example.org/nanopub-validator-example/").path.read_text()
                )]
        ) as mock_get:
            np = Nanopub(
                source_uri="https://purl.org/np/whateverNp",
                conf=NanopubConf(use_test_server=True),
            )

        assert mock_get.call_count == 2
        assert len(np.rdf) > 0

    def test_metadata_matches_fetched_graph(self, testsuite):
        """Metadata extracted from the fetched graph should reference the nanopub URI."""
        with patch("nanopub.nanopub.requests.get", return_value=_make_ok_response(
                testsuite.get_by_nanopub_uri("http://example.org/nanopub-validator-example/").path.read_text()
        )):
            np = Nanopub(source_uri="https://purl.org/np/whateverNp", conf=NanopubConf())

        # This returns the np_uri read in the nanopub, which in this case is http://example.org/nanopub-validator-example/ as per the fixture
        assert "http://example.org/nanopub-validator-example/" in str(np.metadata.np_uri)


class TestCreationFromDataset:

    def test_dataset_is_stored(self, testsuite):
        """Passing a Dataset should populate internal RDF."""
        np = Nanopub(rdf=_make_dataset_from_trig(testsuite), conf=NanopubConf())
        assert len(np.rdf) > 0

    def test_all_sub_graphs_are_non_empty(self, testsuite):
        """All four named sub-graphs should be accessible and non-empty."""
        np = Nanopub(rdf=_make_dataset_from_trig(testsuite), conf=NanopubConf())
        assert len(np.assertion) > 0
        assert len(np.provenance) > 0
        assert len(np.pubinfo) > 0
        assert len(np.head) > 0

    def test_source_uri_none_without_trusty_uri(self, testsuite):
        """Without a trusty URI in the graph, source_uri should be None."""
        np = Nanopub(rdf=_make_dataset_from_trig(testsuite), conf=NanopubConf())
        assert np.source_uri is None

    def test_empty_dataset_is_invalid(self):
        """An empty Dataset should raise MalformedNanopubError."""
        with pytest.raises(MalformedNanopubError):
            Nanopub(rdf=Dataset(), conf=NanopubConf())

    def test_metadata_matches_graph(self, testsuite):
        """Metadata np_uri should reflect the URI in the parsed trig."""
        ds = Dataset()
        ds.parse(data=testsuite.get_by_nanopub_uri("http://example.org/nanopub-validator-example/").path.read_text(),
                 format="trig")
        np = Nanopub(rdf=ds, conf=NanopubConf())
        assert "http://example.org/nanopub-validator-example/" in str(np.metadata.np_uri)


class TestCreationFromFile:

    def test_trig_file_is_parsed(self, tmp_path, testsuite):
        """A .trig file on disk should be parsed into a non-empty graph."""
        trig_file = tmp_path / "test.trig"
        trig_file.write_text(testsuite.get_valid(TestSuiteSubfolder.PLAIN)[0].path.read_text())

        np = Nanopub(rdf=trig_file, conf=NanopubConf())

        assert len(np.rdf) > 0
        assert len(np.assertion) > 0

    def test_all_sub_graphs_non_empty(self, tmp_path, testsuite):
        """All four named sub-graphs should be non-empty when loaded from file."""
        trig_file = tmp_path / "test.trig"
        trig_file.write_text(testsuite.get_valid(TestSuiteSubfolder.PLAIN)[0].path.read_text())

        np = Nanopub(rdf=trig_file, conf=NanopubConf())

        assert len(np.provenance) > 0
        assert len(np.pubinfo) > 0
        assert len(np.head) > 0

    def test_missing_file_raises(self, tmp_path):
        """Pointing to a non-existent file should raise an exception."""
        with pytest.raises(Exception):
            Nanopub(rdf=tmp_path / "does_not_exist.trig", conf=NanopubConf())

    def test_metadata_np_uri_extracted_from_file(self, tmp_path, testsuite):
        """Metadata np_uri should match the URI declared inside the trig file."""
        trig_file = tmp_path / "test.trig"
        trig_file.write_text(
            testsuite.get_by_nanopub_uri("http://example.org/nanopub-validator-example/").path.read_text())

        np = Nanopub(rdf=trig_file)

        assert str(np.metadata.np_uri) == "http://example.org/nanopub-validator-example/"


class TestCreationFromTrustyNanopub:
    """When a nanopub carries a trusty URI, source_uri should be resolved from
    the graph itself, not rely on an externally passed argument."""

    def test_source_uri_resolved_from_trusty_dataset(self, testsuite):
        """source_uri should be set from the trusty URI found in the graph."""
        ds = Dataset()
        ds.parse(data=testsuite.get_by_nanopub_uri(
            "http://purl.org/np/RA1sViVmXf-W2aZW4Qk74KTaiD9gpLBPe2LhMsinHKKz8").path.read_text(), format="trig")
        np = Nanopub(rdf=ds, conf=NanopubConf())
        assert np.source_uri == "http://purl.org/np/RA1sViVmXf-W2aZW4Qk74KTaiD9gpLBPe2LhMsinHKKz8"
        assert np.is_valid

    def test_source_uri_resolved_from_trusty_file(self, tmp_path, testsuite):
        """source_uri should be set from the trusty URI when loaded from a file."""
        trig_file = tmp_path / "trusty.trig"
        trig_file.write_text(testsuite.get_by_nanopub_uri(
            "http://purl.org/np/RA1sViVmXf-W2aZW4Qk74KTaiD9gpLBPe2LhMsinHKKz8").path.read_text())
        np = Nanopub(rdf=trig_file, conf=NanopubConf())
        assert np.source_uri == "http://purl.org/np/RA1sViVmXf-W2aZW4Qk74KTaiD9gpLBPe2LhMsinHKKz8"
        assert np.is_valid

    def test_metadata_np_uri_matches_trusty_uri(self, testsuite):
        """Metadata np_uri should match the trusty URI declared in the graph."""
        ds = Dataset()
        ds.parse(data=testsuite.get_by_nanopub_uri(
            "http://purl.org/np/RA1sViVmXf-W2aZW4Qk74KTaiD9gpLBPe2LhMsinHKKz8").path.read_text(), format="trig")
        np = Nanopub(rdf=ds, conf=NanopubConf())
        assert str(np.metadata.np_uri) == "http://purl.org/np/RA1sViVmXf-W2aZW4Qk74KTaiD9gpLBPe2LhMsinHKKz8"
        assert np.is_valid

    def test_all_sub_graphs_non_empty(self, testsuite):
        """All four sub-graphs should be populated from a trusty trig."""
        ds = Dataset()
        ds.parse(data=testsuite.get_by_nanopub_uri(
            "http://purl.org/np/RA1sViVmXf-W2aZW4Qk74KTaiD9gpLBPe2LhMsinHKKz8").path.read_text(), format="trig")
        np = Nanopub(rdf=ds, conf=NanopubConf())
        assert len(np.head) > 0
        assert len(np.assertion) > 0
        assert len(np.provenance) > 0
        assert len(np.pubinfo) > 0

    def test_get_source_uri_from_graph_returns_trusty(self, testsuite):
        """get_source_uri_from_graph should extract the trusty URI from the head."""
        ds = Dataset()
        ds.parse(data=testsuite.get_by_nanopub_uri(
            "http://purl.org/np/RA1sViVmXf-W2aZW4Qk74KTaiD9gpLBPe2LhMsinHKKz8").path.read_text(), format="trig")
        np = Nanopub(rdf=ds, conf=NanopubConf())
        assert np.get_source_uri_from_graph == "http://purl.org/np/RA1sViVmXf-W2aZW4Qk74KTaiD9gpLBPe2LhMsinHKKz8"


class TestSign:

    def test_sign_errors(self, monkeypatch):
        # No profile -> should raise ProfileError
        np = Nanopub(conf=NanopubConf(profile=None))
        np._assertion.add(
            (URIRef("http://test"), namespaces.HYCL.claims, Literal("test claim"))
        )
        np._provenance.add(
            (
                np._assertion.identifier,
                PROV.wasAttributedTo,
                URIRef("http://someone"),
            )
        )
        np._pubinfo.add((np._metadata.namespace[""], DC.creator, Literal("tester")))

        with pytest.raises(ProfileError):
            np.sign()

        # Already signed -> should raise MalformedNanopubError
        np2 = Nanopub(conf=NanopubConf(profile=default_conf.profile))
        np2._assertion.add(
            (URIRef("http://test2"), namespaces.HYCL.claims, Literal("test claim 2"))
        )
        np2._provenance.add(
            (
                np2._assertion.identifier,
                PROV.wasAttributedTo,
                URIRef("http://someone"),
            )
        )
        np2._pubinfo.add((np2._metadata.namespace[""], DC.creator, Literal("tester")))
        np2._metadata.signature = True

        with pytest.raises(MalformedNanopubError):
            np2.sign()

        # Invalid nanopub -> should raise MalformedNanopubError
        monkeypatch.setattr(type(np2), "is_valid", property(lambda self: False))

        np2._metadata.signature = None
        with pytest.raises(MalformedNanopubError):
            np2.sign()

    def test_nanopub_sign_uri(self):
        expected_trusty = "RAIh8Oq-29dIVTZDhETpJ6f8oxxrILbZ3gSxkyAQY4220"
        assertion = Graph()
        assertion.add(
            (
                URIRef("http://test"),
                namespaces.HYCL.claims,
                Literal("This is a test of nanopub-python"),
            )
        )
        np = Nanopub(conf=default_conf, assertion=assertion)
        np.sign()
        assert np.has_valid_signature
        assert expected_trusty in np.source_uri

    def test_nanopub_sign_uri2(self):
        expected_trusty = "RAIh8Oq-29dIVTZDhETpJ6f8oxxrILbZ3gSxkyAQY4220"
        np = Nanopub(
            conf=default_conf,
        )
        np.assertion.add(
            (
                URIRef("http://test"),
                namespaces.HYCL.claims,
                Literal("This is a test of nanopub-python"),
            )
        )
        np.sign()
        assert np.has_valid_signature
        assert expected_trusty in np.source_uri

    def test_nanopub_sign_bnode(self):
        expected_trusty = "RAcU1AR3dS0ricV5G_ENcpUCk40XuCvFW3tVFqxNEQzT4"
        assertion = Graph()
        assertion.add(
            (
                BNode("test"),
                namespaces.HYCL.claims,
                Literal("This is a test of nanopub-python"),
            )
        )
        np = Nanopub(conf=default_conf, assertion=assertion)
        np.sign()
        assert np.has_valid_signature
        assert expected_trusty in np.source_uri

    def test_nanopub_sign_bnode2(self):
        expected_trusty = "RA-1eE8scfVaiK7vP4CZueTyEyRmn1g2PpPf-j69WQAgM"
        assertion = Graph()
        assertion.add(
            (
                BNode("test"),
                namespaces.HYCL.claims,
                Literal("This is a test of nanopub-python"),
            )
        )
        assertion.add(
            (
                BNode("test2"),
                namespaces.HYCL.claims,
                Literal("This is another test of nanopub-python"),
            )
        )
        np = Nanopub(conf=default_conf, assertion=assertion)
        np.sign()
        assert expected_trusty in np.source_uri
        assert np.has_valid_signature

    def test_specific_file(self):
        """Test to sign a complex file with many blank nodes"""

        np_conf = NanopubConf(profile=profile_test, use_test_server=True)
        np_conf.add_prov_generated_time = (True,)
        np_conf.add_pubinfo_generated_time = (True,)
        np_conf.attribute_assertion_to_profile = (True,)
        np_conf.attribute_publication_to_profile = (True,)

        with open("./tests/resources/many_bnodes_with_annotations.json") as f:
            nanopub_rdf = json.loads(f.read())

        annotations_rdf = nanopub_rdf["@annotations"]
        del nanopub_rdf["@annotations"]
        nanopub_rdf = str(json.dumps(nanopub_rdf))

        g = Graph()
        g.parse(data=nanopub_rdf, format="json-ld")

        np = Nanopub(
            assertion=g,
            conf=np_conf,
        )
        source = "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=f9641190-9151-4f7e-89ff-1e7a818c30ee"
        if annotations_rdf:
            np.provenance.parse(data=str(json.dumps(annotations_rdf)), format="json-ld")
        if source:
            np.provenance.add(
                (np.assertion.identifier, PROV.hadPrimarySource, URIRef(source))
            )

        PAV = Namespace("http://purl.org/pav/")
        if True:
            np.pubinfo.add(
                (
                    np.metadata.np_uri,
                    DCTERMS.conformsTo,
                    URIRef("https://w3id.org/biolink/vocab/"),
                )
            )
            np.pubinfo.add(
                (
                    URIRef("https://w3id.org/biolink/vocab/"),
                    PAV.version,
                    Literal("3.1.0"),
                )
            )
        np.sign()


class TestPublish:

    def test_nanopub_publish(self):
        expected_trusty = "RAIh8Oq-29dIVTZDhETpJ6f8oxxrILbZ3gSxkyAQY4220"
        assertion = Graph()
        assertion.add(
            (
                URIRef("http://test"),
                namespaces.HYCL.claims,
                Literal("This is a test of nanopub-python"),
            )
        )
        np = Nanopub(conf=default_conf, assertion=assertion)
        np.publish()
        assert np.has_valid_signature
        assert expected_trusty in np.source_uri

    def test_publish_calls_sign(self, monkeypatch):
        np = Nanopub(conf=NanopubConf(profile=None))
        monkeypatch.setattr(np, "sign", lambda: setattr(np, "_published", True))
        np.publish()
        assert np.published


class TestReplaceBlankNodes:

    def test_replace_blank_nodes_unnamed_bnode(self):
        # BNode with 33-character name triggers unnamed branch
        bname = "N" + "a" * 32
        g = Dataset()
        g.add((BNode(bname), URIRef("http://test/p"), Literal("value")))
        np = Nanopub(conf=NanopubConf())
        g2 = np._replace_blank_nodes(g)
        assert len(list(g2.quads((None, None, None, None)))) == 1


class TestHandlePublicationAttributedTo:

    def test_handle_publication_attributed_to_no_profile(self):
        np = Nanopub(conf=NanopubConf(profile=None))
        with pytest.raises(MalformedNanopubError):
            np._handle_publication_attributed_to(
                attribute_publication_to_profile=True, publication_attributed_to=None
            )


class TestHandleDerivedFrom:

    def test_from_list(self):
        np = Nanopub(conf=NanopubConf())
        np._handle_derived_from(["http://example.org/derived2"])
        found2 = list(
            np.provenance.triples((None, None, URIRef("http://example.org/derived2")))
        )
        assert found2

    def test_from_str(self):
        np = Nanopub(conf=NanopubConf())
        np._handle_derived_from("http://example.org/derived")
        found = list(
            np.provenance.triples((None, None, URIRef("http://example.org/derived")))
        )
        assert found


class TestHandleIntroducesConcept:

    def test_handle_introduces_concept_adds_triple(self):
        np = Nanopub(conf=NanopubConf())
        bnode = BNode("concept1")
        np._handle_introduces_concept(bnode)
        triples = list(np.pubinfo.triples((None, None, None)))
        assert triples


class TestValidateNanopubArguments:

    def test_validate_nanopub_arguments_errors(self):
        np = Nanopub(conf=NanopubConf())
        # Both assertion_attributed_to and attribute_assertion_to_profile
        with pytest.raises(MalformedNanopubError):
            np._validate_nanopub_arguments(
                derived_from=None,
                assertion_attributed_to="http://example.org",
                attribute_assertion_to_profile=True,
                introduces_concept=None,
            )
        # introduces_concept not BNode
        with pytest.raises(MalformedNanopubError):
            np._validate_nanopub_arguments(
                derived_from=None,
                assertion_attributed_to=None,
                attribute_assertion_to_profile=False,
                introduces_concept=URIRef("http://example.org"),
            )
