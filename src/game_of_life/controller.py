"""
Controller module for the Model-View-Controller (MVC) architecture.

This module contains the controller logic that mediates between the model
(game simulation) and the view (display interface). It handles game initialization,
iteration, and coordination between model and view components.

Design Patterns
    - Factory Pattern: GridCreatorFactory creates appropriate grid creation
      strategies based on configuration.
    - Iterator Pattern: GoLIterator provides controlled iteration over game
      generations.
    - Model-View-Controller (MVC): The controller coordinates between
      GameOfLife (model) and view components.

Notes
-----
The controller uses match/case statements (Python 3.10+) for exhaustive
handling of enum types, enabling the type checker to verify all cases are handled.
"""

from typing import Self, assert_never

from game_of_life.config import (
    GameOfLifeConfigFrom,
    GridInitialiser,
)
from game_of_life.model import GameOfLife, GridCreator, PatternGridCreator, RandomGridCreator, ZerosGridCreator


class GridCreatorFactory:
    """
    Factory for creating appropriate GridCreator instances based on configuration.

    This class implements the Factory Pattern, which is used to encapsulate the
    complex logic of selecting and instantiating the appropriate grid creation
    strategy (zeros, random, or pattern-based) without exposing that logic to
    the client code.

    Attributes
    ----------
    input_config : GameOfLifeConfigFrom
        Configuration object specifying which grid initializer to use.

    Design Patterns
    ---------------
    Factory Pattern: Encapsulates the creation of GridCreator instances,
        allowing the client to request a grid creator without knowing how
        different types are instantiated.

    This is a common pattern when object creation logic is complex and should
    be centralized in one place, making the code easier to maintain and extend.


    """

    def __init__(self, input_config: GameOfLifeConfigFrom) -> None:
        """
        Initialize the factory with a configuration object.

        Parameters
        ----------
        input_config : GameOfLifeConfigFrom
            Configuration specifying the grid initialization strategy.
        """
        self.input_config: GameOfLifeConfigFrom = input_config

    @staticmethod
    def approximate_offset_to_center(full_length: int, to_center_length: int) -> int:
        """
        Calculate the offset to approximately center a smaller element within a larger space.

        This is a utility method for calculating where to place a pattern within
        the game grid so it appears roughly centered.

        Parameters
        ----------
        full_length : int
            The total length of the container space.
        to_center_length : int
            The length of the element to center.

        Returns
        -------
        int
            The offset (starting position) to approximately center the element.
            The result is floored using integer division.

        Notes
        -----
        This method uses integer division, which floors the result. This means
        when exact centering is impossible, the element is placed slightly towards
        the start of the container.

        Examples
        --------
        >>> GridCreatorFactory.approximate_offset_to_center(50, 30)
        10
        >>> GridCreatorFactory.approximate_offset_to_center(50, 31)
        10
        """
        if full_length < to_center_length:
            raise ValueError("Full length must be greater than length to center")
        return (full_length // 2) - (to_center_length // 2)

    def create(self) -> GridCreator:
        """
        Create and return an appropriate GridCreator based on configuration.

        This method encapsulates the logic for instantiating different grid
        creator types, hiding the complexity from the client.

        Returns
        -------
        GridCreator
            An instantiated grid creator of the appropriate type (ZerosGridCreator,
            RandomGridCreator, or PatternGridCreator).

        Raises
        ------
        ValueError
            If PATTERN initializer is selected but no pattern is provided in config.

        Notes
        -----
        This method demonstrates exhaustive pattern matching using Python 3.10+
        match/case statements on enums. The type checker can verify that all
        possible enum values are handled, preventing bugs from unhandled cases.
        The `assert_never()` function serves as a safety net that will raise an
        AssertionError if any case is somehow not covered.

        Examples
        --------
        >>> config = GameOfLifeConfigFrom(grid_initialiser=GridInitialiser.ZEROS)
        >>> factory = GridCreatorFactory(config)
        >>> creator = factory.create()
        >>> type(creator).__name__
        'ZerosGridCreator'
        """
        # As GridInitialiser is an enum, it can only have values equal to the members defined in the class. This allows
        # us to match different branches (like with `if` statements) directly to these values.
        match self.input_config.grid_initialiser:
            case GridInitialiser.ZEROS:  # equivalent to: if self.input_config.grid_initialiser == GridInitialiser.ZEROS
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
                # A benefit of using match ... case syntax on an Enum is that python's type checking system allow us to
                # perform exhaustiveness checking. The `assert_never` signals to the reader and the type checker
                # that all possible cases should be handled such that this code is unreachable. If not all cases
                # have been handled, then the type checker will throw an error.
                # At runtime, this will also raise an AssertionError if this branch is hit.
                assert_never(unreachable)


def create_game_of_life(config: GameOfLifeConfigFrom) -> GameOfLife:
    """
    Convenience wrapper to create a GameOfLife instance from configuration.

    This is a simple factory function that creates a GameOfLife instance
    using GridCreatorFactory to obtain the appropriate grid creator based
    on the provided configuration.

    Parameters
    ----------
    config : GameOfLifeConfigFrom
        Configuration object specifying game parameters.

    Returns
    -------
    GameOfLife
        A fully initialized GameOfLife instance with the grid created according
        to the configuration.

    Examples
    --------
    >>> config = GameOfLifeConfigFrom(num_rows=100, num_cols=100)
    >>> game = create_game_of_life(config)
    >>> game.generation
    0
    >>> game.grid.shape
    (100, 100)
    """
    return GameOfLife(config.num_rows, config.num_cols, grid_creator=GridCreatorFactory(config).create())


class GoLIterator:
    """
    Iterator for controlling Game of Life simulation iterations.

    This class implements the Iterator Pattern, providing a standard interface
    for iterating over game generations. It can operate in two modes: infinite
    iteration (when max_iterations is None) or finite iteration (when
    max_iterations is specified).

    The Iterator Pattern is useful because it decouples the iteration logic
    from the code that uses it, making it easy to swap different iteration
    strategies or modify iteration behavior in one place.

    Attributes
    ----------
    max_iterations : int | None
        Maximum number of iterations to perform. If None, iteration continues
        indefinitely.
    count : int
        Current iteration count. Incremented each time __next__() is called.

    Design Patterns
    ---------------
    Iterator Pattern: Implements the standard Python iterator protocol (__iter__
        and __next__) to allow the object to be used with for loops and other
        Python constructs that expect iterables.

    Notes
    -----
    This class follows Python's iterator protocol, making it usable with for
    loops and other iteration constructs. The iterator yields monotonically
    increasing generation numbers starting from 0.

    Examples
    --------
    >>> iterator = GoLIterator(max_iterations=3)
    >>> for gen in iterator:
    ...     print(f"Generation {gen}")
    Generation 0
    Generation 1
    Generation 2

    """

    def __init__(self, max_iterations: int | None = None) -> None:
        """
        Initialize the iterator.

        Parameters
        ----------
        max_iterations : int | None, optional
            Maximum number of iterations. If None, iteration is infinite.
            Default is None.
        """
        self.max_iterations: int | None = max_iterations
        self.count: int = 0

    def __iter__(self) -> Self:
        """
        Return the iterator object itself.

        Returns
        -------
        Self
            Returns this iterator instance, as required by the Iterator Protocol.

        Notes
        -----
        This method is part of Python's iterator protocol. It allows the object
        to be used with Python's for loop and other iteration constructs.
        """
        return self

    def __next__(self) -> int:
        """
        Return the next generation number and advance the counter.

        Returns
        -------
        int
            The current generation number (0-based).

        Raises
        ------
        StopIteration
            When max_iterations is reached (if specified), signaling the end
            of iteration.

        Notes
        -----
        This method is called by Python's iteration machinery (for loops, list
        comprehensions, etc.). It returns the current generation number then
        increments the counter for the next call.
        """
        if self.max_iterations is not None and self.count >= self.max_iterations:
            raise StopIteration
        self.count += 1
        return self.count - 1


def execute_game_of_life(
    game: GameOfLife,
    # view: BaseView,
    num_generations: int | None,
) -> None:
    """
    Execute the Game of Life simulation for a specified number of generations.

    This function runs the core simulation loop, stepping the game forward
    one generation at a time. It uses the GoLIterator to control the number
    of iterations.

    Parameters
    ----------
    game : GameOfLife
        The game instance to execute.
    num_generations : int | None
        Number of generations to simulate. If None, runs indefinitely (until
        interrupted by the caller).

    Returns
    -------
    None

    Notes
    -----
    This function is designed to be extended with view rendering once the
    view module is integrated. The current implementation shows the skeleton
    with comments indicating where view calls will be added.

    The simulation progresses by calling game.step() once per generation,
    which updates all cells according to the Game of Life rules.

    Examples
    --------
    >>> config = GameOfLifeConfigFrom(num_rows=50, num_cols=50)
    >>> game = create_game_of_life(config)
    >>> execute_game_of_life(game, num_generations=100)
    """
    # with view as opened_view:
    for _ in GoLIterator(num_generations):  # indent once view class is merged
        # view.render(game)
        game.step()
