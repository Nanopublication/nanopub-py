import pytest
from nanopub.fdo.retrieve import resolve_id
from nanopub.fdo.validate import validate_fdo_record

@pytest.mark.parametrize("identifier", [
    "https://w3id.org/np/RAsSeIyT03LnZt3QvtwUqIHSCJHWW1YeLkyu66Lg4FeBk/nanodash-readme",
    "https://hdl.handle.net/21.T11966/82045bd97a0acce88378",
    "21.T11966/82045bd97a0acce88378",
])
def test_validate_fdo_records(identifier):
    fdo_record = resolve_id(identifier)
    assert fdo_record is not None

    validation_result = validate_fdo_record(fdo_record)
    print(f"Validation result for {identifier}: {validation_result}")

    assert validation_result.is_valid is True
    assert validation_result.errors == []
