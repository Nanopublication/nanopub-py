import hashlib
import re
from functools import cmp_to_key

from rdflib.term import Literal

from nanopub.trustyuri import TrustyUriUtils
from nanopub.trustyuri.rdf.RdfPreprocessor import preprocess
from nanopub.trustyuri.rdf.StatementComparator import StatementComparator
from nanopub.utils import log


def normalize_quads(quads, hashstr=None, baseuri=None):
    quads.sort()
    quads = preprocess(quads, hashstr=hashstr, baseuri=baseuri)
    comp = StatementComparator(hashstr)
    quads = sorted(quads, key=cmp_to_key(lambda q1, q2: comp.compare(q1, q2)))
    s = ""
    previous = ""
    for q in quads:
        e = ""
        e = e + str(value_to_string(q[0]))
        e = e + str(value_to_string(q[1]))
        e = e + str(value_to_string(q[2]))
        e = e + str(value_to_string(q[3]))
        if not e == previous:
            s = s + e
        previous = e
    log.debug(f"Normalized quads before signing/hashing:\n{s}")
    return s


def make_hash(quads, hashstr=None, baseuri=None) -> str:
    s = normalize_quads(quads, hashstr, baseuri)

    # Uncomment next line to see what goes into the hash:
    # print("NORMALIZED QUADS IN MAKE_HASH\n" + s + "NORMALIZED QUADS IN MAKE_HASH\n")
    return "RA" + TrustyUriUtils.get_base64(hashlib.sha256(s.encode("utf-8")).digest())


def value_to_string(value) -> str:
    if value is None:
        return "\n"
    elif isinstance(value, Literal):
        if value.language is not None:
            # TODO: proper canonicalization of language tags
            return f"@{value.language.lower()} {escape(value)}\n"
        if value.datatype is not None:
            return f"^{value.datatype} {escape(value)}\n"
        return f"^http://www.w3.org/2001/XMLSchema#string {escape(value)}\n"
    else:
        return f"{str(value)}\n"


def escape(s) -> str:
    return re.sub(r"\n", r"\\n", re.sub(r"\\", r"\\\\", str(s)))
