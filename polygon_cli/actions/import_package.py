from .common import *


def process_import_problem_from_package(directory):
    if not load_session():
        fatal('No session known. Use relogin or init first.')
    global_vars.problem.import_problem_from_package(directory)
    save_session()


def add_parser(subparsers):
    parser_import_problem_from_package = subparsers.add_parser(
            'import_package',
            help="Imports problem from polygon package"
    )
    parser_import_problem_from_package.\
        add_argument('directory', help='Extracted package directory, which contains problem.xml')
    parser_import_problem_from_package.\
        set_defaults(func=lambda options: process_import_problem_from_package(options.directory))
