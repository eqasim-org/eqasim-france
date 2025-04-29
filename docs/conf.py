# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Eqasim'
copyright = '2024, Eqasim contributors'
author = 'Eqasim contributors'

# fetch version from version file
with open("../version.txt", "r") as f:
    release = version = f.readline()

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['myst_parser', 'sphinx_copybutton']

myst_enable_extensions = [
    "attrs_inline",
    "colon_fence",
    "html_admonition"
]

source_suffix = ['.rst', '.md']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The master toctree document.
master_doc = "contents"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_title = "Eqasim"
html_short_title = "Eqasim documentation"

html_baseurl = "https://eqasim.readthedocs.io/stable/"
# html_theme_options = {
#     "collapse_navigation": True,
#     "navigation_depth": 2,
#     "icon_links": [
#         {"name": "Home Page", "url": html_baseurl, "icon": "fas fa-home"},
#         {
#             "name": "GitHub",
#             "url": "https://github.com/eqasim-org/ile-de-france",
#             "icon": "fab fa-github-square",
#         },
#     ],
#     "navbar_end": ["theme-switcher", "navbar-icon-links"],
#     "secondary_sidebar_items": ["page-toc", "edit-this-page"],
#     "header_links_before_dropdown": 7,
# }

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

html_show_sourcelink = False
