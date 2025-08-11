import hashlib

from nanopub.trustyuri import TrustyUriUtils


def make_hash(content):
    try:
        return "FA" + TrustyUriUtils.get_base64(hashlib.sha256(content).digest())
    except Exception:
        return "FA" + TrustyUriUtils.get_base64(
            hashlib.sha256(content.encode()).digest()
        )
