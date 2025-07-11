from unittest.mock import patch, MagicMock
from rdflib import Graph, URIRef
from nanopub.fdo.retrieve import (
    resolve_id,
    retrieve_record_from_id,
    retrieve_content_from_id,
    resolve_handle_metadata,
    get_fdo_uri_from_fdo_record,
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
