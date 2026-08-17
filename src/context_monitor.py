"""
ContextMonitor - Monitora atividade do sistema para comportamento reativo
"""

from datetime import datetime
import sys

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from os_monitors import get_os_monitor

try:
    from pynput import keyboard, mouse
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class ContextMonitor(QObject):
    """Monitora contexto do sistema e emite mudanças."""

    context_changed = pyqtSignal(dict)

    def __init__(
        self,
        night_mode_start: int = 22,
        night_mode_end: int = 6,
        check_interval_ms: int = 5000,
        detect_meetings: bool = True
    ):
        super().__init__()

        self.night_mode_start = night_mode_start
        self.night_mode_end = night_mode_end
        self.check_interval_ms = check_interval_ms
        self.detect_meetings = detect_meetings

        self.os_monitor = get_os_monitor()

        self.last_keyboard_activity = datetime.now()
        self.last_mouse_activity = datetime.now()
        self.typing_active = False
        self.mouse_active = False
        self.in_meeting = False

        self.recent_keystrokes = 0
        self.recent_mouse_moves = 0

        self.keyboard_listener = None
        self.mouse_listener = None

        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self._check_context)

        self.running = False

    def start(self):
        self.running = True
        if PYNPUT_AVAILABLE:
            self._start_input_listeners()
        self.check_timer.start(self.check_interval_ms)

    def stop(self):
        self.running = False
        self.check_timer.stop()

        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None

    def set_detect_meetings(self, enabled: bool):
        self.detect_meetings = enabled
        if not enabled:
            self.in_meeting = False

    def _start_input_listeners(self):
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press
        )
        self.keyboard_listener.start()

        self.mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click
        )
        self.mouse_listener.start()

    def _on_key_press(self, key):
        self.last_keyboard_activity = datetime.now()
        self.recent_keystrokes += 1

    def _on_mouse_move(self, x, y):
        self.last_mouse_activity = datetime.now()
        self.recent_mouse_moves += 1

    def _on_mouse_click(self, x, y, button, pressed):
        if pressed:
            self.last_mouse_activity = datetime.now()

    def _detect_meeting(self) -> bool:
        if not self.detect_meetings:
            return False
        return self.os_monitor.is_in_meeting()

    def _check_context(self):
        now = datetime.now()

        keyboard_idle = (now - self.last_keyboard_activity).total_seconds()
        mouse_idle = (now - self.last_mouse_activity).total_seconds()
        idle_seconds = min(keyboard_idle, mouse_idle)
        idle_minutes = idle_seconds / 60

        typing_active = self.recent_keystrokes > 10
        mouse_active = self.recent_mouse_moves > 5

        self.recent_keystrokes = 0
        self.recent_mouse_moves = 0

        window_count = 0
        if PSUTIL_AVAILABLE:
            try:
                window_count = len(psutil.pids())
            except:
                pass

        current_hour = now.hour
        is_night = False
        if self.night_mode_start > self.night_mode_end:
            is_night = current_hour >= self.night_mode_start or current_hour < self.night_mode_end
        else:
            is_night = self.night_mode_start <= current_hour < self.night_mode_end

        in_meeting = self._detect_meeting()

        context = {
            "typing_active": typing_active,
            "mouse_active": mouse_active,
            "idle_minutes": idle_minutes,
            "window_count": window_count,
            "is_night": is_night,
            "in_meeting": in_meeting,
            "timestamp": now.isoformat()
        }

        self.context_changed.emit(context)

        self.typing_active = typing_active
        self.mouse_active = mouse_active
        self.in_meeting = in_meeting

    def get_current_context(self) -> dict:
        now = datetime.now()

        keyboard_idle = (now - self.last_keyboard_activity).total_seconds()
        mouse_idle = (now - self.last_mouse_activity).total_seconds()
        idle_minutes = min(keyboard_idle, mouse_idle) / 60

        current_hour = now.hour
        if self.night_mode_start > self.night_mode_end:
            is_night = (
                current_hour >= self.night_mode_start or
                current_hour < self.night_mode_end
            )
        else:
            is_night = self.night_mode_start <= current_hour < self.night_mode_end

        return {
            "typing_active": self.typing_active,
            "mouse_active": self.mouse_active,
            "idle_minutes": idle_minutes,
            "window_count": 0,
            "is_night": is_night,
            "in_meeting": self.in_meeting,
            "timestamp": now.isoformat()
        }