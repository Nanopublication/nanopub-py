from rdflib.graph import Dataset

from nanopub.trustyuri.rdf import RdfHasher, RdfUtils
from nanopub.trustyuri.TrustyUriModule import TrustyUriModule


class RdfModule(TrustyUriModule):
    def module_id(self):
        return "RA"
    def has_correct_hash(self, resource):
        f = RdfUtils.get_format(resource.get_filename())
        cg = Dataset()
        cg.parse(data=resource.get_content(), format=f)
        quads = RdfUtils.get_quads(cg)
        h = RdfHasher.make_hash(quads, resource.get_hashstr())
        return resource.get_hashstr() == h
