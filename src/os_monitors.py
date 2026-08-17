from abc import ABC, abstractmethod
import sys

# Constantes extraídas de context_monitor.py
CALL_PROCESSES = {
    "zoom.exe", "teams.exe", "ms-teams.exe", "webexmta.exe", 
    "webex.exe", "gotomeeting.exe", "skype.exe", "bluejeans.exe", "whereby.exe",
}

CALL_TITLE_HINTS = (
    "zoom meeting", "google meet", "meet.google.com", "microsoft teams", 
    "teams meeting", "reunião", "chamada em andamento", "meet -", 
    "webex meeting", "whereby", "jitsi", "huddle", "google hangouts", 
    "hangouts meet", "you're presenting", "compartilhando sua tela", 
    "apresentando", "in a meeting",
)

CALL_PROCESSES_NEEDS_TITLE = {"discord.exe", "slack.exe", "chrome.exe", "msedge.exe", "firefox.exe"}

class OSContextMonitor(ABC):
    @abstractmethod
    def is_in_meeting(self) -> bool:
        pass

class WindowsMonitor(OSContextMonitor):
    def __init__(self):
        import ctypes
        from ctypes import wintypes
        self.ctypes = ctypes
        self.wintypes = wintypes
        
        try:
            import psutil
            self.psutil = psutil
        except ImportError:
            self.psutil = None

    def _window_process_name(self, user32, hwnd) -> str:
        if not self.psutil:
            return ""
        pid = self.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, self.ctypes.byref(pid))
        try:
            return self.psutil.Process(pid.value).name().lower()
        except Exception:
            return ""

    def _window_indicates_meeting(self, title: str, process_name: str) -> bool:
        lowered_title = title.lower() if title else ""
        if any(hint in lowered_title for hint in CALL_TITLE_HINTS): return True
        if process_name and process_name in CALL_PROCESSES: return True
        return False

    def _scan_windows_for_meeting(self) -> bool:
        user32 = self.ctypes.windll.user32
        found = {"meeting": False}
        WNDENUMPROC = self.ctypes.WINFUNCTYPE(self.wintypes.BOOL, self.wintypes.HWND, self.wintypes.LPARAM)

        def callback(hwnd, lparam):
            if not user32.IsWindowVisible(hwnd): return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0: return True
            
            buffer = self.ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value or ""
            process_name = self._window_process_name(user32, hwnd)

            if process_name in CALL_PROCESSES_NEEDS_TITLE:
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
        user32 = self.ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd: return False
        
        rect = self.wintypes.RECT()
        user32.GetWindowRect(hwnd, self.ctypes.byref(rect))
        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)
        
        return (rect.right - rect.left) >= screen_w and (rect.bottom - rect.top) >= screen_h

    def is_in_meeting(self) -> bool:
        try:
            if self._scan_windows_for_meeting(): return True
            return self._foreground_is_fullscreen()
        except Exception:
            return False

class DummyMonitor(OSContextMonitor):
    def is_in_meeting(self) -> bool:
        return False

def get_os_monitor() -> OSContextMonitor:
    if sys.platform == "win32":
        return WindowsMonitor()
    return DummyMonitor()