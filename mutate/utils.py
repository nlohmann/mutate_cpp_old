# coding=utf-8
import os
import datetime
import subprocess32
import shlex
import ConfigParser
import json


FNULL = open(os.devnull, 'w')


def create_patch(patch_filename, source_filename, source_lines, line_number, line_content):
    original_file_date = os.path.getmtime(source_filename)

    outfile = open(patch_filename, 'w')

    context_before = source_lines[line_number - 3:line_number]
    context_after = source_lines[line_number + 1:line_number + 4]

    outfile.write('--- {filename} {date}\n'.format(filename=source_filename,
                                                   date=datetime.datetime.fromtimestamp(original_file_date).strftime(
                                                       '%Y-%m-%d %H:%M:%S.%f')))
    outfile.write('+++ {filename} {date}\n'.format(filename=source_filename, date=datetime.datetime.now()))
    outfile.write('@@ -{lineno},{context_length} +{lineno},{context_length_shortened} @@\n'.format(
        lineno=line_number - len(context_before) + 1,
        context_length=len(context_before) + len(context_after) + 1,
        context_length_shortened=len(context_before) + len(context_after) + (1 if line_content else 0)
    ))

    outfile.writelines([' ' + x + '\n' for x in context_before])

    outfile.write('-' + source_lines[line_number] + '\n')
    if line_content is not None:
        outfile.write('+' + line_content + '\n')

    outfile.writelines([' ' + x + '\n' for x in context_after])


def execute_command(command, timeout=None, cwd=None, stdin=None):
    res = subprocess32.check_output(shlex.split(command), cwd=cwd, stdin=stdin, stderr=FNULL, timeout=timeout)
    return res


def config_to_dict(config_file):
    config = ConfigParser.ConfigParser()
    config.read(config_file)

    result = dict()
    for s in config.sections():
        result[s] = dict()
        for o in config.options(s):
            try:
                result[s][o] = json.loads(config.get(s, o))
            except ValueError:
                result[s][o] = config.get(s, o)

    return result
