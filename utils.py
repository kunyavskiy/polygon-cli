#!/usr/bin/env python

import os
import shutil
from subprocess import Popen, PIPE

import config


def read_file(filename):
    f = open(filename, 'r')
    l = f.readlines()
    f.close()
    return l


def merge_files(old, our, theirs):
    p = Popen(config.get_merge_tool(old, our, theirs), stdout=PIPE, shell=True)
    diff3out, _ = p.communicate()
    if p.returncode == 1:
        print('Conflict in file %s' % our)
    elif p.returncode != 0:
        raise Exception("diff3 failed!")
    safe_rewrite_file_bin(our, diff3out)


def safe_rewrite_file(path, content):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    if os.path.exists(path):
        shutil.copy(path, path + ".$$$")
        open(path, 'w').write(content)
        os.remove(path + '.$$$')
    else:
        open(path, 'w').write(content)


def safe_rewrite_file_bin(path, content):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    if os.path.exists(path):
        shutil.copy(path, path + ".$$$")
        open(path, 'wb').write(content)
        os.remove(path + '.$$$')
    else:
        open(path, 'wb').write(content)


def safe_update_file(old_path, new_path, content):
    open(old_path + '.new', 'w').write(content)
    merge_files(old_path, new_path, old_path + '.new')
    shutil.move(old_path + '.new', old_path)


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
