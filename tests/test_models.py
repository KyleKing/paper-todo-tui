import pytest

from paper_todo.models import (
    TASK_CHAR_LIMIT,
    Task,
    TimerState,
    get_incomplete_task_indices,
)


def test_task_toggle():
    task = Task(text="Test task")
    assert task.completed is False
    task.toggle()
    assert task.completed is True
    task.toggle()
    assert task.completed is False


def test_task_max_length_rejected():
    with pytest.raises(Exception):
        Task(text="x" * (TASK_CHAR_LIMIT + 1))


@pytest.mark.parametrize(
    ("running", "initial_remaining", "expected_remaining"),
    [
        (True, 60, 59),
        (False, 100, 100),
    ],
    ids=["running-decrements", "stopped-unchanged"],
)
def test_timer_tick(running, initial_remaining, expected_remaining):
    timer = TimerState(running=running, remaining_seconds=initial_remaining)
    timer.tick()
    assert timer.remaining_seconds == expected_remaining


@pytest.mark.parametrize(
    ("running", "remaining", "expected"),
    [
        (False, 0, False),
        (True, 10, False),
        (True, 0, True),
    ],
    ids=["not-running", "running-time-left", "running-finished"],
)
def test_timer_is_finished(running, remaining, expected):
    timer = TimerState(running=running, remaining_seconds=remaining)
    assert timer.is_finished() is expected


def test_timer_should_warn_ten_percent():
    timer = TimerState()
    timer.start(task_index=0, duration_minutes=10, is_break=False)

    timer.remaining_seconds = 61
    assert timer.should_warn_ten_percent() is False

    timer.remaining_seconds = 60
    assert timer.should_warn_ten_percent() is True

    timer.warned_ten_percent = True
    assert timer.should_warn_ten_percent() is False


def test_get_incomplete_task_indices():
    tasks = [
        Task(text="Task 1", completed=False),
        Task(text="Task 2", completed=True),
        Task(text="", completed=False),
        Task(text="Task 4", completed=False),
        Task(text="Task 5", completed=True),
        Task(text="Task 6", completed=False),
    ]

    assert get_incomplete_task_indices(tasks) == [0, 3, 5]
