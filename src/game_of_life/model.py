import re
from typing import Any, ClassVar, Final, Protocol, Self, TypedDict, Unpack, runtime_checkable

import numpy as np
import numpy.typing as npt
from pydantic import BaseModel, PositiveInt, field_validator, model_validator

NDArrayInt = npt.NDArray[np.uint8]


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

        core_pattern = r"^(\d*[bo$])*$"
        if re.match(core_pattern, without_end) is None:
            raise ValueError("Pattern contains invalid characters or structure")

        # Check that all numbers are > 0
        pattern_for_counts = r"(\d+)([bo$])"
        for match in re.finditer(pattern_for_counts, without_end):
            if int(match.group(1)) == 0:
                raise ValueError("Run count cannot be 0 at {match.start()}")

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

    def populate_grid(self, row_offset: int, col_offset: int, grid: NDArrayInt) -> NDArrayInt:
        row_index: int = row_offset
        for row_pattern in self.encoded_pattern.split("$"):
            col_index: int = col_offset
            for match_in_row in re.finditer(r"(\d*)([bo])", row_pattern):
                if match_in_row.group(1).isdecimal():
                    num_to_set: int = int(match_in_row.group(1))
                else:
                    num_to_set: int = 1
                is_alive: bool = match_in_row.group(2) == "o"
                if is_alive:
                    if num_to_set > 1:
                        grid[row_index, col_index : col_index + num_to_set] = 1
                    else:
                        grid[row_index, col_index] = 1
                col_index += num_to_set
            row_index += 1
        return grid


@runtime_checkable
class GridInitialiser(Protocol):
    def __call__(self, n_rows: int, n_cols: int, **kwargs: Any) -> NDArrayInt: ...  # noqa: ANN401


class NoKwargs(TypedDict): ...


def _zeros_initialiser(n_rows: int, n_cols: int, **kwargs: Unpack[NoKwargs]) -> NDArrayInt:  # noqa: ARG001
    return np.zeros((n_rows, n_cols), dtype=np.uint8)


zeros_initialiser: Final[GridInitialiser] = _zeros_initialiser


class RandomInitKwargs(TypedDict, total=False):
    density: float


def _random_initialiser(n_rows: int, n_cols: int, **kwargs: Unpack[RandomInitKwargs]) -> NDArrayInt:
    density: float = kwargs.get("density", 0.2)
    return np.random.default_rng().choice([0, 1], size=(n_rows, n_cols), p=np.asarray([1 - density, density]))


random_initialiser: Final[GridInitialiser] = _random_initialiser


class PatternKwargs(TypedDict):
    pattern: Pattern
    row_offset: int
    col_offset: int


def _initialise_with_pattern(n_rows: int, n_cols: int, **kwargs: Unpack[PatternKwargs]) -> NDArrayInt:
    pattern: Pattern = kwargs["pattern"]
    if pattern.width > n_cols or pattern.height > n_rows:
        raise ValueError("Pattern is larger than grid")

    row_offset: int = kwargs["row_offset"]
    col_offset: int = kwargs["col_offset"]

    if row_offset + pattern.height > n_rows:
        raise ValueError("Pattern with row offset exceeds grid bounds by {row_offset + pattern.height - n_rows}")
    if col_offset + pattern.width > n_cols:
        raise ValueError("Pattern with col offset exceeds grid bounds by {col_offset + pattern.width - n_cols}")

    grid: NDArrayInt = np.zeros((n_rows, n_cols), dtype=np.uint8)

    return pattern.populate_grid(row_offset, col_offset, grid)


pattern_initialiser: Final[GridInitialiser] = _initialise_with_pattern


class Grid:
    N_BIRTH: ClassVar[int] = 3
    N_SURVIVAL: ClassVar[int] = 2  # assumes that N_BIRTH is also a survival

    def __init__(
        self,
        n_rows: int = 50,
        n_cols: int = 50,
        wrap: bool = True,
        grid_init_callback: GridInitialiser = zeros_initialiser,
        callback_kwargs: dict[str, Any] | None = None,
    ) -> None:
        self.n_rows: int = n_rows
        self.n_cols: int = n_cols
        self.wrap: bool = wrap
        self._generation: int = 0
        self._grid: NDArrayInt = grid_init_callback(
            n_rows, n_cols, **(callback_kwargs if callback_kwargs is not None else {})
        )
        self._history: list[NDArrayInt] = [self._grid]

    def population(self) -> int:
        return int(self._grid.sum())

    @property
    def grid(self) -> NDArrayInt:
        return self._grid

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def history(self) -> NDArrayInt:
        return np.dstack(self._history)

    def all_grid_history(self) -> NDArrayInt | None:
        if self._history is not None:
            return np.dstack(self._history)
        return self._history

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
