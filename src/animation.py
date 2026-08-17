"""
AnimationManager - Gerencia sprite sheets e frames de animação

Esta versão foi atualizada para focar em animação procedural de ALTA FIDELIDADE
para o sapo Foqui (brinquedo de borracha), com física real e sec-motion nos olhos.
"""

import math
from pathlib import Path
from typing import Callable, Dict, Optional, List

from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QPolygon, QPen, QFont,
    QLinearGradient, QRadialGradient, QPainterPath,
)
from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QRectF

from easing import (
    ease_in_out_sine, ease_out_cubic, ease_in_cubic,
    ease_out_back, ease_out_elastic, breathe, blink_curve, spring_settle,
)


class AnimationData:
    """Dados de uma animação específica."""

    def __init__(self, name: str, frames: List[QPixmap], loop: bool = True, fps: int = 12):
        self.name = name
        self.frames = frames
        self.loop = loop
        self.fps = fps                      # ritmo próprio da animação
        self.frame_interval_ms = max(1, round(1000 / fps))
        self.current_frame = 0
        self.frame_count = len(frames)

    def get_frame(self) -> Optional[QPixmap]:
        """Retorna o frame atual."""
        if self.frames and 0 <= self.current_frame < len(self.frames):
            return self.frames[self.current_frame]
        return None

    def advance(self) -> bool:
        """
        Avança para o próximo frame.
        Retorna True se a animação terminou.
        """
        self.current_frame += 1

        if self.current_frame >= self.frame_count:
            if self.loop:
                self.current_frame = 0
                return False
            else:
                self.current_frame = self.frame_count - 1
                return True

        return False

    def reset(self):
        """Reseta para o primeiro frame."""
        self.current_frame = 0


class AnimationManager:
    """Gerencia todas as animações de um tipo de pet."""

    # Canvas maior que o corpo (64px) para sobrar espaço para adereços.
    CANVAS_SIZE = 80
    BODY_DX = 8
    BODY_DY = 20

    # Configuração das animações - frames, loop, e agora o fps próprio.
    # A regra: quanto mais lento/suave, mais baixo o fps.
    ANIMATION_CONFIG = {
        "idle_breathe": {"frames": 60, "loop": True,  "fps": 4},  # MUITO lento, 4fps = respiração suave
        "idle_blink":   {"frames": 8,  "loop": False, "fps": 24}, # Rápido, piscar natural
        "idle_look":    {"frames": 16, "loop": False, "fps": 8},  # Lento e elegante
        "happy_jump":   {"frames": 20, "loop": False, "fps": 20}, # Pulo elástico
        "walk_right":   {"frames": 16, "loop": False, "fps": 8},  # Caminhada lenta
        "walk_left":    {"frames": 16, "loop": False, "fps": 8},  # Caminhada lenta
        "pet_reaction": {"frames": 12, "loop": False, "fps": 14}, # Reação ao carinho
        "yawn":         {"frames": 20, "loop": False, "fps": 8},  # Bocejo lento e natural
        "eat":          {"frames": 12, "loop": False, "fps": 10}, # Comer moderado
        "curious":      {"frames": 10, "loop": False, "fps": 8},  # Curiosidade lenta
        "sleep_enter":  {"frames": 12, "loop": False, "fps": 6},  # Entrando no sono lentamente
        "sleep_loop":   {"frames": 16, "loop": True,  "fps": 3},  # Dormindo MUITO lento
        "sleep_exit":   {"frames": 12, "loop": False, "fps": 6},  # Acordando lentamente
        "crochet":      {"frames": 20, "loop": True,  "fps": 6},  # Crochê lento e concentrado
        "music":        {"frames": 16, "loop": True,  "fps": 6},  # Música lenta
        "coffee":       {"frames": 12, "loop": True,  "fps": 5},  # Café bem lento
        "apple":        {"frames": 12, "loop": False, "fps": 8},  # Maçã
        "chocolate":    {"frames": 12, "loop": False, "fps": 8},  # Chocolate
        "water":        {"frames": 10, "loop": False, "fps": 6},  # Água lenta
    }

    # Cores de corpo do placeholder por tipo.
    # Atualizado o sapo para o verde-grama sólido do brinquedo.
    PLACEHOLDER_COLORS = {
        "frog": QColor(74, 165, 74),     # Verde grama sólido
        "rat": QColor(176, 165, 156),    # Cinza pardo
        "cat": QColor(226, 168, 108),    # Laranja acinzentado
        "robot": QColor(150, 172, 196),  # Azul metálico
    }

    def __init__(self, assets_path: Path):
        self.assets_path = assets_path
        self.pet_type = assets_path.name
        self.animations: Dict[str, AnimationData] = {}

        # Mapeamento de handlers de frame
        self._frame_handlers: Dict[str, Callable[[QPainter, int, int], None]] = {
            "idle_breathe": self._frame_idle_breathe,
            "idle_blink": self._frame_idle_blink,
            "idle_look": self._frame_idle_look,
            "happy_jump": self._frame_happy_jump,
            "walk_right": self._frame_walk_right,
            "walk_left": self._frame_walk_left,
            "pet_reaction": self._frame_pet_reaction,
            "yawn": self._frame_yawn,
            "eat": self._frame_eat,
            "curious": self._frame_curious,
            "sleep_enter": self._frame_sleep_enter,
            "sleep_loop": self._frame_sleep_loop,
            "sleep_exit": self._frame_sleep_exit,
            "crochet": self._frame_crochet,
            "music": self._frame_music,
            "coffee": self._frame_coffee,
            "apple": self._frame_apple,
            "chocolate": self._frame_chocolate,
            "water": self._frame_water,
        }

        # Carrega todas as animações
        self._load_animations()

    def _load_animations(self):
        """Carrega todas as animações do diretório de assets."""
        for anim_name, config in self.ANIMATION_CONFIG.items():
            # Sem sprite de verdade: gera cada frame como uma pose distinta.
            # O sistema de carregamento de assets está desativado para o placeholder.
            frames = [
                self._create_placeholder_frame(anim_name, idx, config["frames"])
                for idx in range(config["frames"])
            ]

            self.animations[anim_name] = AnimationData(
                name=anim_name,
                frames=frames,
                loop=config["loop"],
                fps=config.get("fps", 12),
            )

    def _create_placeholder_frame(self, animation_name: str, frame_index: int, frame_count: int) -> QPixmap:
        """Desenha a pose de um frame específico de uma animação."""
        pixmap = QPixmap(self.CANVAS_SIZE, self.CANVAS_SIZE)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        handler = self._frame_handlers.get(animation_name, self._frame_idle_breathe)
        handler(painter, frame_index, max(1, frame_count))

        painter.end()
        return pixmap

    # === Utilitários Matemáticos ===

    @staticmethod
    def _osc(i: int, n: int, cycles: float = 1.0, phase: float = 0.0) -> float:
        """Oscilador senoidal (-1..1) que fecha o ciclo exatamente no loop."""
        return math.sin(2 * math.pi * cycles * i / n + phase)

    @staticmethod
    def _norm(i: int, n: int) -> float:
        """Progresso 0..1 ao longo de uma animação não-loop."""
        return i / max(1, n - 1)

    # === Sistema de Desenho Procedural ===

    def _draw_pet(
        self,
        painter: QPainter,
        eye_state: str = "open",
        mouth_state: Optional[str] = None,
        gaze: float = 0.0,
        bounce: float = 0.0,
        tilt: float = 0.0,
        squash: float = 1.0,
        stretch: float = 1.0,
        eye_openness: float = 1.0, # 0..1 contínuo
        eye_lag: float = 0.0,      # Deslocamento vertical dos olhos
        cheek_wobble: float = 0.0, # Tremor residual da bochecha (spring)
    ):
        """
        Desenha o pet numa pose específica.

        Novos parâmetros de vida:
          eye_openness - 0..1, controla abertura contínua da pálpebra.
          eye_lag      - deslocamento vertical dos olhos que chega um frame
                         DEPOIS do corpo (secondary motion).
          cheek_wobble - tremor residual da bochecha após impacto (spring).
        """
        body_color = self.PLACEHOLDER_COLORS.get(self.pet_type, self.PLACEHOLDER_COLORS["frog"])

        # Sombra fixa no chão - encolhe um pouco quando o pet sobe.
        self._draw_shadow(painter, bounce)

        painter.save()
        painter.translate(self.BODY_DX, self.BODY_DY + bounce)

        if tilt:
            painter.translate(32, 32)
            painter.rotate(math.degrees(tilt))
            painter.translate(-32, -32)

        if squash != 1.0 or stretch != 1.0:
            painter.translate(32, 46)
            painter.scale(squash, stretch)
            painter.translate(-32, -46)

        # 1. Corpo base
        self._draw_body(painter, body_color)

        # 2. Olhos com lag
        self._draw_eyes(painter, eye_state, gaze, body_color,
                        openness=eye_openness, lag=eye_lag)

        # 3. Boca (rest se for sapo, smile padrão para os outros)
        if mouth_state is None:
            mouth_state = "rest" if self.pet_type == "frog" else "smile"
        self._draw_mouth(painter, mouth_state)

        # 4. Bochechas com wobble
        self._draw_cheeks(painter, wobble=cheek_wobble)

        painter.restore()

    def _draw_shadow(self, painter: QPainter, bounce: float):
        """Sombra suave e fixa no chão."""
        cx, cy = self.BODY_DX + 32, self.BODY_DY + 58
        lift = max(0.0, -bounce)
        scale = max(0.55, 1.0 - lift * 0.05)
        rx, ry = 20 * scale, 5 * scale

        gradient = QRadialGradient(QPointF(0, 0), 1.0)
        gradient.setColorAt(0.0, QColor(0, 0, 0, 70))
        gradient.setColorAt(1.0, QColor(0, 0, 0, 0))

        painter.save()
        painter.translate(cx, cy)
        painter.scale(rx, ry)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawEllipse(QPointF(0, 0), 1.0, 1.0)
        painter.restore()

    def _draw_body(self, painter: QPainter, body_color: QColor):
        """Corpo do pet. Atualmente especializado no sapo Foqui."""
        if self.pet_type == "frog":
            self._draw_frog_body(painter, body_color)
        else:
            # Placeholder genérico para outros tipos (desativado nesta versão)
            rect = QRect(12, 20, 40, 35)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(body_color)
            painter.drawEllipse(rect)

    def _draw_frog_body(self, painter: QPainter, body_color: QColor):
        """Corpo do sapo Foqui: blob achatado com patas e barriguinha."""
        cx = 32
        dk = body_color.darker(125)
        lt = body_color.lighter(114)

        painter.setPen(Qt.PenStyle.NoPen)

        # Corpo blob achatado (formato clássico de sapo fofo)
        body = QPainterPath()
        body.moveTo(cx - 28, 45)
        body.cubicTo(cx - 32, 30, cx - 30, 18, cx - 20, 14)
        body.cubicTo(cx - 10, 10, cx + 10, 10, cx + 20, 14)
        body.cubicTo(cx + 30, 18, cx + 32, 30, cx + 28, 45)
        body.cubicTo(cx + 26, 55, cx + 16, 60, cx, 60)
        body.cubicTo(cx - 16, 60, cx - 26, 55, cx - 28, 45)
        body.closeSubpath()

        grad = QLinearGradient(0, 10, 0, 60)
        grad.setColorAt(0.0, lt)
        grad.setColorAt(0.7, body_color)
        grad.setColorAt(1.0, dk)
        painter.setBrush(grad)
        painter.drawPath(body)

        # Patas traseiras (laterais, atrás)
        painter.setBrush(dk)
        painter.drawEllipse(QRectF(cx - 30, 45, 12, 12))
        painter.drawEllipse(QRectF(cx + 18, 45, 12, 12))

        # Patas dianteiras (3 dedinhos cada)
        for fx in (cx - 16, cx + 16):
            painter.setBrush(body_color)
            painter.drawEllipse(QRectF(fx - 8, 52, 16, 10))
            painter.setPen(QPen(dk, 1))
            for d in (-4, 0, 4):
                painter.drawLine(int(fx + d), 60, int(fx + d), 63)
            painter.setPen(Qt.PenStyle.NoPen)

        # Narinas pequenas
        painter.setBrush(dk)
        painter.drawEllipse(QPointF(cx - 4, 30), 1.3, 1.3)
        painter.drawEllipse(QPointF(cx + 4, 30), 1.3, 1.3)

    def _draw_cheeks(self, painter: QPainter, wobble: float = 0.0):
        """Bochechas rosadas com wobble (tremor residual)."""
        if self.pet_type != "frog": return # Apenas sapo tem bochechas nesta versão

        for cx in (15, 49):
            # O tremor empurra a bochecha um pouco pros lados/baixo
            wx = cx + wobble * 1.2
            wy = 36 + abs(wobble) * 0.8
            gradient = QRadialGradient(QPointF(wx, wy), 7)
            gradient.setColorAt(0.0, QColor(255, 190, 190, 150))
            gradient.setColorAt(1.0, QColor(255, 190, 190, 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(gradient)
            painter.drawEllipse(QPointF(wx, wy), 7, 5)

    def _draw_eyes(self, painter: QPainter, state: str = "open", gaze: float = 0.0,
                   body_color: Optional[QColor] = None, openness: float = 1.0, lag: float = 0.0):
        """Olhos - Atualmente especializado no sapo Foqui."""
        if self.pet_type == "frog":
            self._draw_frog_eyes(painter, state, gaze, body_color, openness, lag)
        else:
            # Placeholder genérico (desativado)
            pass

    def _draw_frog_eyes(self, painter: QPainter, state: str, gaze: float,
                        body_color: Optional[QColor], openness: float, lag: float):
        """Olhos do sapo: grandes domos projetados pra cima com abertura contínua."""
        base = body_color or self.PLACEHOLDER_COLORS["frog"]
        dome = base.lighter(114)
        dk = base.darker(125)
        cx = 32
        
        # Centros dos dois olhos, projetados acima do corpo
        gaze_dx = max(-1.2, min(1.2, gaze))
        eyes = [(cx - 10, 17 + lag), (cx + 10, 17 + lag)]

        wide = state == "wide"
        
        for (ex, ey) in eyes:
            # Domo verde (base do olho)
            painter.setBrush(dome)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(ex, ey), 10, 10)

            # Esfera branca (encolhe em altura conforme fecha)
            painter.setBrush(QColor(246, 249, 246))
            white_h = 16 * openness
            painter.drawEllipse(QRectF(ex - 8, ey - white_h / 2, 16, white_h))

            # Pupila preta (só aparece se aberto o bastante)
            if openness > 0.4:
                pr = 4.6 if wide else 4.2
                painter.setBrush(QColor(22, 22, 22))
                painter.drawEllipse(QPointF(ex + gaze_dx * 3.5, ey + 0.5), pr, pr)

    def _draw_mouth(self, painter: QPainter, state: str):
        """Boca do pet. Atualmente especializado no sapo Foqui."""
        if self.pet_type == "frog":
            self._draw_frog_mouth(painter, state)
        else:
            # Placeholder genérico (desativado)
            pass

    def _draw_frog_mouth(self, painter: QPainter, state: str):
        """Boca do sapo: uma linha larga e plácida."""
        cx = 32
        dk = self.PLACEHOLDER_COLORS["frog"].darker(135)

        painter.setPen(QPen(dk, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if state == "rest":
            painter.drawLine(cx - 17, 38, cx + 17, 38)
        # Outros estados (open_small, open_wide, content) não são implementados
        # nesta versão simplificada do placeholder de arte.

    # === Poses por animação ===

    def _frame_idle_breathe(self, painter: QPainter, i: int, n: int):
        # Respiração muito suave e natural
        phase = (i % n) / n
        b = breathe(phase, amplitude=0.15, frequency=0.5)  # Respiração MUITO suave
        signed = b * 2 - 1  # -1..1
        
        # lag: usa a fase anterior pra posicionar o olho um passo atrás
        prev_phase = ((i - 1) % n) / n
        b_prev = breathe(prev_phase, amplitude=0.15, frequency=0.5) * 2 - 1
        eye_lag = (signed - b_prev) * 1.5

        # Blink ocasional sutil
        blink_at = int(n * 0.7)
        openness = 1.0
        if blink_at <= i < blink_at + 2:
            openness = blink_curve((i - blink_at) / 2)

        self._draw_pet(
            painter,
            bounce=-0.8 * signed,  # Movimento bem sutil
            squash=1.0 - 0.015 * signed,  # Menos compressão
            stretch=1.0 + 0.025 * signed,  # Menos esticamento
            eye_openness=openness,
            eye_lag=eye_lag,
            mouth_state="rest"  # Boca de repouso
        )

    def _frame_idle_blink(self, painter: QPainter, i: int, n: int):
        # Blink rápido e natural - os olhos fecham e abrem suavemente
        t = self._norm(i, n)
        
        # Blink curve: fecha nos primeiros 20%, fica fechado no meio, abre depois
        if t < 0.2:
            # Fechando - rápido
            openness = 1.0 - (t / 0.2) * 0.9  # 1.0 -> 0.1
        elif t < 0.4:
            # Fechado por um pouco
            openness = 0.1
        else:
            # Abrindo - um pouco mais lento
            openness = 0.1 + ((t - 0.4) / 0.6) * 0.9  # 0.1 -> 1.0
        
        self._draw_pet(painter, eye_openness=openness, mouth_state="rest")

    def _frame_idle_look(self, painter: QPainter, i: int, n: int):
        # Olhar em volta com antecipação (back leve).
        t = self._norm(i, n)
        # Vai de 0 -> direita -> centro
        swing = math.sin(math.pi * t)              # 0..1..0
        
        # Antecipação no arranque
        antecip = -0.25 * (1 - ease_out_cubic(min(1.0, t * 4))) if t < 0.25 else 0.0
        final_gaze = swing + antecip
        self._draw_pet(painter, gaze=final_gaze, tilt=final_gaze * 0.07)

    def _frame_happy_jump(self, painter: QPainter, i: int, n: int):
        # Pulo com física e sec-motion (squash/stretch, hang time, eye lag, cheek wobble).
        t = self._norm(i, n)

        cheek_wobble = 0.0
        eye_lag = 0.0

        if t < 0.18:
            # anticipation: agacha comprimindo
            c = ease_in_cubic(t / 0.18)
            squash, stretch, bounce = 1.0 + 0.14 * c, 1.0 - 0.09 * c, 2.0 * c
        elif t < 0.5:
            # subida: ease_out
            u = ease_out_cubic((t - 0.18) / 0.32)
            bounce = -14 * u
            stretch = 1.0 + 0.1 * (1 - u)          # estica na decolagem
            squash = 1.0 - 0.06 * (1 - u)
            eye_lag = 2.0 * u                       # olhos ficam pra trás subindo
        elif t < 0.62:
            # hang time: quase parado no ápice
            bounce = -14 + 1.5 * ((t - 0.5) / 0.12)
            stretch, squash = 1.0, 1.0
        elif t < 0.82:
            # queda: ease_in (gravidade)
            d = ease_in_cubic((t - 0.62) / 0.2)
            bounce = -12.5 + 14.5 * d
            stretch = 1.0 + 0.08 * d                # estica na queda
            squash = 1.0 - 0.05 * d
            eye_lag = -1.5 * d                      # olhos pra frente caindo
        else:
            # impacto + amortecimento elástico
            s = (t - 0.82) / 0.18
            squash = 1.0 + 0.16 * (1 - ease_out_cubic(s))
            stretch = 1.0 - 0.1 * (1 - ease_out_cubic(s))
            bounce = 2.0 * (1 - ease_out_cubic(s))
            cheek_wobble = spring_settle(s) * 3.0   # bochecha treme e assenta

        self._draw_pet(
            painter,
            bounce=bounce,
            squash=squash,
            stretch=stretch,
            eye_lag=eye_lag,
            cheek_wobble=cheek_wobble,
        )

    def _frame_walk_right(self, painter: QPainter, i: int, n: int):
        # Caminhada para a direita com balanço natural
        t = self._norm(i, n)
        progress = t * 15  # Movimento horizontal
        bounce = -math.sin(math.pi * t) * 2  # Salto ao caminhar
        tilt = math.sin(2 * math.pi * t) * 0.05  # Oscilação
        
        painter.save()
        painter.translate(progress, 0)  # Move para a direita
        self._draw_pet(painter, bounce=bounce, tilt=tilt)
        painter.restore()

    def _frame_walk_left(self, painter: QPainter, i: int, n: int):
        # Caminhada para a esquerda com balanço natural
        t = self._norm(i, n)
        progress = -t * 15  # Movimento horizontal (esquerda)
        bounce = -math.sin(math.pi * t) * 2  # Salto ao caminhar
        tilt = -math.sin(2 * math.pi * t) * 0.05  # Oscilação
        
        painter.save()
        painter.translate(progress, 0)  # Move para a esquerda
        self._draw_pet(painter, bounce=bounce, tilt=tilt)
        painter.restore()

    def _frame_pet_reaction(self, painter: QPainter, i: int, n: int):
        # Reação ao carinho - pulo pequeno e tremor
        t = self._norm(i, n)
        
        if t < 0.3:
            # Pulo inicial
            b = ease_out_cubic(t / 0.3)
            bounce = -8 * b
            squash = 1.0 + 0.1 * b
            stretch = 1.0 - 0.06 * b
        else:
            # Amortecimento
            s = (t - 0.3) / 0.7
            bounce = -8 * (1 - ease_out_cubic(s))
            squash = 1.0 + 0.1 * (1 - ease_out_cubic(s))
            stretch = 1.0 - 0.06 * (1 - ease_out_cubic(s))
        
        self._draw_pet(painter, bounce=bounce, squash=squash, stretch=stretch)

    def _frame_yawn(self, painter: QPainter, i: int, n: int):
        # Bocejo - abre a boca bem grande
        t = self._norm(i, n)
        
        # Primeiro abre a boca (0 a 0.4), depois fecha (0.4 a 1.0)
        if t < 0.4:
            mouth_state = "smile"  # Placeholder - seria "yawn" num sistema real
            eye_openness = ease_out_cubic(t / 0.4)
        else:
            mouth_state = "smile"
            eye_openness = ease_in_cubic((1.0 - t) / 0.6)
        
        self._draw_pet(painter, mouth_state=mouth_state, eye_openness=eye_openness)

    def _frame_eat(self, painter: QPainter, i: int, n: int):
        # Comendo - movimento repetido de mastigação
        t = self._norm(i, n)
        squash = 1.0 + 0.08 * math.sin(t * 6 * math.pi)  # Mastigação rítmica
        bounce = math.sin(t * 4 * math.pi) * 1.5  # Movimentação
        
        self._draw_pet(painter, squash=squash, bounce=bounce)

    def _frame_curious(self, painter: QPainter, i: int, n: int):
        # Pose curiosa - cabeça inclinada, olhando para cima
        t = self._norm(i, n)
        tilt = ease_in_out_sine(t) * 0.15  # Inclinação de cabeça
        gaze = math.sin(math.pi * t) * 0.5  # Olhar explorando
        
        self._draw_pet(painter, tilt=tilt, gaze=gaze)

    def _frame_sleep_enter(self, painter: QPainter, i: int, n: int):
        # Entrando no sono - pisca e vai fechando os olhos
        t = self._norm(i, n)
        openness = ease_in_cubic(1.0 - t)  # Fecha os olhos gradualmente
        bounce = -math.sin(math.pi * t) * 0.5  # Movimento para baixo
        
        self._draw_pet(painter, eye_openness=openness, bounce=bounce)

    def _frame_sleep_loop(self, painter: QPainter, i: int, n: int):
        # Dormindo - respiração leve com olhos fechados
        t = self._norm(i, n)
        bounce = breathe(t, amplitude=0.5, frequency=0.5)  # Respiração bem lenta
        
        self._draw_pet(painter, eye_openness=0.0, bounce=bounce - 1.0)

    def _frame_sleep_exit(self, painter: QPainter, i: int, n: int):
        # Acordando - estica e abre os olhos
        t = self._norm(i, n)
        openness = ease_out_cubic(t)  # Abre os olhos gradualmente
        bounce = math.sin(math.pi * t * 0.5) * 1.5  # Movimento de despertar
        stretch = 1.0 + 0.1 * ease_in_cubic(t)  # Esticada
        
        self._draw_pet(painter, eye_openness=openness, bounce=bounce, stretch=stretch)

    def _frame_crochet(self, painter: QPainter, i: int, n: int):
        # Crochê - movimento de mãos repetido
        t = self._norm(i, n)
        squash = 1.0 + 0.05 * math.sin(t * 8 * math.pi)  # Movimento de tecelagem
        gaze = 0.3  # Olhando para o trabalho
        
        self._draw_pet(painter, squash=squash, gaze=gaze)

    def _frame_music(self, painter: QPainter, i: int, n: int):
        # Ouvindo música - balanço ritmado
        t = self._norm(i, n)
        tilt = math.sin(t * 4 * math.pi) * 0.1  # Balanço
        bounce = math.sin(t * 4 * math.pi) * 2  # Pulo ritmado
        
        self._draw_pet(painter, tilt=tilt, bounce=bounce)

    def _frame_coffee(self, painter: QPainter, i: int, n: int):
        # Tomando café - movimento de beber
        t = self._norm(i, n)
        
        # Sobe e desce a cada segundo
        phase = (t * 2) % 1.0
        if phase < 0.3:
            bounce = ease_out_cubic(phase / 0.3) * 3  # Sobe
        else:
            bounce = ease_in_cubic((1.0 - phase) / 0.7) * 3  # Desce
        
        self._draw_pet(painter, bounce=bounce)

    def _frame_apple(self, painter: QPainter, i: int, n: int):
        # Comendo maçã - similar ao eat genérico
        t = self._norm(i, n)
        squash = 1.0 + 0.1 * math.sin(t * 6 * math.pi)
        
        self._draw_pet(painter, squash=squash)

    def _frame_chocolate(self, painter: QPainter, i: int, n: int):
        # Comendo chocolate - satisfeito
        t = self._norm(i, n)
        bounce = -math.sin(math.pi * t) * 1.5  # Pequeno pulo de alegria
        squash = 1.0 + 0.08 * math.sin(t * 5 * math.pi)
        
        self._draw_pet(painter, bounce=bounce, squash=squash)

    def _frame_water(self, painter: QPainter, i: int, n: int):
        # Bebendo água - movimento de beber
        t = self._norm(i, n)
        
        # Desce para beber, volta
        if t < 0.5:
            bounce = -ease_out_cubic(t / 0.5) * 4
        else:
            bounce = -4 + ease_in_cubic((t - 0.5) / 0.5) * 4
        
        self._draw_pet(painter, bounce=bounce)

    # === API Pública ===

    def get_frame(self, animation_name: str) -> Optional[QPixmap]:
        """Retorna o frame atual de uma animação."""
        if animation_name in self.animations:
            return self.animations[animation_name].get_frame()
        return None

    def get_frame_interval(self, animation_name: str) -> int:
        """Retorna o intervalo (ms) entre frames desta animação."""
        if animation_name in self.animations:
            return self.animations[animation_name].frame_interval_ms
        return 83  # ~12fps default

    def advance_frame(self, animation_name: str) -> bool:
        """
        Avança o frame de uma animação.
        Retorna True se a animação terminou.
        """
        if animation_name in self.animations:
            return self.animations[animation_name].advance()
        return False

    def reset_animation(self, animation_name: str):
        """Reseta uma animação para o primeiro frame."""
        if animation_name in self.animations:
            self.animations[animation_name].reset()

    def get_animation_names(self) -> List[str]:
        """Retorna lista de nomes de animações disponíveis."""
        return list(self.animations.keys())