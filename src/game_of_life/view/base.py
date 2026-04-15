from abc import abstractmethod
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game_of_life.model import GameOfLife


class BaseView(AbstractContextManager):
    """
    Interface which all view classes should inherit from.

    By inheriting from AbstractContextManager, it requires that the concrete child classes implement the following
    methods,
      1) __enter__(self) -> Self
      2) __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None
    """

    @abstractmethod
    def render(self, game: "GameOfLife") -> None: ...
