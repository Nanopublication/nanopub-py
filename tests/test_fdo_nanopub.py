import pytest
import rdflib
from rdflib import RDF, RDFS, DCTERMS
from nanopub.namespaces import HDL, FDOF, FDOC, NPX
from nanopub.fdo.fdo_nanopub import FdoNanopub, to_hdl_uri
from nanopub.constants import FDO_DATA_REF_HANDLE, FDO_PROFILE_HANDLE

FAKE_HANDLE = "21.T11966/test"
FAKE_URI = HDL[FAKE_HANDLE]
FAKE_LABEL = "Test Object"
FAKE_TYPE_JSON = '{"@type": "Dataset"}'
FAKE_STATUS = "active"
FAKE_ATTR_VALUE = rdflib.Literal("some value")
FAKE_ATTR_LABEL = "Test Attribute"


@pytest.mark.parametrize("fdo_id", [FAKE_HANDLE, HDL[FAKE_HANDLE]])
def test_initial_fdo_triples(fdo_id):
    fdo = FdoNanopub(fdo_id, FAKE_LABEL)
    fdo_uri = to_hdl_uri(fdo_id)

    assert (fdo_uri, RDF.type, FDOF.FAIRDigitalObject) in fdo.assertion
    assert (fdo_uri, RDFS.label, rdflib.Literal(FAKE_LABEL)) in fdo.assertion
    assert (fdo_uri, FDOF.hasMetadata, fdo.metadata.np_uri) in fdo.assertion
    assert (
        fdo.metadata.np_uri,
        RDFS.label,
        rdflib.Literal(f"FAIR Digital Object: {FAKE_LABEL}"),
    ) in fdo.pubinfo
    assert (fdo.metadata.np_uri, NPX.introduces, fdo_uri) in fdo.pubinfo


@pytest.mark.parametrize("fdo_profile", [FAKE_HANDLE, HDL[FAKE_HANDLE]])
def test_add_fdo_profile(fdo_profile):
    fdo = FdoNanopub(FAKE_HANDLE, FAKE_LABEL)
    uri = to_hdl_uri(fdo_profile)
    fdo.add_fdo_profile(fdo_profile)
    assert (fdo.fdo_uri, DCTERMS.conformsTo, uri) in fdo.assertion
    assert (
        HDL[FDO_PROFILE_HANDLE],
        RDFS.label,
        rdflib.Literal("FdoProfile"),
    ) in fdo.pubinfo


@pytest.mark.parametrize("data_ref", [FAKE_HANDLE, HDL[FAKE_HANDLE]])
def test_add_fdo_data_ref(data_ref):
    fdo = FdoNanopub(FAKE_HANDLE, FAKE_LABEL)
    uri = to_hdl_uri(data_ref)
    fdo.add_fdo_data_ref(data_ref)
    assert (fdo.fdo_uri, FDOF.isMaterializedBy, uri) in fdo.assertion
    assert (
        HDL[FDO_DATA_REF_HANDLE],
        RDFS.label,
        rdflib.Literal("DataRef"),
    ) in fdo.pubinfo


@pytest.mark.parametrize("attr_HANDLE", [FAKE_HANDLE, HDL[FAKE_HANDLE]])
def test_add_attribute_and_label(attr_HANDLE):
    fdo = FdoNanopub(FAKE_HANDLE, FAKE_LABEL)
    uri = to_hdl_uri(attr_HANDLE)
    fdo.add_attribute(attr_HANDLE, FAKE_ATTR_VALUE)
    fdo.add_attribute_label(attr_HANDLE, FAKE_ATTR_LABEL)
    assert (fdo.fdo_uri, uri, FAKE_ATTR_VALUE) in fdo.assertion
    assert (uri, RDFS.label, rdflib.Literal(FAKE_ATTR_LABEL)) in fdo.pubinfo
