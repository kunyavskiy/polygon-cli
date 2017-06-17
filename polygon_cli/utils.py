#!/usr/bin/env python

import os
import re
import shutil
import sys
from subprocess import Popen, PIPE
import subprocess

from . import config


def read_file(filename):
    f = open(filename, 'rb')
    l = f.readlines()
    f.close()
    return l


def diff_files(old, our, theirs):
    subprocess.run(config.get_diff_tool(old, our, theirs),
                   stdout=sys.stdout,
                   shell=True)


def safe_rewrite_file(path, content, openmode='wb'):
    dir_name = os.path.dirname(path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)
    if openmode.endswith('b'):
        content = convert_to_bytes(content)
    if os.path.exists(path):
        shutil.copy(path, path + ".$$$")
        open(path, openmode).write(content)
        os.remove(path + '.$$$')
    else:
        open(path, openmode).write(content)


def merge_files(old, our, theirs):
    if open(old, 'rb').read().splitlines() == open(theirs, 'rb').read().splitlines():
        return 'Not changed'
    p = Popen(config.get_merge_tool(old, our, theirs), stdout=PIPE, shell=True)
    diff3out, _ = p.communicate()
    return_value = 'Merged'
    if p.returncode == 1:
        print('Conflict in file %s' % our)
        return_value = 'Conflict'
    elif p.returncode != 0:
        raise Exception("diff3 failed!")
    if return_value != 'Conflict':
        safe_rewrite_file(our, diff3out, 'wb')
    else:
        safe_rewrite_file(our + '.diff', diff3out, 'wb')
        shutil.copy(theirs, our + '.new')
    return return_value


def safe_update_file(old_path, new_path, content):
    open(old_path + '.new', 'wb').write(content)
    return_value = merge_files(old_path, new_path, old_path + '.new')
    shutil.move(old_path + '.new', old_path)
    return return_value


def diff_file_with_content(old_path, new_path, content):
    open(old_path + '.new', 'wb').write(content)
    diff_files(old_path, new_path, old_path + '.new')


def prepare_url_print(url):
    splited = url.split("?")
    if len(splited) != 2:
        return url
    args = splited[1].split('&')
    args = filter(lambda x: not (x.startswith('ccid=') or x.startswith('session=')), args)
    argsstr = '&'.join(args)
    if argsstr:
        argsstr = '?' + argsstr
    return splited[0] + argsstr


def get_local_solutions():
    return os.listdir(config.solutions_path)


def need_update_groups(content):
    match = re.search(rb"<#-- *group *(\d*) *-->", content)
    return match is not None


def parse_script_groups(content, hand_tests):
    groups = {"0": []}
    cur_group = "0"
    test_id = 0
    any = False
    for i in filter(lambda x: x.strip(), content.splitlines()):
        match = re.search(rb"<#-- *group *(\d*) *-->", i)
        if not match:
            t = i.split(b'>')[-1].strip()
            if t == b'$':
                test_id += 1
                while test_id in hand_tests:
                    test_id += 1
            else:
                test_id = int(t)
                assert test_id not in hand_tests
            groups[cur_group].append(test_id)
            continue
        cur_group = match.groups(0)[0].decode("ascii")
        groups[cur_group] = []
        any = True
    if not any:
        return None
    return groups


def convert_to_bytes(x):
    if isinstance(x, bytes):
        return x
    return bytes(str(x), 'utf8')


def convert_newlines(x):
    in_bytes = False
    if isinstance(x, bytes):
        x = str(x, 'utf8')
        in_bytes = True
    x = x.replace('\r\n', os.linesep)
    if in_bytes:
        return bytes(x, 'utf8')
    return x


def get_api_file_type(type):
    if type == 'source' or type == 'resource':
        return type
    if type == 'attachment':
        return 'aux'
    return None
