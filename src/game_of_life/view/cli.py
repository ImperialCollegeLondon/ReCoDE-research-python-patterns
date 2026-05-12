"""Command-line interface view for Game of Life.

This module provides a terminal-based visualization of the Game of Life simulation
using the rich library for formatted text output. The CLI view displays the game board
in real-time with live updates, showing the current generation and board state.
"""

import time
from typing import TYPE_CHECKING, Any, ClassVar, Self, override

import numpy as np
from rich.console import Console
from rich.live import Live
from rich.panel import Panel

from game_of_life.view.base import BaseView

if TYPE_CHECKING:
    from game_of_life.model import GameOfLife


class CliView(BaseView):
    """Terminal-based view for displaying the Game of Life simulation.

    This class renders the Game of Life board in the terminal (command-line interface)
    using `rich` formatting. It displays the game board with live cell updates in
    real-time and shows the current generation.

    Live cells are displayed as full block characters (█), and dead cells as spaces.
    The display is updated in real-time without clearing the previous output.

    Attributes
    ----------
    ALIVE_CELL : str
        The Unicode character used to represent live cells (█).
        This is a class variable shared across all instances.
    DEAD_CELL : str
        The character used to represent dead cells (space).
        This is a class variable shared across all instances.
    console : Console
        A `rich.Console` object used for rich text formatting and output.
    live_display : Live
        A `rich.Live` object that manages live-updating displays.

    Parameters
    ----------
    refresh_per_second : int
        The number of times per second the display should refresh.
        Higher values mean smoother updates but require more CPU resources.

    Examples
    --------
    >>> from game_of_life.model import GameOfLife, RandomGridCreator
    >>> game = GameOfLife(grid_creator=RandomGridCreator())
    >>> view = CliView(refresh_per_second=10)
    >>> with view:
    ...     for _ in range(100):
    ...         view.render(game)
    ...         game.step()
    Conway's Game of Life
    Press Ctrl+C to stop
    <BLANKLINE>
    <BLANKLINE>
    Game stopped.

    """

    ALIVE_CELL: ClassVar[str] = "\u2588"  # Unicode for full block █
    DEAD_CELL: ClassVar[str] = " "

    def __init__(self, time_between_generations: float) -> None:
        """Initialize the CLI view.

        Parameters
        ----------
        refresh_per_second : int
            The number of times per second to refresh the display.
            Recommended values are between 1 and 30 depending on performance.

        Returns
        -------
        None

        """
        super().__init__()
        self.console: Console = Console()
        # When time between generations is < 1, +1 is to guarantee that refresh rate is higher than frequency of data
        # Otherwise, it can refresh twice a second and still be faster than the refresh rate
        refresh_per_second: int = int(np.ceil(1 / time_between_generations)) + 1 if time_between_generations < 1 else 2
        self.live_display: Live = Live(console=self.console, refresh_per_second=refresh_per_second, screen=True)
        self._time_between_gens: float = time_between_generations

    def map_to_string(self, arr: np.ndarray) -> str:
        r"""Convert a 2D numpy array to a string representation.

        This method transforms the numeric grid (where 1 represents live cells and
        0 represents dead cells) into a visual string format using Unicode characters.
        Each row becomes a line in the output string.

        Parameters
        ----------
        arr : np.ndarray
            A 2D numpy array where 1 represents live cells and 0 represents dead cells.
            The array must have exactly 2 dimensions (rows and columns).

        Returns
        -------
        str
            A string representation of the grid where each line corresponds to a row
            in the array. Live cells (1) are shown as █ and dead cells (0) as spaces.

        Examples
        --------
        >>> import numpy as np
        >>> view = CliView(refresh_per_second=10)
        >>> grid = np.array([[1, 0], [0, 1]], dtype=np.uint8)
        >>> view.map_to_string(grid)
        '█ \n █'
        >>> print(view.map_to_string(grid))
        █
         █

        """
        assert arr.ndim == 2
        if arr.ndim != 2:
            raise ValueError("Array must have two dimensions")
        chars = np.where(arr == 1, self.ALIVE_CELL, self.DEAD_CELL)
        return "\n".join("".join(row) for row in chars)

    @override
    def __enter__(self) -> Self:
        """Enter the context manager for the CLI view.

        This method is called when entering a `with` block. It initializes the display,
        prints a title and instructions, and starts the live update mechanism.

        Returns
        -------
        Self
            Returns the instance itself to be used in the with block.

        """
        self.console.print("[bold cyan]Conway's Game of Life[/bold cyan]")
        self.console.print("[dim]Press Ctrl+C to stop[/dim]\n")
        time.sleep(1)
        self.live_display.start()
        return self

    @override
    def render(self, game: "GameOfLife") -> None:
        """Render the current game state in the terminal.

        This method displays the current game board in a formatted panel with the
        current generation number as the title.

        Parameters
        ----------
        game : GameOfLife
            The Game of Life instance with the current board state to render.

        Returns
        -------
        None

        """
        # Render the game board
        board = self.map_to_string(game.grid)
        # Create a panel with the current state
        panel = Panel(
            board,
            title=f"[bold cyan]Conway's Game of Life[/bold cyan] [bold]Generation {game.generation}[/bold]",
            subtitle="[dim]Press Ctrl+C to stop[/dim]",
            border_style="green",
        )
        self.live_display.update(panel)
        time.sleep(self._time_between_gens)

    @override
    def __exit__(self, *exc_details: Any) -> None:
        """Exit magic method for CLI context manager.

        This method is called when exiting a `with` block. It cleans up resources
        by stopping the live display and printing a final message.

        Parameters
        ----------
        *exc_details : Any
            Exception information if an exception occurred. Contains:
            - exc_type: The exception type or None
            - exc_val: The exception value or None
            - exc_tb: The traceback or None

        Returns
        -------
        None

        """
        self.console.print("\n[yellow]Game stopped.[/yellow]")
        self.live_display.stop()
