import re
from setuptools import setup, find_packages

EXTRAS_REQUIRE = {
    "tests": ["pytest", "pytz", "simplejson"],
    "lint": [
        "mypy==0.940",
        "flake8==4.0.1",
        "flake8-bugbear==22.1.11",
        "pre-commit~=2.4",
    ],
    "docs": [
        "sphinx==4.4.0",
        "sphinx-issues==3.0.1",
        "alabaster==0.7.12",
        "sphinx-version-warning==1.1.2",
        "autodocsumm==0.2.7",
    ],
}
EXTRAS_REQUIRE["dev"] = EXTRAS_REQUIRE["tests"] + EXTRAS_REQUIRE["lint"] + ["tox"]


def find_version(fname):
    """Attempts to find the version number in the file names fname.
    Raises RuntimeError if not found.
    """
    version = ""
    with open(fname) as fp:
        reg = re.compile(r'__version__ = [\'"]([^\'"]*)[\'"]')
        for line in fp:
            m = reg.match(line)
            if m:
                version = m.group(1)
                break
    if not version:
        raise RuntimeError("Cannot find version information")
    return version


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content


setup(
    name="marshmallow",
    version=find_version("src/marshmallow/__init__.py"),
    description=(
        "A lightweight library for converting complex "
        "datatypes to and from native Python datatypes."
    ),
    long_description=read("README.rst"),
    author="Steven Loria",
    author_email="sloria1@gmail.com",
    url="https://github.com/marshmallow-code/marshmallow",
    packages=find_packages("src", exclude=("test*", "examples")),
    package_dir={"": "src"},
    package_data={"marshmallow": ["py.typed"]},
    include_package_data=True,
    install_requires=["packaging"],
    extras_require=EXTRAS_REQUIRE,
    license="MIT",
    zip_safe=False,
    keywords=[
        "serialization",
        "rest",
        "json",
        "api",
        "marshal",
        "marshalling",
        "deserialization",
        "validation",
        "schema",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    test_suite="tests",
    project_urls={
        "Changelog": "https://marshmallow.readthedocs.io/en/latest/changelog.html",
        "Issues": "https://github.com/marshmallow-code/marshmallow/issues",
        "Funding": "https://opencollective.com/marshmallow",
        "Tidelift": "https://tidelift.com/subscription/pkg/pypi-marshmallow?utm_source=pypi-marshmallow&utm_medium=pypi",  # noqa
    },
)
