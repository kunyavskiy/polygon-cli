import os

polygon_url = "https://polygon.codeforces.com"
# change this before installation
# login and password will be used for non-api queries, you may leave them None
# WARNING: this will be stored in plain-text on your computer in Python scripts directory
login = None
password = None
api_key = None
api_secret = None
internal_directory_path = '.polygon-cli'
default_source_types = {
    '.cpp': 'cpp.g++17',
    '.c++': 'cpp.g++17',
    '.py': 'python.3',
    '.java': 'java8',
    '.pas': 'pas.fpc',
}
subdirectory_paths = {
    'attachment': 'src',
    'resource': 'src',
    'solution': 'solutions',
    'source': 'src',
    'script': '',
    'test' : 'tests',
    'statement': 'statements',
}
sessionFile = 'session.json'


def get_session_file_path():
    return os.path.join(internal_directory_path, sessionFile)


def get_solution_path(solution):
    return os.path.join(subdirectory_paths['solutions'], solution)


def get_download_solution_path(solution):
    return os.path.join(internal_directory_path, subdirectory_paths['solutions'], solution)


def get_merge_tool(old, our, theirs):
    return ' '.join(["diff3", "--strip-trailing-cr", "--merge", our, old, theirs])


def get_diff_tool(old, our, theirs):
    return ' '.join(["diff", theirs, our])
