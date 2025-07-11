import pytest
from rdflib import URIRef, Graph, Literal
from unittest.mock import patch, MagicMock
from nanopub.fdo.fdo_record import FdoRecord
from nanopub.fdo.update import update_record
from nanopub.nanopub_conf import NanopubConf


@pytest.fixture
def sample_conf():
    conf = MagicMock(spec=NanopubConf)
    conf.profile.public_key = "test-public-key"
    return conf


@pytest.fixture
def sample_record():
    profile_uri = "https://hdl.handle.net/21.T11966/abc123"
    label = "Example FDO"
    dataref = "https://example.org/data/456"
    return FdoRecord(profile_uri=profile_uri, label=label, dataref=dataref)


@patch("nanopub.fdo.update.resolve_in_nanopub_network")
@patch("nanopub.fdo.update.NanopubUpdate")
def test_update_existing_nanopub(mock_update_cls, mock_resolve, sample_conf, sample_record):
    existing_npub = MagicMock()
    existing_npub.signed_with_public_key = sample_conf.profile.public_key
    existing_npub.source_uri = "https://example.org/np/existing"
    existing_npub.assertion = Graph()
    existing_npub.assertion.add((URIRef("http://example.org/s"), URIRef("http://example.org/p"), Literal("o")))

    mock_resolve.return_value = existing_npub

    mock_update = MagicMock()
    mock_update.publish.return_value = ("updated_uri", "updated_head", "updated_sig")
    mock_update_cls.return_value = mock_update

    result = update_record("https://hdl.handle.net/21.T11966/abc123", sample_record, publish=True, conf=sample_conf)

    mock_update_cls.assert_called_once()
    mock_update.sign.assert_called_once()
    mock_update.publish.assert_called_once()
    assert result == ("updated_uri", "updated_head", "updated_sig")


@patch("nanopub.fdo.update.resolve_in_nanopub_network")
def test_no_update_when_keys_differ(mock_resolve, sample_conf, sample_record):
    existing_npub = MagicMock()
    existing_npub.signed_with_public_key = "different-key"
    mock_resolve.return_value = existing_npub

    result = update_record("https://hdl.handle.net/21.T11966/abc123", sample_record, publish=True, conf=sample_conf)

    assert result == (None, None, None)


@patch("nanopub.fdo.update.resolve_in_nanopub_network")
@patch("nanopub.fdo.update.FdoNanopub.create_with_fdo_iri")
def test_create_new_nanopub_when_none_exists(mock_create, mock_resolve, sample_conf, sample_record):
    mock_resolve.return_value = None

    mock_np = MagicMock()
    mock_np.publish.return_value = ("new_uri", "new_head", "new_sig")
    mock_create.return_value = mock_np

    result = update_record("https://hdl.handle.net/21.T11966/abc123", sample_record, publish=True, conf=sample_conf)

    mock_create.assert_called_once_with(
        fdo_record=sample_record,
        fdo_iri="https://hdl.handle.net/21.T11966/abc123",
        data_ref=URIRef("https://example.org/data/456"),
        conf=sample_conf,
    )
    mock_np.publish.assert_called_once()
    assert result == ("new_uri", "new_head", "new_sig")
