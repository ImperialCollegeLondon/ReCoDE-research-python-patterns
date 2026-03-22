from game_of_life.model import Grid


class TestGrid:
    default_n_rows: int = 50
    default_n_cols: int = 50

    def test_default_grid_dimensions(self) -> None:
        grid = Grid()
        assert grid.n_rows == self.default_n_rows
        assert grid.n_cols == self.default_n_cols
        assert grid.population() == 0

    def test_custom_grid_dimensions(self) -> None:
        custom_size: int = 10
        grid = Grid(n_rows=custom_size, n_cols=custom_size)
        assert grid.n_rows == custom_size
        assert grid.n_cols == custom_size
        assert grid.population() == 0

    def test_randomise_grid(self) -> None:
        grid = Grid()
        assert grid.population() == 0
        grid.randomise()
        num_cells: int = self.default_n_rows * self.default_n_cols
        assert (0.1 * num_cells) < grid.population() < (0.25 * num_cells)

    def test_randomise_grid_filled(self) -> None:
        grid = Grid()
        assert grid.population() == 0
        grid.randomise(density=1)
        num_cells: int = self.default_n_rows * self.default_n_cols
        assert num_cells == grid.population()

    def test_step_empty_grid(self) -> None:
        grid = Grid()
        assert grid.population() == 0
        grid.step()
        assert grid.population() == 0

    def test_step_non_empty_grid_increase(self) -> None:
        grid = Grid()
        grid.randomise(density=0.3)
        original_count: int = grid.population()
        grid.step()
        assert grid.population() > original_count

    def test_step_non_empty_grid_decrease(self) -> None:
        grid = Grid()
        grid.randomise(density=0.7)
        original_count: int = grid.population()
        grid.step()
        assert grid.population() < original_count
