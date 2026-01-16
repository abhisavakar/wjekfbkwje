"""Enhanced AI Tutoring Agent for Perfect Scores"""

import time
from typing import Dict, List, Optional

from api_client import KnowunityAPI
from level_inference_improved import HybridLevelDetector
from adaptive_tutor_improved import TutorGenerator
from llm_client_improved import LLMClient
import config


class TutoringAgent:
    """Main agent that orchestrates tutoring sessions - OPTIMIZED VERSION"""
    
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
        
        OPTIMIZED for both MSE = 0 and Tutoring = 5 scores.
        """
        # Initialize session
        self.student_id = student_id
        self.topic_id = topic_id
        self.topic_name = topic_name
        self.subject_name = subject_name
        self.detector = HybridLevelDetector(self.llm)
        self.detector.set_topic(topic_name)
        self.generator = TutorGenerator(self.llm)  # Fresh generator with clean context
        self.conversation_history = []
        self.turn_number = 0
        
        # Start conversation
        start_result = self.api.start_conversation(student_id, topic_id)
        self.conversation_id = start_result["conversation_id"]
        max_turns = start_result["max_turns"]
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"SESSION: {topic_name} ({subject_name})")
            print(f"Student: {student_id}")
            print(f"{'='*60}")
        
        # Opening message - diagnostic
        tutor_msg = self.generator.get_opening(topic_name, subject_name)
        
        # Main conversation loop
        level_estimates = []  # Track progression
        
        while self.turn_number < max_turns:
            # Send message and get response
            result = self.api.send_message(self.conversation_id, tutor_msg)
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
            level_estimates.append(level_est)
            self.predicted_level = round(level_est)
            
            if verbose:
                print(f"   [Estimate: Level {level_est:.2f}, Confidence: {confidence:.0%}]")
            
            # Generate next message (adaptive to current level estimate)
            tutor_msg = self.generator.generate_response(
                self.conversation_history,
                self.predicted_level,
                topic_name,
                self.turn_number + 1,
                student_response
            )
            
            # Small delay to be nice to API
            time.sleep(0.3)
        
        # Final prediction - use stable estimate
        # If estimates varied widely, trust later estimates more
        if len(level_estimates) >= 3:
            # Weight recent estimates more heavily
            weights = [0.1, 0.2, 0.3, 0.4][:len(level_estimates)]
            weights = weights[-len(level_estimates):]  # Take last N weights
            weighted_avg = sum(e * w for e, w in zip(level_estimates, weights)) / sum(weights)
            self.predicted_level = round(weighted_avg)
        else:
            self.predicted_level = self.detector.get_predicted_level(use_llm=self.llm is not None)
        
        # Clamp to valid range
        self.predicted_level = max(1, min(5, self.predicted_level))
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"FINAL PREDICTION: Level {self.predicted_level}")
            print(f"Estimate progression: {[f'{e:.2f}' for e in level_estimates]}")
            print(f"{'='*60}\n")
        
        return self.predicted_level
    
    def run_all_sessions(self, set_type: str = "mini_dev", verbose: bool = True) -> List[Dict]:
        """Run sessions for all student-topic pairs in a set"""
        
        # Get all students
        students = self.api.get_students(set_type)
        
        predictions = []
        total_pairs = 0
        
        # Count total pairs first
        for student in students:
            topics = self.api.get_student_topics(student["id"])
            total_pairs += len(topics)
        
        if verbose:
            print(f"\n🎯 Starting {total_pairs} tutoring sessions on {set_type} set")
            print(f"{'='*60}\n")
        
        pair_count = 0
        for student in students:
            student_id = student["id"]
            student_name = student["name"]
            
            # Get topics for this student
            topics = self.api.get_student_topics(student_id)
            
            for topic in topics:
                pair_count += 1
                topic_id = topic["id"]
                topic_name = topic["name"]
                subject_name = topic["subject_name"]
                
                if verbose:
                    print(f"\n>>> Session {pair_count}/{total_pairs}: {student_name} - {topic_name}")
                
                # Run session
                predicted_level = self.run_session(
                    student_id, topic_id, topic_name, subject_name, verbose
                )
                
                predictions.append({
                    "student_id": student_id,
                    "topic_id": topic_id,
                    "predicted_level": float(predicted_level)
                })
                
                # Brief pause between sessions
                time.sleep(0.5)
        
        return predictions
    
    def submit_and_evaluate(self, predictions: List[Dict], set_type: str = "mini_dev") -> Dict:
        """Submit predictions and get both MSE and tutoring scores"""
        
        print(f"\n{'='*60}")
        print(f"📤 SUBMITTING PREDICTIONS FOR {set_type.upper()}")
        print(f"{'='*60}\n")
        
        # Submit MSE predictions
        print(f"Submitting {len(predictions)} level predictions...")
        mse_result = self.api.submit_predictions(predictions, set_type)
        print(f"\n📊 MSE Score: {mse_result['mse_score']}")
        
        # Get tutoring score
        print("\n⏳ Evaluating tutoring quality (this may take 30-60 seconds)...")
        tutoring_result = self.api.evaluate_tutoring(set_type)
        print(f"📊 Tutoring Score: {tutoring_result['score']}/5.0")
        
        return {
            "mse": mse_result,
            "tutoring": tutoring_result
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="AI Tutoring Agent - OPTIMIZED for MSE=0 and Tutoring=5"
    )
    parser.add_argument("--set", default="mini_dev", 
                       choices=["mini_dev", "dev", "eval"],
                       help="Dataset to use (mini_dev=unlimited, dev=100 submissions, eval=3 submissions)")
    parser.add_argument("--no-llm", action="store_true", 
                       help="Disable LLM (use templates only - NOT RECOMMENDED)")
    parser.add_argument("--quiet", action="store_true", 
                       help="Reduce output verbosity")
    args = parser.parse_args()
    
    # Warning for non-mini_dev sets
    if args.set != "mini_dev":
        print(f"\n⚠️  WARNING: You are using the '{args.set}' set!")
        if args.set == "dev":
            print("   You have 100 MSE submissions and 100 tutoring evaluations.")
        elif args.set == "eval":
            print("   You have only 3 MSE submissions and 10 tutoring evaluations!")
        response = input("   Continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Aborted.")
            return
    
    # Create agent
    print("\n🤖 Initializing AI Tutor Agent (OPTIMIZED VERSION)")
    if args.no_llm:
        print("⚠️  Running without LLM - quality will be lower!")
    agent = TutoringAgent(use_llm=not args.no_llm)
    
    # Run all sessions
    print(f"\n🚀 Running sessions for {args.set} set...")
    predictions = agent.run_all_sessions(args.set, verbose=not args.quiet)
    
    # Submit and evaluate
    results = agent.submit_and_evaluate(predictions, args.set)
    
    # Final report
    print(f"\n{'='*60}")
    print("🏆 FINAL RESULTS")
    print(f"{'='*60}")
    print(f"MSE Score: {results['mse']['mse_score']:.4f} (Target: 0.0000)")
    print(f"Tutoring Score: {results['tutoring']['score']:.1f}/5.0 (Target: 5.0)")
    
    # Success check
    mse_perfect = results['mse']['mse_score'] == 0.0
    tutoring_perfect = results['tutoring']['score'] >= 4.5
    
    if mse_perfect and tutoring_perfect:
        print(f"\n🎉 EXCELLENT! You achieved near-perfect scores!")
    elif mse_perfect:
        print(f"\n✅ MSE is perfect! Work on tutoring quality to reach 5.0")
    elif tutoring_perfect:
        print(f"\n✅ Tutoring is great! Improve level detection for MSE=0")
    else:
        print(f"\n⚠️  Both metrics need improvement. Review conversation patterns.")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
