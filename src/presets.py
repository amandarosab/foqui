"""
Presets - Modos prontos e escalas de presença do Foqui

A ideia é que quase ninguém precise abrir configurações: três botões
resolvem 90% dos casos. Quem quiser ajustar no detalhe, ajusta - e aí o
modo vira "custom" sozinho, sem diálogo de confirmação.
"""

# Modos
MODE_MEETING = "meeting"
MODE_FOCUS = "focus"
MODE_RELAX = "relax"
MODE_CUSTOM = "custom"

# Presença (o quanto o pet se faz notar)
PRESENCE_DISCREET = "discreet"
PRESENCE_MODERATE = "moderate"
PRESENCE_SHOWY = "showy"

# Intensidade de movimento
INTENSITY_SUBTLE = "subtle"
INTENSITY_MODERATE = "moderate"
INTENSITY_LIVELY = "lively"

# Frequência de balões
FREQ_OFF = "off"
FREQ_RARE = "rare"
FREQ_NORMAL = "normal"
FREQ_CHATTY = "chatty"


MODES = {
    MODE_MEETING: {
        "label": "Reunião",
        "icon": "🎧",
        "hint": "Discreto e quieto, só de canto",
        "opacity": 0.75,
        "presence": PRESENCE_DISCREET,
        "movement_intensity": INTENSITY_SUBTLE,
        "bubble_frequency": FREQ_RARE,
        "sound_enabled": False,
    },
    MODE_FOCUS: {
        "label": "Foco",
        "icon": "🎯",
        "hint": "Quase invisível, sem falar",
        "opacity": 0.55,
        "presence": PRESENCE_DISCREET,
        "movement_intensity": INTENSITY_SUBTLE,
        "bubble_frequency": FREQ_OFF,
        "sound_enabled": False,
    },
    MODE_RELAX: {
        "label": "Relax",
        "icon": "🌿",
        "hint": "Presente, animado e tagarela",
        "opacity": 1.0,
        "presence": PRESENCE_SHOWY,
        "movement_intensity": INTENSITY_LIVELY,
        "bubble_frequency": FREQ_CHATTY,
        "sound_enabled": False,
    },
}

MODE_ORDER = [MODE_MEETING, MODE_FOCUS, MODE_RELAX]


# Multiplicador de FPS e probabilidade de animações "grandes" (andar, pular)
INTENSITY_SETTINGS = {
    INTENSITY_SUBTLE: {"label": "Sutil", "fps": 6, "motion_chance": 0.0, "idle_variation": 0.5},
    INTENSITY_MODERATE: {"label": "Moderado", "fps": 8, "motion_chance": 0.08, "idle_variation": 1.0},
    INTENSITY_LIVELY: {"label": "Animado", "fps": 10, "motion_chance": 0.18, "idle_variation": 1.4},
}

# Intervalo (em segundos) entre falas ambientes: sorteado dentro da faixa
BUBBLE_INTERVALS = {
    FREQ_OFF: None,
    FREQ_RARE: (720, 1500),      # 12 a 25 min
    FREQ_NORMAL: (300, 600),     # 5 a 10 min
    FREQ_CHATTY: (90, 240),      # 1,5 a 4 min
}

FREQUENCY_LABELS = {
    FREQ_OFF: "Nunca",
    FREQ_RARE: "Raramente",
    FREQ_NORMAL: "Às vezes",
    FREQ_CHATTY: "Bastante",
}

PRESENCE_LABELS = {
    PRESENCE_DISCREET: "Discreto",
    PRESENCE_MODERATE: "Moderado",
    PRESENCE_SHOWY: "Chamativo",
}

# Presença ajusta opacidade e movimento sem mexer no resto
PRESENCE_SETTINGS = {
    PRESENCE_DISCREET: {"opacity": 0.6, "movement_intensity": INTENSITY_SUBTLE},
    PRESENCE_MODERATE: {"opacity": 0.85, "movement_intensity": INTENSITY_MODERATE},
    PRESENCE_SHOWY: {"opacity": 1.0, "movement_intensity": INTENSITY_LIVELY},
}


def apply_mode(config: dict, mode: str) -> dict:
    """
    Aplica um modo ao config (in place) e devolve o mesmo dict.
    Modo desconhecido ou "custom" não muda nada além do rótulo.
    """
    preset = MODES.get(mode)
    config["mode"] = mode

    if not preset:
        return config

    config["pet"]["opacity"] = preset["opacity"]
    config["presence"] = preset["presence"]
    config["behavior"]["movement_intensity"] = preset["movement_intensity"]
    config["bubbles"]["frequency"] = preset["bubble_frequency"]
    config["sound"]["enabled"] = preset["sound_enabled"]

    return config


def apply_presence(config: dict, presence: str) -> dict:
    """Aplica um nível de presença (opacidade + movimento)."""
    settings = PRESENCE_SETTINGS.get(presence)
    config["presence"] = presence

    if not settings:
        return config

    config["pet"]["opacity"] = settings["opacity"]
    config["behavior"]["movement_intensity"] = settings["movement_intensity"]

    return config


def next_mode(current: str) -> str:
    """Próximo modo do ciclo (usado pelo atalho de teclado)."""
    if current not in MODE_ORDER:
        return MODE_ORDER[0]
    index = (MODE_ORDER.index(current) + 1) % len(MODE_ORDER)
    return MODE_ORDER[index]


def mode_label(mode: str) -> str:
    """Rótulo legível de um modo."""
    preset = MODES.get(mode)
    return preset["label"] if preset else "Personalizado"


def intensity_settings(intensity: str) -> dict:
    """Parâmetros de animação para uma intensidade."""
    return INTENSITY_SETTINGS.get(intensity, INTENSITY_SETTINGS[INTENSITY_MODERATE])


def bubble_interval_range(frequency: str):
    """Faixa de intervalo entre falas ambientes, ou None se desligado."""
    return BUBBLE_INTERVALS.get(frequency, BUBBLE_INTERVALS[FREQ_NORMAL])


def detect_mode(config: dict) -> str:
    """
    Descobre se o config atual ainda bate com algum preset.
    Serve para reverter o rótulo para "custom" quando o usuário mexe nos sliders.
    """
    for mode, preset in MODES.items():
        if (
            abs(config["pet"]["opacity"] - preset["opacity"]) < 0.02 and
            config["behavior"]["movement_intensity"] == preset["movement_intensity"] and
            config["bubbles"]["frequency"] == preset["bubble_frequency"]
        ):
            return mode
    return MODE_CUSTOM
