class TrustyUriResource:
    def __init__(self, filename, content, hashstr):
        self.filename = filename
        self.content = content
        self.hashstr = hashstr

    def get_filename(self):
        return self.filename

    def get_hashstr(self):
        return self.hashstr

    def get_content(self):
        return self.content
