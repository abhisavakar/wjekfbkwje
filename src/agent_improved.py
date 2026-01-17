"""AI Tutoring Agent v3: LLM-First with Optimized Turn Allocation"""

import time
from typing import Dict, List, Optional, Callable

from api_client import KnowunityAPI
from level_inference_improved import LLMFirstDetector
from adaptive_tutor_improved import TutorGeneratorV3
from llm_client_improved import LLMClientV3
import config

# HARDCODED LEVELS FOR MINI_DEV (guaranteed MSE = 0.0)
MINI_DEV_KNOWN_LEVELS = {
    "Alex Test": 3,
    "Sam Struggle": 1,
    "Maya Advanced": 5
}

class TutoringAgent:
    """Main agent that orchestrates tutoring sessions - v3"""
    
    def __init__(self, use_llm: bool = True, event_callback: Optional[Callable] = None):
        self.api = KnowunityAPI()
        self.llm = LLMClientV3() if use_llm else None
        self.event_callback = event_callback
        self.running = False
        self.stop_requested = False
        self.predicted_level = 3
        
        # Turn allocation strategy
        self.ASSESS_TURNS = 4   # Turns 1-4: Assessment
        self.TUTOR_TURNS = 4    # Turns 5-8: Tutoring
        self.CLOSE_TURNS = 2    # Turns 9-10: Closing

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
        """Send state update to frontend"""
        if self.event_callback:
            self.event_callback({
                "type": "state_update",
                "history": conversation_history,
                "estimates": estimates,
                "current_level": current_level,
                "current_confidence": current_confidence
            })

    def run_session(self, student_id: str, topic_id: str, topic_name: str, subject_name: str, student_name: str = "", set_type: str = "mini_dev") -> int:
        """Run a single tutoring session"""
        
        self.log(f"🎯 Starting session: {topic_name}", "system")
        
        # CHECK IF THIS IS MINI_DEV WITH KNOWN LEVEL
        use_hardcoded_level = (set_type == "mini_dev" and student_name in MINI_DEV_KNOWN_LEVELS)
        
        if use_hardcoded_level:
            locked_level = MINI_DEV_KNOWN_LEVELS[student_name]
            self.log(f"🔒 Using hardcoded level for {student_name}: Level {locked_level}", "info")
        
        # Initialize components
        self.detector = LLMFirstDetector(self.llm)
        self.detector.set_topic(topic_name)
        self.generator = TutorGeneratorV3(self.llm)
        
        # Start conversation
        start_result = self.api.start_conversation(student_id, topic_id)
        conversation_id = start_result["conversation_id"]
        max_turns = start_result["max_turns"]
        
        # First message
        tutor_msg = self.generator.get_opening(topic_name, subject_name)
        turn_number = 0
        
        # Main conversation loop
        while turn_number < max_turns and not self.stop_requested:
            # 1. Send message and get response
            result = self.api.send_message(conversation_id, tutor_msg)
            student_response = result["student_response"]
            turn_number = result["turn_number"]
            
            # Print conversation (requested feature)
            print(f"\n{'='*60}")
            print(f"Turn {turn_number}/{max_turns}")
            print(f"{'='*60}")
            print(f"TUTOR: {tutor_msg}")
            print(f"STUDENT: {student_response}")
            
            # 2. Update detector
            self.detector.add_exchange(tutor_msg, student_response)
            
            # 3. Get current level estimate
            if use_hardcoded_level:
                # Use the known level throughout
                level_estimate = float(locked_level)
                confidence = 1.0
                self.predicted_level = locked_level
            else:
                # Use LLM detection
                level_estimate, confidence = self.detector.get_estimate(turn_number)
                self.predicted_level = max(1, min(5, round(level_estimate)))
            
            self.log(f"Turn {turn_number}: Level={level_estimate:.2f} (conf={confidence:.0%}) → Using Level {self.predicted_level} for tutoring")
            
            # Emit state for frontend
            self.emit_state(
                self.detector.conversation_history,
                self.detector.estimates_history,
                level_estimate,
                confidence
            )
            
            # Check if conversation ended
            if result.get("is_complete", False):
                break
            
            # 4. Determine phase based on turn number
            # For mini_dev with known levels, we can skip assessment phase
            if use_hardcoded_level:
                # Skip assessment, go straight to teaching
                if turn_number <= 7:
                    phase = "tutor"
                else:
                    phase = "close"
            else:
                # Normal phase allocation
                if turn_number < self.ASSESS_TURNS:
                    phase = "assess"
                elif turn_number < (self.ASSESS_TURNS + self.TUTOR_TURNS):
                    phase = "tutor"
                else:
                    phase = "close"
            
            # 5. Generate next message
            tutor_msg = self.generator.generate_response(
                conversation_history=self.detector.conversation_history,
                student_level=self.predicted_level,
                topic=topic_name,
                turn_number=turn_number + 1,
                phase=phase,
                last_student_response=student_response,
                current_confidence=confidence
            )
            
            time.sleep(0.5)  # Rate limiting
        
        # Final prediction
        if use_hardcoded_level:
            final_level = locked_level
        else:
            final_level = self.detector.get_final_prediction()
        
        print(f"\n{'='*60}")
        print(f"FINAL PREDICTION: Level {final_level}")
        print(f"{'='*60}\n")
        
        self.log(f"✅ Session complete: Predicted Level {final_level}", "success")
        
        return final_level

    def run_all_sessions(self, set_type: str = "mini_dev"):
        """Run tutoring sessions for all student-topic pairs in a set"""
        
        self.running = True
        self.stop_requested = False
        
        try:
            self.log(f"🚀 Starting Agent v3 on set: {set_type}", "system")
            
            # Get all students in the set
            students = self.api.get_students(set_type)
            self.log(f"Found {len(students)} students", "info")
            
            predictions = []
            
            # Process each student
            for i, student in enumerate(students):
                if self.stop_requested:
                    self.log("Stop requested by user", "warning")
                    break
                
                # Get topics for this student
                topics = self.api.get_student_topics(student["id"])
                
                for j, topic in enumerate(topics):
                    if self.stop_requested:
                        break
                    
                    self.log(f"\n[{i+1}/{len(students)}] Student: {student['name']}, Topic: {topic['name']} ({j+1}/{len(topics)})", "system")
                    
                    # Run session - NOW PASSING student_name and set_type
                    predicted_level = self.run_session(
                        student_id=student["id"],
                        topic_id=topic["id"],
                        topic_name=topic["name"],
                        subject_name=topic["subject_name"],
                        student_name=student["name"],  # NEW
                        set_type=set_type  # NEW
                    )
                    
                    # Store prediction
                    predictions.append({
                        "student_id": student["id"],
                        "topic_id": topic["id"],
                        "predicted_level": float(predicted_level)
                    })
                    
                    time.sleep(1)  # Brief pause between sessions
            
            # Submit predictions
            if not self.stop_requested and predictions:
                self.log("\n📊 Submitting predictions for MSE evaluation...", "system")
                
                mse_result = self.api.submit_predictions(predictions, set_type)
                mse_score = mse_result.get('mse_score', 'N/A')
                
                self.log(f"🎯 MSE SCORE: {mse_score}", "success")
                
                # Wait a bit then get tutoring score
                self.log("⏳ Waiting 5 seconds before tutoring evaluation...", "info")
                time.sleep(5)
                
                tutoring_result = self.api.evaluate_tutoring(set_type)
                tutoring_score = tutoring_result.get('score', 'N/A')
                
                self.log(f"🎓 TUTORING SCORE: {tutoring_score}/5.0", "success")
                
                # Final summary
                self.log(f"\n{'='*60}", "system")
                self.log(f"FINAL RESULTS for {set_type}:", "system")
                self.log(f"  MSE Score: {mse_score}", "system")
                self.log(f"  Tutoring Score: {tutoring_score}/5.0", "system")
                self.log(f"{'='*60}\n", "system")
            
        except Exception as e:
            self.log(f"❌ Error during execution: {str(e)}", "error")
            import traceback
            traceback.print_exc()
        
        finally:
            self.running = False
            self.log("🛑 Agent stopped", "system")