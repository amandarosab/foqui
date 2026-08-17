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
    HAPPY = "happy"           
    CONTENT = "content"       
    NEUTRAL = "neutral"       
    SLEEPY = "sleepy"         

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


HOBBY_ANIMATIONS = (Animation.CROCHET, Animation.MUSIC, Animation.COFFEE)
SNACK_ANIMATIONS = (Animation.EAT, Animation.APPLE, Animation.CHOCOLATE, Animation.WATER)


class Pet(QObject):
    animation_changed = pyqtSignal(str)
    mood_changed = pyqtSignal(str)
    speak_requested = pyqtSignal(str)   

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

        self.mood = Mood(initial_state.get("mood", "happy"))
        self.mood_value = initial_state.get("mood_value", 100)
        self.last_interaction = self._parse_datetime(initial_state.get("last_interaction"))
        self.last_fed = self._parse_datetime(initial_state.get("last_fed"))
        self.total_pets = initial_state.get("total_pets", 0)
        self.total_feeds = initial_state.get("total_feeds", 0)
        self.total_time_active = initial_state.get("total_time_active_minutes", 0)
        self.created_at = self._parse_datetime(initial_state.get("created_at")) or datetime.now()

        self.current_animation = Animation.IDLE_BREATHE
        self.animation_queue = []
        self.is_sleeping = False
        self.is_hovering = False

        self.context = {
            "typing_active": False,
            "mouse_active": False,
            "idle_minutes": 0,
            "window_count": 0,
            "is_night": False,
            "in_meeting": False
        }

        self.animation_manager = AnimationManager(
            assets_path / "pets" / pet_type
        )

        self._last_mood_update = datetime.now()

        self._blink_timer = QTimer(self)
        self._blink_timer.setSingleShot(True)
        self._blink_timer.timeout.connect(self._on_blink_timer)
        self._schedule_blink()

        self._spoke_typing_at = None
        self._spoke_night_today = False

    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        if value:
            try:
                return datetime.fromisoformat(value)
            except:
                pass
        return None

    def get_state(self) -> dict:
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
        if pet_type == self.pet_type:
            return

        self.pet_type = pet_type
        self.animation_manager = AnimationManager(self.assets_path / "pets" / pet_type)

        self.animation_queue.clear()
        self.is_sleeping = False
        self._play_animation(Animation.IDLE_BREATHE)

    def get_mood_label(self) -> str:
        return MOOD_LABELS.get(self.mood, "consciente")

    def get_mood_emoji(self) -> str:
        return MOOD_EMOJIS.get(self.mood, "🙂")

    def get_current_frame(self) -> Optional[QPixmap]:
        return self.animation_manager.get_frame(
            self.current_animation.value
        )

    def advance_frame(self):
        animation_finished = self.animation_manager.advance_frame(
            self.current_animation.value
        )

        if animation_finished:
            self._on_animation_finished()

    def _on_animation_finished(self):
        if self.animation_queue:
            next_anim = self.animation_queue.pop(0)
            self._play_animation(next_anim)
            return

        self._decide_next_animation()

    def _play_animation(self, animation: Animation, reset: bool = True):
        if reset:
            self.animation_manager.reset_animation(animation.value)
        self.current_animation = animation
        self.animation_changed.emit(animation.value)

    def _queue_animation(self, animation: Animation):
        self.animation_queue.append(animation)

    def set_movement_intensity(self, intensity: str):
        self.movement_intensity = intensity

    def _intensity(self) -> dict:
        base_intensity = intensity_settings(self.movement_intensity).copy()
        
        if self.pet_type == "rat":
            base_intensity["fps"] = int(base_intensity["fps"] * 1.5)
            base_intensity["motion_chance"] *= 2.0
            
        return base_intensity

    def _schedule_blink(self):
        if QCoreApplication.instance() is None:
            return 
        self._blink_timer.start(random.randint(5000, 8000))

    def _on_blink_timer(self):
        idle_animations = (
            Animation.IDLE_BREATHE,
            Animation.IDLE_LOOK,
            Animation.CURIOUS
        )

        if not self.is_sleeping and self.current_animation in idle_animations:
            self._play_animation(Animation.IDLE_BLINK)

        self._schedule_blink()

    def _decide_next_animation(self):
        if self.is_sleeping:
            self._play_animation(Animation.SLEEP_LOOP)
            return

        intensity = self._intensity()
        variation = intensity["idle_variation"]
        motion_chance = intensity["motion_chance"]

        if self.context.get("in_meeting"):
            if random.random() < 0.25:
                self._play_animation(Animation.IDLE_LOOK)
            else:
                self._play_animation(Animation.IDLE_BREATHE)
            return

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

        if self.mood == Mood.CONTENT:
            if random.random() < 0.01:  # Muito raro - apenas ocasionalmente
                self._play_animation(Animation.HAPPY_JUMP)
                return

        if self.mood == Mood.SLEEPY or self.context["is_night"]:
            if random.random() < 0.15:
                self._play_animation(Animation.YAWN)
                return

        rand = random.random()
        if rand < 0.05 * variation:
            self._play_animation(Animation.IDLE_LOOK)
        elif rand < 0.1 * variation:
            self._play_animation(Animation.IDLE_BLINK)
        elif rand < 0.1 * variation + motion_chance:
            self._play_animation(
                Animation.WALK_RIGHT if random.random() > 0.5 else Animation.WALK_LEFT
            )
        else:
            self._play_animation(Animation.IDLE_BREATHE)

    def _start_sleeping(self):
        self.is_sleeping = True
        self._play_animation(Animation.SLEEP_ENTER)
        self._queue_animation(Animation.SLEEP_LOOP)

    def _wake_up(self):
        if self.is_sleeping:
            self.is_sleeping = False
            self.animation_queue.clear()
            self._play_animation(Animation.SLEEP_EXIT)
            self._schedule_blink()

    def update_context(self, context: dict):
        old_idle = self.context["idle_minutes"]
        old_meeting = self.context.get("in_meeting", False)
        old_night = self.context.get("is_night", False)

        self.context.update(context)

        new_idle = context.get("idle_minutes", 0)

        if old_idle > 5 and new_idle < 1:
            was_sleeping = self.is_sleeping
            self._wake_up()

            if old_idle > 10:
                self.speak_requested.emit("welcome_back")
            elif was_sleeping:
                self.speak_requested.emit("wake")

        new_meeting = self.context.get("in_meeting", False)
        if new_meeting != old_meeting:
            self.speak_requested.emit("meeting" if new_meeting else "meeting_end")

        if self.context.get("typing_active") and not new_meeting:
            now = datetime.now()
            recent = (
                self._spoke_typing_at is not None and
                (now - self._spoke_typing_at).total_seconds() < 1200
            )
            if not recent and random.random() < 0.15:
                self._spoke_typing_at = now
                self.speak_requested.emit("typing")

        if self.context.get("is_night") and not old_night:
            if not self._spoke_night_today:
                self._spoke_night_today = True
                self.speak_requested.emit("night")
        elif not self.context.get("is_night"):
            self._spoke_night_today = False

        self._update_mood()

    def _update_mood(self):
        now = datetime.now()

        if self.last_interaction:
            hours_since = (now - self.last_interaction).total_seconds() / 3600

            if hours_since < 0.5:
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
        self.total_pets += 1
        self.last_interaction = datetime.now()

        self._wake_up()

        self.mood = Mood.CONTENT
        self.mood_value = min(100, self.mood_value + 10)
        self.mood_changed.emit(self.mood.value)

        self.animation_queue.clear()
        reaction = random.choices(
            (Animation.PET_REACTION, *HOBBY_ANIMATIONS),
            weights=(70, 10, 10, 10),
        )[0]
        self._play_animation(reaction)

    def receive_food(self):
        self.total_feeds += 1
        self.last_fed = datetime.now()
        self.last_interaction = datetime.now()

        self._wake_up()

        self.mood = Mood.CONTENT
        self.mood_value = min(100, self.mood_value + 15)
        self.mood_changed.emit(self.mood.value)

        self.animation_queue.clear()
        self._play_animation(random.choice(SNACK_ANIMATIONS))

    def on_hover_enter(self):
        self.is_hovering = True

    def on_hover_leave(self):
        self.is_hovering = False

    def days_together(self) -> int:
        return max(0, (datetime.now() - self.created_at).days)