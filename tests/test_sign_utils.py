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

    # print("source URI", np.source_uri)
    # print("exp URI", expected_signed_np.source_uri)

    # print("source NS", np.namespace)
    # print("exp NS", expected_signed_np.namespace)
    assert np.source_uri == expected_signed_np.source_uri
