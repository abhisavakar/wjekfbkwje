"""External Judge: Gatekeeper & Self-Evaluator"""

from prompts_improved import get_judge_prompt, get_self_eval_prompt

class QualityJudge:
    def __init__(self, llm_client):
        self.llm = llm_client

    def verify(self, draft_response: str, topic: str, level: int, last_student_msg: str) -> str:
        """Gatekeeper: Rewrites bad responses"""
        if len(draft_response.split()) < 8: return draft_response

        prompt = get_judge_prompt(topic, level, last_student_msg)
        
        try:
            critique = self.llm.chat(
                system_prompt=prompt, 
                user_message=f"Candidate Response: \"{draft_response}\"", 
                max_tokens=300,
                temperature=0.0
            )
            
            if critique.strip().startswith("PASS"):
                return draft_response
            
            # Robust Parsing for "FAIL"
            if "BETTER:" in critique:
                return critique.split("BETTER:")[-1].strip()
            if "Response:" in critique:
                return critique.split("Response:")[-1].strip()
            
            return draft_response
            
        except Exception as e:
            print(f"Judge Error: {e}")
            return draft_response

    def grade_response(self, response: str, topic: str, level: int, student_name: str, last_student_msg: str) -> str:
        """Self-Evaluator: Returns a score and critique string"""
        prompt = get_self_eval_prompt(topic, level, student_name, last_student_msg)
        
        try:
            # Quick check (Max 100 tokens to save cost/time)
            eval_result = self.llm.chat(
                system_prompt=prompt,
                user_message=f"Tutor Response: \"{response}\"",
                max_tokens=100,
                temperature=0.0
            )
            return eval_result.replace("\n", " | ")
        except Exception:
            return "SCORE: N/A | Error"