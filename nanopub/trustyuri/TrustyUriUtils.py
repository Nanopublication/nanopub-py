import base64
import re

TRUSTY_ARTIFACT_RE = re.compile(r"^RA[A-Za-z0-9_-]{40,}$")


def get_trustyuri_tail(s):
    if not re.search(r'(.*[^A-Za-z0-9\-_]|)[A-Za-z0-9\-_]{25,}(\.[A-Za-z0-9\-_]{0,20})?', s):
        return ""
    return re.sub(r'^(.*[^A-Za-z0-9\-_]|)([A-Za-z0-9\-_]{25,})(\.[A-Za-z0-9\-_]{0,20})?$', r'\2', s)


def get_base64(s):
    return re.sub(r'=', '', base64.b64encode(s, b'-_').decode('utf-8'))


def is_trusty_uri(uri: str) -> bool:
    s = str(uri).rstrip("/#")
    last = s.rsplit("/", 1)[-1]
    return bool(TRUSTY_ARTIFACT_RE.match(last))
