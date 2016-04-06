import sys

import requests

from . import config
from . import polygon_file
from . import utils
from .exceptions import PolygonNotLoginnedError, ProblemNotFoundError
from .polygon_html_parsers import *


class ProblemSession:
    def __init__(self, address, problem_id):
        """

        :type address: str
        :type problem_id: int
        """
        self.polygon_address = address
        self.problem_id = problem_id
        self.session = requests.session()
        self.sessionId = None
        self.ccid = None
        self.local_files = []

    def use_ready_session(self, data):
        """

        :type data: dict
        """
        cookies = data["cookies"]
        for i in cookies.keys():
            self.session.cookies.set(i, cookies[i])
        self.ccid = data["ccid"]
        assert self.problem_id == data["problemId"]
        self.sessionId = data["sessionId"]
        self.local_files = data["localFiles"]

    def dump_session(self):
        """

        :rtype: dict
        :return: session ready to json-serialization
        """
        data = dict()
        data["problemId"] = self.problem_id
        data["sessionId"] = self.sessionId
        data["cookies"] = self.session.cookies.get_dict()
        data["ccid"] = self.ccid
        data["localFiles"] = self.local_files
        return data

    def make_link(self, link, ccid=False, ssid=False):
        """

        :type link: str
        :type ccid: bool
        :type ssid: bool
        :rtype: str
        """
        if ccid:
            if link.find('?') != -1:
                link += '&'
            else:
                link += '?'
            link += 'ccid=%s' % self.ccid
        if ssid:
            if link.find('?') != -1:
                link += '&'
            else:
                link += '?'
            link += 'session=%s' % self.sessionId
        if link.startswith('/'):
            result = self.polygon_address + link
        else:
            result = self.polygon_address + '/' + link
        return result

    def send_request(self, method, url, **kw):
        """

        :type method: str
        :type url: str
        :rtype: requests.Response
        :raises: PolygonNotLoginnedError
        """
        print('Sending request to ' + utils.prepare_url_print(url), end=' ')
        sys.stdout.flush()
        result = self.session.request(method, url, **kw)
        print(result.status_code)
        if result.url and result.url.startswith(config.polygon_url + '/login'):
            raise PolygonNotLoginnedError()
        return result

    def login(self, login, password):
        """

        :type login: str
        :type password: str
        """
        fields = {
            "submitted": "true",
            "login": login,
            "password": password,
            "attachSessionToIp": "on",
            "submit": "Login",
        }

        url = self.make_link("login")
        result = self.send_request('POST', url, data=fields)
        parser = ExtractCCIDParser()
        parser.feed(result.text)
        assert parser.ccid
        self.ccid = parser.ccid

    def get_problem_links(self):
        """

        :rtype: dict
        """
        url = self.make_link('problems', ccid=True)
        problems_page = self.send_request('GET', url).text
        parser = ProblemsPageParser(self.problem_id)
        parser.feed(problems_page)
        return {'continue': parser.continueLink,
                'discard': parser.discardLink,
                'start': parser.startLink}

    def create_new_session(self, login, password):
        """

        :type login: str
        :type password: str
        """
        self.login(login, password)
        links = self.get_problem_links()
        if links['start'] is None and links['continue'] is None:
            raise ProblemNotFoundError()
        url = self.make_link(links['continue'] or links['start'])
        problem_page = self.send_request('GET', url).text
        parser = ExtractSessionParser()
        parser.feed(problem_page)
        self.sessionId = parser.session

    def get_solutions_list(self):
        """

        :rtype: list of polygon_file.PolygonFile
        """
        url = self.make_link('solutions', ccid=True, ssid=True)
        solutions_page = self.send_request('GET', url)
        parser = SolutionsPageParser()
        parser.feed(solutions_page.text)
        files = parser.files
        for i in range(len(files)):
            files[i].normalize(self)
        return files

    def get_files_list(self):
        """

        :rtype: list of polygon_file.PolygonFile
        """
        url = self.make_link('files', ccid=True, ssid=True)
        solutions_page = self.send_request('GET', url)
        parser = FilesPageParser()
        parser.feed(solutions_page.text)
        files = parser.files
        for i in range(len(files)):
            files[i].normalize(self)
        script = PolygonFile()
        script.type = 'script'
        script.name = 'script'
        files.append(script)
        return files

    def get_all_files_list(self):
        """

        :rtype: list of polygon_file.PolygonFile
        """
        return self.get_files_list() + self.get_solutions_list()

    def upload_file(self, name, prefix, url, content):
        """
        Uploads new solution to polygon

        :type name: str
        :type prefix: str
        :type url: str
        :type content: str
        :rtype: bool
        """
        file_type = 'cpp.g++11' if name.endswith('.cpp') else ''
        fields = {
            prefix + '_file_type': ('', file_type),
            'submitted': ('', 'true'),
            prefix + '_file_added': (name, content),
            'ccid': ('', self.ccid),
            'session': ('', self.sessionId)
        }
        r = self.send_request('POST', self.make_link(url), files=fields)
        parser = FindUploadErrorParser()
        parser.feed(r.text)
        if parser.error:
            print('Received error:')
            print(parser.error)
            return False
        return True

    def edit_file(self, name, file_type, content):
        """
        Edits existing solution in polygon

        :type name: str
        :type file_type: str
        :type content: str
        :rtype: bool
        """
        if file_type == 'solution':
            file_type = 'solutions'  # because of edit link in polygon
        fields = {
            'type': file_type,
            'file': name,
            'submitted': 'true',
            'content': content,
            'ccid': self.ccid,
            'session': self.sessionId
        }
        r = self.send_request('POST', self.make_link('modify'), data=fields)
        parser = FindEditErrorParser()
        parser.feed(r.text)
        if parser.error:
            print('Received error:')
            print(parser.error)
            return False
        return True

    def set_checker_validator(self, polygon_filename, type):
        """
        Sets checker or validator

        :type polygon_filename: str
        :type type: str
        """
        fields = {
            'submitted': ('', 'true'),
            'file_selected': ('', polygon_filename),
            'file_added': ('', ''),
            'file_type': ('', ''),
            'Set checker': ('', 'Set ' + type),
            'ccid': ('', self.ccid),
            'session': ('', self.sessionId)
        }
        url = 'checker' if type == 'checker' else 'validation'
        self.send_request('POST', self.make_link(url), files=fields)

    def change_solution_type(self, polygon_filename, type):
        """
        Changes type of solution

        :type polygon_filename: str
        :type type: str
        """
        fields = {
            'action': ('', 'tagChangeType'),
            'submitted': ('', 'true'),
            'file': ('', polygon_filename),
            'chosenType': ('', type),
            'ccid': ('', self.ccid),
            'session': ('', self.sessionId)
        }
        self.send_request('POST', self.make_link('solutions'), files=fields)

    def get_local_by_polygon(self, file):
        """

        :type file: polygon_file.PolygonFile
        :rtype: local_file.LocalFile or None
        """
        for local in self.local_files:
            if local.polygon_filename == file.name:
                return local
        return None

    def get_local_by_filename(self, filename):
        """

        :type filename: str
        :rtype: local_file.LocalFile or None
        """
        for local in self.local_files:
            if local.filename == filename:
                return local
        return None

    def download_test(self, test_num):
        """

        :type test_num: str
        """

        input_url = self.make_link('plain-input/input-%s.txt?testset=tests&index=%s' % (test_num, test_num), ccid=True, ssid=True)
        input = self.send_request('GET', input_url).text
        utils.safe_rewrite_file('%03d' % int(test_num), input, 'w')
        answer_url = self.make_link('plain-answer/answer-%s.txt?testset=tests&index=%s' % (test_num, test_num), ccid=True, ssid=True)
        answer = self.send_request('GET', answer_url).text
        utils.safe_rewrite_file('%03d.a' % int(test_num), answer, 'w')

    def load_script(self):
        test_url = self.make_link('tests', ccid=True, ssid=True)
        tests = self.send_request('GET', test_url)
        parser = FindScriptParser()
        parser.feed(tests.text)
        return str.encode(parser.script)

    def update_groups(self, script_content):
        hand_tests = self.get_hand_tests_list()
        groups = utils.parse_script_groups(script_content, hand_tests)
        if groups:
            for i in groups.keys():
                self.set_test_group(groups[i], i)
        return True

    def upload_script(self, content):
        """
        Uploads script solution to polygon

        :type content: str
        """
        url = self.make_link('tests?action=saveScript&testset=tests', ssid=False, ccid=False)
        fields = {
            'submitted': 'true',
            'script': content,
            'ccid': self.ccid,
            'session': self.sessionId,
            'Save': 'Save Script'
        }
        r = self.send_request('POST', url, files=fields)
        parser = FindUploadScriptErrorParser()
        parser.feed(r.text)
        if parser.error:
            print('Received error:')
            print(parser.error)
            return False
        return self.update_groups(content)

    def set_test_group(self, tests, group):
        url = self.make_link('data/tests', ssid=False, ccid=False)
        fields = {
            'action': 'setMultipleTestGroup',
            'session': self.sessionId,
            'testset': 'tests',
            'requestString': '&'.join(map(lambda x: 'testIndex=' + str(x), tests)),
            'groupName': group,
            'ccid': self.ccid
        }

        r = self.send_request('POST', url, files=fields)

    def get_hand_tests_list(self):
        test_url = self.make_link('tests', ccid=True, ssid=True)
        tests = self.send_request('GET', test_url)
        parser = FindHandTestsParser()
        parser.feed(tests.text)
        return parser.tests
