# Publishing nanopublications

The `nanopub` library provides an intuitive API that makes publishing nanopublications much easier. The rationale is that you often do not want to worry about the details of composing the RDF that is often the same in each nanopublication. Instead you should focus on the content of your nanopublication: the assertion.


## 📜 A simple recipe to publish RDF triples

You can use `Nanopub` objects to easily publish nanopublications with your assertion (think of the assertion as the content of your nanopublication).


This is a 3-step recipe that works for most cases:

1. Create a `NanopubConf`
2. Construct a desired assertion using [`rdflib`](https://rdflib.readthedocs.io/en/stable/).
3. Make a `Nanopub` object from the assertion.
4. Publish the `Nanopub` object using `.publish()`.

Here is an example:
```python
import rdflib
from nanopub import Nanopub, NanopubConf, load_profile

# 1. Create the config (we use use_test_server=True to point to the test server)
np_conf = NanopubConf(
    profile=load_profile(),
    use_test_server=True,
    add_prov_generated_time=True,
    attribute_publication_to_profile=True,
)

# 2. Construct a desired assertion (a graph of RDF triples) using RDFLib
my_assertion = rdflib.Graph()
my_assertion.add((
    rdflib.URIRef('www.example.org/timbernerslee'),
    rdflib.RDF.type,
    rdflib.FOAF.Person
))

# 3. Make a Nanopub object with this assertion
np = Nanopub(
    conf=np_conf,
    assertion=my_assertion
)

# 4. Publish the Publication object.
np.publish()
print(np)
```
> View an example of resulting nanopublication [here](http://purl.org/np/RAfk_zBYDerxd6ipfv8fAcQHEzgZcVylMTEkiLlMzsgwQ).

You can also just sign the nanopub with `np.sign()`. Upon signing, or publishing, the `np` object will be automatically updated with the signed RDF and generated trusty URI.

This is the resulting assertion part of the nanopublication:

```turtle
@prefix sub: <http://purl.org/np/RAfk_zBYDerxd6ipfv8fAcQHEzgZcVylMTEkiLlMzsgwQ#> .

sub:assertion {
    <https://www.example.org/timbernerslee> a <http://xmlns.com/foaf/0.1/Person> .
}
```

The library automatically adds relevant RDF triples for the provenance part of the nanopublication:
```turtle
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix sub: <http://purl.org/np/RAfk_zBYDerxd6ipfv8fAcQHEzgZcVylMTEkiLlMzsgwQ#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

sub:provenance {
    sub:assertion prov:generatedAtTime "2020-12-01T10:44:32.367084"^^xsd:dateTime .
}
```
as well as for the publication info part of the nanopublication:
```turtle
@prefix npx: <http://purl.org/nanopub/x/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix sub: <http://purl.org/np/RAfk_zBYDerxd6ipfv8fAcQHEzgZcVylMTEkiLlMzsgwQ#> .
@prefix this: <http://purl.org/np/RAfk_zBYDerxd6ipfv8fAcQHEzgZcVylMTEkiLlMzsgwQ> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

sub:pubinfo {
    sub:sig npx:hasAlgorithm "RSA" ;
        npx:hasPublicKey "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCmso7vmRO/Cp4Pt0RkJJkV5qfc1WFYU/jMtkdxxb5+lfIVXNV97XQnM1Tj4fkb/W6jkP6fHl8mj8Q7hl7VgUnQ6I+B7cMGpxW9Z8Br+JNx8DPMMt08VCH5+JMENPRKl91r7rF/YPWCAgL9eqXSixCNMNAj5RBmMTQoPuRkpgmt1wIDAQAB" ;
        npx:hasSignature "aPZMJ3Md6X1PHYvXJiNoRUni9+1oS9faCfiPRRCrj4K/uZPN0J/znjxGuCUxoZRJ4b4RfSxmHFGRKfCFusJX+7Y3xuxYx4GYHzYhBciK7T5pO02V4w6sdwHLKd5E+Wcl0PTr2t3lEjq6yzY98wEXlZLAbaRDBJvzpg5xORifQDw=" ;
        npx:hasSignatureTarget this: .

    this: prov:generatedAtTime "2020-12-01T10:44:32.367084"^^xsd:dateTime ;
        prov:wasAttributedTo <https://orcid.org/0000-0000-0000-0000> .
}
```

## 📂 Publish from a file

You can also easily sign and publish a Nanopublication from a file.

```python
from rdflib import Dataset
from nanopub import Nanopub, NanopubConf, load_profile

# 1. Create the config
np_conf = NanopubConf(profile=load_profile(), use_test_server=True)

# 2. Load the file in a RDFLib graph
g = Dataset()
g.parse("nanopub.trig")

# 3. Make a Nanopublication object with this assertion
np = Nanopub(conf=np_conf, rdf=g)

# 4. Publish the Publication object.
np.publish()
print(np)
```

## 🖨️ Display more logs

You can change the log level of your logger to display more logs from the nanopub library, which can be help when debugging.

```python
import rdflib
from nanopub import Nanopub, NanopubConf, load_profile

# Instantiate the logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s: [%(module)s:%(funcName)s] %(message)s"
)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Usual workflow to publish nanopubs
np_conf = NanopubConf(
    profile=load_profile(),
    use_test_server=True,
    add_prov_generated_time=True,
    attribute_publication_to_profile=True,
)

my_assertion = rdflib.Graph()
my_assertion.add((
    rdflib.URIRef('www.example.org/timbernerslee'),
    rdflib.RDF.type,
    rdflib.FOAF.Person
))

np = Nanopub(
    conf=np_conf,
    assertion=my_assertion
)
np.publish()
print(np)
```

## ⚙️ Configure the nanopubs

The  `NanopubConf` class is used to create a reusable configuration for the nanopublications you create and publish. It enables you to define:

* which triples will be automatically added to the `provenance` and `pubinfo` graphs
* which user `Profile` to use
* to which server nanopubs will be published

```python
import rdflib
from nanopub import Nanopub, NanopubConf, load_profile

np_conf = NanopubConf(
    profile=load_profile(),

    # Define which server must be used (will be production by default)
    use_test_server=True,
    use_server="http://test-server.nanopubs.lod.labs.vu.nl",

    # Add at which date and time the nanopub was generated:
    add_prov_generated_time=True,
    add_pubinfo_generated_time=True,

    # Attribute the assertion or publication to your profile ORCID:
    attribute_assertion_to_profile=True,
    attribute_publication_to_profile= True,

    # Specify that the nanopub assertion is derived from another URI
    # (such as an existing nanopub):
    derived_from = "http://purl.org/np/RAfk_zBYDerxd6ipfv8fAcQHEzgZcVylMTEkiLlMzsgwQ"
)

# Usual workflow to build publish a nanopub
my_assertion = rdflib.Graph()
my_assertion.add((
    rdflib.URIRef('www.example.org/timbernerslee'),
    rdflib.RDF.type,
    rdflib.FOAF.Person
))
np = Nanopub(
    conf=np_conf,
    assertion=my_assertion
)
np.publish()
print(np)
```

You can also directly provide an ORCID to attribute the publication to, instead of using the user profile:

```python
from nanopub import NanopubConf, load_profile

creator_orcid = "https://orcid.org/0000-0000-0000-0000"

np_conf = NanopubConf(
    profile=load_profile(),
    use_test_server=True,
    use_server="http://test-server.nanopubs.lod.labs.vu.nl",
    add_prov_generated_time=True,
    add_pubinfo_generated_time=True,
    # Directly provide the ORCID:
    assertion_attributed_to = creator_orcid,
    publication_attributed_to = creator_orcid,
)
```
