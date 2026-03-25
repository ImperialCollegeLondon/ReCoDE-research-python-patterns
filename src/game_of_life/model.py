import re
from typing import Any, ClassVar, Final, NotRequired, Protocol, Self, TypedDict, Unpack, runtime_checkable

import numpy as np
import numpy.typing as npt
from pydantic import BaseModel, PositiveInt, field_validator, model_validator

NDArrayU8 = npt.NDArray[np.uint8]


class Pattern(BaseModel):
    width: PositiveInt
    height: PositiveInt
    encoded_pattern: str

    @field_validator("encoded_pattern", mode="after")
    @classmethod
    def validate_pattern_string(cls, pattern_str: str) -> str:
        if len(pattern_str) < 1:
            raise ValueError("Pattern string cannot be empty")

        if not pattern_str.endswith("!"):
            raise ValueError("Pattern string must end with an '!'")

        without_end: str = pattern_str[:-1]

        # Regex pattern which checks that are no invalid characters and that it matches the structure of specifying
        # the lines then the new line
        #   ^ - Start of string anchor, i.e. match must begin here
        #       (\d*[bo$])* - Zero or more occurrences of:
        #           \d* - Zero or more digits
        #           [bo$] - Followed by exactly one character that is either b, o, or $
        #   $ - End of string anchor, i.e. match must end here
        valid_character_pattern = r"^(\d*[bo$])*$"
        if re.match(valid_character_pattern, without_end) is None:
            raise ValueError("Pattern contains invalid characters or structure")

        # Check that all numbers are > 0
        #   Pattern contains two groups: 1) any digits (\d+), 2) token characters b, o or $ ([bo$])
        #   Thus, group 1 will contain the count for a given token
        pattern_for_counts = r"(\d+)([bo$])"
        for match in re.finditer(pattern_for_counts, without_end):
            if int(match.group(1)) == 0:
                raise ValueError(f"Run count cannot be 0 at {match.start()}")

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

    def populate_grid(self, row_offset: int, col_offset: int, grid: NDArrayU8) -> NDArrayU8:
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
                num_to_set: int = int(match) if (match := match_in_row.group(1)) else 1

                # else case is where match_in_row.group(2) == "b". Thus, the cell value should be set to 0
                liveness: int = 1 if match_in_row.group(2) == "o" else 0
                if num_to_set > 1:
                    grid[row_index, col_index : col_index + num_to_set] = liveness
                else:
                    grid[row_index, col_index] = liveness

                col_index += num_to_set
            row_index += 1
        return grid


@runtime_checkable
class GridInitialiser(Protocol):
    def __call__(self, n_rows: int, n_cols: int, **kwargs: Any) -> NDArrayU8: ...  # noqa: ANN401


class NoKwargs(TypedDict): ...


def _zeros_initialiser(n_rows: int, n_cols: int, **kwargs: Unpack[NoKwargs]) -> NDArrayU8:  # noqa: ARG001
    return np.zeros((n_rows, n_cols), dtype=np.uint8)


zeros_initialiser: Final[GridInitialiser] = _zeros_initialiser


class RandomInitKwargs(TypedDict):
    density: float
    rng_seed: NotRequired[int]


def _random_initialiser(n_rows: int, n_cols: int, **kwargs: Unpack[RandomInitKwargs]) -> NDArrayU8:
    density: float = kwargs.get("density", 0.2)
    rng_seed: int | None = kwargs.get("rng_seed")
    return np.random.default_rng(seed=rng_seed).choice(
        [0, 1], size=(n_rows, n_cols), p=np.asarray([1 - density, density])
    )


random_initialiser: Final[GridInitialiser] = _random_initialiser


class PatternKwargs(TypedDict):
    pattern: Pattern
    row_offset: int
    col_offset: int


def _initialise_with_pattern(n_rows: int, n_cols: int, **kwargs: Unpack[PatternKwargs]) -> NDArrayU8:
    pattern: Pattern = kwargs["pattern"]
    if pattern.width > n_cols or pattern.height > n_rows:
        raise ValueError("Pattern is larger than grid")

    row_offset: int = kwargs["row_offset"]
    col_offset: int = kwargs["col_offset"]

    if row_offset + pattern.height > n_rows:
        raise ValueError(f"Pattern with row offset exceeds grid bounds by {row_offset + pattern.height - n_rows}")
    if col_offset + pattern.width > n_cols:
        raise ValueError(f"Pattern with col offset exceeds grid bounds by {col_offset + pattern.width - n_cols}")

    grid: NDArrayU8 = np.zeros((n_rows, n_cols), dtype=np.uint8)

    return pattern.populate_grid(row_offset, col_offset, grid)


pattern_initialiser: Final[GridInitialiser] = _initialise_with_pattern


class Grid:
    N_BIRTH: ClassVar[int] = 3
    """Number of live neighbours to make a dead cell come to life or to survive"""
    N_SURVIVAL: ClassVar[int] = 2  # assumes that N_BIRTH is also a survival
    """Number of live neighbours to survive"""

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
        self._grid: NDArrayU8 = grid_init_callback(
            n_rows, n_cols, **(callback_kwargs if callback_kwargs is not None else {})
        )
        self._history: list[NDArrayU8] = [self._grid]

    def population(self) -> int:
        return int(self._grid.sum())

    @property
    def grid(self) -> NDArrayU8:
        return self._grid

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def history(self) -> list[NDArrayU8]:
        return self._history

    def history_3d(self) -> NDArrayU8:
        return np.dstack(self._history)

    def compute_next_generation(self) -> NDArrayU8:
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
        self._generation += 1
        self._grid = self.compute_next_generation()
        self._history.append(self._grid)
