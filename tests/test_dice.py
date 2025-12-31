import pytest

from paper_todo.dice import DICE_FACES, get_dice_face, roll_die


def test_roll_die_range():
    for _ in range(100):
        roll = roll_die()
        assert 1 <= roll <= 6


def test_get_dice_face_valid():
    for value in range(1, 7):
        face = get_dice_face(value)
        assert isinstance(face, str)
        assert len(face) > 0
        assert "┌" in face
        assert "└" in face


def test_get_dice_face_invalid():
    face = get_dice_face(0)
    assert face == DICE_FACES[1]

    face = get_dice_face(7)
    assert face == DICE_FACES[1]


def test_dice_faces_all_present():
    assert len(DICE_FACES) == 6
    for i in range(1, 7):
        assert i in DICE_FACES
