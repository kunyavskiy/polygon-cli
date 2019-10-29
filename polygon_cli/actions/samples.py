from prettytable import PrettyTable

from .common import *


def process_samples(contest_id, pin, **session_options):
    contest = ProblemSession(config.polygon_url, None, pin, **session_options)
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
                    utils.safe_rewrite_file('examples/%s%d.in' % (problem_name, index), i["inputForStatement"])
                if "outputForStatement" in i:
                    utils.safe_rewrite_file('examples/%s%d.out' % (problem_name, index), i["outputForStatement"])



def add_parser(subparsers):
    parser_samples = subparsers.add_parser(
        'samples',
        help="Download samples"
    )

    parser_samples.add_argument('contest_id', help='Contest id to download')
    parser_samples.add_argument('--pin', dest='pin', default=None, help='Pin code for contest')
    def read_options(options):
        process_samples(options.contest_id, options.pin, **get_session_options(options))

    parser_samples.set_defaults(func=read_options)
