import asyncio
import subprocess

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label, Static

from paper_todo.dice import get_dice_face, roll_die, roll_from_options
from paper_todo.models import MAX_TASKS, TASK_CHAR_LIMIT, AppState, Task
from paper_todo.storage import load_state, save_state


def _send_notification(title: str, message: str, *, sound: str = "Glass") -> None:
    script = f'display notification "{message}" with title "{title}" sound name "{sound}"'
    subprocess.run(["osascript", "-e", script], check=False, capture_output=True)


def _format_task_label(index: int, task: Task, is_active: bool) -> str:
    status = "✓" if task.completed else " "
    text = task.text or "(empty)"
    return f"[{index + 1}] [{status}] {text}"


def _format_timer_time(seconds: int) -> str:
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def _get_timer_status(timer) -> str:
    if timer.running:
        task_info = "Break time!" if timer.is_break else f"Task {(timer.task_index or 0) + 1}"
        return f"▶ {task_info}"
    return "Ready to roll!"


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

            if self.state.timer.running and not is_active:
                label.add_class("inactive-task")
            else:
                label.remove_class("inactive-task")


class RightPanel(Static):
    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
        self.task_dice_value = 1
        self.duration_dice_value = 1

    def compose(self) -> ComposeResult:
        with Vertical(id="right-panel-content"):
            with Horizontal(id="dice-section"):
                with Vertical(id="task-dice-container"):
                    yield Label("[bold cyan]Task #[/bold cyan]", id="task-dice-label")
                    yield Label(get_dice_face(1), id="task-dice-face")
                with Vertical(id="duration-dice-container"):
                    yield Label("[bold yellow]Duration[/bold yellow]", id="duration-dice-label")
                    yield Label(get_dice_face(1), id="duration-dice-face")
            with Vertical(id="timer-section"):
                yield Label("[bold green]⏱️  Timer[/bold green]")
                yield Label("--:--", id="timer-time")
                yield Label("", id="timer-status")

    def set_task_dice_value(self, value: int) -> None:
        self.task_dice_value = value
        self.query_one("#task-dice-face", Label).update(get_dice_face(value))

    def set_duration_dice_value(self, value: int) -> None:
        self.duration_dice_value = value
        self.query_one("#duration-dice-face", Label).update(get_dice_face(value))

    def refresh_timer(self) -> None:
        self.query_one("#timer-time", Label).update(_format_timer_time(self.state.timer.remaining_seconds))
        self.query_one("#timer-status", Label).update(_get_timer_status(self.state.timer))

    def refresh_dimming(self) -> None:
        dice_section = self.query_one("#dice-section")
        if self.state.timer.running:
            dice_section.add_class("dimmed")
        else:
            dice_section.remove_class("dimmed")


class PaperTodoApp(App):
    CSS = """
    Screen {
        background: $surface;
    }

    #left-column {
        width: 3fr;
        height: 100%;
    }

    TaskList {
        border: solid green;
        padding: 1;
        margin: 1;
        height: auto;
    }

    RightPanel {
        border: solid yellow;
        padding: 1;
        margin: 1;
        height: auto;
        width: 2fr;
    }

    #right-panel-content {
        height: auto;
        width: 100%;
    }

    #dice-section {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    #task-dice-container {
        width: 1fr;
        height: auto;
        padding-right: 1;
    }

    #duration-dice-container {
        width: 1fr;
        height: auto;
        padding-left: 1;
    }

    #timer-section {
        width: 100%;
        height: auto;
        border-top: solid blue;
        padding-top: 1;
    }

    #help {
        border: solid white;
        padding: 1;
        margin: 1;
        height: auto;
    }

    .dimmed {
        opacity: 0.3;
    }

    .inactive-task {
        opacity: 0.5;
    }
    """

    BINDINGS = [
        Binding("1", "task_action(1)", "Task 1", show=False),
        Binding("2", "task_action(2)", "Task 2", show=False),
        Binding("3", "task_action(3)", "Task 3", show=False),
        Binding("4", "task_action(4)", "Task 4", show=False),
        Binding("5", "task_action(5)", "Task 5", show=False),
        Binding("6", "task_action(6)", "Task 6", show=False),
        Binding("r,R", "roll", "roll", show=True),
        Binding("c,C", "complete_and_end", "complete & end", show=True),
        Binding("e,E", "end_timer", "end", show=True),
        Binding("q,Q", "quit", "quit", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.state = load_state()
        self.task_list: TaskList | None = None
        self.right_panel: RightPanel | None = None
        self.help_widget: Static | None = None
        self.timer_worker = None

    @property
    def is_timer_active(self) -> bool:
        return self.state.timer.running

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="left-column"):
                self.task_list = TaskList(self.state)
                yield self.task_list
                self.help_widget = Static(self._get_help_text(), id="help")
                yield self.help_widget
            self.right_panel = RightPanel(self.state)
            yield self.right_panel
        yield Footer()

    def _get_help_text(self) -> str:
        if self.is_timer_active:
            return "[bold]Keys:[/bold] c: complete & end | e: end | q: quit"
        return "[bold]Keys:[/bold] 1-6: edit | r: roll | q: quit"

    def _refresh_help(self) -> None:
        if self.help_widget:
            self.help_widget.update(self._get_help_text())
            if self.is_timer_active:
                self.help_widget.add_class("dimmed")
            else:
                self.help_widget.remove_class("dimmed")

    def on_mount(self) -> None:
        if self.state.timer.running:
            self.right_panel.refresh_timer()
            self.right_panel.refresh_dimming()
            self._refresh_help()
            self.start_timer_worker()

    def on_unmount(self) -> None:
        save_state(self.state)

    def action_task_action(self, task_num: int) -> None:
        task_index = task_num - 1
        if not (0 <= task_index < MAX_TASKS):
            return
        if self.is_timer_active:
            self.notify("Timer active - press C to complete & end", severity="warning")
        else:
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
            self.task_list.refresh_tasks()
            save_state(self.state)

        self.run_worker(get_task_input())

    async def _animate_task_dice(self, options: list[int]) -> int:
        for i in range(20):
            value = roll_from_options(options)
            self.right_panel.set_task_dice_value(value)
            delay = 0.05 + (i * 0.01)
            await asyncio.sleep(delay)
        final = roll_from_options(options)
        self.right_panel.set_task_dice_value(final)
        return final

    async def _animate_duration_dice(self, options: list[int]) -> int:
        for i in range(20):
            value = roll_from_options(options)
            self.right_panel.set_duration_dice_value(value)
            delay = 0.05 + (i * 0.01)
            await asyncio.sleep(delay)
        final = roll_from_options(options)
        self.right_panel.set_duration_dice_value(final)
        return final

    @work(exclusive=True)
    async def action_roll(self) -> None:
        if self.is_timer_active:
            self.notify("Timer already running!", severity="warning")
            return

        incomplete = self.state.get_incomplete_task_indices()
        if not incomplete:
            self.notify("No incomplete tasks - add some first!", severity="warning")
            return

        task_options = [i + 1 for i in incomplete]
        task_roll = await self._animate_task_dice(task_options)
        task_index = task_roll - 1
        task_text = self.state.tasks[task_index].text
        self.notify(f"Task {task_roll}: {task_text}")

        await asyncio.sleep(0.8)

        duration_roll = await self._animate_duration_dice([1, 2, 3, 4, 5, 6])
        duration_minutes, is_break = _calculate_duration_and_break(duration_roll)

        if is_break:
            self.notify(f"Rolled {duration_roll}: Lucky! 10 minute break!")
            confirmed = await self.app.push_screen_wait(
                StartTimerConfirmScreen(duration_minutes, None, is_break=True)
            )
            if confirmed:
                self.state.timer.start(None, duration_minutes, is_break=True)
        else:
            self.notify(f"Rolled {duration_roll}: {duration_minutes} minutes")
            confirmed = await self.app.push_screen_wait(
                StartTimerConfirmScreen(duration_minutes, task_index, is_break=False, task_text=task_text)
            )
            if confirmed:
                self.state.timer.start(task_index, duration_minutes, is_break=False)

        if self.state.timer.running:
            self.start_timer_worker()
            self._refresh_help()
            self.right_panel.refresh_dimming()

        self.right_panel.refresh_timer()
        self.task_list.refresh_tasks()
        save_state(self.state)

    def start_timer_worker(self) -> None:
        if self.timer_worker is None:
            self.timer_worker = self.run_worker(self._timer_tick(), exclusive=True)

    async def _timer_tick(self) -> None:
        while self.state.timer.running and self.state.timer.remaining_seconds > 0:
            await asyncio.sleep(1)
            self.state.timer.tick()
            self.right_panel.refresh_timer()

            if self.state.timer.should_warn_ten_percent() and not self.state.timer.warned_ten_percent:
                self.state.timer.warned_ten_percent = True
                remaining = _format_timer_time(self.state.timer.remaining_seconds)
                _send_notification("Paper TODO", f"10% remaining: {remaining}", sound="Purr")
                self.notify(f"10% remaining: {remaining}", severity="warning")

            save_state(self.state)

        if self.state.timer.is_finished():
            task_info = "Break" if self.state.timer.is_break else f"Task {(self.state.timer.task_index or 0) + 1}"
            _send_notification("Paper TODO", f"Time's up! {task_info} complete.", sound="Glass")
            self.notify("Time's up!", severity="information")
            self.state.timer.reset()
            self.timer_worker = None
            self._refresh_help()
            self.right_panel.refresh_timer()
            self.right_panel.refresh_dimming()
            self.task_list.refresh_tasks()
            save_state(self.state)

    def action_complete_and_end(self) -> None:
        if not self.is_timer_active:
            self.notify("No active timer", severity="warning")
            return

        if self.state.timer.task_index is not None:
            task_index = self.state.timer.task_index
            self.state.tasks[task_index].completed = True
            self.notify(f"Task {task_index + 1} completed!")

        self._stop_timer()

    def action_end_timer(self) -> None:
        if not self.is_timer_active:
            self.notify("No active timer", severity="warning")
            return

        self.notify("Timer ended")
        self._stop_timer()

    def _stop_timer(self) -> None:
        if self.timer_worker:
            self.timer_worker.cancel()
            self.timer_worker = None

        self.state.timer.reset()
        self._refresh_help()
        self.right_panel.refresh_timer()
        self.right_panel.refresh_dimming()
        self.task_list.refresh_tasks()
        save_state(self.state)


class StartTimerConfirmScreen(ModalScreen[bool]):
    CSS = """
    StartTimerConfirmScreen {
        align: center middle;
    }

    #dialog {
        width: 60;
        height: auto;
        border: solid yellow;
        background: $surface;
        padding: 1;
    }

    #message {
        width: 100%;
        margin-bottom: 1;
        text-align: center;
    }

    #buttons {
        width: 100%;
        height: auto;
        align: center middle;
    }
    """

    def __init__(self, duration_minutes: int, task_index: int | None, is_break: bool, task_text: str | None = None) -> None:
        super().__init__()
        self.duration_minutes = duration_minutes
        self.task_index = task_index
        self.is_break = is_break
        self.task_text = task_text

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label("[bold yellow]Ready to start timer?[/bold yellow]")
            if self.is_break:
                yield Label(f"[cyan]{self.duration_minutes} minute break[/cyan]", id="message")
            else:
                task_display = self.task_text or "(empty)"
                yield Label(
                    f"[cyan]{self.duration_minutes} minutes[/cyan]\n[green]Task {(self.task_index or 0) + 1}: {task_display}[/green]",
                    id="message",
                )
            with Horizontal(id="buttons"):
                yield Button("Start Timer", variant="success", id="start")
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#start", Button).focus()

    @on(Button.Pressed, "#start")
    def start_timer(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#cancel")
    def cancel_timer(self) -> None:
        self.dismiss(False)


class TaskInputScreen(ModalScreen[tuple[str, str] | None]):
    CSS = """
    TaskInputScreen {
        align: center middle;
    }

    #dialog {
        width: 60;
        height: auto;
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

    def __init__(self, task_index: int, current_text: str, is_completed: bool) -> None:
        super().__init__()
        self.task_index = task_index
        self.current_text = current_text
        self.is_completed = is_completed

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
                if not self.is_completed:
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
