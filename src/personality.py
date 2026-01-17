"""Personality Engine: Tracks Student State & Selects Style"""

from typing import Dict, List, Optional
from prompts_improved import STYLE_PROFILES

class PersonalityDetector:
    """Tracks emotional state and communication style signals over time"""
    
    def __init__(self):
        # State variables (0.0 to 1.0)
        self.confidence = 0.5
        self.frustration = 0.0
        self.curiosity = 0.5
        self.energy = 0.5
        
    def update(self, response: str):
        """Update state based on the latest student message"""
        text = response.lower()
        words = len(response.split())
        
        # 1. Frustration (Hot Signal - increases fast, decays slowly)
        # We want to catch this immediately to pivot style
        if any(w in text for w in ["ugh", "confused", "lost", "don't get", "hard", "stupid", "hate", "weird"]):
            self.frustration = min(1.0, self.frustration + 0.4)
        else:
            self.frustration = max(0.0, self.frustration - 0.1)
            
        # 2. Confidence
        if any(w in text for w in ["i know", "obviously", "easy", "because", "definitely"]):
            self.confidence = min(1.0, self.confidence + 0.1)
        elif any(w in text for w in ["maybe", "guess", "think", "probably", "?", "um"]):
            self.confidence = max(0.0, self.confidence - 0.1)
            
        # 3. Curiosity
        if "?" in response and any(w in text for w in ["why", "how", "what if", "explain"]):
            self.curiosity = min(1.0, self.curiosity + 0.2)
            
        # 4. Energy
        if any(c in response for c in ["!", "omg", "cool", "wow", "thanks"]) or self._has_emoji(response):
            self.energy = min(1.0, self.energy + 0.15)
        elif words < 5 and "?" not in response:
            # Short, flat responses indicate low energy/boredom
            self.energy = max(0.0, self.energy - 0.1)
            
    def _has_emoji(self, text: str) -> bool:
        return any(char in text for char in "😊😂🥰👍🎉🔥💪🌟🥺😎")

    def get_state(self) -> Dict:
        """Returns readable state summary for the LLM"""
        mood = "Neutral"
        if self.frustration > 0.4: mood = "Frustrated/Struggling"
        elif self.curiosity > 0.6: mood = "Curious/Engaged"
        elif self.confidence > 0.8: mood = "Confident"
        elif self.confidence < 0.3: mood = "Uncertain/Shy"
        
        return {
            "mood": mood,
            "frustration": self.frustration,
            "energy": "High" if self.energy > 0.6 else "Low" if self.energy < 0.4 else "Neutral"
        }

    def determine_style(self, level: int) -> str:
        """Selects the best teaching persona based on current state"""
        # Priority 1: Frustration Management (Always pivot to cheerleader if frustrated)
        if self.frustration > 0.3:
            return "cheerleader"
        
        # Priority 2: Level-based defaults
        if level <= 2:
            # Low confidence beginners need support
            return "cheerleader" if self.confidence < 0.5 else "coach"
            
        if level >= 5:
            return "professor"
            
        # Priority 3: Personality adaptations
        if self.curiosity > 0.6:
            return "socratic"
            
        if self.energy > 0.7:
            return "cheerleader"  # Match high energy
            
        # Default for Level 3-4
        return "socratic"