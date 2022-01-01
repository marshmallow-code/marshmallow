import sys
import os
import time
import datetime as dt

import alabaster

sys.path.insert(0, os.path.abspath(os.path.join("..", "src")))
import marshmallow  # noqa: E402

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "alabaster",
    "sphinx_issues",
    "versionwarning.extension",
    "autodocsumm",
]

primary_domain = "py"
default_role = "py:obj"

intersphinx_mapping = {"python": ("https://python.readthedocs.io/en/latest/", None)}

issues_github_path = "marshmallow-code/marshmallow"

templates_path = ["_templates"]

# Use SOURCE_DATE_EPOCH for reproducible build output https://reproducible-builds.org/docs/source-date-epoch/
build_date = dt.datetime.utcfromtimestamp(
    int(os.environ.get("SOURCE_DATE_EPOCH", time.time()))
)

source_suffix = ".rst"
master_doc = "index"

project = "marshmallow"
copyright = (
    ' {:%Y} <a href="https://stevenloria.com">Steven Loria</a> and contributors'.format(
        build_date
    )
)

version = release = marshmallow.__version__

exclude_patterns = ["_build"]

# THEME

html_theme_path = [alabaster.get_path()]
html_theme = "alabaster"
html_static_path = ["_static"]
html_css_files = ["css/versionwarning.css"]
templates_path = ["_templates"]
html_show_sourcelink = False

html_theme_options = {
    "logo": "marshmallow-logo.png",
    "description": "Object serialization and deserialization, lightweight and fluffy.",
    "description_font_style": "italic",
    "github_user": "marshmallow-code",
    "github_repo": "marshmallow",
    "github_banner": True,
    "github_type": "star",
    "opencollective": "marshmallow",
    "tidelift_url": (
        "https://tidelift.com/subscription/pkg/pypi-marshmallow"
        "?utm_source=marshmallow&utm_medium=referral&utm_campaign=docs"
    ),
    "code_font_size": "0.8em",
    "warn_bg": "#FFC",
    "warn_border": "#EEE",
    # Used to populate the useful-links.html template
    "extra_nav_links": {
        "marshmallow @ PyPI": "https://pypi.python.org/pypi/marshmallow",
        "marshmallow @ GitHub": "https://github.com/marshmallow-code/marshmallow",
        "Issue Tracker": "https://github.com/marshmallow-code/marshmallow/issues",
        "Ecosystem": "https://github.com/marshmallow-code/marshmallow/wiki/Ecosystem",
    },
}

html_sidebars = {
    "index": ["about.html", "donate.html", "useful-links.html", "searchbox.html"],
    "**": [
        "about.html",
        "donate.html",
        "useful-links.html",
        "localtoc.html",
        "relations.html",
        "searchbox.html",
    ],
}

# sphinx-version-warning config
versionwarning_messages = {
    "latest": (
        "This document is for the development version. "
        'For the stable version documentation, see <a href="/en/stable/">here</a>.'
    ),
    "2.x-line": (
        "marshmallow 2 is no longer supported as of 2020-08-18. "
        '<a href="https://marshmallow.readthedocs.io/en/latest/upgrading.html#upgrading-to-3-0">'
        "Update your code to use marshmallow 3</a>."
    ),
}
# Show warning at top of page
versionwarning_body_selector = "div.document"
versionwarning_banner_title = ""
# For debugging locally
# versionwarning_project_version = "latest"
