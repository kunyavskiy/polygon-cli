#!/usr/bin/env python3
import argparse
import json
import os
import sys
from getpass import getpass
from sys import argv

from prettytable import PrettyTable

from . import colors
from . import config
from . import global_vars
from . import json_encoders
from . import utils
from .exceptions import PolygonNotLoginnedError
from .local_file import LocalFile
from .problem import ProblemSession


def fatal(error):
    print(error)
    exit(0)


def load_session():
    try:
        if os.path.exists(config.get_session_file_path()):
            session_data_json = open(config.get_session_file_path(), 'r').read()
        elif os.path.exists(os.path.join('..', config.get_session_file_path())):
            config.internal_directory_path = os.path.join('..', config.internal_directory_path)
            session_data_json = open(config.get_session_file_path(), 'r').read()
        else:
            return False
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


def process_init(problem_id):
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


def process_relogin():
    if not load_session() or global_vars.problem.problem_id is None:
        fatal('No problemId known. Use init instead.')
    local_files = global_vars.problem.local_files
    process_init(global_vars.problem.problem_id)
    global_vars.problem.local_files = local_files
    save_session()


def process_update(flat, to_update):
    if not load_session() or global_vars.problem.sessionId is None:
        fatal('No session known. Use relogin or init first.')
    files = global_vars.problem.get_all_files_list()
    table = PrettyTable(['File type', 'Polygon name', 'Local path', 'Status'])
    for file in files:
        if file.type == 'resource':
            continue
        local_file = global_vars.problem.get_local_by_polygon(file)
        need_file = file.name in to_update or \
                    local_file is not None and \
                    (local_file.name in to_update or
                     local_file.filename in to_update or
                     local_file.get_path() in to_update)
        if to_update and not need_file:
            continue
        if local_file is not None:
            print('Updating local file %s from %s' % (local_file.name, file.name))
            status = utils.safe_update_file(local_file.get_internal_path(),
                                            local_file.get_path(),
                                            file.get_content()
                                            )
            if status == 'Not changed':
                status = colors.info(status)
            elif status == 'Conflict':
                status = colors.error(status)
            else:
                status = colors.warning(status)
        else:
            status = colors.success('New')
            local_file = LocalFile()
            local_file.name = file.name.split('.')[0]
            local_file.dir = '' if flat else file.get_default_local_dir()
            local_file.type = file.type
            local_file.filename = file.name
            local_file.polygon_filename = file.name
            print('Downloading new file %s to %s' % (file.name, local_file.get_path()))
            content = file.get_content()
            utils.safe_rewrite_file(local_file.get_path(), content)
            utils.safe_rewrite_file(local_file.get_internal_path(), content)
            global_vars.problem.local_files.append(local_file)
        table.add_row([file.type, file.name, local_file.get_path(), status])
    print(table)
    save_session()


def process_add(file_type, solution_type, files):
    if not load_session() or global_vars.problem.sessionId is None:
        fatal('No session known. Use relogin or init first.')
    as_checker = False
    as_validator = False
    if file_type == 'checker' or file_type == 'validator':
        if len(files) != 1:
            fatal('can''t set several ' + file_type + 's')
        if file_type == 'checker':
            as_checker = True
        else:
            as_validator = True
        file_type = 'source'
    if solution_type is not None:
        if file_type != 'solution':
            fatal('solution type can be set only on solutions')
        if solution_type == 'MAIN':
            solution_type = 'MA'
    table = PrettyTable(['File type', 'Polygon name', 'Local path', 'Status'])
    for filename in files:
        local = global_vars.problem.get_local_by_filename(os.path.basename(filename))
        if local is not None:
            print('file %s already added, use commit instead' % os.path.basename(filename))
            status = colors.warning('Already added')
        else:
            local = LocalFile(os.path.basename(filename),
                              os.path.dirname(filename),
                              str(os.path.basename(filename).split('.')[0]),
                              file_type
                              )
            if local.upload():
                status = colors.success('Uploaded')
                global_vars.problem.local_files.append(local)
                if as_checker:
                    global_vars.problem.set_checker_validator(local.polygon_filename, 'checker')
                if as_validator:
                    global_vars.problem.set_checker_validator(local.polygon_filename, 'validator')
                if solution_type is not None:
                    global_vars.problem.change_solution_type(local.polygon_filename, solution_type.upper())
            else:
                status = colors.error('Error')
        table.add_row([local.type, local.polygon_filename, local.filename, status])
    print(table)
    save_session()


def process_commit(to_commit):
    if not load_session() or global_vars.problem.sessionId is None:
        fatal('No session known. Use relogin or init first.')
    files = global_vars.problem.local_files
    polygon_files = global_vars.problem.get_all_files_list()
    table = PrettyTable(['File type', 'Polygon name', 'Local path', 'Status'])
    for file in files:
        polygon_file = None
        if file.polygon_filename:
            for p in polygon_files:
                if p.name == file.polygon_filename:
                    polygon_file = p
        need_file = (polygon_file is not None and polygon_file.name in to_commit) or \
                    file.name in to_commit or \
                    file.filename in to_commit or \
                    file.get_path() in to_commit
        if to_commit and not need_file:
            continue
        if polygon_file is None:
            file.polygon_filename = None
            if file.polygon_filename:
                status = colors.success('Returned')
                print('polygon_file for %s was removed. Adding it back.' % file.name)
            else:
                status = colors.success('New')
                print('Adding new file %s to polygon' % file.name)
            if not file.upload():
                status = colors.error('Error')
            table.add_row([file.type, file.polygon_filename, file.get_path(), status])
        else:
            polygon_text = polygon_file.get_content()
            old_path = file.get_internal_path()
            status = ''
            while True:
                try:
                    old_text = open(old_path, 'r').read()
                except IOError:
                    status = colors.warning('Outdated')
                    print('file %s is outdated: update first' % file.name)
                    break
                if polygon_text.splitlines() != old_text.splitlines():
                    status = colors.warning('Outdated')
                    print('file %s is outdated: update first' % file.name)
                    break
                new_text = open(file.get_path(), 'r').read()
                if polygon_text.splitlines() == new_text.splitlines():
                    status = colors.info('Not changed')
                    print('file %s not changed' % file.name)
                    break
                print('uploading file %s' % file.name)
                if file.update():
                    status = colors.success('Modified')
                else:
                    status = colors.error('Error')
                break
            table.add_row([file.type, file.polygon_filename, file.get_path(), status])
    print(table)
    save_session()


def process_list():
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


def process_diff(filename):
    if not load_session() or global_vars.problem.sessionId is None:
        fatal('No session known. Use relogin or init first.')
    file = global_vars.problem.get_local_by_filename(filename)
    if file is None:
        fatal('File %s not found' % filename)
    polygon_files = global_vars.problem.get_all_files_list()
    polygon_file = None
    if file.polygon_filename:
        for p in polygon_files:
            if p.name == file.polygon_filename:
                polygon_file = p
    if polygon_file is None:
        fatal('File %s not matched to any file in polygon')
    polygon_text = polygon_file.get_content()
    old_path = file.get_internal_path()
    utils.diff_file_with_content(old_path, file.get_path(), polygon_text)
    save_session()


parser = argparse.ArgumentParser(prog="polygon-cli")
subparsers = parser.add_subparsers(
        title='available subcommands',
        description='',
        help='DESCRIPTION',
        metavar="SUBCOMMAND"
)

parser_init = subparsers.add_parser(
        'init',
        help="Initialize tool"
)
parser_init.add_argument('problem_id', help='Problem id to work with')
parser_init.set_defaults(func=lambda options: process_init(options.problem_id))

parser_relogin = subparsers.add_parser(
        'relogin',
        help="Create new polygon http session for same problem"
)
parser_relogin.set_defaults(func=lambda options: process_relogin())

parser_update = subparsers.add_parser(
        'update',
        help="Download files from polygon working copy, and merge with local copy"
)
parser_update.add_argument('--flat', action='store_true', help='Load files in current folder, not solutions/src')
parser_update.add_argument('file', nargs='*', help='List of files to download (all by default)')
parser_update.set_defaults(func=lambda options: process_update(options.flat, options.file))

parser_add = subparsers.add_parser(
        'add',
        help="Upload files to polygon"
)
parser_add.add_argument('file_type', choices=['solution', 'source', 'checker', 'validator'], help='Type of file to add')
parser_add.add_argument('-t', dest='solution_type', choices=['MAIN', 'OK', 'RJ', 'TL', 'WA', 'PE', 'ML', 'RE'],
                        help='Solution type')
parser_add.add_argument('file', nargs='+', help='List of files to add')
parser_add.set_defaults(func=lambda options: process_add(options.file_type, options.solution_type, options.file))

parser_commit = subparsers.add_parser(
        'commit',
        help="Put all local changes to polygon. Not making a commit in polygon"
)
parser_commit.add_argument('file', nargs='+', help='List of files to commit')
parser_commit.set_defaults(func=lambda options: process_commit(options.file))

parser_list = subparsers.add_parser(
        'list',
        help="List files in polygon"
)
parser_list.set_defaults(func=lambda options: process_list())

parser_diff = subparsers.add_parser(
        'diff',
        help="Prints diff of local and polygon version of file"
)
parser_diff.add_argument('file', help='File to make diff')
parser_diff.set_defaults(func=lambda options: process_diff(options.file))


def main():
    try:
        options = parser.parse_args(argv[1:])
        print(options)
        options.func(options)
    except PolygonNotLoginnedError:
        print('Can not login to polygon. Use relogin to update session')


if __name__ == "__main__":
    main()
