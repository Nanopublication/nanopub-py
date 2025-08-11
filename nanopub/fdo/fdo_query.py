from typing import Iterator
from nanopub.client import NanopubClient


class FdoQuery:
    """
    A utility class to query FDO-specific endpoints, using a NanopubClient instance.
    """

    _endpoints = {
        "text_search": "RAkYh4UPJryajbtIDbLG-Bfd6A4JD2SbU9bmZdvaEdFRY/fdo-text-search",
        "find_by_ref": "RAQiQjx3OiO9ra9ImWl9kpuDpT8d3EiBSrftckOAAwGKc/find-fdos-by-ref",
        "get_feed": "RAP1G35VvTs3gfMaucv_xZUMZuvjB9lxM8tWUGttr5mmo/get-fdo-feed",
        "get_favorites": "RAsyc6zFFnE8mblnDfdCCNRsrcN1CSCBDW9I4Ppidgk9g/get-favorite-things",
    }

    def __init__(self, client: NanopubClient):
        self.client = client

    def text_search(self, query: str) -> Iterator[dict]:
        """Full-text search on FDO nanopublications."""
        if not query:
            raise ValueError("Query string must not be empty")
        return self.client._search(self._endpoints["text_search"], {"query": query})

    def find_by_ref(self, refid: str) -> Iterator[dict]:
        """Find FDOs that refer to the given PID/handle."""
        if not refid:
            raise ValueError("refid must not be empty")
        return self.client._search(self._endpoints["find_by_ref"], {"refid": refid})

    def get_feed(self, creator: str) -> Iterator[dict]:
        """Get FDOs published by the given creator (ORCID URL)."""
        if not creator:
            raise ValueError("creator must not be empty")
        return self.client._search(self._endpoints["get_feed"], {"creator": creator})

    def get_favorite_things(self, creator: str) -> Iterator[dict]:
        """Get favorite things (cito:likes) of the given creator."""
        if not creator:
            raise ValueError("creator must not be empty")
        return self.client._search(
            self._endpoints["get_favorites"], {"creator": creator}
        )
