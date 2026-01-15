import asyncio
import subprocess
from pathlib import Path

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label, Static

from paper_todo.animation import generate_knight_rider_frames, run_animation
from paper_todo.models import MAX_TASKS, TASK_CHAR_LIMIT, AppState, Task
from paper_todo.storage import load_state, save_state
from paper_todo.theme import ThemeMode, detect_system_theme
from paper_todo.widgets import ProgressBarTimer, TaskRow
from paper_todo.widgets.task_indicator import IndicatorState


def _send_notification(title: str, message: str, *, sound: str = "Glass") -> None:
    script = f'display notification "{message}" with title "{title}" sound name "{sound}"'
    subprocess.run(["osascript", "-e", script], check=False, capture_output=True)


def _format_timer_time(seconds: int) -> str:
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def _get_timer_status(timer) -> str:
    if timer.running:
        task_info = "Break time!" if timer.is_break else f"Task {(timer.task_index or 0) + 1}"
        return f"▶ {task_info}"
    return "Ready to start!"


def _calculate_duration_and_break(index: int) -> tuple[int, bool]:
    if index == 5:
        return (10, True)
    return ((index + 1) * 10, False)


class PaperTodoApp(App):
    CSS_PATH = Path(__file__).parent / "paper_todo.tcss"

    BINDINGS = [
        Binding("1", "task_action(1)", "[1-6] edit", show=True),
        Binding("2", "task_action(2)", show=False),
        Binding("3", "task_action(3)", show=False),
        Binding("4", "task_action(4)", show=False),
        Binding("5", "task_action(5)", show=False),
        Binding("6", "task_action(6)", show=False),
        Binding("s,S", "start", "start", show=True),
        Binding("t,T", "toggle_theme", "theme", show=True),
        Binding("c,C", "complete_and_end", "complete & end", show=True),
        Binding("e,E", "end_timer", "end", show=True),
        Binding("q,Q", "quit", "quit", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.state = load_state()
        self.theme_mode = detect_system_theme()
        self.task_rows: list[TaskRow] = []
        self.progress_bar: ProgressBarTimer | None = None
        self.timer_worker = None

    @property
    def is_timer_active(self) -> bool:
        return self.state.timer.running

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "start":
            return None if self.is_timer_active else True
        if action == "task_action":
            return None if self.is_timer_active else True
        if action in ("complete_and_end", "end_timer"):
            return True if self.is_timer_active else None
        return True

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-content"):
            self.progress_bar = ProgressBarTimer(self.state, self.theme_mode)
            yield self.progress_bar
            with Vertical(id="task-list"):
                for i in range(MAX_TASKS):
                    row = TaskRow(i, self.state.tasks[i])
                    self.task_rows.append(row)
                    yield row
        yield Footer()

    def _refresh_task_rows(self) -> None:
        for i, row in enumerate(self.task_rows):
            is_active = self.state.timer.task_index == i and self.state.timer.running
            row.task_model = self.state.tasks[i]
            row.refresh_display(is_active=is_active)

    def on_mount(self) -> None:
        self._apply_theme()
        if self.state.timer.running:
            self._refresh_task_rows()
            self.refresh_bindings()
            if self.progress_bar:
                self.progress_bar.restore_timer_state()
            self.start_timer_worker()

    def on_unmount(self) -> None:
        save_state(self.state)

    def _apply_theme(self) -> None:
        if self.theme_mode == ThemeMode.LIGHT:
            self.screen.add_class("-light-mode")
        else:
            self.screen.remove_class("-light-mode")
        if self.progress_bar:
            self.progress_bar.set_theme_mode(self.theme_mode)

    def action_toggle_theme(self) -> None:
        self.theme_mode = ThemeMode.LIGHT if self.theme_mode == ThemeMode.DARK else ThemeMode.DARK
        self._apply_theme()

    def action_task_action(self, task_num: int) -> None:
        task_index = task_num - 1
        if 0 <= task_index < MAX_TASKS:
            self._edit_task(task_index)

    def _edit_task(self, task_index: int) -> None:
        task = self.state.tasks[task_index]

        async def get_task_input() -> None:
            result = await self.app.push_screen_wait(
                TaskInputScreen(task_index, task.text, task.completed)
            )
            if result is None:
                return
            action, new_text = result
            if action == "save":
                self.state.tasks[task_index].text = new_text[:TASK_CHAR_LIMIT]
            elif action == "complete":
                self.state.tasks[task_index].text = new_text[:TASK_CHAR_LIMIT]
                self.state.tasks[task_index].completed = True
            elif action == "toggle":
                self.state.tasks[task_index].text = new_text[:TASK_CHAR_LIMIT]
                self.state.tasks[task_index].completed = not self.state.tasks[task_index].completed
            self._refresh_task_rows()
            save_state(self.state)

        self.run_worker(get_task_input())

    async def _animate_task_selection(self, incomplete_indices: list[int]) -> int:
        frames = generate_knight_rider_frames(incomplete_indices, num_cycles=3)

        completed_indices = {i for i in range(MAX_TASKS) if self.state.tasks[i].completed}

        def on_frame(idx: int) -> None:
            for i, row in enumerate(self.task_rows):
                if i == idx:
                    row.set_indicator_state(IndicatorState.BRIGHT)
                elif i in completed_indices:
                    row.set_indicator_state(IndicatorState.COMPLETED_DIM)
                elif i in incomplete_indices:
                    row.set_indicator_state(IndicatorState.DIM)
                else:
                    row.set_indicator_state(IndicatorState.INACTIVE)

        final_index = await run_animation(frames, on_frame)

        for i, row in enumerate(self.task_rows):
            if i == final_index:
                row.set_indicator_state(IndicatorState.BRIGHT)
            elif i in completed_indices:
                row.set_indicator_state(IndicatorState.INACTIVE)
            else:
                row.set_indicator_state(IndicatorState.DIM)

        return final_index

    @work(exclusive=True)
    async def action_start(self) -> None:
        if self.is_timer_active:
            self.notify("Timer already running!", severity="warning")
            return

        if not self.progress_bar:
            return

        duration_index = await self.progress_bar.animate_duration_selection()
        duration_minutes, is_break = _calculate_duration_and_break(duration_index)

        if is_break:
            confirmed = await self.app.push_screen_wait(
                StartTimerConfirmScreen(duration_minutes, None, is_break=True)
            )
            if confirmed:
                self.state.timer.start(None, duration_minutes, is_break=True)
                await self.progress_bar.transition_to_running(duration_index, is_break=True)
        else:
            incomplete = self.state.get_incomplete_task_indices()
            if not incomplete:
                self.notify("No incomplete tasks - add some first!", severity="warning")
                self.progress_bar.reset()
                return

            await asyncio.sleep(0.5)

            task_index = await self._animate_task_selection(incomplete)
            task_text = self.state.tasks[task_index].text

            await asyncio.sleep(0.5)

            confirmed = await self.app.push_screen_wait(
                StartTimerConfirmScreen(duration_minutes, task_index, is_break=False, task_text=task_text)
            )
            if confirmed:
                self.state.timer.start(task_index, duration_minutes, is_break=False)
                await self.progress_bar.transition_to_running(duration_index, is_break=False)

        if self.state.timer.running:
            self.start_timer_worker()
            self.refresh_bindings()
            self._refresh_task_rows()
        else:
            self.progress_bar.reset()
            self._refresh_task_rows()

        save_state(self.state)

    def start_timer_worker(self) -> None:
        if self.timer_worker is None:
            self.timer_worker = self.run_worker(self._timer_tick(), exclusive=True)

    async def _timer_tick(self) -> None:
        while self.state.timer.running and self.state.timer.remaining_seconds > 0:
            await asyncio.sleep(1)
            self.state.timer.tick()

            if self.progress_bar:
                elapsed = self.state.timer.duration_seconds - self.state.timer.remaining_seconds
                self.progress_bar.update_fill(elapsed, self.state.timer.duration_seconds)

            if self.state.timer.should_warn_ten_percent() and not self.state.timer.warned_ten_percent:
                self.state.timer.warned_ten_percent = True
                remaining = _format_timer_time(self.state.timer.remaining_seconds)
                _send_notification("Paper TODO", f"10% remaining: {remaining}", sound="Purr")
                self.notify(f"10% remaining: {remaining}", severity="warning")

            save_state(self.state)

        if self.state.timer.is_finished():
            task_info = "Break" if self.state.timer.is_break else f"Task {(self.state.timer.task_index or 0) + 1}"
            _send_notification("Paper TODO", f"Time's up! {task_info} complete.", sound="Glass")
            self.state.timer.reset()
            self.timer_worker = None
            self.refresh_bindings()
            self._refresh_task_rows()
            if self.progress_bar:
                self.progress_bar.reset()
            save_state(self.state)

    def action_complete_and_end(self) -> None:
        if not self.is_timer_active:
            self.notify("No active timer", severity="warning")
            return

        if self.state.timer.task_index is not None:
            task_index = self.state.timer.task_index
            self.state.tasks[task_index].completed = True

            if self.progress_bar:
                self.run_worker(self._celebrate_and_stop())
        else:
            self._stop_timer()

    async def _celebrate_and_stop(self) -> None:
        if self.timer_worker:
            self.timer_worker.cancel()
            self.timer_worker = None

        self.state.timer.reset()
        self.refresh_bindings()
        self._refresh_task_rows()
        save_state(self.state)

        if self.progress_bar:
            await self.progress_bar.celebrate()

    def action_end_timer(self) -> None:
        if not self.is_timer_active:
            self.notify("No active timer", severity="warning")
            return

        self._stop_timer()

    def _stop_timer(self) -> None:
        if self.timer_worker:
            self.timer_worker.cancel()
            self.timer_worker = None

        self.state.timer.reset()
        self.refresh_bindings()
        self._refresh_task_rows()
        if self.progress_bar:
            self.progress_bar.reset()
        save_state(self.state)


class StartTimerConfirmScreen(ModalScreen[bool]):
    BINDINGS = [
        Binding("enter", "confirm", "start"),
        Binding("escape", "cancel", "cancel"),
    ]

    def __init__(self, duration_minutes: int, task_index: int | None, is_break: bool, task_text: str | None = None) -> None:
        super().__init__()
        self.duration_minutes = duration_minutes
        self.task_index = task_index
        self.is_break = is_break
        self.task_text = task_text

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            if self.is_break:
                yield Label("Break", id="task-info")
            else:
                task_display = self.task_text or "(empty)"
                yield Label(task_display, id="task-info")
            yield Label(f"{self.duration_minutes} minutes", id="timer-info")
            yield Label("[dim]Enter[/dim] start   [dim]Esc[/dim] cancel", id="confirm-hints")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


class TaskInputScreen(ModalScreen[tuple[str, str] | None]):
    def __init__(self, task_index: int, current_text: str, is_completed: bool) -> None:
        super().__init__()
        self.task_index = task_index
        self.current_text = current_text
        self.is_completed = is_completed

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            status = " (completed)" if self.is_completed else ""
            yield Label(f"Edit Task {self.task_index + 1}{status} (max {TASK_CHAR_LIMIT} chars)")
            yield Input(
                value=self.current_text,
                placeholder="Enter task description...",
                max_length=TASK_CHAR_LIMIT,
                id="task-input",
            )
            with Horizontal(id="buttons"):
                yield Button("Save", variant="success", id="save")
                if self.is_completed:
                    yield Button("Mark Incomplete", variant="warning", id="toggle")
                else:
                    yield Button("Mark Complete", variant="warning", id="complete")
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    @on(Button.Pressed, "#save")
    def save_task(self) -> None:
        input_widget = self.query_one(Input)
        self.dismiss(("save", input_widget.value))

    @on(Button.Pressed, "#complete")
    def complete_task(self) -> None:
        input_widget = self.query_one(Input)
        self.dismiss(("complete", input_widget.value))

    @on(Button.Pressed, "#toggle")
    def toggle_task(self) -> None:
        input_widget = self.query_one(Input)
        self.dismiss(("toggle", input_widget.value))

    @on(Button.Pressed, "#cancel")
    def cancel_edit(self) -> None:
        self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(("save", event.value))


def main() -> None:
    app = PaperTodoApp()
    app.run()


if __name__ == "__main__":
    main()
