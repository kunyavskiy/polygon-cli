import os

import config
import global_vars
import utils


class LocalFile:
    def __init__(self, filename=None, dir=None, name=None, type=None, polygon_filename=None):
        """

        :type filename: str or None
        :type dir: str or None
        :type name: str or None
        :type type: str or None
        :type polygon_filename: str or None
        """
        self.filename = filename
        self.dir = dir
        self.name = name
        self.type = type
        self.polygon_filename = polygon_filename

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

    def get_internal_path(self):
        """

        :rtype: str
        """
        return os.path.join(config.internal_directory_path, self.filename)

    def upload(self):
        assert self.polygon_filename is None
        content = open(self.get_path(), 'r').read()
        prefix = None
        url = None
        if self.type == 'solution':
            prefix = 'solutions'
            url = 'solutions'
        elif self.type == 'source':
            prefix = 'source'
            url = 'files'
        else:
            raise NotImplementedError("uploading solution of type " + self.type)
        if not global_vars.problem.upload_file(self.filename, prefix, url, content):
            return
        utils.safe_rewrite_file(self.get_internal_path(), content)
        self.polygon_filename = self.filename

    def update(self):
        assert self.polygon_filename is not None
        content = open(self.get_path(), 'r').read()
        if not global_vars.problem.edit_file(self.filename, self.type, content):
            return
        utils.safe_rewrite_file(self.get_internal_path(), content)
