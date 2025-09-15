import pytest
from rdflib import RDF, URIRef
import requests
from io import StringIO

from nanopub import NanopubClient
from nanopub.definitions import TEST_RESOURCES_FILEPATH
from tests.conftest import skip_if_nanopub_server_unavailable

PUBKEY = (
    "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCFJNRSo0AhDh7EfwM3nZXQbACb8v6F7tKGOj4Mnc/"
    "VuEu0CqzwyomaSvXmfwIKeHmCGCdIrL7tMes3U3K7qJ6c3m5j9U1SDBA+d6UDGvBKSN4X8vvRHzH+PNZyeg"
    "n3Wu+liXjq+4bnGdTdhPRdRFO9DjSb+rpAfaH21md4qRhCewIDAQAB"
)

NANOPUB_SAMPLE_SIGNED = str(TEST_RESOURCES_FILEPATH / "nanopub_sample_signed.trig")


# ----------------------
# Fixtures
# ----------------------
@pytest.fixture
def client():
    return NanopubClient(use_test_server=True)


@pytest.fixture
def prod_client():
    return NanopubClient(use_test_server=False)


# ----------------------
# Integration tests
# ----------------------
class TestNanopubClient:

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_nanopubs_with_text(self, client):
        searches = ["comment", "test"]

        for search in searches:
            results = list(client.find_nanopubs_with_text(search))
            assert len(results) > 0
        results = list(client.find_nanopubs_with_text(""))
        assert len(results) == 0

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_nanopubs_with_text_pubkey(self, client):
        results = list(client.find_nanopubs_with_text("user", pubkey=PUBKEY))
        assert len(results) > 0

        results = list(client.find_nanopubs_with_text("comment", pubkey="wrong"))
        assert len(results) == 0

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_nanopubs_with_text_prod(self, prod_client):
        searches = ["comment", "test"]
        for search in searches:
            results = list(prod_client.find_nanopubs_with_text(search))
            assert len(results) > 0

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_nanopubs_with_text_json_not_returned(self, client):
        results = client.find_nanopubs_with_text("\n abcdefghijklmnopqrs")
        with pytest.raises(ValueError):
            list(results)

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_nanopubs_with_pattern(self, client):
        searches = [
            ("", RDF.type, URIRef("http://www.w3.org/2002/07/owl#Thing")),
            (
                "https://w3id.org/np/RAO0soO0mUWTqqMaz1QcGbdIt90MJ55RXJck8w8wGGc0U",
                "",
                "",
            ),
        ]

        for subj, pred, obj in searches:
            results = list(
                client.find_nanopubs_with_pattern(subj=subj, pred=pred, obj=obj)
            )
            assert len(results) > 0
            assert "Error" not in results[0]

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_nanopubs_with_pattern_pubkey(self, client):
        subj, pred, obj = (
            "https://w3id.org/np/RAQUd7PYws4Hh5pCpvLRbHfh0piLS5PyfOQXnSGD5JctY",
            "",
            "",
        )
        results = list(
            client.find_nanopubs_with_pattern(
                subj=subj, pred=pred, obj=obj, pubkey=PUBKEY
            )
        )
        assert len(results) > 0

        results = list(
            client.find_nanopubs_with_pattern(
                subj=subj, pred=pred, obj=obj, pubkey="wrong"
            )
        )
        assert len(results) == 0

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_nanopub_find_things(self, prod_client):
        results = list(prod_client.find_things(type="http://purl.org/net/p-plan#Plan"))
        assert len(results) > 0

        with pytest.raises(Exception):
            list(prod_client.find_things())

        with pytest.raises(Exception):
            list(
                prod_client.find_things(
                    type="http://purl.org/net/p-plan#Plan", searchterm=""
                )
            )

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_nanopub_find_things_empty_searchterm(self, client):
        with pytest.raises(Exception):
            client.find_things(searchterm="")

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_things_filter_retracted(self, client):
        filtered_results = list(
            client.find_things(
                type="http://purl.org/net/p-plan#Plan",
                filter_retracted=True,
                searchterm="WF_protocol3",
            )
        )
        all_results = list(
            client.find_things(
                type="http://purl.org/net/p-plan#Plan",
                filter_retracted=False,
                searchterm="WF_protocol3",
            )
        )
        assert len(filtered_results) > 0
        assert len(all_results) > 0
        assert len(all_results) > len(filtered_results)

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_retractions_of(self, client):
        uri = "https://w3id.org/np/RAjwjgKTAHVVrdP0DCftOEbqi1FL-YPuf0r6xhwNgzDcU"
        results = client.find_retractions_of(uri, valid_only=False)
        expected_uri = (
            "https://w3id.org/np/RAuQdjy3pQhhPyda0hd1XXH4xH-XZ5Df3bW5RYCxxxK_U"
        )
        assert expected_uri in results

    @pytest.mark.flaky(max_runs=10)
    @skip_if_nanopub_server_unavailable
    def test_find_retractions_of_valid_only(self, client):
        uri = "https://w3id.org/np/RAjwjgKTAHVVrdP0DCftOEbqi1FL-YPuf0r6xhwNgzDcU"
        results = client.find_retractions_of(uri, valid_only=True)
        expected_uri = (
            "https://w3id.org/np/RAuQdjy3pQhhPyda0hd1XXH4xH-XZ5Df3bW5RYCxxxK_U"
        )
        assert expected_uri in results

    @pytest.mark.parametrize(
        "test_input,expected",
        [
            (
                {
                    "np": {"value": "test_nanopub_uri"},
                    "v": {"value": "test_description"},
                    "date": {"value": "01-01-2001"},
                },
                {
                    "np": "test_nanopub_uri",
                    "description": "test_description",
                    "date": "01-01-2001",
                },
            ),
            (
                {
                    "np": {"value": "test_nanopub_uri"},
                    "description": {"value": "test_description"},
                    "date": {"value": "01-01-2001"},
                },
                {
                    "np": "test_nanopub_uri",
                    "description": "test_description",
                    "date": "01-01-2001",
                },
            ),
            (
                {"np": {"value": "test_nanopub_uri"}, "date": {"value": "01-01-2001"}},
                {"np": "test_nanopub_uri", "description": "", "date": "01-01-2001"},
            ),
            (
                {
                    "np": {"value": "test_nanopub_uri"},
                    "date": {"value": "01-01-2001"},
                    "irrelevant": {"value": "irrelevant_value"},
                },
                {"np": "test_nanopub_uri", "description": "", "date": "01-01-2001"},
            ),
        ],
    )
    def test_parse_search_result(self, test_input, expected, client):
        assert client._parse_search_result(test_input) == expected


# ----------------------
# Dummy helpers for monkeypatch/unit tests
# ----------------------


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, text_data=None, reason="OK"):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text_data or ""
        self.reason = reason

    def json(self):
        return self._json


# ----------------------
# Unit tests
# ----------------------
def test_query_api_success(monkeypatch, client):
    def fake_get(url, params=None, headers=None):
        return DummyResponse(json_data={"ok": True})

    monkeypatch.setattr(requests, "get", fake_get)
    resp = client._query_api({"q": "x"}, "endpoint", "http://example.org/")
    assert resp.json()["ok"] is True


def test_query_api_returns_text(monkeypatch, client):
    def fake_get(url, params=None, headers=None):
        return DummyResponse(text_data="Hello World", status_code=200)

    monkeypatch.setattr(requests, "get", fake_get)
    resp = client._query_api({"q": "x"}, "endpoint", "http://example.org/")
    assert resp.text == "Hello World"


def test_find_retractions_raises_if_no_pubkey(monkeypatch, client):
    import nanopub.client as client_module

    class DummyNanopub:
        def __init__(self, source_uri=None, conf=None):
            self.signed_with_public_key = None
            self.is_test_publication = False
            self.source_uri = source_uri or "http://example.org/np"

    monkeypatch.setattr(client_module, "Nanopub", DummyNanopub)

    with pytest.raises(ValueError):
        client.find_retractions_of("http://example.org/np", valid_only=True)


def test_query_api_try_servers_502(monkeypatch, client):
    client.query_urls = ["server1", "server2"]
    calls = []

    class DummyResp:
        def __init__(self, status_code):
            self.status_code = status_code
            self.reason = "Bad Gateway"

        def raise_for_status(self):
            if self.status_code != 200:
                raise requests.HTTPError(f"{self.status_code} error")

    def fake_query_api(params, endpoint, query_url):
        calls.append(query_url)
        if query_url == "server1":
            return DummyResp(502)
        return DummyResp(200)

    monkeypatch.setattr(client, "_query_api", fake_query_api)

    resp, url = client._query_api_try_servers({}, "endpoint")
    assert resp.status_code == 200
    assert url == "server2"
    

def test_query_api_try_servers_all_fail(monkeypatch, client):
    class DummyResp:
        status_code = 500
        reason = "Internal Server Error"

        def raise_for_status(self):
            raise requests.HTTPError("fail")

    monkeypatch.setattr(client, "_query_api", lambda params, endpoint, url: DummyResp())
    with pytest.raises(requests.HTTPError):
        client._query_api_try_servers({}, "endpoint")


def test_query_api_parsed_and_csv(monkeypatch, client):
    csv_text = "a,b\n1,2\n3,4\n"
    monkeypatch.setattr(client, "_query_api_csv", lambda p, e, q: csv_text)
    rows = client._query_api_parsed({}, "endpoint", "http://dummy")
    assert rows == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]


def test_query_api_csv_raises(monkeypatch, client):
    class DummyResp:
        status_code = 200
        text = ""

        def raise_for_status(self):
            pass

        encoding = None

    monkeypatch.setattr(
        requests, "get", lambda url, params=None, headers=None: DummyResp()
    )
    # Should not raise
    client._query_api_csv({}, "endpoint", "http://dummy")


def test_find_retractions_of_warnings(monkeypatch, client):
    called = []

    class DummyNanopub:
        def __init__(self, source_uri=None, conf=None):
            self.signed_with_public_key = "pubkey"
            self.is_test_publication = True
            self.source_uri = source_uri or "http://example.org/np"

    monkeypatch.setattr("nanopub.client.Nanopub", DummyNanopub)

    def dummy_find(*args, **kwargs):
        called.append(args)
        return [{"np": "http://example.org/np1"}]

    monkeypatch.setattr(client, "find_nanopubs_with_pattern", dummy_find)

    client.use_test_server = False
    results = client.find_retractions_of(DummyNanopub())
    assert results == ["http://example.org/np1"]


def test_query_sparql_json_csv(monkeypatch, client):
    class DummyRes:
        def convert(self):
            return {"results": {"bindings": [{"a": {"value": "x"}}]}}

    class DummySPARQLWrapper:
        def __init__(self, url): pass
        def setQuery(self, q): pass
        def setReturnFormat(self, fmt): pass
        def query(self):
            return DummyRes()

    monkeypatch.setattr("nanopub.client.SPARQLWrapper", DummySPARQLWrapper)
    out = client.query_sparql("SELECT ?a WHERE {}", return_format="json")
    assert out == [{"a": "x"}]

    class DummyResCSV:
        def convert(self):
            return b"a,b\n1,2\n"

    class DummySPARQLWrapperCSV:
        def __init__(self, url): pass
        def setQuery(self, q): pass
        def setReturnFormat(self, fmt): pass
        def query(self):
            return DummyResCSV()

    monkeypatch.setattr("nanopub.client.SPARQLWrapper", DummySPARQLWrapperCSV)
    out_csv = client.query_sparql("SELECT ?a WHERE {}", return_format="csv")
    assert "a,b" in out_csv
