import requests
from nanopub import NanopubClient, Nanopub, NanopubConf
from nanopub.fdo.utils import looks_like_handle
from nanopub.fdo.fdo_record import FdoRecord
from nanopub.fdo import FdoNanopub
from rdflib import RDF, URIRef, Graph, Dataset
from nanopub.definitions import NANOPUB_FETCH_FORMAT
from nanopub.namespaces import FDOF
from typing import Tuple, Optional, Union, List

def resolve_id(iri_or_handle: str, conf: Optional[NanopubConf] = None) -> FdoRecord:
    try:
        np = resolve_in_nanopub_network(iri_or_handle, conf=conf)
        if np is not None:
            record = FdoRecord(assertion=np.assertion)
            return record

        if looks_like_handle(iri_or_handle):
            np = FdoNanopub.handle_to_nanopub(iri_or_handle)
            record = FdoRecord(assertion=np.assertion)
            return record

        if iri_or_handle.startswith("https://hdl.handle.net/"):
            handle = iri_or_handle.replace("https://hdl.handle.net/", "")
            np = FdoNanopub.handle_to_nanopub(handle)
            return FdoRecord(assertion=np.assertion)

    except Exception as e:
        raise ValueError(f"Could not resolve FDO: {iri_or_handle}") from e

    raise ValueError(f"FDO not found: {iri_or_handle}")



def resolve_in_nanopub_network(
    iri_or_handle: Union[str, URIRef],
    conf: Optional[NanopubConf] = None
) -> Optional[Nanopub]:

    query_id = "RAs0HI_KRAds4w_OOEMl-_ed0nZHFWdfePPXsDHf4kQkU"
    endpoint = "get-fdo-by-id"
    query_url = f"https://query.knowledgepixels.com/api/{query_id}/"

    if conf and conf.use_test_server:
        fetchConf = NanopubConf(use_test_server=True)
        return Nanopub(iri_or_handle, conf=fetchConf)

    data = NanopubClient()._query_api_parsed(
        params={"fdoid": str(iri_or_handle)},
        endpoint=endpoint,
        query_url=query_url,
    )

    if not data:
        return None

    np_uri = data[0].get("np")
    if not np_uri:
        return None

    try:
        # fetch .trig RDF
        r = requests.get(np_uri + ".trig", allow_redirects=True)
        r.raise_for_status()

        content_type = r.headers.get("Content-Type", "").lower()
        if "html" in content_type or r.text.lstrip().startswith("<!DOCTYPE html>"):
            # retry with the effective URL returned by the redirect - this is a dirty workaround for the server somehow returning html when redirecting (strips out the format suffix)
            redirected_url = r.url
            r = requests.get(redirected_url + ".trig")
            r.raise_for_status()

            np = Nanopub(source_uri=redirected_url)
        else:
            np = Nanopub(source_uri=np_uri)
        return np

    except Exception as e:
        raise ValueError(f"Could not fetch nanopub from URI: {np_uri}") from e


    

def retrieve_record_from_id(iri_or_handle: str):
    if looks_like_handle(iri_or_handle):
        np = FdoNanopub.handle_to_nanopub(iri_or_handle)
        return FdoRecord(assertion=np.assertion)
    else:
        raise NotImplementedError("Non-handle IRIs not yet supported")


def retrieve_content_from_id(iri_or_handle: str) -> Union[bytes, List[bytes]]:
    fdo_record = resolve_id(iri_or_handle)

    content_ref = fdo_record.get_data_ref()

    if not content_ref:
        raise ValueError("FDO has no file / DataRef (isMaterializedBy)")

    if isinstance(content_ref, URIRef) or isinstance(content_ref, str):
        if isinstance(content_ref, str):
            content_ref = URIRef(content_ref)
        response = requests.get(str(content_ref))
        response.raise_for_status()
        return response.content

    elif isinstance(content_ref, list):
        contents = []
        for uri in content_ref:
            response = requests.get(str(uri))
            response.raise_for_status()
            contents.append(response.content)
        return contents

    else:
        raise TypeError(f"Unexpected type for content_ref: {type(content_ref)}")


def resolve_handle_metadata(handle: str) -> dict:
    url = f"https://hdl.handle.net/api/handles/{handle}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_fdo_uri_from_fdo_record(assertion_graph: Graph) -> URIRef | None:
    for s, p, o in assertion_graph.triples((None, RDF.type, FDOF.FAIRDigitalObject)):
        if isinstance(s, URIRef):
            return s
    for s in assertion_graph.subjects():
        if isinstance(s, URIRef):
            return s
    return None