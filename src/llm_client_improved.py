"""Enhanced OpenAI API Client for higher quality responses"""

import openai
import config
import json
import re

class LLMClient:
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = "gpt-4o"  # Fast and capable
    
    def chat(self, system_prompt: str, user_message: str, max_tokens: int = 1024) -> str:
        """Send a message to OpenAI and get response"""
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=0.7,  # Slightly creative but consistent
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content
    
    def analyze_level(self, conversation_history: list, topic: str) -> dict:
        """Analyze conversation to determine student level with high accuracy"""
        from prompts_improved import LEVEL_ANALYSIS_PROMPT
        
        # Format conversation with clear structure
        history_text = ""
        for i, msg in enumerate(conversation_history):
            role = "TUTOR" if msg['role'] == 'tutor' else "STUDENT"
            history_text += f"{role}: {msg['content']}\n"
        
        user_msg = f"""Topic: {topic}

Full Conversation:
{history_text}

Analyze this student's understanding level (1-5) based on:
1. Correctness of their answers
2. Depth of understanding shown
3. Confidence/uncertainty in language
4. Ability to explain concepts
5. Questions they ask

Return ONLY a valid JSON object:
{{
  "level": <float between 1.0 and 5.0>,
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<specific evidence from conversation>"
}}"""
        
        try:
            response = self.chat(LEVEL_ANALYSIS_PROMPT, user_msg, max_tokens=500)
            
            # Parse JSON from response
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                # Validate and clamp values
                result["level"] = max(1.0, min(5.0, float(result.get("level", 3.0))))
                result["confidence"] = max(0.0, min(1.0, float(result.get("confidence", 0.5))))
                return result
        except Exception as e:
            print(f"Level analysis parse error: {e}")
        
        return {"level": 3.0, "confidence": 0.5, "reasoning": "Parse error, defaulting to level 3"}
    
    def generate_tutor_message(
        self, 
        conversation_history: list,
        student_level: int,
        topic: str,
        turn_number: int,
        phase: str,
        session_context: dict = None
    ) -> str:
        """Generate high-quality tutoring message appropriate for the student's level"""
        from prompts_improved import TUTOR_SYSTEM_PROMPT, get_phase_instructions
        
        # Format conversation
        history_text = ""
        for msg in conversation_history:
            role = "TUTOR" if msg['role'] == 'tutor' else "STUDENT"
            history_text += f"{role}: {msg['content']}\n"
        
        # Get last student response for context
        last_student = ""
        for msg in reversed(conversation_history):
            if msg['role'] == 'student':
                last_student = msg['content']
                break
        
        # Get phase instructions
        phase_instructions = get_phase_instructions(phase, student_level)
        
        # Build context-aware prompt
        context_note = ""
        if session_context and session_context.get("student_statements"):
            first_statement = session_context["student_statements"][0]
            context_note = f"\nIMPORTANT: The student initially said: '{first_statement[:100]}...' - reference this in your closing if it's relevant."
        
        user_msg = f"""Topic: {topic}
Student Level: {student_level} (1=struggling, 2=below grade, 3=at grade, 4=above grade, 5=advanced)
Current Turn: {turn_number}/10
Phase: {phase}

Full Conversation:
{history_text}

Last Student Response: "{last_student}"

{phase_instructions}
{context_note}

Generate the next tutor message. Remember:
- Match the difficulty to Level {student_level}
- Be warm, encouraging, and specific
- Reference what the student actually said
- {"Ask diagnostic questions" if phase == "assess" else "Teach appropriately" if phase == "tutor" else "End with specific, positive summary"}
- Keep it natural and conversational
- {"2-3 sentences" if phase == "close" else "1-3 sentences" if phase == "assess" else "2-4 sentences"}

Return ONLY the message text (no labels, no metadata):"""
        
        try:
            response = self.chat(TUTOR_SYSTEM_PROMPT, user_msg, max_tokens=300)
            # Clean up any formatting artifacts
            response = response.strip()
            # Remove any "TUTOR:" prefix if model added it
            response = re.sub(r'^(TUTOR|Tutor|Assistant):\s*', '', response, flags=re.IGNORECASE)
            return response
        except Exception as e:
            print(f"Tutor message generation error: {e}")
            # Fallback
            if phase == "close":
                return f"Great work today! You've made real progress with {topic}. Keep learning! 🌟"
            else:
                return f"Can you tell me more about your thinking on {topic}?"
