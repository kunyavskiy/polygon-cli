#!/usr/bin/env python3
import argparse
from sys import argv

from .actions import add as add_action
from .actions import commit as commit_action
from .actions import diff as diff_action
from .actions import gettest as get_test_action
from .actions import init as init_action
from .actions import list as list_action
from .actions import relogin as relogin_action
from .actions import update as update_action
from .exceptions import PolygonNotLoginnedError

parser = argparse.ArgumentParser(prog="polygon-cli")
subparsers = parser.add_subparsers(
        title='available subcommands',
        description='',
        help='DESCRIPTION',
        metavar="SUBCOMMAND",
)

subparsers.required = True

init_action.add_parser(subparsers)
relogin_action.add_parser(subparsers)
update_action.add_parser(subparsers)
add_action.add_parser(subparsers)
commit_action.add_parser(subparsers)
list_action.add_parser(subparsers)
diff_action.add_parser(subparsers)
get_test_action.add_parser(subparsers)


def main():
    try:
        options = parser.parse_args(argv[1:])
        options.func(options)
    except PolygonNotLoginnedError:
        print('Can not login to polygon. Use relogin to update session')


if __name__ == "__main__":
    main()
