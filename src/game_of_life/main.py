"""
Main module containing the command-line interface for the Game of Life application.

This module uses Typer to provide a user-friendly CLI with multiple commands
for running the Game of Life simulation with different configurations and views.

Design Patterns
    - Command Pattern: Each function (run, cli, plot) represents a separate command
      that can be invoked from the CLI.
    - Factory Pattern: The `_view_factory` function creates the appropriate view
      based on the selected interface type.
    - Dependency Injection: Configuration objects are passed to functions rather
      than being created internally, making the code more testable.

Notes
-----
The module uses type hints with Annotated for rich CLI argument validation
and help text generation.
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
    """
    Factory function to create the appropriate view based on configuration.

    This is a private function that demonstrates the Factory Pattern. It takes
    a RunConfig and instantiates the appropriate view type based on the
    interface setting.

    Parameters
    ----------
    run_config : RunConfig
        Complete run configuration including interface type and view settings.

    Raises
    ------
    ValueError
        If the view_config type doesn't match the selected interface.

    Design Patterns
    ---------------
    Factory Pattern: Creates different view objects based on the interface type,
        decoupling the view creation logic from the caller.

    Notes
    -----
    This function uses exhaustive pattern matching on the DisplayInterface enum
    to ensure all interface types are handled. Type guards (isinstance checks)
    provide additional runtime validation that the view_config matches the
    expected type.

    """
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
    """
    Run the Game of Life with configuration from a YAML file.

    This command loads a complete RunConfig from a YAML file, which includes
    both game parameters and view interface configuration, then executes the
    simulation.

    Parameters
    ----------
    config : Path
        Path to the YAML configuration file containing RunConfig.
    generations : int | None, optional
        Number of generations to simulate. If not provided, uses the config's
        value. Required for PLOT interface. Default is None.

    Raises
    ------
    ValueError
        If PLOT interface is selected but generations are not specified.

    Notes
    -----
    This command demonstrates the use of Pydantic's YAML loading, the Factory
    Pattern (via _view_factory), and Dependency Injection by passing
    configuration objects to functions.
    """
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
    """
    Run the Game of Life with a command-line interface display.

    This command loads game configuration from a YAML file and runs the
    simulation with real-time CLI output.

    Parameters
    ----------
    gol_config : Path
        Path to the YAML file containing GameOfLifeConfigFrom.
    speed : float, optional
        Seconds to wait between displaying generations. Must be non-negative.
        Default is 0.2 seconds.
    generations : int | None, optional
        Number of generations to simulate. If not provided, runs indefinitely
        (until interrupted). Default is None.

    Notes
    -----
    This demonstrates a simplified entry point that directly instantiates
    a CLI view rather than loading a complete RunConfig, providing easier
    command-line usage for the common CLI use case.
    """
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
    """
    Run the Game of Life and save visualization plots.

    This command loads game configuration from a YAML file, runs the
    simulation, and saves visualization plots to files.

    Parameters
    ----------
    gol_config : Path
        Path to the YAML file containing GameOfLifeConfigFrom.
    output_file : Path
        Path where the plot output file will be saved. Must be writable.
    generations : int, optional
        Number of generations to simulate. Must be positive. Default is 100.

    Notes
    -----
    Unlike the cli command, this command requires a specific number of
    generations since it needs to produce a final output file. The generation
    count cannot be None.

    This demonstrates providing direct CLI options for parameters that don't
    fit well in the YAML configuration, offering flexibility for command-line
    usage.
    """
    print(f"output file: {output_file}")
    print(f"generations: {generations}")
    print("directly instantiated the PLOT view class")
    game = create_game_of_life(GameOfLifeConfigFrom.from_yaml(gol_config))
    execute_game_of_life(game, generations)
