import os
import re

from nanopub.trustyuri.rdf import HashAdder, RdfHasher, RdfPreprocessor, RdfUtils


def transform_to_file(conjgraph, baseuri, outdir, filename):
    quads = RdfUtils.get_quads(conjgraph)
    quads = RdfPreprocessor.preprocess(quads, baseuri=baseuri)
    hashstr = RdfHasher.make_hash(quads)
    quads = HashAdder.addhash(quads, hashstr)
    conjgraph = RdfUtils.get_dataset(quads)
    name = ""
    if (baseuri is not None) and re.match('.*/.*', str(baseuri)):
        name = re.sub(r'^.*[^A-Za-z0-9.\-_]([A-Za-z0-9.\-_]*)$', r'\1', str(baseuri)) + "."
    ext = os.path.splitext(filename)[1]
    rdfFormat = RdfUtils.get_format(filename)
    conjgraph.serialize(outdir + "/" + name + hashstr + ext, format=rdfFormat)
    return RdfUtils.get_trustyuri(baseuri, baseuri, hashstr, None)


def transform_to_string(conjgraph, baseuri):
    quads = RdfUtils.get_quads(conjgraph)
    quads = RdfPreprocessor.preprocess(quads, baseuri=baseuri)
    hashstr = RdfHasher.make_hash(quads)
    quads = HashAdder.addhash(quads, hashstr)
    conjgraph = RdfUtils.get_dataset(quads)
    return conjgraph.serialize(format='trix')


def transform(conjgraph, baseuri):
    quads = RdfUtils.get_quads(conjgraph)
    quads = RdfPreprocessor.preprocess(quads, baseuri=baseuri)
    hashstr = RdfHasher.make_hash(quads)
    quads = HashAdder.addhash(quads, hashstr)
    return RdfUtils.get_dataset(quads)
