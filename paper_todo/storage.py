import json
import os
from pathlib import Path

from paper_todo.models import AppState


def _get_default_state_file() -> Path:
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        base_dir = Path(xdg_data_home)
    else:
        base_dir = Path.home() / ".local" / "share"

    state_dir = base_dir / "paper-todo"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / "state.json"


DEFAULT_STATE_FILE = _get_default_state_file()


def _parse_state_file(content: str) -> AppState:
    try:
        data = json.loads(content)
        return AppState.model_validate(data)
    except (json.JSONDecodeError, ValueError):
        return AppState()


def load_state(state_file: Path = DEFAULT_STATE_FILE) -> AppState:
    return _parse_state_file(state_file.read_text()) if state_file.exists() else AppState()


def save_state(state: AppState, state_file: Path = DEFAULT_STATE_FILE) -> None:
    state_file.write_text(state.model_dump_json(indent=2))
