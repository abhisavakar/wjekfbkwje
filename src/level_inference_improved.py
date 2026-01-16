"""Enhanced level detection with Stabilization Logic (2-6-2 Strategy)"""

import re
from typing import Dict, List, Tuple, Optional

class LevelDetector:
    """Detects student understanding level from conversation"""
    
    LEVEL_SIGNALS = {
        1: {
            "strong": [r"i don'?t know", r"no idea", r"what (is|does|are|means?)", r"never (learned|heard)", r"lost", r"confus(ed|ing)", r"fail", r"hate math", r"mess of letters", r"don'?t get it", r"stuck"],
            "weak": [r"forgot", r"unclear", r"hard", r"weird", r"guess", r"tricky"]
        },
        2: {
            "strong": [r"i think (maybe|it'?s)", r"i guess", r"is it\s*\?", r"not sure", r"probably", r"might be", r"um+,"],
            "weak": [r"right\?$", r"kind of"]
        },
        3: {
            "strong": [r"\bbecause\b", r"so (that|then)", r"for example", r"means that", r"like if", r"makes sense"],
            "weak": [r"i know", r"remember", r"ok", r"got it"]
        },
        4: {
            "strong": [r"similar to", r"relates to", r"connect(ion|s)", r"reason is", r"in other words", r"analogy", r"compared to"],
            "weak": [r"another way", r"also"]
        },
        5: {
            "strong": [r"what if", r"i wonder", r"deep", r"assume", r"hypothetical", r"limitation", r"generalize", r"imply", r"implies", r"theory", r"hypothesis", r"paradox"],
            "weak": [r"curious", r"interesting", r"actually", r"technically"]
        }
    }
    
    # Advanced terms only
    TECHNICAL_TERMS = [
        'derivative', 'integral', 'asymptote', 'limit', 'continuity',
        'parametric', 'vector', 'scalar', 'matrix',
        'entropy', 'quantum', 'thermodynamic', 'enthalpy', 'ergodic', 'virial',
        'ensemble', 'microstate', 'partition', 'hamiltonian', 'trajectory',
        'spontaneous', 'equilibrium', 'activation energy', 'catalyst', 
        'gibbs', 'boltzmann', 'phase transition', 'chemical potential',
        'recurrence', 'bekenstein', 'hawking', 'past hypothesis'
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
        self.confusion_detected = False
        self.advanced_vocabulary_count = 0
    
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
            # Correct = Level 3 (Competent)
            self.level_scores[3] += 2.0
        elif is_incorrect:
            self.correctness_history.append(False)
            self.level_scores[1] += 1.5
            self.level_scores[2] += 1.0
    
    def _analyze_response(self, response: str):
        response_lower = response.lower()
        words = len(response.split())
        
        # Check for confusion signs
        if any(re.search(p, response_lower) for p in self.LEVEL_SIGNALS[1]["strong"] + self.LEVEL_SIGNALS[2]["strong"]):
            self.confusion_detected = True
        
        # Check for Advanced Vocabulary
        term_count = sum(1 for term in self.TECHNICAL_TERMS if term in response_lower)
        self.advanced_vocabulary_count += term_count
        
        if term_count >= 1:
            self.level_scores[4] += 1.0 * term_count
            self.level_scores[5] += 3.0 * term_count

        # Length Heuristic
        if words > 40:
            self.level_scores[5] += 1.0
            self.level_scores[4] += 1.0
        elif words < 6 and ("?" in response or "what" in response_lower):
            self.level_scores[1] += 2.0
            
        # Pattern Matching
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

        # 1. Calculate Raw Estimate from Data
        weighted_sum = sum(lvl * score for lvl, score in self.level_scores.items())
        raw_estimate = weighted_sum / total
        
        # 2. Apply Logical Clamps (Bounds Checking)
        
        # Level 1 Clamp
        if (self.level_scores[1] / total) > 0.25: 
            raw_estimate = min(raw_estimate, 1.4)
            
        # Level 5 Clamp
        l5_ratio = self.level_scores[5] / total
        if l5_ratio > 0.35: 
            is_high_level_confusion = self.confusion_detected and self.advanced_vocabulary_count > 2
            if self.confusion_detected and not is_high_level_confusion:
                raw_estimate = min(raw_estimate, 3.8)
            else:
                raw_estimate = max(raw_estimate, 4.6)

        # 3. STABILIZATION (The 2-6-2 Strategy)
        # This prevents the "drifting up" issue by anchoring to the previous value.
        
        if self.turns_analyzed <= 2:
            # Phase 1: Rapid Diagnosis
            # Trust the raw data completely to allow quick jumps
            self.current_estimate = raw_estimate
            
        elif self.turns_analyzed <= 8:
            # Phase 2: Dampened Teaching
            # 80% Previous Estimate + 20% New Raw Data
            # This makes the score "heavy" and hard to move up quickly
            self.current_estimate = (self.current_estimate * 0.8) + (raw_estimate * 0.2)
            
        else:
            # Phase 3: Lock
            # 95% Previous Estimate + 5% New Data
            # Effectively freezes the score for the final evaluation
            self.current_estimate = (self.current_estimate * 0.95) + (raw_estimate * 0.05)
            
        self.confidence = min(0.95, total * 0.1)
    
    def get_estimate(self) -> Tuple[float, float]:
        return self.current_estimate, self.confidence

class HybridLevelDetector:
    def __init__(self, llm_client=None):
        self.rule_detector = LevelDetector()
        self.llm_client = llm_client
        self.topic = ""
    
    def set_topic(self, topic: str):
        self.topic = topic
    
    def add_exchange(self, tutor_msg: str, student_msg: str):
        self.rule_detector.add_exchange(tutor_msg, student_msg)
    
    def get_estimate(self, use_llm: bool = True) -> Tuple[float, float]:
        rule_est, rule_conf = self.rule_detector.get_estimate()
        
        if not use_llm or not self.llm_client:
            return rule_est, rule_conf
            
        try:
            llm_res = self.llm_client.analyze_level(self.rule_detector.conversation_history[-6:], self.topic)
            llm_est = float(llm_res.get("level", 3.0))
            
            # Use same dampening logic for LLM mix
            # If we are late in the conversation, trust the stabilized rule detector more
            if self.rule_detector.turns_analyzed > 5:
                combined = (llm_est * 0.4) + (rule_est * 0.6)
            else:
                combined = (llm_est * 0.6) + (rule_est * 0.4)
            
            # Safety Nets
            if rule_est < 1.5: combined = min(combined, 1.5)
            if self.rule_detector.confusion_detected and self.rule_detector.advanced_vocabulary_count <= 2:
                combined = min(combined, 3.9)
            
            return combined, max(rule_conf, 0.8)
        except:
            return rule_est, rule_conf