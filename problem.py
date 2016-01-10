import requests

import config
import utils
from exceptions import PolygonNotLoginnedError, ProblemNotFoundError
from polygon_html_parsers import *


class ProblemSession:
    def __init__(self, address, problem_id):
        self.polygon_address = address
        self.problem_id = problem_id
        self.session = requests.session()
        self.sessionId = None
        self.ccid = None

    def use_ready_session(self, data):
        cookies = data["cookies"]
        for i in cookies.keys():
            self.session.cookies.set(i, cookies[i])
        self.ccid = data["ccid"]
        assert self.problem_id == data["problemId"]
        self.sessionId = data["sessionId"]

    def dump_session(self):
        data = dict()
        data["problemId"] = self.problem_id
        data["sessionId"] = self.sessionId
        data["cookies"] = self.session.cookies.get_dict()
        data["ccid"] = self.ccid
        return data

    def make_link(self, link, ccid=False, ssid=False):
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
        print('Sending request to ' + utils.prepare_url_print(url), end=' ')
        result = self.session.request(method, url, **kw)
        print(result.status_code)
        if result.url and result.url.startswith(config.polygon_url + '/login'):
            raise PolygonNotLoginnedError()
        return result

    def login(self, login, password):
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
        url = self.make_link('problems', ccid=True)
        problems_page = self.send_request('GET', url).text
        parser = ProblemsPageParser(self.problem_id)
        parser.feed(problems_page)
        return {'continue': parser.continueLink,
                'discard': parser.discardLink,
                'start': parser.startLink}

    def create_new_session(self, login, password):
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
        url = self.make_link('solutions', ccid=True, ssid=True)
        solutions_page = self.send_request('GET', url)
        parser = SolutionsPageParser()
        parser.feed(solutions_page.text)
        solutions = parser.solutions
        for i in range(len(solutions)):
            solutions[i].normalize(self)
        return solutions

    def upload_solution(self, name, content):
        fields = {
            'solutions_file_type': ('', ''),
            'submitted': ('', 'true'),
            'solutions_file_added': (name, content),
            'ccid': ('', self.ccid),
            'session': ('', self.sessionId)
        }
        r = self.send_request('POST', self.make_link('solutions'), files=fields)
        open("results.html", 'w').write(r.text)
        parser = FindUploadErrorParser()
        parser.feed(r.text)
        if parser.error:
            print('Received error:')
            print(parser.error)
            return False
        return True

    def edit_solution(self, name, content):
        fields = {
            'type': 'solutions',
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
