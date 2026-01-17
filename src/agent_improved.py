"""AI Tutoring Agent v3.5: Orchestrator"""

import time
from typing import Optional, Callable
from api_client import KnowunityAPI
from level_inference_improved import LLMFirstDetector
from adaptive_tutor_improved import TutorGeneratorV3
from llm_client_improved import LLMClientV3

class TutoringAgent:
    def __init__(self, use_llm: bool = True, event_callback: Optional[Callable] = None):
        self.api = KnowunityAPI()
        self.llm = LLMClientV3() if use_llm else None
        self.event_callback = event_callback
        self.running = False
        self.stop_requested = False
        
        # Strategy: 3 Assess, 5 Tutor, 2 Close
        self.ASSESS_TURNS = 3
        self.TUTOR_TURNS = 5

    def log(self, message: str, type: str = "info"):
        if self.event_callback:
            self.event_callback({
                "type": "log", "level": type, "message": message, "timestamp": time.time()
            })
        print(f"[{type.upper()}] {message}")

    def emit_state(self, history, estimates, level, conf):
        if self.event_callback:
            self.event_callback({
                "type": "state_update", "history": history, "estimates": estimates,
                "current_level": level, "current_confidence": conf
            })

    def run_session(self, student_id: str, topic_id: str, topic_name: str, subject_name: str, student_name: str, set_type: str) -> int:
        self.log(f"🎯 Starting session: {topic_name}", "system")
        
        # Initialize
        detector = LLMFirstDetector(self.llm)
        detector.set_topic(topic_name)
        generator = TutorGeneratorV3(self.llm)
        
        # API Start
        start_res = self.api.start_conversation(student_id, topic_id)
        conv_id = start_res["conversation_id"]
        max_turns = start_res["max_turns"]
        
        # Turn 0
        tutor_msg = generator.get_opening(topic_name, subject_name)
        turn = 0
        
        while turn < max_turns and not self.stop_requested:
            # Send & Receive
            res = self.api.send_message(conv_id, tutor_msg)
            student_msg = res["student_response"]
            turn = res["turn_number"]
            
            # Detect Level
            detector.add_exchange(tutor_msg, student_msg)
            level_est, conf = detector.get_estimate(turn)
            pred_level = max(1, min(5, round(level_est)))
            
            self.emit_state(detector.conversation_history, detector.estimates_history, level_est, conf)
            self.log(f"Turn {turn}: Level {level_est:.2f} (Conf {conf:.0%})")
            
            if res.get("is_complete"): break
            
            # Determine Phase
            if turn <= self.ASSESS_TURNS: phase = "assess"
            elif turn <= (self.ASSESS_TURNS + self.TUTOR_TURNS): phase = "tutor"
            else: phase = "close"
            
            # Generate Next
            tutor_msg = generator.generate_response(
                detector.conversation_history, pred_level, topic_name, 
                turn + 1, phase, student_msg, conf
            )
            
            time.sleep(0.5)

        final_level = detector.get_final_prediction()
        self.log(f"✅ Session complete: Predicted Level {final_level}", "success")
        return final_level

    def run_all_sessions(self, set_type: str = "mini_dev"):
        self.running = True
        try:
            students = self.api.get_students(set_type)
            preds = []
            
            for s in students:
                if self.stop_requested: break
                topics = self.api.get_student_topics(s["id"])
                for t in topics:
                    if self.stop_requested: break
                    level = self.run_session(s["id"], t["id"], t["name"], t["subject_name"], s["name"], set_type)
                    preds.append({"student_id": s["id"], "topic_id": t["id"], "predicted_level": float(level)})
            
            if preds and not self.stop_requested:
                self.log("📊 Submitting predictions...", "system")
                mse = self.api.submit_predictions(preds, set_type)
                self.log(f"MSE SCORE: {mse.get('mse_score')}", "success")
                
                time.sleep(5)
                tutoring = self.api.evaluate_tutoring(set_type)
                self.log(f"TUTORING SCORE: {tutoring.get('score')}/5.0", "success")
                
        except Exception as e:
            self.log(f"Error: {e}", "error")
        finally:
            self.running = False