import os

from . import config
from . import global_vars
from . import utils


class LocalFile:
    def __init__(self, filename=None, dir=None, name=None, type=None, polygon_filename=None, tag=None):
        """

        :type filename: str or None
        :type dir: str or None
        :type name: str or None
        :type type: str or None
        :type polygon_filename: str or None
        :type tag: str or None
        """

        if type == 'statement':
            assert filename is not None
            assert dir is not None
            assert name is not None
            lang = os.path.basename(dir)
            dir = os.path.dirname(dir)
            filename = lang + '/' + filename
            name = lang + '/' + name

        self.filename = filename
        self.dir = dir
        self.name = name
        self.type = type
        self.polygon_filename = polygon_filename
        self.tag = tag

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
        file = open(self.get_path(), 'rb')
        content = file.read()
        if self.type == 'script':
            if not global_vars.problem.upload_script(content):
                return False
        elif self.type == 'statement':
            if not global_vars.problem.upload_statement(self.filename, content):
                return False
        elif not global_vars.problem.upload_file(self.filename, self.type, content, True, self.tag):
            return False
        utils.safe_rewrite_file(self.get_internal_path(), content)
        self.polygon_filename = self.filename
        return True

    def update(self):
        assert self.polygon_filename is not None
        file = open(self.get_path(), 'rb')
        content = file.read()
        if self.type == 'script':
            if not global_vars.problem.upload_script(content):
                return False
        elif self.type == 'statement':
            if not global_vars.problem.upload_statement(self.filename, content):
                return False
        elif not global_vars.problem.upload_file(self.filename, self.type, content, False):
            return False
        utils.safe_rewrite_file(self.get_internal_path(), content)
        return True
