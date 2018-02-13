from prettytable import PrettyTable

from .common import *
from .. import colors
from ..local_file import LocalFile


def process_update(flat, to_update):
    files = global_vars.problem.get_all_files_list()
    table = PrettyTable(['File type', 'Polygon name', 'Local path', 'Status'])
    for file in files:
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
            utils.safe_rewrite_file(local_file.get_path(), content, "wb")
            utils.safe_rewrite_file(local_file.get_internal_path(), content, "wb")
            global_vars.problem.local_files.append(local_file)
        table.add_row([file.type, file.name, local_file.get_path(), status])
    print(table)


def add_parser(subparsers):
    parser_update = subparsers.add_parser(
            'update',
            help="Download files from polygon working copy, and merge with local copy"
    )
    parser_update.add_argument('--flat', action='store_true', help='Load files in current folder, not subdirectories')
    parser_update.add_argument('file', nargs='*', help='List of files to download (all by default)')

    def process_options(options):
        if not load_session_with_options(options):
            fatal('No session known. Use init first.')
        process_update(options.flat, options.file)
        save_session()
    parser_update.set_defaults(func=process_options)
