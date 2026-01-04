import pytest

from paper_todo.dice import DICE_FACES, get_dice_face, roll_die, roll_from_options


def test_roll_die_range():
    for _ in range(50):
        assert 1 <= roll_die() <= 6


@pytest.mark.parametrize(
    ("options", "check"),
    [
        ([1, 3, 5], lambda r, o: r in o),
        ([4], lambda r, _: r == 4),
        ([], lambda r, _: 1 <= r <= 6),
    ],
    ids=["multiple-options", "single-option", "empty-fallback"],
)
def test_roll_from_options(options, check):
    for _ in range(20):
        assert check(roll_from_options(options), options)


@pytest.mark.parametrize("value", range(1, 7))
def test_get_dice_face_valid(value):
    face = get_dice_face(value)
    assert isinstance(face, str)
    assert "┌" in face and "└" in face


@pytest.mark.parametrize("invalid_value", [0, 7, -1])
def test_get_dice_face_invalid(invalid_value):
    assert get_dice_face(invalid_value) == DICE_FACES[1]


def test_dice_faces_structure():
    assert len(DICE_FACES) == 6
    assert all(i in DICE_FACES for i in range(1, 7))
