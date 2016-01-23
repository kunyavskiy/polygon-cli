from .common import *
from .init import process_init


def process_relogin():
    if not load_session() or global_vars.problem.problem_id is None:
        fatal('No problemId known. Use init instead.')
    local_files = global_vars.problem.local_files
    process_init(global_vars.problem.problem_id)
    global_vars.problem.local_files = local_files
    save_session()


def add_parser(subparsers):
    parser_relogin = subparsers.add_parser(
            'relogin',
            help="Create new polygon http session for same problem"
    )
    parser_relogin.set_defaults(func=lambda options: process_relogin())
