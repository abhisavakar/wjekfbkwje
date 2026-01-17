"""Level Detection v3: LLM-First with Rule Validation"""

import re
from typing import Dict, List, Tuple, Optional

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
    
    CONFIDENCE_SIGNALS = {
        "uncertain": [r"i think", r"i guess", r"maybe", r"not sure", r"probably"],
        "confident": [r"because", r"therefore", r"this means", r"so then"]
    }
    
    def __init__(self):
        self.confusion_count = 0
        self.mastery_count = 0
        self.uncertain_count = 0
        self.confident_count = 0
    
    def analyze(self, student_response: str) -> Dict:
        """Quick analysis for extreme signal detection"""
        response_lower = student_response.lower()
        
        # Count extreme signals
        confusion_signals = sum(1 for p in self.EXTREME_CONFUSION if re.search(p, response_lower))
        mastery_signals = sum(1 for p in self.EXTREME_MASTERY if re.search(p, response_lower))
        uncertain_signals = sum(1 for p in self.CONFIDENCE_SIGNALS["uncertain"] if re.search(p, response_lower))
        confident_signals = sum(1 for p in self.CONFIDENCE_SIGNALS["confident"] if re.search(p, response_lower))
        
        self.confusion_count += confusion_signals
        self.mastery_count += mastery_signals
        self.uncertain_count += uncertain_signals
        self.confident_count += confident_signals
        
        # Response length
        word_count = len(response_lower.split())
        
        return {
            "confusion_signals": confusion_signals,
            "mastery_signals": mastery_signals,
            "uncertain_signals": uncertain_signals,
            "confident_signals": confident_signals,
            "word_count": word_count,
            "has_extreme_confusion": confusion_signals >= 2,
            "has_extreme_mastery": mastery_signals >= 2,
            "very_short": word_count < 5
        }
    
    def get_constraint(self) -> Optional[Tuple[float, float]]:
        """Returns (min, max) constraint based on accumulated signals, or None"""
        
        # Strong Level 1 signals
        if self.confusion_count >= 3 and self.uncertain_count >= 2:
            return (1.0, 2.0)  # Must be Level 1-2
        
        # Strong Level 5 signals
        if self.mastery_count >= 4:
            return (4.5, 5.0)  # Must be Level 5
        
        # Moderate constraints
        if self.confusion_count >= 2:
            return (1.0, 3.0)  # Max Level 3
        
        if self.mastery_count >= 2 and self.confident_count >= 2:
            return (4.0, 5.0)  # Min Level 4
        
        return None  # No strong constraint


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
        """Add conversation turn and analyze"""
        self.conversation_history.append({
            "role": "tutor",
            "content": tutor_msg
        })
        self.conversation_history.append({
            "role": "student", 
            "content": student_msg
        })
        
        # Run rule validation
        self.validator.analyze(student_msg)
    
    def get_estimate(self, turn_number: int) -> Tuple[float, float]:
        """Get level estimate with confidence - NOW WITH STABILIZATION"""
        
        # Early turns: use all available data
        # Later turns: use recent context (last 6 messages)
        if turn_number <= 3:
            context = self.conversation_history
        else:
            context = self.conversation_history[-8:]  # Last 4 exchanges
        
        if not context:
            return 3.0, 0.0
        
        # 1. Get LLM Analysis (PRIMARY)
        try:
            llm_result = self.llm_client.analyze_level(context, self.topic, turn_number)
            llm_level = float(llm_result.get("level", 3.0))
            llm_conf = float(llm_result.get("confidence", 0.5))
            reasoning = llm_result.get("reasoning", "")
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            llm_level = 3.0
            llm_conf = 0.3
            reasoning = "LLM error"
        
        # 2. Apply Rule Constraints (SECONDARY)
        constraint = self.validator.get_constraint()
        
        if constraint:
            min_level, max_level = constraint
            original_level = llm_level
            llm_level = max(min_level, min(max_level, llm_level))
            
            if abs(original_level - llm_level) > 0.5:
                print(f"  🔧 Rule constraint: {original_level:.1f} → {llm_level:.1f} (bounds: {min_level}-{max_level})")
        
        # 3. STABILIZATION: Prevent wild jumps
        if len(self.estimates_history) >= 1:
            prev_level = self.estimates_history[-1]["level"]
            
            # If jump is > 1.0, dampen it
            jump = llm_level - prev_level
            if abs(jump) > 1.0:
                # Only allow 50% of the jump per turn
                llm_level = prev_level + (jump * 0.5)
                print(f"  🔒 Dampening: {prev_level:.1f} → {llm_level:.1f} (was trying to jump to {prev_level + jump:.1f})")
        
        # 4. Confidence Boost Logic
        # If multiple turns agree, boost confidence
        if len(self.estimates_history) >= 2:
            recent_estimates = [e["level"] for e in self.estimates_history[-2:]]
            if all(abs(est - llm_level) < 0.5 for est in recent_estimates):
                llm_conf = min(0.95, llm_conf + 0.15)  # Boost for consistency
        
        # 5. Turn-based confidence adjustment
        if turn_number >= 3:
            llm_conf = min(0.95, llm_conf + 0.1)  # More confident with more data
        
        # Store estimate
        self.estimates_history.append({
            "level": llm_level,
            "confidence": llm_conf,
            "reasoning": reasoning,
            "turn": turn_number
        })
        
        return llm_level, llm_conf
    
    def get_final_prediction(self) -> int:
        """Get final integer prediction with CONSERVATIVE rounding"""
        if not self.estimates_history:
            return 3
        
        # Use the MEDIAN of last 3 estimates (more stable than just last)
        recent_estimates = [e["level"] for e in self.estimates_history[-3:]]
        if len(recent_estimates) >= 2:
            recent_estimates.sort()
            final_estimate = recent_estimates[len(recent_estimates) // 2]  # Median
        else:
            final_estimate = self.estimates_history[-1]["level"]
        
        # CONSERVATIVE rounding - favor lower levels when uncertain
        # This prevents over-estimating
        if final_estimate < 1.4:
            return 1
        elif final_estimate < 2.4:
            return 2
        elif final_estimate < 3.6:  # Wider range for Level 3 (most common)
            return 3
        elif final_estimate < 4.6:
            return 4
        else:
            return 5