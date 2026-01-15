import pytest

from paper_todo.app import (
    _calculate_duration_and_break,
    _format_timer_time,
    _get_timer_status,
)
from paper_todo.models import TimerState


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0, "00:00"),
        (59, "00:59"),
        (60, "01:00"),
        (125, "02:05"),
        (3661, "61:01"),
    ],
)
def test_format_timer_time(seconds, expected):
    assert _format_timer_time(seconds) == expected


@pytest.mark.parametrize(
    ("task_index", "running", "is_break", "expected"),
    [
        (None, False, False, "Ready to start!"),
        (2, True, False, "▶ Task 3"),
        (None, True, True, "▶ Break time!"),
    ],
    ids=["ready", "running-task", "running-break"],
)
def test_get_timer_status(task_index, running, is_break, expected):
    timer = TimerState(task_index=task_index, running=running, is_break=is_break)
    assert _get_timer_status(timer) == expected


@pytest.mark.parametrize(
    ("index", "expected_duration", "expected_break"),
    [
        (0, 10, False),
        (1, 20, False),
        (2, 30, False),
        (3, 40, False),
        (4, 50, False),
        (5, 10, True),
    ],
)
def test_calculate_duration_and_break(index, expected_duration, expected_break):
    assert _calculate_duration_and_break(index) == (expected_duration, expected_break)
