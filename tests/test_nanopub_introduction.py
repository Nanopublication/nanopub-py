from nanopub import NanopubIntroduction
from tests.conftest import default_conf


class TestCreation:

    def test_nanopub_introduction(self):
        np = NanopubIntroduction(conf=default_conf, host="http://test")
        np.sign()
        assert np.source_uri is not None
