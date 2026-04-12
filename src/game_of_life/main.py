"""
Main module where the entry point to the code is defined
"""

from pathlib import Path
from typing import Annotated, assert_never

import typer

from game_of_life.config import CLIViewConfig, DisplayInterface, GameOfLifeConfigFrom, PlotViewConfig, RunConfig
from game_of_life.controller import create_game_of_life, execute_game_of_life

# Enable locals to be shown to aid debugging
# NOTE: Do not enable this if it will end up revealing secrets, e.g. passwords, ssh keys, API keys
#       If a test fails in the CI, these secrets will be visible in the logs
app = typer.Typer(pretty_exceptions_show_locals=True)


def _view_factory(run_config: RunConfig) -> None:
    match run_config.interface:
        case DisplayInterface.CLI:
            if not isinstance(run_config.view_config, CLIViewConfig):
                raise ValueError("View config must be of type CLIViewConfig for CLI interface")
            print("create cli view with CLIViewConfig")
        case DisplayInterface.PLOT:
            if not isinstance(run_config.view_config, PlotViewConfig):
                raise ValueError("View config must be of type PlotViewConfig for PLOT interface")
            print("create plot view with PlotViewConfig")
        case _ as unreachable:
            assert_never(unreachable)


@app.command()
def run(
    config: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, readable=True)],
    generations: Annotated[int | None, typer.Option(help="Number of generations", min=1)] = None,
) -> None:
    run_config = RunConfig.from_yaml(config)

    if run_config.interface == DisplayInterface.PLOT and generations is None:
        raise ValueError("Generations must be provided for plot interface")

    _view_factory(run_config)
    game = create_game_of_life(run_config.gol_config)
    execute_game_of_life(game, generations)


@app.command()
def cli(
    gol_config: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, readable=True)],
    speed: Annotated[float, typer.Option(help="Seconds between generations", min=0)] = 0.2,
    generations: Annotated[int | None, typer.Option(help="Number of generations", min=1)] = None,
) -> None:
    print(f"display speed: {speed}")
    print("directly instantiated the CLI view class")
    game = create_game_of_life(GameOfLifeConfigFrom.from_yaml(gol_config))
    execute_game_of_life(game, generations)


@app.command()
def plot(
    gol_config: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, readable=True)],
    output_file: Annotated[Path, typer.Option(file_okay=True, dir_okay=False, writable=True)],
    generations: Annotated[int, typer.Option(help="Number of generations", min=1)] = 100,
) -> None:
    print(f"output file: {output_file}")
    print(f"generations: {generations}")
    print("directly instantiated the PLOT view class")
    game = create_game_of_life(GameOfLifeConfigFrom.from_yaml(gol_config))
    execute_game_of_life(game, generations)
