import json
import pytest
from unittest.mock import patch, MagicMock
from rdflib import URIRef, Graph, Literal, BNode
from rdflib.namespace import DCTERMS, RDFS, RDF, SH
from nanopub.fdo.validate import validate_fdo_record
from nanopub.fdo.fdo_record import FdoRecord
from nanopub.fdo.fdo_nanopub import to_hdl_uri
from nanopub.namespaces import FDOF

FDO_HANDLE = "21.T11966/123456789abcdef"
DATAREF_HANDLE = "21.T11967/83d2b3f39034b2ac78cd"
HDL_PREFIX = "https://hdl.handle.net/"

HANDLE_METADATA = {
    "responseCode": 1,
    "handle": "21.T11966/996c38676da9ee56f8ab", 
    "values": [
        {
            "index": 3,
            "type": "21.T11966/JsonSchema",
            "data": {
                "format": "string",
                "value": '{"$ref": "https://example.org/schema/fdo.json"}',
            },
        }
    ],
}

HANDLE_METADATA_WITH_DATAREF = {
    "responseCode": 1,
    "handle": FDO_HANDLE,
    "values": [
        {
            "index": 1,
            "type": "21.T11966/name",
            "data": {"format": "string", "value": "FDO with DataRef"},
        },
        {
            "index": 2,
            "type": "21.T11966/FdoProfile",
            "data": {"format": "string", "value": "21.T11966/996c38676da9ee56f8ab"},
        },
        {
            "index": 3,
            "type": "21.T11966/JsonSchema",
            "data": {
                "format": "string",
                "value": '{"$ref": "https://example.org/schema/fdo.json"}',
            },
        },
        {
            "index": 4,
            "type": "21.T11966/06a6c27e3e2ef27779ec",
            "data": {"format": "string", "value": DATAREF_HANDLE},
        },
    ],
}

JSON_SCHEMA = {
    "type": "object",
    "required": [
        "21.T11966/FdoProfile",
        "21.T11966/b5b58656b1fa5aff0505"
    ]
}

@pytest.fixture
def valid_fdo_record():
    record = FdoRecord(
        profile_uri="21.T11966/996c38676da9ee56f8ab",
        label="Example FDO",
    )
    return record

@patch("nanopub.fdo.validate.resolve_in_nanopub_network")
@patch("nanopub.fdo.validate.requests.get")
def test_validate_fdo_record_success(mock_get, mock_resolve, valid_fdo_record):
    mock_resolve.return_value = None

    def mock_requests_get(url, *args, **kwargs):
        if "hdl.handle.net/api/handles/21.T11966/996c38676da9ee56f8ab" in url:
            return MagicMock(status_code=200, json=lambda: HANDLE_METADATA)
        elif "example.org/schema/fdo.json" in url:
            return MagicMock(status_code=200, json=lambda: JSON_SCHEMA)
        else:
            raise ValueError(f"Unexpected URL: {url}")

    mock_get.side_effect = mock_requests_get

    result = validate_fdo_record(valid_fdo_record)

    assert result.is_valid is True

@patch("nanopub.fdo.validate.resolve_in_nanopub_network")
@patch("nanopub.fdo.validate.requests.get")
def test_validate_fdo_record_failure(mock_get, mock_resolve, valid_fdo_record):
    mock_resolve.return_value = None
    
    incomplete_metadata = {
        "responseCode": 1,
        "handle": FDO_HANDLE,
        "values": [
            {
                "index": 2,
                "type": "21.T11966/FdoProfile",
                "data": {"format": "string", "value": "21.T11966/996c38676da9ee56f8ab"},
            },
            {
                "index": 1,
                "type": "name",
                "data": {"format": "string", "value": "Example FDO"},
            },
        ],
    }

    mock_get.side_effect = [
        MagicMock(status_code=200, json=lambda: incomplete_metadata),
        MagicMock(status_code=200, json=lambda: JSON_SCHEMA),
    ]

    result = validate_fdo_record(valid_fdo_record)
    assert result.is_valid is False
    assert "JSON Schema entry not found in FDO profile." in result.errors

@patch("nanopub.fdo.validate.requests.get")
@patch("nanopub.fdo.validate.resolve_in_nanopub_network")
def test_valid_fdo_from_nanopub_network(mock_resolve, mock_get):
    record_graph = Graph()
    subject = URIRef("https://example.org/fdo/1")
    record_graph.add((subject, RDF.type, FDOF.FAIRDigitalObject))
    record_graph.add((subject, URIRef("https://example.org/predicate"), Literal("Value")))
    record_graph.add((subject, DCTERMS.conformsTo, URIRef("https://hdl.handle.net/21.T11966/996c38676da9ee56f8ab")))
    fdo_record_nanopub = MagicMock()
    fdo_record_nanopub.assertion = record_graph

    profile_graph = Graph()
    profile_uri = URIRef("https://hdl.handle.net/21.T11966/996c38676da9ee56f8ab")

    shape = BNode()
    property_bnode = BNode()

    profile_graph.add((shape, RDF.type, SH.NodeShape))
    profile_graph.add((shape, SH.targetClass, FDOF.FAIRDigitalObject))
    profile_graph.add((shape, SH.property, property_bnode))
    profile_graph.add((property_bnode, SH.path, URIRef("https://example.org/predicate")))
    profile_graph.add((property_bnode, SH.minCount, Literal(1)))
    profile_graph.add((property_bnode, SH.maxCount, Literal(1)))

    fdo_profile_nanopub = MagicMock()
    fdo_profile_nanopub.assertion = profile_graph

    def resolve_side_effect(uri):
        if str(uri) == str(subject):
            return fdo_record_nanopub
        elif str(uri) == str(profile_uri):
            return fdo_profile_nanopub
        return None

    mock_resolve.side_effect = resolve_side_effect
    mock_get.return_value = MagicMock(status_code=404)  

    record = FdoRecord(assertion=record_graph)
    result = validate_fdo_record(record)

    assert result.is_valid is True
    assert result.errors == []


@patch("nanopub.fdo.validate.requests.get")
@patch("nanopub.fdo.validate.resolve_in_nanopub_network")
def test_invalid_fdo_from_nanopub_network(mock_resolve, mock_get):
    record_graph = Graph()
    subject = URIRef("https://example.org/fdo/2")
    record_graph.add((subject, RDF.type, FDOF.FAIRDigitalObject))
    record_graph.add((subject, DCTERMS.conformsTo, URIRef("https://hdl.handle.net/21.T11966/996c38676da9ee56f8ab")))
    fdo_record_nanopub = MagicMock()
    fdo_record_nanopub.assertion = record_graph

    profile_graph = Graph()
    profile_uri = URIRef("https://hdl.handle.net/21.T11966/996c38676da9ee56f8ab")

    shape = BNode()
    profile_graph.add((shape, RDF.type, SH.NodeShape))
    profile_graph.add((shape, SH.targetClass, FDOF.FAIRDigitalObject))

    property_bnode = BNode()
    profile_graph.add((shape, SH.property, property_bnode))
    profile_graph.add((property_bnode, SH.path, URIRef("https://example.org/predicate")))
    profile_graph.add((property_bnode, SH.minCount, Literal(1)))
    profile_graph.add((property_bnode, SH.maxCount, Literal(1)))

    fdo_profile_nanopub = MagicMock()
    fdo_profile_nanopub.assertion = profile_graph

    def resolve_side_effect(uri):
        if str(uri) == str(subject):
            return fdo_record_nanopub
        elif str(uri) == str(profile_uri):
            return fdo_profile_nanopub
        return None

    mock_resolve.side_effect = resolve_side_effect
    mock_get.return_value = MagicMock(status_code=404) 

    record = FdoRecord(assertion=record_graph)
    result = validate_fdo_record(record)

    assert result.is_valid is False
    assert any("predicate" in e.lower() for e in result.errors)
