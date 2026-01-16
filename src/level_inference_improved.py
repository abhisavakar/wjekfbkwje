"""Enhanced level detection with correctness analysis"""

import re
from typing import Dict, List, Tuple, Optional

class LevelDetector:
    """Detects student understanding level from conversation"""
    
    # Enhanced signal patterns for each level
    LEVEL_SIGNALS = {
        1: {
            "strong": [
                r"i don'?t know",
                r"no idea",
                r"what (is|does|are|means?) (that|this|it)",
                r"never (learned|heard|seen)",
                r"makes no sense",
                r"totally lost",
                r"huh\?+",
                r"confused",
                r"don'?t understand",
                r"can'?t remember",
                r"forgot everything",
            ],
            "weak": [
                r"forgot",
                r"not sure what",
                r"unclear",
            ]
        },
        2: {
            "strong": [
                r"i think (maybe|it'?s|that)",
                r"i guess",
                r"is it\s*\?",
                r"not (really )?sure",
                r"i hope .* right",
                r"probably",
                r"might be",
                r"um\.\.\.",
                r"uh\.\.\.",
            ],
            "weak": [
                r"right\?$",
                r"kind of",
                r"sort of",
            ]
        },
        3: {
            "strong": [
                r"\bbecause\b",
                r"so (that|then|it)",
                r"for example",
                r"this means",
                r"which means",
                r"like if",
                r"such as",
            ],
            "weak": [
                r"i (know|learned|understand|think i)",
                r"makes sense",
                r"remember that",
            ]
        },
        4: {
            "strong": [
                r"similar to",
                r"relates to",
                r"connect(ed|s|ion)",
                r"the reason (is|being|why)",
                r"in other words",
                r"this is like",
                r"related to",
                r"compared to",
            ],
            "weak": [
                r"another way",
                r"also means",
                r"plus",
            ]
        },
        5: {
            "strong": [
                r"what if",
                r"i wonder",
                r"what about when",
                r"could (we|you|i) also",
                r"i'?ve always wondered",
                r"how does .* relate to",
                r"would (it|this) work if",
                r"but what about",
                r"the deeper",
            ],
            "weak": [
                r"interest(ing|ed)",
                r"curious",
                r"actually",
            ]
        }
    }
    
    # Correctness indicators
    CORRECTNESS_PATTERNS = {
        "correct": [
            r"exactly",
            r"correct",
            r"yes,? that'?s right",
            r"good",
            r"perfect",
        ],
        "incorrect": [
            r"not quite",
            r"actually,?",
            r"almost",
            r"close,? but",
        ]
    }
    
    def __init__(self):
        self.conversation_history = []
        self.level_scores = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
        self.current_estimate = 3.0
        self.confidence = 0.0
        self.turns_analyzed = 0
        self.correctness_track = []  # Track correct/incorrect responses
    
    def add_exchange(self, tutor_msg: str, student_msg: str):
        """Add a conversation exchange"""
        self.conversation_history.append({"role": "tutor", "content": tutor_msg})
        self.conversation_history.append({"role": "student", "content": student_msg})
        self.turns_analyzed += 1
        
        # Analyze correctness from tutor feedback
        self._analyze_correctness(tutor_msg)
        
        # Analyze student response patterns
        self._analyze_response(student_msg)
    
    def _analyze_correctness(self, tutor_msg: str):
        """Analyze tutor's feedback to infer if student was correct"""
        tutor_lower = tutor_msg.lower()
        
        # Check if tutor indicated correctness
        is_correct = False
        is_incorrect = False
        
        for pattern in self.CORRECTNESS_PATTERNS["correct"]:
            if re.search(pattern, tutor_lower):
                is_correct = True
                break
        
        for pattern in self.CORRECTNESS_PATTERNS["incorrect"]:
            if re.search(pattern, tutor_lower):
                is_incorrect = True
                break
        
        if is_correct and not is_incorrect:
            self.correctness_track.append(1)
            # Boost higher levels for correct answers
            self.level_scores[3] += 1.5
            self.level_scores[4] += 1.0
            self.level_scores[5] += 0.5
        elif is_incorrect:
            self.correctness_track.append(0)
            # Boost lower levels for incorrect answers
            self.level_scores[1] += 1.0
            self.level_scores[2] += 1.5
            self.level_scores[3] += 0.5
    
    def _analyze_response(self, response: str):
        """Analyze a student response for level signals"""
        response_lower = response.lower()
        
        # Check response length (very short = struggling)
        words = response.split()
        if len(words) <= 3 and self.turns_analyzed <= 3:
            self.level_scores[1] += 1.5
            self.level_scores[2] += 0.5
        
        # Pattern matching
        for level, patterns in self.LEVEL_SIGNALS.items():
            for pattern in patterns["strong"]:
                if re.search(pattern, response_lower):
                    self.level_scores[level] += 2.0
            for pattern in patterns["weak"]:
                if re.search(pattern, response_lower):
                    self.level_scores[level] += 0.5
        
        # Update estimate
        self._update_estimate()
    
    def _update_estimate(self):
        """Update the level estimate based on accumulated scores"""
        total = sum(self.level_scores.values())
        if total == 0:
            # No signals yet, stay at default
            self.current_estimate = 3.0
            self.confidence = 0.0
            return
        
        # Weighted average
        weighted_sum = sum(level * score for level, score in self.level_scores.items())
        raw_estimate = weighted_sum / total
        
        # Apply correctness adjustment
        if self.correctness_track:
            accuracy = sum(self.correctness_track) / len(self.correctness_track)
            # High accuracy pushes up, low accuracy pushes down
            if accuracy >= 0.8:
                raw_estimate = min(5.0, raw_estimate + 0.5)
            elif accuracy <= 0.3:
                raw_estimate = max(1.0, raw_estimate - 0.5)
        
        self.current_estimate = max(1.0, min(5.0, raw_estimate))
        
        # Confidence based on total evidence and turns
        evidence_confidence = min(0.9, total * 0.08)
        turn_confidence = min(0.5, self.turns_analyzed * 0.15)
        self.confidence = min(0.95, evidence_confidence + turn_confidence)
    
    def get_estimate(self) -> Tuple[float, float]:
        """Get current level estimate and confidence"""
        return self.current_estimate, self.confidence
    
    def get_predicted_level(self) -> int:
        """Get final integer prediction"""
        # Round to nearest integer
        return round(self.current_estimate)


class HybridLevelDetector:
    """Combines rule-based and LLM analysis"""
    
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
        """Get level estimate, optionally using LLM for better accuracy"""
        rule_level, rule_conf = self.rule_detector.get_estimate()
        
        if not use_llm or self.llm_client is None:
            return rule_level, rule_conf
        
        # Use LLM for more accurate analysis (but only after turn 2 to have enough context)
        if len(self.rule_detector.conversation_history) < 4:
            return rule_level, rule_conf
        
        try:
            llm_result = self.llm_client.analyze_level(
                self.rule_detector.conversation_history,
                self.topic
            )
            llm_level = llm_result.get("level", 3.0)
            llm_conf = llm_result.get("confidence", 0.5)
            
            # Store LLM estimate for trend analysis
            self.llm_estimates.append(llm_level)
            
            # Combine: weight LLM higher as we get more data
            turns = len(self.rule_detector.conversation_history) // 2
            llm_weight = min(0.7, 0.4 + (turns * 0.1))  # 0.4 at turn 1, up to 0.7
            rule_weight = 1.0 - llm_weight
            
            combined_level = (llm_level * llm_weight) + (rule_level * rule_weight)
            combined_conf = max(rule_conf, llm_conf)
            
            # Clamp to valid range
            combined_level = max(1.0, min(5.0, combined_level))
            
            return combined_level, combined_conf
        
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return rule_level, rule_conf
    
    def get_predicted_level(self, use_llm: bool = True) -> int:
        """Get final integer prediction with consistency check"""
        level, conf = self.get_estimate(use_llm)
        
        # If we have multiple LLM estimates, check for consistency
        if len(self.llm_estimates) >= 2:
            recent_estimates = self.llm_estimates[-2:]
            # If estimates are very different, trust the latest more
            if abs(recent_estimates[0] - recent_estimates[1]) > 1.5:
                level = recent_estimates[-1]  # Use most recent
        
        # Round to nearest integer
        predicted = round(level)
        
        # Bounds check
        return max(1, min(5, predicted))
