import os

polygon_url = "https://polygon.codeforces.com"
login = None
password = None
internal_directory_path = '.polygon-cli'
solutions_path = 'solutions'
sessionFile = 'session.json'


def get_session_file_path():
    return os.path.join(internal_directory_path, sessionFile)


def get_solution_path(solution):
    return os.path.join(solutions_path, solution)


def get_download_solution_path(solution):
    return os.path.join(internal_directory_path, solutions_path, solution)