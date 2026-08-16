"""
HotkeyManager - Gerencia atalhos de teclado globais

Os atalhos são detectados em uma thread do pynput. Nada de tocar na UI a
partir dela: o disparo vira um signal, que o Qt entrega na thread principal.
"""

from typing import Dict

from PyQt6.QtCore import QObject, pyqtSignal

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False


class HotkeyManager(QObject):
    """Gerencia atalhos de teclado globais."""

    # Signal emitido (na thread principal) quando um atalho é acionado
    hotkey_triggered = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        # nome da ação -> conjunto de teclas
        self.hotkeys: Dict[str, frozenset] = {}
        self.listener = None
        self.current_keys = set()
        self.running = False

    def register_hotkey(self, name: str, hotkey: str):
        """
        Registra um atalho global.

        Args:
            name: identificador da ação (ex: "toggle_visibility")
            hotkey: combinação (ex: "ctrl+shift+f")
        """
        if not hotkey:
            return
        self.hotkeys[name] = self._normalize_hotkey(hotkey)

    def unregister_hotkey(self, name: str):
        """Remove um atalho registrado."""
        self.hotkeys.pop(name, None)

    def clear_hotkeys(self):
        """Remove todos os atalhos (usado ao reaplicar configurações)."""
        self.hotkeys.clear()
        self.current_keys.clear()

    def _normalize_hotkey(self, hotkey: str) -> frozenset:
        """
        Normaliza string de hotkey para um frozenset de teclas.
        Ex: "ctrl+shift+f" -> frozenset({'ctrl', 'shift', 'f'})
        """
        parts = hotkey.lower().replace(" ", "").split("+")
        return frozenset(p for p in parts if p)

    def start(self):
        """Inicia o listener de hotkeys."""
        if not PYNPUT_AVAILABLE:
            print("Aviso: pynput não disponível, hotkeys desabilitados")
            return

        if self.listener is not None:
            return

        self.running = True
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()

    def stop(self):
        """Para o listener de hotkeys."""
        self.running = False
        if self.listener:
            self.listener.stop()
            self.listener = None

    def _on_press(self, key):
        """Callback quando uma tecla é pressionada."""
        key_name = self._get_key_name(key)
        if key_name:
            self.current_keys.add(key_name)
            self._check_hotkeys()

    def _on_release(self, key):
        """Callback quando uma tecla é solta."""
        key_name = self._get_key_name(key)
        if key_name:
            self.current_keys.discard(key_name)

    def _get_key_name(self, key):
        """Converte tecla pynput para string normalizada."""
        try:
            return key.char.lower()
        except AttributeError:
            key_map = {
                keyboard.Key.ctrl_l: 'ctrl',
                keyboard.Key.ctrl_r: 'ctrl',
                keyboard.Key.shift_l: 'shift',
                keyboard.Key.shift_r: 'shift',
                keyboard.Key.alt_l: 'alt',
                keyboard.Key.alt_r: 'alt',
                keyboard.Key.cmd: 'cmd',
                keyboard.Key.space: 'space',
                keyboard.Key.enter: 'enter',
                keyboard.Key.esc: 'esc',
                keyboard.Key.tab: 'tab',
                keyboard.Key.f1: 'f1',
                keyboard.Key.f2: 'f2',
                keyboard.Key.f3: 'f3',
                keyboard.Key.f4: 'f4',
                keyboard.Key.f5: 'f5',
                keyboard.Key.f6: 'f6',
                keyboard.Key.f7: 'f7',
                keyboard.Key.f8: 'f8',
                keyboard.Key.f9: 'f9',
                keyboard.Key.f10: 'f10',
                keyboard.Key.f11: 'f11',
                keyboard.Key.f12: 'f12',
            }
            return key_map.get(key, None)

    def _check_hotkeys(self):
        """Verifica se algum atalho registrado foi acionado."""
        current = frozenset(self.current_keys)

        for name, combo in self.hotkeys.items():
            if combo == current:
                # Atravessa para a thread principal via signal
                self.hotkey_triggered.emit(name)
                self.current_keys.clear()
                break
