"""Tutoring v5.0: The Socratic Engine"""

from typing import Dict, List, Optional
from personality import PersonalityDetector
from judge import QualityJudge
from prompts_improved import (
    get_adaptive_tutoring_prompt,
    get_assessment_prompt,
    get_closing_prompt
)

class TutorGeneratorV3:
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.tracker = PersonalityDetector()
        self.judge = QualityJudge(llm_client)
        self.first_student_response = None
        self.concepts_taught = []
    
    def get_opening(self, topic_name: str, subject_name: str) -> str:
        return f"Hi! 👋 Today we're working on {topic_name}. To start, what's the first thing that comes to mind when you hear that topic?"
    
    def generate_response(
        self,
        conversation_history: List[Dict],
        student_level: int,
        topic: str,
        turn_number: int,
        phase: str,
        last_student_response: str,
        current_confidence: float,
        student_name: str = "Student"
    ) -> str:
        
        # 1. Update State
        self.tracker.update(last_student_response)
        if not self.first_student_response:
            self.first_student_response = last_student_response
            
        # 2. Generate
        if phase == "assess":
            return self._generate_assessment(conversation_history, student_level, topic, last_student_response)
        elif phase == "close":
            return self._generate_closing(student_level, topic, last_student_response, student_name)
        else:
            return self._generate_tutoring(
                conversation_history, student_level, topic, 
                last_student_response, student_name
            )

    def _generate_tutoring(self, history, level, topic, last_response, student_name) -> str:
        # A. Select Persona
        # Force "Professor" for Level 5, "Cheerleader" for Level 1-2
        if level >= 5:
            style_key = "professor"
        elif level <= 2:
            style_key = "cheerleader"
        else:
            style_key = "socratic"
            
        student_state = self.tracker.get_state()
        student_state['last_words'] = last_response[:30] + "..."
        
        # B. Draft
        system_prompt = get_adaptive_tutoring_prompt(level, topic, style_key, student_state, student_name)
        formatted_history = self._format_history(history)
        
        user_prompt = f"""
        History:
        {formatted_history}
        
        Student ({student_name}) said: "{last_response}"
        
        Generate response:
        """
        
        draft = self.llm_client.chat(system_prompt, user_prompt, max_tokens=350)
        
        # C. Verify (The Judge enforces the "No Emoji" rule for L5)
        return self.judge.verify(draft, topic, level, last_response)

    def _generate_assessment(self, history, level, topic, last_response) -> str:
        system = get_assessment_prompt(level)
        return self.llm_client.chat(system, f"Topic: {topic}\nStudent said: {last_response}", max_tokens=150)

    def _generate_closing(self, level, topic, last_response, student_name) -> str:
        first = self.first_student_response or "your first message"
        system = get_closing_prompt(level, first, self.concepts_taught, student_name)
        return self.llm_client.chat(system, f"Topic: {topic}\nLast words: {last_response}", max_tokens=150)

    def _format_history(self, history: List[Dict]) -> str:
        return "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in history[-6:]])