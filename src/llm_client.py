"""OpenAI API Client - GPT-5.2 with tuned temperature"""

import openai
import json
import re
import config

class LLMClient:
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = "gpt-5.2"  # Latest model
    
    def chat(self, system_prompt: str, user_message: str, temperature: float = 0.4) -> str:
        """Send a message to OpenAI and get response"""
        response = self.client.chat.completions.create(
            model=self.model,
            max_completion_tokens=1024,
            temperature=temperature,  # Lower = more consistent, natural
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content
    
    def analyze_level(self, conversation_history: list, topic: str) -> dict:
        """Analyze conversation to determine student level"""
        from prompts import LEVEL_ANALYSIS_PROMPT
        
        history_text = "\n".join([
            f"{'TUTOR' if m['role']=='tutor' else 'STUDENT'}: {m['content']}"
            for m in conversation_history
        ])
        
        user_msg = f"""Topic: {topic}

Conversation:
{history_text}

Analyze the student's understanding level (1-5).
Return ONLY JSON: {{"level": X, "confidence": Y, "reasoning": "brief"}}"""
        
        response = self.chat(LEVEL_ANALYSIS_PROMPT, user_msg, temperature=0.2)
        
        # Parse JSON from response
        try:
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                result["level"] = float(result.get("level", 3.0))
                result["confidence"] = float(result.get("confidence", 0.5))
                return result
        except (json.JSONDecodeError, ValueError) as e:
            print(f"JSON parse error: {e}")
        
        return {"level": 3.0, "confidence": 0.5, "reasoning": "Could not parse"}
    
    def generate_tutor_message(
        self, 
        conversation_history: list,
        student_level: int,
        topic: str,
        turn_number: int,
        phase: str
    ) -> str:
        """Generate a tutoring message"""
        from prompts import TUTOR_SYSTEM_PROMPT, get_phase_instructions
        
        history_text = "\n".join([
            f"{'TUTOR' if m['role']=='tutor' else 'STUDENT'}: {m['content']}"
            for m in conversation_history
        ])
        
        # Detect student's language from their messages
        student_messages = [m['content'] for m in conversation_history if m['role'] == 'student']
        language_hint = ""
        if student_messages:
            last_student_msg = student_messages[-1].lower()
            # Simple detection: check for common German words
            german_indicators = ['ich', 'und', 'das', 'ist', 'nicht', 'für', 'auch', 'aber', 'wenn', 'kann']
            german_count = sum(1 for word in german_indicators if word in last_student_msg)
            if german_count >= 2:
                language_hint = "The student is writing in GERMAN. Respond in German."
            else:
                language_hint = "The student is writing in ENGLISH. Respond in English only."
        
        phase_instructions = get_phase_instructions(phase, student_level)
        
        # Response length guidance based on level
        length_hint = ""
        if student_level <= 2:
            length_hint = "Keep your response SHORT (3-5 sentences max). Simple and clear."
        elif student_level == 5:
            length_hint = "Keep your response CONCISE. Ask questions, don't lecture. No walls of equations."
        
        user_msg = f"""Topic: {topic}
Student Level: {student_level}
Turn: {turn_number}/10
Phase: {phase}

{language_hint}
{length_hint}

Conversation so far:
{history_text}

{phase_instructions}

Generate the next tutor message. Be warm, natural, and helpful.
Ask ONE question at a time (not multiple).
Return ONLY the message text."""
        
        # Use slightly higher temperature for more natural responses
        return self.chat(TUTOR_SYSTEM_PROMPT, user_msg, temperature=0.5)
