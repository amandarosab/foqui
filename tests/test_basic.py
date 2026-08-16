"""
Testes básicos para o Foqui
"""

import unittest
import sys
import os

# Adiciona src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestPetMood(unittest.TestCase):
    """Testes para o sistema de humor do pet."""
    
    def test_mood_values(self):
        """Verifica se os valores de humor estão corretos."""
        from pet import Mood
        
        self.assertEqual(Mood.HAPPY.value, "happy")
        self.assertEqual(Mood.CONTENT.value, "content")
        self.assertEqual(Mood.NEUTRAL.value, "neutral")
        self.assertEqual(Mood.SLEEPY.value, "sleepy")
    
    def test_mood_never_sad(self):
        """Verifica que não existe humor triste."""
        from pet import Mood
        
        mood_values = [m.value for m in Mood]
        self.assertNotIn("sad", mood_values)
        self.assertNotIn("hungry", mood_values)
        self.assertNotIn("sick", mood_values)


class TestAnimation(unittest.TestCase):
    """Testes para o sistema de animação."""
    
    def test_animation_values(self):
        """Verifica se as animações estão definidas."""
        from pet import Animation
        
        self.assertEqual(Animation.IDLE_BREATHE.value, "idle_breathe")
        self.assertEqual(Animation.PET_REACTION.value, "pet_reaction")


class TestConfig(unittest.TestCase):
    """Testes para configurações."""
    
    def test_default_config_structure(self):
        """Verifica estrutura do config padrão."""
        import json
        
        config_path = os.path.join(
            os.path.dirname(__file__), '..', 'config.json'
        )
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Verifica seções principais
        self.assertIn("pet", config)
        self.assertIn("position", config)
        self.assertIn("behavior", config)
        self.assertIn("hotkeys", config)
        self.assertIn("system", config)
        
        # Verifica valores de pet
        self.assertIn("type", config["pet"])
        self.assertIn("scale", config["pet"])
        self.assertIn("opacity", config["pet"])


if __name__ == "__main__":
    unittest.main()
