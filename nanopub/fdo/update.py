from typing import Tuple, Optional
from nanopub.fdo.fdo_nanopub import FdoNanopub
from nanopub.fdo.fdo_record import FdoRecord
from nanopub.fdo.retrieve import resolve_in_nanopub_network
from nanopub.nanopub_conf import NanopubConf
from nanopub import NanopubUpdate


def update_record(
    fdo_iri: str,
    record: FdoRecord,
    publish: bool,
    conf: NanopubConf
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Update or create an FDO nanopub depending on whether a source nanopub URI is resolvable
    and signed with our current profile key.
    """
    existing_npub = resolve_in_nanopub_network(fdo_iri, conf=conf)

    if existing_npub:
        existing_pubkey = existing_npub.signed_with_public_key
        current_pubkey = conf.profile.public_key if conf.profile else None

        if str(existing_pubkey) == str(current_pubkey):

            existing_npub.assertion.remove((None, None, None))
            for triple in record.get_graph():
                existing_npub.assertion.add(triple)

            new_np = NanopubUpdate(
                uri=existing_npub.source_uri,
                conf=conf,
                assertion=existing_npub.assertion,
            )
            new_np.sign()
            return new_np.publish() if publish else (None, None, None)
        if str(existing_pubkey) != str(current_pubkey):
            return (None, None, None)

    else:
        npub = FdoNanopub.create_with_fdo_iri(
            fdo_record=record,
            fdo_iri=fdo_iri,
            data_ref=record.get_data_ref(),
            conf=conf
        )
        return npub.publish() if publish else (None, None, None)
