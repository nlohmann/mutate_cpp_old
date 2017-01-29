# coding=utf-8
"""mutation++ operator mutation generator

Usage:
  create_mutations_equal.py <filename> [options]

Options:
  -h --help            Show this screen.
  --directory=<dir>    Patch directory [default: patches].
  --first_line=<line>  First line to consider [default: 0].
  --last_line=<line>   Last line to consider [default: -1].
"""

import progressbar
import os
from mutate.utils import create_patch
from docopt import docopt


def create_mutations_equal(source_filename, patch_directory, first_line, last_line):
    # read source file
    source_lines = [x.rstrip() for x in open(source_filename)]

    if last_line == -1:
        last_line = len(source_lines)

    print "read source file '{source_filename}'".format(source_filename=source_filename)

    files_written = 0
    in_comment = False

    bar = progressbar.ProgressBar()
    for line_number in bar(range(len(source_lines))):
        if line_number < first_line or line_number > last_line:
            continue

        line_orig = source_lines[line_number]
        line = line_orig.strip()

        # skip line comments and preprocessor directives
        if line.startswith('//') or line.startswith('#'):
            continue

        # skip empty lines or "bracket onlys"
        if line in ['', '{', '}', '};', '});', ')']:
            continue

        # recognize the beginning of a line comment
        if line.startswith('/*'):
            in_comment = True
            continue

        # recognize the end of a line comment
        if line.endswith('*/'):
            in_comment = False
            continue

        # write mutation
        if not in_comment:
            if '==' in line:
                patch_filename = '{patch_directory}/{original_source}_equal_{patch:05d}.patch'.format(
                    patch_directory=patch_directory, original_source=os.path.basename(source_filename), patch=line_number + 1
                )
                create_patch(patch_filename, source_filename, source_lines, line_number, line_orig.replace('==', '!='))

                files_written += 1

    print "wrote {filecount} mutations patches to folder '{patch_directory}'".format(filecount=files_written,
                                                                                     patch_directory=patch_directory)


if __name__ == '__main__':
    arguments = docopt(__doc__)

    filename = arguments['<filename>']
    directory = arguments['--directory']
    first_line = int(arguments['--first_line'])
    last_line = int(arguments['--last_line'])

    # create directories if necessary
    if not os.path.exists(directory):
        os.makedirs(directory)

    create_mutations_equal(filename, directory, first_line, last_line)
