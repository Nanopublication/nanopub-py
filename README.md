[![nanopub](https://img.shields.io/badge/rsd-nanopub-00a3e3.svg)](https://www.research-software.nl/software/nanopub)
[![Tests and update docs](https://github.com/Nanopublication/nanopub-py/actions/workflows/build.yml/badge.svg)](https://github.com/Nanopublication/nanopub-py/actions/workflows/build.yml) [![Publish to PyPI](https://github.com/Nanopublication/nanopub-py/actions/workflows/pypi.yml/badge.svg)](https://github.com/Nanopublication/nanopub-py/actions/workflows/pypi.yml)
[![Coverage Status](https://coveralls.io/repos/github/Nanopublication/nanopub-py/badge.svg)](https://coveralls.io/github/Nanopublication/nanopub-py)
[![PyPI version](https://badge.fury.io/py/nanopub.svg)](https://badge.fury.io/py/nanopub)
[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/4491/badge)](https://bestpractices.coreinfrastructure.org/projects/4491)
[![fair-software.eu](https://img.shields.io/badge/fair--software.eu-%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F-green)](https://fair-software.eu)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4336538.svg)](https://doi.org/10.5281/zenodo.4336538)
[![semantic-release: angular](https://img.shields.io/badge/semantic--release-angular-e10079?logo=semantic-release)](https://github.com/semantic-release/semantic-release)

# nanopub

The ```nanopub``` library provides a high-level, user-friendly Python interface for searching, publishing and
retracting nanopublications.

Nanopublications are a formalized and machine-readable way of communicating the smallest possible units of publishable
information. See [the documentation](https://nanopublication.github.io/nanopub-py/getting-started/what-are-nanopubs) for
more information.

# Documentation

Checkout the **[user documentation 📖 ](https://nanopublication.github.io/nanopub-py)**

# Setup

Install using pip:

```
pip install nanopub
```

To publish to the nanopublication network you need to set up your profile. This allows the nanopublication services to
identify you. Run the following command in the terminal:

```
np setup
```

This will ask you a few questions, then it will use that information to add and store RSA keys to sign your
nanopublications with, (optionally) publish a nanopublication with your name and ORCID iD to declare that you are using
these RSA keys, and store your ORCID iD to automatically add as author to the provenance of any nanopublication you will
publish using this library.

## Quick Start

### Publishing nanopublications

```python
from rdflib import Graph
from nanopub import Nanopub, NanopubConf, load_profile

# 1. Create the config
np_conf = NanopubConf(
    use_test_server=True,
    profile=load_profile(),  # Loads the user profile that was created with `np setup`
    add_prov_generated_time=True,
    attribute_publication_to_profile=True,
)

# 2. Construct a desired assertion (a graph of RDF triples) using rdflib
my_assertion = Graph()
my_assertion.add((
    rdflib.URIRef('www.example.org/timbernerslee'),
    rdflib.RDF.type,
    rdflib.FOAF.Person
))

# 2. Make a Nanopub object with this assertion
np = Nanopub(
    conf=np_conf,
    assertion=my_assertion
)

# 3. Publish the Nanopub object
np.publish()
print(np)
```

### Searching for nanopublications

```python
from nanopub import NanopubClient

# Search for all nanopublications containing the text 'fair'
client = NanopubClient()
results = client.find_nanopubs_with_text('fair')
print(results)
```

### Fetching nanopublications and inspecting them

```python
# Fetch the nanopublication at the specified URI
publication = client.fetch('http://purl.org/np/RApJG4fwj0szOMBMiYGmYvd5MCtRle6VbwkMJUb1SxxDM')

# Print the RDF contents of the nanopublication
print(publication)

# Iterate through all triples in the assertion graph
for s, p, o in publication.assertion:
    print(s, p, o)
```

## Development

See the [development page](https://nanopublication.github.io/nanopub-py/getting-started/development/) on the
documentation website.

## Tests

To run tests:

Install dependencies (if not already installed):

```
uv sync
```

Run tests:

```
uv run pytest
```

## Test coverage

Run the tests with coverage tracking:

```
uv run pytest --cov
```

View a terminal summary:

```
uv run coverage report
```

Or generate a detailed HTML report

```
uv run coverage html
```

## License

`nanopub` is free software under the Apache License.
See [LICENSE](https://github.com/Nanopublication/nanopub-py/blob/main/LICENSE).

## Copyright

- Copyright © 2020 Robin Richardson, Sven van der Burg
- Copyright © 2020-2025 the nanopub
  contributors (https://github.com/Nanopublication/nanopub-py/graphs/contributors)
- Copyright © 2025 Knowledge Pixels
- Copyright © 2025 acatech - Deutsche Akademie der Technikwissenschaften e.V.
