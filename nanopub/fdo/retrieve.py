import requests
from nanopub import NanopubClient, Nanopub, NanopubConf
from nanopub.fdo.utils import looks_like_handle
from nanopub.fdo.fdo_record import FdoRecord
from nanopub.fdo import FdoNanopub
from rdflib import RDF, URIRef, Graph
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


def resolve_in_nanopub_network(iri_or_handle: str, conf: Optional[NanopubConf] = None) -> Optional[Nanopub]:
    query_id = "RAs0HI_KRAds4w_OOEMl-_ed0nZHFWdfePPXsDHf4kQkU"
    endpoint = "get-fdo-by-id"
    query_url = f"https://query.knowledgepixels.com/api/{query_id}/"
    np = None
    if conf is not None and conf.use_test_server:
        fetchConf = NanopubConf(
            use_test_server=True
        )
        np = Nanopub(iri_or_handle, conf=fetchConf)
    else:
        data = NanopubClient()._query_api_parsed(
            params={"fdoid": iri_or_handle},
            endpoint=endpoint,
            query_url=query_url,
        )
        if not data:
            return None
        else:
            np_uri = data[0].get("np")
            np = Nanopub(np_uri)
    if np is not None:
        return np
    return None
    
    

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