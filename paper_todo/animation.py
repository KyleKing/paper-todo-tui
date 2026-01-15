import asyncio
from dataclasses import dataclass
from typing import Callable

KNIGHT_RIDER_TOTAL_MS = 3200
KNIGHT_RIDER_INITIAL_DELAY_MS = 34
KNIGHT_RIDER_FINAL_DELAY_MS = 250
DECELERATION_EXPONENT = 1.5

SLIDE_DURATION_MS = 400
FADE_DURATION_MS = 250
RAINBOW_CYCLE_MS = 100


@dataclass(frozen=True)
class AnimationFrame:
    index: int
    delay_ms: float


def generate_knight_rider_frames(
    positions: list[int],
    *,
    final_index: int | None = None,
    num_cycles: int = 3,
    initial_delay_ms: float = KNIGHT_RIDER_INITIAL_DELAY_MS,
    final_delay_ms: float = KNIGHT_RIDER_FINAL_DELAY_MS,
    exponent: float = DECELERATION_EXPONENT,
) -> list[AnimationFrame]:
    if not positions:
        return []

    if final_index is None:
        import random
        final_index = random.choice(positions)

    sequence = []
    for _ in range(num_cycles):
        sequence.extend(positions)
        if len(positions) > 2:
            sequence.extend(reversed(positions[1:-1]))

    final_pos_in_sequence = None
    for i in range(len(sequence) - 1, -1, -1):
        if sequence[i] == final_index:
            final_pos_in_sequence = i
            break

    if final_pos_in_sequence is not None:
        sequence = sequence[: final_pos_in_sequence + 1]
    else:
        sequence.append(final_index)

    num_frames = len(sequence)
    if num_frames == 0:
        return []

    frames = []
    for i, pos in enumerate(sequence):
        progress = i / max(num_frames - 1, 1)
        delay = initial_delay_ms + (final_delay_ms - initial_delay_ms) * (progress**exponent)
        frames.append(AnimationFrame(index=pos, delay_ms=delay))

    return frames


async def run_animation(
    frames: list[AnimationFrame],
    on_frame: Callable[[int], None],
) -> int:
    if not frames:
        return -1

    for frame in frames:
        on_frame(frame.index)
        await asyncio.sleep(frame.delay_ms / 1000)

    return frames[-1].index


def generate_slide_frames(
    start_position: float,
    end_position: float,
    *,
    duration_ms: float = SLIDE_DURATION_MS,
    fps: int = 30,
) -> list[float]:
    num_frames = max(1, int(duration_ms / 1000 * fps))
    positions = []
    for i in range(num_frames + 1):
        progress = i / num_frames
        eased = 1 - (1 - progress) ** 2
        pos = start_position + (end_position - start_position) * eased
        positions.append(pos)
    return positions


RAINBOW_COLORS = [
    "#ed8796",
    "#f5a97f",
    "#eed49f",
    "#a6da95",
    "#8aadf4",
    "#c6a0f6",
]


def get_rainbow_color(offset: int) -> str:
    return RAINBOW_COLORS[offset % len(RAINBOW_COLORS)]
