import pytest
import rdflib
import json
from rdflib import RDF, RDFS, DCTERMS
from nanopub.namespaces import HDL, FDOF, FDOC, NPX
from nanopub.fdo.fdo_nanopub import FdoNanopub, to_hdl_uri 
from nanopub.constants import FDO_DATA_REF_HANDLE, FDO_PROFILE_HANDLE, FDO_DATA_REFS_HANDLE
from nanopub.fdo.fdo_record import FdoRecord

FAKE_HANDLE = "21.T11966/test"
FAKE_URI = HDL[FAKE_HANDLE]
FAKE_LABEL = "Test Object"
FAKE_TYPE_JSON = '{"@type": "Dataset"}'
FAKE_STATUS = "active"
FAKE_ATTR_VALUE = rdflib.Literal("some value")
FAKE_ATTR_LABEL = "Test Attribute"

def test_to_hdl_uri_with_uri_ref():
    uri_ref = rdflib.URIRef("hdl:21.T11966/test")
    result = to_hdl_uri(uri_ref)
    assert result == uri_ref  # should return unchanged


def test_to_hdl_uri_with_non_http_str():
    handle_str = "21.T11966/test"
    result = to_hdl_uri(handle_str)
    assert isinstance(result, rdflib.URIRef)
    assert str(result).endswith(handle_str)


def test_to_hdl_uri_with_http_str_raises():
    with pytest.raises(ValueError):
        to_hdl_uri("http://example.com")


def test_to_hdl_uri_with_invalid_type_raises():
    with pytest.raises(ValueError):
        to_hdl_uri(123)  
        
def test_init_with_fdo_profile():
    profile_handle = "21.T11966/profile"
    fdo = FdoNanopub("21.T11966/test", "Label", fdo_profile=profile_handle)
    profile_uri = to_hdl_uri(profile_handle)
    assert (fdo.fdo_uri, rdflib.namespace.DCTERMS.conformsTo, profile_uri) in fdo.assertion

def test_init_core_fdo_triples_no_profile():
    fdo = FdoNanopub("21.T11966/test", "NoProfile")
    assert isinstance(fdo, FdoNanopub)

@pytest.mark.parametrize("fdo_id", [FAKE_HANDLE, HDL[FAKE_HANDLE]])
def test_initial_fdo_triples(fdo_id):
    fdo = FdoNanopub(fdo_id, FAKE_LABEL)
    fdo_uri = to_hdl_uri(fdo_id)

    assert (fdo_uri, RDF.type, FDOF.FAIRDigitalObject) in fdo.assertion
    assert (fdo_uri, RDFS.label, rdflib.Literal(FAKE_LABEL)) in fdo.assertion
    assert (fdo_uri, FDOF.hasMetadata, fdo.metadata.np_uri) in fdo.assertion
    assert (fdo.metadata.np_uri, RDFS.label, rdflib.Literal(f"FAIR Digital Object: {FAKE_LABEL}")) in fdo.pubinfo
    assert (fdo.metadata.np_uri, NPX.introduces, fdo_uri) in fdo.pubinfo

@pytest.mark.parametrize("fdo_profile", [FAKE_HANDLE, HDL[FAKE_HANDLE]])
def test_add_fdo_profile(fdo_profile):
    fdo = FdoNanopub(FAKE_HANDLE, FAKE_LABEL)
    uri = to_hdl_uri(fdo_profile)
    fdo.add_fdo_profile(fdo_profile)
    assert (fdo.fdo_uri, DCTERMS.conformsTo, uri) in fdo.assertion
    assert (HDL[FDO_PROFILE_HANDLE], RDFS.label, rdflib.Literal("FdoProfile")) in fdo.pubinfo

@pytest.mark.parametrize("data_ref", [FAKE_HANDLE, HDL[FAKE_HANDLE]])
def test_add_fdo_data_ref(data_ref):
    fdo = FdoNanopub(FAKE_HANDLE, FAKE_LABEL)
    uri = to_hdl_uri(data_ref)
    fdo.add_fdo_data_ref(data_ref)
    assert (fdo.fdo_uri, FDOF.isMaterializedBy, uri) in fdo.assertion
    assert (HDL[FDO_DATA_REF_HANDLE], RDFS.label, rdflib.Literal("DataRef")) in fdo.pubinfo

@pytest.mark.parametrize("attr_HANDLE", [FAKE_HANDLE, HDL[FAKE_HANDLE]])
def test_add_attribute_and_label(attr_HANDLE):
    fdo = FdoNanopub(FAKE_HANDLE, FAKE_LABEL)
    uri = to_hdl_uri(attr_HANDLE)
    fdo.add_attribute(attr_HANDLE, FAKE_ATTR_VALUE)
    fdo.add_attribute_label(attr_HANDLE, FAKE_ATTR_LABEL)
    assert (fdo.fdo_uri, uri, FAKE_ATTR_VALUE) in fdo.assertion
    assert (uri, RDFS.label, rdflib.Literal(FAKE_ATTR_LABEL)) in fdo.pubinfo
    
@pytest.mark.parametrize("extra_entry", [
    {"type": FDO_DATA_REF_HANDLE, "data": {"value": "21.T11966/dataref"}},
    {"type": FDO_DATA_REFS_HANDLE, "data": {"value": json.dumps(["21.T11966/data1", "21.T11966/data2"])}},
    {"type": FDO_DATA_REFS_HANDLE, "data": {"value": "not-a-json"}},
    {"type": "customType", "data": {"value": "customValue"}},
    {"type": "HS_ADMIN", "data": {"value": "ignored"}},
])
def test_handle_to_nanopub_branches_minimal(monkeypatch, extra_entry):
    def fake_resolve_handle_metadata(handle):
        return {
            "values": [
                {"type": "name", "data": {"value": "TestLabel"}},
                {"type": FDO_PROFILE_HANDLE, "data": {"value": "21.T11966/profile"}},
                extra_entry,
            ]
        }

    monkeypatch.setattr("nanopub.fdo.retrieve.resolve_handle_metadata", fake_resolve_handle_metadata)

    np = FdoNanopub.handle_to_nanopub("21.T11966/test")
    assert isinstance(np, FdoNanopub)

    profile_uri = to_hdl_uri("21.T11966/profile")
    assert (np.fdo_uri, DCTERMS.conformsTo, profile_uri) in np.assertion

def test_handle_to_nanopub_with_missing_value(monkeypatch):
    def fake_resolve_handle_metadata(handle):
        return {"values": [{"type": "customType"}]} 
    
    monkeypatch.setattr("nanopub.fdo.retrieve.resolve_handle_metadata", fake_resolve_handle_metadata)
    np = FdoNanopub.handle_to_nanopub("21.T11966/test")
    assert isinstance(np, FdoNanopub)

def test_handle_to_nanopub_with_invalid_json(monkeypatch):
    extra_entry = {"type": FDO_DATA_REFS_HANDLE, "data": {"value": '{"bad_json": '}} 

    def fake_resolve_handle_metadata(handle):
        return {
            "values": [
                {"type": "name", "data": {"value": "TestLabel"}},
                {"type": FDO_PROFILE_HANDLE, "data": {"value": "21.T11966/profile"}},
                extra_entry,
            ]
        }

    monkeypatch.setattr("nanopub.fdo.retrieve.resolve_handle_metadata", fake_resolve_handle_metadata)
    np = FdoNanopub.handle_to_nanopub("21.T11966/test")
    assert isinstance(np, FdoNanopub)


def make_minimal_fdo_record(label="Label", profile_uri="21.T11966/profile", dataref=None):
    return FdoRecord(
        profile_uri=profile_uri,
        label=label,
        dataref=dataref
    )

def test_create_with_fdo_iri_minimal():
    record = make_minimal_fdo_record()
    data_ref_uri = rdflib.URIRef("hdl:21.T11966/data")

    np = FdoNanopub.create_with_fdo_iri(
        record,
        "hdl:21.T11966/test",
        data_ref=data_ref_uri
    )

    assert isinstance(np, FdoNanopub)
    assert (np.fdo_uri, FDOF.isMaterializedBy, data_ref_uri) in np.assertion

def test_create_with_fdo_iri_no_label(monkeypatch):
    record = make_minimal_fdo_record(label=None)
    monkeypatch.setattr(FdoNanopub, "add_fdo_data_ref", lambda self, val: None)
    np = FdoNanopub.create_with_fdo_iri(
        record,
        rdflib.URIRef("hdl:21.T11966/test")
    )
    assert str(np.fdo_uri).endswith("21.T11966/test")

def test_create_with_fdo_iri_no_dataref():
    record = make_minimal_fdo_record(dataref=None)
    np = FdoNanopub.create_with_fdo_iri(record, "hdl:21.T11966/test")
    assert isinstance(np, FdoNanopub)
    triples = list(np.assertion.triples((np.fdo_uri, FDOF.isMaterializedBy, None)))
    assert triples == []
    
def test_create_with_fdo_iri_with_list_values():
    record = make_minimal_fdo_record()
    record.tuples[rdflib.URIRef("hdl:custom_pred")] = [
        rdflib.Literal("a"),
        rdflib.Literal("b")
    ]    
    np = FdoNanopub.create_with_fdo_iri(record, "21.T11966/test")
    assert (np.fdo_uri, to_hdl_uri("custom_pred"), rdflib.Literal("a")) not in np.assertion 
    assert isinstance(np, FdoNanopub)
    
def test_create_aggregation_fdo_with_handles():
    agg_handles = ["21.T11966/data1", "21.T11966/data2"]
    np = FdoNanopub.create_aggregation_fdo(
        fdo_iri="21.T11966/agg",
        profile_uri="21.T11966/profile",
        label="Agg FDO",
        aggregates=agg_handles
    )
    assert isinstance(np, FdoNanopub)
        
def test_create_derivation_fdo_with_sources():
    sources = ["21.T11966/source1", "http://example.com/source2"]
    np = FdoNanopub.create_derivation_fdo(
        fdo_iri="21.T11966/der",
        profile_uri="21.T11966/profile",
        label="Der FDO",
        sources=sources
    )
    assert isinstance(np, FdoNanopub)