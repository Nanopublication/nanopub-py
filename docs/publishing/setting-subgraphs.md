# Setting publication info and provenance
Here we show how you can control the publication info and provenance parts of the nanopublication.

## Specifying where the nanopublication is derived from
You can specify that the nanopub's assertion is derived from another URI (such as an existing nanopublication):
```python
from rdflib import URIRef, Graph, BNode, RDF, FOAF
from nanopub import Nanopub

my_assertion = Graph()
my_assertion.add((BNode('timbernserslee'), RDF.type, FOAF.Person))

np = Nanopub(
    assertion=my_assertion,
    conf=NanopubConf(
        add_prov_generated_time=True,
        add_pubinfo_generated_time=True,
        attribute_publication_to_profile=True,
        derived_from=URIRef('http://www.example.org/another-nanopublication'),
    )
)
```
Note that ```derived_from``` may also be passed a list of URIs.

The provenance part of the publication will denote:
```turtle
@prefix sub: <http://purl.org/nanopub/temp/mynanopub#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

:provenance {
    sub:assertion prov:wasDerivedFrom <http://www.example.org/another-nanopublication> .
}
```

## Attributing the assertion to someone
You can attribute the assertion to someone by specifying the `assertion_attributed_to` argument:
```python
from rdflib import URIRef, Graph, BNode, RDF, FOAF
from nanopub import Nanopub

my_assertion = Graph()
my_assertion.add((BNode('timbernserslee'), RDF.type, FOAF.Person))

np = Nanopub(
    assertion=my_assertion,
    conf=NanopubConf(
        add_prov_generated_time=True,
        add_pubinfo_generated_time=True,
        attribute_publication_to_profile=True,
        assertion_attributed_to=URIRef('https://orcid.org/0000-0000-0000-0001'),
    )
)
```

The provenance part of the publication will denote:
```turtle
@prefix : <http://purl.org/nanopub/temp/mynanopub#> .
@prefix prov: <http://www.w3.org/ns/prov#> .

:provenance {
    :assertion prov:wasAttributedTo <https://orcid.org/0000-0000-0000-0001> .
}
```
Note: Often the assertion should be attributed to yourself.

Instead of passing your ORCID iD to `assertion_attributed_to`, you can easily tell nanopub to attribute the assertion to the ORCID iD in your profile by setting `attribute_assertion_to_profile=True`.

## Specifying custom provenance triples
You can add your own triples to the provenance graph of the nanopublication by passing them in an `rdflib.Graph` object to the `provenance_rdf` argument:
```python
import rdflib
from nanopub import namespaces, Nanopub

my_assertion = rdflib.Graph()
my_assertion.add((rdflib.term.BNode('timbernserslee'), rdflib.RDF.type, rdflib.FOAF.Person))

provenance_rdf = rdflib.Graph()
provenance_rdf = provenance_rdf.add((
    BNode('timbernserslee'),
    namespaces.PROV.actedOnBehalfOf,
    BNode('markzuckerberg')
))

np = Nanopub(
    assertion=my_assertion,
    provenance_rdf=provenance_rdf,
    conf=NanopubConf(
        add_prov_generated_time=True,
        add_pubinfo_generated_time=True,
        attribute_publication_to_profile=True,
    )
)
```

## Specifying custom publication info triples
You can add your own triples to the publication info graph of the nanopublication by passing them in an `rdflib.Graph` object to the `pubinfo_rdf` argument:
```python
from rdflib import Graph, BNode, RDF, FOAF
from nanopub import namespaces, Nanopub

my_assertion = Graph()
my_assertion.add((BNode('timbernserslee'), RDF.type, FOAF.Person))

pubinfo_rdf = rdflib.Graph()
pubinfo_rdf = pubinfo_rdf.add((
    BNode('activity'),
    RDF.type,
    namespaces.PROV.Activity
))

np = Nanopub(
    assertion=my_assertion,
    pubinfo=pubinfo_rdf,
    conf=NanopubConf(
        add_prov_generated_time=True,
        add_pubinfo_generated_time=True,
        attribute_publication_to_profile=True,
    )
)
```
