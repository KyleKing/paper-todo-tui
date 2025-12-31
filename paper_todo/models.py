from datetime import datetime

from pydantic import BaseModel, Field

MAX_TASKS = 6
TASK_CHAR_LIMIT = 60


class Task(BaseModel):
    text: str = Field(default="", max_length=TASK_CHAR_LIMIT)
    completed: bool = False

    def toggle(self) -> None:
        self.completed = not self.completed


def _is_task_incomplete(task: Task) -> bool:
    return bool(task.text and not task.completed)


class TimerState(BaseModel):
    task_index: int | None = None
    duration_seconds: int = 0
    remaining_seconds: int = 0
    is_break: bool = False
    running: bool = False
    start_time: datetime | None = None

    def start(self, task_index: int | None, duration_minutes: int, is_break: bool = False) -> None:
        self.task_index = task_index
        self.duration_seconds = duration_minutes * 60
        self.remaining_seconds = self.duration_seconds
        self.is_break = is_break
        self.running = True
        self.start_time = datetime.now()

    def pause(self) -> None:
        self.running = False

    def resume(self) -> None:
        if self.remaining_seconds > 0:
            self.running = True
            self.start_time = datetime.now()

    def tick(self) -> None:
        if self.running and self.remaining_seconds > 0:
            self.remaining_seconds -= 1

    def is_finished(self) -> bool:
        return self.remaining_seconds <= 0

    def reset(self) -> None:
        self.task_index = None
        self.duration_seconds = 0
        self.remaining_seconds = 0
        self.is_break = False
        self.running = False
        self.start_time = None


class AppState(BaseModel):
    tasks: list[Task] = Field(default_factory=lambda: [Task() for _ in range(MAX_TASKS)])
    timer: TimerState = Field(default_factory=TimerState)

    def get_incomplete_task_indices(self) -> list[int]:
        return [i for i, task in enumerate(self.tasks) if _is_task_incomplete(task)]


def get_incomplete_task_indices(tasks: list[Task]) -> list[int]:
    return [i for i, task in enumerate(tasks) if _is_task_incomplete(task)]
