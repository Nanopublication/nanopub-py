from rdflib import Graph, Literal, URIRef

from nanopub import Nanopub, namespaces
from nanopub.client import DUMMY_NAMESPACE
from nanopub.sign_utils import add_signature
from tests.conftest import default_conf, java_wrap, profile_test
import pytest

pytest.skip("Temporary skip: test file under refactor", allow_module_level=True)


def test_nanopub_sign():
    expected_np_uri = "http://purl.org/np/RAoXkQkJe_lpMhYW61Y9mqWDHa5MAj1o4pWIiYLmAzY50"

    assertion = Graph()
    assertion.add((
        URIRef('http://test'), namespaces.HYCL.claims, Literal('This is a test of nanopub-python')
    ))

    np = Nanopub(
        conf=default_conf,
        assertion=assertion
    )
    java_np = java_wrap.sign(np)

    np.sign()
    assert np.source_uri == expected_np_uri
    assert np.source_uri == java_np
