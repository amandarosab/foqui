import json
import copy
from datetime import datetime
from pathlib import Path
import presets

class ConfigManager:
    """Gerencia a leitura e escrita das configurações e do estado do pet."""

    def __init__(self, base_path: Path):
        self.config_path = base_path / "config.json"
        self.state_path = base_path / "pet_state.json"

    def load_config(self) -> dict:
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                stored = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            stored = {}
        return self._merge_defaults(self._default_config(), stored)

    def save_config(self, config: dict):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    def load_state(self) -> dict:
        try:
            with open(self.state_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self._default_state()

    def save_state(self, state: dict):
        with open(self.state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4, ensure_ascii=False)

    def _merge_defaults(self, defaults: dict, stored: dict) -> dict:
        result = copy.deepcopy(defaults)
        for key, value in stored.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = self._merge_defaults(result[key], value)
            else:
                result[key] = value
        return result

    def _default_config(self) -> dict:
        return {
            "pet": {
                "type": "frog",
                "name": "Foqui",
                "scale": 1.0,
                "opacity": 0.85
            },
            "position": {
                "x": 100,
                "y": 100
            },
            "mode": presets.MODE_RELAX,
            "presence": presets.PRESENCE_MODERATE,
            "behavior": {
                "react_to_activity": True,
                "night_mode_auto": True,
                "night_mode_start": 22,
                "night_mode_end": 6,
                "movement_intensity": presets.INTENSITY_MODERATE,
                "detect_meetings": True
            },
            "bubbles": {
                "enabled": True,
                "style": "speech",
                "frequency": presets.FREQ_NORMAL,
                "duration_ms": 4200
            },
            "sound": {
                "enabled": False,
                "volume": 0.25
            },
            "hotkeys": {
                "toggle_visibility": "ctrl+shift+f",
                "cycle_mode": "ctrl+shift+m",
                "open_settings": "ctrl+shift+o"
            },
            "system": {
                "start_with_windows": False,
                "start_minimized": False,
                "onboarding_done": False
            }
        }

    def _default_state(self) -> dict:
        return {
            "mood": "happy",
            "mood_value": 100,
            "last_interaction": None,
            "last_fed": None,
            "total_pets": 0,
            "total_feeds": 0,
            "total_time_active_minutes": 0,
            "created_at": datetime.now().isoformat()
        }