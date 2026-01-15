import asyncio
from enum import StrEnum

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Label, Static

from paper_todo.animation import (
    RAINBOW_CYCLE_MS,
    generate_knight_rider_frames,
    generate_slide_frames,
    get_rainbow_color,
    run_animation,
)
from paper_todo.models import AppState
from paper_todo.theme import ThemeMode, get_palette


class ProgressBarState(StrEnum):
    IDLE = "idle"
    SELECTING = "selecting"
    TRANSITIONING = "transitioning"
    RUNNING = "running"
    CELEBRATION = "celebration"


DURATION_LABELS = ["1", "2", "3", "4", "5", "★"]
DURATION_MINUTES = [10, 20, 30, 40, 50, 10]


class ProgressBarTimer(Static):
    def __init__(self, state: AppState, theme_mode: ThemeMode = ThemeMode.DARK) -> None:
        super().__init__()
        self.app_state = state
        self.theme_mode = theme_mode
        self._bar_state = ProgressBarState.IDLE
        self._selected_index: int | None = None
        self._active_index: int | None = None
        self._fill_percent: float = 0.0
        self._is_break: bool = False
        self._rainbow_offset: int = 0
        self._celebration_task: asyncio.Task | None = None

    def compose(self) -> ComposeResult:
        with Horizontal(id="progress-container"):
            for i, label in enumerate(DURATION_LABELS):
                yield Label(
                    f" {label} ",
                    id=f"duration-{i}",
                    classes="duration-indicator",
                )
        yield Static("", id="progress-bar")
        yield Static("", id="progress-fill")
        yield Label("", id="timer-status")

    def on_mount(self) -> None:
        self._refresh_display()

    def _refresh_display(self) -> None:
        for i in range(6):
            indicator = self.query_one(f"#duration-{i}", Label)
            indicator.remove_class("active", "faded")

            if self._bar_state == ProgressBarState.IDLE:
                pass
            elif self._active_index == i:
                indicator.add_class("active")
            elif self._bar_state in (ProgressBarState.TRANSITIONING, ProgressBarState.RUNNING):
                if self._selected_index is not None and i != self._selected_index:
                    indicator.add_class("faded")

        self._update_status_text()
        self._update_fill()

    def _update_status_text(self) -> None:
        status = self.query_one("#timer-status", Label)
        match self._bar_state:
            case ProgressBarState.IDLE:
                status.update("Press S to start")
            case ProgressBarState.SELECTING:
                status.update("Selecting duration...")
            case ProgressBarState.TRANSITIONING:
                status.update("Starting timer...")
            case ProgressBarState.RUNNING:
                remaining = self.app_state.timer.remaining_seconds
                minutes = remaining // 60
                seconds = remaining % 60
                task_info = "Break" if self._is_break else f"Task {(self.app_state.timer.task_index or 0) + 1}"
                status.update(f"{task_info}: {minutes:02d}:{seconds:02d}")
            case ProgressBarState.CELEBRATION:
                status.update("Complete!")

    def _update_fill(self) -> None:
        fill = self.query_one("#progress-fill", Static)
        bar = self.query_one("#progress-bar", Static)

        try:
            bar_width = bar.size.width
        except Exception:
            bar_width = 60

        if bar_width <= 0:
            bar_width = 60

        filled_width = int(bar_width * self._fill_percent)

        if self._bar_state == ProgressBarState.CELEBRATION or self._is_break:
            fill_chars = []
            for i in range(filled_width):
                color = get_rainbow_color(i + self._rainbow_offset)
                fill_chars.append(f"[{color}]█[/]")
            fill.update("".join(fill_chars))
        else:
            palette = get_palette(self.theme_mode)
            if filled_width > 0:
                fill.update(f"[{palette.blue}]{'█' * filled_width}[/]")
            else:
                fill.update("")

    async def animate_duration_selection(self) -> int:
        self._bar_state = ProgressBarState.SELECTING
        self._refresh_display()

        positions = list(range(6))
        frames = generate_knight_rider_frames(positions, num_cycles=2)

        def on_frame(idx: int) -> None:
            self._active_index = idx
            self._refresh_display()

        final_index = await run_animation(frames, on_frame)
        self._selected_index = final_index
        self._active_index = final_index
        return final_index

    async def transition_to_running(self, selected_index: int, *, is_break: bool) -> None:
        self._bar_state = ProgressBarState.TRANSITIONING
        self._selected_index = selected_index
        self._is_break = is_break
        self._refresh_display()

        for i in range(6):
            if i != selected_index:
                indicator = self.query_one(f"#duration-{i}", Label)
                indicator.add_class("faded")

        await asyncio.sleep(0.3)

        slide_frames = generate_slide_frames(
            start_position=selected_index / 5,
            end_position=1.0,
        )

        selected_indicator = self.query_one(f"#duration-{selected_index}", Label)
        for _ in slide_frames:
            await asyncio.sleep(0.016)

        self._bar_state = ProgressBarState.RUNNING
        self._fill_percent = 0.0
        self._refresh_display()

        if is_break:
            self._start_rainbow_animation()

    def _start_rainbow_animation(self) -> None:
        async def rainbow_loop() -> None:
            try:
                while self._bar_state in (ProgressBarState.RUNNING, ProgressBarState.CELEBRATION) and self._is_break:
                    self._rainbow_offset += 1
                    if self.is_mounted:
                        self._update_fill()
                    await asyncio.sleep(RAINBOW_CYCLE_MS / 1000)
            except Exception:
                pass

        if self._celebration_task:
            self._celebration_task.cancel()
        self._celebration_task = asyncio.create_task(rainbow_loop())

    def update_fill(self, elapsed_seconds: int, total_seconds: int) -> None:
        if total_seconds > 0:
            self._fill_percent = min(1.0, elapsed_seconds / total_seconds)
        else:
            self._fill_percent = 0.0
        self._update_fill()
        self._update_status_text()

    async def celebrate(self) -> None:
        self._bar_state = ProgressBarState.CELEBRATION
        self._is_break = True
        self._fill_percent = 1.0
        self._refresh_display()
        self._start_rainbow_animation()

        await asyncio.sleep(3.0)

        self.reset()

    def reset(self) -> None:
        if self._celebration_task:
            self._celebration_task.cancel()
            self._celebration_task = None

        self._bar_state = ProgressBarState.IDLE
        self._selected_index = None
        self._active_index = None
        self._fill_percent = 0.0
        self._is_break = False
        self._rainbow_offset = 0
        self._refresh_display()

    def set_theme_mode(self, mode: ThemeMode) -> None:
        self.theme_mode = mode
        self._update_fill()
