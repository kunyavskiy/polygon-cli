#!/usr/bin/env python3
import argparse
from sys import argv

from .actions import add as add_action
from .actions import commit as commit_action
from .actions import diff as diff_action
from .actions import gettest as get_test_action
from .actions import init as init_action
from .actions import list as list_action
from .actions import update as update_action
from .actions import package as download_package_action
from .actions import samples as samples_action
from .actions import import_package as import_package_action
from .actions import update_groups as update_groups_action
from .actions import update_info as update_info_action
from .actions import tag_solution as tag_solution_action
from .actions import tag_problem as tag_problem_action
from .exceptions import PolygonNotLoginnedError

parser = argparse.ArgumentParser(prog="polygon-cli")
parser.add_argument('-v', '--verbose',
                    action='store_true',
                    dest='verbose',
                    default=True,
                    help='Verbose output')
parser.add_argument('-V', '--no-verbose',
                    action='store_false',
                    dest='verbose',
                    help='Reduce output verbosity')
subparsers = parser.add_subparsers(
        title='available subcommands',
        description='',
        help='DESCRIPTION',
        metavar="SUBCOMMAND",
)

subparsers.required = True

init_action.add_parser(subparsers)
update_action.add_parser(subparsers)
add_action.add_parser(subparsers)
commit_action.add_parser(subparsers)
list_action.add_parser(subparsers)
diff_action.add_parser(subparsers)
get_test_action.add_parser(subparsers)
download_package_action.add_parser(subparsers)
samples_action.add_parser(subparsers)
import_package_action.add_parser(subparsers)
update_groups_action.add_parser(subparsers)
update_info_action.add_parser(subparsers)
tag_solution_action.add_parser(subparsers)
tag_problem_action.add_parser(subparsers)


def main():
    try:
        options = parser.parse_args(argv[1:])
        options.func(options)
    except PolygonNotLoginnedError:
        print('Can not login to polygon.')


if __name__ == "__main__":
    main()
