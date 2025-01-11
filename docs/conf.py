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

templates_path = ["_templates"]

source_suffix = ".rst"
master_doc = "index"

project = "marshmallow"
copyright = "Steven Loria and contributors"

version = release = importlib.metadata.version("marshmallow")

exclude_patterns = ["_build"]
# Ignore WARNING: more than one target found for cross-reference 'Schema': marshmallow.schema.Schema, marshmallow.Schema
suppress_warnings = ["ref.python"]

# THEME

html_theme = "furo"
html_theme_options = {
    "light_logo": "marshmallow-logo-with-title.png",
    "dark_logo": "marshmallow-logo-with-title-for-dark-theme.png",
    "sidebar_hide_name": True,
    "light_css_variables": {
        # Serif system font stack: https://systemfontstack.com/
        "font-stack": "Iowan Old Style, Apple Garamond, Baskerville, Times New Roman, Droid Serif, Times, Source Serif Pro, serif, Apple Color Emoji, Segoe UI Emoji, Segoe UI Symbol;",
    },
    "top_of_page_buttons": ["view"],
}
html_favicon = "_static/favicon.ico"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_show_sourcelink = False
ogp_image = "_static/marshmallow-logo-200.png"

# Strip the dollar prompt when copying code
# https://sphinx-copybutton.readthedocs.io/en/latest/use.html#strip-and-configure-input-prompts-for-code-cells
copybutton_prompt_text = "$ "

autodoc_typehints = "both"
