"""Knowunity API Client - Matches actual endpoints"""

import requests
from typing import List, Dict, Optional
import config

class KnowunityAPI:
    def __init__(self):
        self.base_url = config.KNOWUNITY_BASE_URL
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": config.KNOWUNITY_API_KEY
        }
    
    # ============ CATALOG (No Auth) ============
    
    def get_subjects(self) -> List[Dict]:
        """Get all subjects"""
        r = requests.get(f"{self.base_url}/subjects")
        return r.json()["subjects"]
    
    def get_topics(self, subject_id: Optional[str] = None) -> List[Dict]:
        """Get all topics, optionally filtered by subject"""
        url = f"{self.base_url}/topics"
        if subject_id:
            url += f"?subject_id={subject_id}"
        r = requests.get(url)
        return r.json()["topics"]
    
    def get_students(self, set_type: str = "mini_dev") -> List[Dict]:
        """Get students for a set (mini_dev, dev, eval)"""
        r = requests.get(f"{self.base_url}/students?set_type={set_type}")
        return r.json()["students"]
    
    def get_student_topics(self, student_id: str) -> List[Dict]:
        """Get topics available for a specific student"""
        r = requests.get(f"{self.base_url}/students/{student_id}/topics")
        return r.json()["topics"]
    
    # ============ INTERACTIONS (Auth Required) ============
    
    def start_conversation(self, student_id: str, topic_id: str) -> Dict:
        """Start a new conversation with a student on a topic"""
        r = requests.post(
            f"{self.base_url}/interact/start",
            headers=self.headers,
            json={"student_id": student_id, "topic_id": topic_id}
        )
        return r.json()
    
    def send_message(self, conversation_id: str, tutor_message: str) -> Dict:
        """Send a message and get student response"""
        r = requests.post(
            f"{self.base_url}/interact",
            headers=self.headers,
            json={
                "conversation_id": conversation_id,
                "tutor_message": tutor_message
            }
        )
        return r.json()
    
    # ============ EVALUATION (Auth Required) ============
    
    def submit_predictions(self, predictions: List[Dict], set_type: str = "mini_dev") -> Dict:
        """
        Submit level predictions for ALL student-topic pairs in a set.
        
        predictions: [{"student_id": "...", "topic_id": "...", "predicted_level": 3.0}, ...]
        """
        r = requests.post(
            f"{self.base_url}/evaluate/mse",
            headers=self.headers,
            json={"set_type": set_type, "predictions": predictions}
        )
        return r.json()
    
    def evaluate_tutoring(self, set_type: str = "mini_dev") -> Dict:
        """Get tutoring score for all conversations in a set"""
        r = requests.post(
            f"{self.base_url}/evaluate/tutoring",
            headers=self.headers,
            json={"set_type": set_type},
            timeout=120  # LLM judge can be slow
        )
        return r.json()
    
    # ============ LEADERBOARDS ============
    
    def get_leaderboard(self, board_type: str = "combined") -> Dict:
        """Get leaderboard (inference, tutoring, or combined)"""
        r = requests.get(f"{self.base_url}/evaluate/leaderboard/{board_type}")
        return r.json()
