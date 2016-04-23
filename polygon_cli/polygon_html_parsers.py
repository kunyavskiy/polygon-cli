from html.entities import name2codepoint
from html.parser import HTMLParser

from .polygon_file import PolygonFile


class ExtractCCIDParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ccid = None

    def handle_starttag(self, tag, attrs):
        if tag == "meta":
            if len(attrs) == 2 and attrs[0][0] == 'name' and attrs[0][1] == 'ccid' and attrs[1][0] == 'content':
                self.ccid = attrs[1][1]


class ProblemsPageParser(HTMLParser):
    def __init__(self, problem_id):
        super().__init__()
        self.continueLink = None
        self.discardLink = None
        self.startLink = None
        self.inCorrectRow = False
        self.problemId = problem_id

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            if len(attrs) > 1 and attrs[0][0] == "problemid" and attrs[0][1] == str(self.problemId):
                self.inCorrectRow = True
        elif tag == 'a' and self.inCorrectRow:
            assert attrs[2][0] == 'class'
            if attrs[2][1].startswith('CONTINUE'):
                self.continueLink = attrs[0][1]
            if attrs[2][1].startswith('DISCARD'):
                self.discardLink = attrs[0][1]
            if attrs[2][1].startswith('START'):
                self.startLink = attrs[0][1]

    def handle_endtag(self, tag):
        if tag == 'tr':
            self.inCorrectRow = False


class ContestPageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.problems = {}

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            if len(attrs) >= 2 and attrs[0][0] == "problemid" and attrs[1][0] == 'problemname':
                self.problems[attrs[1][1]] = attrs[0][1]


class ExtractSessionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.session = None
        self.inCorrectSpan = False

    def handle_starttag(self, tag, attrs):
        if tag == "span":
            if len(attrs) == 2 and attrs[1][0] == 'id' and attrs[1][1] == 'session':
                self.inCorrectSpan = True

    def handle_endtag(self, tag):
        self.inCorrectSpan = False

    def handle_data(self, data):
        if self.inCorrectSpan:
            self.session = data


class FileListParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.files = []
        self.in_tbody = False
        self.td_id = -1
        self.tbody_id = -1

    def get_file_type(self):
        return None

    def handle_starttag(self, tag, attrs):
        if tag == 'tbody':
            self.in_tbody = True
            self.tbody_id += 1
            return
        if not self.in_tbody:
            return
        if tag == 'tr':
            self.files.append(PolygonFile())
            self.files[-1].type = self.get_file_type()
            self.td_id = -1
            return
        if tag == 'td':
            self.td_id += 1
        if tag == 'a':
            if attrs[0][0] == 'class':
                if attrs[0][1] == 'edit-link':
                    self.files[-1].edit_link = attrs[1][1]
            for attr in attrs:
                if attr[0] == 'href' and attr[1].find('action=view') != -1:
                    self.files[-1].download_link = attrs[0][1]
                elif attr[0] == 'href' and attr[1].find('action=remove') != -1:
                    self.files[-1].remove_link = attrs[0][1]

    def handle_endtag(self, tag):
        if tag == 'tbody':
            self.in_tbody = False


class SolutionsPageParser(FileListParser):
    def get_file_type(self):
        return 'solution'

    def handle_data(self, data):
        if self.in_tbody and data.strip():
            if self.td_id == 0:
                if data.strip() == 'No files':
                    self.files = self.files[:-1]
            elif self.td_id == 1 and not self.files[-1].name:
                self.files[-1].name = data.strip()
            elif self.td_id == 3:
                self.files[-1].size = data.strip()
            elif self.td_id == 4:
                self.files[-1].date = data.strip()


class FilesPageParser(FileListParser):
    def get_file_type(self):
        if self.tbody_id == 0:
            return 'resource'
        elif self.tbody_id == 1:
            return 'source'
        elif self.tbody_id == 2:
            return 'attachment'
        else:
            return None

    def handle_data(self, data):
        if self.in_tbody and data.strip():
            if self.td_id == 0:
                if data.strip() == 'No files':
                    self.files = self.files[:-1]
                elif not self.files[-1].name:
                    self.files[-1].name = data.strip()
            elif self.td_id == 2:
                self.files[-1].size = data.strip()
            elif self.td_id == 3:
                self.files[-1].date = data.strip()


class FindEditErrorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.error = None
        self.inError = False

    def handle_starttag(self, tag, attrs):
        if tag == 'td' and len(attrs) == 1 and attrs[0][0] == 'class' and attrs[0][1] == 'field-error':
            self.inError = True
            return

    def handle_endtag(self, tag):
        self.inError = False

    def handle_data(self, data):
        if self.inError and data.strip():
            self.error = data.strip()


class FindUploadErrorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.error = None
        self.inError = False

    def handle_starttag(self, tag, attrs):
        if tag == 'div' and len(attrs) == 1 and attrs[0][0] == 'style' and attrs[0][1].startswith('color: red'):
            self.inError = True
            self.error = ''
            return
        if tag == 'br' and self.inError:
            self.error += '\n'

    def handle_endtag(self, tag):
        if tag == 'div':
            self.inError = False

    def handle_data(self, data):
        if self.inError and data.strip():
            self.error += data

    def handle_entityref(self, name):
        if self.inError:
            self.error += chr(name2codepoint[name])


class FindScriptParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inTextArea = False
        self.script = None

    def handle_starttag(self, tag, attrs):
        if tag == 'textarea' and len(attrs) >= 1 and attrs[0][0] == 'id' and attrs[0][1].startswith('script'):
            self.inTextArea = True
            self.script = ''
            return

    def handle_endtag(self, tag):
        if tag == 'textarea':
            self.inTextArea = False

    def handle_data(self, data):
        if self.inTextArea and data.strip():
            self.script += data

    def handle_entityref(self, name):
        if self.inTextArea:
            self.script += chr(name2codepoint[name])


class FindUploadScriptErrorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.error = None
        self.inError = False

    def handle_starttag(self, tag, attrs):
        if tag == 'div' and len(attrs) == 1 and attrs[0][0] == 'class' and attrs[0][1] == 'field-error':
            self.inError = True
            self.error = ''
            return
        if tag == 'br' and self.inError:
            self.error += '\n'

    def handle_endtag(self, tag):
        if tag == 'div':
            self.inError = False

    def handle_data(self, data):
        if self.inError and data.strip():
            self.error += data

    def handle_entityref(self, name):
        if self.inError:
            self.error += chr(name2codepoint[name])


class FindHandTestsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tests = []

    def handle_starttag(self, tag, attrs):
        if tag == "pre":
            if len(attrs) == 2 and attrs[0][0] == 'id' and attrs[0][1].startswith('text'):
                self.tests.append(int(attrs[0][1][4:]))
