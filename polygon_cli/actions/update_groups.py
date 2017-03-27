from .common import *


def update_groups():
    if not load_session():
        fatal('No session known. Use init first.')
    content = global_vars.problem.get_script_content()
    global_vars.problem.update_groups(content)
    save_session()


def add_parser(subparsers):
    parser_update_groups = subparsers.add_parser(
            'update_groups',
            help="Update groups for tests using script file"
    )
    parser_update_groups.set_defaults(func=lambda options: update_groups())
