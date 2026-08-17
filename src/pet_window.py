"""
PetWindow - Janela transparente e arrastável que exibe o pet
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QCursor

from pet import Pet
from presets import intensity_settings, INTENSITY_MODERATE

DRAG_THRESHOLD = 5
HOVER_HOLD_MS = 1400

class PetWindow(QWidget):
    position_changed = pyqtSignal(int, int)
    pet_clicked = pyqtSignal()
    pet_right_clicked = pyqtSignal(QPoint)
    pet_moved = pyqtSignal()        
    hover_held = pyqtSignal()       

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
        self.base_size = 64  
        
        self._scaled_frames_cache = {}

        self.dragging = False
        self.drag_offset = QPoint()
        self.press_global_position = QPoint()

        self._setup_window()

        self.sprite_label = QLabel(self)
        self.sprite_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sprite_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.sprite_label)

        self.move(initial_position[0], initial_position[1])

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._update_frame)
        self.animation_timer.start(self._frame_interval())

        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self.hover_held.emit)

        self.pet.animation_changed.connect(self._on_animation_changed)

        self._update_size()
        self._update_frame()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool  
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))

    def _frame_interval(self) -> int:
        fps = intensity_settings(self.movement_intensity)["fps"]
        return int(1000 / max(1, fps))

    def _update_size(self):
        size = int(self.base_size * self.scale)
        self.setFixedSize(size, size)
        self.sprite_label.setFixedSize(size, size)

    def _update_frame(self):
        pixmap = self.pet.get_current_frame()

        if pixmap:
            anim_name = self.pet.current_animation.value
            frame_idx = self.pet.animation_manager.animations[anim_name].current_frame
            frame_key = f"{anim_name}_{frame_idx}"

            if frame_key not in self._scaled_frames_cache:
                scaled_size = int(self.base_size * self.scale)
                self._scaled_frames_cache[frame_key] = pixmap.scaled(
                    scaled_size,
                    scaled_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            
            self.sprite_label.setPixmap(self._scaled_frames_cache[frame_key])

        self.pet.advance_frame()

    def _on_animation_changed(self, animation_name: str):
        self._update_frame()

    def anchor_rect(self) -> QRect:
        return QRect(self.pos(), self.size())

    def set_scale(self, scale: float):
        self.scale = max(0.5, min(2.0, scale))
        self._scaled_frames_cache.clear()
        self._update_size()
        self._update_frame()

    def set_opacity(self, opacity: float):
        self.opacity_value = max(0.3, min(1.0, opacity))
        self.setWindowOpacity(self.opacity_value)

    def set_movement_intensity(self, intensity: str):
        self.movement_intensity = intensity
        self.animation_timer.setInterval(self._frame_interval())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.press_global_position = event.globalPosition().toPoint()
            self.drag_offset = self.press_global_position - self.pos()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
        elif event.button() == Qt.MouseButton.RightButton:
            self.pet_right_clicked.emit(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self.dragging:
            new_pos = event.globalPosition().toPoint() - self.drag_offset
            self.move(new_pos)
            self.pet_moved.emit()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.dragging:
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
        self.pet.on_hover_enter()
        self.hover_timer.start(HOVER_HOLD_MS)

    def leaveEvent(self, event):
        self.pet.on_hover_leave()
        self.hover_timer.stop()

    def closeEvent(self, event):
        self.animation_timer.stop()
        self.hover_timer.stop()
        event.accept()

    def showEvent(self, event):
        self.setWindowOpacity(self.opacity_value)
        event.accept()