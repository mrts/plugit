class App(object):
    def __init__(self,
            name, version,
            author=None, author_email=None, depends=None,
            **kwargs):
        self.name = name
        self.version = version
