from prettytable import PrettyTable

from .common import *


def process_list():
    if not load_session():
        fatal('No session known. Use init first.')
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


def add_parser(subparsers):
    parser_list = subparsers.add_parser(
            'list',
            help="List files in polygon"
    )
    parser_list.set_defaults(func=lambda options: process_list())
