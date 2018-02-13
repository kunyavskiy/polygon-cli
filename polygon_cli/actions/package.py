from .common import *


def process_download_last_package(options):
    if not load_session_with_options(options):
        fatal('No session known. Use relogin or init first.')
    global_vars.problem.download_last_package()
    save_session()


def add_parser(subparsers):
    parser_download_package = subparsers.add_parser(
            'download_package',
            help="Downloads package"
    )
    parser_download_package.set_defaults(func=process_download_last_package)
