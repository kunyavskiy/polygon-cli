from prettytable import PrettyTable

from .common import *


def process_samples(contest_id, **session_options):
    contest = ProblemSession(config.polygon_url, None, **session_options)
    problems = contest.get_contest_problems(contest_id)
    print(problems)

    for problem_name in problems:
        contest.problem_id = problems[problem_name]
        tests = contest.send_api_request('problem.tests', {'testset': 'tests'})
        print(tests)
        for i in tests:
            if i["useInStatements"]:
                index = i["index"]
                contest.download_test(index, 'examples', problem_name + '%d.in', problem_name + '%d.out')
                if "inputForStatement" in i:
                    utils.safe_rewrite_file('examples/%s%d.in' % (problem_name, index), i["inputForStatement"])
                if "outputForStatement" in i:
                    utils.safe_rewrite_file('examples/%s%d.out' % (problem_name, index), i["outputForStatement"])



def add_parser(subparsers):
    parser_add = subparsers.add_parser(
        'samples',
        help="Download samples"
    )

    parser_add.add_argument('contest_id', help='Contest id to download')
    def read_options(options):
        if not load_session_with_options(options):
            fatal('No session known. Use relogin or init first.')
        process_samples(options.contest_id, **get_session_options(options))
        save_session()

    parser_add.set_defaults(func=read_options)
