from prettytable import PrettyTable

from .common import *


def process_tag_problem(tags):
    global_vars.problem.send_api_request('problem.saveTags', {'tags': ','.join(tags)})


def add_parser(subparsers):
    parser_add = subparsers.add_parser(
        'tag_problem',
        help="Saves tags for the problem. Existed tags will be replaced by new tags"
    )
    parser_add.add_argument('tags', nargs='+', 
                            help="Non-empty sequnce of tags. If you specified several same tags will be add only one of them")

    def read_options(options):
        if not load_session_with_options(options):
            fatal('No session known. Use relogin or init first.')
        process_tag_problem(options.tags)
        save_session()

    parser_add.set_defaults(func=read_options)
