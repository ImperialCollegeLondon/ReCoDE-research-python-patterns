from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override

from matplotlib import animation
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap
from rich.progress import track

from game_of_life.view.base import BaseView

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from matplotlib.image import AxesImage
    from matplotlib.text import Text

    from game_of_life.model import GameOfLife


class PlotView(BaseView):
    """
    View interface for displaying/exporting with matplotlib
    """

    INTERVAL: ClassVar[int] = 100
    output_path: Path | None
    fig: "Figure"
    ax: "Axes"
    _cmap: ListedColormap
    _frame_artists: list[list["AxesImage | Text"]]

    def __init__(self, output_path: Path | None = None) -> None:
        super().__init__()
        self.output_path = output_path
        self._cmap = ListedColormap(["white", "black"])
        self.fig, self.ax = plt.subplots(constrained_layout=True)
        self._frame_artists = []

    @override
    def setup(self) -> None:
        _ = self.fig.suptitle("Game of Life")

        # Disable axis ticks
        _ = self.ax.set_xticks([])
        _ = self.ax.set_yticks([])

    @override
    def render(self, game: "GameOfLife") -> None:
        self._frame_artists.append([self.ax.imshow(game.grid, cmap=self._cmap, interpolation="nearest")])

    @override
    def teardown(self) -> None:
        animated = animation.ArtistAnimation(
            self.fig,
            self._frame_artists,
            interval=self.INTERVAL,
            blit=True,
            repeat=True,
        )

        if self.output_path is None:
            plt.show()
        else:
            animated.save(
                self.output_path,
                savefig_kwargs={"bbox_inches": "tight"},
                progress_callback=lambda current, total: track(self._frame_artists, completed=current, total=total),
            )
        plt.close(self.fig)
