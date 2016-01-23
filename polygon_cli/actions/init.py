import sys
from getpass import getpass

from .common import *
from .. import config
from .. import global_vars


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


def add_parser(subparsers):
    parser_init = subparsers.add_parser(
            'init',
            help="Initialize tool"
    )
    parser_init.add_argument('problem_id', help='Problem id to work with')
    parser_init.set_defaults(func=lambda options: process_init(options.problem_id))
