from enum import StrEnum
from textwrap import dedent

from textual.widgets import Static


class DurationState(StrEnum):
    DIM = "dim"
    BRIGHT = "bright"
    FADED = "faded"


def _render_indicator_box(label: str) -> str:
    return dedent(f"""\
        ╭───╮
        │ {label} │
        ╰───╯""")


class DurationIndicator(Static):
    def __init__(self, label: str, *, state: DurationState = DurationState.DIM) -> None:
        super().__init__(_render_indicator_box(label))
        self.label = label
        self._state = state

    def on_mount(self) -> None:
        self._apply_state()

    @property
    def state(self) -> DurationState:
        return self._state

    def set_state(self, state: DurationState) -> None:
        self._state = state
        self._apply_state()

    def _apply_state(self) -> None:
        self.remove_class("dim", "bright", "faded")
        self.add_class(self._state.value)
