from prettytable import PrettyTable

from .common import *


def process_tag_solution(solution, tags):
    for i in range(len(tags)):
        data={
            'action':'solutionTestsetOrTestGroupTagChangeType',
            'solutionFileName':solution,
            'tagFor':'testGroup',
            'tagForName':str(i),
            'submitted':True,
            'chosenType':tags[i]
        }
        print(data)
        global_vars.problem.send_request('POST', global_vars.problem.make_link('solutions',ccid=True,ssid=True), data=data)


def add_parser(subparsers):
    parser_add = subparsers.add_parser(
        'tag_solution',
        help="Set group tags for solution"
    )
    parser_add.add_argument('solution', help='solution filename')
    parser_add.add_argument('tags', nargs='+',
                            choices=['MAIN', 'OK', 'RJ', 'TL', 'WA', 'PE', 'ML', 'RE', 'TO'])

    def read_options(options):
        if not load_session_with_options(options):
            fatal('No session known. Use relogin or init first.')
        process_tag_solution(options.solution, options.tags)
        save_session()

    parser_add.set_defaults(func=read_options)
