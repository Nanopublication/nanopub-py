from copy import deepcopy
from pathlib import Path
from typing import Union

from rdflib import Dataset, Graph, URIRef

from nanopub.namespaces import NPX
from nanopub.nanopub import Nanopub
from nanopub.nanopub_conf import NanopubConf
from nanopub.profile import ProfileError
from nanopub.utils import MalformedNanopubError


# TODO: improve to better inherit from the nanopub we want to update
class NanopubUpdate(Nanopub):
    """Update a nanopublication.

    Publish a retraction nanpublication that declares retraction of the nanopublication that
    corresponds to the 'uri' argument.

    Args:
        conf: config for the nanopub
        uri (str): The uri pointing to the to-be-retracted nanopublication
        force (bool): Toggle using force to retract, this will even retract the
            nanopublication if it is signed with a different public key than the one
            in the user profile.
    """

    def __init__(
        self,
        conf: NanopubConf,
        uri: str,
        force: bool = False,
        assertion: Graph = Graph(),
        provenance: Graph = Graph(),
        pubinfo: Graph = Graph(),
        rdf: Union[Dataset, Path] = None,
    ) -> None:
        conf = deepcopy(conf)
        conf.add_prov_generated_time = True
        conf.add_pubinfo_generated_time = True
        conf.attribute_publication_to_profile = True
        conf.attribute_assertion_to_profile = True
        super().__init__(
            conf=conf,
            assertion=assertion,
            provenance=provenance,
            pubinfo=pubinfo,
            rdf=rdf,
        )
        if not self.profile:
            raise ProfileError("No profile provided, cannot generate a Nanopub to retract another nanopub")

        if not force:
            self._check_public_keys_match(uri)

        self.pubinfo.add(
            (self._metadata.namespace[""], NPX.supersedes, URIRef(uri))
        )


    def _check_public_keys_match(self, uri):
        """Check for matching public keys of a nanopublication with the profile.

        Raises:
            AssertionError: When the nanopublication is signed with a public key that does not
                match the public key in the profile
        """
        np = Nanopub(
            uri,
            conf=NanopubConf(
                use_test_server=self._conf.use_test_server,
                use_server=self._conf.use_server,
            )
        )
        if np.metadata.public_key is None:
            raise MalformedNanopubError(f"Public key not found in the nanopub {np.source_uri}")
        if self._conf.profile.public_key is None:
            raise ValueError(f"Public key not found for profile {self._conf.profile.orcid_id}")
        if np.metadata.public_key != self._conf.profile.public_key is None:
            raise AssertionError(
                "The public key in your profile does not match the public key"
                "that the publication that you want to update is signed with."
            )
