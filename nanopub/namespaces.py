"""
This module holds handy namespaces that are often used in nanopublications.
"""

from rdflib import Namespace

NP = Namespace("http://www.nanopub.org/nschema#")
"""Nanopub namespace"""

NPX = Namespace("http://purl.org/nanopub/x/")
"""Nanopub/x namespace"""

NTEMPLATE = Namespace("https://w3id.org/np/o/ntemplate/")
"""Nanopub template namespace"""

PROV = Namespace("http://www.w3.org/ns/prov#")
"""Provenance Ontogoly (PROV-O) namespace"""

HYCL = Namespace("http://purl.org/petapico/o/hycl#")
"""HYCL namespace for claims and hypothesis"""

ORCID = Namespace("https://orcid.org/")
"""ORCID namespace"""

PAV = Namespace("http://purl.org/pav/")
"""Provenance And Versioning namespace"""

PMID = Namespace("http://www.ncbi.nlm.nih.gov/pubmed/")
"""PubMed namespace"""

HDL = Namespace("https://hdl.handle.net/")
"""Handle namespace"""

FDOF = Namespace("https://w3id.org/fdof/ontology#")
"""FAIR Digital Object Framework namespace"""

FDOC = Namespace("https://w3id.org/fdoc/o/terms/")
"""FDO Connect namespace"""
