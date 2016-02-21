from .common import *


def process_get_test(tests):
    if not load_session() or global_vars.problem.sessionId is None:
        fatal('No session known. Use relogin or init first.')
    for i in tests:
        global_vars.problem.download_test(i)
    save_session()


def add_parser(subparsers):
    parser_get_test = subparsers.add_parser(
            'gettest',
            help="Downloads test with given numbers"
    )
    parser_get_test.add_argument('numbers', nargs='+', help='Tests to download')
    parser_get_test.set_defaults(func=lambda options: process_get_test(options.numbers))
