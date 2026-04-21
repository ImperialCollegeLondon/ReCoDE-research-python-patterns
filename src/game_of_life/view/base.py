"""Base view interface for Game of Life visualization.

This module defines the abstract base class that all view implementations must inherit from.
Views are responsible for displaying the current state of the Game of Life simulation
to the user through various output methods (e.g. terminal, etc.).
"""

from abc import abstractmethod
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game_of_life.model import GameOfLife


class BaseView(AbstractContextManager):
    """Abstract base class for all Game of Life visualization views.

    This class defines the interface that all concrete view implementations must follow.
    By inheriting from AbstractContextManager, it enforces that concrete implementations
    provide context manager capabilities (the `with` statement support). This allows
    views to manage resources like file handles, displays, or animations properly.

    A view is responsible for displaying the current state of the Game of Life simulation.
    Different views can display the game in different ways (e.g., terminal, plot, web).

    Notes
    -----
    Concrete child classes must implement the following methods:
        1. __enter__(self) -> Self : Called when entering a with block
        2. __exit__(self, exc_type, exc_val, exc_tb) -> None : Called when exiting a with block
        3. render(self, game) -> None : Display the current game state

    Examples
    --------
    Usage of a view class (concrete implementation):

    >>> # This is how a view would be used (example with CliView)
    >>> from game_of_life.model import GameOfLife
    >>> game = GameOfLife(n_rows=10, n_cols=10)
    >>> # view would be an instance of a concrete class like CliView
    >>> # with view:
    >>> #     view.render(game)

    """

    @abstractmethod
    def render(self, game: "GameOfLife") -> None:
        """Display the current state of the Game of Life simulation.

        This abstract method must be implemented by concrete view classes to
        determine how to visualize the game board and other information.

        Parameters
        ----------
        game : GameOfLife
            The Game of Life instance containing the current grid state and
            generation information to be rendered.

        Returns
        -------
        None

        """
        ...
