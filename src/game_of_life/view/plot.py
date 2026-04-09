from typing import TYPE_CHECKING, override

from game_of_life.view.base import BaseView

if TYPE_CHECKING:
    from game_of_life.model import GameOfLife


class PlotView(BaseView):
    def __init__(self) -> None:
        super().__init__()

    @override
    def setup(self) -> None: ...

    @override
    def render(self, game: "GameOfLife") -> None: ...

    @override
    def teardown(self) -> None: ...
