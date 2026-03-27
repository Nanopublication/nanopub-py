from pathlib import Path

import pytest
from nanopub_testsuite_connector import TestSuiteSubfolder
from rdflib import Dataset

from nanopub import Nanopub
from nanopub.utils import MalformedNanopubError
from tests.conftest import java_wrap, testsuite_conf, _suite


@pytest.mark.parametrize(
    "entry",
    _suite.get_valid(TestSuiteSubfolder.PLAIN),
    ids=lambda e: e.name,
)
def test_testsuite_valid_plain(entry):
    print(f"☑️ Testing valid plain nanopub: {entry.path}")

    np = Nanopub(
        conf=testsuite_conf,
        rdf=Path(entry.path)
    )
    assert np.is_valid


@pytest.mark.parametrize(
    "entry",
    _suite.get_valid(TestSuiteSubfolder.SIGNED),
    ids=lambda e: e.name,
)
def test_testsuite_valid_signed(entry):
    print(f"☑️ Testing valid signed nanopub: {entry.path}")

    np = Nanopub(conf=testsuite_conf, rdf=entry.path)
    assert np.metadata.trusty is not None
    assert np.metadata.signature is not None
    assert java_wrap.check_trusty_with_signature(np)
    assert np.is_valid
    assert np.has_valid_signature


@pytest.mark.parametrize(
    "entry",
    _suite.get_valid(TestSuiteSubfolder.TRUSTY),
    ids=lambda e: e.name,
)
def test_testsuite_valid_trusty(entry):
    print(f"☑️ Testing valid trusty nanopub: {entry.path}")

    np = Nanopub(conf=testsuite_conf, rdf=entry.path)
    assert np.metadata.trusty is not None
    assert np.has_valid_trusty
    assert np.is_valid


@pytest.mark.parametrize(
    "tc",
    _suite.get_transform_cases("rsa-key1"),
    ids=lambda tc: f"{tc.key_name}/{tc.plain.name}",
)
# we only test this with the rsa-key1 key, as the test_profile is set to sign with that key
def test_testsuite_sign_valid(tc):
    """Sign plain nanopubs and compare the trusty URI to that of the expected signed nanopub from the test suite (tc.signed)."""
    print(f'✒️ Testing signing: {tc.plain.name}')
    np_to_sign_dataset = Dataset()
    np_to_sign_dataset.parse(tc.plain.path)
    np_to_sign = Nanopub(conf=testsuite_conf, rdf=np_to_sign_dataset)
    np_to_sign.sign()
    assert np_to_sign.has_valid_signature
    assert np_to_sign.has_valid_trusty
    assert np_to_sign.is_valid

    np_expected_signed_dataset = Dataset()
    np_expected_signed_dataset.parse(tc.signed.path)
    np_expected_signed = Nanopub(conf=testsuite_conf, rdf=np_expected_signed_dataset)
    assert np_to_sign.source_uri == np_expected_signed.source_uri


@pytest.mark.parametrize(
    "tc",
    _suite.get_transform_cases(),
    ids=lambda tc: f"{tc.key_name}/{tc.plain.name}",
)
def test_testsuite_valid_signature(tc):
    print(f"✅ Testing validating signed nanopub: {tc.signed.path}")
    np = Nanopub(
        conf=testsuite_conf,
        rdf=Path(tc.signed.path)
    )
    assert java_wrap.check_trusty_with_signature(np)
    assert np.has_valid_signature
    assert np.has_valid_trusty
    assert np.is_valid


@pytest.mark.parametrize(
    "entry",
    _suite.get_invalid(TestSuiteSubfolder.PLAIN),
    ids=lambda e: e.name,
)
def test_testsuite_invalid_plain(entry):
    print(f"❎ Testing invalid nanopub: {entry.path}")

    with pytest.raises(MalformedNanopubError):
        np = Nanopub(conf=testsuite_conf, rdf=Path(entry.path))
        _ = np.is_valid
