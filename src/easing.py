"""
Easing functions para animações suaves e naturais.
"""

import math


def ease_in_out_sine(t: float) -> float:
    """Easing suave entrada e saída com sine."""
    return -0.5 * (math.cos(math.pi * t) - 1)


def ease_out_cubic(t: float) -> float:
    """Easing cúbico com saída acelerada."""
    return 1 - (1 - t) ** 3


def ease_in_cubic(t: float) -> float:
    """Easing cúbico com entrada desacelerada."""
    return t ** 3


def ease_out_back(t: float) -> float:
    """Easing com overshoot na saída."""
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def ease_out_elastic(t: float) -> float:
    """Easing elástico com vibração na saída."""
    if t == 0:
        return 0
    if t == 1:
        return 1
    
    c5 = (2 * math.pi) / 4.5
    return (2 ** (-10 * t)) * math.sin((t * 10 - 0.75) * c5) + 1


def breathe(t: float, amplitude: float = 0.1, frequency: float = 1.0) -> float:
    """Simula respiração suave e contínua."""
    return 1.0 + amplitude * math.sin(2 * math.pi * frequency * t)


def blink_curve(t: float) -> float:
    """Curva para animar piscar de olhos."""
    # Começa em 1, vai para 0 (fechando), volta para 1 (abrindo)
    if t < 0.3:
        # Abrindo (0 a 0.3)
        return 1.0
    elif t < 0.5:
        # Fechando (0.3 a 0.5)
        return 1.0 - (t - 0.3) / 0.2
    else:
        # Abrindo novamente (0.5 a 1.0)
        return (t - 0.5) / 0.5


def spring_settle(t: float, damping: float = 0.8, stiffness: float = 8.0) -> float:
    """Simula uma mola assentando com oscilação amortecida."""
    return 1.0 - math.exp(-damping * t) * math.cos(stiffness * t)
