# coding=utf-8
"""mutation++ test executor

Usage:
  mutation_test.py <config_file> [options]

Options:
  -h --help               Show this screen.
"""

import progressbar
import glob
import subprocess32
import os
import time
import shutil
from docopt import docopt
from mutate.utils import execute_command, config_to_dict
from termcolor import cprint


def calculate_reference_runtime(clean_command, build_command, test_command, quicktest_command, workdir):
    print 'creating baseline for tests...'

    if clean_command:
        print 'cleaning...'
        execute_command(clean_command, cwd=workdir)

    print 'building...'
    execute_command(build_command, cwd=workdir)

    start = time.time()
    if quicktest_command:
        print 'measuring quick testing...'
        execute_command(quicktest_command, cwd=workdir)
    end = time.time()

    test_duration = end - start
    print '--> quick testing takes %.2f seconds' % test_duration

    start = time.time()
    print 'measuring testing...'
    execute_command(test_command, cwd=workdir)
    end = time.time()

    test_duration2 = end - start
    print '--> testing takes %.2f seconds' % test_duration2

    return test_duration, test_duration2


def run_tests(options):
    mutations_dir = options['directories'].get('mutations_dir')
    survived_mutations_dir = options['directories'].get('survived_mutations_dir')
    workdir = options['directories'].get('workdir')

    clean_command = options['commands'].get('clean_command')
    build_command = options['commands'].get('build_command')
    quicktest_command = options['commands'].get('quicktest_command')
    test_command = options['commands'].get('test_command')

    timeout_multiplicator = options['parameters']['timeout_multiplicator']

    reference_runtime, reference_runtime2 = calculate_reference_runtime(clean_command, build_command, test_command, quicktest_command, workdir)

    statistics = {
        'total': 0,
        'compilation_failure': 0,
        'test_failure': 0,
        'test_timeout': 0,
        'survived': 0
    }

    #bar = progressbar.ProgressBar(redirect_stdout=True)
    for mutant in glob.glob('{outdir}/*.patch'.format(outdir=mutations_dir)):
        statistics['total'] += 1

        print 78 * '-'
        print 'processing %s...' % mutant

        if clean_command:
            print 'cleaning...'
            execute_command(clean_command, cwd=workdir)

        execute_command('patch -p1', stdin=open(mutant), cwd='/')

        mutant_alive = True
        while True:
            try:
                print 'building...'
                execute_command(build_command, cwd=workdir)
            except subprocess32.CalledProcessError:
                statistics['compilation_failure'] += 1
                mutant_alive = False
                break

            try:
                if quicktest_command:
                    print 'quick testing...'
                    execute_command(quicktest_command, timeout=reference_runtime * timeout_multiplicator, cwd=workdir)
                print 'testing...'
                execute_command(test_command, timeout=reference_runtime2 * timeout_multiplicator, cwd=workdir)
            except subprocess32.CalledProcessError:
                statistics['test_failure'] += 1
                mutant_alive = False
                break
            except subprocess32.TimeoutExpired:
                statistics['test_timeout'] += 1
                mutant_alive = False
                break

            break

        # reverting patch
        execute_command('patch -R -p1', stdin=open(mutant), cwd='/')

        if mutant_alive:
            statistics['survived'] += 1
            cprint('--> %s survived!' % mutant, 'red')
            if survived_mutations_dir:
                shutil.move(mutant, survived_mutations_dir)
        else:
            cprint('--> %s killed' % mutant, 'green')
            os.remove(mutant)


if __name__ == '__main__':
    # read command line arguments
    arguments = docopt(__doc__)

    # read config file
    options = config_to_dict(arguments['<config_file>'])
    print 'read config file %s' % arguments['<config_file>']

    run_tests(options)
