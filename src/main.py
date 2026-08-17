import sys
import os
from PyQt6.QtWidgets import QApplication, QLabel, QWidget
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Remove as bordas da janela da aplicação e deixa o fundo transparente
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Cria o contêiner (label) que vai exibir a imagem
        self.label = QLabel(self)
        
        # Caminho exato apontando para a pasta onde você salvou a imagem
        image_path = os.path.join("assets", "pets", "frog", "sapingo.png")
        
        # Carrega a imagem do sapinho
        pixmap = QPixmap(image_path)
        
        # Redimensiona a imagem caso ela seja muito grande (ajuste o 150, 150 se quiser maior ou menor)
        pixmap = pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        self.label.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())

        # Variável para rastrear a posição do clique do mouse
        self.drag_pos = None

    # --- Funções para permitir clicar e arrastar o sapinho pela tela ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.drag_pos is not None:
            delta = event.globalPosition().toPoint() - self.drag_pos
            self.move(self.pos() + delta)
            self.drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Cria e exibe o pet
    pet = DesktopPet()
    pet.show()
    
    # Executa o loop principal do programa
    sys.exit(app.exec())