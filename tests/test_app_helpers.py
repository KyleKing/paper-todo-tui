import pytest

from paper_todo.app import (
    _calculate_duration_and_break,
    _format_task_label,
    _format_timer_time,
    _get_timer_status,
    _roll_for_incomplete_task,
)
from paper_todo.models import Task, TimerState


def test_format_task_label():
    task = Task(text="Test task", completed=False)
    label = _format_task_label(0, task, is_active=False)
    assert label == "[1] [ ] Test task"


def test_format_task_label_completed():
    task = Task(text="Done task", completed=True)
    label = _format_task_label(2, task, is_active=False)
    assert label == "[3] [✓] Done task"


def test_format_task_label_empty():
    task = Task()
    label = _format_task_label(5, task, is_active=False)
    assert label == "[6] [ ] (empty)"


def test_format_timer_time():
    assert _format_timer_time(0) == "00:00"
    assert _format_timer_time(59) == "00:59"
    assert _format_timer_time(60) == "01:00"
    assert _format_timer_time(125) == "02:05"
    assert _format_timer_time(3661) == "61:01"


def test_get_timer_status_ready():
    timer = TimerState()
    assert _get_timer_status(timer) == "Ready to roll!"


def test_get_timer_status_paused():
    timer = TimerState()
    timer.remaining_seconds = 100
    timer.running = False
    assert _get_timer_status(timer) == "⏸ Paused"


def test_get_timer_status_running_task():
    timer = TimerState()
    timer.task_index = 2
    timer.running = True
    timer.is_break = False
    status = _get_timer_status(timer)
    assert status == "▶ Task 3"


def test_get_timer_status_running_break():
    timer = TimerState()
    timer.running = True
    timer.is_break = True
    status = _get_timer_status(timer)
    assert status == "▶ Break time!"


def test_roll_for_incomplete_task():
    incomplete = [0, 2, 5]
    for _ in range(20):
        result = _roll_for_incomplete_task(incomplete)
        assert result in incomplete


def test_roll_for_incomplete_task_single():
    incomplete = [3]
    result = _roll_for_incomplete_task(incomplete)
    assert result == 3


def test_calculate_duration_and_break():
    assert _calculate_duration_and_break(1) == (10, False)
    assert _calculate_duration_and_break(2) == (20, False)
    assert _calculate_duration_and_break(3) == (30, False)
    assert _calculate_duration_and_break(4) == (40, False)
    assert _calculate_duration_and_break(5) == (50, False)
    assert _calculate_duration_and_break(6) == (10, True)
