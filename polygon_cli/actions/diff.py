from .common import *


def process_diff(filename):
    if not load_session() or global_vars.problem.sessionId is None:
        fatal('No session known. Use relogin or init first.')
    file = global_vars.problem.get_local_by_filename(filename)
    if file is None:
        fatal('File %s not found' % filename)
    polygon_files = global_vars.problem.get_all_files_list()
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
    parser_diff.add_argument('file', help='File to make diff')
    parser_diff.set_defaults(func=lambda options: process_diff(options.file))
