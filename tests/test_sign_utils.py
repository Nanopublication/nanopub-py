from pathlib import Path

import pytest

from nanopub import Nanopub
from tests.conftest import _suite, testsuite_conf


@pytest.mark.parametrize(
    "tc",
    _suite.get_transform_cases("rsa-key1"),
    ids=lambda tc: f"{tc.key_name}/{tc.plain.name}",
)
def test_nanopub_sign(tc):
    np = Nanopub(
        conf=testsuite_conf,
        rdf=Path(tc.plain.path)
    )
    np.sign()

    expected_signed_np = Nanopub(
        conf=testsuite_conf,
        rdf=Path(tc.signed.path)
    )

    assert np.source_uri == expected_signed_np.source_uri
    assert np.metadata.trusty == expected_signed_np.metadata.trusty
    assert np.metadata.public_key == expected_signed_np.metadata.public_key
    assert set(np.rdf) == set(expected_signed_np.rdf)
