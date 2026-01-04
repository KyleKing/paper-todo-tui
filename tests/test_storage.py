import json
from pathlib import Path

import pytest

from paper_todo.models import AppState
from paper_todo.storage import _get_default_state_file, _parse_state_file, load_state, save_state


def test_get_default_state_file_with_xdg(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    state_file = _get_default_state_file()

    assert state_file == tmp_path / "paper-todo" / "state.json"
    assert state_file.parent.exists()


def test_get_default_state_file_no_xdg(tmp_path, monkeypatch):
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    state_file = _get_default_state_file()
    assert state_file == tmp_path / ".local" / "share" / "paper-todo" / "state.json"


def test_parse_state_file_valid():
    state = AppState()
    state.tasks[0].text = "Test task"

    parsed = _parse_state_file(state.model_dump_json())
    assert parsed.tasks[0].text == "Test task"


@pytest.mark.parametrize(
    "invalid_content",
    [
        "invalid json {",
        '{"invalid": "data"}',
    ],
    ids=["malformed-json", "wrong-schema"],
)
def test_parse_state_file_invalid(invalid_content):
    result = _parse_state_file(invalid_content)
    assert isinstance(result, AppState)
    assert len(result.tasks) == 6


def test_load_state_nonexistent(tmp_path):
    state = load_state(tmp_path / "nonexistent.json")
    assert isinstance(state, AppState)
    assert len(state.tasks) == 6


def test_load_state_existing(tmp_path):
    state_file = tmp_path / "state.json"
    original = AppState()
    original.tasks[0].text = "Test task"
    original.tasks[0].completed = True
    state_file.write_text(original.model_dump_json())

    loaded = load_state(state_file)
    assert loaded.tasks[0].text == "Test task"
    assert loaded.tasks[0].completed is True


def test_save_state(tmp_path):
    state_file = tmp_path / "state.json"
    state = AppState()
    state.tasks[0].text = "Save test"
    state.timer.task_index = 2

    save_state(state, state_file)

    assert state_file.exists()
    data = json.loads(state_file.read_text())
    assert data["tasks"][0]["text"] == "Save test"
    assert data["timer"]["task_index"] == 2


def test_load_save_roundtrip(tmp_path):
    state_file = tmp_path / "state.json"
    original = AppState()
    original.tasks[0].text = "Roundtrip test"
    original.tasks[1].completed = True
    original.timer.remaining_seconds = 300

    save_state(original, state_file)
    loaded = load_state(state_file)

    assert loaded.tasks[0].text == "Roundtrip test"
    assert loaded.tasks[1].completed is True
    assert loaded.timer.remaining_seconds == 300
