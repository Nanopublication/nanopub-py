import logging

from rdflib import Graph, Literal, URIRef

from nanopub import Nanopub, NanopubConf, load_profile, namespaces

log = logging.getLogger()
log.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s: [%(module)s:%(funcName)s] %(message)s"
)
console_handler.setFormatter(formatter)
log.addHandler(console_handler)


conf = NanopubConf(
    add_prov_generated_time=False,
    add_pubinfo_generated_time=True,
    attribute_assertion_to_profile=True,
    attribute_publication_to_profile=True,
    profile=load_profile(),
    # use_test_server=True,
)

assertion = Graph()
assertion.add(
    (
        URIRef("http://test"),
        namespaces.HYCL.claims,
        Literal("This is a test for the nanopub python library"),
    )
)

np = Nanopub(conf=conf, assertion=assertion)

np.sign()
# np.publish()
print(np)
