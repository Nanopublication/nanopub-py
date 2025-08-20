import pytest
from rdflib import RDF, URIRef

from nanopub import NanopubClient
from nanopub.definitions import TEST_RESOURCES_FILEPATH
from tests.conftest import skip_if_nanopub_server_unavailable

client = NanopubClient(use_test_server=True)
prod_client = NanopubClient(use_test_server=False)

PUBKEY = 'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCFJNRSo0AhDh7EfwM3nZXQbACb8v6F7tKGOj4Mnc/' \
    'VuEu0CqzwyomaSvXmfwIKeHmCGCdIrL7tMes3U3K7qJ6c3m5j9U1SDBA+d6UDGvBKSN4X8vvRHzH+PNZyeg' \
    'n3Wu+liXjq+4bnGdTdhPRdRFO9DjSb+rpAfaH21md4qRhCewIDAQAB'


NANOPUB_SAMPLE_SIGNED = str(TEST_RESOURCES_FILEPATH / 'nanopub_sample_signed.trig')


class TestNanopubClient:

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_nanopubs_with_text(self):
        """
        Check that Nanopub text search is returning results for a few common search terms
        """
        searches = ['comment', 'test']

        for search in searches:
            results = list(client.find_nanopubs_with_text(search))
            assert len(results) > 0
        results = list(client.find_nanopubs_with_text(''))
        assert len(results) == 0

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_nanopubs_with_text_pubkey(self):
        results = list(client.find_nanopubs_with_text('user', pubkey=PUBKEY))
        assert len(results) > 0

        results = list(client.find_nanopubs_with_text('comment', pubkey='wrong'))
        assert len(results) == 0

    @pytest.mark.flaky(max_runs=10)
    def test_find_nanopubs_with_text_prod(self):
        """
        Check that Nanopub text search is returning results for a few common search terms on the
        production nanopub server
        """
        prod_client = NanopubClient()
        searches = ['comment', 'test']
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
        results = client.find_nanopubs_with_text('\n abcdefghijklmnopqrs')

        with pytest.raises(ValueError):
            list(results)

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_nanopubs_with_pattern(self):
        """
            Check that Nanopub pattern search is returning results
        """
        searches = [
            ('', RDF.type, URIRef("http://www.w3.org/2002/07/owl#Thing")),
            ('https://w3id.org/np/RAO0soO0mUWTqqMaz1QcGbdIt90MJ55RXJck8w8wGGc0U', '', '')
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
            'https://w3id.org/np/RAQUd7PYws4Hh5pCpvLRbHfh0piLS5PyfOQXnSGD5JctY', '', '')
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
        results = list(prod_client.find_things(type='http://purl.org/net/p-plan#Plan'))
        assert len(results) > 0

        with pytest.raises(Exception):
            list(prod_client.find_things())

        with pytest.raises(Exception):
            list(prod_client.find_things(type='http://purl.org/net/p-plan#Plan', searchterm=''))

    # TODO: filtering by pubkey does not seem to be working on the production server
    # @pytest.mark.flaky(max_runs=10)
    # @skip_if_nanopub_server_unavailable
    # def test_find_things_pubkey(self):
    #     things_pubkey = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCoZmUKAHAF0CY2sKahOanR1V8wP62NOw3G0wcVLULWxqXB/        gcW25bGPcA5RKoiuhT6dUbfcRXmwLknE29h6KWfKYLtNaqdrHbjSnNC65dNmNxCNp0i6ZLZRh51mxw9IPJHZrDqQ9bcLwm9d1G1fDKasA+h1vrF3Hv1YrQsF9aW1QIDAQAB"
    #     results = list(prod_client.find_things(type='http://purl.org/net/p-plan#Step', pubkey=things_pubkey))
    #     assert len(results) > 0

    #     results = list(prod_client.find_things(type='http://purl.org/net/p-plan#Step', pubkey='wrong'))
    #     assert len(results) == 0

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_nanopub_find_things_empty_searchterm(self):
        """
        Check that Nanopub 'find_things' search raises exception if search string is empty
        """
        with pytest.raises(Exception):
            client.find_things(searchterm='')

    # TODO: find retracted in the new nanopub server to fix those tests

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_things_filter_retracted(self):
        filtered_results = list(
            client.find_things(
                type="http://purl.org/net/p-plan#Plan",
                filter_retracted=True,
                searchterm="WF_protocol3",
            )
        )
        assert len(filtered_results) > 0
        all_results = list(
            client.find_things(
                type="http://purl.org/net/p-plan#Plan",
                filter_retracted=False,
                searchterm="WF_protocol3",
            )
        )
        assert len(all_results) > 0
        # The filtered results should be a smaller subset of all the results, assuming that some of
        # the results are retracted nanopublications.
        assert len(all_results) > len(filtered_results)

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_retractions_of(self):
        uri = 'https://w3id.org/np/RAjwjgKTAHVVrdP0DCftOEbqi1FL-YPuf0r6xhwNgzDcU'
        results = client.find_retractions_of(uri, valid_only=False)
        expected_uri = 'https://w3id.org/np/RAuQdjy3pQhhPyda0hd1XXH4xH-XZ5Df3bW5RYCxxxK_U'
        assert expected_uri in results

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_retractions_of_valid_only(self):
        uri = 'https://w3id.org/np/RAjwjgKTAHVVrdP0DCftOEbqi1FL-YPuf0r6xhwNgzDcU'
        results = client.find_retractions_of(uri, valid_only=True)
        expected_uri = 'https://w3id.org/np/RAuQdjy3pQhhPyda0hd1XXH4xH-XZ5Df3bW5RYCxxxK_U'
        assert expected_uri in results
        # This is a nanopublication that is signed with a different public key than the nanopub
        # it retracts, so it is not valid and should not be returned.
        # TODO: re-enable this test when we have a non-valid retraction to check
        # unexpected_uri = 'http://purl.org/np/RACdYpR-6DZnT6JkEr1ItoYYXMAILjOhDqDZsMVO8EBZI'
        # assert unexpected_uri not in results

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
