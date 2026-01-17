"""Level Detection v3: LLM-First with Rule Validation"""

import re
from typing import Dict, Tuple, Optional

class RuleValidator:
    """Fast rule-based validation to catch extreme cases"""
    
    # Critical signals for extreme levels
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
        """Quick analysis for extreme signal detection"""
        response_lower = student_response.lower()
        
        # Count extreme signals
        confusion_signals = sum(1 for p in self.EXTREME_CONFUSION if re.search(p, response_lower))
        mastery_signals = sum(1 for p in self.EXTREME_MASTERY if re.search(p, response_lower))
        word_count = len(response_lower.split())
        
        return {
            "confusion": confusion_signals,
            "mastery": mastery_signals,
            "word_count": word_count
        }
    
    def get_constraint(self, analysis: Dict) -> Optional[Tuple[float, float]]:
        """Returns (min, max) constraint based on accumulated signals"""
        if analysis["confusion"] >= 2:
            return (1.0, 2.5)  # Hard cap on level if confused
        if analysis["mastery"] >= 2:
            return (4.0, 5.0)  # Floor on level if using advanced terms
        return None

class LLMFirstDetector:
    """Primary detector using LLM with rule validation"""
    
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
        # Context window management
        context = self.conversation_history if turn_number <= 3 else self.conversation_history[-8:]
        
        # 1. LLM Analysis
        try:
            llm_result = self.llm_client.analyze_level(context, self.topic, turn_number)
            level = llm_result.get("level", 3.0)
            conf = llm_result.get("confidence", 0.5)
        except Exception:
            level, conf = 3.0, 0.0
        
        # 2. Rule Validation
        last_msg = self.conversation_history[-1]["content"]
        analysis = self.validator.analyze(last_msg)
        constraint = self.validator.get_constraint(analysis)
        
        if constraint:
            min_l, max_l = constraint
            level = max(min_l, min(max_l, level))
        
        # 3. Stabilization (Weighted Average)
        if self.estimates_history:
            prev = self.estimates_history[-1]["level"]
            # Allow max 1.0 shift per turn
            if abs(level - prev) > 1.0:
                level = prev + (1.0 if level > prev else -1.0)
        
        self.estimates_history.append({"level": level, "confidence": conf})
        return level, conf
    
    def get_final_prediction(self) -> int:
        if not self.estimates_history: return 3
        # Median of last 3 estimates for stability
        recent = sorted([e["level"] for e in self.estimates_history[-3:]])
        final = recent[len(recent)//2]
        
        # Conservative rounding
        if final < 1.4: return 1
        if final < 2.4: return 2
        if final < 3.6: return 3
        if final < 4.6: return 4
        return 5