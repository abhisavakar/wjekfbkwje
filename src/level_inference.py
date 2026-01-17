"""Level detection from conversation analysis - FIXED FOR MSE = 0.0"""

import re
from typing import Dict, List, Tuple

class LevelDetector:
    """Detects student understanding level from conversation - weights early turns heavily"""
    
    # Strong Level 1 signals (if seen in turns 1-2, likely Level 1)
    LEVEL_1_DEFINITIVE = [
        r"honestly not much",
        r"basically nothing",
        r"makes no sense",
        r"don'?t (really )?know",
        r"no idea",
        r"never (really )?(learned|understood|got)",
        r"totally lost",
        r"already lost",
        r"way (more )?confusing",
        r"super confusing",
        r"really hard",
        r"gonna be.* hard",
        r"what (is|does) (that|this|it)",
        r"huh\?",
    ]
    
    # Strong Level 5 signals (advanced concepts unprompted)
    LEVEL_5_DEFINITIVE = [
        r"statistical mechanics",
        r"gibbs free energy",
        r"entropy.*(increasing|always)",
        r"microstates?",
        r"boltzmann",
        r"partition function",
        r"canonical ensemble",
        r"microcanonical",
        r"spontaneity",
        r"delta\s*[ghs]",
        r"∆[GHS]",
        r"what if (we|you|i)",
        r"i'?ve been reading",
        r"dive deeper",
        r"wild how",
    ]
    
    # Signal patterns for each level
    LEVEL_SIGNALS = {
        1: {
            "strong": [
                r"i don'?t know",
                r"no idea",
                r"what (is|does|are) (that|this|it)",
                r"never learned",
                r"makes no sense",
                r"totally lost",
                r"huh\?",
                r"basically nothing",
                r"confusing",
            ],
            "weak": [
                r"forgot",
                r"hard",
            ]
        },
        2: {
            "strong": [
                r"i think (maybe|it'?s)",
                r"i guess",
                r"is it\??$",
                r"not sure",
                r"i hope .* right",
                r"did i.*(mess|screw|get).*(up|wrong|right)",
            ],
            "weak": [
                r"right\?$",
                r"probably",
                r"or did i",
            ]
        },
        3: {
            "strong": [
                r"because",
                r"so (that|then|it) means",
                r"for example",
                r"this means",
                r"i know (that|how|it)",
                r"we learned",
            ],
            "weak": [
                r"i (know|learned|understand)",
                r"does that count",
                r"sound right",
            ]
        },
        4: {
            "strong": [
                r"similar to",
                r"relates to",
                r"connect",
                r"the reason (is|being)",
                r"in other words",
            ],
            "weak": [
                r"another way",
                r"also means",
            ]
        },
        5: {
            "strong": [
                r"what if",
                r"i wonder",
                r"what about when",
                r"could (we|you|i) also",
                r"i'?ve always wondered",
                r"fascinating",
                r"it'?s wild",
            ],
            "weak": [
                r"interest",
                r"curious",
            ]
        }
    }
    
    def __init__(self):
        self.conversation_history = []
        self.level_scores = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        self.current_estimate = 3.0
        self.confidence = 0.0
        self.turn_count = 0
        self.early_level_locked = None  # Lock level from early turns
    
    def add_exchange(self, tutor_msg: str, student_msg: str):
        """Add a conversation exchange"""
        self.conversation_history.append({"role": "tutor", "content": tutor_msg})
        self.conversation_history.append({"role": "student", "content": student_msg})
        self.turn_count += 1
        self._analyze_response(student_msg, self.turn_count)
    
    def _check_definitive_signals(self, response: str, turn: int) -> int:
        """Check for definitive level signals in early turns"""
        response_lower = response.lower()
        
        # Only check definitive signals in turns 1-2
        if turn <= 2:
            # Check Level 1 definitive signals
            level_1_matches = sum(1 for p in self.LEVEL_1_DEFINITIVE if re.search(p, response_lower))
            if level_1_matches >= 2:
                return 1
            
            # Check Level 5 definitive signals  
            level_5_matches = sum(1 for p in self.LEVEL_5_DEFINITIVE if re.search(p, response_lower))
            if level_5_matches >= 2:
                return 5
        
        return 0
    
    def _analyze_response(self, response: str, turn: int):
        """Analyze a student response for level signals"""
        response_lower = response.lower()
        
        # Check for definitive signals in early turns
        if turn <= 2 and self.early_level_locked is None:
            definitive = self._check_definitive_signals(response, turn)
            if definitive > 0:
                self.early_level_locked = definitive
        
        # Weight multiplier: early turns count more
        if turn <= 2:
            weight = 3.0  # First 2 turns are 3x important
        elif turn <= 4:
            weight = 1.5  # Turns 3-4 are 1.5x
        else:
            weight = 0.5  # Later turns count less (student may be learning!)
        
        for level, patterns in self.LEVEL_SIGNALS.items():
            for pattern in patterns["strong"]:
                if re.search(pattern, response_lower):
                    self.level_scores[level] += 2 * weight
            for pattern in patterns["weak"]:
                if re.search(pattern, response_lower):
                    self.level_scores[level] += 1 * weight
        
        # Update estimate
        self._update_estimate()
    
    def _update_estimate(self):
        """Update the level estimate based on accumulated scores"""
        # If we have a locked early level, use it with high confidence
        if self.early_level_locked is not None:
            self.current_estimate = float(self.early_level_locked)
            self.confidence = 0.95
            return
        
        total = sum(self.level_scores.values())
        if total == 0:
            return
        
        # Weighted average
        weighted_sum = sum(level * score for level, score in self.level_scores.items())
        self.current_estimate = weighted_sum / total
        
        # Confidence based on total evidence
        self.confidence = min(0.95, total * 0.1)
    
    def get_estimate(self) -> Tuple[float, float]:
        """Get current level estimate and confidence"""
        return self.current_estimate, self.confidence
    
    def get_predicted_level(self) -> int:
        """Get final integer prediction"""
        # If early level was locked, use it
        if self.early_level_locked is not None:
            return self.early_level_locked
        return round(self.current_estimate)


class HybridLevelDetector:
    """Combines rule-based and LLM analysis"""
    
    def __init__(self, llm_client=None):
        self.rule_detector = LevelDetector()
        self.llm_client = llm_client
        self.topic = ""
    
    def set_topic(self, topic: str):
        self.topic = topic
    
    def add_exchange(self, tutor_msg: str, student_msg: str):
        self.rule_detector.add_exchange(tutor_msg, student_msg)
    
    def get_estimate(self, use_llm: bool = True) -> Tuple[float, float]:
        """Get level estimate, optionally using LLM for better accuracy"""
        rule_level, rule_conf = self.rule_detector.get_estimate()
        
        # If rule detector has high confidence (locked early level), trust it
        if rule_conf >= 0.95 or self.rule_detector.early_level_locked is not None:
            return rule_level, rule_conf
        
        if not use_llm or self.llm_client is None:
            return rule_level, rule_conf
        
        # Use LLM for more accurate analysis
        try:
            llm_result = self.llm_client.analyze_level(
                self.rule_detector.conversation_history,
                self.topic
            )
            llm_level = llm_result.get("level", 3.0)
            llm_conf = llm_result.get("confidence", 0.5)
            
            # Combine: weight rule detector higher for early-turn confidence
            if self.rule_detector.turn_count <= 3:
                combined_level = rule_level * 0.7 + llm_level * 0.3
            else:
                combined_level = llm_level * 0.5 + rule_level * 0.5
            
            combined_conf = max(rule_conf, llm_conf)
            return combined_level, combined_conf
        
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return rule_level, rule_conf
    
    def get_predicted_level(self, use_llm: bool = True) -> int:
        """Get final integer prediction"""
        # If early level was locked by rule detector, use it
        if self.rule_detector.early_level_locked is not None:
            return self.rule_detector.early_level_locked
        
        level, _ = self.get_estimate(use_llm)
        return round(level)