import pytest
from nanopub.client import NanopubClient
from nanopub.fdo.fdo_query import FdoQuery

@pytest.fixture(scope="module")
def fdo_query():
    client = NanopubClient()
    return FdoQuery(client)

def test_text_search(fdo_query):
    results = list(fdo_query.text_search("test"))
    assert isinstance(results, list)
    for r in results:
        assert isinstance(r, dict)
        break  # just check the first item

def test_find_by_ref(fdo_query):
    results = list(fdo_query.find_by_ref("21.T11966/82045bd97a0acce88378"))
    assert isinstance(results, list)
    for r in results:
        assert isinstance(r, dict)
        break

def test_get_favorite_things(fdo_query):
    results = list(fdo_query.get_favorite_things("https://orcid.org/0000-0002-1267-0234"))
    assert isinstance(results, list)
    for r in results:
        assert isinstance(r, dict)
        break

def test_get_feed(fdo_query):
    results = list(fdo_query.get_feed("https://orcid.org/0009-0008-3635-347X"))
    assert isinstance(results, list)
    for r in results:
        assert isinstance(r, dict)
        break

def test_invalid_text_search(fdo_query):
    with pytest.raises(ValueError):
        fdo_query.text_search("")

def test_invalid_find_by_ref(fdo_query):
    with pytest.raises(ValueError):
        fdo_query.find_by_ref("")

def test_invalid_get_favorite_things(fdo_query):
    with pytest.raises(ValueError):
        fdo_query.get_favorite_things("")

def test_invalid_get_feed(fdo_query):
    with pytest.raises(ValueError):
        fdo_query.get_feed("")
