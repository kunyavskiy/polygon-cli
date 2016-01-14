#!/usr/bin/env python3
import json
import os
import sys
import traceback
from getpass import getpass
from sys import argv

from prettytable import PrettyTable

import config
import global_vars
import json_encoders
import utils
from local_file import LocalFile
from polygon_file import PolygonFile
from problem import ProblemSession
from exceptions import PolygonNotLoginnedError


def load_session():
    try:
        session_data_json = open(config.get_session_file_path(), 'r').read()
        session_data = json.loads(session_data_json, object_hook=json_encoders.my_json_decoder)
        global_vars.problem = ProblemSession(config.polygon_url, session_data["problemId"])
        global_vars.problem.use_ready_session(session_data)
        return True
    except:
        return False


def save_session():
    session_data = global_vars.problem.dump_session()
    session_data_json = json.dumps(session_data, sort_keys=True, indent='  ', default=json_encoders.my_json_encoder)
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
    if not load_session() or global_vars.problem.problem_id is None:
        print('No problemId known. Use init instead.')
        exit(0)
    process_init([global_vars.problem.problem_id])


def process_update(args):
    if not load_session() or global_vars.problem.sessionId is None:
        print('No session known. Use relogin or init first.')
        exit(0)
    if len(args) == 0:
        files = global_vars.problem.get_all_files_list()
        for file in files:
            if file.type == 'resource':
                continue
            local_file = global_vars.problem.get_local(file)
            if local_file is not None:
                print('Updating local file %s from %s' % (local_file.name, file.name))
                utils.safe_update_file(local_file.get_internal_path(),
                                       local_file.get_path(),
                                       file.get_content()
                                       )
            else:
                local_file = LocalFile()
                local_file.name = file.name.split('.')[0]
                local_file.dir = file.get_default_local_dir()
                local_file.type = file.type
                local_file.filename = file.name
                local_file.polygon_filename = file.name
                print('Downloading new file %s to %s' % (file.name, local_file.get_path()))
                content = file.get_content()
                utils.safe_rewrite_file(local_file.get_path(), content)
                utils.safe_rewrite_file(local_file.get_internal_path(), content)
                global_vars.problem.local_files.append(local_file)
    else:
        raise NotImplementedError("updating not all files")
    save_session()


def process_send(args):
    if not load_session() or global_vars.problem.sessionId is None:
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
            solution_text = solution.get_content().splitlines()  # TODO: check some fingerprint
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
    if not load_session() or global_vars.problem.sessionId is None:
        print('No session known. Use relogin or init first.')
        exit(0)
    files = global_vars.problem.get_all_files_list()
    local_files = global_vars.problem.local_files
    table = PrettyTable(['File type', 'Polygon name', 'Local path', 'Local name'])
    printed_local = set()
    for file in files:
        local = global_vars.problem.get_local(file)
        path = local.get_path() if local else 'None'
        name = local.name if local else 'None'
        table.add_row([file.type, file.name, path, name])
        if name:
            printed_local.add(name)
    for file in local_files:
        if file.name in printed_local:
            continue
        table.add_row([file.type, '!' + file.polygon_name, file.get_path(), file.name])
    print(table)


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
