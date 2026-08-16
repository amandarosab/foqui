"""
OnboardingWindow - Primeira execução do Foqui

Três telas, uma frase cada, botões grandes. Dá para pular a qualquer momento.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal

from presets import MODES, MODE_ORDER, MODE_RELAX


class OnboardingWindow(QDialog):
    """Boas-vindas em três passos, com escolha de modo inicial."""

    finished_onboarding = pyqtSignal(str)  # modo escolhido

    STEPS = [
        {
            "title": "Ei, eu sou o Foqui.",
            "body": "Fico aqui no canto só pra te lembrar que você está presente.\n"
                    "Sem meta, sem streak, sem cobrança.",
            "next": "Legal, e aí?",
        },
        {
            "title": "Clique em mim pra fazer carinho.",
            "body": "Clique direito abre o menu rápido.\n"
                    "Arrastar me leva pra onde você quiser.",
            "next": "Entendi",
        },
        {
            "title": "Some quando você precisar.",
            "body": "Ctrl+Shift+F esconde e mostra.\n"
                    "Ctrl+Shift+M troca de modo. Ctrl+Shift+O abre as configurações.",
            "next": "Escolher meu modo",
        },
    ]

    def __init__(self, pet_name: str = "Foqui"):
        super().__init__()

        self.pet_name = pet_name
        self.step = 0
        self.chosen_mode = MODE_RELAX

        self._setup_ui()
        self._render_step()

    def _setup_ui(self):
        self.setWindowTitle("Oi!")
        self.setMinimumWidth(460)
        self.setModal(False)
        self.setStyleSheet("""
            QDialog { background-color: #1A1D26; }
            QLabel#title { font-size: 19px; font-weight: 600; color: #F5F7FA; }
            QLabel#body { font-size: 14px; color: #C4CAD6; }
            QLabel#step { font-size: 12px; color: #7C8496; }
            QPushButton {
                font-size: 15px;
                padding: 12px 22px;
                border-radius: 10px;
                border: 1px solid #3A4050;
                background-color: #232838;
                color: #F0F2F6;
            }
            QPushButton:hover { background-color: #2C3346; border-color: #86C29C; }
            QPushButton#primary {
                background-color: #86C29C;
                color: #14171F;
                font-weight: 600;
                border: none;
            }
            QPushButton#primary:hover { background-color: #9AD3AE; }
            QPushButton#link {
                background: transparent;
                border: none;
                color: #7C8496;
                font-size: 13px;
                padding: 6px;
            }
            QPushButton#link:hover { color: #C4CAD6; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 20)
        layout.setSpacing(14)

        self.step_label = QLabel()
        self.step_label.setObjectName("step")
        layout.addWidget(self.step_label)

        self.title_label = QLabel()
        self.title_label.setObjectName("title")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        self.body_label = QLabel()
        self.body_label.setObjectName("body")
        self.body_label.setWordWrap(True)
        layout.addWidget(self.body_label)

        # Área trocável: botão "próximo" ou os três modos
        self.action_area = QWidget()
        self.action_layout = QVBoxLayout(self.action_area)
        self.action_layout.setContentsMargins(0, 8, 0, 0)
        self.action_layout.setSpacing(10)
        layout.addWidget(self.action_area)

        skip_layout = QHBoxLayout()
        skip_layout.addStretch()
        self.skip_btn = QPushButton("Pular")
        self.skip_btn.setObjectName("link")
        self.skip_btn.clicked.connect(self._finish)
        skip_layout.addWidget(self.skip_btn)
        layout.addLayout(skip_layout)

    def _clear_actions(self):
        while self.action_layout.count():
            item = self.action_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _render_step(self):
        """Desenha o passo atual."""
        if self.step < len(self.STEPS):
            data = self.STEPS[self.step]

            self.step_label.setText(f"{self.step + 1} de {len(self.STEPS) + 1}")
            self.title_label.setText(data["title"])
            self.body_label.setText(data["body"])

            self._clear_actions()
            next_btn = QPushButton(data["next"])
            next_btn.setObjectName("primary")
            next_btn.clicked.connect(self._next_step)
            self.action_layout.addWidget(next_btn)
        else:
            self._render_mode_step()

    def _render_mode_step(self):
        """Último passo: escolher o modo inicial."""
        self.step_label.setText(f"{len(self.STEPS) + 1} de {len(self.STEPS) + 1}")
        self.title_label.setText("Como você quer me ver hoje?")
        self.body_label.setText("Dá pra trocar depois com Ctrl+Shift+M.")

        self._clear_actions()

        for mode in MODE_ORDER:
            preset = MODES[mode]
            btn = QPushButton(f"{preset['icon']}  {preset['label']} — {preset['hint']}")
            btn.setMinimumHeight(50)
            btn.clicked.connect(lambda _, m=mode: self._choose_mode(m))
            self.action_layout.addWidget(btn)

        self.skip_btn.setText("Deixa como está")

    def _next_step(self):
        self.step += 1
        self._render_step()

    def _choose_mode(self, mode: str):
        self.chosen_mode = mode
        self._finish()

    def _finish(self):
        self.finished_onboarding.emit(self.chosen_mode)
        self.close()
