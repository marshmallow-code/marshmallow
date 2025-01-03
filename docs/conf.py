import importlib.metadata

import alabaster

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "alabaster",
    "sphinx_issues",
    "autodocsumm",
]

primary_domain = "py"
default_role = "py:obj"

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

issues_github_path = "marshmallow-code/marshmallow"

templates_path = ["_templates"]

source_suffix = ".rst"
master_doc = "index"

project = "marshmallow"
copyright = '<a href="https://stevenloria.com">Steven Loria</a> and contributors'

version = release = importlib.metadata.version("marshmallow")

exclude_patterns = ["_build"]

# THEME

html_theme_path = [alabaster.get_path()]
html_theme = "alabaster"
html_static_path = ["_static"]
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
        "marshmallow @ PyPI": "https://pypi.org/project/marshmallow/",
        "marshmallow @ GitHub": "https://github.com/marshmallow-code/marshmallow",
        "Issue Tracker": "https://github.com/marshmallow-code/marshmallow/issues",
        "Ecosystem": "https://github.com/marshmallow-code/marshmallow/wiki/Ecosystem",
    },
}

html_sidebars = {
    "index": ["about.html", "searchbox.html", "donate.html", "useful-links.html"],
    "**": [
        "about.html",
        "searchbox.html",
        "donate.html",
        "useful-links.html",
        "localtoc.html",
        "relations.html",
    ],
}
