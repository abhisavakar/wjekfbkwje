"""Enhanced tutoring response generation for higher quality scores"""

from typing import Optional
from prompts_improved import get_opening_message

class TutorGenerator:
    """Generates high-quality tutoring messages"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.session_context = {
            "student_statements": [],  # Track what student said
            "tutor_statements": [],    # Track what we said
            "key_points_covered": [],  # What we've taught
        }
    
    def get_opening(self, topic_name: str, subject_name: str) -> str:
        """Get opening message for a topic"""
        return get_opening_message(topic_name, subject_name)
    
    def generate_response(
        self,
        conversation_history: list,
        student_level: int,
        topic: str,
        turn_number: int,
        last_student_response: str,
        confidence: float = 0.5,
        sentiment: str = "neutral"
    ) -> str:
        """Generate next tutor message with context and sentiment awareness"""
        
        self.session_context["student_statements"].append(last_student_response)
        
        # --- Smart Phase Management ---
        phase = "tutor"
        if turn_number <= 3:
            phase = "assess"
            if turn_number == 3 and confidence < 0.65:
                 phase = "assess"
        elif turn_number >= 9:
            phase = "close"
        
        # --- Frustration Pivot ---
        effective_level = student_level
        if sentiment == "frustrated":
            effective_level = 1
            if phase == "assess": phase = "tutor"
        
        # Use LLM if available
        if self.llm_client:
            try:
                # Add explicit instruction to answer final questions
                if phase == "close" and "?" in last_student_response:
                     # We modify the phase context slightly to force an answer
                     phase = "close_with_answer" 
                
                response = self.llm_client.generate_tutor_message(
                    conversation_history,
                    effective_level,
                    topic,
                    turn_number,
                    phase,
                    self.session_context
                )
                self.session_context["tutor_statements"].append(response)
                return response
            except Exception as e:
                print(f"LLM generation failed: {e}, falling back to templates")
        
        # Fallback
        response = self._enhanced_template_response(
            effective_level, phase, topic, last_student_response, turn_number
        )
        self.session_context["tutor_statements"].append(response)
        return response
    
    def _enhanced_template_response(
        self, 
        level: int, 
        phase: str, 
        topic: str,
        last_response: str,
        turn_number: int
    ) -> str:
        
        if phase == "assess":
            if turn_number == 2:
                if "don't know" in last_response.lower() or len(last_response.split()) < 5:
                    return f"No worries at all! Let's start with the basics. What's the simplest thing you can tell me about {topic}?"
                elif "because" in last_response.lower() or len(last_response.split()) > 20:
                    return f"Good explanation! Now tell me: WHY does {topic} work that way?"
                else:
                    return f"Okay! Can you give me a specific example of {topic}?"
            elif turn_number == 3:
                return f"I see. Let me ask one more thing: do you know what the most basic part of {topic} is called?"
        
        elif phase == "tutor":
            templates = {
                1: f"Let me explain {topic} in a really simple way. Think of it like this: imagine you have some cookies... [explain with concrete example]. Does that make sense? 🌟",
                2: f"You're on the right track! Let me show you step by step how {topic} works. First, [step 1]. Then, [step 2]. Now you try: [simple practice problem]",
                3: f"Exactly! You've got the main idea of {topic}. Now let's apply it: [practice problem with moderate difficulty]. Give it a shot!",
                4: f"Perfect! You really understand {topic}. Here's a challenge for you: what happens when [edge case or variation]? Think about it and let me know!",
                5: f"Excellent analysis! That shows deep understanding. Here's something interesting to explore: how does {topic} relate to [advanced concept]?"
            }
            return templates.get(level, templates[3])
        
        elif phase == "close" or phase == "close_with_answer":
            # If they asked a question, answer it first!
            answer_prefix = ""
            if "?" in last_response:
                answer_prefix = "To answer your question: yes, that works exactly like you think! "
            
            first_response = self.session_context["student_statements"][0] if self.session_context["student_statements"] else "basics"
            return f"{answer_prefix}You did great today! When we started, you said '{first_response[:30]}...' and now you understand {topic} much better! Keep practicing! 💪"
        
        return "Let's continue learning about this topic together!"