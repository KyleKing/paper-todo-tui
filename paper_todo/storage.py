import json
from pathlib import Path

from paper_todo.models import AppState


DEFAULT_STATE_FILE = Path.home() / ".paper_todo_state.json"


def load_state(state_file: Path = DEFAULT_STATE_FILE) -> AppState:
    if not state_file.exists():
        return AppState()

    try:
        data = json.loads(state_file.read_text())
        return AppState.model_validate(data)
    except (json.JSONDecodeError, ValueError):
        return AppState()


def save_state(state: AppState, state_file: Path = DEFAULT_STATE_FILE) -> None:
    state_file.write_text(state.model_dump_json(indent=2))
