import asyncio
from datetime import datetime

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label, Static

from paper_todo.dice import get_dice_face, roll_die
from paper_todo.models import MAX_TASKS, TASK_CHAR_LIMIT, AppState, Task, TimerState
from paper_todo.storage import load_state, save_state


def _format_task_label(index: int, task: Task, is_active: bool) -> str:
    status = "✓" if task.completed else " "
    text = task.text or "(empty)"
    return f"[{index + 1}] [{status}] {text}"


def _format_timer_time(seconds: int) -> str:
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def _get_timer_status(timer: TimerState) -> str:
    if timer.running:
        task_info = "Break time!" if timer.is_break else f"Task {(timer.task_index or 0) + 1}"
        return f"▶ {task_info}"
    elif timer.remaining_seconds > 0:
        return "⏸ Paused"
    else:
        return "Ready to roll!"


def _roll_for_incomplete_task(incomplete_indices: list[int]) -> int:
    valid_task_numbers = [i + 1 for i in incomplete_indices]
    roll = roll_die()
    while roll not in valid_task_numbers:
        roll = roll_die()
    return roll - 1


def _calculate_duration_and_break(roll: int) -> tuple[int, bool]:
    if roll == 6:
        return (10, True)
    return (roll * 10, False)


class TaskList(Static):
    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield Label("[bold cyan]📝 Your Tasks (max 6)[/bold cyan]")
        for i in range(MAX_TASKS):
            is_active = self.state.timer.task_index == i and self.state.timer.running
            highlight = "on blue" if is_active else ""
            yield Label(_format_task_label(i, self.state.tasks[i], is_active), id=f"task-{i}", classes=highlight)

    def refresh_tasks(self) -> None:
        for i in range(MAX_TASKS):
            is_active = self.state.timer.task_index == i and self.state.timer.running
            label = self.query_one(f"#task-{i}", Label)
            label.update(_format_task_label(i, self.state.tasks[i], is_active))
            label.styles.background = "blue" if is_active else "transparent"


class DiceDisplay(Static):
    def __init__(self) -> None:
        super().__init__()
        self.current_value = 1

    def compose(self) -> ComposeResult:
        yield Label("[bold yellow]🎲 Dice[/bold yellow]")
        yield Label(get_dice_face(1), id="dice-face")

    def set_value(self, value: int) -> None:
        self.current_value = value
        self.query_one("#dice-face", Label).update(get_dice_face(value))


class TimerDisplay(Static):
    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield Label("[bold green]⏱️  Timer[/bold green]")
        yield Label("--:--", id="timer-time")
        yield Label("", id="timer-status")

    def refresh_timer(self) -> None:
        self.query_one("#timer-time", Label).update(_format_timer_time(self.state.timer.remaining_seconds))
        self.query_one("#timer-status", Label).update(_get_timer_status(self.state.timer))


class PaperTodoApp(App):
    CSS = """
    Screen {
        background: $surface;
    }

    TaskList {
        border: solid green;
        padding: 1;
        margin: 1;
        height: auto;
    }

    DiceDisplay {
        border: solid yellow;
        padding: 1;
        margin: 1;
        width: 40;
        height: auto;
    }

    TimerDisplay {
        border: solid blue;
        padding: 1;
        margin: 1;
        width: 40;
        height: auto;
    }

    #help {
        border: solid white;
        padding: 1;
        margin: 1;
        height: auto;
    }
    """

    BINDINGS = [
        Binding("1", "edit_task(1)", "Edit task 1", show=False),
        Binding("2", "edit_task(2)", "Edit task 2", show=False),
        Binding("3", "edit_task(3)", "Edit task 3", show=False),
        Binding("4", "edit_task(4)", "Edit task 4", show=False),
        Binding("5", "edit_task(5)", "Edit task 5", show=False),
        Binding("6", "edit_task(6)", "Edit task 6", show=False),
        Binding("r", "roll_task", "Roll for task", show=True),
        Binding("t", "roll_time", "Roll for time", show=True),
        Binding("space", "toggle_timer", "Start/Pause", show=True),
        Binding("c", "toggle_complete", "Complete", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.state = load_state()
        self.editing_task: int | None = None
        self.task_list: TaskList | None = None
        self.dice_display: DiceDisplay | None = None
        self.timer_display: TimerDisplay | None = None
        self.timer_worker = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical():
                self.task_list = TaskList(self.state)
                yield self.task_list
                yield Static(
                    "[bold]Keys:[/bold] 1-6: Edit | R: Roll task | T: Roll time | Space: Start/Pause | C: Complete | Q: Quit",
                    id="help",
                )
            with Vertical():
                self.dice_display = DiceDisplay()
                yield self.dice_display
                self.timer_display = TimerDisplay(self.state)
                yield self.timer_display
        yield Footer()

    def on_mount(self) -> None:
        if self.state.timer.running or self.state.timer.remaining_seconds > 0:
            self.timer_display.refresh_timer()
            if self.state.timer.running:
                self.start_timer_worker()

    def on_unmount(self) -> None:
        save_state(self.state)

    def action_edit_task(self, task_num: int) -> None:
        task_index = task_num - 1
        if 0 <= task_index < MAX_TASKS:
            self.edit_task(task_index)

    def edit_task(self, task_index: int) -> None:
        async def get_task_input() -> None:
            current_text = self.state.tasks[task_index].text
            result = await self.app.push_screen_wait(
                TaskInputScreen(task_index, current_text)
            )
            if result is not None:
                self.state.tasks[task_index].text = result[:TASK_CHAR_LIMIT]
                self.task_list.refresh_tasks()
                save_state(self.state)

        self.run_worker(get_task_input())

    async def _animate_and_roll_task(self) -> int | None:
        if not (incomplete := self.state.get_incomplete_task_indices()):
            self.notify("No incomplete tasks to roll for!", severity="warning")
            return None

        for _ in range(10):
            self.dice_display.set_value(roll_die())
            await asyncio.sleep(0.1)

        selected_index = _roll_for_incomplete_task(incomplete)
        self.dice_display.set_value(selected_index + 1)
        return selected_index

    @work(exclusive=True)
    async def action_roll_task(self) -> None:
        if (selected_index := await self._animate_and_roll_task()) is not None:
            self.notify(f"Work on task {selected_index + 1}: {self.state.tasks[selected_index].text}")

    @work(exclusive=True)
    async def action_roll_time(self) -> None:
        for _ in range(10):
            self.dice_display.set_value(roll_die())
            await asyncio.sleep(0.1)

        final_roll = roll_die()
        self.dice_display.set_value(final_roll)
        duration_minutes, is_break = _calculate_duration_and_break(final_roll)

        if is_break:
            self.notify(f"Rolled {final_roll}: 10 minute break!")
            self.state.timer.start(None, duration_minutes, is_break=True)
        else:
            self.notify(f"Rolled {final_roll}: {duration_minutes} minutes")
            if incomplete := self.state.get_incomplete_task_indices():
                await asyncio.sleep(0.5)
                if (selected_index := await self._animate_and_roll_task()) is not None:
                    self.notify(f"Work on task {selected_index + 1}: {self.state.tasks[selected_index].text}")
                    self.state.timer.start(selected_index, duration_minutes, is_break=False)
                else:
                    self.state.timer.start(None, duration_minutes, is_break=True)
            else:
                self.state.timer.start(None, duration_minutes, is_break=True)

        self.timer_display.refresh_timer()
        self.task_list.refresh_tasks()
        save_state(self.state)

    def action_toggle_timer(self) -> None:
        if self.state.timer.running:
            self.state.timer.pause()
            self.notify("Timer paused")
            if self.timer_worker:
                self.timer_worker.cancel()
                self.timer_worker = None
        elif self.state.timer.remaining_seconds > 0:
            self.state.timer.resume()
            self.notify("Timer resumed")
            self.start_timer_worker()
        else:
            self.notify("Roll for time first (press T)", severity="warning")

        self.timer_display.refresh_timer()
        self.task_list.refresh_tasks()
        save_state(self.state)

    def start_timer_worker(self) -> None:
        if self.timer_worker is None:
            self.timer_worker = self.run_worker(self.timer_tick(), exclusive=True)

    @work(exclusive=True)
    async def timer_tick(self) -> None:
        while self.state.timer.running and self.state.timer.remaining_seconds > 0:
            await asyncio.sleep(1)
            self.state.timer.tick()
            self.timer_display.refresh_timer()
            save_state(self.state)

        if self.state.timer.is_finished():
            self.notify("⏰ Time's up!", severity="information")
            self.state.timer.reset()
            self.timer_display.refresh_timer()
            self.task_list.refresh_tasks()
            save_state(self.state)

    def action_toggle_complete(self) -> None:
        if self.state.timer.task_index is not None:
            task_index = self.state.timer.task_index
            self.state.tasks[task_index].toggle()
            task = self.state.tasks[task_index]
            status = "completed" if task.completed else "incomplete"
            self.notify(f"Task {task_index + 1} marked as {status}")
            self.task_list.refresh_tasks()
            save_state(self.state)
        else:
            self.notify("No active task to complete", severity="warning")


class TaskInputScreen(ModalScreen[str | None]):
    CSS = """
    TaskInputScreen {
        align: center middle;
    }

    #dialog {
        width: 60;
        height: 11;
        border: solid green;
        background: $surface;
        padding: 1;
    }

    #task-input {
        width: 100%;
        margin-bottom: 1;
    }

    #buttons {
        width: 100%;
        height: auto;
        align: center middle;
    }
    """

    def __init__(self, task_index: int, current_text: str) -> None:
        super().__init__()
        self.task_index = task_index
        self.current_text = current_text

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label(f"Edit Task {self.task_index + 1} (max {TASK_CHAR_LIMIT} chars)")
            yield Input(
                value=self.current_text,
                placeholder="Enter task description...",
                max_length=TASK_CHAR_LIMIT,
                id="task-input",
            )
            with Horizontal(id="buttons"):
                yield Button("Save", variant="success", id="save")
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    @on(Button.Pressed, "#save")
    def save_task(self) -> None:
        input_widget = self.query_one(Input)
        self.dismiss(input_widget.value)

    @on(Button.Pressed, "#cancel")
    def cancel_edit(self) -> None:
        self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)


def main() -> None:
    app = PaperTodoApp()
    app.run()


if __name__ == "__main__":
    main()
