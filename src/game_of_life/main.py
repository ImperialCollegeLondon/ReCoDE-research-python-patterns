"""
Main module where the entry point to the code is defined
"""

from pathlib import Path
from typing import Annotated

import typer

# Enable locals to be shown to aid debugging
# NOTE: Do not enable this if it will end up revealing secrets, e.g. passwords, ssh keys, API keys
#       If a test fails in the CI, these secrets will be visible in the logs
app = typer.Typer(pretty_exceptions_show_locals=True)


@app.command()
def run(
    config: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, readable=True)],
) -> None:
    print(f"config file path: {config}")


@app.command()
def cli(
    gol_config: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, readable=True)],
    speed: Annotated[float, typer.Option(help="Seconds between generations", min=0)] = 0.2,
    generations: Annotated[int | None, typer.Option(help="Number of generations", min=1)] = None,
) -> None:
    print(f"config file path: {gol_config}")
    print(f"display speed: {speed}")
    print(f"generations: {generations}")


@app.command()
def plot(
    gol_config: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, readable=True)],
    output_file: Annotated[Path, typer.Option(file_okay=True, dir_okay=False, writable=True)],
    generations: Annotated[int, typer.Option(help="Number of generations", min=1)] = 100,
) -> None:
    print(f"config file path: {gol_config}")
    print(f"output file: {output_file}")
    print(f"generations: {generations}")
