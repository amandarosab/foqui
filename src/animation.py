"""
AnimationManager - Gerencia sprite sheets e frames de animação

Sem arte de verdade ainda, cada frame é desenhado em código. O que importa
aqui é que cada animação seja uma sequência de POSES diferentes - corpo,
olhos, boca e adereços mudando frame a frame - e não uma imagem estática
repetida. É isso que faz o pet parecer vivo.
"""

import math
from pathlib import Path
from typing import Callable, Dict, Optional, List

from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QPolygon, QPen, QFont,
    QLinearGradient, QRadialGradient,
)
from PyQt6.QtCore import Qt, QPoint, QPointF, QRect


class AnimationData:
    """Dados de uma animação específica."""

    def __init__(self, name: str, frames: List[QPixmap], loop: bool = True):
        self.name = name
        self.frames = frames
        self.loop = loop
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

    # Canvas maior que o corpo (64px) para sobrar espaço para adereços que
    # passam da cabeça: notas de música, vapor de café, zzz de sono etc.
    CANVAS_SIZE = 80
    BODY_DX = 8
    BODY_DY = 20

    # Configuração das animações - quantos frames cada uma tem e se repete.
    ANIMATION_CONFIG = {
        "idle_breathe": {"frames": 16, "loop": True},
        "idle_blink": {"frames": 4, "loop": False},
        "idle_look": {"frames": 12, "loop": False},
        "walk_right": {"frames": 18, "loop": True},
        "walk_left": {"frames": 18, "loop": True},
        "sleep_enter": {"frames": 5, "loop": False},
        "sleep_loop": {"frames": 16, "loop": True},
        "sleep_exit": {"frames": 5, "loop": False},
        "yawn": {"frames": 8, "loop": False},
        "eat": {"frames": 10, "loop": False},
        "pet_reaction": {"frames": 8, "loop": False},
        "happy_jump": {"frames": 14, "loop": False},
        "curious": {"frames": 6, "loop": False},
        # Animações temáticas - pequenas cenas que dão personalidade ao pet
        "crochet": {"frames": 16, "loop": False},
        "music": {"frames": 16, "loop": False},
        "coffee": {"frames": 14, "loop": False},
        "apple": {"frames": 14, "loop": False},
        "chocolate": {"frames": 12, "loop": False},
        "water": {"frames": 12, "loop": False},
    }

    # Cores de corpo do placeholder por tipo - sem arte de verdade ainda,
    # mas dá pra distinguir os pets a olho nu enquanto isso.
    PLACEHOLDER_COLORS = {
        "frog": QColor(134, 194, 156),   # verde menta
        "rat": QColor(176, 165, 156),    # cinza pardo
        "cat": QColor(226, 168, 108),    # laranja acinzentado
        "robot": QColor(150, 172, 196),  # azul metálico
    }

    # Cores usadas nos adereços temáticos - fixas, não dependem do tipo de
    # pet, pra manter a identidade do hobby reconhecível em qualquer skin.
    YARN_COLOR = QColor(214, 110, 140)
    NOTE_COLORS = [
        QColor(240, 90, 90),
        QColor(240, 200, 60),
        QColor(90, 180, 240),
        QColor(120, 210, 130),
    ]

    def __init__(self, assets_path: Path):
        self.assets_path = assets_path
        self.pet_type = assets_path.name
        self.animations: Dict[str, AnimationData] = {}

        # Uma função por animação, responsável por desenhar a pose de um
        # frame específico. Precisa existir antes de _load_animations rodar.
        self._frame_handlers: Dict[str, Callable[[QPainter, int, int], None]] = {
            "idle_breathe": self._frame_idle_breathe,
            "idle_blink": self._frame_idle_blink,
            "idle_look": self._frame_idle_look,
            "walk_right": self._frame_walk_right,
            "walk_left": self._frame_walk_left,
            "sleep_enter": self._frame_sleep_enter,
            "sleep_loop": self._frame_sleep_loop,
            "sleep_exit": self._frame_sleep_exit,
            "yawn": self._frame_yawn,
            "eat": self._frame_eat,
            "pet_reaction": self._frame_pet_reaction,
            "happy_jump": self._frame_happy_jump,
            "curious": self._frame_curious,
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
            frames = self._load_animation_frames(anim_name, config["frames"])

            # Sem sprite de verdade: gera cada frame como uma pose distinta,
            # nunca repete a mesma imagem em todos os frames.
            if not frames:
                frames = [
                    self._create_placeholder_frame(anim_name, idx, config["frames"])
                    for idx in range(config["frames"])
                ]

            self.animations[anim_name] = AnimationData(
                name=anim_name,
                frames=frames,
                loop=config["loop"]
            )

    def _load_animation_frames(self, animation_name: str, frame_count: int) -> List[QPixmap]:
        """
        Carrega frames de uma animação.
        Tenta carregar sprite sheet primeiro, depois frames individuais.
        """
        frames = []

        # Tenta carregar sprite sheet
        sprite_sheet_path = self.assets_path / f"{animation_name}.png"
        if sprite_sheet_path.exists():
            sprite_sheet = QPixmap(str(sprite_sheet_path))
            if not sprite_sheet.isNull():
                frame_width = sprite_sheet.width() // frame_count
                frame_height = sprite_sheet.height()

                for i in range(frame_count):
                    frame = sprite_sheet.copy(
                        i * frame_width, 0,
                        frame_width, frame_height
                    )
                    frames.append(frame)

                return frames

        # Tenta carregar frames individuais
        for i in range(frame_count):
            frame_path = self.assets_path / f"{animation_name}_{i}.png"
            if frame_path.exists():
                frame = QPixmap(str(frame_path))
                if not frame.isNull():
                    frames.append(frame)

        return frames

    # === Geração procedural de frames ===

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

    @staticmethod
    def _osc(i: int, n: int, cycles: float = 1.0, phase: float = 0.0) -> float:
        """Oscilador senoidal (-1..1) que fecha o ciclo exatamente no loop."""
        return math.sin(2 * math.pi * cycles * i / n + phase)

    @staticmethod
    def _hump(i: int, n: int) -> float:
        """Sobe e desce suavemente uma vez só (0 -> 1 -> 0), para gestos únicos."""
        return math.sin(math.pi * min(i, n) / n)

    def _draw_pet(
        self,
        painter: QPainter,
        eye_state: str = "open",
        mouth_state: str = "smile",
        gaze: float = 0.0,
        bounce: float = 0.0,
        tilt: float = 0.0,
        squash: float = 1.0,
        stretch: float = 1.0,
        extra: Optional[Callable[[QPainter], None]] = None,
    ):
        """
        Desenha o pet numa pose específica. `extra`, se passado, é chamado
        por último, ainda dentro da transformação do corpo - serve para
        adereços que precisam se mexer junto com ele (fone, xícara, maçã...).
        """
        body_color = self.PLACEHOLDER_COLORS.get(self.pet_type, self.PLACEHOLDER_COLORS["frog"])

        # Sombra fixa no chão - não acompanha o bounce, só encolhe um
        # pouco quando o pet sobe, pra dar noção de profundidade.
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

        # Acessórios atrás do corpo (orelhas, antena) para não ficarem escondidos
        self._draw_accessory_back(painter)

        self._draw_body(painter, body_color)
        self._draw_eyes(painter, eye_state, gaze, body_color)
        self._draw_mouth(painter, mouth_state)
        self._draw_cheeks(painter)

        # Acessórios na frente do corpo (bigodes, focinho)
        self._draw_accessory_front(painter, body_color)

        if extra:
            extra(painter)

        painter.restore()

    def _draw_shadow(self, painter: QPainter, bounce: float):
        """Sombra suave e fixa no chão, atrás de qualquer transformação do
        corpo - dá noção de profundidade sem se mexer junto com o bounce."""
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
        """Corpo com gradiente (claro em cima, mais fechado embaixo) e um
        brilho sutil no topo - traço mais fofinho que uma cor chapada."""
        rect = QRect(12, 20, 40, 35)

        gradient = QLinearGradient(0, rect.top(), 0, rect.bottom())
        gradient.setColorAt(0.0, body_color.lighter(122))
        gradient.setColorAt(1.0, body_color)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawEllipse(rect)

        painter.setBrush(QColor(255, 255, 255, 35))
        painter.drawEllipse(18, 24, 20, 10)

    def _draw_cheeks(self, painter: QPainter):
        """Bochechas com gradiente radial (esmaece nas bordas) em vez de
        uma elipse sólida - efeito parecido com o blur do protótipo CSS."""
        for cx in (15, 49):
            gradient = QRadialGradient(QPointF(cx, 36), 7)
            gradient.setColorAt(0.0, QColor(255, 190, 190, 150))
            gradient.setColorAt(1.0, QColor(255, 190, 190, 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(gradient)
            painter.drawEllipse(QPointF(cx, 36), 7, 5)

    def _draw_eyes(self, painter: QPainter, state: str = "open", gaze: float = 0.0, body_color: Optional[QColor] = None):
        """Olhos - redondos por padrão, quadrados (estilo LED) para o robô."""
        eye_pupil = QColor(40, 40, 40)
        outline = (body_color or self.PLACEHOLDER_COLORS["frog"]).darker(140)

        if self.pet_type == "robot":
            led_bright = QColor(120, 220, 255)
            led_dim = QColor(70, 120, 145)

            if state == "closed":
                painter.setPen(QPen(led_bright, 3))
                painter.drawLine(18, 20, 30, 20)
                painter.drawLine(34, 20, 46, 20)
                return

            color = led_dim if state == "half" else led_bright
            height = 5 if state == "half" else 10
            y = 17 if state == "half" else 15

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(17, y, 13, height, 2, 2)
            painter.drawRoundedRect(34, y, 13, height, 2, 2)
            return

        if state == "closed":
            painter.setPen(QPen(eye_pupil, 2))
            painter.drawLine(18, 20, 30, 20)
            painter.drawLine(34, 20, 46, 20)
            return

        if state == "happy":
            painter.setPen(QPen(eye_pupil, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(QRect(17, 12, 14, 14), 20 * 16, 140 * 16)
            painter.drawArc(QRect(33, 12, 14, 14), 20 * 16, 140 * 16)
            return

        eye_white = QColor(255, 255, 255)
        gaze_dx = max(-3.0, min(3.0, gaze * 4))
        height = 8 if state == "half" else 16
        y_off = 16 if state == "half" else 12

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(eye_white)
        painter.drawEllipse(16, y_off, 16, height)
        painter.drawEllipse(32, y_off, 16, height)

        pupil_size = 8 if state == "wide" else 6
        pupil_y = y_off + max(1, height // 2 - pupil_size // 2)
        painter.setBrush(eye_pupil)
        painter.drawEllipse(QPointF(22 + gaze_dx, pupil_y + pupil_size / 2), pupil_size / 2, pupil_size / 2)
        painter.drawEllipse(QPointF(38 + gaze_dx, pupil_y + pupil_size / 2), pupil_size / 2, pupil_size / 2)

    def _draw_mouth(self, painter: QPainter, state: str = "smile"):
        """Boca - muda de forma pra transmitir o que o pet tá fazendo."""
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if state == "smile":
            painter.drawArc(QRect(22, 30, 20, 12), 0, -180 * 16)
        elif state == "content":
            painter.drawLine(26, 36, 38, 36)
        elif state == "closed":
            painter.drawLine(27, 34, 37, 34)
        elif state == "open_small":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(110, 55, 55))
            painter.drawEllipse(27, 30, 10, 8)
        elif state == "open_wide":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(110, 55, 55))
            painter.drawEllipse(21, 25, 22, 18)
        elif state == "surprised":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(110, 55, 55))
            painter.drawEllipse(28, 28, 8, 10)

    def _draw_accessory_back(self, painter: QPainter):
        """Orelhas ou antena, desenhadas antes do corpo para ficarem atrás dele."""
        accent = QColor(80, 80, 80)

        if self.pet_type == "cat":
            painter.setBrush(self.PLACEHOLDER_COLORS["cat"])
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(QPolygon([QPoint(14, 16), QPoint(20, 2), QPoint(26, 16)]))
            painter.drawPolygon(QPolygon([QPoint(38, 16), QPoint(44, 2), QPoint(50, 16)]))

        elif self.pet_type == "rat":
            painter.setBrush(QColor(210, 190, 180, 220))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(10, 6, 12, 12)
            painter.drawEllipse(42, 6, 12, 12)
            # Rabo, saindo de trás do corpo
            painter.setPen(QColor(190, 170, 160))
            painter.drawLine(48, 45, 60, 56)

        elif self.pet_type == "robot":
            painter.setPen(accent)
            painter.drawLine(32, 8, 32, 2)
            painter.setBrush(QColor(255, 140, 140))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(28, -2, 8, 8)

    def _draw_accessory_front(self, painter: QPainter, body_color: QColor):
        """Bigodes, focinho ou outros detalhes por cima do corpo."""
        if self.pet_type == "cat":
            painter.setPen(QColor(90, 90, 90))
            painter.drawLine(6, 34, 18, 32)
            painter.drawLine(6, 40, 18, 40)
            painter.drawLine(46, 32, 58, 34)
            painter.drawLine(46, 40, 58, 40)

        elif self.pet_type == "rat":
            painter.setBrush(QColor(90, 90, 90))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(29, 26, 6, 5)

    # === Poses por animação ===
    # Cada função aqui é chamada uma vez por frame e decide como o corpo,
    # os olhos, a boca e os adereços mudam ao longo da animação.

    def _frame_idle_breathe(self, painter: QPainter, i: int, n: int):
        t = self._osc(i, n, cycles=1.0)
        self._draw_pet(
            painter,
            bounce=-1.2 * t,
            squash=1.0 - 0.02 * t,
            stretch=1.0 + 0.035 * t,
        )

    def _frame_idle_blink(self, painter: QPainter, i: int, n: int):
        states = ["open", "half", "closed", "half"]
        state = states[min(i, len(states) - 1)]
        self._draw_pet(painter, eye_state=state)

    def _frame_idle_look(self, painter: QPainter, i: int, n: int):
        gaze = self._osc(i, n, cycles=1.0)
        self._draw_pet(painter, gaze=gaze, tilt=gaze * 0.06)

    def _frame_walk(self, painter: QPainter, i: int, n: int, direction: int):
        hop_raw = self._osc(i, n, cycles=2.0)
        hop = abs(hop_raw)

        def feet(p: QPainter):
            p.setBrush(QColor(70, 70, 70, 160))
            p.setPen(Qt.PenStyle.NoPen)
            # Pé alternado segue o mesmo osc. do salto - continua em fase
            # com o corpo não importa quantos frames a animação tenha.
            step = 4 if hop_raw >= 0 else -4
            p.drawEllipse(18 + step, 52, 10, 6)
            p.drawEllipse(36 - step, 52, 10, 6)

        self._draw_pet(
            painter,
            gaze=direction * 0.5,
            bounce=-6 * hop,
            squash=1.0 - 0.08 * hop,
            stretch=1.0 + 0.08 * hop,
            tilt=direction * 0.10,
            extra=feet,
        )

    def _frame_walk_right(self, painter: QPainter, i: int, n: int):
        self._frame_walk(painter, i, n, direction=1)

    def _frame_walk_left(self, painter: QPainter, i: int, n: int):
        self._frame_walk(painter, i, n, direction=-1)

    def _frame_sleep_enter(self, painter: QPainter, i: int, n: int):
        states = ["open", "half", "half", "closed", "closed"]
        state = states[min(i, len(states) - 1)]
        t = i / max(1, n - 1)
        self._draw_pet(
            painter,
            eye_state=state,
            mouth_state="content",
            bounce=6 * t,
            squash=1.0 + 0.12 * t,
            stretch=1.0 - 0.08 * t,
        )

    def _frame_sleep_loop(self, painter: QPainter, i: int, n: int):
        breathe = self._osc(i, n, cycles=1.0)

        def zzz(p: QPainter):
            for k in range(3):
                phase = (i / n + k * 0.33) % 1.0
                alpha = int(230 * math.sin(math.pi * phase))
                if alpha <= 0:
                    continue
                size = 6 + k * 3
                x = 44 + k * 6
                y = 4 - int(10 * phase) - k * 2
                p.setPen(QColor(120, 140, 200, max(0, min(255, alpha))))
                p.setFont(QFont("Arial", size, QFont.Weight.Bold))
                p.drawText(x, y, "z")

        self._draw_pet(
            painter,
            eye_state="closed",
            mouth_state="content",
            bounce=6 - 1.0 * breathe,
            squash=1.12 - 0.02 * breathe,
            stretch=0.92 + 0.02 * breathe,
            extra=zzz,
        )

    def _frame_sleep_exit(self, painter: QPainter, i: int, n: int):
        states = ["closed", "closed", "half", "half", "open"]
        state = states[min(i, len(states) - 1)]
        t = 1 - i / max(1, n - 1)
        self._draw_pet(
            painter,
            eye_state=state,
            bounce=6 * t,
            squash=1.0 + 0.12 * t,
            stretch=1.0 - 0.08 * t,
        )

    def _frame_yawn(self, painter: QPainter, i: int, n: int):
        mouths = ["smile", "open_small", "open_wide", "open_wide", "open_wide", "open_small", "content", "smile"]
        eyes = ["open", "half", "closed", "closed", "closed", "half", "open", "open"]
        idx = min(i, len(mouths) - 1)
        hump = self._hump(i, n)

        self._draw_pet(
            painter,
            eye_state=eyes[idx],
            mouth_state=mouths[idx],
            bounce=-2 * hump,
            squash=1.0 - 0.03 * hump,
            stretch=1.0 + 0.06 * hump,
        )

    def _frame_eat(self, painter: QPainter, i: int, n: int):
        bite_stage = min(3, i // 3)
        mouth = "open_small" if i % 2 == 0 else "closed"
        if i >= n - 2:
            mouth = "content"

        def snack(p: QPainter):
            size = max(0, 14 - bite_stage * 4)
            if size <= 0:
                return
            approach = min(1.0, i / 3)
            x = int(50 - approach * 16)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(214, 178, 122))
            p.drawEllipse(x, 30, size, size)

        self._draw_pet(painter, mouth_state=mouth, extra=snack)

    def _frame_pet_reaction(self, painter: QPainter, i: int, n: int):
        def heart(p: QPainter):
            stage = i / max(1, n - 1)
            if stage < 0.15 or stage > 0.9:
                return
            alpha = int(255 * math.sin(math.pi * min(1.0, (stage - 0.15) / 0.6)))
            scale = 0.6 + 0.6 * stage
            r = 5 * scale
            cx, cy = 32, -2 - int(6 * stage)

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(235, 90, 120, max(0, min(255, alpha))))
            p.drawEllipse(QPointF(cx - r * 0.6, cy), r, r)
            p.drawEllipse(QPointF(cx + r * 0.6, cy), r, r)
            p.drawPolygon(QPolygon([
                QPoint(int(cx - r * 1.1), int(cy + r * 0.3)),
                QPoint(int(cx + r * 1.1), int(cy + r * 0.3)),
                QPoint(int(cx), int(cy + r * 2)),
            ]))

        # O corpo fica parado - só o coraçãozinho aparece e some por cima.
        self._draw_pet(
            painter,
            eye_state="happy",
            mouth_state="content",
            extra=heart,
        )

    def _frame_happy_jump(self, painter: QPainter, i: int, n: int):
        # Curva suave: agachar, subir, pairar um instante, descer, aterrissar.
        # Espalhada por mais frames pra não parecer um "pulo" instantâneo.
        t = i / max(1, n - 1)

        if t < 0.2:
            crouch = t / 0.2
            squash, stretch, bounce = 1.0 + 0.1 * crouch, 1.0 - 0.06 * crouch, 1.5 * crouch
        elif t < 0.8:
            arc = math.sin(math.pi * (t - 0.2) / 0.6)
            bounce = -10 * arc
            stretch = 1.0 + 0.05 * arc
            squash = 1.0 - 0.03 * arc
        else:
            land = (t - 0.8) / 0.2
            squash = 1.0 + 0.08 * (1 - land)
            stretch = 1.0 - 0.05 * (1 - land)
            bounce = 1.5 * (1 - land)

        self._draw_pet(
            painter,
            eye_state="happy",
            mouth_state="open_small",
            bounce=bounce,
            squash=squash,
            stretch=stretch,
        )

    def _frame_curious(self, painter: QPainter, i: int, n: int):
        hump = self._hump(i, n)
        self._draw_pet(painter, eye_state="wide", gaze=0.6 * hump, tilt=0.18 * hump)

    # --- Animações temáticas ---

    def _frame_crochet(self, painter: QPainter, i: int, n: int):
        hook_phase = self._osc(i, n, cycles=3.0)
        stitches_done = min(5, i // 3)

        def props(p: QPainter):
            p.save()
            p.translate(2, 38)

            # Novelo de lã
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self.YARN_COLOR)
            p.drawEllipse(0, 6, 16, 16)
            p.setPen(QPen(self.YARN_COLOR.darker(115), 1))
            p.drawLine(4, 10, 12, 18)
            p.drawLine(12, 10, 4, 18)

            # Fio até a agulha
            p.setPen(QPen(self.YARN_COLOR, 1))
            p.drawLine(14, 12, 30, 4)

            # Agulha de crochê, balançando como se estivesse fisgando pontos
            p.save()
            p.translate(30, 4)
            p.rotate(-20 + hook_phase * 18)
            p.setPen(QPen(QColor(200, 200, 210), 2))
            p.drawLine(0, 0, 10, -2)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(200, 200, 210))
            p.drawEllipse(8, -5, 4, 4)
            p.restore()

            # Carreira de pontos já feitos, crescendo aos poucos
            for k in range(stitches_done):
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(self.YARN_COLOR.lighter(115))
                p.drawEllipse(18 + k * 5, 18, 5, 5)

            p.restore()

        self._draw_pet(painter, eye_state="half", mouth_state="content", gaze=-0.3, extra=props)

    def _frame_music(self, painter: QPainter, i: int, n: int):
        # Notas piscando tipo pisca-pisca, atrás/acima da cabeça
        positions = [(6, 8), (60, 10), (18, 2), (46, 0), (34, 16)]
        for idx, (x, y) in enumerate(positions):
            phase = 2 * math.pi * idx / len(positions)
            twinkle = (math.sin(2 * math.pi * 2 * i / n + phase) + 1) / 2
            color = QColor(self.NOTE_COLORS[idx % len(self.NOTE_COLORS)])
            color.setAlpha(int(60 + twinkle * 190))

            painter.setPen(QPen(color, 2))
            painter.drawLine(x, y, x, y - 8)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(x - 3, y - 3, 6, 5)

        def headphones(p: QPainter):
            p.setPen(QPen(QColor(50, 50, 55), 3))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(QRect(10, -6, 44, 40), 20 * 16, 140 * 16)

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(50, 50, 55))
            p.drawRoundedRect(6, 22, 12, 18, 4, 4)
            p.drawRoundedRect(46, 22, 12, 18, 4, 4)
            p.setBrush(QColor(80, 80, 90))
            p.drawRoundedRect(8, 25, 8, 12, 3, 3)
            p.drawRoundedRect(48, 25, 8, 12, 3, 3)

        # A cabeça fica parada - só o fone e as notas atrás se mexem.
        self._draw_pet(
            painter,
            eye_state="closed",
            mouth_state="content",
            extra=headphones,
        )

    def _frame_coffee(self, painter: QPainter, i: int, n: int):
        t = i / max(1, n - 1)

        if t < 0.3:
            approach, mouth, eye = t / 0.3, "smile", "open"
        elif t < 0.55:
            approach, mouth, eye = 1.0, "open_small", "closed"
        elif t < 0.75:
            approach, mouth, eye = 1.0 - (t - 0.55) / 0.2, "content", "half"
        else:
            approach, mouth = 0.0, "content"
            eye = "happy" if t > 0.85 else "half"

        def cup(p: QPainter):
            cup_x = 44
            cup_y = int(46 - approach * 14)

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(230, 230, 235))
            p.drawRoundedRect(cup_x, cup_y, 14, 12, 2, 2)

            p.setPen(QPen(QColor(230, 230, 235), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(QRect(cup_x + 12, cup_y + 2, 8, 8), -90 * 16, 180 * 16)

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(90, 55, 35))
            p.drawRoundedRect(cup_x + 2, cup_y + 2, 10, 5, 1, 1)

            steam_wave = (math.sin(2 * math.pi * 2 * i / n) + 1) / 2
            steam_alpha = int(90 + 90 * steam_wave)
            p.setPen(QPen(QColor(220, 220, 225, steam_alpha), 2))
            for k in range(2):
                wobble = math.sin(2 * math.pi * 2 * i / n + k * 1.5) * 3
                base_x = cup_x + 4 + k * 6
                p.drawLine(int(base_x + wobble), cup_y - 2, int(base_x - wobble), cup_y - 12)

        self._draw_pet(painter, eye_state=eye, mouth_state=mouth, extra=cup)

    def _frame_water(self, painter: QPainter, i: int, n: int):
        t = i / max(1, n - 1)

        if t < 0.3:
            approach, mouth, eye = t / 0.3, "smile", "open"
        elif t < 0.55:
            approach, mouth, eye = 1.0, "open_small", "closed"
        elif t < 0.75:
            approach, mouth, eye = 1.0 - (t - 0.55) / 0.2, "content", "half"
        else:
            approach, mouth = 0.0, "content"
            eye = "happy" if t > 0.85 else "half"

        def glass(p: QPainter):
            glass_x = 44
            glass_y = int(46 - approach * 14)

            p.setPen(QPen(QColor(190, 215, 225), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawLine(glass_x, glass_y, glass_x, glass_y + 14)
            p.drawLine(glass_x + 12, glass_y, glass_x + 12, glass_y + 14)
            p.drawLine(glass_x, glass_y + 14, glass_x + 12, glass_y + 14)

            wobble = math.sin(2 * math.pi * 2 * i / n)
            water_top = glass_y + 5 + int(wobble)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(140, 200, 230, 200))
            p.drawRect(glass_x + 1, water_top, 10, glass_y + 14 - water_top)

            bubble_alpha = int(120 + 100 * ((math.sin(2 * math.pi * 2 * i / n + 1.2) + 1) / 2))
            p.setBrush(QColor(220, 240, 250, max(0, min(255, bubble_alpha))))
            p.drawEllipse(glass_x + 4, glass_y + 9, 2, 2)
            p.drawEllipse(glass_x + 8, glass_y + 7, 2, 2)

        self._draw_pet(painter, eye_state=eye, mouth_state=mouth, extra=glass)

    def _frame_apple(self, painter: QPainter, i: int, n: int):
        bite_count = min(3, i // 4)
        mouth = "open_small" if i % 2 == 0 else "closed"
        if i >= n - 2:
            mouth = "content"

        def apple_prop(p: QPainter):
            approach = min(1.0, i / 3)
            x = int(46 - approach * 12)
            y = 30

            # Desenhada num pixmap à parte pra poder "morder" (recortar
            # com transparência) sem apagar pedaço nenhum do corpo do pet.
            apple_size = 20
            apple_pix = QPixmap(apple_size, apple_size)
            apple_pix.fill(Qt.GlobalColor.transparent)

            ap = QPainter(apple_pix)
            ap.setRenderHint(QPainter.RenderHint.Antialiasing)

            ap.setPen(QPen(QColor(90, 60, 30), 2))
            ap.drawLine(10, 2, 10, 6)
            ap.setPen(Qt.PenStyle.NoPen)
            ap.setBrush(QColor(90, 170, 90))
            ap.drawEllipse(9, 1, 6, 4)

            ap.setBrush(QColor(205, 55, 55))
            ap.drawEllipse(2, 5, 16, 15)

            if bite_count > 0:
                ap.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                bite_angles = [200, 60, 320]
                for k in range(bite_count):
                    angle = math.radians(bite_angles[k % len(bite_angles)])
                    bx = 10 + math.cos(angle) * 8
                    by = 12 + math.sin(angle) * 8
                    ap.setPen(Qt.PenStyle.NoPen)
                    ap.setBrush(QColor(0, 0, 0))
                    ap.drawEllipse(QPointF(bx, by), 6, 6)
                ap.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            ap.end()
            p.drawPixmap(x, y, apple_pix)

        self._draw_pet(painter, mouth_state=mouth, extra=apple_prop)

    def _frame_chocolate(self, painter: QPainter, i: int, n: int):
        eaten = min(6, int(6 * i / max(1, n - 1)))
        remaining = 6 - eaten
        wiggle = self._osc(i, n, cycles=2.0)
        mouth = "open_small" if i % 2 == 0 else "closed"
        if i >= n - 2:
            mouth = "content"

        def bar(p: QPainter):
            approach = min(1.0, i / 3)
            x0 = int(40 - approach * 10)
            y0 = 30
            cell = 6

            p.setPen(QPen(QColor(60, 35, 20), 1))
            p.setBrush(QColor(96, 58, 34))
            count = 0
            for r in range(2):
                for c in range(3):
                    if count < remaining:
                        p.drawRoundedRect(x0 + c * (cell + 1), y0 + r * (cell + 1), cell, cell, 1, 1)
                    count += 1

            # Estrelinha de "hmm, gostoso" logo depois de cada pedaço comido
            if eaten > 0 and i % 4 in (0, 1):
                p.setPen(QPen(QColor(255, 220, 120, 220), 2))
                sx, sy = x0 + 18, y0 - 6
                p.drawLine(sx - 3, sy, sx + 3, sy)
                p.drawLine(sx, sy - 3, sx, sy + 3)

        self._draw_pet(
            painter,
            mouth_state=mouth,
            bounce=-2 * wiggle,
            squash=1.0 + 0.02 * wiggle,
            extra=bar,
        )

    def get_frame(self, animation_name: str) -> Optional[QPixmap]:
        """Retorna o frame atual de uma animação."""
        if animation_name in self.animations:
            return self.animations[animation_name].get_frame()
        return None

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
