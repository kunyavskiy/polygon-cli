from . import global_vars
from . import utils


class PolygonFile:
    def __init__(self):
        self.name = None
        self.type = None
        self.date = None
        self.size = None
        self.remove_link = None
        self.download_link = None
        self.edit_link = None
        self.apiFile = False

    def __repr__(self):
        return str(self.__dict__)

    def by_dict(self, data):
        for key in data.keys():
            if key != '__type':
                setattr(self, key, data[key])

    def normalize(self, session):
        """

        :type session: problem.ProblemSession
        """
        assert self.remove_link
        assert self.download_link
        assert self.edit_link
        self.remove_link = session.make_link(self.remove_link, ssid=True)
        self.download_link = session.make_link(self.download_link, ssid=True)
        self.edit_link = session.make_link(self.edit_link, ssid=True)

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
        if self.type == 'solution':
            return 'solutions'
        if self.type == 'source':
            return 'src'
        if self.type == 'resource':
            return 'src'
        if self.type == 'attachment':
            return 'src'
        if self.type == 'script':
            return ''
        raise NotImplementedError("loading files of type %s" % self.type)
