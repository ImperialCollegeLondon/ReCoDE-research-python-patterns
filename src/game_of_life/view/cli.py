from typing import TYPE_CHECKING, Any, ClassVar, Self, override

import numpy as np
from rich.console import Console
from rich.live import Live
from rich.panel import Panel

from game_of_life.view.base import BaseView

if TYPE_CHECKING:
    from game_of_life.model import GameOfLife


class CliView(BaseView):
    """
    View interface for displaying in the command line
    """

    ALIVE_CELL: ClassVar[str] = "\u2588"  # Unicode for full block █
    DEAD_CELL: ClassVar[str] = " "

    def __init__(self, refresh_per_second: int) -> None:
        super().__init__()
        self.console: Console = Console()
        self.live_display: Live = Live(console=self.console, refresh_per_second=refresh_per_second, screen=True)

    def map_to_string(self, arr: np.ndarray) -> str:
        assert arr.ndim == 2
        chars = np.where(arr == 1, self.ALIVE_CELL, self.DEAD_CELL)
        return "\n".join("".join(row) for row in chars)

    @override
    def __enter__(self) -> Self:
        self.console.print("[bold cyan]Conway's Game of Life[/bold cyan]")
        self.console.print("[dim]Press Ctrl+C to stop[/dim]\n")
        self.live_display.start()
        return self

    @override
    def render(self, game: "GameOfLife") -> None:
        # Render the game board
        board = self.map_to_string(game.grid)
        # Create a panel with the current state
        panel = Panel(board, title=f"[bold]Generation {game.generation}[/bold]", border_style="green")
        self.live_display.update(panel)

    @override
    def __exit__(self, *exc_details: Any) -> None:
        self.console.print("\n[yellow]Game stopped.[/yellow]")
        self.live_display.stop()
