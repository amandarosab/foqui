"""
ContextMonitor - Monitora atividade do sistema para comportamento reativo
"""

from datetime import datetime
import sys

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

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

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes


# Processos cuja simples presença já indica uma chamada (apps dedicados de call).
# Discord e Slack ficam de fora daqui: são usados o tempo todo sem chamada ativa,
# então só contam quando o título da janela também bate com CALL_TITLE_HINTS.
CALL_PROCESSES = {
    "zoom.exe", "teams.exe", "ms-teams.exe",
    "webexmta.exe", "webex.exe", "gotomeeting.exe",
    "skype.exe", "bluejeans.exe", "whereby.exe",
}

# Títulos que indicam chamada em andamento, em qualquer janela (não só a em foco) -
# assim o Foqui detecta a reunião mesmo se você estiver com outra janela aberta.
CALL_TITLE_HINTS = (
    "zoom meeting",
    "google meet", "meet.google.com",
    "microsoft teams", "teams meeting",
    "reunião", "chamada em andamento",
    "meet -", "webex meeting", "whereby", "jitsi", "huddle",
    "google hangouts", "hangouts meet",
    "you're presenting", "compartilhando sua tela", "apresentando",
    "in a meeting",
)

# Processos que só contam como reunião se o título também bater com um hint acima
CALL_PROCESSES_NEEDS_TITLE = {"discord.exe", "slack.exe", "chrome.exe", "msedge.exe", "firefox.exe"}


class ContextMonitor(QObject):
    """Monitora contexto do sistema e emite mudanças."""

    # Signal emitido quando o contexto muda
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

        # Estado atual
        self.last_keyboard_activity = datetime.now()
        self.last_mouse_activity = datetime.now()
        self.typing_active = False
        self.mouse_active = False
        self.in_meeting = False

        # Contadores de atividade recente
        self.recent_keystrokes = 0
        self.recent_mouse_moves = 0

        # Listeners (pynput)
        self.keyboard_listener = None
        self.mouse_listener = None

        # Timer para checar contexto periodicamente
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self._check_context)

        # Flag de execução
        self.running = False

    def start(self):
        """Inicia o monitoramento."""
        self.running = True

        # Inicia listeners de input
        if PYNPUT_AVAILABLE:
            self._start_input_listeners()

        # Inicia timer de verificação
        self.check_timer.start(self.check_interval_ms)

    def stop(self):
        """Para o monitoramento."""
        self.running = False

        # Para timer
        self.check_timer.stop()

        # Para listeners
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None

    def set_detect_meetings(self, enabled: bool):
        """Liga/desliga a detecção de reuniões."""
        self.detect_meetings = enabled
        if not enabled:
            self.in_meeting = False

    def _start_input_listeners(self):
        """Inicia listeners de teclado e mouse."""
        # Keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press
        )
        self.keyboard_listener.start()

        # Mouse listener
        self.mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click
        )
        self.mouse_listener.start()

    def _on_key_press(self, key):
        """Callback quando uma tecla é pressionada."""
        self.last_keyboard_activity = datetime.now()
        self.recent_keystrokes += 1

    def _on_mouse_move(self, x, y):
        """Callback quando o mouse move."""
        self.last_mouse_activity = datetime.now()
        self.recent_mouse_moves += 1

    def _on_mouse_click(self, x, y, button, pressed):
        """Callback quando o mouse é clicado."""
        if pressed:
            self.last_mouse_activity = datetime.now()

    # === Detecção de reunião (best effort, só Windows) ===

    def _window_process_name(self, user32, hwnd) -> str:
        """Nome do processo dono de uma janela, em minúsculas."""
        if not PSUTIL_AVAILABLE:
            return ""

        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        try:
            return psutil.Process(pid.value).name().lower()
        except Exception:
            return ""

    def _window_indicates_meeting(self, title: str, process_name: str) -> bool:
        """Decide se uma janela (título + processo) indica chamada em andamento."""
        lowered_title = title.lower() if title else ""
        title_matches = any(hint in lowered_title for hint in CALL_TITLE_HINTS)

        if title_matches:
            return True

        if process_name and process_name in CALL_PROCESSES:
            return True

        return False

    def _scan_windows_for_meeting(self) -> bool:
        """
        Varre todas as janelas visíveis do sistema em busca de uma chamada.
        Não depende de qual janela está em foco: se você minimizar o Zoom para
        anotar algo em outro lugar, a reunião continua sendo reconhecida.
        """
        user32 = ctypes.windll.user32
        found = {"meeting": False}

        WNDENUMPROC = ctypes.WINFUNCTYPE(
            wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
        )

        def callback(hwnd, lparam):
            if not user32.IsWindowVisible(hwnd):
                return True

            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True

            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value or ""

            process_name = self._window_process_name(user32, hwnd)

            if process_name in CALL_PROCESSES_NEEDS_TITLE:
                # Apps de uso geral (navegador, Discord, Slack) só contam
                # como reunião se o título também indicar uma chamada.
                if any(hint in title.lower() for hint in CALL_TITLE_HINTS):
                    found["meeting"] = True
                    return False
                return True

            if self._window_indicates_meeting(title, process_name):
                found["meeting"] = True
                return False

            return True

        try:
            user32.EnumWindows(WNDENUMPROC(callback), 0)
        except Exception:
            return False

        return found["meeting"]

    def _foreground_is_fullscreen(self) -> bool:
        """Se a janela em foco cobre o monitor inteiro."""
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()

        if not hwnd:
            return False

        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)

        return (
            (rect.right - rect.left) >= screen_w and
            (rect.bottom - rect.top) >= screen_h
        )

    def _detect_meeting(self) -> bool:
        """
        Tenta identificar uma chamada em andamento.
        Falha de forma silenciosa: se não der para saber, assume que não há.
        """
        if not self.detect_meetings or not IS_WINDOWS:
            return False

        try:
            if self._scan_windows_for_meeting():
                return True

            # Tela cheia também pede o comportamento "presente e discreto"
            return self._foreground_is_fullscreen()
        except Exception:
            return False

    def _check_context(self):
        """Verifica contexto atual e emite mudanças."""
        now = datetime.now()

        # Calcula tempo idle
        keyboard_idle = (now - self.last_keyboard_activity).total_seconds()
        mouse_idle = (now - self.last_mouse_activity).total_seconds()
        idle_seconds = min(keyboard_idle, mouse_idle)
        idle_minutes = idle_seconds / 60

        # Detecta se está digitando ativamente (muitas teclas recentes)
        typing_active = self.recent_keystrokes > 10

        # Detecta se mouse está ativo
        mouse_active = self.recent_mouse_moves > 5

        # Reseta contadores
        self.recent_keystrokes = 0
        self.recent_mouse_moves = 0

        # Conta processos ativos (indicador grosseiro de carga de trabalho)
        window_count = 0
        if PSUTIL_AVAILABLE:
            try:
                window_count = len(psutil.pids())
            except:
                pass

        # Verifica se é horário noturno
        current_hour = now.hour
        is_night = False
        if self.night_mode_start > self.night_mode_end:
            # Ex: 22h até 6h (cruza meia-noite)
            is_night = current_hour >= self.night_mode_start or current_hour < self.night_mode_end
        else:
            # Ex: 23h até 23h (não faz sentido, mas trata)
            is_night = self.night_mode_start <= current_hour < self.night_mode_end

        # Reunião / call em andamento
        in_meeting = self._detect_meeting()

        # Monta contexto
        context = {
            "typing_active": typing_active,
            "mouse_active": mouse_active,
            "idle_minutes": idle_minutes,
            "window_count": window_count,
            "is_night": is_night,
            "in_meeting": in_meeting,
            "timestamp": now.isoformat()
        }

        # Emite mudança
        self.context_changed.emit(context)

        # Atualiza estado interno
        self.typing_active = typing_active
        self.mouse_active = mouse_active
        self.in_meeting = in_meeting

    def get_current_context(self) -> dict:
        """Retorna contexto atual sem emitir signal."""
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
