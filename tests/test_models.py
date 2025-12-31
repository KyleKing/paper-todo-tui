from datetime import datetime

import pytest

from paper_todo.models import (
    MAX_TASKS,
    TASK_CHAR_LIMIT,
    AppState,
    Task,
    TimerState,
    _is_task_incomplete,
    get_incomplete_task_indices,
)


def test_task_defaults():
    task = Task()
    assert task.text == ""
    assert task.completed is False


def test_task_toggle():
    task = Task(text="Test task")
    assert task.completed is False
    task.toggle()
    assert task.completed is True
    task.toggle()
    assert task.completed is False


def test_task_max_length():
    long_text = "x" * (TASK_CHAR_LIMIT + 10)
    with pytest.raises(Exception):
        Task(text=long_text)


def test_is_task_incomplete():
    assert _is_task_incomplete(Task(text="Test", completed=False)) is True
    assert _is_task_incomplete(Task(text="Test", completed=True)) is False
    assert _is_task_incomplete(Task(text="", completed=False)) is False
    assert _is_task_incomplete(Task(text="", completed=True)) is False


def test_timer_state_defaults():
    timer = TimerState()
    assert timer.task_index is None
    assert timer.duration_seconds == 0
    assert timer.remaining_seconds == 0
    assert timer.is_break is False
    assert timer.running is False
    assert timer.start_time is None


def test_timer_start():
    timer = TimerState()
    timer.start(task_index=2, duration_minutes=10, is_break=False)

    assert timer.task_index == 2
    assert timer.duration_seconds == 600
    assert timer.remaining_seconds == 600
    assert timer.is_break is False
    assert timer.running is True
    assert isinstance(timer.start_time, datetime)


def test_timer_start_break():
    timer = TimerState()
    timer.start(task_index=None, duration_minutes=10, is_break=True)

    assert timer.task_index is None
    assert timer.is_break is True
    assert timer.running is True


def test_timer_pause_resume():
    timer = TimerState()
    timer.start(task_index=0, duration_minutes=5, is_break=False)

    timer.pause()
    assert timer.running is False

    timer.resume()
    assert timer.running is True


def test_timer_resume_no_time_remaining():
    timer = TimerState()
    timer.remaining_seconds = 0
    timer.resume()
    assert timer.running is False


def test_timer_tick():
    timer = TimerState()
    timer.start(task_index=0, duration_minutes=1, is_break=False)
    initial_remaining = timer.remaining_seconds

    timer.tick()
    assert timer.remaining_seconds == initial_remaining - 1


def test_timer_tick_not_running():
    timer = TimerState()
    timer.remaining_seconds = 100
    timer.running = False

    timer.tick()
    assert timer.remaining_seconds == 100


def test_timer_is_finished():
    timer = TimerState()
    assert timer.is_finished() is True

    timer.remaining_seconds = 10
    assert timer.is_finished() is False

    timer.remaining_seconds = 0
    assert timer.is_finished() is True


def test_timer_reset():
    timer = TimerState()
    timer.start(task_index=3, duration_minutes=20, is_break=False)
    timer.reset()

    assert timer.task_index is None
    assert timer.duration_seconds == 0
    assert timer.remaining_seconds == 0
    assert timer.is_break is False
    assert timer.running is False
    assert timer.start_time is None


def test_app_state_defaults():
    state = AppState()
    assert len(state.tasks) == MAX_TASKS
    assert all(isinstance(task, Task) for task in state.tasks)
    assert isinstance(state.timer, TimerState)


def test_get_incomplete_task_indices():
    tasks = [
        Task(text="Task 1", completed=False),
        Task(text="Task 2", completed=True),
        Task(text="", completed=False),
        Task(text="Task 4", completed=False),
        Task(text="Task 5", completed=True),
        Task(text="Task 6", completed=False),
    ]

    incomplete = get_incomplete_task_indices(tasks)
    assert incomplete == [0, 3, 5]


def test_app_state_get_incomplete_task_indices():
    state = AppState()
    state.tasks[0].text = "Task 1"
    state.tasks[1].text = "Task 2"
    state.tasks[1].completed = True
    state.tasks[3].text = "Task 4"

    incomplete = state.get_incomplete_task_indices()
    assert incomplete == [0, 3]
