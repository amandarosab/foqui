"""
TrayIcon - Ícone na bandeja do sistema e menu rápido do pet

O mesmo menu é usado no clique direito sobre o pet: itens grandes, rótulos
curtos, um ícone por linha. Nada de submenu escondido.
"""

from pathlib import Path

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction, QActionGroup
from PyQt6.QtCore import Qt, pyqtSignal, QPoint

from presets import MODES, MODE_ORDER, mode_label


MENU_STYLE = """
QMenu {
    background-color: #1A1D26;
    border: 1px solid #3A4050;
    border-radius: 10px;
    padding: 8px;
    color: #F0F2F6;
    font-size: 14px;
}
QMenu::item {
    padding: 11px 20px 11px 16px;
    border-radius: 8px;
    margin: 2px 0;
}
QMenu::item:selected {
    background-color: #2C3346;
}
QMenu::item:disabled {
    color: #6B7284;
}
QMenu::separator {
    height: 1px;
    background: #2C3346;
    margin: 6px 10px;
}
"""


class TrayIcon(QSystemTrayIcon):
    """Ícone na bandeja do sistema com menu de contexto."""

    # Signals
    toggle_visibility_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    feed_requested = pyqtSignal()
    stats_requested = pyqtSignal()
    mode_requested = pyqtSignal(str)
    quit_requested = pyqtSignal()

    def __init__(self, pet_type: str, assets_path: Path, current_mode: str = "relax"):
        super().__init__()

        self.pet_type = pet_type
        self.assets_path = assets_path
        self.current_mode = current_mode
        self.mode_actions = {}

        # Configura ícone
        icon = self._load_icon()
        self.setIcon(icon)

        # Tooltip
        self.setToolTip("Foqui - clique para mostrar ou esconder")

        # Menu de contexto
        self.menu = self._create_menu()
        self.setContextMenu(self.menu)

        # Conecta clique no ícone
        self.activated.connect(self._on_activated)

    def _load_icon(self) -> QIcon:
        """Carrega ícone do pet ou cria um placeholder."""
        icon_path = self.assets_path / "icons" / f"tray_{self.pet_type}.png"

        if icon_path.exists():
            return QIcon(str(icon_path))

        # Cria ícone placeholder
        return QIcon(self._create_placeholder_icon())

    def _create_placeholder_icon(self) -> QPixmap:
        """Cria um ícone placeholder (sapinho simples)."""
        size = 32
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Corpo verde
        body_color = QColor(134, 194, 156)
        painter.setBrush(body_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(4, 10, 24, 18)

        # Olhos
        eye_color = QColor(255, 255, 255)
        pupil_color = QColor(40, 40, 40)

        painter.setBrush(eye_color)
        painter.drawEllipse(6, 4, 10, 10)
        painter.drawEllipse(16, 4, 10, 10)

        painter.setBrush(pupil_color)
        painter.drawEllipse(9, 6, 4, 4)
        painter.drawEllipse(19, 6, 4, 4)

        painter.end()

        return pixmap

    def _create_menu(self) -> QMenu:
        """Cria o menu rápido."""
        menu = QMenu()
        menu.setStyleSheet(MENU_STYLE)

        # Modos: a decisão mais comum fica no topo
        mode_group = QActionGroup(menu)
        mode_group.setExclusive(True)

        for mode in MODE_ORDER:
            preset = MODES[mode]
            action = QAction(f"{preset['icon']}  {preset['label']}", menu)
            action.setCheckable(True)
            action.setChecked(mode == self.current_mode)
            action.setToolTip(preset["hint"])
            action.triggered.connect(lambda _, m=mode: self.mode_requested.emit(m))

            mode_group.addAction(action)
            menu.addAction(action)
            self.mode_actions[mode] = action

        menu.addSeparator()

        # Esconder/Mostrar
        self.toggle_action = QAction("🙈  Esconder", menu)
        self.toggle_action.setShortcut("Ctrl+Shift+F")
        self.toggle_action.triggered.connect(self.toggle_visibility_requested.emit)
        menu.addAction(self.toggle_action)

        # Alimentar
        feed_action = QAction("🍎  Alimentar", menu)
        feed_action.triggered.connect(self.feed_requested.emit)
        menu.addAction(feed_action)

        # Status
        status_action = QAction("💬  Status", menu)
        status_action.triggered.connect(self.stats_requested.emit)
        menu.addAction(status_action)

        menu.addSeparator()

        # Sair
        quit_action = QAction("👋  Sair", menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)

        return menu

    def _on_activated(self, reason):
        """Callback quando o ícone é ativado."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Clique simples
            self.toggle_visibility_requested.emit()
        elif reason == QSystemTrayIcon.ActivationReason.Context:
            # Clique direito - menu já é mostrado automaticamente
            pass

    def show_context_menu(self, pos: QPoint):
        """Mostra o menu rápido em uma posição específica."""
        self.menu.popup(pos)

    def set_pet_type(self, pet_type: str):
        """Atualiza o ícone da bandeja para o novo tipo de pet."""
        if pet_type == self.pet_type:
            return
        self.pet_type = pet_type
        self.setIcon(self._load_icon())

    def set_mode(self, mode: str):
        """Marca o modo ativo no menu."""
        self.current_mode = mode
        for name, action in self.mode_actions.items():
            action.setChecked(name == mode)

    def set_visibility_state(self, is_visible: bool):
        """Ajusta o rótulo do item de esconder/mostrar."""
        if is_visible:
            self.toggle_action.setText("🙈  Esconder")
        else:
            self.toggle_action.setText("👀  Mostrar")

    def update_tooltip(self, mood_label: str, mood_emoji: str, mode: str):
        """Atualiza o tooltip com humor e modo atuais."""
        self.setToolTip(f"Foqui {mood_emoji} {mood_label} · modo {mode_label(mode)}")
