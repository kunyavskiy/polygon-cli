from .common import *


def process_update_info(options):
    if not load_session_with_options(options):
        fatal('No session known. Use relogin or init first.')
    global_vars.problem.update_info(inputfile=options.inputfile, outputfile=options.outputfile,
                                    memorylimit=options.memory_limit, timelimit=options.time_limit,
                                    interactive=options.interactive)


def add_parser(subparsers):
    parser = subparsers.add_parser(
            'update_info',
            help="Update TL, ML, input, output file names and/or problem interactiveness status information"
    )
    parser.add_argument("-m", "--ml", dest="memory_limit", type=int,
                        help="provide memory limit in MB as an integer between 4 and 1024 to change memory limit")
    parser.add_argument("-t", "--tl", dest="time_limit", type=int,
                        help="provide time limit in ms as an integer between 250 and 15000 to change time limit")
    parser.add_argument("-i", "--input", dest="inputfile",
                        help="provide input file name or 'stdin' for standard input to change input method")
    parser.add_argument("-o", "--output", dest="outputfile",
                        help="provide output file name or 'stdout' for standard output to change output method")
    parser.add_argument("-I", "--interactive", dest="interactive", choices=["true", "false"],
                        help="provide true/false to enable/disable problem interactiveness, respectively")
    parser.set_defaults(func=process_update_info)
