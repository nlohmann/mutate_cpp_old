# coding=utf-8
"""mutation++ syntax checker

Usage:
  mutation_syntax.py [options]

Options:
  -h --help          Show this screen.
  --directory=<dir>  Patch directory [default: patches].
"""

from mutate.utils import execute_command
import progressbar
import glob
import subprocess32
import os
import time
import multiprocessing
from multiprocessing.dummy import Pool
from docopt import docopt


check_syntax_command = '/Users/niels/Documents/projects/clang/bin/clang-check {filename} -- -std=c++11'
patch_command = 'patch -p0 -i{patch_input} --output={patch_output}'


def test_syntax(patch):
    # apply patch
    patch_output = patch + '.cpp'
    execute_command(patch_command.format(patch_input=patch, patch_output=patch_output))

    # syntax check
    try:
        execute_command(check_syntax_command.format(filename=os.path.abspath(patch_output)))
        result = True
    except subprocess32.CalledProcessError:
        result = False

    if not result:
        # remove failed patch
        os.remove(patch)

    # delete patched file
    os.remove(patch_output)

    return result


def syntax_check(patch_list):
    # the syntax check results for the patches
    result = []

    # create thread pool
    pool = Pool(processes=multiprocessing.cpu_count())

    # schedule all syntax checks
    for patch in patch_list:
        pool.apply_async(test_syntax, (patch,), callback=result.append)
    pool.close()

    # wait until all patches have been checked
    bar = progressbar.ProgressBar(max_value=len(patch_list))
    while True:
        bar.update(len(result))

        if len(result) == len(patch_list):
            break

        time.sleep(0.1)

    pool.join()
    return result


if __name__ == '__main__':
    arguments = docopt(__doc__)

    patches = glob.glob('{outdir}/*.patch'.format(outdir=arguments['--directory']))#
    res = syntax_check(patches)

    ok, nok = len([x for x in res if x]), len([x for x in res if not x])
    print 'checked %d patches: %d passed / %d failed' % (len(patches), ok, nok)
