"""
SpeechBubble - Balão flutuante de fala ou pensamento exibido ao lado do pet

Janela própria, sem borda, sempre no topo e transparente para o mouse:
o balão nunca rouba foco nem bloqueia clique em nada atrás dele.
"""

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import (
    Qt, QRect, QRectF, QPoint, QTimer, QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import QPainter, QColor, QFont, QFontMetrics, QPainterPath, QPen


# Estilos de balão
STYLE_SPEECH = "speech"
STYLE_THOUGHT = "thought"

# Paleta de alto contraste - legível sobre qualquer coisa que esteja na tela
BG_COLOR = QColor(26, 29, 38, 242)
TEXT_COLOR = QColor(245, 247, 250)
BORDER_COLOR = QColor(134, 194, 156, 210)

# Métricas do balão
MAX_WIDTH = 300
PAD_X = 14
PAD_Y = 11
RADIUS = 14
TAIL_H = 11
TAIL_W = 18
GAP = 8          # distância entre o balão e o pet
MARGIN = 8       # respiro mínimo até a borda da tela


class SpeechBubble(QWidget):
    """Balão de fala/pensamento que aparece perto do pet e some sozinho."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.text = ""
        self.style = STYLE_SPEECH
        self.tail_up = False        # True = balão abaixo do pet, cauda para cima
        self.tail_x = 0             # posição horizontal da cauda dentro do widget
        self.target_opacity = 1.0

        self._bubble_rect = QRect()
        self._text_rect = QRect()

        self._setup_window()

        self.font = QFont()
        self.font.setPointSize(10)
        self.font.setBold(False)

        # Timer que fecha o balão sozinho
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.dismiss)

        # Animação de fade
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._fade.finished.connect(self._on_fade_finished)
        self._fading_out = False

    def _setup_window(self):
        """Janela sem borda, no topo, sem foco e sem captura de mouse."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    # === API pública ===

    def say(
        self,
        text: str,
        anchor: QRect,
        style: str = STYLE_SPEECH,
        duration_ms: int = 4200,
        opacity: float = 1.0
    ):
        """
        Mostra uma fala ancorada no retângulo do pet (coordenadas globais).

        A duração é esticada para textos longos: ninguém deveria precisar
        ler correndo por causa de um timer.
        """
        if not text:
            return

        self.text = text
        self.style = style
        self.target_opacity = max(0.4, min(1.0, opacity))

        self._layout_for(anchor)

        # ~55ms por caractere além dos 40 primeiros, limitado a +4s
        extra = min(4000, max(0, len(text) - 40) * 55)
        total_duration = duration_ms + extra

        self._fading_out = False
        if not self.isVisible():
            self.setWindowOpacity(0.0)
            self.show()
        self.raise_()

        self._fade.stop()
        self._fade.setDuration(180)
        self._fade.setStartValue(self.windowOpacity())
        self._fade.setEndValue(self.target_opacity)
        self._fade.start()

        self._hide_timer.start(total_duration)
        self.update()

    def follow(self, anchor: QRect):
        """Reposiciona o balão quando o pet se move (arrastar, por exemplo)."""
        if self.isVisible():
            self._layout_for(anchor)
            self.update()

    def dismiss(self):
        """Some com fade out."""
        if not self.isVisible() or self._fading_out:
            return

        self._hide_timer.stop()
        self._fading_out = True
        self._fade.stop()
        self._fade.setDuration(220)
        self._fade.setStartValue(self.windowOpacity())
        self._fade.setEndValue(0.0)
        self._fade.start()

    def hide_now(self):
        """Some imediatamente, sem animação (usado ao esconder o pet)."""
        self._hide_timer.stop()
        self._fade.stop()
        self._fading_out = False
        self.hide()

    # === Layout ===

    def _layout_for(self, anchor: QRect):
        """Calcula tamanho e posição do balão em relação ao pet."""
        fm = QFontMetrics(self.font)
        available = MAX_WIDTH - 2 * PAD_X

        text_rect = fm.boundingRect(
            QRect(0, 0, available, 2000),
            int(Qt.TextFlag.TextWordWrap),
            self.text
        )

        bubble_w = min(MAX_WIDTH, text_rect.width() + 2 * PAD_X)
        bubble_h = text_rect.height() + 2 * PAD_Y
        total_h = bubble_h + TAIL_H

        screen = self._screen_geometry(anchor)

        # Prefere ficar acima do pet; se não couber, vai para baixo
        y_above = anchor.top() - total_h - GAP
        if y_above >= screen.top() + MARGIN:
            self.tail_up = False
            y = y_above
            self._bubble_rect = QRect(0, 0, bubble_w, bubble_h)
        else:
            self.tail_up = True
            y = anchor.bottom() + GAP
            self._bubble_rect = QRect(0, TAIL_H, bubble_w, bubble_h)

        # Centraliza no pet e prende dentro da tela
        x = anchor.center().x() - bubble_w // 2
        x = max(screen.left() + MARGIN, min(x, screen.right() - bubble_w - MARGIN))
        y = max(screen.top() + MARGIN, min(y, screen.bottom() - total_h - MARGIN))

        # A cauda aponta para o pet mesmo quando o balão foi deslocado
        self.tail_x = anchor.center().x() - x
        self.tail_x = max(RADIUS + TAIL_W // 2, min(self.tail_x, bubble_w - RADIUS - TAIL_W // 2))

        self._text_rect = QRect(
            self._bubble_rect.left() + PAD_X,
            self._bubble_rect.top() + PAD_Y,
            bubble_w - 2 * PAD_X,
            bubble_h - 2 * PAD_Y
        )

        self.setFixedSize(bubble_w, total_h)
        self.move(x, y)

    def _screen_geometry(self, anchor: QRect) -> QRect:
        """Área útil do monitor onde o pet está."""
        screen = QApplication.screenAt(anchor.center())
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen is None:
            return QRect(0, 0, 1920, 1080)
        return screen.availableGeometry()

    # === Pintura ===

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self.font)

        path = QPainterPath()
        path.addRoundedRect(QRectF(self._bubble_rect), RADIUS, RADIUS)

        painter.setBrush(BG_COLOR)
        painter.setPen(QPen(BORDER_COLOR, 1.5))
        painter.drawPath(path)

        if self.style == STYLE_THOUGHT:
            self._draw_thought_tail(painter)
        else:
            self._draw_speech_tail(painter)

        painter.setPen(TEXT_COLOR)
        painter.drawText(
            self._text_rect,
            int(Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
            self.text
        )

    def _draw_speech_tail(self, painter: QPainter):
        """Triângulo apontando para o pet."""
        half = TAIL_W // 2
        tail = QPainterPath()

        if self.tail_up:
            base_y = self._bubble_rect.top()
            tail.moveTo(self.tail_x - half, base_y + 1)
            tail.lineTo(self.tail_x, base_y - TAIL_H + 1)
            tail.lineTo(self.tail_x + half, base_y + 1)
        else:
            base_y = self._bubble_rect.bottom()
            tail.moveTo(self.tail_x - half, base_y - 1)
            tail.lineTo(self.tail_x, base_y + TAIL_H - 1)
            tail.lineTo(self.tail_x + half, base_y - 1)

        tail.closeSubpath()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(BG_COLOR)
        painter.drawPath(tail)

    def _draw_thought_tail(self, painter: QPainter):
        """Bolhinhas decrescentes, estilo balão de pensamento."""
        painter.setBrush(BG_COLOR)
        painter.setPen(QPen(BORDER_COLOR, 1.2))

        if self.tail_up:
            y1 = self._bubble_rect.top() - 5
            y2 = self._bubble_rect.top() - 10
        else:
            y1 = self._bubble_rect.bottom() + 1
            y2 = self._bubble_rect.bottom() + 6

        painter.drawEllipse(QPoint(self.tail_x, y1), 4, 4)
        painter.drawEllipse(QPoint(self.tail_x + 5, y2), 2, 2)

    # === Eventos ===

    def _on_fade_finished(self):
        if self._fading_out:
            self._fading_out = False
            self.hide()
