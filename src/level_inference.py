"""Level detection from conversation analysis"""

import re
from typing import Dict, List, Tuple

class LevelDetector:
    """Detects student understanding level from conversation"""
    
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
            ],
            "weak": [
                r"confus",
                r"forgot",
            ]
        },
        2: {
            "strong": [
                r"i think (maybe|it'?s)",
                r"i guess",
                r"is it\??",
                r"not sure",
                r"i hope .* right",
            ],
            "weak": [
                r"right\?$",
                r"probably",
            ]
        },
        3: {
            "strong": [
                r"because",
                r"so (that|then|it)",
                r"for example",
                r"this means",
            ],
            "weak": [
                r"i (know|learned|understand)",
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
    
    def add_exchange(self, tutor_msg: str, student_msg: str):
        """Add a conversation exchange"""
        self.conversation_history.append({"role": "tutor", "content": tutor_msg})
        self.conversation_history.append({"role": "student", "content": student_msg})
        self._analyze_response(student_msg)
    
    def _analyze_response(self, response: str):
        """Analyze a student response for level signals"""
        response_lower = response.lower()
        
        for level, patterns in self.LEVEL_SIGNALS.items():
            for pattern in patterns["strong"]:
                if re.search(pattern, response_lower):
                    self.level_scores[level] += 2
            for pattern in patterns["weak"]:
                if re.search(pattern, response_lower):
                    self.level_scores[level] += 1
        
        # Update estimate
        self._update_estimate()
    
    def _update_estimate(self):
        """Update the level estimate based on accumulated scores"""
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
            
            # Combine: weight LLM higher if confident
            if llm_conf > 0.7:
                combined_level = llm_level * 0.7 + rule_level * 0.3
            else:
                combined_level = llm_level * 0.5 + rule_level * 0.5
            
            combined_conf = max(rule_conf, llm_conf)
            return combined_level, combined_conf
        
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return rule_level, rule_conf
    
    def get_predicted_level(self, use_llm: bool = True) -> int:
        level, _ = self.get_estimate(use_llm)
        return round(level)