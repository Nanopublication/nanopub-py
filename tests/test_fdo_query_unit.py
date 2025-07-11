import pytest
from unittest.mock import MagicMock
from nanopub.fdo.fdo_query import FdoQuery

@pytest.fixture
def mock_client():
    client = MagicMock()
    client._search.return_value = iter([{"id": 1}, {"id": 2}])
    return client

@pytest.fixture
def fdo_query(mock_client):
    return FdoQuery(mock_client)

def test_text_search_calls_search(mock_client, fdo_query):
    results = list(fdo_query.text_search("test"))
    mock_client._search.assert_called_once_with(
        "RAkYh4UPJryajbtIDbLG-Bfd6A4JD2SbU9bmZdvaEdFRY/fdo-text-search", {"query": "test"}
    )
    assert results == [{"id": 1}, {"id": 2}]

def test_find_by_ref_calls_search(mock_client, fdo_query):
    list(fdo_query.find_by_ref("abc123"))
    mock_client._search.assert_called_once_with(
        "RAQiQjx3OiO9ra9ImWl9kpuDpT8d3EiBSrftckOAAwGKc/find-fdos-by-ref", {"refid": "abc123"}
    )

def test_get_feed_calls_search(mock_client, fdo_query):
    list(fdo_query.get_feed("https://orcid.org/1234"))
    mock_client._search.assert_called_once_with(
        "RAP1G35VvTs3gfMaucv_xZUMZuvjB9lxM8tWUGttr5mmo/get-fdo-feed", {"creator": "https://orcid.org/1234"}
    )

def test_get_favorite_things_calls_search(mock_client, fdo_query):
    list(fdo_query.get_favorite_things("https://orcid.org/5678"))
    mock_client._search.assert_called_once_with(
        "RAsyc6zFFnE8mblnDfdCCNRsrcN1CSCBDW9I4Ppidgk9g/get-favorite-things", {"creator": "https://orcid.org/5678"}
    )

def test_text_search_raises_on_empty(fdo_query):
    with pytest.raises(ValueError, match="must not be empty"):
        fdo_query.text_search("")

def test_find_by_ref_raises_on_empty(fdo_query):
    with pytest.raises(ValueError, match="must not be empty"):
        fdo_query.find_by_ref("")

def test_get_feed_raises_on_empty(fdo_query):
    with pytest.raises(ValueError, match="must not be empty"):
        fdo_query.get_feed("")

def test_get_favorite_things_raises_on_empty(fdo_query):
    with pytest.raises(ValueError, match="must not be empty"):
        fdo_query.get_favorite_things("")
