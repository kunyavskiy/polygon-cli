from . import global_vars
from . import utils
from .config import subdirectory_paths

class PolygonFile:
    def __init__(self):
        self.name = None
        self.type = None
        self.date = None
        self.size = None

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
        else:
            file_text = global_vars.problem.send_api_request('problem.viewFile',
                                                             {'name': self.name,
                                                              'type': utils.get_api_file_type(self.type)}, False)
        return file_text

    def get_default_local_dir(self):
        if self.type in subdirectory_paths:
            return subdirectory_paths[self.type]
        raise NotImplementedError("loading files of type %s" % self.type)
