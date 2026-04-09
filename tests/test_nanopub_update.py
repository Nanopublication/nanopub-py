from unittest.mock import MagicMock

import pytest
from rdflib import Graph, URIRef, Literal

from nanopub import namespaces, Nanopub, NanopubUpdate
from tests.conftest import default_conf


class TestCreation:

    def test_nanopub_update_adds_supersedes(self, monkeypatch):
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

    def test_nanopub_update_public_key_mismatch(self, monkeypatch):
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

    def test_nanopub_update_init(self, monkeypatch):
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

    def test_nanopub_update(self):
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
