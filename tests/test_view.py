"""
Test for the classes responsible for the interface which presents information to the user
"""

import itertools

import numpy as np
import pytest

from game_of_life.view.cli import CliView


class TestCLIView:
    @pytest.fixture
    def view_instance(self) -> CliView:
        return CliView(1)

    def test_map_to_str_must_have_two_dims_1d(self, view_instance: CliView) -> None:
        with pytest.raises(AssertionError):
            _ = view_instance.map_to_string(np.arange(10))

    def test_map_to_str_must_have_two_dims_3d(self, view_instance: CliView) -> None:
        with pytest.raises(AssertionError):
            _ = view_instance.map_to_string(np.zeros((3, 4, 4)))

    @pytest.mark.parametrize("is_alive", [True, False])
    @pytest.mark.parametrize("shape", [(2, 2), (5, 4), (4, 15)])
    def test_map_to_str_all_dead_or_alive(self, view_instance: CliView, shape: tuple[int, int], is_alive: bool) -> None:
        create_numpy_array = np.ones if is_alive else np.zeros
        as_str = view_instance.map_to_string(create_numpy_array(shape, dtype=np.uint8))
        n_row, n_cols = shape
        cell_representation = view_instance.ALIVE_CELL if is_alive else view_instance.DEAD_CELL
        assert as_str == "\n".join(itertools.repeat(cell_representation * n_cols, n_row))

    def test_map_to_str_some_dead_or_alive(self, view_instance: CliView) -> None:
        as_str = view_instance.map_to_string(np.eye(2, dtype=np.uint8))
        alive, dead = view_instance.ALIVE_CELL, view_instance.DEAD_CELL
        assert as_str == f"{alive}{dead}\n{dead}{alive}"
