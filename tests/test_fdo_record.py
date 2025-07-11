import pytest
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDFS, DCTERMS
from nanopub.namespaces import FDOF, FDOC
from nanopub.fdo.fdo_record import FdoRecord

PROFILE_URI = "https://hdl.handle.net/21.T11966/abc123"
DATAREF_URI = "https://hdl.handle.net/21.T11966/data456"
LABEL = "Example FDO"

def test_init_from_params():
    record = FdoRecord(profile_uri=PROFILE_URI, label=LABEL, dataref=DATAREF_URI)

    assert record.get_profile() == URIRef(PROFILE_URI)
    assert record.get_label() == LABEL
    assert record.get_data_ref() == URIRef(DATAREF_URI)
    assert record.get_id() == "abc123"
    subject = URIRef(f"https://hdl.handle.net/{record.get_id()}")
    assert (subject, DCTERMS.conformsTo, URIRef(PROFILE_URI)) in record.get_graph()

def test_init_missing_profile_raises():
    with pytest.raises(ValueError, match="profile_uri is required"):
        FdoRecord()

def test_init_from_graph():
    g = Graph()
    subj = URIRef("https://hdl.handle.net/21.T11966/abc123")
    g.add((subj, DCTERMS.conformsTo, URIRef(PROFILE_URI)))
    g.add((subj, RDFS.label, Literal(LABEL)))
    record = FdoRecord(assertion=g)

    assert record.get_profile() == URIRef(PROFILE_URI)
    assert record.get_label() == LABEL
    assert record.get_id() == "abc123"

def test_init_graph_missing_profile_raises():
    g = Graph()
    g.add((URIRef("https://hdl.handle.net/21.T11966/xyz"), RDFS.label, Literal("no profile")))
    with pytest.raises(ValueError, match="Missing required FDO profile statement"):
        FdoRecord(assertion=g)

def test_setters_and_getters():
    record = FdoRecord(profile_uri=PROFILE_URI)
    record.set_id("customid")
    record.set_label("New Label")
    record.set_data_ref(DATAREF_URI)
    record.set_property("http://example.org/custom", "value")

    assert record.get_id() == "customid"
    assert record.get_label() == "New Label"
    assert record.get_data_ref() == URIRef(DATAREF_URI)
    assert record.tuples[URIRef("http://example.org/custom")] == Literal("value")

def test_set_profile_fdof_flag():
    record = FdoRecord(profile_uri=PROFILE_URI)
    record.set_profile(PROFILE_URI, use_fdof=True)
    assert record.tuples[FDOC.hasFdoProfile] == URIRef(PROFILE_URI)

def test_graph_generation():
    record = FdoRecord(profile_uri=PROFILE_URI, label=LABEL, dataref=DATAREF_URI)
    g = record.get_graph()
    subj = URIRef("https://hdl.handle.net/abc123")

    assert (subj, DCTERMS.conformsTo, URIRef(PROFILE_URI)) in g
    assert (subj, RDFS.label, Literal(LABEL)) in g
    assert (subj, FDOF.isMaterializedBy, URIRef(DATAREF_URI)) in g

def test_add_aggregate():
    record = FdoRecord(profile_uri=PROFILE_URI)
    agg1 = URIRef("https://example.org/fdo/1")
    agg2 = URIRef("https://example.org/fdo/2")

    record.add_aggregate(agg1)
    record.add_aggregate(agg2)

    value = record.tuples[DCTERMS.hasPart]
    assert isinstance(value, list)
    assert agg1 in value
    assert agg2 in value

def test_copy_creates_independent_instance():
    record = FdoRecord(profile_uri=PROFILE_URI, label=LABEL)
    copied = record.copy()

    assert copied is not record
    assert copied.tuples == record.tuples
    assert copied.id == record.id
    copied.set_label("Changed")
    assert copied.get_label() != record.get_label()

def test_str_repr_output():
    record = FdoRecord(profile_uri=PROFILE_URI, label=LABEL)
    s = str(record)
    assert "Label: Example FDO" in s
    assert "Profile: https://hdl.handle.net/21.T11966/abc123" in s
