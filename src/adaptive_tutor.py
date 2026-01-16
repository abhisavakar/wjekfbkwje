"""Generate tutoring responses based on student level"""

from typing import Optional
from prompts import get_opening_message

class TutorGenerator:
    """Generates appropriate tutoring messages"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    def get_opening(self, topic_name: str, subject_name: str) -> str:
        """Get opening message for a topic"""
        return get_opening_message(topic_name, subject_name)
    
    def generate_response(
        self,
        conversation_history: list,
        student_level: int,
        topic: str,
        turn_number: int,
        last_student_response: str
    ) -> str:
        """Generate next tutor message"""
        
        # Determine phase
        if turn_number <= 3:
            phase = "assess"
        elif turn_number <= 8:
            phase = "tutor"
        else:
            phase = "close"
        
        # Use LLM if available
        if self.llm_client:
            return self.llm_client.generate_tutor_message(
                conversation_history,
                student_level,
                topic,
                turn_number,
                phase
            )
        
        # Fallback to templates
        return self._template_response(
            student_level, phase, topic, last_student_response
        )
    
    def _template_response(
        self, 
        level: int, 
        phase: str, 
        topic: str,
        last_response: str
    ) -> str:
        """Fallback template-based responses"""
        
        if phase == "assess":
            if level <= 2:
                return f"No worries! Let's break this down. What's the simplest thing you know about {topic}?"
            else:
                return f"Good thinking! Can you explain WHY that works?"
        
        elif phase == "tutor":
            templates = {
                1: f"Great effort! Let me explain this in a simpler way. Think of {topic} like this...",
                2: f"You're on the right track! Let me show you step by step...",
                3: f"Correct! Now let's try applying that to a new problem...",
                4: f"Exactly right! Here's a challenge: what happens if we change...?",
                5: f"Excellent analysis! What connections do you see to other concepts?"
            }
            return templates.get(level, templates[3])
        
        elif phase == "close":
            templates = {
                1: f"Great work today! You made real progress with {topic}. Keep practicing the basics and you'll get even stronger! 💪",
                2: f"Nice job! You're getting the hang of {topic}. Keep practicing those steps! 🌟",
                3: f"Good session! You have a solid grasp of {topic}. Keep building on it!",
                4: f"Excellent work! You really understand {topic} well. Keep challenging yourself! 🎉",
                5: f"Impressive session! Your understanding of {topic} is advanced. Keep exploring! 🏆"
            }
            return templates.get(level, templates[3])
        
        return "Let's continue learning!"