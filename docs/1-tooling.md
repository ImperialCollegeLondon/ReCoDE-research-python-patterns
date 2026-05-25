# Tooling

This page explores three core tools that strengthen research software development: `uv` for dependency and environment management, `ruff` for automated linting and formatting, and `pre-commit` hooks for quality gates. Beyond `uv`, the latter two act as automated safeguards—they catch mistakes before you run your code, saving valuable debugging time.

## Overview

- `uv`: A fast, modern Python package manager and environment manager that integrates with `pyproject.toml` and produces reproducible lock files
- `ruff`: A unified linter and formatter that enforces code style and catches common errors automatically
- `pre-commit` hooks: Automated checks that run before each git commit, preventing problematic code from entering your repository
- `ty` and `pyright`: Static type checkers which will be covered in the [next tutorial](2-type-hinting.md).


## Python Environment Management

[`uv`](https://docs.astral.sh/uv/) is a Python package manager and environment manager, similar to `pip` and [`conda`](https://www.anaconda.com/docs/main). It offers a few advantages over those tools, namely: substantial performance improvements over `conda`, automatic Python version installation and management, integration with `pyproject.toml`, and a universal lock file (`uv.lock`) for reproducible environments.

### What is the `pyproject.toml` file? And how does it integrate with `uv`

!!! quote "What is the pyproject.toml file?"
    [`pyproject.toml`](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) is a configuration file used by packaging tools, as well as other tools such as linters, type checkers, etc.

A common misconception about the `pyproject.toml` file is that it is not useful unless you're planning to distribute your code by packaging, i.e. bundling it up the code so that others can easily install and use it through [`PyPI` (the python package index)](https://www.software.ac.uk/news/introducing-2026-fellowship-cohort-insights-and-celebrations).
Instead, it is a general-purpose configuration file for Python projects which can be used beyond packaging for specifying settings for tools or dependencies.

The `pyproject.toml` file can also specify the entry point for your Python project. This is how users invoke your code from the command line. This project is a command-line tool for running Conway's Game of Life. Once installed into the virtual environment (see [getting started](index.md#getting-started)), users can invoke it with `game-of-life --help`. This is configured via the [`[project.scripts]`](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#creating-executable-scripts) section:

```toml title="pyproject.toml"
{%
    include-markdown "../pyproject.toml"
    start="venv = \".venv\""
    end="[build-system]"
%}
```

The entry point `game_of_life.main:app` can be broken down as follows:

- `game_of_life` $\Rightarrow$ the package defined in [`src/game_of_life/__init__.py`](https://github.com/ImperialCollegeLondon/ReCoDE-research-python-patterns/blob/main/src/game_of_life/__init__.py)
- `.main` $\Rightarrow$ the module defined in [`src/game_of_life/main.py`](https://github.com/ImperialCollegeLondon/ReCoDE-research-python-patterns/blob/main/src/game_of_life/main.py)
- `:app` $\Rightarrow$ the callable function stored in the [variable `app`](https://github.com/ImperialCollegeLondon/ReCoDE-research-python-patterns/blob/2835a5589068b6446a6e635b0d55c2c9349fc236/src/game_of_life/main.py#L35)

#### Adding dependencies to `pyproject.toml` with `uv`

When using `conda`, dependencies are usually specified using an `environment.yml` file. When using `pip`, dependencies are specified using a `requirements.txt` file. The equivalent of this in the `pyproject.toml` is to specify `dependencies` under the `[project]` table. For this project, it has been specified as,

```toml title="pyproject.toml"
{%
    include-markdown "../pyproject.toml"
    start="requires-python = \">=3.12\""
    end="[project.optional-dependencies]"
%}
```

`uv` integrates with `pyproject.toml` through the [`uv add` command](https://docs.astral.sh/uv/reference/cli/#uv-add). For example, to add `matplotlib` as a dependency:

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

Optional dependencies are features that some users may want, but not all require. For example, `pydantic` offers [two optional dependencies](https://pydantic.dev/docs/validation/latest/get-started/install/#optional-dependencies): `email` and `timezone`. In this project, documentation tools are grouped as an optional `docs` feature, allowing users who don't need documentation to avoid installing the extra dependencies:

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
    The main difference between optional dependencies and dependency groups lies at the packaging level. If you're not planning to distribute your code as a package, the distinction matters less, though it remains good practice to organise them appropriately.

`uv`'s [documentation on managing dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/) has more information about the different types of dependencies and how to manage them.

### Universal lock file for dependencies

![it works on my machine meme](https://raw.githubusercontent.com/DXHeroes/knowledge-base-content/master/files/it_works.jpg){ width="320" align=right }

One of the most common frustrations in software development is when code works perfectly on your machine but fails on someone else's. This is often down to differences in the versions of dependencies being used, a problem that gets worse the longer dependencies go without being updated and can quickly spiral into what is known as [dependency hell](https://en.wikipedia.org/wiki/Dependency_hell).

In research software, this is particularly prevalent as keeping dependencies up to date is rarely prioritised. Beyond convenience for users, [reproducibility](https://book.the-turing-way.org/reproducible-research/overview/overview-definitions/)reproducibility depends on others being able to run the exact code that produced your results. [The Turing Way](https://book.the-turing-way.org/) offers [excellent guidance](https://book.the-turing-way.org/reproducible-research/reproducible-research/) on research reproducibility best practices.

!!! quote "What does a lock file do?"
    A [lockfile](https://docs.astral.sh/uv/concepts/projects/layout/#the-lockfile) ensures that developers working on the project are using a consistent set of package versions. Additionally, it ensures when deploying the project as an application that the exact set of used package versions is known

`uv` solves this through the [`uv.lock` file](https://docs.astral.sh/uv/concepts/projects/layout/#the-lockfile), which records the specific versions of all installed packages. See `uv`'s documentation on [locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/#locking-and-syncing) for more details.

To update all dependencies, use:

```console
$ uv lock --upgrade
```

Recently, Python introduced the [`pylock.toml` specification](https://packaging.python.org/en/latest/specifications/pylock-toml/) which is a tooling independent file "for specifying dependencies to enable reproducible installation in a Python environment".


## Linting and Formatting

- Explain what is a linter and why it is useful
- Configured with the ruff.toml file
- Explain what the various things specified in the toml file do
- Mention that the configuration in the ruff.toml file can be placed in the pyproject.toml file and is part of what the pyproject.toml file is for. This has been separated out to make it neater and easier to read

## Git Commit Hooks

- What are these hooks? Tools like `prek` and `pre-commit` do this job
- Link this to the pyproject.toml
- Explain what is going on in the .pre-commit-config.yaml file
- Explain that ruff is invoked during this process so it runs to check that everything is sound statically and before any bad code is committed. This helps to keep a cleaner git history too
- Don't go into details about `pyright` as that would be covered in the next tutorial
