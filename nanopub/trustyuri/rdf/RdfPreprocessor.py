from rdflib.term import BNode, URIRef

from nanopub.trustyuri.rdf import RdfUtils


def preprocess(quads, hashstr=None, baseuri=None):
    newquads = []
    bnodemap = {}
    for q in quads:
        c = transform(q[0], hashstr, baseuri, bnodemap)
        s = transform(q[1], hashstr, baseuri, bnodemap)
        p = transform(q[2], hashstr, baseuri, bnodemap)
        o = q[3]
        if isinstance(q[3], URIRef) or isinstance(q[3], BNode):
            o = transform(q[3], hashstr, baseuri, bnodemap)
        newquads.append((c, s, p, o))
    return newquads


def transform(uri, hashstr, baseuri, bnodemap):
    if uri is None:
        return None

    if baseuri is None:
        try:
            return URIRef(RdfUtils.normalize(uri, hashstr).decode("utf-8"))
        except Exception:
            return URIRef(RdfUtils.normalize(uri, hashstr))
    return RdfUtils.get_trustyuri(uri, baseuri, hashstr, bnodemap)
