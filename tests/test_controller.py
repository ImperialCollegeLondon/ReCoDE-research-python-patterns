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
    computed_offset: int = GridCreatorFactory.approximate_offset_to_center(full_length, to_center_size)
    assert computed_offset == correct_value
