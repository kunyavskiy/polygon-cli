from prettytable import PrettyTable

from .common import *
from .. import colors
from ..local_file import LocalFile


def process_add(file_type, solution_type, files):
    real_file_type = file_type
    if file_type in ['checker', 'validator', 'interactor']:
        if len(files) != 1:
            fatal('can''t set several ' + file_type + 's')
        file_type = 'source'
    if solution_type is not None:
        if file_type != 'solution':
            fatal('solution type can be set only on solutions')
        if solution_type == 'MAIN':
            solution_type = 'MA'
    table = PrettyTable(['File type', 'Polygon name', 'Local path', 'Status'])
    for filename in files:
        local_file = LocalFile(os.path.basename(filename),
                               os.path.dirname(filename),
                               str(os.path.basename(filename).split('.')[0]),
                               file_type
                               )
        local = global_vars.problem.get_local_by_filename(local_file.filename)
        if local is not None:
            print('file %s already added, use commit instead' % local.filename)
            status = colors.warning('Already added')
        else:
            local = local_file
            if solution_type is not None:
                local.tag = solution_type
            if local.upload():
                status = colors.success('Uploaded')
                global_vars.problem.local_files.append(local)
                if real_file_type != file_type:
                    global_vars.problem.set_utility_file(local.polygon_filename, real_file_type)
            else:
                status = colors.error('Error')
        table.add_row([local.type, local.polygon_filename, local.get_path(), status])
    print(table)


def add_parser(subparsers):
    parser_add = subparsers.add_parser(
            'add',
            help="Upload files to polygon"
    )
    parser_add.add_argument('file_type', choices=['solution', 'resource', 'source', 'attachment', 'checker',
                                                  'validator', 'interactor', 'statement', 'statementResource'],
                            help='Type of file to add')
    parser_add.add_argument('-t', dest='solution_type',
                            choices=['MAIN', 'OK', 'RJ', 'TL', 'WA', 'PE', 'ML', 'RE', 'TO', 'NR', 'TM'],
                            help='Solution type')
    parser_add.add_argument('file', nargs='+', help='List of files to add')

    def read_options(options):
        if not load_session_with_options(options):
            fatal('No session known. Use relogin or init first.')
        process_add(options.file_type, options.solution_type, options.file)
        save_session()

    parser_add.set_defaults(func=read_options)
