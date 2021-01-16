from prettytable import PrettyTable

from .common import *


def process_samples(polygon_name, contest_id, pin, **session_options):
    config.setup_login_by_url(polygon_name)
    contest = ProblemSession(polygon_name, None, pin, **session_options)
    problems = contest.get_contest_problems(contest_id)

    for problem_name in problems:
        print('Downloading for', problem_name)
        contest.problem_id = problems[problem_name]
        tests = contest.send_api_request('problem.tests', {'testset': 'tests'})
        for i in tests:
            if i["useInStatements"]:
                index = i["index"]
                contest.download_test(index, 'examples', problem_name + '%d.in', problem_name + '%d.out')
                if "inputForStatement" in i:
                    while True:
                       print("Problem %s have custom input for sample test %d. Should I download it? (y/n)" % (problem_name, index))
                       ans = input()
                       if ans == 'y' or ans == 'yes':
                          utils.safe_rewrite_file('examples/%s%d.in' % (problem_name, index), i["inputForStatement"])
                          break
                       if ans == 'n' or ans == 'no':
                          break
                if "outputForStatement" in i:
                    utils.safe_rewrite_file('examples/%s%d.out' % (problem_name, index), i["outputForStatement"])



def add_parser(subparsers):
    parser_samples = subparsers.add_parser(
        'samples',
        help="Download samples"
    )

    parser_samples.add_argument('contest_id', help='Contest id to download')
    parser_samples.add_argument('--pin', dest='pin', default=None, help='Pin code for contest')
    parser_samples.add_argument('--polygon-name',
                        action='store',
                        dest='polygon_name',
                        help='Name of polygon server to use for this problem',
                        default='main'
                        )

    def read_options(options):
        process_samples(options.polygon_name, options.contest_id, options.pin, **get_session_options(options))

    parser_samples.set_defaults(func=read_options)
