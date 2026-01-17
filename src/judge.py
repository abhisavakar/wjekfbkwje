"""External Judge: Verifies Quality Before Sending"""

from prompts_improved import get_judge_prompt

class QualityJudge:
    def __init__(self, llm_client):
        self.llm = llm_client

    def verify(self, draft_response: str, topic: str, level: int, last_student_msg: str) -> str:
        """
        Evaluates the draft response. 
        Returns the draft if it passes, or a rewritten version if it fails.
        """
        # We skip judging for very short messages to save latency
        if len(draft_response.split()) < 5:
            return draft_response

        prompt = get_judge_prompt(topic, level, last_student_msg)
        
        try:
            critique = self.llm.chat(
                system_prompt=prompt, 
                user_message=f"Candidate Response: \"{draft_response}\"", 
                max_tokens=200,
                temperature=0.0  # Strict judgment
            )
            
            # Check for PASS
            if critique.strip().startswith("PASS"):
                return draft_response
            
            # Check for FAIL and extraction
            print(f"👨‍⚖️ JUDGE INTERVENTION: {critique[:60]}...")
            
            if "BETTER:" in critique:
                return critique.split("BETTER:")[-1].strip()
            if "Response:" in critique:
                return critique.split("Response:")[-1].strip()
            
            # If we can't parse the better response, return draft to be safe
            return draft_response
            
        except Exception as e:
            print(f"Judge Error: {e}")
            return draft_response