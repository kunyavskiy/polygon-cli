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
    safe_rewrite_file(our, diff3out, 'wb')


def safe_rewrite_file(path, content, openmode='w'):
    dir_name = os.path.dirname(path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)
    if os.path.exists(path):
        shutil.copy(path, path + ".$$$")
        open(path, openmode).write(content)
        os.remove(path + '.$$$')
    else:
        open(path, openmode).write(content)


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
