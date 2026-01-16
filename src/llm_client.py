"""OpenAI API Client for intelligent responses"""

import openai
import config

class LLMClient:
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = "gpt-4o"  # Fast and capable, can also use "gpt-4-turbo" or "gpt-4o-mini"
    
    def chat(self, system_prompt: str, user_message: str) -> str:
        """Send a message to OpenAI and get response"""
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1024,
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
        
        user_msg = f"""
Topic: {topic}

Conversation:
{history_text}

Analyze the student's understanding level (1-5) based on their responses.
Return ONLY a JSON object with:
- "level": (float between 1.0 and 5.0)
- "confidence": (float between 0.0 and 1.0)
- "reasoning": (brief explanation)
"""
        
        response = self.chat(LEVEL_ANALYSIS_PROMPT, user_msg)
        
        # Parse JSON from response
        import json
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"level": 3.0, "confidence": 0.5, "reasoning": "Could not parse"}
    
    def generate_tutor_message(
        self, 
        conversation_history: list,
        student_level: int,
        topic: str,
        turn_number: int,
        phase: str  # "assess", "tutor", or "close"
    ) -> str:
        """Generate a tutoring message appropriate for the student's level"""
        from prompts import TUTOR_SYSTEM_PROMPT, get_phase_instructions
        
        history_text = "\n".join([
            f"{'TUTOR' if m['role']=='tutor' else 'STUDENT'}: {m['content']}"
            for m in conversation_history
        ])
        
        phase_instructions = get_phase_instructions(phase, student_level)
        
        user_msg = f"""
Topic: {topic}
Student Level: {student_level}
Turn: {turn_number}/10
Phase: {phase}

Conversation so far:
{history_text}

{phase_instructions}

Generate the next tutor message. Be natural, conversational, and appropriate for Level {student_level}.
Return ONLY the message text, nothing else.
"""
        
        return self.chat(TUTOR_SYSTEM_PROMPT, user_msg)
