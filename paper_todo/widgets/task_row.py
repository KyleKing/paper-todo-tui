from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Label

from paper_todo.models import Task
from paper_todo.widgets.task_indicator import IndicatorState, TaskIndicator


class TaskRow(Horizontal):
    def __init__(self, index: int, task_model: Task) -> None:
        super().__init__()
        self.index = index
        self._task_data = task_model
        self.indicator: TaskIndicator | None = None

    @property
    def task_model(self) -> Task:
        return self._task_data

    @task_model.setter
    def task_model(self, value: Task) -> None:
        self._task_data = value

    def compose(self) -> ComposeResult:
        initial_state = IndicatorState.INACTIVE if self._task_data.completed else IndicatorState.DIM
        self.indicator = TaskIndicator(self.index + 1, state=initial_state)
        yield self.indicator
        yield Label(self._format_text(), classes="task-text")

    def _format_text(self) -> str:
        return self._task_data.text or "(empty)"

    def refresh_display(self, *, is_active: bool = False) -> None:
        label = self.query_one(".task-text", Label)
        text = self._task_data.text or "(empty)"

        label.update(text)
        if self._task_data.completed:
            label.add_class("completed")
            label.remove_class("active")
        elif is_active:
            label.remove_class("completed")
            label.add_class("active")
        else:
            label.remove_class("completed", "active")

        if self.indicator:
            if self._task_data.completed:
                self.indicator.set_state(IndicatorState.INACTIVE)
            elif is_active:
                self.indicator.set_state(IndicatorState.BRIGHT)
            else:
                self.indicator.set_state(IndicatorState.DIM)

    def set_indicator_state(self, state: IndicatorState) -> None:
        if self.indicator:
            self.indicator.set_state(state)
