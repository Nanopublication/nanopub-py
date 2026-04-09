from unittest.mock import MagicMock

import pytest
from rdflib import URIRef, Graph, BNode, Literal

from nanopub import NanopubConf, NanopubRetract, namespaces, Nanopub
from nanopub.profile import ProfileError
from tests.conftest import default_conf


class TestCreation:

    def test_nanopub_retract_profile_required(self):
        """Should raise ProfileError if no profile is provided"""
        conf = NanopubConf(profile=None)
        with pytest.raises(ProfileError):
            NanopubRetract(conf=conf, uri="http://example.org/np1", force=True)

    def test_nanopub_retract_adds_assertion(self, monkeypatch):
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

    def test_nanopub_retract_public_key_mismatch(self, monkeypatch):
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

    def test_nanopub_retract(self):
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
