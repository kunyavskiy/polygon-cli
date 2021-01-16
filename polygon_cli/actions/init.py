from prettytable import PrettyTable

from .common import *
from .. import colors
from .. import config
from .. import global_vars


def process_init(polygon_name, problem_id, pin, **session_options):
    config.setup_login_by_url(polygon_name)
    if not problem_id.isdigit():
        session = ProblemSession(polygon_name, None, None, **session_options)
        problems = session.send_api_request('problems.list', {}, problem_data=False)
        list = []
        for i in problems:
            if i["name"] == problem_id:
                list.append(i)
        if len(list) == 0:
            print('No problem %s found' % problem_id)
            exit(0)
        if len(list) == 1:
            problem_id = list[0]["id"]
            print('Detected problem id is %s' % problem_id)
        if len(list) == 2:
            print('Problem %s is ambigious, choose by id' % problem_id)
            table = PrettyTable(['Id', 'Name', 'Owner', 'Access'])
            for i in list:
                table.add_row([i["id"], i["name"], i["owner"], i["accessType"]])
            print(table)
            exit(0)
    global_vars.problem = ProblemSession(polygon_name, problem_id, pin, **session_options)
    save_session()


def process_init_contest(polygon_name, contest_id, pin, **session_options):
    config.setup_login_by_url(polygon_name)
    contest = ProblemSession(polygon_name, None, pin, **session_options)
    problems = contest.get_contest_problems(contest_id)
    print(problems)
    result = PrettyTable(['Problem name', 'Problem id', 'Status'])

    for problem in problems.keys():
        if os.path.exists(problem):
            result.add_row([problem, problems[problem], colors.error('Directory exists')])
        else:
            try:
                os.mkdir(problem)
                old_path = os.getcwd()
                os.chdir(problem)
                process_init(polygon_name, str(problems[problem]), pin, **session_options)
                os.chdir(old_path)
                result.add_row([problem, problems[problem], colors.success('Done')])
            except Exception as e:
                print(e)
                result.add_row([problem, problems[problem], colors.error('Exception during init')])

    print(result)


def add_parser(subparsers):
    parser_init = subparsers.add_parser(
            'init',
            help="Initialize tool"
    )
    parser_init.add_argument('problem_id', help='Problem id to work with')
    parser_init.add_argument('--pin', dest='pin', default=None, help='Pin code for problem')
    parser_init.set_defaults(func=lambda options: process_init(options.polygon_name, options.problem_id, options.pin, **get_session_options(options)))
    parser_init.add_argument('--polygon-name',
                        action='store',
                        dest='polygon_name',
                        help='Name of polygon server to use for this problem',
                        default='main'
                        )

    parser_init_contest = subparsers.add_parser(
            'init_contest',
            help="Initialize tool for several problems in one contest"
    )
    parser_init_contest.add_argument('contest_id', help='Contest id to init')
    parser_init_contest.add_argument('--pin', dest='pin', default=None, help='Pin code for contest')
    parser_init_contest.add_argument('--polygon-name',
                        action='store',
                        dest='polygon_name',
                        help='Name of polygon server to use for this problem',
                        default='main'
                        )
    parser_init_contest.set_defaults(func=lambda options: process_init_contest(options.polygon_name, options.contest_id, options.pin, **get_session_options(options)))
