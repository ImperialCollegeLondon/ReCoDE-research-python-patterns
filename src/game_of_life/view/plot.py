from typing import override

from game_of_life.view.base import BaseView


class PlotView(BaseView):
    def __init__(self) -> None:
        super().__init__()

    @override
    def render(self) -> None: ...
