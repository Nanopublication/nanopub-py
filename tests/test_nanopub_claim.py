from nanopub import NanopubClaim
from tests.conftest import default_conf


class TestCreation:

    def test_create_with_claim(self):
        np = NanopubClaim(
            claim="Some controversial statement",
            conf=default_conf,
        )
        np.sign()
        assert np.source_uri is not None
        assert np.assertion is not None
        assert np.provenance is not None
        assert np.pubinfo is not None
