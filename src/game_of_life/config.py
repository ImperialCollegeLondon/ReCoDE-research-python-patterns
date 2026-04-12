"""
Module for everything related to configuring how the game of life executes
"""

from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, Self

import yaml
from pydantic import BaseModel, DirectoryPath, Field, NonNegativeFloat, PositiveInt

from game_of_life.model import Pattern

# pydantic.Field(): Performs additional validation on the input. Here, it enforces that it must be <=1
Proportion = Annotated[NonNegativeFloat, Field(le=1)]


if TYPE_CHECKING:
    from collections.abc import Hashable
    from pathlib import Path


class GridInitialiser(StrEnum):
    ZEROS = "zeros"
    RANDOM = "random"
    PATTERN = "pattern"


class FromYaml(BaseModel):
    @classmethod
    def from_yaml(cls, path: "Path") -> Self:
        if path.is_file():
            data: dict[Hashable, Any] = {}
            with path.open(mode="r") as f:
                data = yaml.safe_load(f)

            # raises ValidationError if it fails
            return cls.model_validate(data)
        raise ValueError("Configuration file not found or is not a file.")


class GameOfLifeConfigFrom(FromYaml):
    num_rows: Annotated[PositiveInt, Field(description="Number of rows in game of life grid")] = 50
    num_cols: Annotated[PositiveInt, Field(description="Number of cols in game of life grid")] = 50
    grid_initialiser: GridInitialiser = GridInitialiser.ZEROS
    density: Annotated[Proportion | None, Field(description="Density of cells in game of life grid")] = None
    pattern: Annotated[Pattern | None, Field(description="Pattern to initialise grid with")] = None


class DisplayInterface(StrEnum):
    CLI = "cli"
    PLOT = "plot"


class CLIViewConfig(BaseModel):
    speed: float


class PlotViewConfig(BaseModel):
    output_dir: DirectoryPath
    output_filename: str


class RunConfig(FromYaml):
    interface: DisplayInterface
    view_config: CLIViewConfig | PlotViewConfig
    gol_config: GameOfLifeConfigFrom
