from game_of_life.model import Grid


class TestGrid:
    default_grid_size: int = 50

    def test_default_grid_dimensions(self) -> None:
        grid = Grid()
        assert grid.grid_size == self.default_grid_size
        assert grid.population() == 0

    def test_custom_grid_dimensions(self) -> None:
        custom_size: int = 10
        grid = Grid(grid_size=custom_size)
        assert grid.grid_size == custom_size
        assert grid.population() == 0

    def test_randomise_grid(self) -> None:
        grid = Grid()
        assert grid.population() == 0
        grid.randomise()
        num_cells: int = self.default_grid_size * self.default_grid_size
        assert (0.1 * num_cells) < grid.population() < (0.25 * num_cells)

    def test_randomise_grid_filled(self) -> None:
        grid = Grid()
        assert grid.population() == 0
        grid.randomise(density=1)
        num_cells: int = self.default_grid_size * self.default_grid_size
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
