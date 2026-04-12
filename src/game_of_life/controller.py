"""
Controller in the Model-View-Controller architecture

It is responsible for linking the model and the view
"""

from typing import Self, assert_never

from game_of_life.config import (
    GameOfLifeConfigFrom,
    GridInitialiser,
)
from game_of_life.model import GameOfLife, GridCreator, PatternGridCreator, RandomGridCreator, ZerosGridCreator


class GridCreatorFactory:
    """
    Factory class which takes the config to create the GridCreator for the GameOfLife
    """

    def __init__(self, input_config: GameOfLifeConfigFrom) -> None:
        self.input_config: GameOfLifeConfigFrom = input_config

    @staticmethod
    def approximate_offset_to_center(full_length: int, to_center_length: int) -> int:
        return (full_length // 2) - (to_center_length // 2)

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
                row_offset = self.approximate_offset_to_center(self.input_config.num_rows, target_pattern.height)
                col_offset = self.approximate_offset_to_center(self.input_config.num_cols, target_pattern.width)
                return PatternGridCreator(target_pattern, row_offset=row_offset, col_offset=col_offset)
            case _ as unreachable:
                assert_never(unreachable)


def create_game_of_life(config: GameOfLifeConfigFrom) -> GameOfLife:
    """
    Convenience method which takes the config and puts the args into the correct places to instantiate the GameOfLife

    :param config: Configuration for the game of life
    :return: GameOfLife
    """
    return GameOfLife(config.num_rows, config.num_cols, grid_creator=GridCreatorFactory(config).create())


class GoLIterator:
    """
    Iterator which can either be an infinite loop or a finite loop
    """

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
