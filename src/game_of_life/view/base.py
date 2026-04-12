from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game_of_life.model import GameOfLife


class BaseView(ABC):
    """
    Interface which all view classes should inherit from.
    """

    @abstractmethod
    def setup(self) -> None: ...
    @abstractmethod
    def render(self, game: "GameOfLife") -> None: ...
    @abstractmethod
    def teardown(self) -> None: ...
