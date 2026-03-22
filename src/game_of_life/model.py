import re
from typing import ClassVar, Self

import numpy as np
import numpy.typing as npt
from pydantic import BaseModel, PositiveInt, field_validator, model_validator

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


class Pattern(BaseModel):
    width: PositiveInt
    height: PositiveInt
    encoded_pattern: str

    @field_validator("encoded_pattern", mode="after")
    @classmethod
    def validate_pattern_string(cls, pattern_str: str) -> str:
        if not pattern_str.endswith("!"):
            raise ValueError("Pattern string must end with an '!'")

        without_end: str = pattern_str[:-1]

        # valid_pattern = re.compile(r"^[\d$bo]*$")
        # if not valid_pattern.match(without_end ):
        #    invalid_chars = "".join(sorted(set(re.findall(r"[^\d$bo]", without_end))))
        #    raise ValueError(f"Invalid characters found: {invalid_chars}")
        core_pattern = r"^(\d*[bo$])*$"
        if re.match(core_pattern, without_end) is None:
            raise ValueError("Pattern contains invalid characters or structure")

        # Check that all numbers are > 0
        pattern_for_counts = r"(\d+)([bo$])"
        for match in re.finditer(pattern_for_counts, without_end):
            if int(match.group(1)) == 0:
                raise ValueError("Run count cannot be 0 at {match.start()}")

        # return pattern_str[:-1]
        return without_end

    @model_validator(mode="after")
    def check_height_matches_pattern(self) -> Self:
        num_new_lines: int = self.height - 1
        if self.encoded_pattern.count("$") != num_new_lines:
            # Matches groups of digits with $. Then, sums the digits to get number of new lines for that group
            new_line_sum: int = sum(
                int(m.group(1)) if m.group(1).isdecimal() else 1
                for m in re.finditer(r"(\d*)(\$)", self.encoded_pattern)
            )
            if new_line_sum != num_new_lines:
                raise ValueError("Number of new lines does not match specified pattern height")
        return self
