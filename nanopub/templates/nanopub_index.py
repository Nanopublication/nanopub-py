from copy import deepcopy
from typing import List, Union

from rdflib import Literal, URIRef
from rdflib.namespace import DC, DCTERMS, RDF, RDFS, XSD

from nanopub.definitions import DUMMY_NAMESPACE, DUMMY_URI, MAX_NP_PER_INDEX
from nanopub.namespaces import NPX, PAV
from nanopub.nanopub import Nanopub
from nanopub.nanopub_conf import NanopubConf
from nanopub.utils import log


class NanopubIndex(Nanopub):
    """Publish a list of nanopub URIs in a Nanopub Index

    Args:
        conf: config for the nanopub
        np_list: List of nanopub URIs
        title: Title of the Nanopub Index
        description: Description of the Nanopub Index
        creation_time: Creation time of the Nanopub Index, in format YYYY-MM-DDThh-mm-ss
        creators: List of the ORCID of the creators of the Nanopub Index
        see_also: A URL to a page with further information on the Nanopub Index
    """

    def __init__(
        self,
        conf: NanopubConf,
        np_list: Union[List[str], List[Nanopub]],
        title: str,
        description: str,
        creation_time: str,
        creators: List[str],
        see_also: str = None,
        top_level: bool = False,
    ) -> None:
        conf = deepcopy(conf)
        conf.add_prov_generated_time = False
        conf.add_pubinfo_generated_time = True
        conf.attribute_publication_to_profile = True
        super().__init__(
            conf=conf,
        )

        for np in np_list:
            if isinstance(np, Nanopub):
                np_uri = np.source_uri
            else:
                np_uri = np
            if top_level:
                self.assertion.add((DUMMY_URI, NPX.appendsIndex, URIRef(np_uri)))
            else:
                self.assertion.add((DUMMY_URI, NPX.includesElement, URIRef(np_uri)))

        self.pubinfo.add((DUMMY_URI, RDF.type, NPX.NanopubIndex))
        self.pubinfo.add((DUMMY_URI, DC.title, Literal(title)))
        self.pubinfo.add((DUMMY_URI, DC.description, Literal(description)))
        if see_also:
            self.pubinfo.add((DUMMY_URI, RDFS.seeAlso, URIRef(see_also)))
        for creator in creators:
            self.pubinfo.add((DUMMY_URI, PAV.createdBy, URIRef(creator)))
        # TODO: use current time if not provided
        # datetime.datetime.now().astimezone().replace(microsecond=0).isoformat() ?
        self.pubinfo.add(
            (
                DUMMY_URI,
                DCTERMS.created,
                Literal(creation_time, datatype=XSD.dateTime, normalize=False),
            )
        )

        self.provenance.add((DUMMY_NAMESPACE.assertion, RDF.type, NPX.IndexAssertion))


def create_nanopub_index(
    conf: NanopubConf,
    np_list: Union[List[str], List[Nanopub]],
    title: str,
    description: str,
    creation_time: str,
    creators: List[str],
    see_also: str = None,
) -> List[Nanopub]:
    """Create a Nanopub index.

    Publish a list of nanopub URIs in a Nanopub Index

    Args:
        np_list: List of nanopub URIs
        title: Title of the Nanopub Index
        description: Description of the Nanopub Index
        creation_time: Creation time of the Nanopub Index, in format YYYY-MM-DDThh-mm-ss
        creators: List of the ORCID of the creators of the Nanopub Index
        see_also: A URL to a page with further information on the Nanopub Index
    """
    pub_list: List[Nanopub] = []
    for i in range(0, len(np_list), MAX_NP_PER_INDEX):
        np_chunk = np_list[i : i + MAX_NP_PER_INDEX]
        pub = NanopubIndex(
            conf,
            np_chunk,
            title,
            description,
            creation_time,
            creators,
            see_also,
            top_level=False,
        )
        pub.sign()
        log.info(f"Signed Nanopub Index: {pub.source_uri}")
        pub_list.append(pub)

    if len(pub_list) > 1:
        toplevel_pub = NanopubIndex(
            conf,
            pub_list,
            title,
            description,
            creation_time,
            creators,
            see_also,
            top_level=True,
        )
        toplevel_pub.sign()
        log.info(f"Signed top level Nanopub Index: {toplevel_pub.source_uri}")
        pub_list.append(toplevel_pub)

    return pub_list
