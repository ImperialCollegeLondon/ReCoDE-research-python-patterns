"""
Configuration module for the Game of Life simulation.

This module provides configuration classes and enums for setting up and running
the Game of Life simulation. It uses Pydantic for validation, which is a common
pattern for ensuring data integrity in Python applications.

Notes
-----
The module uses Pydantic's validation system to enforce constraints on configuration
values, such as positive integers and proportions between 0 and 1.
"""

from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, Self

import yaml
from pydantic import BaseModel, DirectoryPath, Field, NonNegativeFloat, PositiveInt

from game_of_life.model import Pattern

# pydantic.Field(): Performs additional validation on the input. Here, it enforces that it must be <=1
Proportion = Annotated[NonNegativeFloat, Field(le=1)]
"""Type alias for a proportion value constrained to [0, 1].

A validated type that ensures non-negative floats do not exceed 1.0, useful for
representing probabilities and density values. This is an example of using type
annotations to enhance type safety in Python.

Type
----
Annotated[NonNegativeFloat, Field(le=1)]
    A constrained float type where 0 <= value <= 1.
"""


if TYPE_CHECKING:
    from collections.abc import Hashable
    from pathlib import Path


class GridInitialiser(StrEnum):
    """
    Enumeration of supported grid initialization strategies.

    This enum constrains inputs to a fixed set of valid options. When used with
    Pydantic models, it provides automatic validation ensuring that only valid
    initialization strategies are accepted. This eliminates the need for manual
    validation logic (e.g., manual if-statements or error handling).

    Attributes
    ----------
    ZEROS : str
        Initialize the grid with all cells dead (zeros).
    RANDOM : str
        Initialize the grid with random live and dead cells.
    PATTERN : str
        Initialize the grid with a specific pattern.

    Design Patterns
    ---------------
    Enumeration Pattern: Restricts values to a predefined set, enabling type-safe
        configuration and exhaustive pattern matching.

    Notes
    -----
    StrEnum is a Python 3.11+ feature that provides string-based enums,
    making them both type-safe and JSON/YAML serializable.

    When a field uses GridInitialiser in a Pydantic model, Pydantic automatically
    validates that the input matches one of these enum values. Invalid inputs
    raise a ValidationError, preventing invalid states from entering the system.

    """

    ZEROS = "zeros"
    RANDOM = "random"
    PATTERN = "pattern"


class FromYaml(BaseModel):
    """
    Base class providing YAML loading functionality for configuration classes.

    Notes
    -----
    This class uses Pydantic's BaseModel for automatic validation and serialization.
    """

    @classmethod
    def from_yaml(cls, path: "Path") -> Self:
        """
        Load configuration from a YAML file.

        Parameters
        ----------
        path : Path
            Path to the YAML configuration file.

        Returns
        -------
        Self
            An instance of the configuration class with values from the YAML file.

        Raises
        ------
        ValueError
            If the file does not exist or is not a file.
        pydantic.ValidationError
            If the YAML content fails validation against the class schema.

        Notes
        -----
        Uses `yaml.safe_load()` for security, preventing arbitrary code execution
        from untrusted YAML files.
        """
        if not path.is_file():
            raise ValueError("Configuration file not found or is not a file.")

        # Default mode of open is "r" => read. It is specified here to make it explicit
        with path.open(mode="r", encoding="utf-8") as f:
            data: dict[Hashable, Any] = yaml.safe_load(f)

        # raises ValidationError if it fails
        return cls.model_validate(data)


class GameOfLifeConfigFrom(FromYaml):
    """
    Configuration for Game of Life simulation parameters.

    This class inherits from FromYaml to allow it to be initialized from a YAML file.

    Attributes
    ----------
    num_rows : int
        Number of rows in the game grid. Must be positive. Default is 50.
    num_cols : int
        Number of columns in the game grid. Must be positive. Default is 50.
    grid_initialiser : GridInitialiser
        Strategy for initializing the grid. Default is ZEROS.
    density : Proportion | None
        Density of live cells for random initialization. Must be in [0, 1].
        Only used when grid_initialiser is RANDOM. Default is None.
    pattern : Pattern | None
        Specific pattern to initialize the grid with. Only used when
        grid_initialiser is PATTERN. Default is None.


    """

    num_rows: Annotated[PositiveInt, Field(description="Number of rows in game of life grid")] = 50
    num_cols: Annotated[PositiveInt, Field(description="Number of cols in game of life grid")] = 50
    grid_initialiser: GridInitialiser = GridInitialiser.ZEROS
    density: Annotated[Proportion | None, Field(description="Density of cells in game of life grid")] = None
    pattern: Annotated[Pattern | None, Field(description="Pattern to initialise grid with")] = None


class DisplayInterface(StrEnum):
    """
    Enumeration of supported display/view interfaces.

    This enum constrains inputs to a fixed set of valid display options. When used
    with Pydantic models, it provides automatic validation ensuring that only valid
    interfaces are accepted. This eliminates the need for manual validation logic.

    Attributes
    ----------
    CLI : str
        Command-line interface for displaying the simulation.
    PLOT : str
        Plotting/visualization interface for displaying the simulation.

    Design Patterns
    ---------------
    Enumeration Pattern: Restricts values to a predefined set, enabling type-safe
        configuration and exhaustive pattern matching.

    Notes
    -----
    This demonstrates using enums for creating type-safe, enumerated constants
    that can be easily validated and serialized.

    When a field uses DisplayInterface in a Pydantic model, Pydantic automatically
    validates that the input matches one of these enum values. Invalid inputs
    raise a ValidationError. This is a form of declarative validation - the valid
    values are declared in the enum definition, and Pydantic handles the actual
    validation without requiring manual implementation.

    """

    CLI = "cli"
    PLOT = "plot"


class CLIViewConfig(BaseModel):
    """
    Configuration for command-line interface view.

    Attributes
    ----------
    speed : float
        Rendering speed in generations per second.
    """

    speed: float


class PlotViewConfig(BaseModel):
    """
    Configuration for plotting/visualization view.

    Attributes
    ----------
    output_dir : DirectoryPath
        Directory path where output plots will be saved. Must be a valid directory.
    output_filename : str
        Name of the output file (e.g., 'simulation.png').
    """

    output_dir: DirectoryPath
    output_filename: str


class RunConfig(FromYaml):
    """
    Top-level configuration for running the Game of Life application.

    This class combines the game simulation configuration with the view/display
    configuration, demonstrating composition - combining multiple configuration
    objects into a higher-level configuration.

    Attributes
    ----------
    interface : DisplayInterface
        Type of display interface to use (CLI or PLOT).
    view_config : CLIViewConfig | PlotViewConfig
        Configuration specific to the chosen interface.
    gol_config : GameOfLifeConfigFrom
        Configuration for the Game of Life simulation parameters.

    Design Patterns
    ---------------
    Composition: Combines multiple configuration objects (view_config and gol_config)
        into a single, unified configuration object.

    Notes
    -----
    The type of view_config depends on the interface selection. Pydantic's
    validation ensures consistency between interface and view_config types.
    """

    interface: DisplayInterface
    view_config: CLIViewConfig | PlotViewConfig
    gol_config: GameOfLifeConfigFrom
