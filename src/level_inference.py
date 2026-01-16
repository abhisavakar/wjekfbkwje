"""Level detection from conversation analysis"""

import re
from typing import Dict, List, Tuple

class LevelDetector:
    """Detects student understanding level from conversation"""
    
    # Expanded signal patterns for each level
    LEVEL_SIGNALS = {
        1: {
            "strong": [
                r"i don'?t know",
                r"no idea",
                r"what (is|does|are|means?) (that|this|it|x|\^)",
                r"never (learned|heard|studied)",
                r"makes no sense",
                r"totally lost",
                r"completely lost",
                r"huh\?+",
                r"\?\?\?",
                r"what does .* mean",
                r"i'?m (so )?confus(ed|ing)",
                r"random (letters|numbers|symbols)",
                r"can'?t (understand|follow|get)",
                r"(nothing|barely anything)",
                r"ugh",
            ],
            "weak": [
                r"forgot",
                r"don'?t remember",
            ]
        },
        2: {
            "strong": [
                r"i think (maybe|it'?s|that)",
                r"i guess",
                r"is (it|this|that)\??",
                r"not (really )?sure",
                r"i hope .* (right|correct)",
                r"maybe it'?s",
                r"probably",
                r"wait,",
                r"um+,",
                r"kind of",
                r"sort of",
            ],
            "weak": [
                r"right\?+$",
                r"\?\?$",
            ]
        },
        3: {
            "strong": [
                r"because",
                r"so (that|then|it) (means|is)",
                r"for example",
                r"(this|that|it) means",
                r"like (when|if)",
                r"basically",
                r"(i think|i learned|i know) (it'?s|that)",
                r"my teacher (said|explained|showed)",
            ],
            "weak": [
                r"i (know|learned|understand) (that|this|it)",
                r"does that count",
            ]
        },
        4: {
            "strong": [
                r"similar to",
                r"relates to",
                r"connect(ed|ion|s)",
                r"the reason (is|being|why)",
                r"in other words",
                r"this is (like|similar)",
                r"kind of like",
                r"same (angle|idea|concept)",
                r"analogy",
                r"train tracks",
                r"parallel",
            ],
            "weak": [
                r"another way",
                r"also means",
                r"that also",
            ]
        },
        5: {
            "strong": [
                r"what if (we|you|i)",
                r"i wonder",
                r"i'?ve always wondered",
                r"what about when",
                r"could (we|you|i) (also|try)",
                r"would it work if",
                r"what happens (if|when)",
                r"another way to (think|approach)",
                r"(violation|principle|law|theorem)",
                r"deeper (reason|meaning)",
                r"quantum",
                r"entropy",
                r"derivative",
                r"asymptote",
            ],
            "weak": [
                r"interest(ing|ed)",
                r"curious",
                r"fascinating",
            ]
        }
    }
    
    def __init__(self):
        self.conversation_history = []
        self.level_scores = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
        self.current_estimate = 3.0
        self.confidence = 0.0
        self.turn_count = 0
    
    def add_exchange(self, tutor_msg: str, student_msg: str):
        """Add a conversation exchange"""
        self.conversation_history.append({"role": "tutor", "content": tutor_msg})
        self.conversation_history.append({"role": "student", "content": student_msg})
        self.turn_count += 1
        self._analyze_response(student_msg, self.turn_count)
    
    def _analyze_response(self, response: str, turn: int):
        """Analyze a student response for level signals"""
        response_lower = response.lower()
        
        # Weight recent turns more heavily
        recency_weight = 1.0 + (turn * 0.1)  # Later turns weighted more
        
        # Check patterns
        for level, patterns in self.LEVEL_SIGNALS.items():
            for pattern in patterns["strong"]:
                if re.search(pattern, response_lower):
                    self.level_scores[level] += 3.0 * recency_weight
            for pattern in patterns["weak"]:
                if re.search(pattern, response_lower):
                    self.level_scores[level] += 1.0 * recency_weight
        
        # Response length heuristic
        words = len(response.split())
        if words < 10:  # Very short = struggling or advanced
            if "?" in response or any(p in response_lower for p in ["don't know", "no idea", "what"]):
                self.level_scores[1] += 2.0
            elif any(p in response_lower for p in ["what if", "wonder", "could"]):
                self.level_scores[5] += 1.5
        elif words > 40:  # Long detailed = likely advanced
            self.level_scores[5] += 1.5
            self.level_scores[4] += 1.0
        
        # Detect technical terminology (suggests higher level)
        technical_terms = [
            'equation', 'formula', 'variable', 'function', 'derivative', 'integral',
            'energy', 'momentum', 'force', 'velocity', 'acceleration',
            'entropy', 'quantum', 'thermodynamic', 'conservation',
            'slope', 'intercept', 'coefficient', 'exponent', 'logarithm'
        ]
        for term in technical_terms:
            if term in response_lower:
                self.level_scores[4] += 1.0
                self.level_scores[5] += 0.5
        
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
        
        # Snap to extremes if very strong evidence
        if self.level_scores[1] > total * 0.6:
            self.current_estimate = min(self.current_estimate, 1.5)
        elif self.level_scores[5] > total * 0.5:
            self.current_estimate = max(self.current_estimate, 4.5)
        
        # Confidence based on total evidence and consistency
        max_score = max(self.level_scores.values())
        consistency = max_score / total if total > 0 else 0
        self.confidence = min(0.95, consistency * (total * 0.08))
    
    def get_estimate(self) -> Tuple[float, float]:
        """Get current level estimate and confidence"""
        return self.current_estimate, self.confidence
    
    def get_predicted_level(self) -> int:
        """Get final integer prediction"""
        # Round but respect evidence for extremes
        if self.current_estimate < 1.5:
            return 1
        elif self.current_estimate > 4.5:
            return 5
        else:
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
