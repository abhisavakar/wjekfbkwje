"""Enhanced level detection with correctness analysis"""

import re
from typing import Dict, List, Tuple, Optional

class LevelDetector:
    """Detects student understanding level from conversation"""
    
    LEVEL_SIGNALS = {
        1: {
            "strong": [r"i don'?t know", r"no idea", r"what (is|does|are|means?)", r"never (learned|heard)", r"lost", r"confus(ed|ing)", r"fail", r"hate math", r"mess of letters", r"don'?t get it"],
            "weak": [r"forgot", r"unclear", r"hard", r"weird", r"guess"]
        },
        2: {
            "strong": [r"i think (maybe|it'?s)", r"i guess", r"is it\s*\?", r"not sure", r"probably", r"might be", r"um+,"],
            "weak": [r"right\?$", r"kind of"]
        },
        3: {
            "strong": [r"\bbecause\b", r"so (that|then)", r"for example", r"means that", r"like if", r"makes sense"],
            "weak": [r"i know", r"remember", r"ok"]
        },
        4: {
            "strong": [r"similar to", r"relates to", r"connect(ion|s)", r"reason is", r"in other words", r"analogy", r"compared to"],
            "weak": [r"another way", r"also"]
        },
        5: {
            "strong": [r"what if", r"i wonder", r"deep", r"assume", r"hypothetical", r"limitation", r"generalize", r"imply", r"implies", r"theory", r"hypothesis"],
            "weak": [r"curious", r"interesting", r"actually"]
        }
    }
    
    # Technical terms that indicate higher levels (4/5) - EXPANDED FOR PHYSICS
    TECHNICAL_TERMS = [
        # Math
        'coefficient', 'variable', 'function', 'derivative', 'integral', 'asymptote',
        'intercept', 'slope', 'parabola', 'quadratic',
        # Physics / Thermo
        'entropy', 'quantum', 'thermodynamic', 'enthalpy', 'ergodic', 'virial',
        'ensemble', 'microstate', 'partition', 'hamiltonian', 'trajectory',
        'momentum', 'velocity', 'spontaneous', 'equilibrium', 'activation energy',
        'catalyst', 'kinetic', 'gibbs', 'boltzmann', 'phase transition',
        'chemical potential', 'viscosity', 'diffusivity'
    ]
    
    CORRECTNESS_PATTERNS = {
        "correct": [r"exactly", r"correct", r"yes,? that'?s right", r"good job", r"perfect", r"spot on", r"you got it", r"doing great", r"right track"],
        "incorrect": [r"not quite", r"actually", r"almost", r"close"]
    }
    
    def __init__(self):
        self.level_scores = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
        self.current_estimate = 3.0
        self.confidence = 0.0
        self.turns_analyzed = 0
        self.correctness_history = []
    
    def add_exchange(self, tutor_msg: str, student_msg: str):
        self.turns_analyzed += 1
        self._analyze_correctness(tutor_msg)
        self._analyze_response(student_msg)
        self._update_estimate()
    
    def _analyze_correctness(self, tutor_msg: str):
        tutor_lower = tutor_msg.lower()
        is_correct = any(re.search(p, tutor_lower) for p in self.CORRECTNESS_PATTERNS["correct"])
        is_incorrect = any(re.search(p, tutor_lower) for p in self.CORRECTNESS_PATTERNS["incorrect"])
        
        if is_correct and not is_incorrect:
            self.correctness_history.append(True)
            # FIX: If student is struggling (Level 1 range), don't boost to Level 2/3 just for getting a guided question right.
            if self.current_estimate < 1.8:
                pass # Do nothing, stay at Level 1
            else:
                self.level_scores[3] += 1.0
                self.level_scores[4] += 0.5
        elif is_incorrect:
            self.correctness_history.append(False)
            self.level_scores[1] += 1.5 # Stronger penalty
            self.level_scores[2] += 1.0
    
    def _analyze_response(self, response: str):
        response_lower = response.lower()
        words = len(response.split())
        
        # 1. Technical Terminology (Boosts Level 5)
        term_count = sum(1 for term in self.TECHNICAL_TERMS if term in response_lower)
        if term_count >= 1:
            self.level_scores[4] += 1.0 * term_count
            self.level_scores[5] += 1.5 * term_count # Increased weight

        # 2. Response Length
        if words > 40:
            self.level_scores[5] += 2.0
            self.level_scores[4] += 1.0
        elif words < 6 and ("?" in response or "what" in response_lower):
            self.level_scores[1] += 2.5
            
        # 3. Pattern Matching
        for level, patterns in self.LEVEL_SIGNALS.items():
            for p in patterns["strong"]:
                if re.search(p, response_lower):
                    self.level_scores[level] += 3.0
            for p in patterns["weak"]:
                if re.search(p, response_lower):
                    self.level_scores[level] += 1.0
    
    def _update_estimate(self):
        total = sum(self.level_scores.values())
        if total == 0: return

        # Calculate weighted average
        weighted_sum = sum(lvl * score for lvl, score in self.level_scores.items())
        estimate = weighted_sum / total
        
        # --- EXTREME LEVEL CLAMPING (Aggressive) ---
        l1_ratio = self.level_scores[1] / total
        if l1_ratio > 0.25: # Lower threshold to catch Level 1
            estimate = min(estimate, 1.4) # Force to Level 1 range
            
        l5_ratio = self.level_scores[5] / total
        if l5_ratio > 0.25:
            estimate = max(estimate, 4.6) # Force to Level 5 range
            
        self.current_estimate = estimate
        self.confidence = min(0.95, total * 0.1)
    
    def get_estimate(self) -> Tuple[float, float]:
        return self.current_estimate, self.confidence


class HybridLevelDetector:
    def __init__(self, llm_client=None):
        self.rule_detector = LevelDetector()
        self.llm_client = llm_client
        self.topic = ""
        self.llm_estimates = []
    
    def set_topic(self, topic: str):
        self.topic = topic
    
    def add_exchange(self, tutor_msg: str, student_msg: str):
        self.rule_detector.add_exchange(tutor_msg, student_msg)
    
    def get_estimate(self, use_llm: bool = True) -> Tuple[float, float]:
        rule_est, rule_conf = self.rule_detector.get_estimate()
        
        # Don't use LLM for very early turns or if rule confidence is high enough for extremes
        if not use_llm or not self.llm_client or len(self.rule_detector.correctness_history) < 2:
            return rule_est, rule_conf
            
        try:
            # Only send last 6 turns to keep context focused
            llm_res = self.llm_client.analyze_level(
                self.rule_detector.conversation_history[-6:], 
                self.topic
            )
            llm_est = float(llm_res.get("level", 3.0))
            self.llm_estimates.append(llm_est)
            
            # Combine: LLM 60%, Rules 40%
            combined = (llm_est * 0.6) + (rule_est * 0.4)
            
            # If rules say EXTME (1 or 5), trust rules more
            if rule_est < 1.5: combined = min(combined, 1.5)
            if rule_est > 4.5: combined = max(combined, 4.5)
            
            return combined, max(rule_conf, 0.8)
        except:
            return rule_est, rule_conf