# How to contribute to _Eqasim_

Welcome, and thank you for considering contributing to _Eqasim_ !

This document aims to help _Eqasim_ users sharing improvements and new features to the project. 
_Eqasim_ is highly supported by a community of researchers and developers, so contributions are an important part of its lifecycle.

Every contribution is welcome. If you don't know if your feature is relevant or already implemented, 
you can use the [issue tracker](https://github.com/eqasim-org/ile-de-france/issues/new) to ask the project maintainers. 

The following sections take a closer look on how to make your contributions available to all, and how to format them. 
However, if you're not comfortable with our development tools, please reach out to us, we will figure out a way together.

## Making a Pull request

The most common way to contribute to an open-source project is to make a Pull request (PR),
so the project maintainers can review your code and discuss changes if needed.

The following section explains how to make changes in _Eqasim_ and create a PR to merge them into the main repository. 
It requires having [Git](https://git-scm.com/) installed and being able to perform some actions
like cloning a repository, creating a branch and doing a commit, using command lines in a terminal.

If you need any help in this process, please reach out to the code maintainers.

### Fork the _Eqasim_ repository

First, go to the [_Eqasim_ repository homepage](https://github.com/eqasim-org/ile-de-france) and [fork it](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo)
by clicking the `Fork` button. This will create a copy of the repository on your GitHub account.

### Clone your fork

In order to make changes to the codebase, you have to [clone your new repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)
into your local machine. Click the `Code` button on the main page and copy the one of the addresses of the repository,
then use it with the `git clone` command line:

```bash
git clone https://github.com/<YourUserName>/<projectname>
```

This will create a new folder with the repository contents.

### Create a branch

In the root folder of your local repository, [create a new branch](https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging)
using the following command line:

```bash
git checkout -b my-branch-name
```

### Commit changes into the code

You can now implement changes into the main codebase of _Eqasim_. Once you are done, 
[commit your changes](https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository). 
This command line will commit all modified files:

```bash
git commit -a -m "<my commit message>"
```

### Push your changes

Now that your local branch contains your changes, you can ["push" it online](https://git-scm.com/book/en/v2/Git-Basics-Working-with-Remotes), into the GitHub repository
you created by forking _Eqasim_. In order to do so, execute this command line:

```bash
git push origin <my-branch-name>
```

### Pull request creation

Finally, go to your GitHub repository homepage in order to [create your Pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request). 
You should be able to click a green `Compare and pull request` button.
Alternatively, click the `Pull requests` tab and the `New pull request` button.

On top of the page, selectors allow you to choose what is merged into what.

- On the left side, make sure that the `base repository` is set to `eqasim-org/ile-de-france` and `base` is set to `develop`.
On the 
- On the right side, `head repository` should be your repository name, and `compare` should be set to your branch name

Click `Create pull request`, give it a title and a description to explain your changes, and you're done !

#### Pull request title

The PR title should comply with [Conventional commits](https://www.conventionalcommits.org/en/v1.0.0/).
This ensures that once the PR contents are squashed and merged in the `develop` branch,
its history is readable and can be used for things like generating the [Changelog](CHANGELOG.md).

**Commits of the branch don't have to be conventional commits !**

When a PR is created, a GitHub action checks that the title is compliant, so don't worry too much about it.

#### Automatic testing

Tests are automatically run upon PR creation and when changes are made to the incoming branch.
This ensures that your changes don't break _Eqasim_ and that they can be safely merged.

## Development environment and guidelines

This section is intended for people with some experience in Python development and GitHub.
Is it mainly a cheatsheet for maintainers to remember how the various tools used by _Eqasim_ work. 

If these guidelines are too complicated and prevent your contribution to _Eqasim_,
you can post a message along with your PR to ask the maintainers to
help you with your contribution !

### Versioning and releases

#### Release Please

_Eqasim_ uses [Release Please](https://github.com/googleapis/release-please) to manage versions and releases.

> Release Please automates CHANGELOG generation, the creation of GitHub releases, and version bumps

**Release Please will create and update a release PR** (named `chore(develop): release <new-version-number>`) when the `develop` branch receives pushes.

This requires commits **on the `develop` branch** to follow the Conventional commits convention (see #pull-request-title).

#### Version number

The new version number is defined according to the [SemVer](https://semver.org/) convention, based on the commits since the last release:
    
- A `fix` commit will increase the PATCH number (0.0.Z)
- Any `feat` commit will instead increase the MINOR number (0.Y.0)
- Any breaking commit (`!` marker) will instead increase the MAJOR number (X.0.0)

#### Release action

**When we are ready to release, simply merge the release PR.** 
Release Please will then do the following:

- Merge the changes contained in the release PR into the `develop` branch, creating a commit with the same name as the branch. These changes include:
  - Updating the version number in all relevant places of the code
  - Update the Changelog based on the contents of the commits added since the last release
- Create a git tag on this commit with the new version number
- Create a new release
- This will also trigger the publication of a new version of the documentation


### Sphinx documentation

_Eqasim_ uses [Sphinx](https://www.sphinx-doc.org/en/master/index.html) to generate a documentation website.
The documentation pages and generation scripts are located in the `docs/` folder.

#### Hosting

The documentation is hosted by [Readthedocs](https://docs.readthedocs.com/platform/stable/index.html) which automatically
builds a new instance when the `develop` branch is pushed and when a new git tag is created.

#### How to generate the Sphinx documentation locally

First, install the documentation libraries
listed in `docs/doc_requirements.txt`. Using pip, for instance:

```bash
pip install -r docs/doc_requirements.txt
```

Then, build the HTML documentation from the `docs/` folder:

```bash
# in the docs/ folder
make html
```

Finally, open the pages HTML generated in `docs/_build/html/` (homepage is `index.html`). For instance:

```bash
firefox docs/_build/html/index.html
```

##### Reactivity

The build is not reactive, you have to call `make html` again after making a modification. You can look at [sphinx-autobuild](https://www.sphinx-doc.org/en/master/usage/quickstart.html#running-the-build) if it bothers you.

##### Force build on all files

If you see a part of the page not updating correctly (like the main sections on the left), you can delete the `_build` folder to force re-rendering all pages, or use the `-a` and `-E` options:

```bash
make html -a -E
```

#### How to write documentation pages

Sphinx creates pages from documentation files, and allows introducing layouts, links, and all sort of widgets in the rendered pages.

##### File format

Pages can be written in **either** _[reStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)_
**or** _[Markdown](https://www.markdownguide.org/)_ thanks to the [MyST](https://myst-parser.readthedocs.io/en/latest/intro.html) parser extension that allows using Markdown pages.

When looking at what is possible to do with Sphinx, refer to the Sphinx/reStructuredText official documentation, then see if you can make it work with MyST. 
Otherwise, write it in reStructuredText.

##### Indicating subpages

In Sphinx, we can specify which pages consist of subpages of the current page using the _toctree_ directive.
This will result in links to the subpages being added to the left navigation drawer.

This will also add a bullet point list to the page with links to each subpage.
If you want to ignore this list generation, add the `:hidden:` option.

Example with the `toctree` directive of the `population_summary.md` page (_Markdown_ format):

```text
    ```{toctree}
    
    population_data.md
    population_execution.md
    population_analysis.md
    ```
```

and the equivalent in _reStructuredText_:

```text
.. toctree::
   :hidden:

   my_documentation_file
```
