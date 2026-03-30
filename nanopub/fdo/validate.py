import json
from dataclasses import dataclass
from typing import List

import rdflib
import requests
from pyshacl import validate as _pyshacl_validate
from rdflib.namespace import SH

from nanopub.fdo.fdo_nanopub import FdoNanopub
from nanopub.fdo.fdo_record import FdoRecord
from nanopub.fdo.retrieve import resolve_in_nanopub_network
from nanopub.fdo.utils import convert_jsonschema_to_shacl, looks_like_handle, fix_numeric_shacl_constraints


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]


def _profile_landing_page_uri_to_api_url(uri: str) -> str:
    """
    Convert an FdoProfile landing page URI into a handle API URI unless it is already an API URI.

    Examples:
    - https://hdl.handle.net/21.T11966/996c38676da9ee56f8ab
      -> https://hdl.handle.net/api/handles/21.T11966/996c38676da9ee56f8ab

    - https://hdl.handle.net/api/handles/21.T11966/996c38676da9ee56f8ab
      -> returns as is
    """
    if uri.startswith("https://hdl.handle.net/api/handles/"):
        return uri  # Already API URL

    parts = uri.rstrip("/").split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid handle URI: {uri}")
    handle = "/".join(parts[-2:])
    api_url = f"https://hdl.handle.net/api/handles/{handle}"
    return api_url


def validate_fdo_record(record: FdoRecord, profile_np: FdoNanopub = None) -> ValidationResult:
    try:
        shape_graph = None

        if profile_np is not None:
            shape_graph = profile_np.assertion
        else:
            profile_uri = record.get_profile()
            if not profile_uri:
                return ValidationResult(False, ["FDO profile URI not found in record."], [])

            if looks_like_handle(profile_uri) or str(profile_uri).startswith("https://hdl.handle.net/"):
                api_url = _profile_landing_page_uri_to_api_url(str(profile_uri))
                resp = requests.get(api_url)
                if resp.status_code != 200:
                    return ValidationResult(False, [f"Could not fetch handle metadata for {api_url}"], [])
                metadata = resp.json()

                schema_entry = next(
                    (v for v in metadata.get("values", []) if v["type"].endswith("JsonSchema")),
                    None
                )
                if not schema_entry:
                    return ValidationResult(False, ["JSON Schema entry not found in FDO profile."], [])

                schema_str = schema_entry["data"]["value"]
                schema_json = json.loads(schema_str)
                shape_graph = convert_jsonschema_to_shacl(schema_json)

            else:
                profile_np = resolve_in_nanopub_network(profile_uri)
                if not profile_np:
                    return ValidationResult(False, [f"Could not resolve profile nanopub for {profile_uri}"], [])
                shape_graph = fix_numeric_shacl_constraints(profile_np.assertion)

        if shape_graph is None:
            return ValidationResult(False, ["SHACL shape graph could not be created."], [])

        graph = record.get_graph()
        _prev_normalize = rdflib.NORMALIZE_LITERALS
        try:
            conforms, results_graph, results_text = _pyshacl_validate(
                graph,
                shacl_graph=shape_graph,
                inference="rdfs",
                abort_on_first=False,
                meta_shacl=False,
                advanced=True,
                debug=False
            )
        finally:
            rdflib.NORMALIZE_LITERALS = _prev_normalize

        errors = [str(o) for s, p, o in results_graph.triples((None, SH.resultMessage, None))]
        return ValidationResult(conforms, errors, [])

    except Exception as e:
        return ValidationResult(False, [f"Validation error: {str(e)}"], [])
