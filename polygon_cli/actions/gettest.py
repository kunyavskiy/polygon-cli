from .common import *


def process_get_test(tests):
    if not load_session():
        fatal('No session known. Use init first.')
    for i in tests:
        global_vars.problem.download_test(i)
    save_session()


def process_get_all_tests():
    if not load_session():
        fatal('No session known. Use init first.')
    global_vars.problem.download_all_tests()
    save_session()


def add_parser(subparsers):
    parser_get_test = subparsers.add_parser(
            'gettest',
            help="Downloads test with given numbers"
    )
    parser_get_test.add_argument('numbers', nargs='+', help='Tests to download')
    parser_get_test.set_defaults(func=lambda options: process_get_test(options.numbers))

    parser_get_all_tests = subparsers.add_parser(
            'getalltests',
            help="Downloads alls tests"
    )
    parser_get_all_tests.set_defaults(func=lambda options: process_get_all_tests())
