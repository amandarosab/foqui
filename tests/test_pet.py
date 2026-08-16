"""
Testes básicos para a classe Pet
"""

import os
import pytest
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtWidgets import QApplication

from pet import Pet, Mood, Animation, SNACK_ANIMATIONS, HOBBY_ANIMATIONS


@pytest.fixture(scope="module", autouse=True)
def qapp():
    """
    Pet cria QPixmaps (frames de animação) já no __init__, e isso trava
    indefinidamente sem uma QApplication instanciada antes - por isso o
    fixture roda automaticamente pra toda a classe.
    """
    instance = QApplication.instance()
    return instance if instance else QApplication(sys.argv)


class TestPet:
    """Testes para a classe Pet."""

    def setup_method(self):
        """Setup executado antes de cada teste."""
        self.initial_state = {
            "mood": "happy",
            "mood_value": 100,
            "last_interaction": None,
            "last_fed": None,
            "total_pets": 0,
            "total_feeds": 0,
            "total_time_active_minutes": 0,
            "created_at": None
        }
        self.assets_path = Path(__file__).parent.parent / "assets"
    
    def test_pet_creation(self):
        """Testa criação básica do pet."""
        pet = Pet(
            pet_type="frog",
            name="Foqui",
            initial_state=self.initial_state,
            assets_path=self.assets_path
        )
        
        assert pet.name == "Foqui"
        assert pet.pet_type == "frog"
        assert pet.mood == Mood.HAPPY
    
    def test_receive_pet(self):
        """Testa interação de carinho."""
        pet = Pet(
            pet_type="frog",
            name="Foqui",
            initial_state=self.initial_state,
            assets_path=self.assets_path
        )
        
        initial_pets = pet.total_pets
        pet.receive_pet()
        
        assert pet.total_pets == initial_pets + 1
        assert pet.mood == Mood.CONTENT
    
    def test_receive_food(self):
        """Testa alimentação."""
        pet = Pet(
            pet_type="frog",
            name="Foqui",
            initial_state=self.initial_state,
            assets_path=self.assets_path
        )
        
        initial_feeds = pet.total_feeds
        pet.receive_food()
        
        assert pet.total_feeds == initial_feeds + 1
        assert pet.mood == Mood.CONTENT
    
    def test_get_state(self):
        """Testa exportação de estado."""
        pet = Pet(
            pet_type="frog",
            name="Foqui",
            initial_state=self.initial_state,
            assets_path=self.assets_path
        )
        
        state = pet.get_state()
        
        assert "mood" in state
        assert "mood_value" in state
        assert "total_pets" in state
        assert "total_feeds" in state

    def test_receive_food_varies_the_snack_animation(self):
        """Alimentar troca entre lanche genérico, maçã e chocolate, não sempre o mesmo."""
        seen = set()

        for _ in range(60):
            pet = Pet(
                pet_type="frog",
                name="Foqui",
                initial_state=self.initial_state,
                assets_path=self.assets_path
            )
            pet.receive_food()
            seen.add(pet.current_animation)

        assert seen == set(SNACK_ANIMATIONS)
        assert Animation.APPLE in seen
        assert Animation.CHOCOLATE in seen
        assert Animation.WATER in seen

    def test_receive_pet_can_reveal_a_hobby(self):
        """Carinho é o único gatilho dos hobbies - nunca aparecem sozinhos."""
        seen = set()

        for _ in range(80):
            pet = Pet(
                pet_type="frog",
                name="Foqui",
                initial_state=self.initial_state,
                assets_path=self.assets_path
            )
            pet.receive_pet()
            seen.add(pet.current_animation)

        assert seen <= {Animation.PET_REACTION, *HOBBY_ANIMATIONS}
        assert Animation.PET_REACTION in seen

    def test_idle_decisions_never_spontaneously_start_a_hobby(self):
        """Hobbies não podem aparecer sem o usuário ter dado carinho antes."""
        pet = Pet(
            pet_type="frog",
            name="Foqui",
            initial_state=self.initial_state,
            assets_path=self.assets_path
        )

        for _ in range(200):
            pet._decide_next_animation()
            assert pet.current_animation not in HOBBY_ANIMATIONS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
