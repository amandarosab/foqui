"""
PetWindow - Janela transparente e arrastável que exibe o pet
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QCursor

from pet import Pet
from presets import intensity_settings, INTENSITY_MODERATE


# Distância em pixels a partir da qual um clique vira arrasto
DRAG_THRESHOLD = 5

# Tempo parado com o mouse em cima antes de o pet reagir
HOVER_HOLD_MS = 1400


class PetWindow(QWidget):
    """Janela transparente always-on-top que exibe o pet."""

    # Signals
    position_changed = pyqtSignal(int, int)
    pet_clicked = pyqtSignal()
    pet_right_clicked = pyqtSignal(QPoint)
    pet_moved = pyqtSignal()        # durante o arrasto, para o balão acompanhar
    hover_held = pyqtSignal()       # mouse parado em cima por um tempinho

    def __init__(
        self,
        pet: Pet,
        scale: float = 1.0,
        opacity: float = 0.85,
        initial_position: tuple = (100, 100),
        movement_intensity: str = INTENSITY_MODERATE
    ):
        super().__init__()

        self.pet = pet
        self.scale = scale
        self.opacity_value = opacity
        self.movement_intensity = movement_intensity
        self.base_size = 64  # Tamanho base do sprite

        # Estado de drag
        self.dragging = False
        self.drag_offset = QPoint()
        self.press_global_position = QPoint()

        # Configura a janela
        self._setup_window()

        # Cria o label que exibe o sprite
        self.sprite_label = QLabel(self)
        self.sprite_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sprite_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.sprite_label)

        # Posição inicial
        self.move(initial_position[0], initial_position[1])

        # Timer de animação (FPS depende da intensidade de movimento)
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._update_frame)
        self.animation_timer.start(self._frame_interval())

        # Timer de hover: reage a quem fica encarando
        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self.hover_held.emit)

        # Conecta ao pet para receber updates de animação
        self.pet.animation_changed.connect(self._on_animation_changed)

        # Atualiza tamanho
        self._update_size()

        # Primeiro frame
        self._update_frame()

    def _setup_window(self):
        """Configura propriedades da janela."""
        # Remove decorações da janela
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool  # Não aparece na taskbar
        )

        # Fundo transparente
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # A janela nunca deve roubar o foco de quem está trabalhando
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Permite mouse tracking
        self.setMouseTracking(True)

        # Cursor de mão ao passar por cima
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))

    def _frame_interval(self) -> int:
        """Intervalo entre frames, em ms, derivado da intensidade."""
        fps = intensity_settings(self.movement_intensity)["fps"]
        return int(1000 / max(1, fps))

    def _update_size(self):
        """Atualiza tamanho da janela baseado na escala."""
        size = int(self.base_size * self.scale)
        self.setFixedSize(size, size)
        self.sprite_label.setFixedSize(size, size)

    def _update_frame(self):
        """Atualiza o frame atual da animação."""
        pixmap = self.pet.get_current_frame()

        if pixmap:
            # Escala o pixmap
            scaled_size = int(self.base_size * self.scale)
            scaled_pixmap = pixmap.scaled(
                scaled_size,
                scaled_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.sprite_label.setPixmap(scaled_pixmap)

        # Avança para o próximo frame
        self.pet.advance_frame()

    def _on_animation_changed(self, animation_name: str):
        """Callback quando a animação do pet muda."""
        # Reset do frame atual acontece no Pet
        self._update_frame()

    def anchor_rect(self) -> QRect:
        """Retângulo do pet em coordenadas globais (âncora do balão)."""
        return QRect(self.pos(), self.size())

    def set_scale(self, scale: float):
        """Define a escala do pet."""
        self.scale = max(0.5, min(2.0, scale))
        self._update_size()
        self._update_frame()

    def set_opacity(self, opacity: float):
        """Define a opacidade da janela."""
        self.opacity_value = max(0.3, min(1.0, opacity))
        self.setWindowOpacity(self.opacity_value)

    def set_movement_intensity(self, intensity: str):
        """Ajusta o ritmo da animação conforme a intensidade escolhida."""
        self.movement_intensity = intensity
        self.animation_timer.setInterval(self._frame_interval())

    # === Mouse Events ===

    def mousePressEvent(self, event):
        """Início do drag ou clique."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.press_global_position = event.globalPosition().toPoint()
            self.drag_offset = self.press_global_position - self.pos()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
        elif event.button() == Qt.MouseButton.RightButton:
            self.pet_right_clicked.emit(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        """Durante o drag."""
        if self.dragging:
            new_pos = event.globalPosition().toPoint() - self.drag_offset
            self.move(new_pos)
            self.pet_moved.emit()

    def mouseReleaseEvent(self, event):
        """Fim do drag ou clique."""
        if event.button() == Qt.MouseButton.LeftButton and self.dragging:
            # Compara com onde o clique começou, não com a posição atual da janela
            moved_distance = (
                event.globalPosition().toPoint() - self.press_global_position
            ).manhattanLength()

            if moved_distance < DRAG_THRESHOLD:
                self.pet_clicked.emit()
            else:
                self.position_changed.emit(self.pos().x(), self.pos().y())

            self.dragging = False
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))

    def enterEvent(self, event):
        """Mouse entra na janela."""
        self.pet.on_hover_enter()
        self.hover_timer.start(HOVER_HOLD_MS)

    def leaveEvent(self, event):
        """Mouse sai da janela."""
        self.pet.on_hover_leave()
        self.hover_timer.stop()

    # === Window Events ===

    def closeEvent(self, event):
        """Janela sendo fechada."""
        self.animation_timer.stop()
        self.hover_timer.stop()
        event.accept()

    def showEvent(self, event):
        """Janela sendo mostrada."""
        self.setWindowOpacity(self.opacity_value)
        event.accept()
