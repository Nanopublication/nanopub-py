from copy import deepcopy
from typing import Optional

from rdflib import Literal, URIRef
from rdflib.namespace import FOAF

from nanopub.namespaces import NPX
from nanopub.nanopub import Nanopub
from nanopub.nanopub_conf import NanopubConf
from nanopub.profile import ProfileError


class NanopubIntroduction(Nanopub):
    """Publish a Nanopub introduction to introduce a key pair for an ORCID

    Args:
        conf: config for the nanopub
        host: the service where the keypair are hosted
    """

    def __init__(
        self,
        conf: NanopubConf,
        host: Optional[str] = None,
    ) -> None:
        conf = deepcopy(conf)
        conf.add_prov_generated_time = False
        conf.add_pubinfo_generated_time = True
        conf.attribute_publication_to_profile = True
        conf.attribute_assertion_to_profile = True
        super().__init__(
            conf=conf,
        )
        if not self.profile:
            raise ProfileError(
                "No profile provided, cannot generate a Nanopub Introduction"
            )

        key_declaration = self._metadata.namespace.keyDeclaration
        orcid_node = URIRef(self.conf.profile.orcid_id)

        self.assertion.add((key_declaration, NPX.declaredBy, orcid_node))
        self.assertion.add((key_declaration, NPX.hasAlgorithm, Literal("RSA")))
        self.assertion.add(
            (key_declaration, NPX.hasPublicKey, Literal(self.conf.profile.public_key))
        )
        self.assertion.add((orcid_node, FOAF.name, Literal(self.conf.profile.name)))
        if host:
            self.assertion.add((key_declaration, NPX.hasKeyLocation, URIRef(host)))
