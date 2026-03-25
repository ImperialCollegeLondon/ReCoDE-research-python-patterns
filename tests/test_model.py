import numpy as np
import pytest

from game_of_life.model import Grid, Pattern, PatternGridCreator, RandomGridCreator


class TestGrid:
    default_n_rows: int = 50
    default_n_cols: int = 50
    four_cells: Pattern = Pattern(width=4, height=1, encoded_pattern="4o!")
    t_tetromino: Pattern = Pattern(width=3, height=2, encoded_pattern="bo$3o!")

    def test_default_grid_dimensions(self) -> None:
        grid = Grid()
        assert grid.grid.shape == (self.default_n_rows, self.default_n_cols)
        assert grid.population() == 0

    def test_custom_grid_dimensions(self) -> None:
        custom_size: int = 10
        grid = Grid(n_rows=custom_size, n_cols=custom_size)
        assert grid.grid.shape == (custom_size, custom_size)
        assert grid.population() == 0

    def test_randomise_grid_sparse(self) -> None:
        grid = Grid(grid_creator=RandomGridCreator(density=0.1))
        assert grid.population() != 0
        num_cells: int = self.default_n_rows * self.default_n_cols
        assert (0.05 * num_cells) < grid.population() < (0.15 * num_cells)

    def test_randomise_grid_no_density(self) -> None:
        grid = Grid(grid_creator=RandomGridCreator())
        assert grid.population() != 0
        num_cells: int = self.default_n_rows * self.default_n_cols
        assert (0.1 * num_cells) < grid.population() < (0.25 * num_cells)

    def test_randomise_grid_filled(self) -> None:
        grid = Grid(grid_creator=RandomGridCreator(density=1))
        assert grid.population() != 0
        num_cells: int = self.default_n_rows * self.default_n_cols
        assert num_cells == grid.population()

    def test_step_empty_grid(self) -> None:
        grid = Grid()
        assert grid.population() == 0
        grid.step()
        assert grid.population() == 0

    @pytest.mark.parametrize("rng_seed", [1, 53, 100, 344, 1234576])
    def test_step_non_empty_grid_increase(self, rng_seed: int) -> None:
        grid = Grid(grid_creator=RandomGridCreator(density=0.3, rng_seed=rng_seed))
        original_count: int = grid.population()
        grid.step()
        assert grid.population() > original_count

    @pytest.mark.parametrize("seed", [1, 53, 100, 344, 1234576])
    def test_step_non_empty_grid_decrease(self, seed: int) -> None:
        grid = Grid(grid_creator=RandomGridCreator(density=0.7, rng_seed=seed))
        original_count: int = grid.population()
        grid.step()
        assert grid.population() < original_count

    def test_initialise_with_pattern_zero_offset(self) -> None:
        grid = Grid(grid_creator=PatternGridCreator(self.four_cells))
        num_in_pattern: int = 4
        assert grid.population() == num_in_pattern
        np.testing.assert_array_equal(grid.grid[0, 0:4], np.ones((4), dtype=np.uint8))

    @pytest.mark.parametrize(("col_offset", "row_offset"), [(1, 1), (5, 7), (45, 45)])
    def test_initialise_with_pattern_with_offset(self, col_offset: int, row_offset: int) -> None:
        grid = Grid(grid_creator=PatternGridCreator(self.four_cells, col_offset=col_offset, row_offset=row_offset))
        assert grid.population() == 4
        np.testing.assert_array_equal(
            grid.grid[0 + row_offset, 0 + col_offset : 4 + col_offset], np.ones((4), dtype=np.uint8)
        )

    def test_step_four_cell_pattern(self) -> None:
        grid = Grid(grid_creator=PatternGridCreator(self.four_cells, col_offset=1, row_offset=1))
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
        grid = Grid(grid_creator=PatternGridCreator(self.four_cells))
        assert grid.generation == 0
        np.testing.assert_array_equal(grid.grid[0, 0:4], np.ones((4), dtype=np.uint8))
        grid.step()
        np.testing.assert_array_equal(np.nonzero(grid.grid)[0], np.asarray([0, 0, 1, 1, 49, 49]))
        np.testing.assert_array_equal(np.nonzero(grid.grid)[1], np.asarray([1, 2, 1, 2, 1, 2]))

    def test_step_four_cell_pattern_no_wrap(self) -> None:
        grid = Grid(grid_creator=PatternGridCreator(self.four_cells), wrap=False)
        assert grid.generation == 0
        np.testing.assert_array_equal(grid.grid[0, 0:4], np.ones((4), dtype=np.uint8))
        grid.step()
        np.testing.assert_array_equal(np.nonzero(grid.grid)[0], np.asarray([1, 1]))
        np.testing.assert_array_equal(np.nonzero(grid.grid)[1], np.asarray([1, 2]))

    def test_t_tetromino_init(self) -> None:
        grid = Grid(grid_creator=PatternGridCreator(self.t_tetromino, col_offset=25, row_offset=25))
        starting_population: int = 4
        assert grid.population() == starting_population
        np.testing.assert_array_equal(np.nonzero(grid.grid)[0], np.asarray([25, 26, 26, 26]))
        np.testing.assert_array_equal(np.nonzero(grid.grid)[1], np.asarray([26, 25, 26, 27]))

    def test_t_tetromino_grid_too_small(self) -> None:
        with pytest.raises(ValueError, match="Pattern is larger than grid"):
            _ = Grid(
                grid_creator=PatternGridCreator(self.t_tetromino, col_offset=25, row_offset=25), n_rows=1, n_cols=2
            )

    @pytest.mark.parametrize(("col_offset", "row_offset"), [(1, 60), (60, 7), (60, 60)])
    def test_pattern_outside_grid(self, col_offset: int, row_offset: int) -> None:
        with pytest.raises(ValueError, match=r".*offset exceeds grid bounds by.*"):
            _ = Grid(grid_creator=PatternGridCreator(self.four_cells, col_offset=col_offset, row_offset=row_offset))


class TestPatternValidation:
    def test_valid_light_weight_spaceship(self) -> None:
        _ = Pattern(width=5, height=4, encoded_pattern="o2bo$4bo$o3bo$b4o!")

    def test_valid_gosper_glider_gun(self) -> None:
        _ = Pattern(
            width=36,
            height=16,
            encoded_pattern="27bo$26bobo$9b2o15b2obo4b2o$9bobo14b2ob2o3b2o$2o2b2o6bo13b2obo$2obo2bo2bo2bo13bobo$4b2o6bo8bo5bo$9bobo7bobo$9b2o9b2o5$28bo$29bo$27b3o!",
        )

    def test_empty_string(self) -> None:
        with pytest.raises(ValueError, match="Pattern string cannot be empty"):
            _ = Pattern(width=5, height=4, encoded_pattern="")

    def test_no_end_of_pattern(self) -> None:
        with pytest.raises(ValueError, match="Pattern string must end with an '!'"):
            _ = Pattern(width=5, height=4, encoded_pattern="o2bo$4bo$o3bo$b4o")

    def test_only_end_of_pattern_pass(self) -> None:
        _ = Pattern(width=5, height=1, encoded_pattern="!")

    def test_only_end_of_pattern_fails(self) -> None:
        with pytest.raises(ValueError, match="Number of new lines does not match specified pattern height"):
            _ = Pattern(width=5, height=4, encoded_pattern="!")

    @pytest.mark.parametrize("pattern", ["o2kbo$4bo$o3bo$b4o!", "o2bo$4bio$o3bo$b4o!", "o2bo$4bo$o3$9999i$bo$b4o!"])
    def test_invalid_character_or_structure(self, pattern: str) -> None:
        with pytest.raises(ValueError, match="Pattern contains invalid characters or structure"):
            _ = Pattern(width=5, height=4, encoded_pattern=pattern)

    @pytest.mark.parametrize("pattern", ["o0bo$4bo$o3bo$b4o!", "o2bo$4b0o$o3bo$b4o!", "o2bo0$4bo$o3bo$b4o!"])
    def test_count_starts_with_zero(self, pattern: str) -> None:
        with pytest.raises(ValueError, match="Run count cannot be 0 at"):
            _ = Pattern(width=5, height=4, encoded_pattern=pattern)

    @pytest.mark.parametrize("pattern", ["$$$$!", "b$b$b$b$!", "4$!", "$!", "b$!", "2$!", "bo$5$!"])
    def test_num_rows_no_match_height(self, pattern: str) -> None:
        with pytest.raises(ValueError, match="Number of new lines does not match specified pattern height"):
            _ = Pattern(width=5, height=4, encoded_pattern=pattern)
