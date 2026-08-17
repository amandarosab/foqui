"""
FoquiApp - Classe principal que orquestra todos os componentes
"""

import copy
import random
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from config_manager import ConfigManager
from pet_window import PetWindow
from pet import Pet, HOBBY_ANIMATIONS
from context_monitor import ContextMonitor
from tray import TrayIcon
from reopen_tab import ReopenTab
from hotkeys import HotkeyManager
from settings import SettingsWindow
from speech_bubble import SpeechBubble
from dialogue import DialogueBank
from onboarding import OnboardingWindow
from sound import SoundPlayer
import presets


# Intervalo mínimo entre dois balões seguidos (evita o pet virar notificação)
MIN_BUBBLE_GAP_SECONDS = 8

# Carinho sempre reage (animação + som), mas só ganha fala nova a cada 2min
PET_BUBBLE_COOLDOWN_SECONDS = 120


class FoquiApp(QObject):
    """Classe principal que gerencia todos os componentes do Foqui."""

    # Signals
    visibility_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        # Paths
        self.base_path = Path(__file__).parent.parent
        self.assets_path = self.base_path / "assets"

        # Novo ConfigManager centralizando a persistência
        self.config_manager = ConfigManager(self.base_path)
        self.config = self.config_manager.load_config()
        self.state = self.config_manager.load_state()

        # Componentes com Type Hints para silenciar falsos-positivos do linter do VS Code
        self.pet: Pet = None  # type: ignore
        self.pet_window: PetWindow = None  # type: ignore
        self.context_monitor: ContextMonitor = None  # type: ignore
        self.tray: TrayIcon = None  # type: ignore
        self.reopen_tab: ReopenTab = None  # type: ignore
        self.hotkey_manager: HotkeyManager = None  # type: ignore
        self.settings_window: SettingsWindow = None  # type: ignore
        self.onboarding_window: OnboardingWindow = None  # type: ignore
        self.bubble: SpeechBubble = None  # type: ignore
        self.sound: SoundPlayer = None  # type: ignore
        self.dialogue = DialogueBank()

        # Estado
        self.is_visible = True
        self._last_bubble_at = None
        self._last_pet_click_at = None

        # Timer de falas ambientes
        self.chatter_timer = QTimer(self)
        self.chatter_timer.setSingleShot(True)
        self.chatter_timer.timeout.connect(self._on_chatter_tick)

    # === Delegação de Salvamento ===

    def _save_config(self):
        """Redireciona para o ConfigManager"""
        self.config_manager.save_config(self.config)

    def _save_state(self):
        """Redireciona para o ConfigManager"""
        if self.pet:
            self.state = self.pet.get_state()
        self.config_manager.save_state(self.state)

    # === Inicialização ===

    def start(self):
        """Inicializa todos os componentes e mostra o pet."""
        intensity = self.config["behavior"]["movement_intensity"]

        # Cria o pet com estado carregado
        self.pet = Pet(
            pet_type=self.config["pet"]["type"],
            name=self.config["pet"]["name"],
            initial_state=self.state,
            assets_path=self.assets_path,
            movement_intensity=intensity
        )
        self.pet.speak_requested.connect(self._on_speak_requested)
        self.pet.mood_changed.connect(self._on_mood_changed)

        # Cria a janela do pet
        self.pet_window = PetWindow(
            pet=self.pet,
            scale=self.config["pet"]["scale"],
            opacity=self.config["pet"]["opacity"],
            initial_position=(
                self.config["position"]["x"],
                self.config["position"]["y"]
            ),
            movement_intensity=intensity
        )

        # Conecta eventos da janela
        self.pet_window.position_changed.connect(self._on_position_changed)
        self.pet_window.pet_clicked.connect(self._on_pet_clicked)
        self.pet_window.pet_right_clicked.connect(self._on_pet_right_clicked)
        self.pet_window.pet_moved.connect(self._on_pet_moved)
        self.pet_window.hover_held.connect(self._on_hover_held)

        # Balão de fala
        self.bubble = SpeechBubble()

        # Som (mudo por padrão)
        self.sound = SoundPlayer(
            assets_path=self.assets_path,
            enabled=self.config["sound"]["enabled"],
            volume=self.config["sound"]["volume"]
        )

        # Cria o monitor de contexto
        if self.config["behavior"]["react_to_activity"]:
            self._start_context_monitor()

        # Cria o tray icon
        self.tray = TrayIcon(
            pet_type=self.config["pet"]["type"],
            assets_path=self.assets_path,
            current_mode=self.config["mode"]
        )
        self.tray.toggle_visibility_requested.connect(self.toggle_visibility)
        self.tray.settings_requested.connect(self.show_settings)
        self.tray.feed_requested.connect(self.feed_pet)
        self.tray.stats_requested.connect(self.show_status)
        self.tray.mode_requested.connect(self.set_mode)
        self.tray.quit_requested.connect(self.quit)
        self.tray.show()
        self._update_tray_tooltip()

        # Indicador fixo embaixo da tela 
        self.reopen_tab = ReopenTab(pet_type=self.config["pet"]["type"])
        self.reopen_tab.clicked.connect(self.toggle_visibility)

        # Configura hotkeys
        self.hotkey_manager = HotkeyManager()
        self.hotkey_manager.hotkey_triggered.connect(self._on_hotkey)
        self._register_hotkeys()
        self.hotkey_manager.start()

        # Mostra a janela
        if self.config["system"]["start_minimized"]:
            self.is_visible = False
            self.reopen_tab.show()
        else:
            self.pet_window.show()

        # Primeira execução: apresenta o pet antes de qualquer outra coisa
        if not self.config["system"].get("onboarding_done"):
            QTimer.singleShot(600, self.show_onboarding)
        else:
            QTimer.singleShot(1500, lambda: self._say("hello"))

        self._schedule_chatter()

    def _start_context_monitor(self):
        """Cria e inicia o monitor de contexto."""
        self.context_monitor = ContextMonitor(
            night_mode_start=self.config["behavior"]["night_mode_start"],
            night_mode_end=self.config["behavior"]["night_mode_end"],
            detect_meetings=self.config["behavior"]["detect_meetings"]
        )
        self.context_monitor.context_changed.connect(self._on_context_changed)
        self.context_monitor.start()

    def _register_hotkeys(self):
        """(Re)registra os atalhos a partir do config."""
        self.hotkey_manager.clear_hotkeys()
        for name, combo in self.config["hotkeys"].items():
            self.hotkey_manager.register_hotkey(name, combo)

    # === Falas ===

    def _say(self, category: str, force: bool = False):
        """Mostra um balão, respeitando frequência, modo e um intervalo mínimo."""
        if not self.config["bubbles"]["enabled"]:
            return
        if not self.is_visible or self.bubble is None:
            return

        now = datetime.now()

        if not force and self._last_bubble_at is not None:
            elapsed = (now - self._last_bubble_at).total_seconds()
            if elapsed < MIN_BUBBLE_GAP_SECONDS:
                return

        text = self.dialogue.get(category)
        if not text:
            return

        self._show_bubble(text)

    def _show_bubble(self, text: str):
        """Exibe um texto qualquer no balão."""
        if not self.is_visible or self.bubble is None:
            return

        self.bubble.say(
            text=text,
            anchor=self.pet_window.anchor_rect(),
            style=self.config["bubbles"]["style"],
            duration_ms=self.config["bubbles"]["duration_ms"],
            opacity=max(0.75, self.config["pet"]["opacity"])
        )
        self._last_bubble_at = datetime.now()

    def _on_speak_requested(self, category: str):
        """O pet pediu para falar (gatilho de contexto)."""
        self._say(category)

    def _schedule_chatter(self):
        """Agenda a próxima fala ambiente conforme a frequência escolhida."""
        self.chatter_timer.stop()

        if not self.config["bubbles"]["enabled"]:
            return

        interval_range = presets.bubble_interval_range(self.config["bubbles"]["frequency"])
        if not interval_range:
            return

        seconds = random.randint(*interval_range)
        self.chatter_timer.start(seconds * 1000)

    def _on_chatter_tick(self):
        """Hora de comentar alguma coisa - se for um bom momento."""
        quiet_moment = (
            self.is_visible and
            self.pet is not None and
            not self.pet.is_sleeping and
            not self.pet.context.get("in_meeting")
        )

        if quiet_moment:
            category = "night" if self.pet.context.get("is_night") else "idle"
            self._say(category)

        self._schedule_chatter()

    # === Callbacks da janela ===

    def _on_position_changed(self, x: int, y: int):
        """Callback quando a posição do pet muda."""
        self.config["position"]["x"] = x
        self.config["position"]["y"] = y
        self._save_config()

    def _on_pet_moved(self):
        """Durante o arrasto, o balão acompanha o pet."""
        if self.bubble is not None:
            self.bubble.follow(self.pet_window.anchor_rect())

    def _on_pet_clicked(self):
        """Callback quando o pet é clicado (carinho)."""
        now = datetime.now()

        self.pet.receive_pet()
        self.sound.play("pet")

        due_for_new_bubble = (
            self._last_pet_click_at is None or
            (now - self._last_pet_click_at).total_seconds() >= PET_BUBBLE_COOLDOWN_SECONDS
        )

        if due_for_new_bubble:
            self._last_pet_click_at = now
            hobby = self.pet.current_animation in HOBBY_ANIMATIONS
            category = self.pet.current_animation.value if hobby else "pet"
            self._say(category, force=True)

    def _on_pet_right_clicked(self, pos):
        """Callback quando o pet é clicado com botão direito."""
        self.tray.show_context_menu(pos)

    def _on_hover_held(self):
        """Mouse parado em cima do pet: reage de vez em quando."""
        if random.random() < 0.4:
            self._say("hover")

    def _on_context_changed(self, context: dict):
        """Callback quando o contexto do sistema muda."""
        self.pet.update_context(context)

    def _on_mood_changed(self, mood: str):
        """Humor mudou: só atualiza o tooltip, sem alarde."""
        self._update_tray_tooltip()

    def _update_tray_tooltip(self):
        """Mantém o tooltip do tray coerente com o estado atual."""
        if self.tray and self.pet:
            self.tray.update_tooltip(
                self.pet.get_mood_label(),
                self.pet.get_mood_emoji(),
                self.config["mode"]
            )

    # === Ações ===

    def _on_hotkey(self, name: str):
        """Despacha atalhos (já na thread principal)."""
        if name == "toggle_visibility":
            self.toggle_visibility()
        elif name == "cycle_mode":
            self.set_mode(presets.next_mode(self.config["mode"]))
        elif name == "open_settings":
            self.show_settings()

    def toggle_visibility(self):
        """Alterna visibilidade do pet."""
        self.is_visible = not self.is_visible

        if self.is_visible:
            self.pet_window.show()
            if self.reopen_tab:
                self.reopen_tab.hide()
            self._say("show", force=True)
        else:
            self.bubble.hide_now()
            self.pet_window.hide()
            if self.reopen_tab:
                self.reopen_tab.show()

        if self.tray:
            self.tray.set_visibility_state(self.is_visible)

        self.visibility_changed.emit(self.is_visible)

    def set_mode(self, mode: str):
        """Aplica um modo pronto."""
        presets.apply_mode(self.config, mode)
        self._save_config()
        self._apply_settings()

        if self.tray:
            self.tray.set_mode(mode)
        if self.settings_window is not None:
            self.settings_window.refresh(self.config)

        category = f"mode_{mode}"
        text = self.dialogue.get(category)
        if text and self.is_visible and self.bubble is not None:
            self.bubble.say(
                text=text,
                anchor=self.pet_window.anchor_rect(),
                style=self.config["bubbles"]["style"],
                duration_ms=self.config["bubbles"]["duration_ms"],
                opacity=max(0.75, self.config["pet"]["opacity"])
            )
            self._last_bubble_at = datetime.now()

    def show_status(self):
        """Mostra um resumo leve da convivência - sem métrica de cobrança."""
        text = self.dialogue.status_line(
            days_together=self.pet.days_together(),
            total_pets=self.pet.total_pets,
            total_feeds=self.pet.total_feeds
        )

        if not self.is_visible:
            self.toggle_visibility()

        self._show_bubble(text)

    def show_onboarding(self):
        """Mostra as boas-vindas da primeira execução."""
        if self.onboarding_window is None:
            self.onboarding_window = OnboardingWindow(self.config["pet"]["name"])
            self.onboarding_window.finished_onboarding.connect(self._on_onboarding_done)

        self.onboarding_window.show()
        self.onboarding_window.raise_()
        self.onboarding_window.activateWindow()

    def _on_onboarding_done(self, mode: str):
        """Primeira execução concluída."""
        self.config["system"]["onboarding_done"] = True
        self._save_config()

        self.set_mode(mode)
        QTimer.singleShot(900, lambda: self._say("hello", force=True))

    def show_settings(self):
        """Mostra janela de configurações."""
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self.config)
            self.settings_window.settings_changed.connect(self._on_settings_changed)
            self.settings_window.preview_changed.connect(self._on_settings_preview)
            self.settings_window.preview_cancelled.connect(self._on_settings_cancelled)
        else:
            self.settings_window.refresh(self.config)

        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def _on_settings_preview(self, scale: float, opacity: float):
        """Pré-visualização ao vivo de tamanho e opacidade."""
        self.pet_window.set_scale(scale)
        self.pet_window.set_opacity(opacity)

    def _on_settings_cancelled(self):
        """Fechou sem salvar: volta ao que estava valendo."""
        self.pet_window.set_scale(self.config["pet"]["scale"])
        self.pet_window.set_opacity(self.config["pet"]["opacity"])

    def _on_settings_changed(self, new_config: dict):
        """Callback quando configurações são alteradas."""
        old_pet_type = self.config["pet"]["type"]

        self.config = copy.deepcopy(new_config)
        self._save_config()
        self._apply_settings()

        if self.tray:
            self.tray.set_mode(self.config["mode"])

        if self.config["pet"]["type"] != old_pet_type:
            self.pet.set_pet_type(self.config["pet"]["type"])
            if self.tray:
                self.tray.set_pet_type(self.config["pet"]["type"])
            if self.reopen_tab:
                self.reopen_tab.set_pet_type(self.config["pet"]["type"])
            self._show_bubble("Pronto, corpo novo.")
        else:
            self._say("settings_saved", force=True)

    def _apply_settings(self):
        """Aplica configurações atuais aos componentes."""
        intensity = self.config["behavior"]["movement_intensity"]

        # Janela e animação
        self.pet_window.set_scale(self.config["pet"]["scale"])
        self.pet_window.set_opacity(self.config["pet"]["opacity"])
        self.pet_window.set_movement_intensity(intensity)
        self.pet.set_movement_intensity(intensity)

        # Som
        self.sound.set_enabled(self.config["sound"]["enabled"])
        self.sound.set_volume(self.config["sound"]["volume"])

        # Balões
        if not self.config["bubbles"]["enabled"]:
            self.bubble.hide_now()
        self._schedule_chatter()

        # Monitor de contexto
        if self.config["behavior"]["react_to_activity"]:
            if self.context_monitor is None:
                self._start_context_monitor()
            else:
                self.context_monitor.set_detect_meetings(
                    self.config["behavior"]["detect_meetings"]
                )
        else:
            if self.context_monitor:
                self.context_monitor.stop()
                self.context_monitor = None  # type: ignore

        # Atalhos
        if self.hotkey_manager:
            self._register_hotkeys()

        self._update_tray_tooltip()

    def feed_pet(self):
        """Alimenta o pet."""
        if not self.is_visible:
            self.toggle_visibility()

        self.pet.receive_food()
        self.sound.play("feed")
        self._say("feed", force=True)

    def quit(self):
        """Encerra a aplicação."""
        self._save_state()
        self._save_config()

        self.chatter_timer.stop()
        if self.context_monitor:
            self.context_monitor.stop()
        if self.hotkey_manager:
            self.hotkey_manager.stop()

        if self.bubble:
            self.bubble.hide_now()
        if self.pet_window:
            self.pet_window.close()
        if self.reopen_tab:
            self.reopen_tab.close()
        if self.settings_window:
            self.settings_window.close()
        if self.onboarding_window:
            self.onboarding_window.close()

        from PyQt6.QtWidgets import QApplication
        QApplication.quit()