import random
from textwrap import dedent

DICE_FACES = {
    1: dedent("""\
        ┌─────────┐
        │         │
        │    ●    │
        │         │
        └─────────┘"""),
    2: dedent("""\
        ┌─────────┐
        │  ●      │
        │         │
        │      ●  │
        └─────────┘"""),
    3: dedent("""\
        ┌─────────┐
        │  ●      │
        │    ●    │
        │      ●  │
        └─────────┘"""),
    4: dedent("""\
        ┌─────────┐
        │  ●   ●  │
        │         │
        │  ●   ●  │
        └─────────┘"""),
    5: dedent("""\
        ┌─────────┐
        │  ●   ●  │
        │    ●    │
        │  ●   ●  │
        └─────────┘"""),
    6: dedent("""\
        ┌─────────┐
        │  ●   ●  │
        │  ●   ●  │
        │  ●   ●  │
        └─────────┘"""),
}


def roll_die() -> int:
    return random.randint(1, 6)


def get_dice_face(value: int) -> str:
    return DICE_FACES.get(value, DICE_FACES[1])
