import warnings
from unittest import mock

import pytest
from rdflib import FOAF, RDF, ConjunctiveGraph

from nanopub import Nanopub, NanopubClient
from nanopub.definitions import TEST_RESOURCES_FILEPATH
from tests.conftest import skip_if_nanopub_server_unavailable

client = NanopubClient(use_test_server=True)

PUBKEY = 'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCC686zsZaQWthNDSZO6unvhtSkXSLT8iSY/UUwD/' \
         '7T9tabrEvFt/9UPsCsg/A4HG6xeuPtL5mVziVnzbxqi9myQOY62LBja85pYLWaZPUYakP' \
         'HyVm9A0bRC2PUYZde+METkZ6eoqLXP26Qo5b6avPcmNnKkr5OQb7KXaeX2K2zQQIDAQAB'
NANOPUB_SAMPLE_SIGNED = str(TEST_RESOURCES_FILEPATH / 'nanopub_sample_signed.trig')


class TestNanopubClient:

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_nanopubs_with_text(self):
        """
        Check that Nanopub text search is returning results for a few common search terms
        """
        searches = ['test', 'US']

        for search in searches:
            results = list(client.find_nanopubs_with_text(search))
            assert len(results) > 0
        results = list(client.find_nanopubs_with_text(''))
        assert len(results) == 0

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_nanopubs_with_text_pubkey(self):
        results = list(client.find_nanopubs_with_text('test', pubkey=PUBKEY))
        assert len(results) > 0

        results = list(client.find_nanopubs_with_text('test', pubkey='wrong'))
        assert len(results) == 0

    @pytest.mark.flaky(max_runs=10)
    def test_find_nanopubs_with_text_prod(self):
        """
        Check that Nanopub text search is returning results for a few common search terms on the
        production nanopub server
        """
        prod_client = NanopubClient()
        searches = ['test', 'US']
        for search in searches:
            results = list(prod_client.find_nanopubs_with_text(search))
            assert len(results) > 0

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_nanopubs_with_text_json_not_returned(self):
        """
        Check that text search that triggers a virtuoso error is handled correctly. In such a
        case HTML is returned by the server rather than JSON.
        """
        results = client.find_nanopubs_with_text(
            'a string that is not in any of the nanopublications'
            ' and that virtuoso does not like')

        with pytest.raises(ValueError):
            list(results)

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_nanopubs_with_pattern(self):
        """
            Check that Nanopub pattern search is returning results
        """
        searches = [
            ('', RDF.type, FOAF.Person),
            ('http://purl.org/np/RA8ui7ddvV25m1qdyxR4lC8q8-G0yb3SN8AC0Bu5q8Yeg', '', '')
        ]

        for subj, pred, obj in searches:
            results = list(client.find_nanopubs_with_pattern(subj=subj, pred=pred, obj=obj))
            assert len(results) > 0
            assert 'Error' not in results[0]

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_nanopubs_with_pattern_pubkey(self):
        """
            Check that Nanopub pattern search is returning results
        """
        subj, pred, obj = (
            'http://purl.org/np/RA8ui7ddvV25m1qdyxR4lC8q8-G0yb3SN8AC0Bu5q8Yeg', '', '')
        results = list(client.find_nanopubs_with_pattern(subj=subj, pred=pred, obj=obj,
                                                         pubkey=PUBKEY))
        assert len(results) > 0

        results = list(client.find_nanopubs_with_pattern(subj=subj, pred=pred, obj=obj,
                                                         pubkey='wrong'))
        assert len(results) == 0

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_nanopub_find_things(self):
        """
        Check that Nanopub 'find_things' search is returning results
        """
        results = list(client.find_things(type='http://purl.org/net/p-plan#Plan'))
        assert len(results) > 0

        with pytest.raises(Exception):
            list(client.find_things())

        with pytest.raises(Exception):
            list(client.find_things(type='http://purl.org/net/p-plan#Plan', searchterm=''))

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_things_pubkey(self):
        results = list(client.find_things(type='http://purl.org/net/p-plan#Plan', pubkey=PUBKEY))
        assert len(results) > 0

        results = list(client.find_things(type='http://purl.org/net/p-plan#Plan', pubkey='wrong'))
        assert len(results) == 0

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_nanopub_find_things_empty_searchterm(self):
        """
        Check that Nanopub 'find_things' search raises exception if search string is empty
        """
        with pytest.raises(Exception):
            client.find_things(searchterm='')

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_things_filter_retracted(self):
        filtered_results = list(client.find_things(type='http://purl.org/net/p-plan#Plan',
                                                   filter_retracted=True))
        assert len(filtered_results) > 0
        all_results = list(client.find_things(type='http://purl.org/net/p-plan#Plan',
                                              filter_retracted=False))
        assert len(all_results) > 0
        # The filtered results should be a smaller subset of all the results, assuming that some of
        # the results are retracted nanopublications.
        assert len(all_results) > len(filtered_results)

    def test_find_retractions_of_publication_raise_warning(self):
        test_rdf = ConjunctiveGraph()
        test_rdf.parse(NANOPUB_SAMPLE_SIGNED, format='trig')

        # # A test publication
        # publication = Nanopub(rdf=test_rdf, source_uri='http://test-server/example')
        # assert publication.is_test_publication

        # # Production server client
        # client = NanopubClient(profile=profile_test, use_test_server=False)
        # client.find_nanopubs_with_pattern = mock.MagicMock()
        # # Because we try searching the prod server with a test publication this should trigger a
        # # warning.
        # with warnings.catch_warnings(record=True) as w:
        #     warnings.simplefilter("always")
        #     client.find_retractions_of(publication, valid_only=False)
        #     assert len(w) == 1

        # Not a test publication
        publication = Nanopub(rdf=test_rdf, source_uri='http://a-real-server/example')
        assert not publication.is_test_publication
        # Production server client
        client = NanopubClient(use_test_server=True)
        client.find_nanopubs_with_pattern = mock.MagicMock()
        # Because we try searching the prod server with a test publication this should trigger a
        # warning.
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            client.find_retractions_of(publication, valid_only=False)
            assert len(w) == 1


    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_retractions_of(self):
        uri = 'http://purl.org/np/RAnksi2yDP7jpe7F6BwWCpMOmzBEcUImkAKUeKEY_2Yus'
        results = client.find_retractions_of(uri, valid_only=False)
        expected_uris = [
            'http://purl.org/np/RAYhe0XddJhBsJvVt0h_aq16p6f94ymc2wS-q2BAgnPVY',
            'http://purl.org/np/RACdYpR-6DZnT6JkEr1ItoYYXMAILjOhDqDZsMVO8EBZI']
        for expected_uri in expected_uris:
            assert expected_uri in results

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_retractions_of_valid_only(self):
        uri = 'http://purl.org/np/RAnksi2yDP7jpe7F6BwWCpMOmzBEcUImkAKUeKEY_2Yus'
        # uri = 'http://purl.org/np/RAXUwamR3TGmJAPAJHiamh4sGCmYmzLG9jj-02HR0Ok0U'
        results = client.find_retractions_of(uri, valid_only=True)
        expected_uri = 'http://purl.org/np/RAYhe0XddJhBsJvVt0h_aq16p6f94ymc2wS-q2BAgnPVY'
        assert expected_uri in results
        # This is a nanopublication that is signed with a different public key than the nanopub
        # it retracts, so it is not valid and should not be returned.
        unexpected_uri = 'http://purl.org/np/RACdYpR-6DZnT6JkEr1ItoYYXMAILjOhDqDZsMVO8EBZI'
        assert unexpected_uri not in results

    @pytest.mark.parametrize(
        "test_input,expected",
        [   # Input with 'v'
            ({'np': {'value': 'test_nanopub_uri'},
              'v': {'value': 'test_description'},
              'date': {'value': '01-01-2001'}},
             {'np': 'test_nanopub_uri',
              'description': 'test_description',
              'date': '01-01-2001'}),
            # Input with 'description'
            ({'np': {'value': 'test_nanopub_uri'},
              'description': {'value': 'test_description'},
              'date': {'value': '01-01-2001'}},
             {'np': 'test_nanopub_uri',
              'description': 'test_description',
              'date': '01-01-2001'}),
            # Input without 'v' or 'description'
            ({'np': {'value': 'test_nanopub_uri'},
              'date': {'value': '01-01-2001'}},
             {'np': 'test_nanopub_uri',
              'description': '',
              'date': '01-01-2001'}),
            # Input without 'v' or 'description' and irrelevant fields
            ({'np': {'value': 'test_nanopub_uri'},
              'date': {'value': '01-01-2001'},
              'irrelevant': {'value': 'irrelevant_value'}},
             {'np': 'test_nanopub_uri',
              'description': '',
              'date': '01-01-2001'})
        ]
    )
    def test_parse_search_result(self, test_input, expected):
        assert client._parse_search_result(test_input) == expected

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_nanopub_fetch(self):
        """
        Check that Nanopub fetch is returning results for a few known nanopub URIs.
        """
        known_nps = [
            'http://purl.org/np/RANGY8fx_EYVeZzJOinH9FoY-WrQBerKKUy2J9RCDWH6U',
            'http://purl.org/np/RAABh3eQwmkdflVp50zYavHUK0NgZE2g2ewS2j4Ur6FHI',
            'http://purl.org/np/RA8to60YFWSVCh2n_iyHZ2yiYEt-hX_DdqbWa5yI9r-gI'
        ]

        for np_uri in known_nps:
            np = client.fetch(np_uri)
            assert isinstance(np, Nanopub)
            assert len(np.rdf) > 0
            assert np.assertion is not None
            assert np.pubinfo is not None
            assert np.provenance is not None
            assert len(np.__str__()) > 0
