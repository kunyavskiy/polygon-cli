import hashlib
import json
import random
import sys
import time
from getpass import getpass

import requests

from . import config
from . import polygon_file
from . import utils
from .exceptions import PolygonNotLoginnedError, ProblemNotFoundError, PolygonApiError
from .polygon_html_parsers import *


def get_login_password():
    if config.login:
        print('Using login %s from config' % config.login)
    else:
        print('Enter login:', end=' ')
        sys.stdout.flush()
        config.login = sys.stdin.readline().strip()
    if config.password:
        print('Using password from config')
    else:
        config.password = getpass('Enter password: ')


def parse_api_file_list(files, files_raw, type):
    for j in files_raw:
        file = polygon_file.PolygonFile()
        file.type = type
        file.name = j["name"]
        file.date = j["modificationTimeSeconds"]
        file.size = j["length"]
        files.append(file)


class ProblemSession:
    def __init__(self, address, problem_id):
        """

        :type address: str
        :type problem_id: int or None
        """
        self.polygon_address = address
        self.problem_id = problem_id
        self.owner = None
        self.problem_name = None
        self.session = requests.session()
        self.sessionId = None
        self.ccid = None
        self.local_files = []
        self.relogin_done = False

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
        if "version" not in data:
            print('Your session file is too old, relogin required')
            self.sessionId = None
            self.ccid = None
        else:
            self.owner = data["owner"]
            self.problem_name = data["problemName"]

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
        data["problemName"] = self.problem_name
        data["owner"] = self.owner
        data["version"] = 1
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
        if self.sessionId is None:
            self.renew_http_data()
        print('Sending request to ' + utils.prepare_url_print(url), end=' ')
        sys.stdout.flush()
        result = self.session.request(method, url, **kw)
        print(result.status_code)
        if result.url and result.url.startswith(config.polygon_url + '/login'):
            if not self.relogin_done:
                self.renew_http_data()
                return self.send_request(method, url, **kw)
            else:
                print('Already tried to relogin, but it didn''t helped')
                raise PolygonNotLoginnedError()
        return result

    def send_api_request(self, api_method, params, is_json=True, problem_data=True):
        print('Invoking ' + api_method, end=' ')
        sys.stdout.flush()
        params["apiKey"] = config.api_key
        params["time"] = int(time.time())
        if problem_data:
            params["problemId"] = self.problem_id
        signature_random = ''.join([chr(random.SystemRandom().randint(0, 25) + ord('a')) for _ in range(6)])
        signature_random = utils.convert_to_bytes(signature_random)
        param_list = [(utils.convert_to_bytes(key), utils.convert_to_bytes(params[key])) for key in params]
        param_list.sort()
        signature_string = signature_random + b'/' + utils.convert_to_bytes(api_method)
        signature_string += b'?' + b'&'.join([i[0] + b'=' + i[1] for i in param_list])
        signature_string += b'#' + utils.convert_to_bytes(config.api_secret)
        params["apiSig"] = signature_random + utils.convert_to_bytes(hashlib.sha512(signature_string).hexdigest())
        url = self.polygon_address + '/api/' + api_method
        result = self.session.request('POST', url, data=params)
        print(result.status_code)
        if not is_json and result.status_code == 200:
            return result.content
        result = json.loads(result.content.decode('utf8'))
        if result["status"] == "FAILED":
            print(result["comment"])
            raise PolygonApiError()
        if "result" in result:
            return result["result"]
        return None

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
                'start': parser.startLink,
                'owner': parser.owner,
                'problem_name': parser.problemName
                }

    def renew_http_data(self):
        self.relogin_done = True
        get_login_password()
        self.login(config.login, config.password)
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
        solutions_raw = self.send_api_request('problem.solutions', {})
        files = []
        parse_api_file_list(files, solutions_raw, 'solution')
        return files

    def get_files_list(self):
        """

        :rtype: list of polygon_file.PolygonFile
        """
        files_raw = self.send_api_request('problem.files', {})
        files = []
        types_map = {'sourceFiles': 'source', 'resourceFiles': 'resource', 'auxFiles': 'attachment'}
        for i in types_map:
            parse_api_file_list(files, files_raw[i], types_map[i])

        script = polygon_file.PolygonFile()
        script.type = 'script'
        script.name = 'script'
        files.append(script)
        return files

    def get_all_files_list(self):
        """

        :rtype: list of polygon_file.PolygonFile
        """
        return self.get_files_list() + self.get_solutions_list()

    def upload_file(self, name, type, content, is_new, tag=None):
        """
        Uploads new solution to polygon

        :type name: str
        :type type: str
        :type content: bytes
        :type is_new: bool
        :type tag: str or None
        :rtype: bool
        """
        options = {}
        if name.endswith('.cpp'):
            options['sourceType'] = 'cpp.g++11'
        if is_new:
            options['checkExisting'] = 'true'
        else:
            options['checkExisting'] = 'false'
        options['name'] = name
        if type == 'solution':
            api_method = 'problem.saveSolution'
            if tag:
                options['tag'] = tag
        else:
            api_method = 'problem.saveFile'
            options['type'] = utils.get_api_file_type(type)
            if not options['type']:
                raise NotImplementedError("uploading file of type " + type)

        options['file'] = content
        try:
            self.send_api_request(api_method, options)
        except PolygonApiError as e:
            print(e)
            return False

        return True

    def set_utility_file(self, polygon_filename, type):
        """
        Sets checker or validator

        :type polygon_filename: str
        :type type: str
        """

        self.send_api_request('problem.set' + type.title(), {type: polygon_filename})

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

        input = self.send_api_request('problem.testInput',
                                      {'testset': 'tests', 'testIndex': test_num},
                                      is_json=False)
        utils.safe_rewrite_file('%03d' % int(test_num), utils.convert_newlines(input))
        answer = self.send_api_request('problem.testAnswer',
                                       {'testset': 'tests', 'testIndex': test_num},
                                       is_json=False)
        utils.safe_rewrite_file('%03d.a' % int(test_num), utils.convert_newlines(answer))

    def download_all_tests(self):
        tests = self.send_api_request('problem.tests',{'testset': 'tests'})
        for t in tests:
            self.download_test(t["index"])

    def load_script(self):
        return self.send_api_request('problem.script', {'testset': 'tests'}, is_json=False)

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

        :type content: bytes
        """
        try:
            self.send_api_request('problem.saveScript', {'testset': 'tests', 'source': content})
        except PolygonApiError as e:
            print(e)
            return False
        return self.update_groups(content)

    def set_test_group(self, tests, group):
        for i in tests:
            self.send_api_request('problem.saveTest', {'testset': 'tests', 'testIndex': i, 'testGroup': group})

    def get_hand_tests_list(self):
        tests = self.send_api_request('problem.tests', {'testset': 'tests'})
        result = []
        for i in tests:
            if i["manual"]:
                result.append(int(i["index"]))
        return result

    def get_contest_problems(self, contest_id):
        assert (self.problem_id is None)
        problems = self.send_api_request('contest.problems', {'contestId': contest_id}, problem_data=False)
        result = {}
        for i in problems.keys():
            result[problems[i]["name"]] = problems[i]["id"]
        return result
