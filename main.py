#!/usr/bin/env python3
import json
import os
import sys
from getpass import getpass
from sys import argv

import config
import global_vars
import utils
from problem import ProblemSession
from exceptions import PolygonNotLoginnedError


def load_session():
    try:
        session_data_json = open(config.get_session_file_path(), 'r').read()
        session_data = json.loads(session_data_json)
        global_vars.problem = ProblemSession(config.polygon_url, session_data["problemId"])
        global_vars.problem.use_ready_session(session_data)
        return True
    except:
        return False


def save_session():
    session_data = global_vars.problem.dump_session()
    session_data_json = json.dumps(session_data, sort_keys=True, indent='  ')
    utils.safe_rewrite_file(config.get_session_file_path(), session_data_json)


def process_init(args):
    problem_id = None
    try:
        problem_id = int(args[0])
    except:
        print_help()
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
    global_vars.problem = ProblemSession(config.polygon_url, problem_id)
    global_vars.problem.create_new_session(config.login, config.password)
    save_session()
    exit(0)


def process_relogin(args):
    if len(args) != 0:
        print_help()
    load_session()
    if global_vars.problem.problem_id is None:
        print('No problemId known. Use init instead.')
        exit(0)
    process_init([global_vars.problem.problem_id])


def download_solution(url):
    solution_text = global_vars.problem.send_request('GET', url).text
    return solution_text.replace(' \r\n', '\r\n')


def process_update(args):
    load_session()
    if global_vars.problem.sessionId is None:
        print('No session known. Use relogin or init first.')
        exit(0)
    solutions = global_vars.problem.get_solutions_list()
    try:
        local_solutions = utils.get_local_solutions()
    except FileNotFoundError:
        local_solutions = []

    local_solutions = set(local_solutions)

    for solution in solutions:
        if len(args) and solution.name not in args:
            print('ignoring solution ' + solution.name)
            continue
        solution_text = download_solution(solution.download_link)
        if solution.name not in local_solutions:
            print('New solution found: %s' % solution.name)
            utils.safe_rewrite_file(config.get_solution_path(solution.name), solution_text)
        else:
            print('Updating solution %s' % solution.name)
            old_path = config.get_download_solution_path(solution.name)
            if not os.path.exists(old_path):
                utils.safe_rewrite_file(old_path, '')
            utils.safe_update_file(old_path, config.get_solution_path(solution.name), solution_text)
    save_session()


def process_send(args):
    load_session()
    if global_vars.problem.sessionId is None:
        print('No session known. Use relogin or init first.')
        exit(0)
    solutions = global_vars.problem.get_solutions_list()
    solutions_dict = {i.name: i for i in solutions}
    for name in args:
        if name.startswith(config.solutions_path + '/'):
            name = name[len(config.solutions_path + '/'):]
        if not os.path.exists(config.get_solution_path(name)):
            print('solution %s not found' % name)
            continue
        if name in solutions_dict:
            solution = solutions_dict[name]
            old_path = config.get_download_solution_path(name)
            if not os.path.exists(old_path):
                print('solution %s is outdated: update first' % name)
                continue
            solution_text = download_solution(solution.download_link).splitlines()  # TODO: check some fingerprint
            old_solution_text = open(old_path, 'r').read().splitlines()
            if solution_text != old_solution_text:
                print('solution %s is outdated: update first' % name)
                continue
            print('uploading solution %s' % name)
            content = open(config.get_solution_path(name), 'r').read()
            success = global_vars.problem.edit_solution(name, content)
        else:
            content = open(config.get_solution_path(name), 'r').read()
            success = global_vars.problem.upload_solution(name, content)
        if success:
            utils.safe_rewrite_file(config.get_download_solution_path(name), content)


def process_list(args):
    load_session()
    if global_vars.problem.sessionId is None:
        print('No session known. Use relogin or init first.')
        exit(0)
    files = global_vars.problem.get_all_files_list()
    for file in files:
        print('%s\t%s' % (file.type, file.name))


def print_help():
    print("""
polygon-cli Tool for using polygon from commandline
Supported commands:
    init <problemId>\tinitialize tool for problem <problemId>
    relogin\tCreate new polygon http session for same problem
    update\tDownload all solutions from working copy, and merges with local copy
    send <files>\tUpload files as solutions
    list\tlist of files in polygon
""")
    exit(1)


def main():
    try:
        if len(argv) < 2:
            print_help()
        elif argv[1] == 'init':
            process_init(argv[2:])
        elif argv[1] == 'relogin':
            process_relogin(argv[2:])
        elif argv[1] == 'update':
            process_update(argv[2:])
        elif argv[1] == 'send':
            process_send(argv[2:])
        elif argv[1] == 'list':
            process_list(argv[2:])
        else:
            print_help()
    except PolygonNotLoginnedError:
        print('Can not login to polygon. Use relogin to update session')


if __name__ == "__main__":
    main()
