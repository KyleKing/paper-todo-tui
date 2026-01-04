from unittest.mock import patch

import pytest

from paper_todo.app import PaperTodoApp
from paper_todo.models import AppState, Task, TimerState


def _fresh_state() -> AppState:
    return AppState()


async def test_app_initializes():
    with patch("paper_todo.app.load_state", return_value=_fresh_state()):
        app = PaperTodoApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.state is not None
            assert len(app.state.tasks) == 6


async def test_edit_task_dialog():
    with patch("paper_todo.app.load_state", return_value=_fresh_state()):
        app = PaperTodoApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("1")
            await pilot.pause(delay=0.5)
            assert len(pilot.app.screen_stack) == 2
            input_widget = pilot.app.screen.query_one("#task-input")
            input_widget.value = ""
            await pilot.pause()
            for char in "Test task":
                await pilot.press(char)
            await pilot.pause()
            await pilot.click("#save")
            await pilot.pause()
            assert app.state.tasks[0].text == "Test task"


async def test_edit_task_cancel():
    with patch("paper_todo.app.load_state", return_value=_fresh_state()):
        app = PaperTodoApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            original_text = app.state.tasks[0].text
            await pilot.press("1")
            await pilot.pause(delay=0.5)
            input_widget = pilot.app.screen.query_one("#task-input")
            input_widget.value = ""
            await pilot.pause()
            for char in "New text":
                await pilot.press(char)
            await pilot.pause()
            await pilot.click("#cancel")
            await pilot.pause()
            assert app.state.tasks[0].text == original_text


async def test_edit_task_mark_complete():
    state = _fresh_state()
    state.tasks[0].text = "Task to complete"
    with patch("paper_todo.app.load_state", return_value=state):
        app = PaperTodoApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("1")
            await pilot.pause(delay=0.5)
            await pilot.click("#complete")
            await pilot.pause()
            assert app.state.tasks[0].completed is True


@pytest.mark.parametrize(
    ("key", "check_screen_stack"),
    [
        ("2", True),
        ("r", False),
    ],
    ids=["edit-blocked", "roll-blocked"],
)
async def test_action_blocked_during_timer(key, check_screen_stack):
    state = _fresh_state()
    state.tasks[0].text = "Test task"
    state.timer.start(0, 10, is_break=False)
    initial_remaining = state.timer.remaining_seconds
    with patch("paper_todo.app.load_state", return_value=state):
        app = PaperTodoApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press(key)
            await pilot.pause(delay=0.5)
            if check_screen_stack:
                assert len(pilot.app.screen_stack) == 1
            assert app.state.timer.remaining_seconds == initial_remaining


async def test_roll_no_incomplete_tasks():
    state = _fresh_state()
    for task in state.tasks:
        task.text = "Task"
        task.completed = True
    with patch("paper_todo.app.load_state", return_value=state):
        app = PaperTodoApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("r")
            await pilot.pause(delay=0.5)
            assert not app.state.timer.running


@pytest.mark.parametrize(
    ("duration_roll", "expected_minutes", "is_break"),
    [
        (3, 30, False),
        (6, 10, True),
    ],
    ids=["task-timer", "break-timer"],
)
async def test_roll_with_confirmation_start(duration_roll, expected_minutes, is_break):
    state = _fresh_state()
    state.tasks[0].text = "Test task"
    state.tasks[0].completed = False
    task_rolls = [1] * 11
    duration_rolls = [duration_roll] * 11
    with (
        patch("paper_todo.app.load_state", return_value=state),
        patch("paper_todo.app.roll_from_options", side_effect=task_rolls + duration_rolls),
    ):
        app = PaperTodoApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            with patch.object(app, "start_timer_worker") as mock_start:
                await pilot.press("r")
                await pilot.pause(delay=3.0)
                assert len(pilot.app.screen_stack) == 2
                await pilot.click("#start")
                await pilot.pause()
                assert app.state.timer.running
                assert app.state.timer.is_break is is_break
                assert app.state.timer.remaining_seconds == expected_minutes * 60
                mock_start.assert_called_once()


async def test_roll_with_confirmation_cancel():
    state = _fresh_state()
    state.tasks[0].text = "Test task"
    state.tasks[0].completed = False
    task_rolls = [1] * 11
    duration_rolls = [3] * 11
    with (
        patch("paper_todo.app.load_state", return_value=state),
        patch("paper_todo.app.roll_from_options", side_effect=task_rolls + duration_rolls),
    ):
        app = PaperTodoApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("r")
            await pilot.pause(delay=3.0)
            await pilot.click("#cancel")
            await pilot.pause()
            assert not app.state.timer.running
            assert app.state.timer.remaining_seconds == 0


async def test_complete_and_end_with_active_timer():
    state = _fresh_state()
    state.tasks[0].text = "Test task"
    state.timer.start(0, 10, is_break=False)
    with patch("paper_todo.app.load_state", return_value=state):
        app = PaperTodoApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            assert not app.state.tasks[0].completed
            await pilot.press("c")
            await pilot.pause()
            assert app.state.tasks[0].completed
            assert not app.state.timer.running


async def test_end_timer_without_completing():
    state = _fresh_state()
    state.tasks[0].text = "Test task"
    state.timer.start(0, 10, is_break=False)
    with patch("paper_todo.app.load_state", return_value=state):
        app = PaperTodoApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            assert not app.state.tasks[0].completed
            await pilot.press("e")
            await pilot.pause()
            assert not app.state.tasks[0].completed
            assert not app.state.timer.running


async def test_timer_persists_on_mount():
    state = AppState(
        tasks=[Task(text=f"Task {i}") for i in range(6)],
        timer=TimerState(
            running=True,
            remaining_seconds=600,
            duration_seconds=600,
            task_index=0,
            is_break=False,
        ),
    )
    with patch("paper_todo.app.load_state", return_value=state):
        app = PaperTodoApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.state.timer.running
            assert app.state.timer.remaining_seconds == 600
