import pytest
from typing import List
from nanopub.fdo.retrieve import (
    resolve_id,
    retrieve_record_from_id,
    retrieve_content_from_id,
    resolve_handle_metadata,
)

HANDLE_IRI = "https://hdl.handle.net/21.T11966/82045bd97a0acce88378"
HANDLE_PID = "21.T11975/7fcfec59-f27e-45a7-a9d1-8c9e0c64b064"
FDO_NANOPUB_IRI = "https://w3id.org/np/RAsSeIyT03LnZt3QvtwUqIHSCJHWW1YeLkyu66Lg4FeBk/nanodash-readme"
HANDLE_PID_WITH_DATAREF = '21.T11975/7fcfec59-f27e-45a7-a9d1-8c9e0c64b064'
HANDLE_PID_WITH_MULTIPLE_DATAREFS = '21.T11975/1686b432-dd80-4ec8-b8d7-be7fe1d06318'


@pytest.mark.network
def test_resolve_id_with_handle():
    record = resolve_id(HANDLE_PID)
    assert record.get_profile() is not None


@pytest.mark.network
def test_retrieve_record_from_id():
    record = retrieve_record_from_id(HANDLE_PID)
    assert record.get_profile() is not None


@pytest.mark.network
def test_retrieve_content_from_fdo_nanopub_id():
    content = retrieve_content_from_id(FDO_NANOPUB_IRI)
    assert isinstance(content, bytes)
    assert len(content) > 0
    
@pytest.mark.network
def test_retrieve_content_from_handle():
    content = retrieve_content_from_id(HANDLE_PID_WITH_DATAREF)
    assert isinstance(content, bytes)
    assert len(content) > 0
    
@pytest.mark.network
def test_retrieve_content_from_handle_multiple_datarefs():
    content = retrieve_content_from_id(HANDLE_PID_WITH_MULTIPLE_DATAREFS)
    assert isinstance(content, List)
    assert len(content) > 0
    for c in content:
        assert isinstance(c, bytes)
        assert len(c) > 0


@pytest.mark.network
def test_resolve_handle_metadata():
    result = resolve_handle_metadata(HANDLE_PID)
    assert "values" in result
