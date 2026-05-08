"""Matplotlib-based visualization for Game of Life.

This module provides visualization and animation export capabilities for Game of Life
simulations using matplotlib. It can display animations interactively or save them to
files (MP4, GIF, etc.). This view is suitable for analyzing simulation dynamics and
creating shareable animations.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Self, override

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
    """Matplotlib-based view for visualizing and exporting Game of Life simulations.

    This class uses matplotlib to create an animated visualization of the Game of Life
    simulation. It can display the animation interactively on screen or save it to a
    file (e.g., MP4, GIF). Each frame in the animation represents a generation of
    the simulation.

    The visualization uses a simple color scheme where white represents dead cells
    and black represents live cells. Frames are collected during rendering and
    combined into an animation when exiting the context manager.

    Attributes
    ----------
    INTERVAL : int
        The time interval (in milliseconds) between frames in the animation.
        Default is 100ms (10 frames per second).
    output_path : Path | None
        File path where the animation will be saved. If None, the animation
        is displayed interactively instead of being saved.
    fig : Figure
        The matplotlib Figure object containing the plot.
    ax : Axes
        The matplotlib Axes object where the grid is displayed.
    _cmap : ListedColormap
        The color map used for rendering: white for dead cells, black for live cells.
    _frame_artists : list[list[AxesImage | Text]]
        Storage for all frame artists (images and text) collected during rendering.

    Parameters
    ----------
    output_path : Path | None, optional
        Path where the animation will be saved. If None (default), the animation
        is displayed interactively using matplotlib's default viewer.
        File format is determined by the extension (e.g., '.mp4', '.gif').

    Examples
    --------
    Display animation on screen:

    >>> from pathlib import Path
    >>> from game_of_life.model import GameOfLife, RandomGridCreator
    >>> game = GameOfLife(grid_creator=RandomGridCreator())
    >>> view = PlotView()  # Display on screen
    >>> with view:
    ...     for _ in range(100):
    ...         view.render(game)
    ...         game.step()

    Save animation to file:

    >>> view = PlotView(output_path=Path("game_of_life.gif"))  # Save to file
    >>> with view:
    ...     for _ in range(100):
    ...         view.render(game)
    ...         game.step()

    """

    INTERVAL: ClassVar[int] = 100
    output_path: Path | None
    fig: "Figure"
    ax: "Axes"
    _cmap: ListedColormap
    _frame_artists: list[list["AxesImage | Text"]]

    def __init__(self, output_path: Path | None = None) -> None:
        """Initialize the PlotView.

        Sets up the matplotlib figure and axes, and initializes the color map
        for visualization.

        Parameters
        ----------
        output_path : Path | None, optional
            Path where the animation will be saved. If None (default), the
            animation is displayed interactively.

        Returns
        -------
        None

        """
        super().__init__()
        self.output_path = output_path
        self._cmap = ListedColormap(["white", "black"])
        self.fig, self.ax = plt.subplots(constrained_layout=True)
        self._frame_artists = []

    @override
    def __enter__(self) -> Self:
        """Enter the context manager for the PlotView.

        Sets up the figure title and disables axis ticks for a cleaner visualization.
        Should be used with a `with` statement.

        Returns
        -------
        Self
            Returns the instance itself to be used in the with block.

        Examples
        --------
        >>> view = PlotView()
        >>> with view:  # __enter__ is called here
        ...     # view is ready to use
        ...     pass

        """
        _ = self.fig.suptitle("Game of Life")

        # Disable axis ticks
        _ = self.ax.set_xticks([])
        _ = self.ax.set_yticks([])
        return self

    @override
    def render(self, game: "GameOfLife") -> None:
        """Render and store a frame of the current game state.

        This method creates an image from the current game grid and stores it as
        a frame for later animation. Multiple calls build up an animation sequence.

        Parameters
        ----------
        game : GameOfLife
            The Game of Life instance with the current board state to render.

        Returns
        -------
        None

        """
        self._frame_artists.append([self.ax.imshow(game.grid, cmap=self._cmap, interpolation="nearest")])

    @override
    def __exit__(self, *exc_details: Any) -> None:
        """Exit magic method for plotting context manager.

        This method is called when exiting a `with` block. It combines all collected
        frames into an animation and either displays it on screen or saves it to file,
        depending on whether output_path was provided.

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
