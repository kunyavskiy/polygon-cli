#!/usr/bin/env python3
import json
import os
import sys
from getpass import getpass
from sys import argv

from prettytable import PrettyTable

import config
import global_vars
import json_encoders
import utils
from exceptions import PolygonNotLoginnedError
from local_file import LocalFile
from problem import ProblemSession


def fatal(error):
    print(error)
    exit(0)


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


def process_relogin(args):
    if len(args) != 0:
        print_help()
    if not load_session() or global_vars.problem.problem_id is None:
        fatal('No problemId known. Use init instead.')
    local_files = global_vars.problem.local_files
    process_init([global_vars.problem.problem_id])
    global_vars.problem.local_files = local_files
    save_session()


def process_update(args):
    if not load_session() or global_vars.problem.sessionId is None:
        fatal('No session known. Use relogin or init first.')
    if len(args) == 0:
        files = global_vars.problem.get_all_files_list()
        for file in files:
            if file.type == 'resource':
                continue
            local_file = global_vars.problem.get_local_by_polygon(file)
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


def process_add(args):
    if not load_session() or global_vars.problem.sessionId is None:
        fatal('No session known. Use relogin or init first.')
    if len(args) < 2:
        print_help()
    valid_types = ['solution', 'source', 'checker', 'validator']
    if args[0] not in valid_types:
        fatal('type should be in ' + str(valid_types))
    as_checher = False
    as_validator = False
    if args[0] == 'checker' or args[0] == 'validator':
        if len(args) != 2:
            fatal('can''t set several ' + args[0] + 's')
        if args[0] == 'checker':
            as_checher = True
        else:
            as_validator = True
        args[0] = 'source'
    for filename in args[1:]:
        local = global_vars.problem.get_local_by_filename(os.path.basename(filename))
        if local is not None:
            print('file %s already added, use commit instead' % os.path.basename(filename))
            continue
        local = LocalFile(os.path.basename(filename),
                          os.path.dirname(filename),
                          str(os.path.basename(filename).split('.')[0]),
                          args[0]
                          )
        if local.upload():
            global_vars.problem.local_files.append(local)
            if as_checher:
                global_vars.problem.set_checker_validator(local.polygon_filename, 'checker')
            if as_validator:
                global_vars.problem.set_checker_validator(local.polygon_filename, 'validator')
    save_session()


def process_commit(args):
    if not load_session() or global_vars.problem.sessionId is None:
        fatal('No session known. Use relogin or init first.')
    if len(args):
        raise NotImplementedError("uploading not all files")
    files = global_vars.problem.local_files
    polygon_files = global_vars.problem.get_all_files_list()
    for file in files:
        polygon_file = None
        if file.polygon_filename:
            for p in polygon_files:
                if p.name == file.polygon_filename:
                    polygon_file = p
        if polygon_file is None:
            file.polygon_filename = None
            if file.polygon_filename:
                print('polygon_file for %s was removed. Adding it back.' % file.name)
            else:
                print('Adding new file %s to polygon' % file.name)
            file.upload()
        else:
            polygon_text = polygon_file.get_content()
            old_path = file.get_internal_path()
            try:
                old_text = open(old_path, 'r').read()
            except IOError:
                print('file %s is outdated: update first' % file.name)
                continue
            if polygon_text.splitlines() != old_text.splitlines():
                print('file %s is outdated: update first' % file.name)
                continue
            new_text = open(file.get_path(), 'r').read()
            if polygon_text.splitlines() == new_text.splitlines():
                print('file %s not changed' % file.name)
                continue
            print('uploading file %s' % file.name)
            file.update()
    save_session()


def process_list(args):
    if not load_session() or global_vars.problem.sessionId is None:
        fatal('No session known. Use relogin or init first.')
    files = global_vars.problem.get_all_files_list()
    local_files = global_vars.problem.local_files
    table = PrettyTable(['File type', 'Polygon name', 'Local path', 'Local name'])
    printed_local = set()
    for file in files:
        local = global_vars.problem.get_local_by_polygon(file)
        path = local.get_path() if local else 'None'
        name = local.name if local else 'None'
        table.add_row([file.type, file.name, path, name])
        if name:
            printed_local.add(name)
    for file in local_files:
        if file.name in printed_local:
            continue
        table.add_row([file.type, '!' + file.polygon_filename, file.get_path(), file.name])
    print(table)
    save_session()


def print_help():
    print("""
polygon-cli Tool for using polygon from commandline
Supported commands:
    init <problemId>\tInitialize tool for problem <problemId>
    relogin\t\tCreate new polygon http session for same problem
    update\t\tDownload all files from polygon working copy, and merge with local copy
    commit\t\tPut all local changes to polygon. NOT COMMITING YET!!!!
    add <type> <files>\tUpload files as <type>. <type> can be 'solution', 'source', 'validator' or 'checker'
    list\t\tList files in polygon
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
        elif argv[1] == 'add':
            process_add(argv[2:])
        elif argv[1] == 'commit':
            process_commit(argv[2:])
        elif argv[1] == 'list':
            process_list(argv[2:])
        else:
            print_help()
    except PolygonNotLoginnedError:
        print('Can not login to polygon. Use relogin to update session')


if __name__ == "__main__":
    main()
