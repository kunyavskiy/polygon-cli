from . import config
from . import global_vars
from . import utils


class PolygonFile:
    def __init__(self):
        self.name = None
        self.type = None
        self.date = None
        self.size = None
        self.content = None

    @staticmethod
    def to_byte(value, encoding):
        return value.encode(encoding=encoding) if encoding else value.encode()

    def __repr__(self):
        return str(self.__dict__)

    def by_dict(self, data):
        for key in data.keys():
            if key != '__type':
                setattr(self, key, data[key])

    def get_content(self):
        """

        :rtype: bytes
        """
        if self.type == 'script':
            file_text = global_vars.problem.load_script()
        elif self.type == 'solution':
            file_text = global_vars.problem.send_api_request('problem.viewSolution', {'name': self.name}, False)
        elif self.type == 'statement':
            if self.content is not None:
                file_text = self.content
            else:
                data = global_vars.problem.send_api_request('problem.statements', {})
                lang, name = self.name.split('/')
                data = data.get(lang, {})
                if name.endswith(".tex"):
                    name = name[:-4]
                encoding = data.get('encoding', None)
                content = data.get(name, None)
                file_text = PolygonFile.to_byte(content, encoding)
        elif self.type == 'statementResource':
            file_text = global_vars.problem.send_api_request('problem.viewStatementResource', {'name': self.name}, False)
        else:
            file_text = global_vars.problem.send_api_request('problem.viewFile',
                                                             {'name': self.name,
                                                              'type': utils.get_api_file_type(self.type)}, False)
        return file_text

    def get_default_local_dir(self):
        if self.type in list(config.subdirectory_paths.keys()):
            return config.subdirectory_paths[self.type]
        raise NotImplementedError("loading files of type %s" % self.type)
