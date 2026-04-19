"""
Test module for the main CLI module.

This module provides test utilities for testing the command-line interface
commands defined in the main module.

Notes
-----
Uses Typer's CliRunner, which provides a way to invoke CLI commands in tests
without actually starting separate processes. This makes testing faster and
more reliable.

See Also
--------
For more information on testing Typer CLIs, see:
https://typer.tiangolo.com/tutorial/testing/#import-and-create-a-clirunner
"""

from typer.testing import CliRunner

# See: https://typer.tiangolo.com/tutorial/testing/#import-and-create-a-clirunner
runner = CliRunner()
"""
CliRunner instance for testing Typer CLI commands.

Type
----
CliRunner
    A utility from Typer that provides methods to invoke CLI commands in a
    test environment.
"""
