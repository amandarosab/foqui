"""
Testes do AnimationManager - garante que cada animação realmente se move
(frames distintos) e que as animações temáticas existem e têm mais de um frame.
"""

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtWidgets import QApplication

from animation import AnimationManager


@pytest.fixture(scope="module", autouse=True)
def qapp():
    instance = QApplication.instance()
    return instance if instance else QApplication(sys.argv)


PET_TYPES = ["frog", "rat", "cat", "robot"]

THEMED_ANIMATIONS = ["crochet", "music", "coffee", "apple", "chocolate"]


def _frame_bytes(pixmap):
    image = pixmap.toImage()
    return image.bits().asstring(image.sizeInBytes())


class TestAnimationManager:
    """Cada animação deve ser uma sequência de poses diferentes, não uma imagem parada."""

    @pytest.mark.parametrize("pet_type", PET_TYPES)
    def test_every_animation_actually_animates(self, pet_type):
        """Nenhuma animação pode ter todos os frames idênticos."""
        manager = AnimationManager(Path(__file__).parent.parent / "assets" / "pets" / pet_type)

        for name, data in manager.animations.items():
            assert len(data.frames) >= 2, f"{name} tem só {len(data.frames)} frame(s)"

            distinct = {_frame_bytes(frame) for frame in data.frames}
            assert len(distinct) > 1, f"{name} tem {len(data.frames)} frames mas todos são iguais"

    @pytest.mark.parametrize("animation_name", THEMED_ANIMATIONS)
    def test_themed_animations_exist(self, animation_name):
        """crochê, música, café, maçã e chocolate precisam estar disponíveis."""
        manager = AnimationManager(Path(__file__).parent.parent / "assets" / "pets" / "frog")

        assert animation_name in manager.animations
        assert manager.animations[animation_name].loop is False

    def test_advance_and_reset_cycle_through_frames(self):
        manager = AnimationManager(Path(__file__).parent.parent / "assets" / "pets" / "frog")

        manager.reset_animation("crochet")
        first = manager.get_frame("crochet")
        manager.advance_frame("crochet")
        second = manager.get_frame("crochet")

        assert _frame_bytes(first) != _frame_bytes(second)
