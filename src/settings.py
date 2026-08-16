"""
SettingsWindow - Janela de configurações do Foqui

Uma coluna só, sem abas, sem texto longo. Os três modos ficam no topo
porque resolvem a maioria dos casos sem ninguém precisar ler o resto.
"""

import copy

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QSlider, QComboBox, QCheckBox, QPushButton,
    QLineEdit, QFormLayout, QScrollArea, QWidget, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal

from presets import (
    MODES, MODE_ORDER, MODE_CUSTOM,
    PRESENCE_LABELS, FREQUENCY_LABELS, INTENSITY_SETTINGS,
    apply_mode, apply_presence, detect_mode, mode_label
)


DIALOG_STYLE = """
QDialog { background-color: #1A1D26; }
QGroupBox {
    color: #C4CAD6;
    font-size: 13px;
    border: 1px solid #2C3346;
    border-radius: 10px;
    margin-top: 14px;
    padding: 14px 12px 12px 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QLabel { color: #C4CAD6; font-size: 13px; }
QCheckBox { color: #E4E8F0; font-size: 14px; padding: 7px 2px; }
QCheckBox::indicator { width: 20px; height: 20px; }
QComboBox, QLineEdit {
    background-color: #232838;
    border: 1px solid #3A4050;
    border-radius: 8px;
    padding: 8px 10px;
    color: #F0F2F6;
    font-size: 14px;
}
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background-color: #232838;
    color: #F0F2F6;
    selection-background-color: #2C3346;
    border: 1px solid #3A4050;
}
QPushButton {
    font-size: 14px;
    padding: 11px 18px;
    border-radius: 9px;
    border: 1px solid #3A4050;
    background-color: #232838;
    color: #F0F2F6;
}
QPushButton:hover { background-color: #2C3346; border-color: #86C29C; }
QPushButton:checked {
    background-color: #86C29C;
    color: #14171F;
    font-weight: 600;
    border-color: #86C29C;
}
QPushButton#primary {
    background-color: #86C29C;
    color: #14171F;
    font-weight: 600;
    border: none;
}
QPushButton#primary:hover { background-color: #9AD3AE; }
QSlider::groove:horizontal {
    height: 6px; background: #2C3346; border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #86C29C; width: 18px; height: 18px;
    margin: -7px 0; border-radius: 9px;
}
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollBar:vertical {
    background: #1A1D26; width: 10px; margin: 0;
}
QScrollBar::handle:vertical {
    background: #3A4050; border-radius: 5px; min-height: 24px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


class SettingsWindow(QDialog):
    """Janela de configurações."""

    # Emitido ao salvar
    settings_changed = pyqtSignal(dict)
    # Emitido enquanto os sliders se mexem (scale, opacity) - pré-visualização
    preview_changed = pyqtSignal(float, float)
    # Emitido ao fechar sem salvar, para o app restaurar o estado real
    preview_cancelled = pyqtSignal()

    def __init__(self, config: dict):
        super().__init__()

        self.config = copy.deepcopy(config)
        self._saved = False
        self._loading = False
        self.mode_buttons = {}

        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        """Configura a interface."""
        self.setWindowTitle("Foqui")
        self.setMinimumWidth(440)
        self.setModal(False)
        self.setStyleSheet(DIALOG_STYLE)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(20, 16, 20, 16)
        outer_layout.setSpacing(10)

        # Conteúdo rolável: em telas pequenas nem tudo cabe de uma vez
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 8, 0)
        content_layout.setSpacing(10)

        content_layout.addWidget(self._create_mode_group())
        content_layout.addWidget(self._create_appearance_group())
        content_layout.addWidget(self._create_behavior_group())
        content_layout.addWidget(self._create_bubbles_group())
        content_layout.addWidget(self._create_hotkeys_group())
        content_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

        # Botões: sempre visíveis, fora da área rolável
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(close_btn)

        save_btn = QPushButton("Salvar")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self._on_save)
        buttons_layout.addWidget(save_btn)

        outer_layout.addLayout(buttons_layout)

        self._fit_to_screen(content)

    def _fit_to_screen(self, content: QWidget):
        """Limita a altura da janela ao que cabe na tela, sem cortar os botões."""
        screen = QApplication.primaryScreen()
        if screen is None:
            return

        available_height = screen.availableGeometry().height()
        # Reserva espaço para margens e a barra de botões
        max_height = max(360, int(available_height * 0.85))

        self.setMaximumHeight(max_height)
        content_hint = content.sizeHint().height() + 90
        self.resize(self.width(), min(content_hint, max_height))

    # === Grupos ===

    def _create_mode_group(self) -> QGroupBox:
        """Três botões grandes: o atalho para tudo."""
        group = QGroupBox("Modo")
        layout = QHBoxLayout(group)
        layout.setSpacing(8)

        for mode in MODE_ORDER:
            preset = MODES[mode]
            btn = QPushButton(f"{preset['icon']}\n{preset['label']}")
            btn.setCheckable(True)
            btn.setMinimumHeight(58)
            btn.setToolTip(preset["hint"])
            btn.clicked.connect(lambda _, m=mode: self._on_mode_clicked(m))

            layout.addWidget(btn)
            self.mode_buttons[mode] = btn

        return group

    def _create_appearance_group(self) -> QGroupBox:
        """Aparência: presença, tamanho, opacidade, tipo de pet."""
        group = QGroupBox("Aparência")
        layout = QFormLayout(group)
        layout.setSpacing(10)

        # Presença
        self.presence_combo = QComboBox()
        for key, label in PRESENCE_LABELS.items():
            self.presence_combo.addItem(label, key)
        self.presence_combo.currentIndexChanged.connect(self._on_presence_changed)
        layout.addRow("Presença:", self.presence_combo)

        # Tamanho
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setMinimum(50)
        self.scale_slider.setMaximum(200)
        self.scale_slider.setTickInterval(25)

        self.scale_label = QLabel("100%")
        self.scale_label.setMinimumWidth(42)
        self.scale_slider.valueChanged.connect(self._on_scale_changed)

        scale_layout = QHBoxLayout()
        scale_layout.addWidget(self.scale_slider)
        scale_layout.addWidget(self.scale_label)
        layout.addRow("Tamanho:", scale_layout)

        # Opacidade
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(30)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setTickInterval(10)

        self.opacity_label = QLabel("85%")
        self.opacity_label.setMinimumWidth(42)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)

        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        layout.addRow("Opacidade:", opacity_layout)

        # Pet
        self.pet_combo = QComboBox()
        self.pet_combo.addItem("Sapinho", "frog")
        self.pet_combo.addItem("Ratinho", "rat")
        self.pet_combo.addItem("Gato", "cat")
        self.pet_combo.addItem("Robô", "robot")
        layout.addRow("Pet:", self.pet_combo)

        return group

    def _create_behavior_group(self) -> QGroupBox:
        """Comportamento: movimento e reações."""
        group = QGroupBox("Comportamento")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)

        # Intensidade de movimento
        intensity_row = QHBoxLayout()
        intensity_row.addWidget(QLabel("Movimento:"))
        self.intensity_combo = QComboBox()
        for key, data in INTENSITY_SETTINGS.items():
            self.intensity_combo.addItem(data["label"], key)
        self.intensity_combo.currentIndexChanged.connect(self._mark_custom)
        intensity_row.addWidget(self.intensity_combo, 1)
        layout.addLayout(intensity_row)

        self.react_checkbox = QCheckBox("Reage à atividade")
        layout.addWidget(self.react_checkbox)

        self.meeting_checkbox = QCheckBox("Fica discreto em reunião")
        layout.addWidget(self.meeting_checkbox)

        self.night_checkbox = QCheckBox("Modo noturno automático")
        layout.addWidget(self.night_checkbox)

        self.startup_checkbox = QCheckBox("Iniciar com o Windows")
        layout.addWidget(self.startup_checkbox)

        return group

    def _create_bubbles_group(self) -> QGroupBox:
        """Balões e som."""
        group = QGroupBox("Balões")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        self.bubbles_checkbox = QCheckBox("Mostrar balões de fala")
        self.bubbles_checkbox.toggled.connect(self._on_bubbles_toggled)
        layout.addWidget(self.bubbles_checkbox)

        form = QFormLayout()
        form.setSpacing(8)

        self.frequency_combo = QComboBox()
        for key, label in FREQUENCY_LABELS.items():
            self.frequency_combo.addItem(label, key)
        self.frequency_combo.currentIndexChanged.connect(self._mark_custom)
        form.addRow("Frequência:", self.frequency_combo)

        self.bubble_style_combo = QComboBox()
        self.bubble_style_combo.addItem("Fala", "speech")
        self.bubble_style_combo.addItem("Pensamento", "thought")
        form.addRow("Formato:", self.bubble_style_combo)

        layout.addLayout(form)

        self.sound_checkbox = QCheckBox("Som leve ao interagir")
        layout.addWidget(self.sound_checkbox)

        return group

    def _create_hotkeys_group(self) -> QGroupBox:
        """Atalhos de teclado."""
        group = QGroupBox("Atalhos")
        layout = QFormLayout(group)
        layout.setSpacing(8)

        self.toggle_hotkey = QLineEdit()
        self.toggle_hotkey.setPlaceholderText("ctrl+shift+f")
        layout.addRow("Esconder:", self.toggle_hotkey)

        self.mode_hotkey = QLineEdit()
        self.mode_hotkey.setPlaceholderText("ctrl+shift+m")
        layout.addRow("Trocar modo:", self.mode_hotkey)

        self.settings_hotkey = QLineEdit()
        self.settings_hotkey.setPlaceholderText("ctrl+shift+o")
        layout.addRow("Configurações:", self.settings_hotkey)

        return group

    # === Carga e escrita de valores ===

    def _load_values(self):
        """Carrega valores atuais nos controles."""
        self._loading = True

        pet = self.config["pet"]
        behavior = self.config["behavior"]
        bubbles = self.config["bubbles"]
        hotkeys = self.config["hotkeys"]

        # Modo
        self._highlight_mode(self.config.get("mode", MODE_CUSTOM))

        # Aparência
        self._select_by_data(self.presence_combo, self.config.get("presence", "moderate"))

        scale_percent = int(pet["scale"] * 100)
        self.scale_slider.setValue(scale_percent)
        self.scale_label.setText(f"{scale_percent}%")

        opacity_percent = int(pet["opacity"] * 100)
        self.opacity_slider.setValue(opacity_percent)
        self.opacity_label.setText(f"{opacity_percent}%")

        self._select_by_data(self.pet_combo, pet["type"])

        # Comportamento
        self._select_by_data(self.intensity_combo, behavior.get("movement_intensity", "moderate"))
        self.react_checkbox.setChecked(behavior.get("react_to_activity", True))
        self.meeting_checkbox.setChecked(behavior.get("detect_meetings", True))
        self.night_checkbox.setChecked(behavior.get("night_mode_auto", True))
        self.startup_checkbox.setChecked(self.config["system"].get("start_with_windows", False))

        # Balões
        self.bubbles_checkbox.setChecked(bubbles.get("enabled", True))
        self._select_by_data(self.frequency_combo, bubbles.get("frequency", "normal"))
        self._select_by_data(self.bubble_style_combo, bubbles.get("style", "speech"))
        self._on_bubbles_toggled(bubbles.get("enabled", True))

        self.sound_checkbox.setChecked(self.config["sound"].get("enabled", False))

        # Atalhos
        self.toggle_hotkey.setText(hotkeys.get("toggle_visibility", ""))
        self.mode_hotkey.setText(hotkeys.get("cycle_mode", ""))
        self.settings_hotkey.setText(hotkeys.get("open_settings", ""))

        self._loading = False

    def _select_by_data(self, combo: QComboBox, value):
        """Seleciona o item cujo userData bate com o valor."""
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _collect_values(self) -> dict:
        """Lê os controles para dentro do config."""
        self.config["pet"]["scale"] = self.scale_slider.value() / 100
        self.config["pet"]["opacity"] = self.opacity_slider.value() / 100
        self.config["pet"]["type"] = self.pet_combo.currentData()

        self.config["presence"] = self.presence_combo.currentData()

        self.config["behavior"]["movement_intensity"] = self.intensity_combo.currentData()
        self.config["behavior"]["react_to_activity"] = self.react_checkbox.isChecked()
        self.config["behavior"]["detect_meetings"] = self.meeting_checkbox.isChecked()
        self.config["behavior"]["night_mode_auto"] = self.night_checkbox.isChecked()

        self.config["bubbles"]["enabled"] = self.bubbles_checkbox.isChecked()
        self.config["bubbles"]["frequency"] = self.frequency_combo.currentData()
        self.config["bubbles"]["style"] = self.bubble_style_combo.currentData()

        self.config["sound"]["enabled"] = self.sound_checkbox.isChecked()

        self.config["system"]["start_with_windows"] = self.startup_checkbox.isChecked()

        self.config["hotkeys"]["toggle_visibility"] = self.toggle_hotkey.text().strip()
        self.config["hotkeys"]["cycle_mode"] = self.mode_hotkey.text().strip()
        self.config["hotkeys"]["open_settings"] = self.settings_hotkey.text().strip()

        # O modo só continua marcado se os valores ainda baterem com o preset
        self.config["mode"] = detect_mode(self.config)

        return self.config

    # === Reações da interface ===

    def _on_mode_clicked(self, mode: str):
        """Aplica um preset e recarrega os controles."""
        self._collect_values()
        apply_mode(self.config, mode)
        self._load_values()
        self._emit_preview()

    def _on_presence_changed(self):
        """Presença mexe em opacidade e movimento de uma vez."""
        if self._loading:
            return

        presence = self.presence_combo.currentData()
        self._collect_values()
        apply_presence(self.config, presence)
        self._load_values()
        self._emit_preview()

    def _on_scale_changed(self, value: int):
        self.scale_label.setText(f"{value}%")
        if not self._loading:
            self._mark_custom()
            self._emit_preview()

    def _on_opacity_changed(self, value: int):
        self.opacity_label.setText(f"{value}%")
        if not self._loading:
            self._mark_custom()
            self._emit_preview()

    def _on_bubbles_toggled(self, enabled: bool):
        """Sem balões, os controles de balão não fazem sentido."""
        self.frequency_combo.setEnabled(enabled)
        self.bubble_style_combo.setEnabled(enabled)
        if not self._loading:
            self._mark_custom()

    def _mark_custom(self):
        """Mexer nos detalhes desmarca o preset, sem perguntar nada."""
        if self._loading:
            return

        self._highlight_mode(MODE_CUSTOM)

    def _highlight_mode(self, mode: str):
        """Marca visualmente o modo ativo."""
        for name, btn in self.mode_buttons.items():
            btn.setChecked(name == mode)

    def _emit_preview(self):
        """Mostra o efeito de tamanho/opacidade em tempo real."""
        self.preview_changed.emit(
            self.scale_slider.value() / 100,
            self.opacity_slider.value() / 100
        )

    # === Salvar / fechar ===

    def _on_save(self):
        """Salva as configurações."""
        self._saved = True
        self.settings_changed.emit(self._collect_values())
        self.close()

    def closeEvent(self, event):
        """Fechar sem salvar descarta a pré-visualização."""
        if not self._saved:
            self.preview_cancelled.emit()
        self._saved = False
        event.accept()

    def refresh(self, config: dict):
        """Recarrega a janela a partir do config real (ex: modo trocado por atalho)."""
        self.config = copy.deepcopy(config)
        self._load_values()
