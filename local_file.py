import os

import global_vars
from polygon_file import PolygonFile


class LocalFile:
    def __init__(self):
        self.filename = None
        self.dir = None
        self.name = None
        self.type = None
        self.polygon_filename = None

    def __repr__(self):
        return str(self.__dict__)

    def by_dict(self, data):
        for key in data.keys():
            if key != '__type':
                setattr(self, key, data[key])

    def get_path(self):
        """

        :rtype: str
        """
        return os.path.join(self.dir, self.filename)

    def upload(self):
        assert self.polygon_filename is None
        if type == 'solution':
            return global_vars.problem.upload_solution(self.name, open(self.get_path(), 'r').read())
        else:
            raise NotImplementedError

    def update(self):
        assert self.polygon_filename is not None
        if type == 'solution':
            return global_vars.problem.update_solution(self.polygon_filename, open(self.get_path(), 'r').read())
        else:
            raise NotImplementedError
