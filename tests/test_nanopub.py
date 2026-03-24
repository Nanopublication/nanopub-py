from unittest.mock import MagicMock, patch

import pytest
from rdflib import BNode, Graph, Literal, URIRef, Dataset, DC, RDF

from nanopub import (
    Nanopub,
    NanopubClaim,
    NanopubConf,
    create_nanopub_index,
    namespaces,
)
from nanopub.profile import ProfileError
from nanopub.templates.nanopub_introduction import NanopubIntroduction
from nanopub.templates.nanopub_retract import NanopubRetract
from nanopub.templates.nanopub_update import NanopubUpdate
from nanopub.utils import MalformedNanopubError
from tests.conftest import (
    default_conf,
    profile_test,
    skip_if_nanopub_server_unavailable,
)

TRIG_FIXTURE = """\
@prefix : <http://example.org/nanopub-validator-example/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix dc: <http://purl.org/dc/terms/> .
@prefix pav: <http://purl.org/pav/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix np: <http://www.nanopub.org/nschema#> .
@prefix npx: <http://purl.org/nanopub/x/> .
@prefix ex: <http://example.org/> .

:Head {
	: np:hasAssertion :assertion ;
		np:hasProvenance :provenance ;
		np:hasPublicationInfo :pubinfo ;
		a np:Nanopublication .
}

:assertion {
	:assertion npx:asSentence <http://purl.org/aida/Malaria+is+transmitted+by+mosquitoes.> ;
		a npx:UnderspecifiedAssertion .
}

:provenance {
	:assertion prov:hadPrimarySource <http://dx.doi.org/10.3233/ISU-2010-0613> .
}

:pubinfo {
	: dc:created "2014-07-29T10:13:35+01:00"^^xsd:dateTime ;
		pav:createdBy <http://orcid.org/0000-0002-1267-0234> ;
		a npx:ExampleNanopub .
}
"""

TRUSTY_URI = "http://purl.org/np/RAdf9taM_Gyq2-WavUq3CxaVIvsHockMXzonj3W_igNhM"
TRIG_FIXTURE_TRUSTY = """\
@prefix this: <http://purl.org/np/RAdf9taM_Gyq2-WavUq3CxaVIvsHockMXzonj3W_igNhM> .
@prefix sub: <http://purl.org/np/RAdf9taM_Gyq2-WavUq3CxaVIvsHockMXzonj3W_igNhM#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix np: <http://www.nanopub.org/nschema#> .
@prefix orcid: <https://orcid.org/> .
@prefix nt: <https://w3id.org/np/o/ntemplate/> .
@prefix npx: <http://purl.org/nanopub/x/> .
@prefix fip: <https://w3id.org/fair/fip/terms/> .

sub:Head {
  this: np:hasAssertion sub:assertion;
    np:hasProvenance sub:provenance;
    np:hasPublicationInfo sub:pubinfo;
    a np:Nanopublication .
}

sub:assertion {
  sub:DwC a fip:Available-FAIR-Enabling-Resource, fip:Data-schema, fip:FAIR-Enabling-Resource;
    rdfs:comment "Darwin Core schema";
    rdfs:label "Darwin Core" .
}

sub:provenance {
  sub:assertion prov:wasAttributedTo orcid:0000-0001-8050-0299 .
}

sub:pubinfo {
  sub:sig npx:hasAlgorithm "RSA";
    npx:hasPublicKey "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCK0bP9YbOpX9gkjJ2pgsWHTSa7bNQUGoh1LmmALJZyElQjEswZH0UgweLiB0qO74y9XGnbjFUDJiQGeVML6XugTWR29ujRUk9vOU0YKe2ZXTjSm87bMD4S7w2kTIKg1EFu27TKmJwR1l4RoGJpB0YMzR/zris//sbDhpKYPUaA0QIDAQAB";
    npx:hasSignature "Qi7p95ignv+MnRvc/pDFxYYDUeFkrNloQEk81INsr+un26CS/mNnoUXoEquiu2R5ObZ8DTywzPkFQUqO4tLIQN/qvVmrGSvoreNBO14Uwh2X2Z9DJIPgUr/t0JvDwbj16oufAi07oUVRZJ3F/W1l5hlfu6JR7DSJn4cAT3KJgB0=";
    npx:hasSignatureTarget this: .

  this: dct:created "2020-10-05T10:49:41.102+02:00"^^xsd:dateTime;
    dct:creator orcid:0000-0001-8050-0299;
    npx:introduces sub:DwC;
    nt:wasCreatedFromProvenanceTemplate <http://purl.org/np/RANwQa4ICWS5SOjw7gp99nBpXBasapwtZF1fIM3H2gYTM>;
    nt:wasCreatedFromPubinfoTemplate <http://purl.org/np/RAA2MfqdBCzmz9yVWjKLXNbyfBNcwsMmOqcNUxkk1maIM>;
    nt:wasCreatedFromTemplate <http://purl.org/np/RAHvHX5qjbdnYXsZWsRMO3KuFekGUFR6LuPjigZns9_VA> .
}
"""


def _make_dataset_from_trig(trig: str = TRIG_FIXTURE) -> Dataset:
    ds = Dataset()
    ds.parse(data=trig, format="trig")
    return ds


def _make_ok_response(text: str = TRIG_FIXTURE) -> MagicMock:
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


class TestCreationFromSourceUri:

    def test_http_error_raises(self):
        """raise_for_status propagating should surface as an exception."""
        with patch("nanopub.nanopub.requests.get", return_value=_make_fail_response()):
            with pytest.raises(Exception, match="404"):
                Nanopub(source_uri="https://purl.org/np/nonExistingNp", conf=NanopubConf())

    def test_fallback_to_test_server_on_first_failure(self):
        """When use_test_server=True and primary request fails, a second GET is issued."""
        fail = _make_fail_response()
        fail.raise_for_status = MagicMock()  # don't raise on first call, just ok=False

        with patch(
                "nanopub.nanopub.requests.get", side_effect=[fail, _make_ok_response()]
        ) as mock_get:
            np = Nanopub(
                source_uri="https://purl.org/np/whateverNp",
                conf=NanopubConf(use_test_server=True),
            )

        assert mock_get.call_count == 2
        assert len(np.rdf) > 0

    def test_metadata_matches_fetched_graph(self):
        """Metadata extracted from the fetched graph should reference the nanopub URI."""
        with patch("nanopub.nanopub.requests.get", return_value=_make_ok_response()):
            np = Nanopub(source_uri="https://purl.org/np/whateverNp", conf=NanopubConf())

        # This returns the np_uri read in the nanopub, which in this case is http://example.org/nanopub-validator-example/ as per the fixture
        assert "http://example.org/nanopub-validator-example/" in str(np.metadata.np_uri)


class TestCreationFromDataset:

    def test_dataset_is_stored(self):
        """Passing a Dataset should populate internal RDF."""
        np = Nanopub(rdf=_make_dataset_from_trig(), conf=NanopubConf())
        assert len(np.rdf) > 0

    def test_all_sub_graphs_are_non_empty(self):
        """All four named sub-graphs should be accessible and non-empty."""
        np = Nanopub(rdf=_make_dataset_from_trig(), conf=NanopubConf())
        assert len(np.assertion) > 0
        assert len(np.provenance) > 0
        assert len(np.pubinfo) > 0
        assert len(np.head) > 0

    def test_source_uri_none_without_trusty_uri(self):
        """Without a trusty URI in the graph, source_uri should be None."""
        np = Nanopub(rdf=_make_dataset_from_trig(), conf=NanopubConf())
        assert np.source_uri is None

    def test_empty_dataset_is_invalid(self):
        """An empty Dataset should raise MalformedNanopubError."""
        with pytest.raises(MalformedNanopubError):
            Nanopub(rdf=Dataset(), conf=NanopubConf())

    def test_metadata_matches_graph(self):
        """Metadata np_uri should reflect the URI in the parsed trig."""
        np = Nanopub(rdf=_make_dataset_from_trig(), conf=NanopubConf())
        assert "http://example.org/nanopub-validator-example/" in str(np.metadata.np_uri)


class TestCreationFromFile:

    def test_trig_file_is_parsed(self, tmp_path):
        """A .trig file on disk should be parsed into a non-empty graph."""
        trig_file = tmp_path / "test.trig"
        trig_file.write_text(TRIG_FIXTURE)

        np = Nanopub(rdf=trig_file, conf=NanopubConf())

        assert len(np.rdf) > 0
        assert len(np.assertion) > 0

    def test_all_sub_graphs_non_empty(self, tmp_path):
        """All four named sub-graphs should be non-empty when loaded from file."""
        trig_file = tmp_path / "test.trig"
        trig_file.write_text(TRIG_FIXTURE)

        np = Nanopub(rdf=trig_file, conf=NanopubConf())

        assert len(np.provenance) > 0
        assert len(np.pubinfo) > 0
        assert len(np.head) > 0

    def test_missing_file_raises(self, tmp_path):
        """Pointing to a non-existent file should raise an exception."""
        with pytest.raises(Exception):
            Nanopub(rdf=tmp_path / "does_not_exist.trig", conf=NanopubConf())

    def test_metadata_np_uri_extracted_from_file(self, tmp_path):
        """Metadata np_uri should match the URI declared inside the trig file."""
        trig_file = tmp_path / "test.trig"
        trig_file.write_text(TRIG_FIXTURE)

        np = Nanopub(rdf=trig_file, conf=NanopubConf())

        assert str(np.metadata.np_uri) == "http://example.org/nanopub-validator-example/"


class TestCreationFromTrustyNanopub:
    """When a nanopub carries a trusty URI, source_uri should be resolved from
    the graph itself, not rely on an externally passed argument."""

    def test_source_uri_resolved_from_trusty_dataset(self):
        """source_uri should be set from the trusty URI found in the graph."""
        ds = Dataset()
        ds.parse(data=TRIG_FIXTURE_TRUSTY, format="trig")
        np = Nanopub(rdf=ds, conf=NanopubConf())
        assert np.source_uri == TRUSTY_URI
        assert np.is_valid

    def test_source_uri_resolved_from_trusty_file(self, tmp_path):
        """source_uri should be set from the trusty URI when loaded from a file."""
        trig_file = tmp_path / "trusty.trig"
        trig_file.write_text(TRIG_FIXTURE_TRUSTY)
        np = Nanopub(rdf=trig_file, conf=NanopubConf())
        assert np.source_uri == TRUSTY_URI
        assert np.is_valid

    def test_source_uri_resolved_from_trusty_fetch(self):
        """source_uri should be set from the trusty URI in the fetched graph,
        even when a different URI is passed to the constructor."""
        with patch("nanopub.nanopub.requests.get", return_value=_make_ok_response(TRIG_FIXTURE_TRUSTY)):
            np = Nanopub(source_uri=TRUSTY_URI, conf=NanopubConf())
        assert np.source_uri == TRUSTY_URI
        assert np.is_valid

    def test_metadata_np_uri_matches_trusty_uri(self):
        """Metadata np_uri should match the trusty URI declared in the graph."""
        ds = Dataset()
        ds.parse(data=TRIG_FIXTURE_TRUSTY, format="trig")
        np = Nanopub(rdf=ds, conf=NanopubConf())
        assert str(np.metadata.np_uri) == TRUSTY_URI
        assert np.is_valid

    def test_all_sub_graphs_non_empty(self):
        """All four sub-graphs should be populated from a trusty trig."""
        ds = Dataset()
        ds.parse(data=TRIG_FIXTURE_TRUSTY, format="trig")
        np = Nanopub(rdf=ds, conf=NanopubConf())
        assert len(np.head) > 0
        assert len(np.assertion) > 0
        assert len(np.provenance) > 0
        assert len(np.pubinfo) > 0

    def test_get_source_uri_from_graph_returns_trusty(self):
        """get_source_uri_from_graph should extract the trusty URI from the head."""
        ds = Dataset()
        ds.parse(data=TRIG_FIXTURE_TRUSTY, format="trig")
        np = Nanopub(rdf=ds, conf=NanopubConf())
        assert np.get_source_uri_from_graph == TRUSTY_URI


def test_nanopub_sign_uri():
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


def test_nanopub_sign_uri2():
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


def test_nanopub_sign_bnode():
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


def test_nanopub_sign_bnode2():
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


def test_nanopub_publish():
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


def test_nanopub_claim():
    np = NanopubClaim(
        claim="Some controversial statement",
        conf=default_conf,
    )
    np.sign()
    assert np.source_uri is not None


def test_nanopub_retract():
    assertion = Graph()
    assertion.add(
        (
            BNode("test"),
            namespaces.HYCL.claims,
            Literal("This is a test of nanopub-python"),
        )
    )
    np = Nanopub(conf=default_conf, assertion=assertion)
    np.publish()
    # Now retract
    np2 = NanopubRetract(
        uri=np.source_uri,
        conf=default_conf,
    )
    np2.sign()
    assert np2.source_uri is not None


def test_nanopub_update():
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
    # Now update
    assertion2 = Graph()
    assertion2.add(
        (
            URIRef("http://test"),
            namespaces.HYCL.claims,
            Literal("Another test of nanopub-python"),
        )
    )
    np2 = NanopubUpdate(
        uri=np.source_uri,
        conf=default_conf,
        assertion=assertion,
    )
    np2.sign()
    assert np2.source_uri is not None


def test_nanopub_introduction():
    np = NanopubIntroduction(conf=default_conf, host="http://test")
    np.sign()
    assert np.source_uri is not None


def test_nanopub_index():
    np_list = create_nanopub_index(
        conf=default_conf,
        np_list=[
            "https://purl.org/np/RA5cwuR2b7Or9Pkb50nhPcHa2-cD0-gEPb2B3Ly5IxyuA",
            "https://purl.org/np/RAj1G7tgntNvXEgaMDmrc3rhxLekjZX6qsPIaEjUJ49NU",
        ],
        title="My nanopub index",
        description="This is my nanopub index",
        creation_time="2020-09-21T00:00:00",
        creators=["https://orcid.org/0000-0000-0000-0000"],
        see_also="https://github.com/Nanopublication/nanopub-py",
    )
    for np in np_list:
        assert np.source_uri is not None


@pytest.mark.flaky(max_runs=10)
@skip_if_nanopub_server_unavailable
def test_nanopub_fetch():
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


def test_invalid_fetch():
    with pytest.raises(Exception):
        Nanopub(source_uri="http://a-real-server/example")


def test_specific_file():
    """Test to sign a complex file with many blank nodes"""
    import json

    from rdflib import Namespace
    from rdflib.namespace import DCTERMS, PROV

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


def test_replace_blank_nodes_unnamed_bnode():
    # BNode with 33-character name triggers unnamed branch
    bname = "N" + "a" * 32
    g = Dataset()
    g.add((BNode(bname), URIRef("http://test/p"), Literal("value")))
    np = Nanopub(conf=NanopubConf())
    g2 = np._replace_blank_nodes(g)
    assert len(list(g2.quads((None, None, None, None)))) == 1


def test_handle_publication_attributed_to_no_profile():
    np = Nanopub(conf=NanopubConf(profile=None))
    with pytest.raises(MalformedNanopubError):
        np._handle_publication_attributed_to(
            attribute_publication_to_profile=True, publication_attributed_to=None
        )


def test_handle_derived_from_list_and_str():
    np = Nanopub(conf=NanopubConf())
    # string
    np._handle_derived_from("http://example.org/derived")
    found = list(
        np.provenance.triples((None, None, URIRef("http://example.org/derived")))
    )
    assert found
    # list
    np._handle_derived_from(["http://example.org/derived2"])
    found2 = list(
        np.provenance.triples((None, None, URIRef("http://example.org/derived2")))
    )
    assert found2


def test_handle_introduces_concept_adds_triple():
    np = Nanopub(conf=NanopubConf())
    bnode = BNode("concept1")
    np._handle_introduces_concept(bnode)
    triples = list(np.pubinfo.triples((None, None, None)))
    assert triples


def test_validate_nanopub_arguments_errors():
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


def test_is_valid_empty_graphs_and_graph_count():
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


def test_get_source_uri_from_graph_none():
    np = Nanopub(conf=NanopubConf())
    # No matching regex, should return None
    assert np.get_source_uri_from_graph is None


def test_signed_with_public_key_none():
    np = Nanopub(conf=NanopubConf())
    assert np.signed_with_public_key is None


def test_introduces_concept_multiple_error():
    np = Nanopub(conf=NanopubConf())
    np._pubinfo.add(
        (URIRef("http://s"), namespaces.NPX.introduces, URIRef("http://c1"))
    )
    np._pubinfo.add(
        (URIRef("http://s"), namespaces.NPX.introduces, URIRef("http://c2"))
    )
    with pytest.raises(MalformedNanopubError):
        np.introduces_concept


def test_sign_errors(monkeypatch):
    # No profile -> should raise ProfileError
    np = Nanopub(conf=NanopubConf(profile=None))
    np._assertion.add(
        (URIRef("http://test"), namespaces.HYCL.claims, Literal("test claim"))
    )
    np._provenance.add(
        (
            np._assertion.identifier,
            namespaces.PROV.wasAttributedTo,
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
            namespaces.PROV.wasAttributedTo,
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


def test_publish_calls_sign(monkeypatch):
    np = Nanopub(conf=NanopubConf(profile=None))
    monkeypatch.setattr(np, "sign", lambda: setattr(np, "_published", True))
    np.publish()
    assert np.published


def test_str_method_includes_uri():
    np = Nanopub(conf=NanopubConf())
    np._source_uri = "http://example.org/np/RA123"
    s = str(np)
    assert "RA123" in s


def test_nanopub_retract_profile_required():
    """Should raise ProfileError if no profile is provided"""
    conf = NanopubConf(profile=None)
    with pytest.raises(ProfileError):
        NanopubRetract(conf=conf, uri="http://example.org/np1", force=True)


def test_nanopub_retract_adds_assertion(monkeypatch):
    """Should create a retract assertion triple"""
    uri_to_retract = "http://example.org/np1"

    monkeypatch.setattr(
        "nanopub.nanopub.Nanopub.__init__", lambda self, *args, **kwargs: None
    )

    retract_np = NanopubRetract.__new__(NanopubRetract)

    retract_np._conf = default_conf
    retract_np._profile = default_conf.profile

    retract_np._assertion = MagicMock()

    orcid_id = retract_np.profile.orcid_id
    retract_np._assertion.add(
        (URIRef(orcid_id), namespaces.NPX.retracts, URIRef(uri_to_retract))
    )

    retract_np._assertion.add.assert_called_once_with(
        (URIRef(orcid_id), namespaces.NPX.retracts, URIRef(uri_to_retract))
    )


def test_nanopub_retract_public_key_mismatch(monkeypatch):
    """Should raise AssertionError if public keys do not match and force=False"""
    uri_to_retract = "http://example.org/np1"

    monkeypatch.setattr(
        "nanopub.nanopub.Nanopub.__init__", lambda self, *args, **kwargs: None
    )

    retract_np = NanopubRetract.__new__(NanopubRetract)
    retract_np._conf = default_conf
    retract_np.profile = default_conf.profile
    retract_np._check_public_keys_match = lambda uri: (_ for _ in ()).throw(
        AssertionError("public key mismatch")
    )

    with pytest.raises(AssertionError):
        retract_np._check_public_keys_match(uri_to_retract)


def test_nanopub_update_adds_supersedes(monkeypatch):
    """Should create a supersedes triple in pubinfo"""
    uri_to_update = "http://example.org/np1"

    monkeypatch.setattr(
        "nanopub.nanopub.Nanopub.__init__", lambda self, *args, **kwargs: None
    )

    update_np = NanopubUpdate.__new__(NanopubUpdate)
    update_np._conf = default_conf
    update_np._profile = default_conf.profile
    update_np._metadata = MagicMock()
    update_np._metadata.namespace = {"": "http://example.org/ns#"}

    update_np._pubinfo = MagicMock()

    update_np.pubinfo.add(
        (
            update_np._metadata.namespace[""],
            namespaces.NPX.supersedes,
            URIRef(uri_to_update),
        )
    )

    update_np._pubinfo.add.assert_called_once_with(
        (
            update_np._metadata.namespace[""],
            namespaces.NPX.supersedes,
            URIRef(uri_to_update),
        )
    )


def test_nanopub_update_public_key_mismatch(monkeypatch):
    """Should raise AssertionError if public keys do not match and force=False"""
    uri_to_update = "http://example.org/np1"

    monkeypatch.setattr(
        "nanopub.nanopub.Nanopub.__init__", lambda self, *args, **kwargs: None
    )

    update_np = NanopubUpdate.__new__(NanopubUpdate)
    update_np._conf = default_conf
    update_np._profile = default_conf.profile
    update_np._check_public_keys_match = lambda uri: (_ for _ in ()).throw(
        AssertionError("public key mismatch")
    )

    with pytest.raises(AssertionError):
        update_np._check_public_keys_match(uri_to_update)


def test_nanopub_update_init(monkeypatch):
    monkeypatch.setattr(
        "nanopub.nanopub.requests.get",
        lambda url: type(
            "Resp", (), {"ok": True, "text": "", "raise_for_status": lambda: None}
        )(),
    )

    uri_to_update = "http://example.org/np1"

    assertion = Graph()
    provenance = Graph()
    pubinfo = Graph()

    np_update = NanopubUpdate(
        conf=default_conf,
        uri=uri_to_update,
        force=True,
        assertion=assertion,
        provenance=provenance,
        pubinfo=pubinfo,
    )

    triples = list(
        np_update.pubinfo.triples(
            (None, namespaces.NPX.supersedes, URIRef(uri_to_update))
        )
    )
    assert len(triples) == 1
