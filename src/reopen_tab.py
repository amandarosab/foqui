"""
ReopenTab - Indicador fixo na parte inferior da tela, visível só quando o
pet está escondido.

O ícone da bandeja já permite reabrir o pet, mas o Windows costuma esconder
ícones de bandeja no menu de "ícones ocultos" - fácil de nunca notar. Essa
bolinha garante que sempre exista um jeito óbvio e visível de trazer o
Foqui de volta.
"""

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QCursor, QPolygon

from animation import AnimationManager


class ReopenTab(QWidget):
    """Bolinha clicável, ancorada embaixo, que reabre o pet escondido."""

    clicked = pyqtSignal()

    SIZE = 40
    BOTTOM_MARGIN = 8

    def __init__(self, pet_type: str = "frog"):
        super().__init__()

        self.pet_type = pet_type
        self._hovering = False

        self._setup_window()
        self.setFixedSize(self.SIZE, self.SIZE)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip("Mostrar o Foqui")
        self.setMouseTracking(True)

        self._reposition()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool  # Não aparece na taskbar
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

    def _reposition(self):
        """Centraliza embaixo, acima da barra de tarefas."""
        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            return

        area = screen.availableGeometry()
        x = area.center().x() - self.SIZE // 2
        y = area.bottom() - self.SIZE - self.BOTTOM_MARGIN
        self.move(x, y)

    def set_pet_type(self, pet_type: str):
        """Atualiza a cor do indicador para o novo tipo de pet."""
        if pet_type == self.pet_type:
            return
        self.pet_type = pet_type
        self.update()

    def showEvent(self, event):
        self._reposition()
        super().showEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        body_color = AnimationManager.PLACEHOLDER_COLORS.get(
            self.pet_type, AnimationManager.PLACEHOLDER_COLORS["frog"]
        )

        # Fundo escuro semitransparente, um pouco mais opaco no hover
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(26, 29, 38, 235 if self._hovering else 205))
        painter.drawEllipse(0, 0, self.SIZE, self.SIZE)

        # Bolinha central na cor do pet atual
        painter.setBrush(body_color)
        inset = 9
        painter.drawEllipse(inset, inset, self.SIZE - inset * 2, self.SIZE - inset * 2)

        # Seta pra cima: "puxa aqui pra trazer de volta"
        painter.setBrush(QColor(245, 247, 250))
        cx = self.SIZE // 2
        painter.drawPolygon(QPolygon([
            QPoint(cx, 13),
            QPoint(cx - 5, 21),
            QPoint(cx + 5, 21),
        ]))

    def enterEvent(self, event):
        self._hovering = True
        self.update()

    def leaveEvent(self, event):
        self._hovering = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
