import hashlib
import json
import random
import sys
import time
from getpass import getpass

from xml.etree import ElementTree
import os
import glob
import re
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
    def __init__(self, polygon_name, problem_id, pin, verbose=True):
        """

        :type polygon_name: str
        :type problem_id: int or None
        """
        self.polygon_name = polygon_name
        self.problem_id = problem_id
        self.owner = None
        self.problem_name = None
        self.session = requests.session()
        self.sessionId = None
        self.ccid = None
        self.local_files = []
        self.relogin_done = False
        self.verbose = verbose
        self.pin = pin
        self.scores_enabled = False
        self.groups_enabled = set()

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
        if "pin" in data:
            self.pin = data["pin"]
        else:
            self.pin = None
        if "version" not in data:
            print('Your session file is too old, relogin required')
            self.sessionId = None
            self.ccid = None
        else:
            self.owner = data["owner"]
            self.problem_name = data["problemName"]
            if data["version"] < 2:
                for i in range(len(self.local_files)):
                    if self.local_files[i].type == "statement":
                        self.local_files[i].polygon_filename += ".tex"
                        path = self.local_files[i].get_path()
                        os.rename(path, path + ".tex")
                        internal_path = self.local_files[i].get_internal_path()
                        os.rename(internal_path, internal_path + ".tex")
                        self.local_files[i].filename += ".tex"

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
        data["polygon_name"] = self.polygon_name
        data["version"] = 3
        if self.pin is not None:
            data["pin"] = self.pin
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
            if self.ccid is None:
                self.renew_http_data()
            link += 'ccid=%s' % self.ccid
        if ssid:
            if link.find('?') != -1:
                link += '&'
            else:
                link += '?'
            if self.sessionId is None:
                self.renew_http_data()
            link += 'session=%s' % self.sessionId
        if link.startswith('/'):
            result = config.polygon_url + link
        else:
            result = config.polygon_url + '/' + link
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
            if not self.relogin_done:
                self.renew_http_data()
                return self.send_request(method, url, **kw)
            else:
                print('Already tried to relogin, but it didn''t helped')
                raise PolygonNotLoginnedError()
        return result

    def send_api_request(self, api_method, params, is_json=True, problem_data=True):
        if self.verbose:
            print('Invoking ' + api_method, end=' ')
            sys.stdout.flush()
        params["apiKey"] = config.api_key
        params["time"] = int(time.time())
        if self.pin is not None:
            params["pin"] = self.pin
        if problem_data:
            params["problemId"] = self.problem_id
        signature_random = ''.join([chr(random.SystemRandom().randint(0, 25) + ord('a')) for _ in range(6)])
        signature_random = utils.convert_to_bytes(signature_random)
        for i in params:
            params[i] = utils.convert_to_bytes(params[i])
        param_list = [(utils.convert_to_bytes(key), params[key]) for key in params]
        param_list.sort()
        signature_string = signature_random + b'/' + utils.convert_to_bytes(api_method)
        signature_string += b'?' + b'&'.join([i[0] + b'=' + i[1] for i in param_list])
        signature_string += b'#' + utils.convert_to_bytes(config.api_secret)
        params["apiSig"] = signature_random + utils.convert_to_bytes(hashlib.sha512(signature_string).hexdigest())
        url = config.polygon_url + '/api/' + api_method
        result = self.session.request('POST', url, files=params)
        if self.verbose or result.status_code != 200:
            if not self.verbose:
                print('Invoking ' + api_method, end=' ')
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

    def get_script_content(self):
        for i in self.local_files:
            if i.type == 'script':
                return open(i.get_path(), 'rb').read()
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
        currentpage = 1
        while True:
            url = self.make_link('problems?page=%d' % currentpage, ccid=True)
            problems_page = self.send_request('GET', url).text
            parser = ProblemsPageParser(self.problem_id)
            parser.feed(problems_page)
            if parser.continueLink or parser.startLink:
                return {'continue': parser.continueLink,
                        'discard': parser.discardLink,
                        'start': parser.startLink,
                        'owner': parser.owner,
                        'problem_name': parser.problemName
                        }
            if currentpage >= parser.numberOfProblemPages:
                break
            currentpage += 1
        return {'continue': None,
                'discard': None,
                'start': None,
                'owner': None,
                'problem_name': None
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

    def get_statements_list(self):
        """

        :rtype: list of polygon_file.PolygonFile
        """
        statements_raw = self.send_api_request('problem.statements', {})
        files = []
        for lang, files_raw in statements_raw.items():
            encoding = files_raw.get('encoding', None)
            for name, content in files_raw.items():
                file = polygon_file.PolygonFile()
                file.type = 'statement'
                file.name = '%s/%s.tex' % (lang, name)
                file.content = polygon_file.PolygonFile.to_byte(content, encoding)
                file.size = len(content)
                files.append(file)
        return files

    def get_statement_resources_list(self):
        """

        :rtype: list of polygon_file.PolygonFile
        """
        files_raw = self.send_api_request('problem.statementResources', {})
        files = []
        parse_api_file_list(files, files_raw, 'statementResource')
        return files

    def get_all_files_list(self):
        """

        :rtype: list of polygon_file.PolygonFile
        """
        return self.get_files_list() + self.get_solutions_list() + self.get_statements_list() + self.get_statement_resources_list()

    def upload_file(self, name, type, content, is_new, tag=None, source_type=None):
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
        if type != 'resource':
            if source_type is None:
                for extension in config.default_source_types.keys():
                    if name.endswith(extension):
                        options['sourceType'] = config.default_source_types[extension]
            else:
                options['sourceType'] = source_type
        if is_new:
            options['checkExisting'] = 'true'
        else:
            options['checkExisting'] = 'false'
        options['name'] = name
        if type == 'solution':
            api_method = 'problem.saveSolution'
            if tag:
                options['tag'] = tag
        elif type == 'statementResource':
            api_method = 'problem.saveStatementResource'
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

    def upload_statement(self, name, content):
        lang, name = name.split('/')
        if name.endswith(".tex"):
            name = name[:-4]
        options = {
            'lang': lang,
            name: content,
        }
        try:
            self.send_api_request('problem.saveStatement', options)
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

    def get_local_by_path(self, path):
        """

        :type path: str
        :rtype: local_file.LocalFile or None
        """
        path = os.path.normpath(os.path.relpath(path, "."))
        for local in self.local_files:
            if os.path.normpath(local.get_path()) == path:
                return local
        return None

    def download_test(self, test_num, test_directory='.', input_pattern='%03d', output_pattern='%03d.a'):
        """

        :type test_num: str
        """

        input = self.send_api_request('problem.testInput',
                                      {'testset': 'tests', 'testIndex': test_num},
                                      is_json=False)
        utils.safe_rewrite_file(test_directory + ('/' + input_pattern) % int(test_num), utils.convert_newlines(input))
        answer = self.send_api_request('problem.testAnswer',
                                       {'testset': 'tests', 'testIndex': test_num},
                                       is_json=False)
        utils.safe_rewrite_file(test_directory + ('/' + output_pattern) % int(test_num), utils.convert_newlines(answer))

    def download_all_tests(self):
        tests = self.send_api_request('problem.tests', {'testset': 'tests'})
        for t in tests:
            self.download_test(t["index"], config.subdirectory_paths['test'])

    def load_script(self):
        return self.send_api_request('problem.script', {'testset': 'tests'}, is_json=False)

    def update_groups(self, script_content):
        self.ensure_groups_enabled('tests')
        tests = self.get_tests()
        hand_tests = self.get_hand_tests_list(tests)
        groups, scores = utils.parse_script_groups(script_content, hand_tests)
        test_group = {i["index"]: i["group"] if "group" in i else None for i in tests}
        test_score = {i["index"]: i["points"] if "points" in i else 0.0 for i in tests}
        if groups:
            for i in groups.keys():
                bad_current_groups = list(filter(lambda x: test_group[x] != i, groups[i]))
                if bad_current_groups:
                    print('Set group ' + str(i) + ' for tests ' + str(bad_current_groups))
                self.set_test_group(bad_current_groups, i)
                if scores[i] is not None:
                    self.ensure_scores_enabled()
                    need_score_test = groups[i][0]
                    for t in groups[i]:
                        score = test_score[t]
                        need_score = scores[i]["score"] if t == need_score_test else 0.0
                        if score != need_score:
                            if bad_current_groups:
                                print('Set score ' + str(need_score) + ' for test ' + str(t))
                            self.set_test_score(t, i, need_score)
            for i in groups.keys():
                if scores[i] is not None and scores[i]["depends"] is not None:
                    self.set_test_group_deps(i, scores[i]["depends"])

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
        if not utils.need_update_groups(content):
            return True
        return self.update_groups(content)

    def update_info(self, inputfile=None, outputfile=None, timelimit=None, memorylimit=None, interactive=None):
        """
        Updates problem info
        :param inputfile: input file name or None if no update required
        :param outputfile: output file name or None if no update required
        :param timelimit: timelimit in milliseconds or None if no update required
        :param memorylimit: memorylimit in MB or None if no update required
        :param interactive: boolean, if problem is interactive, or None if no update required
        :returns boolean, if updated
        """
        options = {}

        def add_option(name, value):
            if value is not None:
                options[name] = value

        add_option('inputFile', inputfile)
        add_option('outputFile', outputfile)
        add_option('timeLimit', timelimit)
        add_option('memoryLimit', memorylimit)
        add_option('interactive', interactive)
        try:
            self.send_api_request('problem.updateInfo', options)
        except PolygonApiError as e:
            print(e)
            return False
        return True

    def set_test_group(self, tests, group):
        for i in tests:
            self.send_api_request('problem.saveTest', {'testset': 'tests', 'testIndex': i, 'testGroup': group})

    def set_test_score(self, test, group, score):
        data = {'testset': 'tests', 'testIndex': test, 'testGroup': group, 'testPoints': score}
        if score is None:
            del data['testPoints']
        self.send_api_request('problem.saveTest', data)

    def get_tests(self):
        return self.send_api_request('problem.tests', {'testset': 'tests'})

    def get_hand_tests_list(self, tests):
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

    def download_last_package(self):
        url = self.make_link('package', ssid=True, ccid=True)
        data = self.send_request('GET', url).text
        parser = PackageParser()
        parser.feed(data)
        print(parser.url)
        if parser.url is None:
            print('No package created')
            return
        link = self.make_link(parser.url, ssid=True, ccid=False)
        filename = parser.url
        filename = filename[:filename.find('.zip')]
        filename = filename[filename.rfind('/') + 1:]
        filename = filename[:filename.rfind('-')]
        f = open('%s.zip' % (filename), 'wb')
        r = self.send_request('GET', link)
        for c in r.iter_content(1024):
            if (c):
                f.write(c)
        f.close()

    def save_statement_from_file(self, filepath, encoding, language, set_limits=False):
        existing_statements = self.send_api_request('problem.statements', {})
        if existing_statements and language in existing_statements:
            print('Statement of language %s already exists' % language)
            return False
        statement_file = open(filepath, 'r', encoding=encoding)
        options = {'lang': language, 'encoding': 'UTF-8'}
        content = statement_file.read()
        statement_file.close()
        options['name'] = content[len('\\begin{problem}{'):content.find('}', len('\\begin{problem}{'))]
        if set_limits:
            tl = None
            ml = None
            match = re.search("{\s*([\d.]+)\s+sec[^}]*}", content)
            if match is not None:
                tl = match.group(1)
                print('Found TL = {} seconds'.format(tl))
                tl = int(float(tl) * 1000)  # seconds to ms
            match = re.search("{\s*(\d+)\s+[MmмМ][^}]*}", content)
            if match is not None:
                ml = match.group(1)
                print('Found ML = {} mebibytes'.format(ml))
                ml = int(ml)  # bytes to
            self.update_info(None, None, tl, ml, None)
        content = content[content.find('\n') + 1:]
        input_format_start = content.find('\\InputFile')
        options['legend'] = content[:input_format_start]
        content = content[input_format_start:]
        content = content[content.find('\n') + 1:]
        output_format_start = content.find('\\OutputFile')
        options['input'] = content[:output_format_start]
        content = content[output_format_start:]
        content = content[content.find('\n') + 1:]
        options['output'] = content[:content.find('\\Example')]
        notes_start_pos = content.find('\\Note')
        if notes_start_pos >= 0:
            content = content[notes_start_pos:]
            content = content[content.find('\n') + 1:]
            options['notes'] = content[:content.find('\\end{problem}')]
        try:
            self.send_api_request('problem.saveStatement', options)
            return True
        except PolygonApiError as e:
            print(e)
        return False

    def import_problem_from_package(self, directory):
        path_to_problemxml = os.path.join(directory, 'problem.xml')

        def upload_file_from_node(node, type, tag=None):
            if node.find('source') is not None:
                node = node.find('source')
            is_executable = type != 'resource' and type != 'attachment'
            filepath = os.path.join(directory, node.attrib['path'])
            source_type = node.attrib['type'] if is_executable else None
            f = open(filepath, 'rb')
            content = f.read()
            f.close()
            print('Adding ' + type + ': ' + filepath)
            return self.upload_file(os.path.basename(filepath), type, content, True, tag, source_type)

        if os.path.isfile(path_to_problemxml):
            problem_node = ElementTree.parse(path_to_problemxml)
        else:
            print("problem.xml not found or couldn't be opened")
            return
        judging_node = problem_node.find('judging')
        if judging_node is not None:
            input_file_name = judging_node.attrib['input-file']
            output_file_name = judging_node.attrib['output-file']
            if input_file_name == "":
                input_file_name = "stdin"
            if output_file_name == "":
                output_file_name = "stdout"
            any_testset = judging_node.find('testset')
            time_limit = int(any_testset.find('time-limit').text)
            memory_limit = int(any_testset.find('memory-limit').text) // 2 ** 20
            self.update_info(input_file_name, output_file_name, time_limit, memory_limit, None)
        if problem_node.find('tags') is not None:
            tags = []
            for tag_node in problem_node.find('tags').findall('tag'):
                tags.append(tag_node.attrib['value'])
            print('tags:', tags)
            self.send_api_request('problem.saveTags', {'tags': ','.join(tags)})
        if problem_node.find('documents') is not None:
            for document_node in problem_node.find('documents').findall('document'):
                document_path = os.path.join(directory, document_node.attrib['path'])
                if os.path.basename(document_path) == 'description.txt':
                    with open(document_path, 'r') as document_file:
                        description_content = self.send_api_request('problem.viewGeneralDescription', {})
                        if description_content == '':
                            description_content = document_file.read()
                            self.send_api_request('problem.saveGeneralDescription',
                                                  {'description': description_content})
                if os.path.basename(document_path) == 'tutorial.txt':
                    with open(document_path, 'r') as document_file:
                        tutorial_content = self.send_api_request('problem.viewGeneralTutorial', {})
                        if tutorial_content == '':
                            tutorial_content = document_file.read()
                            self.send_api_request('problem.saveGeneralTutorial', {'tutorial': tutorial_content})
        for statement_node in problem_node.find('statements').findall('statement'):
            if not statement_node.attrib['type'].endswith('tex'):
                continue
            self.save_statement_from_file(os.path.join(directory, statement_node.attrib['path']),
                                          statement_node.attrib['charset'], statement_node.attrib['language'])
        assets_node = problem_node.find('assets')
        for solution_node in assets_node.find('solutions').findall('solution'):
            xml_tag_to_api_tag = {'accepted': 'OK',
                                  'main': 'MA',
                                  'time-limit-exceeded': 'TL',
                                  'memory-limit-exceeded': 'ML',
                                  'wrong-answer': 'WA',
                                  'incorrect': 'RJ',
                                  'rejected': 'RJ',
                                  'time-limit-exceeded-or-accepted': "TO",
                                  'time-limit-exceeded-or-memory-limit-exceeded': "TM",
                                  'presentation-error': "PE",
                                  'do-not-run': "NR",
                                  'failed': "RE"}
            upload_file_from_node(solution_node, 'solution', xml_tag_to_api_tag[solution_node.attrib['tag']])
        files_node = problem_node.find('files')
        if files_node is not None:
            resources_node = files_node.find('resources')
            if resources_node is not None:
                for resource_node in resources_node.findall('file'):
                    filepath = resource_node.attrib['path']
                    if filepath.endswith('testlib.h') or filepath.endswith('olymp.sty') or \
                            filepath.endswith('problem.tex') or filepath.endswith('statements.ftl'):
                        continue
                    upload_file_from_node(resource_node, 'resource')
            attachments_node = files_node.find('attachments')
            if attachments_node is not None:
                for attachment_node in attachments_node.findall('file'):
                    upload_file_from_node(attachment_node, 'attachment')
            executables_node = files_node.find('executables')
            if executables_node is not None:
                for executable_node in executables_node.findall('executable'):
                    upload_file_from_node(executable_node, 'source')
        for checker_node in assets_node.findall('checker'):
            if 'name' in checker_node.attrib and checker_node.attrib['name'].startswith('std::'):
                checker_name = checker_node.attrib['name']
            else:
                checker_name = os.path.basename(checker_node.find('source').attrib['path'])
            self.set_utility_file(checker_name, 'checker')
        validators_node = assets_node.find('validators')
        if validators_node is not None:
            for validator_node in validators_node.findall('validator'):
                self.set_utility_file(os.path.basename(validator_node.find('source').attrib['path']), 'validator')
        for testset_node in problem_node.find('judging').findall('testset'):
            testset_name = testset_node.attrib['name']
            input_pattern = testset_node.find('input-path-pattern').text
            print('testset = ' + testset_name)
            test_id = 0
            script = ''
            tests_from_file = {}
            groups = {}
            script_tests_in_statements = []
            for test_node in testset_node.find('tests').findall('test'):
                test_id += 1
                if 'group' in test_node.attrib:
                    group = test_node.attrib['group']
                    if group not in groups:
                        groups[group] = []
                    groups[group].append(str(test_id))
                if test_node.attrib['method'] == 'manual':
                    options = {}
                    options['checkExisting'] = 'true'
                    options['testset'] = testset_name
                    options['testIndex'] = str(test_id)
                    test_file = open(os.path.join(directory, input_pattern % test_id), 'r')
                    options['testInput'] = test_file.read()
                    test_file.close()
                    if 'sample' in test_node.attrib:
                        options['testUseInStatements'] = test_node.attrib['sample']
                    try:
                        print('Adding test %d' % test_id)
                        self.send_api_request('problem.saveTest', options)
                    except PolygonApiError as e:
                        print(e)
                else:
                    if 'sample' in test_node.attrib and test_node.attrib['sample'] == 'true':
                        script_tests_in_statements.append(test_id)
                    if 'from-file' in test_node.attrib:
                        cmd = test_node.attrib['cmd']
                        if not cmd in tests_from_file:
                            tests_from_file[cmd] = []
                        tests_from_file[cmd].append(int(test_node.attrib['from-file']))
                    else:
                        script_line = test_node.attrib['cmd'] + ' > $'  # (' > %d' % test_id)
                        script += script_line + '\n'
                        print('Added "' + script_line + '" to script')
            for cmd in tests_from_file:
                tests_list = tests_from_file[cmd]
                tests_list.sort()
                i = 0
                tests_str = ''
                while i < len(tests_list):
                    j = i + 1
                    while j < len(tests_list) and tests_list[j] - tests_list[i] == j - i:
                        j += 1
                    if len(tests_str) > 0:
                        tests_str += ','
                    tests_str += str(tests_list[i]) if i + 1 == j else '%d-%d' % (tests_list[i], tests_list[j - 1])
                    i = j
                script = ('%s > {%s}\n' % (cmd, tests_str)) + script
            if len(script) > 0:
                try:
                    self.send_api_request('problem.saveScript', {'testset': testset_name,
                                                                 'source': script})
                except PolygonApiError as e:
                    print(e)
            for test in script_tests_in_statements:
                try:
                    self.send_api_request('problem.saveTest', {'testset': testset_name,
                                                               'checkExisting': 'false',
                                                               'testIndex': str(test),
                                                               'testUseInStatements': 'true'})
                except PolygonApiError as e:
                    print(e)
            if len(groups) > 0:
                self.ensure_groups_enabled(testset_name)
            for group, tests in groups.items():
                print('Setting group %s for tests %s' % (group, str(tests)))
                self.set_test_group(tests, group)
            assert (test_id == int(testset_node.find('test-count').text))

    def ensure_groups_enabled(self, testset_name):
        if testset_name not in self.groups_enabled:
            self.groups_enabled.add(testset_name)
            if self.send_api_request('problem.enableGroups',
                                     {'testset': testset_name, 'enable': 'true'}, is_json=False) is None:
                print("Couldn't enable groups for testset %s" % testset_name)

    def ensure_scores_enabled(self):
        if not self.scores_enabled:
            self.scores_enabled = True
            if self.send_api_request('problem.enablePoints',
                                     {'enable': 'true'}, is_json=False) is None:
                print("Couldn't enable scores for problem")

    def set_test_group_deps(self, group, depends):
        self.send_api_request('problem.saveTestGroup', {
            'testset': 'tests',
            'group': group,
            'pointsPolicy': 'COMPLETE_GROUP',
            'dependencies': ','.join(map(str, depends))
        })
