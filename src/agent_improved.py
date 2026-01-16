"""Enhanced AI Tutoring Agent - OPTIMIZED v2.2"""

import time
from typing import Dict, List, Optional

from api_client import KnowunityAPI
from level_inference_improved import HybridLevelDetector
from adaptive_tutor_improved import TutorGenerator
from llm_client_improved import LLMClient
import config

class TutoringAgent:
    """Main agent that orchestrates tutoring sessions"""
    
    def __init__(self, use_llm: bool = True, event_callback=None):
        self.api = KnowunityAPI()
        self.llm = LLMClient() if use_llm else None
        self.detector = HybridLevelDetector(self.llm)
        self.generator = TutorGenerator(self.llm)
        self.predicted_level = 3
        self.event_callback = event_callback
        self.running = False
        self.stop_requested = False
    
    def _emit_event(self, event_type: str, data: dict):
        """Helper to emit events if callback is set"""
        if self.event_callback:
            self.event_callback({"type": event_type, "data": data})
    
    def run_session(self, student_id: str, topic_id: str, topic_name: str, subject_name: str, verbose: bool = True) -> int:
        if self.stop_requested:
            return self.predicted_level
            
        self.detector = HybridLevelDetector(self.llm)
        self.detector.set_topic(topic_name)
        self.generator = TutorGenerator(self.llm)
        self.conversation_history = []
        
        self._emit_event("session_start", {"topic": topic_name, "subject": subject_name})
        
        start_result = self.api.start_conversation(student_id, topic_id)
        conversation_id = start_result["conversation_id"]
        max_turns = start_result["max_turns"]
        
        if verbose:
            print(f"\n{'='*60}\nSESSION: {topic_name}\n{'='*60}")
        
        tutor_msg = self.generator.get_opening(topic_name, subject_name)
        level_estimates = []
        turn_number = 0
        
        while turn_number < max_turns:
            if self.stop_requested:
                break
                
            result = self.api.send_message(conversation_id, tutor_msg)
            student_response = result["student_response"]
            turn_number = result["turn_number"]
            
            self._emit_event("turn", {
                "turn_number": turn_number,
                "tutor_message": tutor_msg,
                "student_response": student_response
            })
            
            if verbose:
                print(f"\n[Turn {turn_number}]\nTUTOR: {tutor_msg}\nSTUDENT: {student_response}")
            
            self.conversation_history.append({"role": "tutor", "content": tutor_msg})
            self.conversation_history.append({"role": "student", "content": student_response})
            self.detector.detector = self.detector.add_exchange(tutor_msg, student_response)
            
            level_est, confidence = self.detector.get_estimate(use_llm=self.llm is not None)
            level_estimates.append(level_est)
            
            # Prompt uses standard rounding
            self.predicted_level = int(level_est + 0.5)
            
            self._emit_event("level_estimate", {
                "estimate": level_est,
                "confidence": confidence,
                "predicted_level": self.predicted_level
            })
            
            if verbose:
                print(f"   [Estimate: {level_est:.2f}]")
            
            if result.get("is_complete", False): break
                
            tutor_msg = self.generator.generate_response(
                self.conversation_history, self.predicted_level, topic_name, turn_number + 1, student_response
            )
            time.sleep(0.3)
        
        # --- FINAL PREDICTION LOGIC ---
        final_raw, _ = self.detector.get_estimate(use_llm=self.llm is not None)
        
        # Aggressive clamping for final submission
        if final_raw < 2.0:  # Any 1.x becomes 1
            self.predicted_level = 1
        elif final_raw > 4.0: # Any 4.x becomes 5 (if high enough, but let's say >4.2)
            self.predicted_level = 5
        else:
            self.predicted_level = int(final_raw + 0.5)
            
        self.predicted_level = max(1, min(5, self.predicted_level))
        
        self._emit_event("session_complete", {
            "topic": topic_name,
            "predicted_level": self.predicted_level,
            "raw_estimate": final_raw
        })
        
        if verbose:
            print(f"\nFINAL PREDICTION: Level {self.predicted_level} (Raw: {final_raw:.2f})")
            
        return self.predicted_level
    
    def run_all_sessions(self, set_type: str = "mini_dev", verbose: bool = True) -> List[Dict]:
        self.running = True
        self.stop_requested = False
        self._emit_event("start", {"set_type": set_type})
        
        students = self.api.get_students(set_type)
        predictions = []
        
        for student in students:
            if self.stop_requested:
                break
                
            topics = self.api.get_student_topics(student["id"])
            for topic in topics:
                if self.stop_requested:
                    break
                    
                pred = self.run_session(student["id"], topic["id"], topic["name"], topic["subject_name"], verbose)
                predictions.append({
                    "student_id": student["id"],
                    "topic_id": topic["id"],
                    "predicted_level": float(pred)
                })
                time.sleep(1) # Pause between sessions
        
        self.running = False
        self._emit_event("complete", {"predictions": predictions})
        return predictions

    def submit_and_evaluate(self, predictions: List[Dict], set_type: str = "mini_dev") -> Dict:
        print(f"\n{'='*60}\n📤 SUBMITTING PREDICTIONS\n{'='*60}")
        mse_result = self.api.submit_predictions(predictions, set_type)
        print(f"📊 MSE Score: {mse_result.get('mse_score')}")
        
        print("\n⏳ Waiting 5 seconds before tutoring evaluation to prevent 500 error...")
        time.sleep(5)
        
        tutoring_result = self.api.evaluate_tutoring(set_type)
        print(f"📊 Tutoring Score: {tutoring_result.get('score', 0)}/5.0")
        
        return {"mse": mse_result, "tutoring": tutoring_result}

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", default="mini_dev")
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args()
    
    agent = TutoringAgent(use_llm=not args.no_llm)
    preds = agent.run_all_sessions(args.set)
    agent.submit_and_evaluate(preds, args.set)

if __name__ == "__main__":
    main()