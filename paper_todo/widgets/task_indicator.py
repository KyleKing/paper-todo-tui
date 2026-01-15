from enum import StrEnum
from textwrap import dedent

from textual.widgets import Static


class IndicatorState(StrEnum):
    DIM = "dim"
    BRIGHT = "bright"
    COMPLETED_DIM = "completed-dim"
    INACTIVE = "inactive"


def _render_indicator_box(number: int) -> str:
    return dedent(f"""\
        ╭───╮
        │ {number} │
        ╰───╯""")


class TaskIndicator(Static):
    def __init__(self, number: int, *, state: IndicatorState = IndicatorState.DIM) -> None:
        super().__init__(_render_indicator_box(number))
        self.number = number
        self._state = state

    def on_mount(self) -> None:
        self._apply_state()

    @property
    def state(self) -> IndicatorState:
        return self._state

    def set_state(self, state: IndicatorState) -> None:
        self._state = state
        self._apply_state()

    def _apply_state(self) -> None:
        self.remove_class("dim", "bright", "completed-dim", "inactive")
        self.add_class(self._state.value)
