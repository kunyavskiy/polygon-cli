from html.parser import HTMLParser

from solution import Solution


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


class SolutionsPageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.solutions = []
        self.in_tbody = False
        self.tdId = -1

    def handle_starttag(self, tag, attrs):
        if tag == 'tbody':
            self.in_tbody = True
            return
        if not self.in_tbody:
            return
        if tag == 'tr':
            self.solutions.append(Solution())
            self.tdId = -1
            return
        if tag == 'td':
            self.tdId += 1
        if tag == 'a' and self.tdId == 6:
            if attrs[0][0] == 'class':
                if attrs[0][1] == 'remove-link':
                    assert attrs[1][0] == 'file'
                    self.solutions[-1].name = attrs[1][1]
                    self.solutions[-1].remove_link = attrs[2][1]
                elif attrs[0][1] == 'edit-link':
                    self.solutions[-1].edit_link = attrs[1][1]
            else:
                self.solutions[-1].download_link = attrs[0][1]

    def handle_endtag(self, tag):
        if tag == 'tbody':
            self.in_tbody = False

    def handle_data(self, data):
        if self.in_tbody and data.strip():
            if self.tdId == 0:
                if data.strip() == 'No files':
                    self.solutions = self.solutions[:-1]
                else:
                    self.solutions[-1].author = data.strip()
            elif self.tdId == 3:
                self.solutions[-1].size = data.strip()
            elif self.tdId == 4:
                self.solutions[-1].date = data.strip()


class FindErrorParser(HTMLParser):
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
