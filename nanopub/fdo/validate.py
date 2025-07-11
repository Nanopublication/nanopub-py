import json
import requests
from pyshacl import validate
from rdflib import Graph
from nanopub.fdo.utils import convert_jsonschema_to_shacl, looks_like_handle
from nanopub.fdo.retrieve import resolve_in_nanopub_network
from nanopub.fdo.fdo_record import FdoRecord 
from nanopub.fdo.fdo_nanopub import FdoNanopub
from nanopub.namespaces import FDOC
from rdflib.namespace import SH
from typing import List
from dataclasses import dataclass

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


def validate_fdo_record(record: FdoRecord) -> ValidationResult:
    try:
        profile_uri = record.get_profile()
        if not profile_uri:
            return ValidationResult(False, ["FDO profile URI not found in record."], [])

        shape_graph = None

        if looks_like_handle(profile_uri):
            profile_nanopub = FdoNanopub.handle_to_nanopub(profile_uri)
            fdo_profile_uri = profile_nanopub.fdo_uri
            handle = str(fdo_profile_uri).replace("https://hdl.handle.net/", "").replace("hdl:", "")
            profile_api_url = f"https://hdl.handle.net/api/handles/{handle}"

            profile_response = requests.get(profile_api_url)
            profile_data = profile_response.json()

            jsonschema_entry = next(
                (v for v in profile_data.get("values", []) if v.get("type") == "21.T11966/JsonSchema"),
                None
            )
            if not jsonschema_entry:
                return ValidationResult(False, ["JSON Schema entry not found in FDO profile."], [])

            raw_value = jsonschema_entry["data"]["value"]
            parsed_value = json.loads(raw_value)
            jsonschema_url = parsed_value.get("$ref")
            if not jsonschema_url:
                return ValidationResult(False, ["JSON Schema $ref not found."], [])

            schema_response = requests.get(jsonschema_url)
            json_schema = schema_response.json()
            shape_graph = convert_jsonschema_to_shacl(json_schema)

        else:
            profile = resolve_in_nanopub_network(profile_uri)
            if profile:
                shape_graph = profile.assertion
            else:
                try:
                    profile_response = requests.get(profile_uri, headers={"Accept": "application/ld+json"})
                    if profile_response.status_code != 200:
                        return ValidationResult(False, [f"Failed to fetch profile: {profile_response.status_code}"], [])

                    profile_data = profile_response.json()
                    shape_uri = None
                    profile_uri_str = str(profile_uri)

                    for item in profile_data:
                        for node in item.get('@graph', []):
                            if node.get('@id') == profile_uri_str:
                                has_shape = node.get(str(FDOC.hasShape))
                                if isinstance(has_shape, list) and len(has_shape) > 0:
                                    shape_uri = has_shape[0].get('@id')
                                break
                        if shape_uri:
                            break

                    if not shape_uri:
                        return ValidationResult(False, ["No hasShape found in profile JSON-LD"], [])

                    shape_graph = Graph()
                    shape_graph.parse(shape_uri, format='json-ld')

                except Exception as e:
                    try:
                        profile_api_url = _profile_landing_page_uri_to_api_url(str(profile_uri))
                        profile_response = requests.get(profile_api_url)
                        profile_data = profile_response.json()

                        jsonschema_entry = next(
                            (v for v in profile_data.get("values", []) if v.get("type") == "21.T11966/JsonSchema"),
                            None
                        )
                        if not jsonschema_entry:
                            return ValidationResult(False, ["JSON Schema entry not found in FDO profile."], [])

                        raw_value = jsonschema_entry["data"]["value"]
                        parsed_value = json.loads(raw_value)
                        jsonschema_url = parsed_value.get("$ref")
                        if not jsonschema_url:
                            return ValidationResult(False, ["JSON Schema $ref not found."], [])

                        schema_response = requests.get(jsonschema_url)
                        json_schema = schema_response.json()
                        shape_graph = convert_jsonschema_to_shacl(json_schema)

                    except Exception as e2:
                        return ValidationResult(False, [f"Validation fallback error: {str(e2)}"], [])

        if shape_graph is None:
            return ValidationResult(False, ["SHACL shape graph could not be created."], [])

        graph = record.get_graph()
        conforms, results_graph, results_text = validate(
            graph,
            shacl_graph=shape_graph,
            inference='rdfs',
            abort_on_first=False,
            meta_shacl=False,
            advanced=True,
            debug=False
        )

        errors = []
        for s, p, o in results_graph.triples((None, SH.resultMessage, None)):
            errors.append(str(o))

        return ValidationResult(conforms, errors, [])

    except Exception as e:
        return ValidationResult(False, [f"Validation error: {str(e)}"], [])
