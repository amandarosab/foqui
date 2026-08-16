"""
Smoke test - sobe o app inteiro em modo offscreen e exercita as interações

Não valida aparência: valida que nada explode ao clicar, alimentar, trocar de
modo, abrir configurações e falar. Roda sem tela.
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtWidgets import QApplication

from app import FoquiApp
from settings import SettingsWindow
from onboarding import OnboardingWindow
from speech_bubble import SpeechBubble, STYLE_THOUGHT
import presets


def get_app() -> QApplication:
    """QApplication compartilhada entre os testes."""
    instance = QApplication.instance()
    return instance if instance else QApplication(sys.argv)


class TestFoquiSmoke(unittest.TestCase):
    """Exercita o fluxo principal sem tela."""

    @classmethod
    def setUpClass(cls):
        cls.qapp = get_app()

    def setUp(self):
        """Isola config e estado em um diretório temporário."""
        self.tmp = tempfile.TemporaryDirectory()
        tmp_path = Path(self.tmp.name)

        self.foqui = FoquiApp()
        self.foqui.base_path = tmp_path
        self.foqui.config_path = tmp_path / "config.json"
        self.foqui.state_path = tmp_path / "pet_state.json"
        self.foqui.assets_path = tmp_path / "assets"
        self.foqui.config = self.foqui._load_config()
        self.foqui.state = self.foqui._load_state()

        # Onboarding fora do caminho: é testado separadamente
        self.foqui.config["system"]["onboarding_done"] = True
        self.foqui.start()

    def tearDown(self):
        self.foqui.quit_requested = None
        if self.foqui.context_monitor:
            self.foqui.context_monitor.stop()
        if self.foqui.hotkey_manager:
            self.foqui.hotkey_manager.stop()
        if self.foqui.pet_window:
            self.foqui.pet_window.close()
        if self.foqui.reopen_tab:
            self.foqui.reopen_tab.close()
        if self.foqui.bubble:
            self.foqui.bubble.hide_now()
        self.tmp.cleanup()

    def test_starts_with_all_components(self):
        """Todos os componentes principais sobem."""
        self.assertIsNotNone(self.foqui.pet)
        self.assertIsNotNone(self.foqui.pet_window)
        self.assertIsNotNone(self.foqui.bubble)
        self.assertIsNotNone(self.foqui.tray)
        self.assertIsNotNone(self.foqui.reopen_tab)

    def test_reopen_tab_only_shows_while_pet_is_hidden(self):
        """A bolinha de reabrir só aparece quando o pet está escondido."""
        self.assertFalse(self.foqui.reopen_tab.isVisible())

        self.foqui.toggle_visibility()
        self.assertFalse(self.foqui.is_visible)
        self.assertTrue(self.foqui.reopen_tab.isVisible())

        self.foqui.toggle_visibility()
        self.assertTrue(self.foqui.is_visible)
        self.assertFalse(self.foqui.reopen_tab.isVisible())

    def test_clicking_reopen_tab_shows_the_pet(self):
        """Clicar na bolinha reabre o pet, igual ao ícone da bandeja."""
        self.foqui.toggle_visibility()
        self.assertFalse(self.foqui.is_visible)

        self.foqui.reopen_tab.clicked.emit()

        self.assertTrue(self.foqui.is_visible)
        self.assertFalse(self.foqui.reopen_tab.isVisible())

    def test_click_shows_bubble(self):
        """Carinho responde na hora, com balão."""
        self.foqui._on_pet_clicked()

        self.assertEqual(self.foqui.pet.total_pets, 1)
        self.assertTrue(self.foqui.bubble.isVisible())
        self.assertTrue(self.foqui.bubble.text)

    def test_repeated_clicks_keep_the_same_bubble(self):
        """Cliques seguidos reagem sempre, mas só trocam de fala a cada 2min."""
        self.foqui._on_pet_clicked()
        first = self.foqui.bubble.text
        self.foqui._on_pet_clicked()
        second = self.foqui.bubble.text

        self.assertEqual(first, second)
        self.assertEqual(self.foqui.pet.total_pets, 2)

    def test_click_after_cooldown_gets_a_new_bubble(self):
        """Passado o cooldown de carinho, um novo clique pode falar de novo."""
        from datetime import datetime, timedelta
        import app as app_module

        self.foqui._on_pet_clicked()
        self.foqui._last_pet_click_at = (
            datetime.now() - timedelta(seconds=app_module.PET_BUBBLE_COOLDOWN_SECONDS + 1)
        )
        # Evita o cooldown geral entre balões atrapalhar o teste
        self.foqui._last_bubble_at = (
            datetime.now() - timedelta(seconds=60)
        )

        before = self.foqui._last_pet_click_at
        self.foqui._on_pet_clicked()

        self.assertGreater(self.foqui._last_pet_click_at, before)
        self.assertEqual(self.foqui.pet.total_pets, 2)

    def test_feed(self):
        """Alimentar registra e responde."""
        self.foqui.feed_pet()
        self.assertEqual(self.foqui.pet.total_feeds, 1)

    def test_mode_switch_applies_preset(self):
        """Trocar de modo aplica opacidade, movimento e frequência do preset."""
        self.foqui.set_mode(presets.MODE_FOCUS)

        preset = presets.MODES[presets.MODE_FOCUS]
        self.assertEqual(self.foqui.config["mode"], presets.MODE_FOCUS)
        self.assertAlmostEqual(self.foqui.config["pet"]["opacity"], preset["opacity"])
        self.assertEqual(
            self.foqui.config["behavior"]["movement_intensity"],
            preset["movement_intensity"]
        )
        self.assertEqual(self.foqui.config["bubbles"]["frequency"], presets.FREQ_OFF)
        self.assertEqual(self.foqui.pet.movement_intensity, preset["movement_intensity"])

    def test_cycle_mode_hotkey(self):
        """O atalho de modo percorre os três presets."""
        self.foqui.set_mode(presets.MODE_MEETING)
        self.foqui._on_hotkey("cycle_mode")
        self.assertEqual(self.foqui.config["mode"], presets.MODE_FOCUS)

    def test_toggle_visibility(self):
        """Esconder e mostrar mantém tudo consistente."""
        self.foqui._on_hotkey("toggle_visibility")
        self.assertFalse(self.foqui.is_visible)
        self.assertFalse(self.foqui.bubble.isVisible())

        self.foqui._on_hotkey("toggle_visibility")
        self.assertTrue(self.foqui.is_visible)

    def test_hidden_pet_stays_quiet(self):
        """Escondido, o pet não fala."""
        self.foqui._on_hotkey("toggle_visibility")
        self.foqui._say("idle", force=True)
        self.assertFalse(self.foqui.bubble.isVisible())

    def test_status_bubble(self):
        """Status vira fala, não janela."""
        self.foqui.show_status()
        self.assertIn("cobranças", self.foqui.bubble.text)

    def test_settings_roundtrip(self):
        """Salvar configurações persiste e reaplica."""
        self.foqui.show_settings()
        window = self.foqui.settings_window

        window.scale_slider.setValue(120)
        window.opacity_slider.setValue(70)
        window._on_save()

        self.assertAlmostEqual(self.foqui.config["pet"]["scale"], 1.2)
        self.assertAlmostEqual(self.foqui.config["pet"]["opacity"], 0.7)
        self.assertTrue(self.foqui.config_path.exists())

    def test_settings_preview_is_discarded_on_close(self):
        """Fechar sem salvar volta ao valor real."""
        original = self.foqui.config["pet"]["opacity"]

        self.foqui.show_settings()
        window = self.foqui.settings_window
        window.opacity_slider.setValue(35)
        window.close()

        self.assertAlmostEqual(self.foqui.pet_window.opacity_value, original)
        self.assertAlmostEqual(self.foqui.config["pet"]["opacity"], original)

    def test_meeting_context_makes_pet_observe(self):
        """Reunião detectada dispara fala e tira o pet do modo andarilho."""
        self.foqui._on_context_changed({
            "typing_active": False,
            "mouse_active": False,
            "idle_minutes": 0,
            "window_count": 0,
            "is_night": False,
            "in_meeting": True
        })

        self.assertTrue(self.foqui.pet.context["in_meeting"])

        # Em reunião o pet só respira e olha, nunca sai andando
        from pet import Animation
        for _ in range(60):
            self.foqui.pet._decide_next_animation()
            self.assertIn(
                self.foqui.pet.current_animation,
                (Animation.IDLE_BREATHE, Animation.IDLE_LOOK)
            )

    def test_config_migration_keeps_old_keys(self):
        """Um config.json antigo continua abrindo, com os campos novos preenchidos."""
        import json

        legacy = {
            "pet": {"type": "frog", "name": "Foqui", "scale": 1.0, "opacity": 0.85},
            "position": {"x": 10, "y": 20},
            "behavior": {"react_to_activity": False},
            "hotkeys": {"toggle_visibility": "ctrl+shift+f"},
            "system": {"start_with_windows": False}
        }
        with open(self.foqui.config_path, "w", encoding="utf-8") as f:
            json.dump(legacy, f)

        migrated = self.foqui._load_config()

        self.assertEqual(migrated["position"]["x"], 10)
        self.assertFalse(migrated["behavior"]["react_to_activity"])
        self.assertIn("bubbles", migrated)
        self.assertIn("cycle_mode", migrated["hotkeys"])
        self.assertEqual(migrated["behavior"]["night_mode_start"], 22)


class TestSpeechBubble(unittest.TestCase):
    """Testes do balão isolado."""

    @classmethod
    def setUpClass(cls):
        cls.qapp = get_app()

    def test_bubble_positions_itself(self):
        """O balão se coloca perto da âncora e dentro da tela."""
        from PyQt6.QtCore import QRect

        bubble = SpeechBubble()
        anchor = QRect(400, 400, 64, 64)
        bubble.say("Oi, eu sou um balão de teste.", anchor)

        self.assertTrue(bubble.isVisible())
        self.assertGreater(bubble.width(), 0)
        self.assertLess(abs(bubble.geometry().center().x() - anchor.center().x()), 200)

        bubble.hide_now()

    def test_bubble_flips_when_there_is_no_room_above(self):
        """Colado no topo da tela, o balão vai para baixo."""
        from PyQt6.QtCore import QRect

        bubble = SpeechBubble()
        bubble.say("Sem espaço em cima.", QRect(300, 0, 64, 64))

        self.assertTrue(bubble.tail_up)
        bubble.hide_now()

    def test_thought_style(self):
        """Formato pensamento também renderiza."""
        from PyQt6.QtCore import QRect

        bubble = SpeechBubble()
        bubble.say("Hmm.", QRect(300, 300, 64, 64), style=STYLE_THOUGHT)

        self.assertEqual(bubble.style, STYLE_THOUGHT)
        bubble.hide_now()


class TestOnboarding(unittest.TestCase):
    """Testes do onboarding."""

    @classmethod
    def setUpClass(cls):
        cls.qapp = get_app()

    def test_walks_through_steps_and_picks_a_mode(self):
        """Passar por todos os passos termina escolhendo um modo."""
        window = OnboardingWindow()
        chosen = []
        window.finished_onboarding.connect(chosen.append)

        for _ in range(len(OnboardingWindow.STEPS)):
            window._next_step()

        window._choose_mode(presets.MODE_MEETING)

        self.assertEqual(chosen, [presets.MODE_MEETING])

    def test_skip_finishes_immediately(self):
        """Pular também conclui, sem travar ninguém."""
        window = OnboardingWindow()
        chosen = []
        window.finished_onboarding.connect(chosen.append)

        window.skip_btn.click()

        self.assertEqual(len(chosen), 1)


if __name__ == "__main__":
    unittest.main()
