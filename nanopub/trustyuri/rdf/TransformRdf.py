import logging
import os
import sys

from rdflib.graph import Dataset
from rdflib.term import URIRef

from nanopub.trustyuri.rdf import RdfTransformer, RdfUtils


def transform(args):
    filename = args[0]
    baseuristr = args[1]

    with open(filename) as f:
        rdfFormat = RdfUtils.get_format(filename)
        cg = Dataset()
        cg.parse(data=f.read(), format=rdfFormat)
        baseuri = URIRef(baseuristr)
        outdir = os.path.abspath(os.path.join(str(filename), os.pardir))
        RdfTransformer.transform_to_file(cg, baseuri, outdir, filename)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    args = sys.argv
    args.pop(0)
    transform(args)
