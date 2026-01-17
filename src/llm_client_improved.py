"""LLM Client v3: Optimized for Quality"""

import openai
import config
import json
import re

class LLMClientV3:
    """Handles all LLM interactions with optimized prompts"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = "gpt-4o"  # Fast and high quality
    
    def chat(self, system_prompt: str, user_message: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        """Send a message to OpenAI and get response"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            raise
    
    def analyze_level(self, conversation_history: list, topic: str, turn_number: int) -> dict:
        """Analyze conversation to determine student level"""
        
        from prompts_improved import LEVEL_ANALYSIS_PROMPT
        
        # Format conversation
        history_text = ""
        for msg in conversation_history:
            role = "TUTOR" if msg['role'] == 'tutor' else "STUDENT"
            history_text += f"{role}: {msg['content']}\n"
        
        user_msg = f"""Topic: {topic}
Turn Number: {turn_number}

Conversation:
{history_text}

Analyze the STUDENT's responses carefully. What level (1.0-5.0) are they at?

Remember:
- Level 3 = Correct answers, knows formulas
- Level 5 = Advanced terminology, deep questions, cross-domain connections
- Don't overrate! Most students are Level 2-4.

Return ONLY valid JSON:"""
        
        try:
            response = self.chat(
                LEVEL_ANALYSIS_PROMPT, 
                user_msg, 
                max_tokens=400,
                temperature=0.3  # Lower temp for more consistent analysis
            )
            
            # Extract JSON from response
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # Validate and clamp
                result["level"] = max(1.0, min(5.0, float(result.get("level", 3.0))))
                result["confidence"] = max(0.0, min(1.0, float(result.get("confidence", 0.5))))
                
                # Print reasoning for debugging
                print(f"  📊 LLM Analysis: Level {result['level']:.1f} ({result['confidence']:.0%}) - {result.get('reasoning', '')[:80]}")
                
                return result
            else:
                print("  ⚠️  No JSON found in LLM response")
                return {"level": 3.0, "confidence": 0.5, "reasoning": "Parse error"}
                
        except json.JSONDecodeError as e:
            print(f"  ⚠️  JSON parse error: {e}")
            return {"level": 3.0, "confidence": 0.5, "reasoning": "JSON parse error"}
        except Exception as e:
            print(f"  ⚠️  LLM analysis error: {e}")
            return {"level": 3.0, "confidence": 0.3, "reasoning": "API error"}