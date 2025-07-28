import importlib.metadata

extensions = [
    "autodocsumm",
    "sphinx.ext.autodoc",
    "sphinx.ext.autodoc.typehints",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx_issues",
    "sphinxext.opengraph",
]

primary_domain = "py"
default_role = "py:obj"

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

issues_github_path = "marshmallow-code/marshmallow"

source_suffix = ".rst"
master_doc = "index"

project = "marshmallow"
copyright = "Steven Loria and contributors"  # noqa: A001

version = release = importlib.metadata.version("marshmallow")

exclude_patterns = ["_build"]
# Ignore WARNING: more than one target found for cross-reference 'Schema': marshmallow.schema.Schema, marshmallow.Schema
suppress_warnings = ["ref.python"]

# THEME

html_theme = "furo"
html_theme_options = {
    "light_logo": "marshmallow-logo-with-title.png",
    "dark_logo": "marshmallow-logo-with-title-for-dark-theme.png",
    "source_repository": "https://github.com/marshmallow-code/marshmallow",
    "source_branch": "dev",
    "source_directory": "docs/",
    "sidebar_hide_name": True,
    "light_css_variables": {
        # Serif system font stack: https://systemfontstack.com/
        "font-stack": "Iowan Old Style, Apple Garamond, Baskerville, Times New Roman, Droid Serif, Times, Source Serif Pro, serif, Apple Color Emoji, Segoe UI Emoji, Segoe UI Symbol;",
    },
    "top_of_page_buttons": ["view", "edit"],
}
pygments_dark_style = "lightbulb"
html_favicon = "_static/favicon.ico"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_copy_source = False  # Don't copy source files to _build/sources
html_show_sourcelink = False  # Don't link to source files
ogp_image = "_static/marshmallow-logo-200.png"

# Strip the dollar prompt when copying code
# https://sphinx-copybutton.readthedocs.io/en/latest/use.html#strip-and-configure-input-prompts-for-code-cells
copybutton_prompt_text = "$ "

autodoc_default_options = {
    "exclude-members": "__new__",
    # Don't show signatures in the summary tables
    "autosummary-nosignatures": True,
    # Don't render summaries for classes within modules
    "autosummary-no-nesting": True,
}
# Only display type hints next to params but not within the signature
# to avoid the signature from getting too long
autodoc_typehints = "description"
