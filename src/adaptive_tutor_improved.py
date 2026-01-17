"""Tutoring v3.5: Personality-Aware with Judge Loop"""

from typing import Dict, List
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
        current_confidence: float
    ) -> str:
        
        # 1. Update Personality State
        self.tracker.update(last_student_response)
        
        # 2. Track History
        if not self.first_student_response:
            self.first_student_response = last_student_response
            
        # 3. Route by Phase
        if phase == "assess":
            return self._generate_assessment(conversation_history, student_level, topic, last_student_response)
        elif phase == "close":
            return self._generate_closing(student_level, topic, last_student_response)
        else:
            return self._generate_tutoring(conversation_history, student_level, topic, last_student_response)

    def _generate_tutoring(self, history, level, topic, last_response) -> str:
        # A. Select Persona
        style_key = self.tracker.determine_style(level)
        student_state = self.tracker.get_state()
        
        # B. Generate Draft
        system_prompt = get_adaptive_tutoring_prompt(level, topic, style_key, student_state)
        formatted_history = self._format_history(history)
        
        user_prompt = f"""
        History:
        {formatted_history}
        
        Student said: "{last_response}"
        
        Generate response:
        """
        
        draft = self.llm_client.chat(system_prompt, user_prompt, max_tokens=300)
        
        # C. Run Judge (The Quality Gate)
        final_response = self.judge.verify(draft, topic, level, last_response)
        
        # D. Track Concept
        self._track_concepts(final_response)
        
        return final_response

    def _generate_assessment(self, history, level, topic, last_response) -> str:
        # Simple generation for assessment
        system = get_assessment_prompt(level)
        return self.llm_client.chat(system, f"Topic: {topic}\nStudent said: {last_response}", max_tokens=150)

    def _generate_closing(self, level, topic, last_response) -> str:
        first = self.first_student_response or "your first message"
        system = get_closing_prompt(level, first, self.concepts_taught)
        return self.llm_client.chat(system, f"Topic: {topic}\nLast words: {last_response}", max_tokens=150)

    def _format_history(self, history: List[Dict]) -> str:
        return "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in history[-6:]])

    def _track_concepts(self, message: str):
        # Basic keyword tracking to populate the closing message
        words = message.lower().split()
        if "slope" in words and "slope" not in self.concepts_taught: self.concepts_taught.append("slope")
        if "energy" in words and "energy" not in self.concepts_taught: self.concepts_taught.append("energy")
        # Add more keywords as needed