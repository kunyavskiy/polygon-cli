from .common import *
import os.path


def process_diff(options):
    input_files = list(map(os.path.abspath, options.file))

    if not load_session():
        fatal('No session known. Use init first.')

    polygon_files = global_vars.problem.get_all_files_list()
    for filename in input_files:
        file = global_vars.problem.get_local_by_filename(filename) or \
               global_vars.problem.get_local_by_path(filename)

        if file is None:
            fatal('File %s not found' % filename)

        polygon_file = None
        if file.polygon_filename:
            for p in polygon_files:
                if p.name == file.polygon_filename:
                    polygon_file = p
        if polygon_file is None:
            fatal('File %s not matched to any file in polygon')
        polygon_text = polygon_file.get_content()
        old_path = file.get_internal_path()
        utils.diff_file_with_content(old_path, file.get_path(), polygon_text)

    save_session()


def add_parser(subparsers):
    parser_diff = subparsers.add_parser(
            'diff',
            help="Prints diff of local and polygon version of file"
    )
    parser_diff.add_argument('file', nargs='+',
                             help='One or multiple files to make diff')
    parser_diff.set_defaults(func=process_diff)
