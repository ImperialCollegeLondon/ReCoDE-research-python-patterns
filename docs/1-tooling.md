# Tooling

This page explores three core tools that strengthen research software development: `uv` for dependency and environment management, `ruff` for automated linting and formatting, and `pre-commit` hooks for quality gates. Beyond `uv`, the latter two act as automated safeguards—they catch mistakes before you run your code, saving valuable debugging time.

## Overview

- `uv`: A fast, modern Python package manager and environment manager that integrates with `pyproject.toml` and produces reproducible lock files
- `ruff`: A unified linter and formatter that enforces code style and catches common errors automatically
- `pre-commit` hooks: Automated checks that run before each git commit, preventing problematic code from entering your repository
<!-- ADD LINK IN THE NEXT PR: [next tutorial](2-type-hinting.md)  -->
- `ty` and `pyright`: Static type checkers which will be covered in the next tutorial.


## Python Environment Management

[`uv`](https://docs.astral.sh/uv/) is a Python package manager and environment manager, similar to `pip` and [`conda`](https://www.anaconda.com/docs/main). It offers a few advantages over those tools, namely: substantial performance improvements over `conda`, automatic Python version installation and management, integration with `pyproject.toml`, and a universal lock file (`uv.lock`) for reproducible environments.

### What is the `pyproject.toml` file? And how does it integrate with `uv`

!!! quote "What is the pyproject.toml file?"
    [`pyproject.toml`](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) is a configuration file used by packaging tools, as well as other tools such as linters, type checkers, etc.

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

A common misconception about the `pyproject.toml` file is that it is not useful unless you're planning to distribute your code by packaging, i.e. bundling it up the code so that others can easily install and use it through [`PyPI` (the python package index)](https://pypi.org/).

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

### Why Linting and Formatting Matter

In research software development, it's easy to focus solely on getting your code to work; making sure your simulation runs and your analysis produces the right output. However, code that only "works" can still be problematic. A linter is a tool that automatically scans your code *before* you run it to spot issues, such as: unused variables, inconsistent naming conventions, import problems, or code that violates style guidelines. Rather than discovering these issues when tests fail or code is reviewed, a linter catches them immediately while you're working.

A formatter complements a linter by automatically rewriting your code to follow consistent style conventions, such as line length, spacing, and quote style. Together, linters and formatters serve as an automated code reviewer that enforces standards without requiring human effort. In a research context, this is helps to reduces cognitive load (you don't have to think about style), prevents sneaky bugs (unused imports or variables often indicate logic errors), and makes your code more readable to collaborators and your future self.

!!! tip
    Most editors and IDEs can run a linter in the background as you write. The shorter the feedback loop, the easier the fix. Catching a style or logic issue while you are still in that part of the code beats finding it later in testing or code review.


### Ruff for Linting and Formatting

This project uses [`ruff`](https://docs.astral.sh/ruff/), a fast, all-in-one linter and formatter written in Rust. Ruff combines the functionality of several traditional Python tools (like `flake8`, `isort`, `black`) into a single tool that is substantially faster than running them separately.

#### Configuration: `ruff.toml`

Rather than embedding ruff configuration in the `pyproject.toml` file, this project maintains a separate `ruff.toml` file. This separation improves readability and makes it easier to reason about linting rules without scrolling through project metadata. However, this configuration could equivalently be placed under a `[tool.ruff]` section in `pyproject.toml`. Both are standard and valid approaches.

The configuration starts by specifying the that the format for the project.
Here, the `line-length = 120` setting allows lines up to 120 characters. This is more relaxed than the Python default (79 characters) which is very restrictive and not necessary for modern screens and terminal.

```toml title="ruff.toml"
{%
    include-markdown "../ruff.toml"
    end="[lint]"
%}
```

The next section specifies which linting rules to enforce.
By default, `ruff` only enforces a subset of rules, namely [`Pyflake` (`F`)](https://docs.astral.sh/ruff/rules/#pyflakes-f) and some [`pycodestyle` (`E`)](https://docs.astral.sh/ruff/rules/#error-e) rules. If you're just starting out with Python, that is a good place to begin without being overwhelmed. If you have some experience with Python, extending the rule set is particularly useful for learning best practices and common pitfalls.
In the `ruff.toml` file, the `[lint]` section uses `select` to explicitly list which rule categories ruff should apply. This is better than extending the default rules because it makes the chosen rules explicit and visible.

```toml title="ruff.toml (excerpt)"
{%
    include-markdown "../ruff.toml"
    start="line-length = 120"
    end="[lint.pydocstyle]"
%}
```

Some of the key categories active in this project are,

- `F` (PyFlakes): Detects undefined names, unused imports, unused variables
- `E`, `W` (pycodestyle): Enforces PEP 8 style guidelines
- `I` (isort): Ensures imports are sorted and organized consistently
- `ANN` (annotations): Encourages type annotations on function arguments and returns
- `D` (pydocstyle): Checks that docstrings follow the NumPy convention (specified via `convention = "numpy"`)
- `NPY`, `PT`, `PL`: Domain-specific rules for NumPy, pytest, and pylint

The `ignore` list carves out specific rules that would otherwise conflict or be too strict for this project.

The `ruff` documentation provides more information on [rule selection](https://docs.astral.sh/ruff/linter/#rule-selection) and [details on what each of these rules contain](https://docs.astral.sh/ruff/rules/).

!!! tip
    Part of gaining mastery in a programming language is learning when some of these rules should be broken.

#### Running ruff

To [check your code with ruff](https://docs.astral.sh/ruff/linter/#ruff-check), run:

```console
$ ruff check .
```

To automatically fix issues that ruff can resolve, use:

```console
$ ruff check . --fix
```

To [format your code](https://docs.astral.sh/ruff/formatter/) consistently, use:

```console
$ ruff format .
```

## Git Commit Hooks

### What Are Git Commit Hooks?

Git allows you to automatically run scripts at certain points in the version control workflow, these are called *hooks*. A pre-commit hook runs automatically just before you commit, giving you an opportunity to check your work and reject the commit if issues are found. Pre-commit hooks are invaluable for maintaining code quality because they prevent bad code from entering your repository in the first place. Rather than discovering problems after commit (during code review or CI/CD), hooks catch them in your local workflow.

Without automation, pre-commit checks require discipline and manual execution. The tools like [`pre-commit`](https://pre-commit.com/) and [`prek`](https://prek.j178.dev/) makes managing these hooks easy: it reads a configuration file, installs the hooks into your repository, and runs them automatically when you commit.

In this project, both `pre-commit` and [`prek`](https://prek.j178.dev/) can be used to run the hooks. The latter does not need any additional set up as it part of the development dependencies. Simply activate the Python environment with the development dependencies to use it.

### Managing Hooks with `prek`

This project uses the `prek` to manage git hooks. As it is specified as a development dependency, it will be installed in the Python environment which has been synced using the `uv sync --all-extras` command. The [quick start guide](https://prek.j178.dev/quickstart/#new-to-pre-commit-style-workflows) in the documentation contains more information generic set up.

The configuration is for this project is specified in `.pre-commit-config.yaml`:

```yaml title=".pre-commit-config.yaml"
{%
    include-markdown "../.pre-commit-config.yaml"
%}
```

This file declares which "repositories" (tools) should be run as hooks, along with their versions and which specific hooks to execute from each tool.

#### Understanding Each Hook Repository

**Pre-commit hooks (basic checks)**: The first repository provides general-purpose checks managed by the pre-commit framework itself:
- `trailing-whitespace`: Removes trailing whitespace at the end of lines
- `end-of-file-fixer`: Ensures files end with exactly one newline
- `check-added-large-files`: Prevents accidentally committing large files
- `check-case-conflict`: Detects files that differ only in case (problematic on case-insensitive filesystems)
- `check-toml`: Validates that TOML files (like `pyproject.toml`) are syntactically correct
- `check-yaml`: Validates YAML files

**Ruff hooks (linting and formatting)**: The ruff-pre-commit repository runs your configured linting and formatting checks:
- `ruff-check --fix`: Automatically fixes linting issues that can be auto-corrected
- `ruff-format`: Formats code to match the configured style

These hooks apply the same rules defined in `ruff.toml`, ensuring that all code entering the repository meets the project's code quality standards.

**UV lock hook**: The `uv-lock` hook ensures that `uv.lock` is kept in sync with `pyproject.toml`. When you add or modify dependencies, this hook will update the lockfile automatically.

<!-- ADD LINK IN NEXT PR [separate tutorial](2-type-hinting.md) -->
**Type checking (pyright)**: The `pyright` hook runs static type analysis to catch type mismatches. Type checking is detailed in a separate tutorial. It's mentioned here only to show how it's integrated into the commit workflow.

#### Workflow in Practice

##### Before committing

Before attempting to commit, the hooks can be run using `prek -a`. The example below shows a case where the formatting of the file had failed. As the issue can be fixed automatically, the hook fixes it.

```console
$ prek -a
trim trailing whitespace.................................................Failed
- hook id: trailing-whitespace
- exit code: 1
- files were modified by this hook

  Fixing docs/1-tooling.md
fix end of files.........................................................Passed
check for added large files..............................................Passed
check for case conflicts.................................................Passed
check toml...............................................................Passed
check yaml...............................................................Passed
ruff check...............................................................Passed
ruff format..............................................................Passed
uv-lock..................................................................Passed
pyright..................................................................Passed
```

When `prek` is run again, all the checks pass,

```console
$ prek -a
trim trailing whitespace.................................................Passed
fix end of files.........................................................Passed
check for added large files..............................................Passed
check for case conflicts.................................................Passed
check toml...............................................................Passed
check yaml...............................................................Passed
ruff check...............................................................Passed
ruff format..............................................................Passed
uv-lock..................................................................Passed
pyright..................................................................Passed
```

##### Making a commit

When you attempt to commit:

```console
$ git commit -m "feat: Add feature"
```

Pre-commit automatically runs all configured hooks on the staged files. If any hook fails, your commit is blocked:

```
ruff check failed
...
# Fix the issues, then:
$ git add .
$ git commit -m "Add feature"  # Try again
```

Once all hooks pass, the commit succeeds.

### Shift Left on Quality

The term ["shift left"](https://en.wikipedia.org/wiki/Shift-left_testing) refers to catching issues as early as possible in development—moving quality checks leftward on the timeline from "after deployment" to "before commit". Pre-commit hooks are a means to achieving it. It helps by catching problems locally, before they ever reach a pull request or shared branch. This makes code review more productive (reviewers focus on logic, not formatting) and keeps the git history clean and consistent.

In research software, where reproducibility depends on having a clear record of what was tested and why, maintaining a clean commit history via pre-commit hooks is particularly valuable.
