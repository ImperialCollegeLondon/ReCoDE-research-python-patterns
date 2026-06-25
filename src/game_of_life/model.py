"""Model for Conway's Game of Life simulation.

This module contains the core game logic and data structures for simulating
Conway's Game of Life. It includes:

- Pattern: A data model for representing and encoding game patterns
- GridCreator: Abstract interface for grid initialization strategies
- ZerosGridCreator: Creates an empty (all dead) grid
- RandomGridCreator: Creates a grid with random cell states
- PatternGridCreator: Creates a grid initialized with a specific pattern
- GameOfLife: The main game engine that simulates the cellular automaton

The module implements Conway's classic Game of Life rules: a cell lives if
it has 2-3 live neighbors, a dead cell comes to life with exactly 3 live
neighbors.

"""

import re
from abc import ABC, abstractmethod
from typing import Annotated, ClassVar, Self, override

import numpy as np
import numpy.typing as npt
from pydantic import BaseModel, PositiveInt, StringConstraints, field_validator, model_validator

NDArrayU8 = npt.NDArray[np.uint8]


class Pattern(BaseModel):
    """Model for encoding and validating Game of Life patterns.

    This class uses Pydantic for data validation and represents patterns using
    a Run Length Encoded (RLE) format. The RLE format is a compact way to specify
    which cells are alive and dead without storing the entire grid.

    The RLE format works as follows:
    - 'b' represents a dead cell
    - 'o' represents a live cell
    - '$' represents end of line (row separator)
    - Numbers before a character indicate repetition (e.g., '3b' = 'bbb')
    - '!' marks the end of the pattern

    Example pattern string: "3b$bob$2b!" represents:
        b b b
        b o b
        b b

    Attributes
    ----------
    width : int
        The width (number of columns) of the pattern. Must be positive.
    height : int
        The height (number of rows) of the pattern. Must be positive.
    encoded_pattern : str
        The Run Length Encoded pattern string. Automatically converted to lowercase
        and whitespace is stripped. Must end with '!' and follow the RLE format.

    Raises
    ------
    ValueError
        If the encoded pattern doesn't match the specified width or height.
    ValueError
        If the encoded pattern contains invalid run counts (e.g., zero).

    Examples
    --------
    Create a 3x3 pattern (glider):

    >>> pattern = Pattern(width=3, height=3, encoded_pattern="bob$2bo$3o!")
    >>> print(f"Pattern: {pattern.width}x{pattern.height}")
    Pattern: 3x3

    """

    width: PositiveInt
    height: PositiveInt
    # StringConstraints checks that:
    #   1) min_length=1: String is not empty as it has a minimum length of 1
    #   2) pattern=r"^(\d*[bo$])*!$": String matches this regex pattern which checks that are no invalid characters,
    #                                 ends with an !, and that it matches the structure of specifying the cells in
    #                                 a line then the new line
    #                ^ - Start of string anchor, i.e. match must begin here
    #                    (\d*[bo$])* - Zero or more occurrences of:
    #                        \d* - Zero or more digits
    #                        [bo$] - Followed by exactly one character that is either b, o, or $
    #                $ - End of string anchor, i.e. match must end here
    encoded_pattern: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, pattern=r"^(\d*[bo$])*!$", min_length=1)
    ]

    @field_validator("encoded_pattern", mode="after")
    @classmethod
    def validate_pattern_string(cls, pattern_str: str) -> str:
        """Validate that run counts in the pattern are positive (non-zero).

        This validator checks that any numeric run counts in the RLE string are
        greater than zero. Counts of zero are not meaningful and indicate an error.

        The @field_validator decorator with mode="after" ensures that this validation
        runs after the initial string constraints.

        Parameters
        ----------
        pattern_str : str
            The encoded pattern string to validate (without the trailing '!').

        Returns
        -------
        str
            The validated pattern string unchanged without the trailing '!'.

        Raises
        ------
        ValueError
            If any run count is zero.

        """
        without_end: str = pattern_str[:-1]

        # Check that all numbers are > 0
        #   Pattern contains two groups: 1) any digits (\d+), 2) token characters b, o or $ ([bo$])
        #   Thus, group 1 will contain the count for a given token
        pattern_for_counts = r"(\d+)([bo$])"
        for match in re.finditer(pattern_for_counts, without_end):
            if int(match.group(1)) == 0:
                raise ValueError(f"Run count cannot be 0 at {match.start()}")

        return without_end

    @staticmethod
    def get_counts(match: re.Match[str], *, group_num: int = 1) -> int:
        r"""Extract run count from a regex match group.

        Helper method to extract the numeric repetition count from a regex match.
        If the group is empty, returns 1 (no explicit count means one occurrence).

        Parameters
        ----------
        match : re.Match[str]
            A regex match object from iterating over the pattern string.
        group_num : int, optional
            The group number to extract from. Default is 1.

        Returns
        -------
        int
            The count value from the match group, or 1 if the group was empty.

        Examples
        --------
        >>> import re
        >>> pattern = Pattern(width=3, height=1, encoded_pattern="3b!")
        >>> m = re.search(r"(\d*)([bo])", "3b")
        >>> Pattern.get_counts(m)
        3

        """
        return int(counts) if (counts := match.group(group_num)) else 1

    @model_validator(mode="after")
    def check_height_matches_pattern(self) -> Self:
        """Validate that the pattern height matches the number of newlines.

        Checks that the number of '$' (row separator) characters in the encoded
        pattern matches the expected height. For a pattern of height H, there
        should be H-1 row separators (since the last row doesn't need a separator).

        Parameters
        ----------
        None

        Returns
        -------
        Self
            Returns self if validation passes.

        Raises
        ------
        ValueError
            If the number of row separators doesn't match the specified height.

        """
        num_new_lines: int = self.height - 1
        if self.encoded_pattern.count("$") != num_new_lines:
            # Matches groups of digits with $. Then, sums the digits to get number of new lines for that group
            new_line_sum: int = sum(
                self.get_counts(m, group_num=1) for m in re.finditer(r"(\d*)(\$)", self.encoded_pattern)
            )
            if new_line_sum != num_new_lines:
                raise ValueError("Number of new lines does not match specified pattern height")
        return self

    @model_validator(mode="after")
    def check_width_matches_pattern(self) -> Self:
        """Validate that each row's cell count is less than the pattern width.

        Checks that no row in the pattern exceeds the specified width. Patterns
        may be narrower than the specified width (they will be placed at the
        top-left of a larger grid), but cannot be wider.

        Parameters
        ----------
        None

        Returns
        -------
        Self
            Returns self if validation passes.

        Raises
        ------
        ValueError
            If any row in the pattern exceeds the specified width.

        """
        for row_pattern in self.encoded_pattern.split("$"):
            row_sum: int = sum(
                self.get_counts(match_in_row, group_num=1) for match_in_row in re.finditer(r"(\d*)([bo])", row_pattern)
            )
            if row_sum > self.width:
                raise ValueError("Number of cells is larger than specified pattern width")

        return self

    def populate_grid(self, row_offset: int, col_offset: int, grid: NDArrayU8) -> NDArrayU8:
        """Place this pattern into a grid at the specified offset position.

        Decodes the RLE encoded pattern and fills the grid with the pattern's
        cells starting at the given row and column offsets. Live cells are marked
        as 1, dead cells as 0.

        Parameters
        ----------
        row_offset : int
            The row index in the grid where the pattern starts (top-left).
        col_offset : int
            The column index in the grid where the pattern starts (top-left).
        grid : NDArrayU8
            A 2D numpy array (dtype=uint8) to populate. Will be modified in-place.

        Returns
        -------
        NDArrayU8
            The modified grid with the pattern placed at the offset.

        Examples
        --------
        >>> import numpy as np
        >>> pattern = Pattern(width=2, height=2, encoded_pattern="o$bo!")
        >>> grid = np.zeros((3, 3), dtype=np.uint8)
        >>> grid = pattern.populate_grid(0, 0, grid)
        >>> print(grid)
        [[1 0 0]
         [0 1 0]
         [0 0 0]]

        """
        row_index: int = row_offset

        # New line separate is "$" char => split by "$" yields each row's encoding
        for row_pattern in self.encoded_pattern.split("$"):
            col_index: int = col_offset

            # Regex will match into two groups:
            #   1. (\d*): All digits => gets the number of cells to set. If digit is not specfied, that group yields
            #             an empty string, i.e. ""
            #   2. ([bo]): Matches the characters "b" or "o" which specifies the liveness of a cell
            #              b => dead cell, o => live cell
            for match_in_row in re.finditer(r"(\d*)([bo])", row_pattern):
                num_to_set: int = self.get_counts(match_in_row, group_num=1)

                # else case is where match_in_row.group(2) == "b". Thus, the cell value should be set to 0
                liveness: int = 1 if match_in_row.group(2) == "o" else 0
                if num_to_set > 1:
                    grid[row_index, col_index : col_index + num_to_set] = liveness
                else:
                    grid[row_index, col_index] = liveness

                col_index += num_to_set
            row_index += 1
        return grid


class GridCreator(ABC):
    """Abstract base class for creating initial game grids.

    This interface defines how different strategies can initialize the Game of Life grid.
    By using this abstract class, different initialization methods (empty, random, pattern-based)
    can be implemented without changing the GameOfLife class itself.

    This is an example of the Strategy design pattern: we encapsulate different initialization
    algorithms in separate classes that all follow the same interface.

    Notes
    -----
    Additional keyword arguments needed for grid initialization should be passed to the
    constructor of concrete implementations.

    Examples
    --------
    Creating a GameOfLife with different grid creators:

    Empty grid

    >>> game1 = GameOfLife(grid_creator=ZerosGridCreator())

    Random grid

    >>> game2 = GameOfLife(grid_creator=RandomGridCreator(density=0.3))

    Pattern-based grid

    >>> pattern = Pattern(width=3, height=3, encoded_pattern="bob$2bo$3o!")
    >>> game3 = GameOfLife(grid_creator=PatternGridCreator(pattern))

    """

    @abstractmethod
    def initialise(self, n_rows: int, n_cols: int) -> NDArrayU8:
        """Create and return an initialized grid.

        This abstract method must be implemented by concrete classes to create
        a grid with specific initialization strategy.

        Parameters
        ----------
        n_rows : int
            Number of rows in the grid. Must be positive.
        n_cols : int
            Number of columns in the grid. Must be positive.

        Returns
        -------
        NDArrayU8
            A 2D numpy array of dtype uint8 where each cell is 0 (dead) or 1 (live).

        """
        ...


class ZerosGridCreator(GridCreator):
    """Grid creator that initializes an all-dead (empty) grid.

    This is the simplest grid initialization strategy. It creates a grid where
    all cells are dead (set to 0). This is useful for starting a simulation with
    no live cells, which can then be populated manually.

    Examples
    --------
    >>> creator = ZerosGridCreator()
    >>> grid = creator.initialise(10, 10)
    >>> int(grid.sum())  # No live cells
    0

    """

    def __init__(self) -> None:
        """Initialize the ZerosGridCreator.

        No parameters needed as this strategy always creates the same result.

        Returns
        -------
        None

        """
        super().__init__()

    @override
    def initialise(self, n_rows: int, n_cols: int) -> NDArrayU8:
        """Create a grid with all cells set to dead (0).

        Parameters
        ----------
        n_rows : int
            Number of rows in the grid.
        n_cols : int
            Number of columns in the grid.

        Returns
        -------
        NDArrayU8
            A 2D numpy array with all elements set to 0.

        """
        return np.zeros((n_rows, n_cols), dtype=np.uint8)


class RandomGridCreator(GridCreator):
    """Grid creator that initializes a grid with random cell states.

    This strategy creates grids with cells randomly set to alive or dead according
    to a specified density. This is useful for exploring how different initial
    populations evolve, and is often used in demonstrations of the Game of Life.

    Attributes
    ----------
    _density : float
        Probability that each cell will be alive (1). Should be between 0 and 1.
    _rng_seed : int | None
        Seed for the random number generator for reproducibility. If None,
        each run will produce different results.

    Parameters
    ----------
    density : float, optional
        Probability of a cell being alive. Default is 0.2 (20% of cells alive).
    rng_seed : int | None, optional
        Seed for reproducibility. If None, results are non-deterministic.

    Examples
    --------
    >>> # Create a grid with 30% of cells alive
    >>> creator = RandomGridCreator(density=0.3, rng_seed=42)
    >>> grid = creator.initialise(10, 10)
    >>> grid.sum() > 0  # Should have some live cells
    np.True_

    The same seed produces same grid

    >>> grid1 = RandomGridCreator(rng_seed=42).initialise(5, 5)
    >>> grid2 = RandomGridCreator(rng_seed=42).initialise(5, 5)
    >>> (grid1 == grid2).all()
    np.True_

    """

    def __init__(self, density: float = 0.2, rng_seed: int | None = None) -> None:
        """Initialize the RandomGridCreator with density and optional seed.

        Parameters
        ----------
        density : float, optional
            Probability that a cell will be alive. Must be between 0 and 1.
            Default is 0.2 (20%).
        rng_seed : int | None, optional
            Seed for numpy's random number generator. If provided, the same
            seed produces the same grid each time. Default is None (non-deterministic).

        Returns
        -------
        None

        """
        self._density: float = density
        self._rng_seed: int | None = rng_seed

    @override
    def initialise(self, n_rows: int, n_cols: int) -> NDArrayU8:
        """Create a grid with random cell states.

        Generates a grid where each cell is independently alive (1) or dead (0)
        with probability determined by the density parameter.

        Parameters
        ----------
        n_rows : int
            Number of rows in the grid.
        n_cols : int
            Number of columns in the grid.

        Returns
        -------
        NDArrayU8
            A 2D numpy array with random cell states (0 or 1).

        """
        return np.random.default_rng(seed=self._rng_seed).choice(
            [0, 1], size=(n_rows, n_cols), p=np.asarray([1 - self._density, self._density])
        )


class PatternGridCreator(GridCreator):
    """Grid creator that initializes a grid with a specific pattern.

    This strategy creates grids initialized with a predefined pattern (using RLE format).
    It allows positioning the pattern at a specific offset in the grid. This is useful
    for studying how known patterns evolve (oscillators, spaceships, etc.) or for
    building complex configurations from simpler patterns.

    Attributes
    ----------
    _pattern : Pattern
        The RLE-encoded pattern to place in the grid.
    _row_offset : int
        The row index where the pattern's top-left corner will be placed.
    _col_offset : int
        The column index where the pattern's top-left corner will be placed.

    Parameters
    ----------
    pattern : Pattern
        A Pattern object specifying the cells to initialize.
    row_offset : int, optional
        Starting row position for the pattern. Default is 0 (top).
    col_offset : int, optional
        Starting column position for the pattern. Default is 0 (left).

    Raises
    ------
    ValueError
        If the pattern is larger than the grid or extends beyond grid bounds.

    Examples
    --------
    >>> from game_of_life.model import Pattern, PatternGridCreator, GameOfLife
    >>> # Create a glider pattern
    >>> pattern = Pattern(width=3, height=3, encoded_pattern="bob$2bo$3o!")
    >>> creator = PatternGridCreator(pattern, row_offset=5, col_offset=5)
    >>> game = GameOfLife(n_rows=20, n_cols=20, grid_creator=creator)

    """

    def __init__(self, pattern: Pattern, *, row_offset: int = 0, col_offset: int = 0) -> None:
        """Initialize the PatternGridCreator.

        Parameters
        ----------
        pattern : Pattern
            The pattern to place in the grid.
        row_offset : int, optional
            Row position where the pattern begins. Default is 0.
        col_offset : int, optional
            Column position where the pattern begins. Default is 0.

        Returns
        -------
        None

        Notes
        -----
        The row_offset and col_offset parameters are keyword-only to make
        their purpose explicit and prevent accidental positional argument errors.

        """
        self._pattern: Pattern = pattern
        self._row_offset: int = row_offset
        self._col_offset: int = col_offset

    @override
    def initialise(self, n_rows: int, n_cols: int) -> NDArrayU8:
        """Create a grid initialized with the pattern at the specified offset.

        Creates an all-dead grid and then populates it with the pattern.

        Parameters
        ----------
        n_rows : int
            Number of rows in the grid. Must be large enough for the pattern.
        n_cols : int
            Number of columns in the grid. Must be large enough for the pattern.

        Returns
        -------
        NDArrayU8
            A 2D numpy array with the pattern placed at the offset.

        Raises
        ------
        ValueError
            If the pattern width is larger than grid width.
        ValueError
            If the pattern height is larger than grid height.
        ValueError
            If the pattern with offset exceeds grid bounds in rows.
        ValueError
            If the pattern with offset exceeds grid bounds in columns.

        """
        if self._pattern.width > n_cols or self._pattern.height > n_rows:
            raise ValueError("Pattern is larger than grid")

        if self._row_offset + self._pattern.height > n_rows:
            raise ValueError(
                f"Pattern with row offset exceeds grid bounds by {self._row_offset + self._pattern.height - n_rows}"
            )
        if self._col_offset + self._pattern.width > n_cols:
            raise ValueError(
                f"Pattern with col offset exceeds grid bounds by {self._col_offset + self._pattern.width - n_cols}"
            )

        grid: NDArrayU8 = np.zeros((n_rows, n_cols), dtype=np.uint8)

        return self._pattern.populate_grid(self._row_offset, self._col_offset, grid)


class GameOfLife:
    """Main Game of Life engine implementing Conway's cellular automaton rules.

    This class simulates Conway's Game of Life, a cellular automaton where cells
    evolve according to simple rules based on their neighbors. The simulation can
    wrap at edges (toroidal topology) or treat edges as dead zones, and can be
    initialized in various ways using different GridCreator strategies.

    Conway's Rules:
    1. Any live cell with 2-3 live neighbors survives to the next generation
    2. Any dead cell with exactly 3 live neighbors becomes alive
    3. All other cells die or stay dead

    The class tracks the complete history of all generations, allowing analysis of
    the simulation's evolution over time.

    Attributes
    ----------
    N_BIRTH : int
        The number of live neighbors required for a dead cell to come to life
        (class constant = 3).
    N_SURVIVAL : int
        The number of live neighbors required for a live cell to survive.
        A cell survives with N_BIRTH or N_SURVIVAL neighbors (class constant = 2).
    wrap : bool
        If True, the grid wraps around at edges (toroidal). If False, edges
        are treated as dead zones.
    _generation : int
        Current generation number (incremented each step).
    _grid : NDArrayU8
        Current state of the grid (1 = alive, 0 = dead).
    _history : list[NDArrayU8]
        Complete history of all grid states, from initial state to current.

    Parameters
    ----------
    n_rows : int, optional
        Number of rows in the grid. Default is 50.
    n_cols : int, optional
        Number of columns in the grid. Default is 50.
    wrap : bool, optional
        Whether the grid wraps at edges (toroidal topology). Default is True.
    grid_creator : GridCreator | None, optional
        Strategy for initializing the grid. If None (default), uses ZerosGridCreator.

    Examples
    --------
    Create and run a simple simulation:

    >>> from game_of_life.model import GameOfLife, RandomGridCreator
    >>> game = GameOfLife(n_rows=30, n_cols=30, grid_creator=RandomGridCreator(density=0.3, rng_seed=42))
    >>> # Simulate 100 generations
    >>> for _ in range(100):
    ...     game.step()
    >>> print(f"Final generation: {game.generation}")
    Final generation: 100
    >>> print(f"Population: {game.population()}")
    Population: 83

    """

    N_BIRTH: ClassVar[int] = 3
    """Number of live neighbours for dead cell to live or for cell to survive"""
    N_SURVIVAL: ClassVar[int] = 2  # assumes that N_BIRTH is also a survival
    """Number of live neighbours to survive"""

    def __init__(
        self,
        n_rows: int = 50,
        n_cols: int = 50,
        wrap: bool = True,
        grid_creator: GridCreator | None = None,
    ) -> None:
        """Initialize a Game of Life instance.

        Parameters
        ----------
        n_rows : int, optional
            Number of rows in the grid. Must be positive. Default is 50.
        n_cols : int, optional
            Number of columns in the grid. Must be positive. Default is 50.
        wrap : bool, optional
            If True, the grid uses toroidal (wrapping) boundaries where the edges
            connect to the opposite side. If False, edges are treated as permanently
            dead. Default is True.
        grid_creator : GridCreator | None, optional
            Strategy object for initializing the grid. If None (default), uses
            ZerosGridCreator to create an empty grid. Can be set to RandomGridCreator
            or PatternGridCreator for different initialization strategies.

        Returns
        -------
        None

        """
        self.wrap: bool = wrap
        self._generation: int = 0
        if grid_creator is None:
            grid_creator = ZerosGridCreator()
        self._grid: NDArrayU8 = grid_creator.initialise(n_rows, n_cols)
        self._history: list[NDArrayU8] = [self._grid]

    def population(self) -> int:
        """Count the number of live cells in the current generation.

        Returns
        -------
        int
            The number of cells with value 1 (alive) in the current grid.

        Examples
        --------
        >>> game = GameOfLife(n_rows=5, n_cols=5)
        >>> game.population()
        0

        """
        return int(self._grid.sum())

    @property
    def grid(self) -> NDArrayU8:
        """Get the current grid state.

        Returns
        -------
        NDArrayU8
            The current game grid as a 2D numpy array where 1 = alive, 0 = dead.

        """
        return self._grid

    @property
    def generation(self) -> int:
        """Get the current generation number.

        Returns
        -------
        int
            The number of simulation steps (generations) completed.

        """
        return self._generation

    @property
    def history(self) -> list[NDArrayU8]:
        """Get the complete history of grid states.

        Returns
        -------
        list[NDArrayU8]
            A list of all grid states from initial to current generation.
            Index 0 is the initial state, index n is generation n.

        """
        return self._history

    @property
    def history_3d(self) -> NDArrayU8:
        """Get the complete history as a single 3D array.

        Stacks all historical grids along the z-axis, creating a 3D array where
        the z-index represents the generation number. This is useful for
        visualization or batch analysis.

        Returns
        -------
        NDArrayU8
            A 3D numpy array with shape (n_rows, n_cols, n_generations) where
            the z-dimension contains all generations.

        Examples
        --------
        >>> game = GameOfLife(n_rows=5, n_cols=5)
        >>> game.step()
        >>> game.step()
        >>> history_3d = game.history_3d

        When checking the shape of the history, there will be 3 generations (initial + 2 steps) and the grid size is 5x5

        >>> history_3d.shape
        (5, 5, 3)

        """
        return np.dstack(self._history)

    def compute_next_generation(self) -> NDArrayU8:
        """Compute the next generation grid based on current state.

        Applies Conway's Game of Life rules to each cell:
        - Cells with exactly 3 neighbors become/stay alive
        - Cells with 2 neighbors survive if currently alive
        - All other cells die or remain dead

        Does not modify the current grid; returns a new grid. Call step() to
        update the game state and history.

        Returns
        -------
        NDArrayU8
            The next generation grid computed from the current state.

        Notes
        -----
        This method uses numpy's roll function for efficient neighbor counting.
        The wrap attribute determines boundary behavior (toroidal vs flat edges).

        """
        # Finds the number of neighbours that are alive
        neighbours = (
            np.roll(np.roll(self._grid, 1, axis=0), 1, axis=1)
            + np.roll(np.roll(self._grid, 1, axis=0), -1, axis=1)
            + np.roll(np.roll(self._grid, -1, axis=0), 1, axis=1)
            + np.roll(np.roll(self._grid, -1, axis=0), -1, axis=1)
            + np.roll(self._grid, 1, axis=0)
            + np.roll(self._grid, -1, axis=0)
            + np.roll(self._grid, 1, axis=1)
            + np.roll(self._grid, -1, axis=1)
        )

        # If the number of alive neighbours is N_BIRTH, then the cell will always be alive. This is as there must be
        #   N_BIRTH neighbouring cells for a dead cell to come to life or for it to survive
        # If the number of alive neighbours is N_SURVIVAL, then a cell only survives if it s currently alive.
        # Hence, if
        #   N_BIRTH neighbours => always alive
        #   N_SURVIVAL neighbours => must be alive FIRST to remain alive => additional check
        next_generation = np.where(
            (neighbours == self.N_BIRTH) | ((self._grid == 1) & (neighbours == self.N_SURVIVAL)), 1, 0
        )

        if not self.wrap:
            next_generation[0, :] = 0
            next_generation[-1, :] = 0
            next_generation[:, 0] = 0
            next_generation[:, -1] = 0

        return next_generation

    def step(self) -> None:
        """Advance the simulation by one generation.

        Computes the next generation, updates the current grid, increments the
        generation counter, and stores the new state in the history.

        Returns
        -------
        None

        Examples
        --------
        >>> game = GameOfLife()
        >>> game.generation
        0
        >>> game.step()
        >>> game.generation
        1

        """
        self._generation += 1
        self._grid = self.compute_next_generation()
        self._history.append(self._grid)
