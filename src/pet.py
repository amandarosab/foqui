"""
Pet - Lógica do pet, incluindo estado, humor e animações
"""

from enum import Enum
from datetime import datetime
from pathlib import Path
from typing import Optional
import random

from PyQt6.QtCore import QObject, QTimer, QCoreApplication, pyqtSignal
from PyQt6.QtGui import QPixmap

from animation import AnimationManager
from presets import intensity_settings, INTENSITY_MODERATE


class Mood(Enum):
    """Estados de humor do pet."""
    HAPPY = "happy"           # Default, animações variadas
    CONTENT = "content"       # Após interação, mais ativo
    NEUTRAL = "neutral"       # Sem interação por um tempo
    SLEEPY = "sleepy"         # Sem interação por muito tempo ou noite


# Rótulos exibidos ao usuário. Nenhum estado descreve carência ou falta:
# o pet nunca fica "com fome", "triste" ou "abandonado".
MOOD_LABELS = {
    Mood.HAPPY: "consciente",
    Mood.CONTENT: "relaxado",
    Mood.NEUTRAL: "curioso",
    Mood.SLEEPY: "sonolento",
}

MOOD_EMOJIS = {
    Mood.HAPPY: "🙂",
    Mood.CONTENT: "😌",
    Mood.NEUTRAL: "👀",
    Mood.SLEEPY: "😴",
}


class Animation(Enum):
    """Animações disponíveis."""
    IDLE_BREATHE = "idle_breathe"
    IDLE_BLINK = "idle_blink"
    IDLE_LOOK = "idle_look"
    WALK_RIGHT = "walk_right"
    WALK_LEFT = "walk_left"
    SLEEP_ENTER = "sleep_enter"
    SLEEP_LOOP = "sleep_loop"
    SLEEP_EXIT = "sleep_exit"
    YAWN = "yawn"
    EAT = "eat"
    PET_REACTION = "pet_reaction"
    HAPPY_JUMP = "happy_jump"
    CURIOUS = "curious"
    CROCHET = "crochet"
    MUSIC = "music"
    COFFEE = "coffee"
    APPLE = "apple"
    CHOCOLATE = "chocolate"
    WATER = "water"


# Pequenos hobbies que o pet só mostra em resposta a um carinho (ver
# receive_pet) - nunca disparam sozinhos.
HOBBY_ANIMATIONS = (Animation.CROCHET, Animation.MUSIC, Animation.COFFEE)

# Variedade de "petiscos" ao alimentar - mesma ação, aparência diferente.
SNACK_ANIMATIONS = (Animation.EAT, Animation.APPLE, Animation.CHOCOLATE, Animation.WATER)


class Pet(QObject):
    """Representa o pet com seu estado, humor e comportamento."""

    # Signals
    animation_changed = pyqtSignal(str)
    mood_changed = pyqtSignal(str)
    speak_requested = pyqtSignal(str)   # categoria de fala (ver dialogue.py)

    def __init__(
        self,
        pet_type: str,
        name: str,
        initial_state: dict,
        assets_path: Path,
        movement_intensity: str = INTENSITY_MODERATE
    ):
        super().__init__()

        self.pet_type = pet_type
        self.name = name
        self.assets_path = assets_path
        self.movement_intensity = movement_intensity

        # Estado do pet
        self.mood = Mood(initial_state.get("mood", "happy"))
        self.mood_value = initial_state.get("mood_value", 100)
        self.last_interaction = self._parse_datetime(initial_state.get("last_interaction"))
        self.last_fed = self._parse_datetime(initial_state.get("last_fed"))
        self.total_pets = initial_state.get("total_pets", 0)
        self.total_feeds = initial_state.get("total_feeds", 0)
        self.total_time_active = initial_state.get("total_time_active_minutes", 0)
        self.created_at = self._parse_datetime(initial_state.get("created_at")) or datetime.now()

        # Estado de animação
        self.current_animation = Animation.IDLE_BREATHE
        self.animation_queue = []
        self.is_sleeping = False
        self.is_hovering = False

        # Contexto atual
        self.context = {
            "typing_active": False,
            "mouse_active": False,
            "idle_minutes": 0,
            "window_count": 0,
            "is_night": False,
            "in_meeting": False
        }

        # Gerenciador de animações
        self.animation_manager = AnimationManager(
            assets_path / "pets" / pet_type
        )

        # Timer interno para decay de mood
        self._last_mood_update = datetime.now()

        # Piscada cronometrada: a cada 5-8s, como no briefing de animação
        self._blink_timer = QTimer(self)
        self._blink_timer.setSingleShot(True)
        self._blink_timer.timeout.connect(self._on_blink_timer)
        self._schedule_blink()

        # Controle de falas contextuais para não repetir o mesmo gatilho
        self._spoke_typing_at = None
        self._spoke_night_today = False

    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        """Converte string ISO para datetime."""
        if value:
            try:
                return datetime.fromisoformat(value)
            except:
                pass
        return None

    def get_state(self) -> dict:
        """Retorna estado atual do pet para persistência."""
        return {
            "mood": self.mood.value,
            "mood_value": self.mood_value,
            "last_interaction": self.last_interaction.isoformat() if self.last_interaction else None,
            "last_fed": self.last_fed.isoformat() if self.last_fed else None,
            "total_pets": self.total_pets,
            "total_feeds": self.total_feeds,
            "total_time_active_minutes": self.total_time_active,
            "created_at": self.created_at.isoformat()
        }

    def set_pet_type(self, pet_type: str):
        """Troca de skin sem precisar reiniciar o Foqui."""
        if pet_type == self.pet_type:
            return

        self.pet_type = pet_type
        self.animation_manager = AnimationManager(self.assets_path / "pets" / pet_type)

        self.animation_queue.clear()
        self.is_sleeping = False
        self._play_animation(Animation.IDLE_BREATHE)

    def get_mood_label(self) -> str:
        """Rótulo do humor atual, em português e sem culpa."""
        return MOOD_LABELS.get(self.mood, "consciente")

    def get_mood_emoji(self) -> str:
        """Emoji correspondente ao humor atual."""
        return MOOD_EMOJIS.get(self.mood, "🙂")

    def get_current_frame(self) -> Optional[QPixmap]:
        """Retorna o frame atual da animação."""
        return self.animation_manager.get_frame(
            self.current_animation.value
        )

    def advance_frame(self):
        """Avança para o próximo frame da animação."""
        animation_finished = self.animation_manager.advance_frame(
            self.current_animation.value
        )

        if animation_finished:
            self._on_animation_finished()

    def _on_animation_finished(self):
        """Callback quando uma animação termina."""
        # Se tem animações na fila, executa a próxima
        if self.animation_queue:
            next_anim = self.animation_queue.pop(0)
            self._play_animation(next_anim)
            return

        # Caso contrário, decide próxima animação baseada no estado
        self._decide_next_animation()

    def _play_animation(self, animation: Animation, reset: bool = True):
        """Inicia uma animação."""
        if reset:
            self.animation_manager.reset_animation(animation.value)
        self.current_animation = animation
        self.animation_changed.emit(animation.value)

    def _queue_animation(self, animation: Animation):
        """Adiciona animação à fila."""
        self.animation_queue.append(animation)

    # === Movimento e piscadas ===

    def set_movement_intensity(self, intensity: str):
        """Define o quanto o pet se mexe (sutil / moderado / animado)."""
        self.movement_intensity = intensity

    def _intensity(self) -> dict:
        return intensity_settings(self.movement_intensity)

    def _schedule_blink(self):
        """Agenda a próxima piscada para daqui a 5-8 segundos."""
        if QCoreApplication.instance() is None:
            return  # sem event loop (testes), não agenda

        self._blink_timer.start(random.randint(5000, 8000))

    def _on_blink_timer(self):
        """Pisca, se estiver em uma animação de descanso."""
        idle_animations = (
            Animation.IDLE_BREATHE,
            Animation.IDLE_LOOK,
            Animation.CURIOUS
        )

        if not self.is_sleeping and self.current_animation in idle_animations:
            self._play_animation(Animation.IDLE_BLINK)

        self._schedule_blink()

    def _decide_next_animation(self):
        """Decide qual animação tocar baseado no contexto e humor."""
        # Se está dormindo, continua dormindo
        if self.is_sleeping:
            self._play_animation(Animation.SLEEP_LOOP)
            return

        intensity = self._intensity()
        variation = intensity["idle_variation"]
        motion_chance = intensity["motion_chance"]

        # Em reunião o pet vira observador: fica parado, só olha e pisca
        if self.context.get("in_meeting"):
            if random.random() < 0.25:
                self._play_animation(Animation.IDLE_LOOK)
            else:
                self._play_animation(Animation.IDLE_BREATHE)
            return

        # Animações baseadas no contexto
        if self.context["typing_active"]:
            if random.random() < 0.3 * variation:
                self._play_animation(Animation.CURIOUS)
                return

        if self.context["idle_minutes"] > 15:
            if not self.is_sleeping:
                self._start_sleeping()
                return

        if self.context["idle_minutes"] > 5:
            if random.random() < 0.1:
                self._play_animation(Animation.YAWN)
                return

        # Hobbies (crochê, música, café) não disparam sozinhos - só saem
        # em resposta a um carinho, em receive_pet(). Do contrário o pet
        # fica trocando de atividade "do nada" o tempo todo.

        # Animações baseadas no humor
        if self.mood == Mood.CONTENT:
            if random.random() < 0.08 * variation:
                self._play_animation(Animation.HAPPY_JUMP)
                return

        if self.mood == Mood.SLEEPY or self.context["is_night"]:
            if random.random() < 0.15:
                self._play_animation(Animation.YAWN)
                return

        # Animações aleatórias ocasionais
        rand = random.random()
        if rand < 0.05 * variation:
            self._play_animation(Animation.IDLE_LOOK)
        elif rand < 0.1 * variation:
            self._play_animation(Animation.IDLE_BLINK)
        elif rand < 0.1 * variation + motion_chance:
            # Andar depende da intensidade escolhida (0 no modo sutil)
            self._play_animation(
                Animation.WALK_RIGHT if random.random() > 0.5 else Animation.WALK_LEFT
            )
        else:
            self._play_animation(Animation.IDLE_BREATHE)

    def _start_sleeping(self):
        """Inicia sequência de dormir."""
        self.is_sleeping = True
        self._play_animation(Animation.SLEEP_ENTER)
        self._queue_animation(Animation.SLEEP_LOOP)

    def _wake_up(self):
        """Acorda o pet."""
        if self.is_sleeping:
            self.is_sleeping = False
            self.animation_queue.clear()
            self._play_animation(Animation.SLEEP_EXIT)
            self._schedule_blink()

    def update_context(self, context: dict):
        """Atualiza contexto do sistema."""
        old_idle = self.context["idle_minutes"]
        old_meeting = self.context.get("in_meeting", False)
        old_night = self.context.get("is_night", False)

        self.context.update(context)

        new_idle = context.get("idle_minutes", 0)

        # Se estava idle e voltou a ter atividade, acorda
        if old_idle > 5 and new_idle < 1:
            was_sleeping = self.is_sleeping
            self._wake_up()

            # Volta de longe = comentário de boas-vindas; cochilo curto = só um bocejo verbal
            if old_idle > 10:
                self.speak_requested.emit("welcome_back")
            elif was_sleeping:
                self.speak_requested.emit("wake")

        # Entrou ou saiu de reunião
        new_meeting = self.context.get("in_meeting", False)
        if new_meeting != old_meeting:
            self.speak_requested.emit("meeting" if new_meeting else "meeting_end")

        # Digitando muito: comenta no máximo uma vez a cada 20 minutos
        if self.context.get("typing_active") and not new_meeting:
            now = datetime.now()
            recent = (
                self._spoke_typing_at is not None and
                (now - self._spoke_typing_at).total_seconds() < 1200
            )
            if not recent and random.random() < 0.15:
                self._spoke_typing_at = now
                self.speak_requested.emit("typing")

        # Virou a noite
        if self.context.get("is_night") and not old_night:
            if not self._spoke_night_today:
                self._spoke_night_today = True
                self.speak_requested.emit("night")
        elif not self.context.get("is_night"):
            self._spoke_night_today = False

        # Atualiza humor baseado no tempo
        self._update_mood()

    def _update_mood(self):
        """Atualiza humor baseado no tempo desde última interação."""
        now = datetime.now()

        if self.last_interaction:
            hours_since = (now - self.last_interaction).total_seconds() / 3600

            if hours_since < 0.5:
                # Menos de 30min desde interação = contente
                new_mood = Mood.CONTENT
            elif hours_since < 4:
                new_mood = Mood.HAPPY
            elif hours_since < 8:
                new_mood = Mood.NEUTRAL
            else:
                new_mood = Mood.SLEEPY

            if new_mood != self.mood:
                self.mood = new_mood
                self.mood_changed.emit(new_mood.value)

    def receive_pet(self):
        """Pet recebe carinho."""
        self.total_pets += 1
        self.last_interaction = datetime.now()

        # Acorda se estava dormindo
        self._wake_up()

        # Muda humor para contente
        self.mood = Mood.CONTENT
        self.mood_value = min(100, self.mood_value + 10)
        self.mood_changed.emit(self.mood.value)

        # Toca animação de reação - na maioria das vezes o coitinho de
        # sempre, mas de vez em quando ele mostra o que estava fazendo
        # (crochê, música, café). Só aparece por causa do clique, nunca sozinho.
        self.animation_queue.clear()
        reaction = random.choices(
            (Animation.PET_REACTION, *HOBBY_ANIMATIONS),
            weights=(70, 10, 10, 10),
        )[0]
        self._play_animation(reaction)

    def receive_food(self):
        """Pet recebe comida."""
        self.total_feeds += 1
        self.last_fed = datetime.now()
        self.last_interaction = datetime.now()

        # Acorda se estava dormindo
        self._wake_up()

        # Muda humor para contente
        self.mood = Mood.CONTENT
        self.mood_value = min(100, self.mood_value + 15)
        self.mood_changed.emit(self.mood.value)

        # Toca animação de comer - varia o petisco pra não ficar repetitivo
        self.animation_queue.clear()
        self._play_animation(random.choice(SNACK_ANIMATIONS))

    def on_hover_enter(self):
        """Mouse entra na área do pet."""
        self.is_hovering = True

    def on_hover_leave(self):
        """Mouse sai da área do pet."""
        self.is_hovering = False

    def days_together(self) -> int:
        """Quantos dias desde que o pet foi criado."""
        return max(0, (datetime.now() - self.created_at).days)
