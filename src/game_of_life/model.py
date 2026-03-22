from typing import ClassVar

import numpy as np
import numpy.typing as npt

NDArrayInt = npt.NDArray[np.uint8]


class Grid:
    N_BIRTH: ClassVar[int] = 3
    N_SURVIVAL: ClassVar[int] = 2  # assumes that N_BIRTH is also a survival

    def __init__(self, n_rows: int = 50, n_cols: int = 50, wrap: bool = True, store_history: bool = False) -> None:
        self.n_rows: int = n_rows
        self.n_cols: int = n_cols
        self.wrap: bool = wrap
        self._generation: int = 0
        self._grid: NDArrayInt = np.zeros((n_rows, n_cols), dtype=np.uint8)
        self._history: list[NDArrayInt] | None = [self._grid] if store_history else None

    def population(self) -> int:
        return int(self._grid.sum())

    @property
    def grid(self) -> NDArrayInt:
        return self._grid

    @property
    def generation(self) -> int:
        return self._generation

    def all_grid_history(self) -> NDArrayInt | None:
        if self._history is not None:
            return np.dstack(self._history)
        return self._history

    def randomise(self, density: float = 0.2) -> None:
        assert self.generation == 0, "Grid can only be randomised at the start"
        self._grid = np.random.default_rng().choice(
            [0, 1], size=(self.n_rows, self.n_cols), p=np.asarray([1 - density, density])
        )
        if self._history is not None:
            self._history[0] = self._grid

    def compute_next_generation(self) -> NDArrayInt:
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

        return next_generation

    def step(self) -> None:
        self._generation += 1
        self._grid = self.compute_next_generation()
        if self._history is not None:
            self._history.append(self._grid)
