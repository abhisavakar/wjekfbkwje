"""Main AI Tutoring Agent"""

import time
from typing import Dict, List, Tuple, Optional

from api_client import KnowunityAPI
from level_inference import HybridLevelDetector
from adaptive_tutor import TutorGenerator
from llm_client import LLMClient
import config


class TutoringAgent:
    """Main agent that orchestrates tutoring sessions"""
    
    def __init__(self, use_llm: bool = True):
        self.api = KnowunityAPI()
        self.llm = LLMClient() if use_llm else None
        self.detector = HybridLevelDetector(self.llm)
        self.generator = TutorGenerator(self.llm)
        
        # Session state
        self.conversation_id = None
        self.student_id = None
        self.topic_id = None
        self.topic_name = None
        self.subject_name = None
        self.turn_number = 0
        self.conversation_history = []
        self.predicted_level = 3
    
    def run_session(
        self, 
        student_id: str, 
        topic_id: str,
        topic_name: str,
        subject_name: str,
        verbose: bool = True
    ) -> int:
        """
        Run a complete tutoring session with a student.
        Returns the predicted level.
        """
        # Initialize
        self.student_id = student_id
        self.topic_id = topic_id
        self.topic_name = topic_name
        self.subject_name = subject_name
        self.detector = HybridLevelDetector(self.llm)
        self.detector.set_topic(topic_name)
        self.conversation_history = []
        self.turn_number = 0
        
        # Start conversation
        start_result = self.api.start_conversation(student_id, topic_id)
        self.conversation_id = start_result["conversation_id"]
        max_turns = start_result["max_turns"]
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"SESSION: {topic_name} ({subject_name})")
            print(f"{'='*60}")
        
        # Opening message
        tutor_msg = self.generator.get_opening(topic_name, subject_name)
        
        # Main conversation loop
        while self.turn_number < max_turns:
            # Send message
            result = self.api.send_message(self.conversation_id, tutor_msg)
            
            # Handle API errors
            if "error" in result:
                print(f"\n⚠️ API Error: {result.get('error')}")
                return None
            
            if "student_response" not in result:
                print(f"\n⚠️ Missing student_response in API response: {result}")
                return None
            
            student_response = result["student_response"]
            self.turn_number = result["turn_number"]
            
            if verbose:
                print(f"\n[Turn {self.turn_number}]")
                print(f"TUTOR: {tutor_msg}")
                print(f"STUDENT: {student_response}")
            
            # Track conversation
            self.conversation_history.append({"role": "tutor", "content": tutor_msg})
            self.conversation_history.append({"role": "student", "content": student_response})
            self.detector.add_exchange(tutor_msg, student_response)
            
            # Check if complete
            if result.get("is_complete", False):
                break
            
            # Get current estimate
            level_est, confidence = self.detector.get_estimate(use_llm=self.llm is not None)
            self.predicted_level = round(level_est)
            
            if verbose:
                print(f"   [Estimate: Level {level_est:.1f}, Confidence: {confidence:.0%}]")
            
            # Generate next message
            tutor_msg = self.generator.generate_response(
                self.conversation_history,
                self.predicted_level,
                topic_name,
                self.turn_number + 1,
                student_response
            )
            
            # Small delay to be nice to API
            time.sleep(0.3)
        
        # Final prediction
        self.predicted_level = self.detector.get_predicted_level(use_llm=self.llm is not None)
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"FINAL PREDICTION: Level {self.predicted_level}")
            print(f"{'='*60}\n")
        
        return self.predicted_level
    
    def run_all_sessions(self, set_type: str = "mini_dev", verbose: bool = True) -> List[Dict]:
        """Run sessions for all student-topic pairs in a set"""
        
        # Get all students
        students = self.api.get_students(set_type)
        
        predictions = []
        
        for student in students:
            student_id = student["id"]
            student_name = student["name"]
            
            # Get topics for this student
            topics = self.api.get_student_topics(student_id)
            
            for topic in topics:
                topic_id = topic["id"]
                topic_name = topic["name"]
                subject_name = topic["subject_name"]
                
                if verbose:
                    print(f"\n>>> Starting session: {student_name} - {topic_name}")
                
                # Run session
                predicted_level = self.run_session(
                    student_id, topic_id, topic_name, subject_name, verbose
                )
                
                predictions.append({
                    "student_id": student_id,
                    "topic_id": topic_id,
                    "predicted_level": float(predicted_level)
                })
        
        return predictions
    
    def submit_and_evaluate(self, predictions: List[Dict], set_type: str = "mini_dev") -> Dict:
        """Submit predictions and get both MSE and tutoring scores"""
        
        # Submit MSE predictions
        mse_result = self.api.submit_predictions(predictions, set_type)
        print(f"\n📊 MSE Score: {mse_result['mse_score']}")
        
        # Get tutoring score
        print("⏳ Evaluating tutoring (may take a moment)...")
        tutoring_result = self.api.evaluate_tutoring(set_type)
        print(f"📊 Tutoring Score: {tutoring_result['score']}")
        
        return {
            "mse": mse_result,
            "tutoring": tutoring_result
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Tutoring Agent")
    parser.add_argument("--set", default="mini_dev", choices=["mini_dev", "dev", "eval"])
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM (use templates)")
    parser.add_argument("--quiet", action="store_true", help="Less output")
    args = parser.parse_args()
    
    # Create agent
    agent = TutoringAgent(use_llm=not args.no_llm)
    
    # Run all sessions
    print(f"🚀 Running sessions for {args.set} set...")
    predictions = agent.run_all_sessions(args.set, verbose=not args.quiet)
    
    # Submit and evaluate
    print(f"\n📤 Submitting {len(predictions)} predictions...")
    results = agent.submit_and_evaluate(predictions, args.set)
    
    print(f"\n{'='*60}")
    print("FINAL RESULTS")
    print(f"{'='*60}")
    print(f"MSE Score: {results['mse']['mse_score']}")
    print(f"Tutoring Score: {results['tutoring']['score']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()