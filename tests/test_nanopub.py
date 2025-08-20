import pytest
from rdflib import BNode, Graph, Literal, URIRef

from nanopub import Nanopub, NanopubClaim, NanopubConf, NanopubRetract, NanopubUpdate, create_nanopub_index, namespaces
from nanopub.templates.nanopub_introduction import NanopubIntroduction
from tests.conftest import default_conf, profile_test, skip_if_nanopub_server_unavailable


def test_nanopub_sign_uri():
    expected_trusty = "RAIh8Oq-29dIVTZDhETpJ6f8oxxrILbZ3gSxkyAQY4220"
    assertion = Graph()
    assertion.add((
        URIRef('http://test'), namespaces.HYCL.claims, Literal('This is a test of nanopub-python')
    ))
    np = Nanopub(
        conf=default_conf,
        assertion=assertion
    )
    np.sign()
    assert np.has_valid_signature
    assert expected_trusty in np.source_uri



def test_nanopub_sign_uri2():
    expected_trusty = "RAIh8Oq-29dIVTZDhETpJ6f8oxxrILbZ3gSxkyAQY4220"
    np = Nanopub(
        conf=default_conf,
    )
    np.assertion.add((
        URIRef('http://test'), namespaces.HYCL.claims, Literal('This is a test of nanopub-python')
    ))
    np.sign()
    assert np.has_valid_signature
    assert expected_trusty in np.source_uri


def test_nanopub_sign_bnode():
    expected_trusty = "RAcU1AR3dS0ricV5G_ENcpUCk40XuCvFW3tVFqxNEQzT4"
    assertion = Graph()
    assertion.add((
        BNode('test'), namespaces.HYCL.claims, Literal('This is a test of nanopub-python')
    ))
    np = Nanopub(
        conf=default_conf,
        assertion=assertion
    )
    np.sign()
    assert np.has_valid_signature
    assert expected_trusty in np.source_uri


def test_nanopub_sign_bnode2():
    expected_trusty = "RA-1eE8scfVaiK7vP4CZueTyEyRmn1g2PpPf-j69WQAgM"
    assertion = Graph()
    assertion.add((
        BNode('test'), namespaces.HYCL.claims, Literal('This is a test of nanopub-python')
    ))
    assertion.add((
        BNode('test2'), namespaces.HYCL.claims, Literal('This is another test of nanopub-python')
    ))
    np = Nanopub(
        conf=default_conf,
        assertion=assertion
    )
    np.sign()
    assert expected_trusty in np.source_uri
    assert np.has_valid_signature

def test_nanopub_publish():
    expected_trusty = "RAIh8Oq-29dIVTZDhETpJ6f8oxxrILbZ3gSxkyAQY4220"
    assertion = Graph()
    assertion.add((
        URIRef('http://test'), namespaces.HYCL.claims, Literal('This is a test of nanopub-python')
    ))
    np = Nanopub(
        conf=default_conf,
        assertion=assertion
    )
    np.publish()
    assert np.has_valid_signature
    assert expected_trusty in np.source_uri



def test_nanopub_claim():
    np = NanopubClaim(
        claim='Some controversial statement',
        conf=default_conf,
    )
    np.sign()
    assert np.source_uri is not None


def test_nanopub_retract():
    assertion = Graph()
    assertion.add((
        BNode('test'), namespaces.HYCL.claims, Literal('This is a test of nanopub-python')
    ))
    np = Nanopub(
        conf=default_conf,
        assertion=assertion
    )
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
    assertion.add((
        URIRef('http://test'), namespaces.HYCL.claims, Literal('This is a test of nanopub-python')
    ))
    np = Nanopub(
        conf=default_conf,
        assertion=assertion
    )
    np.publish()
    # Now update
    assertion2 = Graph()
    assertion2.add((
        URIRef('http://test'), namespaces.HYCL.claims, Literal('Another test of nanopub-python')
    ))
    np2 = NanopubUpdate(
        uri=np.source_uri,
        conf=default_conf,
        assertion=assertion,
    )
    np2.sign()
    assert np2.source_uri is not None


def test_nanopub_introduction():
    np = NanopubIntroduction(
        conf=default_conf,
        host="http://test"
    )
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
        'https://w3id.org/np/RAQUd7PYws4Hh5pCpvLRbHfh0piLS5PyfOQXnSGD5JctY',
        'https://w3id.org/np/RAO0soO0mUWTqqMaz1QcGbdIt90MJ55RXJck8w8wGGc0U',
    ]
    for np_uri in known_nps:
        np = Nanopub(
            source_uri=np_uri,
            conf=NanopubConf(use_test_server=True)
        )
        assert len(np.rdf) > 0
        assert np.assertion is not None
        assert np.pubinfo is not None
        assert np.provenance is not None
        assert np.is_valid


def test_unvalid_fetch():
    try:
        publication = Nanopub(source_uri='http://a-real-server/example')
        assert publication.is_valid
    except Exception:
        assert True


def test_specific_file():
    """Test to sign a complex file with many blank nodes"""
    import json

    from rdflib import Namespace
    from rdflib.namespace import DCTERMS, PROV
    np_conf = NanopubConf(profile=profile_test, use_test_server=True)
    np_conf.add_prov_generated_time = True,
    np_conf.add_pubinfo_generated_time = True,
    np_conf.attribute_assertion_to_profile = True,
    np_conf.attribute_publication_to_profile = True,

    with open('./tests/resources/many_bnodes_with_annotations.json') as f:
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
        np.provenance.add((np.assertion.identifier, PROV.hadPrimarySource, URIRef(source)))

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
