"""
SoundPlayer - Sons curtos e opcionais de interação
"""

import logging
from pathlib import Path
import math
import struct
import wave

from PyQt6.QtCore import QUrl

try:
    from PyQt6.QtMultimedia import QSoundEffect
    MULTIMEDIA_AVAILABLE = True
except ImportError:
    MULTIMEDIA_AVAILABLE = False

logger = logging.getLogger(__name__)

SAMPLE_RATE = 44100

SOUNDS = {
    "pet": [(660, 70), (880, 90)],
    "feed": [(520, 80), (660, 70), (784, 110)],
    "bubble": [(700, 55)],
}


def _write_wav(path: Path, notes):
    """Gera um WAV mono 16-bit com envelope suave para não estalar."""
    frames = bytearray()

    for freq, duration_ms in notes:
        count = int(SAMPLE_RATE * duration_ms / 1000)
        fade = max(1, count // 6)

        for i in range(count):
            if i < fade:
                envelope = i / fade
            elif i > count - fade:
                envelope = (count - i) / fade
            else:
                envelope = 1.0

            sample = math.sin(2 * math.pi * freq * i / SAMPLE_RATE)
            value = int(sample * envelope * 0.28 * 32767)
            frames += struct.pack("<h", value)

    path.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(bytes(frames))


class SoundPlayer:
    """Toca os sons de interação, se estiverem habilitados."""

    def __init__(self, assets_path: Path, enabled: bool = False, volume: float = 0.25):
        self.assets_path = assets_path
        self.enabled = enabled
        self.volume = max(0.0, min(1.0, volume))
        self.effects = {}

        if MULTIMEDIA_AVAILABLE:
            self._prepare_sounds()

    def _prepare_sounds(self):
        """Gera os arquivos que ainda não existem e carrega os efeitos."""
        sounds_path = self.assets_path / "sounds"

        for name, notes in SOUNDS.items():
            file_path = sounds_path / f"{name}.wav"

            try:
                if not file_path.exists():
                    _write_wav(file_path, notes)

                effect = QSoundEffect()
                effect.setSource(QUrl.fromLocalFile(str(file_path)))
                effect.setVolume(self.volume)
                self.effects[name] = effect
            except Exception:
                logger.exception(f"Aviso: não foi possível preparar o som '{name}'")

    def play(self, name: str):
        """Toca um som, se habilitado e disponível."""
        if not self.enabled:
            return

        effect = self.effects.get(name)
        if effect is not None:
            try:
                effect.play()
            except Exception:
                pass

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))
        for effect in self.effects.values():
            try:
                effect.setVolume(self.volume)
            except Exception:
                pass