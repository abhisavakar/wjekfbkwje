"""Tutoring v3: LLM-Powered with Context Tracking"""

from typing import Optional, Dict, List

class TutorGeneratorV3:
    """Generates high-quality tutoring messages using LLM"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.first_student_response = None
        self.key_concepts_taught = []
        self.student_progress_notes = []
    
    def get_opening(self, topic_name: str, subject_name: str) -> str:
        """Opening message - keep it simple and open-ended"""
        return f"Hi! Today we're working on {topic_name}. To start, can you tell me what you already know about this topic?"
    
    def track_first_response(self, response: str):
        """Store first response for closing reference"""
        if self.first_student_response is None:
            self.first_student_response = response
    
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
        """Generate next tutor message with full LLM"""
        
        # Track first response - get it from conversation history
        if self.first_student_response is None:
            # Find the first student message in history
            for msg in conversation_history:
                if msg["role"] == "student":
                    self.first_student_response = msg["content"]
                    break
        
        # Determine what to do based on phase and confidence
        if phase == "assess":
            return self._generate_assessment_message(
                conversation_history, student_level, topic, 
                turn_number, current_confidence, last_student_response
            )
        elif phase == "tutor":
            return self._generate_tutoring_message(
                conversation_history, student_level, topic,
                turn_number, last_student_response
            )
        else:  # close
            return self._generate_closing_message(
                conversation_history, student_level, topic,
                turn_number
            )
    
    def _generate_assessment_message(
        self, history, level, topic, turn, confidence, last_response
    ) -> str:
        """Generate diagnostic questions"""
        
        from prompts_improved import get_assessment_prompt
        
        # Determine what kind of question to ask
        if turn == 2:
            # Based on first response, probe appropriately
            if confidence < 0.5:
                instruction = "Ask a simpler, more basic question to confirm their level"
            elif level <= 2:
                instruction = "Ask them to define a basic term or concept"
            elif level == 3:
                instruction = "Ask them to solve a standard problem or give an example"
            else:
                instruction = "Ask them WHY something works or to explain the reasoning"
        elif turn == 3:
            # Confirmation question
            if level <= 2:
                instruction = "Ask a very simple recall question"
            elif level == 3:
                instruction = "Give them a standard practice problem"
            else:
                instruction = "Ask about edge cases or connections to other concepts"
        else:  # turn 4
            instruction = "Final diagnostic: ask them to explain their understanding in their own words"
        
        system_prompt = get_assessment_prompt(level)
        user_prompt = f"""Topic: {topic}
Student Level Estimate: {level} (confidence: {confidence:.0%})
Current Turn: {turn}

Conversation so far:
{self._format_history(history)}

Last student response: "{last_response}"

Task: {instruction}

Generate ONLY the tutor's next question (1-2 sentences, keep it natural):"""
        
        try:
            response = self.llm_client.chat(system_prompt, user_prompt, max_tokens=150)
            return self._clean_response(response)
        except Exception as e:
            print(f"Assessment generation failed: {e}")
            return f"Can you tell me more about how you understand {topic}?"
    
    def _generate_tutoring_message(
        self, history, level, topic, turn, last_response
    ) -> str:
        """Generate teaching content - WITH CONFUSION DETECTION"""
        
        from prompts_improved import get_tutoring_prompt
        
        # DETECT CONFUSION SIGNALS
        confusion_words = ["confused", "lost", "brain hurt", "too fast", "don't get", "don't understand", "headache", "makes no sense"]
        is_confused = any(word in last_response.lower() for word in confusion_words)
        
        system_prompt = get_tutoring_prompt(level, topic)
        
        # If student is confused, add SLOW DOWN instruction
        confusion_note = ""
        if is_confused:
            confusion_note = f"""
🚨 CRITICAL: Student just said they're CONFUSED: "{last_response[:100]}"

DO NOT move forward. DO NOT introduce new concepts.
Instead:
1. Acknowledge their confusion
2. Explain the SAME concept in SIMPLER words
3. Give ONE very easy example
4. Ask if THIS makes sense

Example: "Let me explain that differently. x² just means you multiply x by itself. 
So 3² = 3 × 3 = 9. Does that make sense?"
"""
        
        user_prompt = f"""Topic: {topic}
Student Level: {level}
Current Turn: {turn}/10

Full conversation:
{self._format_history(history)}

Last student response: "{last_response}"

{confusion_note}

Your task: Teach ONE specific concept related to {topic}.

REQUIREMENTS:
- Use CONCRETE examples (real numbers, real scenarios)
- Break it into small steps if Level {level} <= 2
- Give them ONE practice question to try
- Reference what they just said
- Be warm and encouraging
- 2-3 sentences + 1 practice question

Concepts already covered: {', '.join(self.key_concepts_taught) if self.key_concepts_taught else 'none yet'}

Generate ONLY the tutor's message:"""
        
        try:
            response = self.llm_client.chat(system_prompt, user_prompt, max_tokens=250)
            
            # Extract what concept we just taught (for tracking)
            self._track_concept(response, topic)
            
            return self._clean_response(response)
        except Exception as e:
            print(f"Tutoring generation failed: {e}")
            # Emergency fallback
            if level <= 2:
                return f"Let me explain {topic} more simply. Can you tell me what part is confusing you?"
            else:
                return f"Great! Let's build on {topic}. Try this problem: [example]"
    
    def _generate_closing_message(
        self, history, level, topic, turn
    ) -> str:
        """Generate personalized closing with progress summary"""
        
        from prompts_improved import get_closing_prompt
        
        # Get ACTUAL first student response
        # If not stored, extract from history
        if self.first_student_response is None or self.first_student_response == "":
            for msg in history:
                if msg["role"] == "student":
                    self.first_student_response = msg["content"]
                    break
        
        first_response = self.first_student_response or "wanted to learn about this topic"
        
        last_student_msg = ""
        for msg in reversed(history):
            if msg["role"] == "student":
                last_student_msg = msg["content"]
                break
        
        # Make first response concise
        first_snippet = first_response[:80] + "..." if len(first_response) > 80 else first_response
        
        system_prompt = get_closing_prompt(level)
        
        user_prompt = f"""Topic: {topic}
Student Level: {level}

ACTUAL FIRST thing student said: "{first_snippet}"

LAST thing student said: "{last_student_msg[:100]}"

Key concepts we covered: {', '.join(self.key_concepts_taught[-3:]) if self.key_concepts_taught else topic}

Your task: Write a closing message that:
1. References their ACTUAL first words (quote a few key words from "{first_snippet}")
2. Shows SPECIFIC progress (what skills/concepts they learned)
3. Ends with encouragement and emoji

CRITICAL: Do NOT use phrases like "the basics" or "didn't know much". Use their ACTUAL WORDS from the first message.

Length: 2-3 sentences maximum.

Generate ONLY the tutor's closing message:"""
        
        try:
            response = self.llm_client.chat(system_prompt, user_prompt, max_tokens=200)
            return self._clean_response(response)
        except Exception as e:
            print(f"Closing generation failed: {e}")
            # Better fallback that uses actual first response
            return f"You started by saying '{first_snippet}' - now you've deepened your understanding of {topic}! Great progress. Keep learning! 🌟"
    
    def _format_history(self, history: List[Dict]) -> str:
        """Format conversation history for LLM"""
        formatted = []
        for msg in history[-10:]:  # Last 10 messages
            role = "TUTOR" if msg["role"] == "tutor" else "STUDENT"
            formatted.append(f"{role}: {msg['content']}")
        return "\n".join(formatted)
    
    def _clean_response(self, response: str) -> str:
        """Clean up LLM response"""
        import re
        response = response.strip()
        # Remove any role labels
        response = re.sub(r'^(TUTOR|Tutor|Assistant|Teacher):\s*', '', response, flags=re.IGNORECASE)
        # Remove quotes if LLM added them
        response = response.strip('"\'')
        return response
    
    def _track_concept(self, message: str, topic: str):
        """Try to extract what concept was just taught"""
        # Simple heuristic: look for key phrases
        message_lower = message.lower()
        
        # Common concept indicators
        if "slope" in message_lower and "slope" not in [c.lower() for c in self.key_concepts_taught]:
            self.key_concepts_taught.append("slope")
        elif "intercept" in message_lower and "intercept" not in [c.lower() for c in self.key_concepts_taught]:
            self.key_concepts_taught.append("intercept")
        elif "quadratic" in message_lower and "quadratic" not in [c.lower() for c in self.key_concepts_taught]:
            self.key_concepts_taught.append("quadratic formula")
        elif "energy" in message_lower and "energy" not in [c.lower() for c in self.key_concepts_taught]:
            self.key_concepts_taught.append("energy conservation")
        
        # Generic fallback
        if not self.key_concepts_taught:
            self.key_concepts_taught.append(topic.split()[0])  # First word of topic
