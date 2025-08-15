from unittest.mock import patch, MagicMock
from rdflib import Graph, URIRef
import pytest
from nanopub.fdo.fdo_record import FdoRecord
from nanopub.fdo.retrieve import NanopubConf
from nanopub.fdo.retrieve import (
    resolve_id,
    retrieve_record_from_id,
    retrieve_content_from_id,
    resolve_handle_metadata,
    get_fdo_uri_from_fdo_record,
    resolve_in_nanopub_network
)

@patch("nanopub.fdo.retrieve.resolve_in_nanopub_network")
def test_resolve_id_via_nanopub_network(mock_resolve):
    fake_np = MagicMock()
    fake_np.assertion = Graph()
    mock_resolve.return_value = fake_np

    record = resolve_id("some-iri")
    assert record is not None


@patch("nanopub.fdo.retrieve.FdoNanopub.handle_to_nanopub")
def test_resolve_id_with_handle(mock_handle):
    fake_np = MagicMock()
    fake_np.assertion = Graph()
    mock_handle.return_value = fake_np

    record = resolve_id("21.T11966/abc")
    assert record is not None


@patch("nanopub.fdo.retrieve.FdoNanopub.handle_to_nanopub")
def test_retrieve_record_from_id(mock_handle):
    fake_np = MagicMock()
    fake_np.assertion = Graph()
    mock_handle.return_value = fake_np

    record = retrieve_record_from_id("21.T11966/abc")
    assert record is not None


@patch("nanopub.fdo.retrieve.requests.get")
@patch("nanopub.fdo.retrieve.resolve_id")
def test_retrieve_content_from_id(mock_resolve_id, mock_requests_get):
    mock_response = MagicMock()
    mock_response.content = b"fake content"
    mock_response.raise_for_status = MagicMock()
    mock_requests_get.return_value = mock_response

    mock_record = MagicMock()
    mock_record.get_data_ref.return_value = "https://example.org/file.txt"
    mock_resolve_id.return_value = mock_record

    content = retrieve_content_from_id("21.T11966/fake")
    assert content == b"fake content"


@patch("nanopub.fdo.retrieve.requests.get")
def test_resolve_handle_metadata(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"values": []}
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    result = resolve_handle_metadata("21.T11966/abc")
    assert isinstance(result, dict)


def test_get_fdo_uri_from_fdo_record_returns_subject():
    g = Graph()
    uri = "https://example.org/fdo"
    g.add((URIRef(uri), URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), URIRef("https://w3id.org/fdo#FAIRDigitalObject")))
    result = get_fdo_uri_from_fdo_record(g)
    assert str(result) == uri

@patch("nanopub.fdo.retrieve.FdoNanopub.handle_to_nanopub")
def test_resolve_id_with_hdl_prefix(mock_handle):
    fake_np = MagicMock()
    fake_np.assertion = Graph()
    mock_handle.return_value = fake_np
    record = resolve_id("https://hdl.handle.net/21.T11966/test")
    assert isinstance(record, FdoRecord)


@patch("nanopub.fdo.retrieve.resolve_in_nanopub_network", return_value=None)
@patch("nanopub.fdo.retrieve.looks_like_handle", return_value=False)
def test_resolve_id_not_found(mock_looks_like_handle, mock_resolve):
    with pytest.raises(ValueError):
        resolve_id("nonexistent")


@patch("nanopub.fdo.retrieve.resolve_in_nanopub_network", side_effect=RuntimeError("boom"))
def test_resolve_id_exception_path(mock_resolve):
    with pytest.raises(ValueError) as excinfo:
        resolve_id("broken-id")
    assert "Could not resolve FDO" in str(excinfo.value)


@patch("nanopub.fdo.retrieve.Nanopub")
def test_resolve_in_nanopub_network_test_server_mode(mock_np):
    conf = NanopubConf(use_test_server=True)
    mock_np.return_value = "np-instance"
    result = resolve_in_nanopub_network("some-iri", conf=conf)
    assert result == "np-instance"
    mock_np.assert_called_once()


@patch("nanopub.fdo.retrieve.NanopubClient._query_api_parsed", return_value=None)
def test_resolve_in_nanopub_network_no_data(mock_query):
    result = resolve_in_nanopub_network("id")
    assert result is None


@patch("nanopub.fdo.retrieve.requests.get")
@patch("nanopub.fdo.retrieve.resolve_id")
def test_retrieve_content_from_id_list_case(mock_resolve_id, mock_get):
    mock_record = MagicMock()
    mock_record.get_data_ref.return_value = [
        URIRef("https://example.org/file1"),
        URIRef("https://example.org/file2"),
    ]
    mock_resolve_id.return_value = mock_record
    mock_resp = MagicMock(content=b"abc", raise_for_status=lambda: None)
    mock_get.return_value = mock_resp
    content_list = retrieve_content_from_id("some-id")
    assert content_list == [b"abc", b"abc"]


@patch("nanopub.fdo.retrieve.resolve_id")
def test_retrieve_content_from_id_no_data_ref(mock_resolve_id):
    mock_record = MagicMock()
    mock_record.get_data_ref.return_value = None
    mock_resolve_id.return_value = mock_record
    with pytest.raises(ValueError):
        retrieve_content_from_id("id")


@patch("nanopub.fdo.retrieve.resolve_id")
def test_retrieve_content_from_id_unexpected_type(mock_resolve_id):
    mock_record = MagicMock()
    mock_record.get_data_ref.return_value = 12345  
    mock_resolve_id.return_value = mock_record
    with pytest.raises(TypeError):
        retrieve_content_from_id("id")


def test_get_fdo_uri_from_fdo_record_fallback_subjects():
    g = Graph()
    uri = URIRef("https://example.org/other")
    g.add((uri, URIRef("p"), URIRef("o"))) 
    assert get_fdo_uri_from_fdo_record(g) == uri


def test_get_fdo_uri_from_fdo_record_none_case():
    g = Graph()
    assert get_fdo_uri_from_fdo_record(g) is None