from nanopub.trustyuri.file import FileHasher
from nanopub.trustyuri.TrustyUriModule import TrustyUriModule


class FileModule(TrustyUriModule):
    def module_id(self):
        return "FA"

    def has_correct_hash(self, resource):
        h = FileHasher.make_hash(resource.get_content())
        return resource.get_hashstr() == h
