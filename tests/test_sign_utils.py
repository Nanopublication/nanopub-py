from unittest.mock import MagicMock, patch

import pytest
from rdflib import Graph, Literal, URIRef, Dataset, Namespace

from nanopub import Nanopub, namespaces
from nanopub.sign_utils import verify_trusty
from tests.conftest import default_conf, java_wrap


class TestVerifyTrusty:

    def test_real_uri_returns_true(self):
        np = Nanopub(source_uri="https://w3id.org/np/RAYP7TG5JayGG1PvCTmv37Gjcfls2DFzdaXqLvpaCwsec")
        assert verify_trusty(np.rdf, np.source_uri, np.metadata.namespace)


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
