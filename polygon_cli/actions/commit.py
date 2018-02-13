from prettytable import PrettyTable

from .common import *
from .. import colors


def process_commit(to_commit):
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
                    old_text = open(old_path, 'rb').read()
                except IOError:
                    status = colors.warning('Outdated')
                    print('file %s is outdated: update first' % file.name)
                    break
                if polygon_text.splitlines() != old_text.splitlines():
                    status = colors.warning('Outdated')
                    print('file %s is outdated: update first' % file.name)
                    break
                new_text = open(file.get_path(), 'rb').read()
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


def add_parser(subparsers):
    parser_commit = subparsers.add_parser(
            'commit',
            help="Put all local changes to polygon. Not making a commit in polygon"
    )
    parser_commit.add_argument('file', nargs='*', help='List of files to commit')

    def read_options(options):
        if not load_session_with_options(options):
            fatal('No session known. Use relogin or init first.')
        process_commit(options.file)
        save_session()
    parser_commit.set_defaults(func=read_options)
