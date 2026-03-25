from nanopub import Nanopub
from nanopub.sign_utils import verify_trusty


class TestVerifyTrusty:

    def test_real_uri_returns_true(self):
        np = Nanopub(source_uri="https://w3id.org/np/RAAwn-ONPeKgxxWJNBDtVotYfZcFyppCy_z8ASy2mJLKY")
        assert verify_trusty(np.rdf, np.source_uri, np.namespace)
