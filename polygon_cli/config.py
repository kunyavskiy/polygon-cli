import os
import sys
import getpass
import yaml

MAIN_POLYGON_URL = 'https://polygon.codeforces.com'

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
    'statementResource': 'statements',
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


def setup_login_by_url(polygon_name):
    global polygon_url, login, password, api_key, api_secret
    authentication_file = os.path.join(os.path.expanduser('~'), '.config', 'polygon-cli', 'auth.yaml')
    auth_data = {}
    if os.path.exists(authentication_file):
        with open(authentication_file, 'r') as fo:
            auth_data = yaml.load(fo, Loader=yaml.BaseLoader)
        if auth_data.get('version') is None:
            with open(authentication_file, 'w') as fo:
                auth_data = {
                    'version': 1,
                    'polygons': {
                        'main': {
                            'url': MAIN_POLYGON_URL,
                            'login': auth_data.get('login'),
                            'password': auth_data.get('password'),
                            'api_key': auth_data.get('api_key'),
                            'api_secret': auth_data.get('api_secret'),
                        }
                    }
                }
                yaml.dump(auth_data, fo, default_flow_style=False)
        auth_data_by_name = auth_data.get('polygons').get(polygon_name)
        if auth_data_by_name:
            polygon_url = auth_data_by_name.get('url')
            login = auth_data_by_name.get('login')
            password = auth_data_by_name.get('password')
            api_key = auth_data_by_name.get('api_key')
            api_secret = auth_data_by_name.get('api_secret')

    if not login or not api_key or not api_secret:
        print('No login data found for polygon name ' + polygon_name)
        print('WARNING: Authentication data will be stored in plain text in {}'.format(authentication_file))
        if polygon_name == 'main':
            polygon_url = MAIN_POLYGON_URL
            print('main polygon url is ' + polygon_url + '\n')
        elif polygon_name == 'lksh':
            polygon_url = 'https://polygon.lksh.ru'
            print('lksh polygon url is ' + polygon_url + '\n')
        else:
            polygon_url = input('Url: ').strip()
        login = input('Login: ').strip()
        password = getpass.getpass('Password (leave blank if you want to enter it when needed): ').strip()
        api_key = input('API Key: ').strip()
        api_secret = input('API Secret: ').strip()
        os.makedirs(os.path.dirname(authentication_file), exist_ok=True)
        with open(authentication_file, 'w') as fo:
            if 'polygons' not in auth_data:
                auth_data['polygons'] = {}
            auth_data['polygons'][polygon_name] = {
                'url': polygon_url,
                'login': login,
                'password': password,
                'api_key': api_key,
                'api_secret': api_secret
            }
            yaml.dump(auth_data, fo, default_flow_style=False)
        print('Authentication data is stored in {}'.format(authentication_file))


polygon_url = None
login = None
password = None
api_key = None
api_secret = None
