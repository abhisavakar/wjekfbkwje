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
        last_student_response: str
    ) -> str:
        """Generate next tutor message with context awareness"""
        
        # Track student statement
        self.session_context["student_statements"].append(last_student_response)
        
        # Determine phase
        if turn_number <= 3:
            phase = "assess"
        elif turn_number <= 8:
            phase = "tutor"
        else:
            phase = "close"
        
        # Use LLM if available (HIGHLY RECOMMENDED for quality)
        if self.llm_client:
            try:
                response = self.llm_client.generate_tutor_message(
                    conversation_history,
                    student_level,
                    topic,
                    turn_number,
                    phase,
                    self.session_context
                )
                self.session_context["tutor_statements"].append(response)
                return response
            except Exception as e:
                print(f"LLM generation failed: {e}, falling back to templates")
                # Fall through to templates
        
        # Fallback to enhanced templates
        response = self._enhanced_template_response(
            student_level, phase, topic, last_student_response, turn_number
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
        """Enhanced template-based responses with better quality"""
        
        if phase == "assess":
            # Assessment phase - diagnostic questions
            if turn_number == 2:
                # Based on first response, adjust difficulty
                if "don't know" in last_response.lower() or len(last_response.split()) < 5:
                    return f"No worries at all! Let's start with the basics. What's the simplest thing you can tell me about {topic}?"
                elif "because" in last_response.lower() or len(last_response.split()) > 20:
                    return f"Good explanation! Now tell me: WHY does {topic} work that way?"
                else:
                    return f"Okay! Can you give me a specific example of {topic}?"
            
            elif turn_number == 3:
                # Final diagnostic
                templates = {
                    1: f"I see. Let me ask one more thing: do you know what the most basic part of {topic} is called?",
                    2: f"Alright. Can you try walking me through how you'd approach a simple problem with {topic}?",
                    3: f"Got it! Can you solve this for me: [standard {topic} problem]?",
                    4: f"Interesting! What happens if we change something about {topic}?",
                    5: f"Great thinking! How does {topic} connect to other concepts you know?"
                }
                return templates.get(level, templates[3])
        
        elif phase == "tutor":
            # Tutoring phase - teach at their level
            templates = {
                1: f"Let me explain {topic} in a really simple way. Think of it like this: imagine you have some cookies... [explain with concrete example]. Does that make sense? 🌟",
                
                2: f"You're on the right track! Let me show you step by step how {topic} works. First, [step 1]. Then, [step 2]. Now you try: [simple practice problem]",
                
                3: f"Exactly! You've got the main idea of {topic}. Now let's apply it: [practice problem with moderate difficulty]. Give it a shot!",
                
                4: f"Perfect! You really understand {topic}. Here's a challenge for you: what happens when [edge case or variation]? Think about it and let me know!",
                
                5: f"Excellent analysis! That shows deep understanding. Here's something interesting to explore: how does {topic} relate to [advanced concept]? What's your take on it?"
            }
            return templates.get(level, templates[3])
        
        elif phase == "close":
            # Closing phase - personalized summary
            # Try to reference something specific from the session
            first_response = self.session_context["student_statements"][0] if self.session_context["student_statements"] else "basics"
            
            templates = {
                1: f"You did great today! When we started, you {first_response[:30]}... and now you understand the basics of {topic}! That's real progress. Keep practicing and you'll get even better! 💪",
                
                2: f"Nice work! You've come a long way with {topic} today. You learned the key steps and can work through problems with some guidance. Keep practicing those techniques! 🌟",
                
                3: f"Great session! You have a solid grasp of {topic} now. You know the concepts, can apply them, and gave some good examples. Keep building on this foundation! 📚",
                
                4: f"Excellent work! You really understand {topic} well - not just the 'what' but also the 'why'. Your question about [edge case] showed strong thinking. Keep challenging yourself! 🎉",
                
                5: f"Impressive session! Your understanding of {topic} goes beyond the standard material. The way you connected it to [other concept] shows advanced thinking. Keep exploring and questioning! 🏆"
            }
            return templates.get(level, templates[3])
        
        return "Let's continue learning about this topic together!"
