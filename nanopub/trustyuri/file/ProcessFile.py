import os
import re
import sys

from nanopub.trustyuri.file import FileHasher


def process(args):
    filename = args[0]

    with open(filename) as f:
        hashstr = FileHasher.make_hash(f.read())
        ext = ""
        base = filename
        if re.search(r".\.[A-Za-z0-9\-_]{0,20}$", filename):
            ext = re.sub(r"^(.*)(\.[A-Za-z0-9\-_]{0,20})$", r"\2", filename)
            base = re.sub(r"^(.*)(\.[A-Za-z0-9\-_]{0,20})$", r"\1", filename)
        os.rename(filename, base + "." + hashstr + ext)


if __name__ == "__main__":
    args = sys.argv
    args.pop(0)
    process(args)
