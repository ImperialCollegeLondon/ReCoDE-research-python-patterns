from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer()


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
