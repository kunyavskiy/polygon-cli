from html.parser import HTMLParser


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
        self.tdId = 0
        self.owner = ''
        self.problemName = ''
        self.problemId = problem_id
        self.numberOfProblemPages = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            if len(attrs) > 1 and attrs[0][0] == "problemid" and attrs[0][1] == str(self.problemId):
                self.inCorrectRow = True
                self.tdId = 0
        elif tag == 'td':
            self.tdId += 1
        elif tag == 'a' and self.inCorrectRow:
            assert attrs[2][0] == 'class'
            if attrs[2][1].startswith('CONTINUE'):
                self.continueLink = attrs[0][1]
            if attrs[2][1].startswith('DISCARD'):
                self.discardLink = attrs[0][1]
            if attrs[2][1].startswith('START'):
                self.startLink = attrs[0][1]
        if tag == 'a' and attrs[0][0] == 'href' and attrs[0][1].find('/problems?page=') >= 0:
            link = attrs[0][1]
            link = link[len('/problems?page='):]
            self.numberOfProblemPages = int(link[:link.find('&')])

    def handle_endtag(self, tag):
        if tag == 'tr':
            self.inCorrectRow = False

    def handle_data(self, data):
        if self.inCorrectRow and self.tdId == 3:
            self.problemName += data.strip()
        if self.inCorrectRow and self.tdId == 4:
            self.owner += data.strip()


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


class PackageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.url = None

    def handle_starttag(self, tag, attrs):
        if self.url is None and tag == "a":
            for e in attrs:
                if e[0] == 'href' and e[1].find('windows.zip') >= 0: # TODO change to something better
                    self.url = e[1]
