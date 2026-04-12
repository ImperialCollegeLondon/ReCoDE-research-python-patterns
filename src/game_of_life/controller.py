"""
Controller in the Model-View-Controller architecture

It is responsible for linking the model and the view
"""

from typing import Self, assert_never

from game_of_life.config import (
    CLIViewConfig,
    DisplayInterface,
    GameOfLifeConfigFrom,
    GridInitialiser,
    PlotViewConfig,
    RunConfig,
)
from game_of_life.model import GameOfLife, GridCreator, PatternGridCreator, RandomGridCreator, ZerosGridCreator


class GridCreatorFactory:
    def __init__(self, input_config: GameOfLifeConfigFrom) -> None:
        self.input_config: GameOfLifeConfigFrom = input_config

    def create(self) -> GridCreator:
        match self.input_config.grid_initialiser:
            case GridInitialiser.ZEROS:
                return ZerosGridCreator()
            case GridInitialiser.RANDOM:
                if self.input_config.density is not None:
                    return RandomGridCreator(density=float(self.input_config.density))
                return RandomGridCreator()
            case GridInitialiser.PATTERN:
                if self.input_config.pattern is None:
                    raise ValueError("Pattern must be specified for pattern grid initialiser")
                target_pattern = self.input_config.pattern
                # Approximately centre the pattern
                row_offset = (self.input_config.num_rows // 2) - target_pattern.height // 2
                col_offset = (self.input_config.num_cols // 2) - target_pattern.width // 2
                return PatternGridCreator(target_pattern, row_offset=row_offset, col_offset=col_offset)
            case _ as unreachable:
                assert_never(unreachable)


def view_factory(run_config: RunConfig) -> None:
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


def create_game_of_life(config: GameOfLifeConfigFrom) -> GameOfLife:
    return GameOfLife(config.num_rows, config.num_cols, grid_creator=GridCreatorFactory(config).create())


class GoLIterator:
    def __init__(self, max_iterations: int | None = None) -> None:
        self.max_iterations: int | None = max_iterations
        self.count: int = 0

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> int:
        if self.max_iterations is not None and self.count >= self.max_iterations:
            raise StopIteration
        self.count += 1
        return self.count - 1


def execute_game_of_life(
    game: GameOfLife,
    # view: BaseView,
    num_generations: int | None,
) -> None:
    # view.setup()
    for _ in GoLIterator(num_generations):
        # view.render(game)
        game.step()

    # view.teardown()
