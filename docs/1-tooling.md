# Tooling

outline: Three main tools `uv`, linting using `ruff` and `pre-commit`

This page will explain what each of them are and their relationship, and how/why they are useful tools for research and make life easier when developing. Other than `uv` the others are about safe guards and spotting mistakes early so you don't need to wait how ever long it takes to run your code to spot a mistake.


## Python Environment Management

[`uv`](https://docs.astral.sh/uv/) is a Python package manager similar to `pip` and [`conda`](https://www.anaconda.com/docs/main). One of the key advantages of `uv` over `conda` is its significantly faster performance. Moreover, `uv` can install and manage the python version so you won't need to install python on your own.

In addition to this, there another two features which makes `uv` a great tool. Firstly, is that it integrates with the `pyproject.toml` file. Secondly, that it has a universal lockfile (`uv.lock`).

### What is the `pyproject.toml` file? And how does it integrate with `uv`

!!! quote "What is the pyproject.toml file?"
    [`pyproject.toml`](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) is a configuration file used by packaging tools, as well as other tools such as linters, type checkers, etc.

A common misconception about the `pyproject.toml` file is that it is not useful unless you're planning to distribute your code by packaging, i.e. bundling it up the code so that others can easily install and use it through [`PyPI` (the python package index)](https://www.software.ac.uk/news/introducing-2026-fellowship-cohort-insights-and-celebrations).
Instead, it is a general-purpose configuration file for Python projects which can be used beyond packaging for specifying settings for tools or dependencies.

The `pyproject.toml` file can also be used to configure specify the entry point to your python project. For example, this project is a command line tool for users to run the game of life. Once the project is installed into the virtual environment (see [getting started for details](index.md#getting-started)), the tool can be run in the terminal, e.g. `game-of-life --help`.
This is possible by through the [`[project.scripts]`](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#creating-executable-scripts),

```toml title="pyproject.toml"
{%
    include-markdown "../pyproject.toml"
    start="venv = \".venv\""
    end="[build-system]"
%}
```

In English the `game_of_life.main:app` reads as,

- `game_of_life` $\Rightarrow$ go to the package called `game_of_life` defined in [`src/game_of_life/__init__.py`](https://github.com/ImperialCollegeLondon/ReCoDE-research-python-patterns/blob/main/src/game_of_life/__init__.py)
- `.main` $\Rightarrow$ in that package go to the module called `main` defined in [`src/game_of_life/main.py`](https://github.com/ImperialCollegeLondon/ReCoDE-research-python-patterns/blob/main/src/game_of_life/main.py)
- `:app` $\Rightarrow$ invoke the function stored in the [variable called `app`](https://github.com/ImperialCollegeLondon/ReCoDE-research-python-patterns/blob/2835a5589068b6446a6e635b0d55c2c9349fc236/src/game_of_life/main.py#L35)

#### Adding dependencies to `pyproject.toml` with `uv`

When using `conda`, dependencies are usually specified using an `environment.yml` file. When using `pip`, dependencies are specified using a `requirements.txt` file. The equivalent of this in the `pyproject.toml` is to specify `dependencies` under the `[project]` table. For this project, it has been specified as,

```toml title="pyproject.toml"
{%
    include-markdown "../pyproject.toml"
    start="requires-python = \">=3.12\""
    end="[project.optional-dependencies]"
%}
```

`uv` integrates with the `pyproject.toml` file as you can add a dependency using the [`uv add` command](https://docs.astral.sh/uv/reference/cli/#uv-add). For example here, to add `matplotlib` as a dependency it would be

```console
$ uv add matplotlib
```

This would add `matplotlib` under `dependencies`.

#### Optional dependencies and dependency groups

!!! abstract "TL;DR"
    Optional dependencies are published on [PyPI](https://pypi.org/) while dependency groups are local for development. To install all development dependencies for this project,
    ```console
    $ uv sync --all-extras
    ```
    For more info about the differences, [check this page out](https://pydevtools.com/handbook/explanation/what-are-optional-dependencies-and-dependency-groups/)



Optional dependencies in a `pyproject.toml` are dependencies which provide optional features that some users may want. For example, in one of our dependencies, `pydantic`, it has [two optional dependencies](https://pydantic.dev/docs/validation/latest/get-started/install/#optional-dependencies): `email` and `timezone`. These features are useful but not every use may want to have them. For this project, running the documentation locally is an optional feature for users, as such they have been placed in a `docs` group as follows,

```toml title="pyproject.toml"
[project.optional-dependencies]
{%
    include-markdown "../pyproject.toml"
    start="[project.optional-dependencies]"
    end="[dependency-groups]"
%}
```

When working on a coding project there are often dependencies that are useful for development but are not required to use and run the code in the project. For example, `pytest` is used for running and writing test but isn't required to run the core code of the project. Such dependencies are called development dependencies. These have been specified in the `pyproject.toml` as follows,

```toml title="pyproject.toml"
[dependency-groups]
{%
    include-markdown "../pyproject.toml"
    start="[dependency-groups]"
    end="[tool.pyright]"
%}
```

The specifics on what each of these dependencies are and why they are useful will be covered through the course of this tutorial.
For more information about dependency groups, [see this webpage on dependency group in uv](https://pydevtools.com/handbook/explanation/understanding-dependency-groups-in-uv/).

!!! info
    The main difference between optional dependencies and dependency groups is at the packaging level. If you're not planning to package your code, then there isn't much of a different even though it is good practice to separate it accordingly.



### Universal lock file for dependencies

`uv.lock`

## Linting and Formatting


## Git Commit Hooks
