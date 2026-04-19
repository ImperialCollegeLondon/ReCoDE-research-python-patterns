"""
Test module for the controller module.

This module contains unit tests for the controller components, particularly
the GridCreatorFactory and its offset calculation logic.

Notes
-----
Tests use pytest parametrization to test multiple scenarios with a single
test function, demonstrating a common pattern for efficient test coverage.
"""

import pytest

from game_of_life.controller import GridCreatorFactory


@pytest.mark.parametrize(
    ("full_length", "to_center_size", "correct_value"),
    [
        pytest.param(50, 50, 0, id="trivial-same-size"),
        pytest.param(50, 0, 25, id="trivial-empty-size"),
        pytest.param(50, 30, 10, id="exactly-divisible"),
        pytest.param(50, 31, 10, id="to-center-floored"),
        pytest.param(50, 32, 9, id="to-center-not-floored"),
        pytest.param(51, 30, 10, id="full-floored"),
    ],
)
def test_approx_offset_to_center(full_length: int, to_center_size: int, correct_value: int) -> None:
    """
    Test the approximate_offset_to_center method with various edge cases.

    This test uses parametrization, a powerful pytest feature that allows
    testing multiple scenarios with a single test function. Each tuple
    represents a test case with different inputs and expected outputs.

    Parameters
    ----------
    full_length : int
        The total length of the container space.
    to_center_size : int
        The length of the element to center.
    correct_value : int
        The expected offset calculation result.

    Notes
    -----
    The test cases cover important edge cases:
    - When sizes are equal (no offset needed)
    - When element is empty (maximum offset)
    - When division is exact vs. requires flooring
    - When the container length requires flooring

    Parametrization reduces code duplication and makes it easy to add new
    test cases by simply adding new tuples to the parameter list.


    """
    computed_offset: int = GridCreatorFactory.approximate_offset_to_center(full_length, to_center_size)
    assert computed_offset == correct_value
