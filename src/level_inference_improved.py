"""Level Detection v4.0: Extreme Trust Protocol"""

import re
from typing import Dict, Tuple, Optional

class RuleValidator:
    """Fast rule-based validation to catch extreme cases"""
    
    EXTREME_CONFUSION = [
        r"i don'?t know", r"no idea", r"what (is|does|are|means?)", 
        r"never (learned|heard)", r"totally lost", r"makes no sense",
        r"bunch of (random|weird)", r"\?\?\?", r"huh\??"
    ]
    
    EXTREME_MASTERY = [
        r"entropy", r"derivative", r"integral", r"quantum", r"thermodynamic",
        r"asymptote", r"parametric", r"matrix", r"hamiltonian", r"equilibrium",
        r"what if we (change|tried|consider)", r"i'?ve always wondered",
        r"limitation", r"paradox", r"hypothesis", r"implication"
    ]
    
    def analyze(self, student_response: str) -> Dict:
        response_lower = student_response.lower()
        confusion_signals = sum(1 for p in self.EXTREME_CONFUSION if re.search(p, response_lower))
        mastery_signals = sum(1 for p in self.EXTREME_MASTERY if re.search(p, response_lower))
        
        return {
            "confusion": confusion_signals,
            "mastery": mastery_signals
        }
    
    def get_constraint(self, analysis: Dict) -> Optional[Tuple[float, float]]:
        # If student says "I don't know", HARD CAP at 1.5. No exceptions.
        if analysis["confusion"] >= 1:
            return (1.0, 1.5) 
        if analysis["mastery"] >= 2:
            return (4.5, 5.0)
        return None

class LLMFirstDetector:
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.validator = RuleValidator()
        self.conversation_history = []
        self.topic = ""
        self.estimates_history = []
    
    def set_topic(self, topic: str):
        self.topic = topic
    
    def add_exchange(self, tutor_msg: str, student_msg: str):
        self.conversation_history.append({"role": "tutor", "content": tutor_msg})
        self.conversation_history.append({"role": "student", "content": student_msg})
    
    def get_estimate(self, turn_number: int) -> Tuple[float, float]:
        context = self.conversation_history if turn_number <= 3 else self.conversation_history[-8:]
        
        # 1. LLM Analysis
        try:
            llm_result = self.llm_client.analyze_level(context, self.topic, turn_number)
            level = llm_result.get("level", 3.0)
            conf = llm_result.get("confidence", 0.5)
        except Exception:
            level, conf = 3.0, 0.0
        
        # 2. Rule Validation (Safety Net)
        last_msg = self.conversation_history[-1]["content"]
        analysis = self.validator.analyze(last_msg)
        constraint = self.validator.get_constraint(analysis)
        
        if constraint:
            min_l, max_l = constraint
            level = max(min_l, min(max_l, level))
            # If rules triggered, boost confidence in that extreme
            conf = 0.95 

        # 3. EXTREME TRUST PROTOCOL (The Fix for MSE)
        # If we are super confident it's an extreme level, DO NOT average with history.
        # This prevents "drifting to the middle".
        is_extreme = (level <= 1.5 or level >= 4.5)
        if is_extreme and conf > 0.9:
            self.estimates_history.append({"level": level, "confidence": conf})
            return level, conf

        # 4. Inertia (Only applies to non-extremes)
        if self.estimates_history:
            prev_level = self.estimates_history[-1]["level"]
            avg_history = sum(e["level"] for e in self.estimates_history) / len(self.estimates_history)
            
            if abs(level - avg_history) > 1.0:
                if conf < 0.9:
                    level = (level + avg_history * 2) / 3
        
        self.estimates_history.append({"level": level, "confidence": conf})
        return level, conf
    
    def get_final_prediction(self) -> int:
        if not self.estimates_history: return 3
        
        # If the last 2 turns were definitely Level 1, predict Level 1 (ignore early guesses)
        last_3 = [e["level"] for e in self.estimates_history[-3:]]
        avg_last_3 = sum(last_3) / len(last_3)
        
        if avg_last_3 <= 1.5: return 1
        if avg_last_3 >= 4.5: return 5
        
        # Otherwise use full average
        levels = [e["level"] for e in self.estimates_history]
        avg_level = sum(levels) / len(levels)
        
        if avg_level < 1.6: return 1
        if avg_level < 2.6: return 2
        if avg_level < 3.6: return 3
        if avg_level < 4.6: return 4
        return 5