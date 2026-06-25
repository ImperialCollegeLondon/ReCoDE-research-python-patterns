"""Unit tests for the Game of Life view module.

This test module validates the view layer that handles displaying the Game of Life
simulation. It tests CLI view rendering, grid-to-string conversion, and proper
handling of different grid dimensions and cell states.

These tests ensure that visualization output is correct and serve as documentation
on how the view components work.
"""

import itertools
from unittest.mock import Mock

import numpy as np
import pytest

from game_of_life.view.cli import CliView


class TestCLIView:
    """Test suite for the CLI view rendering functionality.

    Tests the CliView class's ability to convert numeric grid arrays to string
    representations and handle various grid configurations and edge cases.
    """

    _print_on_start: str = "Conway's Game of Life\nPress Ctrl+C to stop\n\n"
    _print_on_stop: str = "\nGame stopped.\n"

    @pytest.fixture
    def view_instance(self) -> CliView:
        """Fixture providing a CliView instance for tests.

        Returns
        -------
        CliView
            A CliView instance with 1 frame per second refresh rate.

        """
        return CliView(1)

    def test_map_to_str_must_have_two_dims_1d(self, view_instance: CliView) -> None:
        """Test that map_to_string rejects 1D arrays.

        The method expects 2D arrays (rows and columns). A 1D array should
        raise an AssertionError.
        """
        with pytest.raises(ValueError, match="Array must have two dimensions"):
            _ = view_instance.map_to_string(np.arange(10))

    def test_map_to_str_must_have_two_dims_3d(self, view_instance: CliView) -> None:
        """Test that map_to_string rejects 3D arrays.

        The method expects exactly 2D arrays. A 3D array should raise an
        AssertionError.
        """
        with pytest.raises(ValueError, match="Array must have two dimensions"):
            _ = view_instance.map_to_string(np.zeros((3, 4, 4)))

    @pytest.mark.parametrize("is_alive", [True, False])
    @pytest.mark.parametrize("shape", [(2, 2), (5, 4), (4, 15)])
    def test_map_to_str_all_dead_or_alive(self, view_instance: CliView, shape: tuple[int, int], is_alive: bool) -> None:
        """Test string conversion for grids that are completely alive or dead.

        Verifies that grids with all cells in the same state (all alive or all dead)
        are correctly converted to strings of all live symbols or all dead symbols.

        Parameters
        ----------
        view_instance : CliView
            The view instance to test.
        shape : tuple[int, int]
            The dimensions (rows, cols) of the test grid.
        is_alive : bool
            If True, test a grid of all live cells. If False, all dead cells.

        """
        create_numpy_array = np.ones if is_alive else np.zeros
        as_str = view_instance.map_to_string(create_numpy_array(shape, dtype=np.uint8))
        n_row, n_cols = shape
        cell_representation = view_instance.ALIVE_CELL if is_alive else view_instance.DEAD_CELL
        assert as_str == "\n".join(itertools.repeat(cell_representation * n_cols, n_row))

    @pytest.mark.parametrize("multiplier", [-1, 2, 4, 5, 7])
    @pytest.mark.parametrize("shape", [(2, 2), (5, 4), (4, 15)])
    def test_map_to_str_not_ones_as_dead(self, view_instance: CliView, shape: tuple[int, int], multiplier: int) -> None:
        """Test that only 1 represents a live cell.

        Verifies that array values other than 1 (like -1, 2, 4, etc.) are
        treated as dead cells, not as live cells.

        Parameters
        ----------
        view_instance : CliView
            The view instance to test.
        shape : tuple[int, int]
            The dimensions (rows, cols) of the test grid.
        multiplier : int
            A non-1 value to use for array elements.

        """
        as_str = view_instance.map_to_string(np.ones(shape, dtype=np.int8) * multiplier)
        n_row, n_cols = shape
        assert as_str == "\n".join(itertools.repeat(view_instance.DEAD_CELL * n_cols, n_row))

    def test_map_to_str_some_dead_or_alive(self, view_instance: CliView) -> None:
        """Test string conversion for a mixed alive/dead pattern.

        Tests a 2x2 identity matrix where the diagonal is alive and
        off-diagonal is dead.
        """
        as_str = view_instance.map_to_string(np.eye(2, dtype=np.uint8))
        alive, dead = view_instance.ALIVE_CELL, view_instance.DEAD_CELL
        assert as_str == f"{alive}{dead}\n{dead}{alive}"

    def test_setup(self, view_instance: CliView, capsys: pytest.CaptureFixture[str]) -> None:
        view_instance.__enter__()
        captured = capsys.readouterr()
        assert captured.out == self._print_on_start
        assert captured.err == ""

    def test_teardown(self, view_instance: CliView, capsys: pytest.CaptureFixture[str]) -> None:
        view_instance.__exit__(None, None, None)
        captured = capsys.readouterr()
        assert captured.out == self._print_on_stop
        assert captured.err == ""

    def test_as_context_manager(self, view_instance: CliView, capsys: pytest.CaptureFixture[str]) -> None:
        with view_instance:
            pass
        captured = capsys.readouterr()
        assert captured.out == f"{self._print_on_start}{self._print_on_stop}"
        assert captured.err == ""

    def test_render(self, view_instance: CliView, capsys: pytest.CaptureFixture[str]) -> None:
        # Mock the GameOfLife class to isolate the functionality to be tested
        mock_game = Mock()
        mock_game.grid = np.ones((2, 2), dtype=np.uint8)
        mock_game.generation = 1

        view_instance.render(mock_game)

        # No output to stdout or err as it goes in to a rich.LiveDisplay
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""

        # Instance should not be invoked, only the properties which have been patched
        mock_game.assert_not_called()
