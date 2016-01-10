class solution:
    def __init__(self):
        self.name = None
        self.date = None
        self.size = None
        self.author = None
        self.remove_link = None
        self.download_link = None
        self.edit_link = None

    def __repr__(self):
        return str(self.__dict__)

    def byDict(self, dict):
        for key in dict.keys():
            if key != '__type':
                setattr(self, key, dict[key])

    def normalize(self, session):
        assert self.remove_link
        assert self.download_link
        assert self.edit_link
        self.remove_link = session.make_link(self.remove_link, ssid=True)
        self.download_link = session.make_link(self.download_link, ssid=True)
        self.edit_link = session.make_link(self.edit_link, ssid=True)
