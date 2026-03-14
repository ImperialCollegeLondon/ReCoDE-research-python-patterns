from typing import ClassVar

import numpy as np
import numpy.typing as npt

NDArrayInt = npt.NDArray[np.int_]


class Grid:
    N_BIRTH: ClassVar[int] = 3
    N_SURVIVAL: ClassVar[int] = 2  # assumes that N_BIRTH is also a survival

    def __init__(self, grid_size: int = 50, wrap: bool = True) -> None:
        self.grid_size: int = grid_size
        self.wrap: bool = wrap
        self._grid: NDArrayInt = np.zeros((grid_size, grid_size), dtype=int)

    def population(self) -> int:
        return int(self._grid.sum())

    def randomise(self, density: float = 0.2) -> None:
        self._grid = np.random.default_rng().choice(
            [0, 1], size=(self.grid_size, self.grid_size), p=np.asarray([1 - density, density])
        )

    def step(self) -> None:
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
        # 3 neighbours => always alive
        # 2 neighbours => must be alive to remain alive
        next_generation = np.where(
            (neighbours == self.N_BIRTH) | ((self._grid == 1) & (neighbours == self.N_SURVIVAL)), 1, 0
        )

        if not self.wrap:
            next_generation[0, :] = 0
            next_generation[-1, :] = 0
            next_generation[:, 0] = 0
            next_generation[:, -1] = 0

        self._grid = next_generation


class GameOfLife:
    def __init__(self, grid: Grid) -> None:
        self.generation: int = 0
        self.grid: Grid = grid

    @property
    def population(self) -> int:
        return self.grid.population()

    def step(self) -> None:
        self.grid.step()
        self.generation += 1
