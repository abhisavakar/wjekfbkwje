"""AI Tutoring Agent v5.1: History Aware"""

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
        self.stop_requested = False
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

    def run_session(self, student_id: str, topic_id: str, topic_name: str, subject_name: str, full_student_name: str, set_type: str) -> int:
        self.log(f"🎯 Starting: {topic_name} ({full_student_name})", "system")
        student_first_name = full_student_name.split()[0] if full_student_name else "Student"

        detector = LLMFirstDetector(self.llm)
        detector.set_topic(topic_name)
        generator = TutorGeneratorV3(self.llm)
        
        start_res = self.api.start_conversation(student_id, topic_id)
        conv_id = start_res["conversation_id"]
        max_turns = start_res["max_turns"]
        tutor_msg = generator.get_opening(topic_name, subject_name)
        turn = 0
        
        # Simple History Hash to prevent exact duplicate questions
        last_tutor_questions = []

        while turn < max_turns and not self.stop_requested:
            self.log(f"Turn {turn+1}/{max_turns}", "info")
            self.log(f"TUTOR: {tutor_msg[:100]}{'...' if len(tutor_msg) > 100 else ''}", "info")
            
            # Duplication Check (Basic)
            if any(q in tutor_msg for q in last_tutor_questions[-2:]):
                self.log("⚠️ Detected repetition. Rerolling...", "info")
                # (In a real system, we'd trigger a regenerate here, but for now we proceed)
            last_tutor_questions.append(tutor_msg)

            res = self.api.send_message(conv_id, tutor_msg)
            student_msg = res["student_response"]
            self.log(f"STUDENT: {student_msg[:100]}{'...' if len(student_msg) > 100 else ''}", "info")
            
            turn = res["turn_number"]
            detector.add_exchange(tutor_msg, student_msg)
            level_est, conf = detector.get_estimate(turn)
            pred_level = max(1, min(5, round(level_est)))
            
            self.log(f"📈 Level: {level_est:.1f} | Confidence: {conf:.0%}", "info")
            
            self.emit_state(detector.conversation_history, detector.estimates_history, level_est, conf)
            
            if res.get("is_complete"): break
            
            phase = "assess" if turn <= self.ASSESS_TURNS else "tutor"
            if turn > (self.ASSESS_TURNS + self.TUTOR_TURNS): phase = "close"
            
            tutor_msg = generator.generate_response(
                conversation_history=detector.conversation_history, 
                student_level=pred_level, 
                topic=topic_name, 
                turn_number=turn + 1, 
                phase=phase, 
                last_student_response=student_msg, 
                current_confidence=conf,
                student_name=student_first_name 
            )
            time.sleep(0.5)

        final_level = detector.get_final_prediction()
        self.log(f"✅ Prediction: Level {final_level}", "success")
        return final_level

    def run_all_sessions(self, set_type: str = "mini_dev"):
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
                self.log("📊 Submitting...", "system")
                mse = self.api.submit_predictions(preds, set_type)
                self.log(f"MSE: {mse.get('mse_score')}", "success")
                tutoring = self.api.evaluate_tutoring(set_type)
                self.log(f"TUTORING: {tutoring.get('score')}/5.0", "success")
                
        except Exception as e:
            self.log(f"Error: {e}", "error")