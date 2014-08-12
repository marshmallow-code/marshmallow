# -*- coding: utf-8 -*-
import os
import sys
from invoke import task, run

docs_dir = 'docs'
build_dir = os.path.join(docs_dir, '_build')

@task
def test():
    """Run the tests."""
    run('python setup.py test', pty=True)

@task
def watch():
    """Run tests when a file changes."""
    run('py.test -f tests/', pty=True)

@task
def clean():
    run("rm -rf build")
    run("rm -rf dist")
    run("rm -rf marshmallow.egg-info")
    clean_docs()
    print("Cleaned up.")

@task
def clean_docs():
    run("rm -rf %s" % build_dir)

@task
def browse_docs():
    platform = str(sys.platform).lower()
    command = {
        'darwin': 'open ',
        'linux': 'idle ',
        'win32': '',
    }
    cmd = command.get(platform)
    if cmd:
        run("{0}{1}".format(cmd, os.path.join(build_dir, 'index.html')))
    else:
        print('Unsure how to open the built file on this operating system.')
        sys.exit(1)

@task
def docs(clean=False, browse=False):
    """Build the docs."""
    if clean:
        clean_docs()
    run("sphinx-build %s %s" % (docs_dir, build_dir), pty=True)
    if browse:
        browse_docs()

@task
def watch_docs():
    try:
        import sphinx_autobuild  # noqa
    except ImportError:
        print('ERROR: watch task requires the sphinx_autobuild package.')
        print('Install it with:')
        print('    pip install sphinx-autobuild')
        sys.exit(1)
    run('sphinx-autobuild {} {}'.format(docs_dir, build_dir), pty=True)

@task
def readme(browse=False):
    run("rst2html.py README.rst > README.html", pty=True)
    if browse:
        run("open README.html")

@task
def publish(test=False):
    """Publish to the cheeseshop."""
    try:
        __import__('wheel')
    except ImportError:
        print("wheel required. Run `pip install wheel`.")
        sys.exit(1)
    if test:
        run('python setup.py register -r test sdist bdist_wheel upload -r test')
    else:
        run("python setup.py register sdist bdist_wheel upload")
