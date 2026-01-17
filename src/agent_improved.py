"""Enhanced AI Tutoring Agent - Web Enabled & Optimized v2.5"""

import time
from typing import Dict, List, Optional, Callable

from api_client import KnowunityAPI
from level_inference_improved import HybridLevelDetector
from adaptive_tutor_improved import TutorGenerator
from llm_client_improved import LLMClient
import config

class TutoringAgent:
    """Main agent that orchestrates tutoring sessions"""
    
    def __init__(self, use_llm: bool = True, event_callback: Optional[Callable] = None):
        self.api = KnowunityAPI()
        self.llm = LLMClient() if use_llm else None
        self.event_callback = event_callback
        self.running = False
        self.stop_requested = False
        self.predicted_level = 3

    def log(self, message: str, type: str = "info"):
        """Send a log event to the frontend"""
        if self.event_callback:
            self.event_callback({
                "type": "log",
                "level": type,
                "message": message,
                "timestamp": time.time()
            })
        print(f"[{type.upper()}] {message}")

    def emit_state(self, conversation_history, estimates, current_level, current_confidence):
        if self.event_callback:
            self.event_callback({
                "type": "state_update",
                "history": conversation_history,
                "estimates": estimates,
                "current_level": current_level,
                "current_confidence": current_confidence
            })

    def run_session(self, student_id: str, topic_id: str, topic_name: str, subject_name: str) -> int:
        self.log(f"Starting session: {topic_name}", "system")
        
        self.detector = HybridLevelDetector(self.llm)
        self.detector.set_topic(topic_name)
        self.generator = TutorGenerator(self.llm)
        self.conversation_history = []
        
        start_result = self.api.start_conversation(student_id, topic_id)
        conversation_id = start_result["conversation_id"]
        max_turns = start_result["max_turns"]
        
        tutor_msg = self.generator.get_opening(topic_name, subject_name)
        turn_number = 0
        estimates_history = []
        
        while turn_number < max_turns and not self.stop_requested:
            # 1. Interact
            result = self.api.send_message(conversation_id, tutor_msg)
            student_response = result["student_response"]
            turn_number = result["turn_number"]
            
            print(f"\n[Turn {turn_number}]")
            print(f"TUTOR: {tutor_msg}")
            print(f"STUDENT: {student_response}")

            # 2. Update State
            self.conversation_history.append({"role": "tutor", "content": tutor_msg})
            self.conversation_history.append({"role": "student", "content": student_response})
            self.detector.add_exchange(tutor_msg, student_response)
            
            # 3. Analyze (Now with Sentiment)
            level_est, confidence, sentiment = self.detector.get_estimate(use_llm=self.llm is not None)
            
            self.predicted_level = int(level_est + 0.5)
            estimates_history.append({"level": level_est, "confidence": confidence})
            
            self.log(f"Turn {turn_number}: Est={level_est:.2f} Conf={confidence:.0%} Sent={sentiment}")
            self.emit_state(self.conversation_history, estimates_history, level_est, confidence)
            
            if result.get("is_complete", False): break
                
            # 4. Generate Response (Now with Confidence & Sentiment)
            tutor_msg = self.generator.generate_response(
                self.conversation_history, 
                self.predicted_level, 
                topic_name, 
                turn_number + 1, 
                student_response,
                confidence=confidence,
                sentiment=sentiment
            )
            time.sleep(0.5)

        # --- FINAL PREDICTION ---
        final_raw, final_conf, _ = self.detector.get_estimate(use_llm=self.llm is not None)
        
        if final_raw < 1.8: final_level = 1
        elif final_raw > 4.2: final_level = 5
        else: final_level = int(final_raw + 0.5)
        
        final_level = max(1, min(5, final_level))
        
        estimates_history.append({"level": float(final_level), "confidence": final_conf})
        self.emit_state(self.conversation_history, estimates_history, float(final_level), final_conf)
        
        self.log(f"Final Prediction: Level {final_level} (Raw: {final_raw:.2f})", "success")
        return final_level

    def run_all_sessions(self, set_type: str = "mini_dev"):
        self.running = True
        self.stop_requested = False
        try:
            students = self.api.get_students(set_type)
            predictions = []
            
            for student in students:
                if self.stop_requested: break
                topics = self.api.get_student_topics(student["id"])
                for topic in topics:
                    if self.stop_requested: break
                    
                    self.log(f"Processing {student['name']} - {topic['name']}", "system")
                    pred = self.run_session(student["id"], topic["id"], topic["name"], topic["subject_name"])
                    
                    predictions.append({
                        "student_id": student["id"],
                        "topic_id": topic["id"],
                        "predicted_level": float(pred)
                    })
                    time.sleep(1)
            
            if not self.stop_requested:
                self.log("Submitting predictions...", "system")
                mse = self.api.submit_predictions(predictions, set_type)
                self.log(f"FINAL_MSE_SCORE: {mse.get('mse_score')}", "success")
                
                self.log("Waiting 5s for tutoring eval...", "system")
                time.sleep(5)
                
                tutoring = self.api.evaluate_tutoring(set_type)
                self.log(f"FINAL_TUTORING_SCORE: {tutoring.get('score')}", "success")
                
        except Exception as e:
            self.log(f"Error: {str(e)}", "error")
        finally:
            self.running = False
            self.log("Agent stopped", "system")