import pytest
from rdflib import Graph, Literal, XSD, URIRef, SH
from nanopub.fdo.utils import (
    fix_numeric_shacl_constraints,
    looks_like_handle,
    looks_like_url,
    handle_to_iri,
    convert_jsonschema_to_shacl
)

def test_fix_numeric_shacl_constraints():
    g = Graph()
    s = URIRef("http://example.org/s")
    g.add((s, SH.minCount, Literal("5")))  # must be URIRef
    g2 = fix_numeric_shacl_constraints(g)
    for s, p, o in g2.triples((None, SH.minCount, None)):
        assert o.datatype == XSD.integer
        assert int(o) == 5

def test_looks_like_handle():
    assert looks_like_handle("12345")
    assert not looks_like_handle("http://example.com")

def test_handle_to_iri():
    iri = handle_to_iri("12345")
    assert str(iri).startswith("https://hdl.handle.net/12345")

def test_convert_jsonschema_to_shacl():
    schema = {"required": ["field1", "field2"]}
    g = convert_jsonschema_to_shacl(schema)
    assert len(list(g.subjects())) > 0
