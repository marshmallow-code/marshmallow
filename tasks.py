# -*- coding: utf-8 -*-
import os
import sys
import webbrowser

from invoke import task

docs_dir = 'docs'
build_dir = os.path.join(docs_dir, '_build')

@task
def test(ctx, watch=False, last_failing=False):
    """Run the tests.

    Note: --watch requires pytest-xdist to be installed.
    """
    import pytest
    syntax(ctx)
    args = []
    if watch:
        args.append('-f')
    if last_failing:
        args.append('--lf')
    if int(sys.version_info[0]) < 3:
        args.append('--ignore={0}'.format(os.path.join('tests', 'test_py3')))
    retcode = pytest.main(args)
    benchmark(ctx)
    sys.exit(retcode)

@task
def syntax(ctx):
    """Run flake8 on codebase."""
    ctx.run('pre-commit run --all-files', echo=True)

@task
def benchmark(ctx):
    """Run fast benchmark on codebase."""
    # Explicitly shell out to get more consistent results by creating a new process
    # every time, for example running out of process ensures a pristine class_registry.
    ctx.run('python performance/benchmark.py --iterations=100 --repeat=3', echo=True)

@task
def clean(ctx):
    ctx.run('rm -rf build')
    ctx.run('rm -rf dist')
    ctx.run('rm -rf marshmallow.egg-info')
    clean_docs(ctx)
    print('Cleaned up.')

@task
def clean_docs(ctx):
    ctx.run('rm -rf %s' % build_dir)

@task
def browse_docs(ctx):
    path = os.path.join(build_dir, 'index.html')
    webbrowser.open_new_tab(path)

def build_docs(ctx, browse):
    ctx.run('sphinx-build %s %s' % (docs_dir, build_dir), echo=True)
    if browse:
        browse_docs(ctx)

@task
def docs(ctx, clean=False, browse=False, watch=False):
    """Build the docs."""
    if clean:
        clean_docs(ctx)
    if watch:
        watch_docs(ctx, browse=browse)
    else:
        build_docs(ctx, browse=browse)

@task
def watch_docs(ctx, browse=False):
    """Run build the docs when a file changes."""
    try:
        import sphinx_autobuild  # noqa
    except ImportError:
        print('ERROR: watch task requires the sphinx_autobuild package.')
        print('Install it with:')
        print('    pip install sphinx-autobuild')
        sys.exit(1)
    ctx.run(
        'sphinx-autobuild {0} {1} {2} -z marshmallow'.format(
            '--open-browser' if browse else '', docs_dir, build_dir,
        ), echo=True, pty=True,
    )

@task
def readme(ctx, browse=False):
    ctx.run('rst2html.py README.rst > README.html')
    if browse:
        webbrowser.open_new_tab('README.html')
