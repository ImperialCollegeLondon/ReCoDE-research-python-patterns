"""Unit tests for the Game of Life model module.

This test module validates the core game logic including:
- Grid initialization with different strategies
- Pattern encoding and validation
- Game step computation and rule application
- Boundary conditions (wrapping vs non-wrapping edges)

These tests ensure the game engine behaves correctly according to Conway's
Game of Life rules.

Examples
--------
Tests can be run using pytest:

    pytest tests/test_model.py

With uv, the command will be:

    uv run pytest tests/test_model.py

"""

import numpy as np
import pytest
from pydantic import ValidationError

from game_of_life.model import GameOfLife, Pattern, PatternGridCreator, RandomGridCreator


class TestGrid:
    """Test suite for Game of Life grid initialization and behavior.

    This class tests various aspects of grid creation, initialization, and
    game simulation including different grid creation strategies, pattern
    placement, and boundary conditions.

    Class Attributes
    ----------------
    default_n_rows : int
        Default grid size used in tests (50 rows).
    default_n_cols : int
        Default grid size used in tests (50 columns).
    four_cells : Pattern
        A simple test pattern with four live cells in a row.
    t_tetromino : Pattern
        A T-shaped test pattern used for multi-row testing.
    """

    default_n_rows: int = 50
    default_n_cols: int = 50
    four_cells: Pattern = Pattern(width=4, height=1, encoded_pattern="4o!")
    t_tetromino: Pattern = Pattern(width=3, height=2, encoded_pattern="bo$3o!")

    def test_default_grid_dimensions(self) -> None:
        """Test that a GameOfLife instance created with default parameters has correct dimensions.

        Verifies that the default grid is 50x50 and starts with no live cells.
        This is a smoke test ensuring basic initialization works.
        """
        grid = GameOfLife()
        assert grid.grid.shape == (self.default_n_rows, self.default_n_cols)
        assert grid.population() == 0

    def test_custom_grid_dimensions(self) -> None:
        """Test that custom grid dimensions are properly set.

        Creates a 10x10 grid and verifies its size and initial population.
        """
        custom_size: int = 10
        grid = GameOfLife(n_rows=custom_size, n_cols=custom_size)
        assert grid.grid.shape == (custom_size, custom_size)
        assert grid.population() == 0

    def test_randomise_grid_sparse(self) -> None:
        """Test RandomGridCreator with sparse density (10% live cells).

        Verifies that random initialization produces approximately the expected
        number of live cells given a 10% density setting.
        """
        grid = GameOfLife(grid_creator=RandomGridCreator(density=0.1))
        assert grid.population() != 0
        num_cells: int = self.default_n_rows * self.default_n_cols
        assert (0.05 * num_cells) < grid.population() < (0.15 * num_cells)

    def test_randomise_grid_no_density(self) -> None:
        """Test RandomGridCreator with default density parameter.

        Verifies that the default density (20%) produces a reasonable number
        of live cells without explicit density specification.
        """
        grid = GameOfLife(grid_creator=RandomGridCreator())
        assert grid.population() != 0
        num_cells: int = self.default_n_rows * self.default_n_cols
        assert (0.1 * num_cells) < grid.population() < (0.25 * num_cells)

    def test_randomise_grid_filled(self) -> None:
        """Test RandomGridCreator with maximum density (100% live cells).

        Verifies that density=1.0 produces a completely filled grid.
        """
        grid = GameOfLife(grid_creator=RandomGridCreator(density=1))
        assert grid.population() != 0
        num_cells: int = self.default_n_rows * self.default_n_cols
        assert num_cells == grid.population()

    def test_step_empty_grid(self) -> None:
        """Test that an empty grid remains empty after one generation.

        Verifies that with no live cells, the game rules produce no live cells
        (no spontaneous generation).
        """
        grid = GameOfLife()
        assert grid.population() == 0
        grid.step()
        assert grid.population() == 0

    @pytest.mark.parametrize("rng_seed", [1, 53, 100, 344, 1234576])
    def test_step_non_empty_grid_increase(self, rng_seed: int) -> None:
        """Test that certain random configurations grow in population.

        Tests with multiple random seeds that a 30% density random grid
        typically increases in population after one generation (cells reproduce).
        """
        grid = GameOfLife(grid_creator=RandomGridCreator(density=0.3, rng_seed=rng_seed))
        original_count: int = grid.population()
        grid.step()
        assert grid.population() > original_count

    @pytest.mark.parametrize("seed", [1, 53, 100, 344, 1234576])
    def test_step_non_empty_grid_decrease(self, seed: int) -> None:
        """Test that densely populated grids decrease in population.

        Tests with multiple seeds that a 70% density random grid typically
        decreases after one generation due to overcrowding.
        """
        grid = GameOfLife(grid_creator=RandomGridCreator(density=0.7, rng_seed=seed))
        original_count: int = grid.population()
        grid.step()
        assert grid.population() < original_count

    def test_initialise_with_pattern_zero_offset(self) -> None:
        """Test that patterns are correctly placed at the grid origin (0,0).

        Creates a grid with a 4-cell pattern at the top-left and verifies
        the pattern is in the correct position.
        """
        grid = GameOfLife(grid_creator=PatternGridCreator(self.four_cells))
        num_in_pattern: int = 4
        assert grid.population() == num_in_pattern
        np.testing.assert_array_equal(grid.grid[0, 0:4], np.ones((4), dtype=np.uint8))

    @pytest.mark.parametrize(("col_offset", "row_offset"), [(1, 1), (5, 7), (45, 45)])
    def test_initialise_with_pattern_with_offset(self, col_offset: int, row_offset: int) -> None:
        """Test that patterns are correctly placed at specified offsets.

        Verifies pattern placement at various row and column offsets.

        Parameters
        ----------
        col_offset : int
            Column position where pattern should be placed.
        row_offset : int
            Row position where pattern should be placed.

        """
        grid = GameOfLife(
            grid_creator=PatternGridCreator(self.four_cells, col_offset=col_offset, row_offset=row_offset)
        )
        assert grid.population() == 4
        np.testing.assert_array_equal(
            grid.grid[0 + row_offset, 0 + col_offset : 4 + col_offset], np.ones((4), dtype=np.uint8)
        )

    def test_step_four_cell_pattern(self) -> None:
        """Test the evolution of a 4-cell line pattern over multiple generations.

        The 4-cell horizontal line should evolve into a blinker pattern
        (oscillates between horizontal and vertical orientations).
        """
        grid = GameOfLife(grid_creator=PatternGridCreator(self.four_cells, col_offset=1, row_offset=1))
        assert grid.generation == 0
        np.testing.assert_array_equal(grid.grid[1, 1:5], np.ones((4), dtype=np.uint8))
        grid.step()
        np.testing.assert_array_equal(grid.grid[0:3, 2:4], np.ones((3, 2), dtype=np.uint8))
        np.testing.assert_array_equal(np.nonzero(grid.grid)[0], np.asarray([0, 0, 1, 1, 2, 2]))
        np.testing.assert_array_equal(np.nonzero(grid.grid)[1], np.asarray([2, 3, 2, 3, 2, 3]))
        grid.step()
        assert len(np.nonzero(grid.grid)[0]) == 6
        np.testing.assert_array_equal(np.nonzero(grid.grid)[0], np.asarray([0, 0, 1, 1, 2, 2]))
        np.testing.assert_array_equal(np.nonzero(grid.grid)[1], np.asarray([2, 3, 1, 4, 2, 3]))
        grid.step()
        # After the first step, the pattern does not change
        np.testing.assert_array_equal(np.nonzero(grid.grid)[0], np.asarray([0, 0, 1, 1, 2, 2]))
        np.testing.assert_array_equal(np.nonzero(grid.grid)[1], np.asarray([2, 3, 1, 4, 2, 3]))

    def test_step_four_cell_pattern_wraps(self) -> None:
        """Test that patterns interact correctly with wrapping (toroidal) boundaries.

        Verifies that with wrap=True (default), cells at edges wrap to opposite sides.
        """
        grid = GameOfLife(grid_creator=PatternGridCreator(self.four_cells))
        assert grid.generation == 0
        np.testing.assert_array_equal(grid.grid[0, 0:4], np.ones((4), dtype=np.uint8))
        grid.step()
        np.testing.assert_array_equal(np.nonzero(grid.grid)[0], np.asarray([0, 0, 1, 1, 49, 49]))
        np.testing.assert_array_equal(np.nonzero(grid.grid)[1], np.asarray([1, 2, 1, 2, 1, 2]))

    def test_step_four_cell_pattern_no_wrap(self) -> None:
        """Test that patterns interact correctly with non-wrapping boundaries.

        Verifies that with wrap=False, edges are dead zones and patterns
        don't wrap around.
        """
        grid = GameOfLife(grid_creator=PatternGridCreator(self.four_cells), wrap=False)
        assert grid.generation == 0
        np.testing.assert_array_equal(grid.grid[0, 0:4], np.ones((4), dtype=np.uint8))
        grid.step()
        np.testing.assert_array_equal(np.nonzero(grid.grid)[0], np.asarray([1, 1]))
        np.testing.assert_array_equal(np.nonzero(grid.grid)[1], np.asarray([1, 2]))

    def test_t_tetromino_init(self) -> None:
        """Test initialization of a T-shaped tetromino pattern.

        Verifies correct placement and population count of a multi-row pattern.
        """
        grid = GameOfLife(grid_creator=PatternGridCreator(self.t_tetromino, col_offset=25, row_offset=25))
        starting_population: int = 4
        assert grid.population() == starting_population
        np.testing.assert_array_equal(np.nonzero(grid.grid)[0], np.asarray([25, 26, 26, 26]))
        np.testing.assert_array_equal(np.nonzero(grid.grid)[1], np.asarray([26, 25, 26, 27]))

    def test_t_tetromino_grid_too_small(self) -> None:
        """Test that creating a pattern in a too-small grid raises ValueError.

        Verifies error handling when pattern dimensions exceed grid dimensions.
        """
        with pytest.raises(ValueError, match="Pattern is larger than grid"):
            _ = GameOfLife(
                grid_creator=PatternGridCreator(self.t_tetromino, col_offset=25, row_offset=25), n_rows=1, n_cols=2
            )

    @pytest.mark.parametrize(("col_offset", "row_offset"), [(1, 60), (60, 7), (60, 60)])
    def test_pattern_outside_grid(self, col_offset: int, row_offset: int) -> None:
        """Test that placing a pattern with an offset outside grid bounds raises ValueError.

        Verifies error handling when pattern placement would exceed grid boundaries.

        Parameters
        ----------
        col_offset : int
            Column offset that places pattern outside grid.
        row_offset : int
            Row offset that places pattern outside grid.

        """
        with pytest.raises(ValueError, match=r".*offset exceeds grid bounds by.*"):
            _ = GameOfLife(
                grid_creator=PatternGridCreator(self.four_cells, col_offset=col_offset, row_offset=row_offset)
            )


class TestPatternValidation:
    """Test suite for Pattern encoding and validation.

    Tests the Pattern class's RLE (Run Length Encoded) format parsing and validation,
    ensuring patterns are correctly encoded, validated, and that invalid patterns
    are rejected with appropriate error messages.
    """

    def test_valid_light_weight_spaceship(self) -> None:
        """Test that a valid known pattern (light-weight spaceship) is accepted.

        The light-weight spaceship is a known moving pattern in Game of Life.
        """
        _ = Pattern(width=5, height=4, encoded_pattern="o2bo$4bo$o3bo$b4o!")

    def test_valid_gosper_glider_gun(self) -> None:
        """Test that a valid complex pattern (Gosper glider gun) is accepted.

        The Gosper glider gun is a famous complex pattern that generates gliders.
        """
        _ = Pattern(
            width=36,
            height=16,
            encoded_pattern="27bo$26bobo$9b2o15b2obo4b2o$9bobo14b2ob2o3b2o$2o2b2o6bo13b2obo$2obo2bo2bo2bo13bobo$4b2o6bo8bo5bo$9bobo7bobo$9b2o9b2o5$28bo$29bo$27b3o!",
        )

    def test_empty_string(self) -> None:
        """Test that an empty pattern string is rejected.

        Empty strings are not valid patterns per the RLE format.
        """
        with pytest.raises(ValidationError):
            _ = Pattern(width=5, height=4, encoded_pattern="")

    def test_no_end_of_pattern(self) -> None:
        """Test that patterns missing the '!' terminator are rejected.

        All RLE patterns must end with '!' to be valid.
        """
        with pytest.raises(ValidationError):
            _ = Pattern(width=5, height=4, encoded_pattern="o2bo$4bo$o3bo$b4o")

    def test_only_end_of_pattern_pass(self) -> None:
        """Test that a single '!' terminator with matching dimensions is valid.

        This represents an empty pattern (no live cells) with width=5, height=1.
        """
        _ = Pattern(width=5, height=1, encoded_pattern="!")

    def test_only_end_of_pattern_fails(self) -> None:
        """Test that '!' alone is rejected when height doesn't match.

        A 1-row pattern cannot have height=4.
        """
        with pytest.raises(ValueError, match="Number of new lines does not match specified pattern height"):
            _ = Pattern(width=5, height=4, encoded_pattern="!")

    @pytest.mark.parametrize("pattern", ["o2kbo$4bo$o3bo$b4o!", "o2bo$4bio$o3bo$b4o!", "o2bo$4bo$o3$9999i$bo$b4o!"])
    def test_invalid_character_or_structure(self, pattern: str) -> None:
        """Test that patterns with invalid characters are rejected.

        RLE patterns may only contain digits, 'b', 'o', '$', and '!'.

        Parameters
        ----------
        pattern : str
            An invalid pattern string containing invalid characters.

        """
        with pytest.raises(ValidationError):
            _ = Pattern(width=5, height=4, encoded_pattern=pattern)

    @pytest.mark.parametrize("pattern", ["o0bo$4bo$o3bo$b4o!", "o2bo$4b0o$o3bo$b4o!", "o2bo0$4bo$o3bo$b4o!"])
    def test_count_starts_with_zero(self, pattern: str) -> None:
        """Test that patterns with zero run counts are rejected.

        Counts of zero are meaningless and indicate an error in the pattern.

        Parameters
        ----------
        pattern : str
            A pattern string with one or more zero run counts.

        """
        with pytest.raises(ValueError, match="Run count cannot be 0 at"):
            _ = Pattern(width=5, height=4, encoded_pattern=pattern)

    @pytest.mark.parametrize("pattern", ["$$$$!", "b$b$b$b$!", "4$!", "$!", "b$!", "2$!", "bo$5$!"])
    def test_num_rows_no_match_height(self, pattern: str) -> None:
        """Test that patterns with mismatched row counts are rejected.

        The number of '$' (row separator) characters must correspond to the
        specified height. For height=H, there should be H-1 row separators.

        Parameters
        ----------
        pattern : str
            A pattern with incorrect number of rows for the specified height.

        """
        with pytest.raises(ValueError, match="Number of new lines does not match specified pattern height"):
            _ = Pattern(width=5, height=4, encoded_pattern=pattern)

    @pytest.mark.parametrize("pattern", ["o2bo$4bo$o3bo!", "4b$5bo$3o!", "obobo$4o$o!"])
    def test_num_rows_too_wide(self, pattern: str) -> None:
        """Test that patterns exceeding the specified width are rejected.

        Each row's cell count must not exceed the specified width.

        Parameters
        ----------
        pattern : str
            A pattern where at least one row is wider than the specified width.

        """
        with pytest.raises(ValueError, match="Number of cells is larger than specified pattern width"):
            _ = Pattern(width=4, height=3, encoded_pattern=pattern)
