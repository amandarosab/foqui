"""
Foqui - Ferramenta de regulação atencional para profissionais neurodivergentes
Autora: Amanda Belo
"""

import sys
import os

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from app import FoquiApp


def main():
    # Habilita high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Mantém rodando no tray
    app.setApplicationName("Foqui")
    app.setApplicationDisplayName("Foqui")
    
    # Inicializa a aplicação principal
    foqui = FoquiApp()
    foqui.start()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
