import os
import sys
import getpass
import yaml


polygon_url = "https://polygon.codeforces.com"


authentication_file = os.path.join(os.path.expanduser('~'), '.config', 'polygon-cli', 'auth.yaml')
if os.path.exists(authentication_file):
    with open(authentication_file, 'r') as fo:
        auth_data = yaml.load(fo, Loader=yaml.BaseLoader)
    login = auth_data.get('login')
    password = auth_data.get('password')
    api_key = auth_data.get('api_key')
    api_secret = auth_data.get('api_secret')

if not os.path.exists(authentication_file) or not login or not api_key or not api_secret:
    print('WARNING: Authentication data will be stored in plain text in {}'.format(authentication_file))
    login = input('Login: ')
    password = getpass.getpass('Password (leave blank if you want to enter it when needed): ')
    api_key = input('API Key: ')
    api_secret = input('API Secret: ')
    os.makedirs(os.path.dirname(authentication_file), exist_ok=True)
    with open(authentication_file, 'w') as fo:
        auth_data = {
            'login': login,
            'password': password,
            'api_key': api_key,
            'api_secret': api_secret
        }
        yaml.dump(auth_data, fo, default_flow_style=False)
    print('Authentication data is stored in {}'.format(authentication_file))


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
    'test': 'tests',
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
    if sys.platform == 'darwin':
        return ' '.join(["diff3", "--merge", our, old, theirs])
    else:
        return ' '.join(["diff3", "--strip-trailing-cr", "--merge", our, old, theirs])


def get_diff_tool(old, our, theirs):
    return ' '.join(["diff", theirs, our])
