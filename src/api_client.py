"""Knowunity API Client - Matches actual endpoints"""

import requests
import time
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
        r = requests.get(f"{self.base_url}/subjects")
        r.raise_for_status()
        return r.json()["subjects"]
    
    def get_topics(self, subject_id: Optional[str] = None) -> List[Dict]:
        url = f"{self.base_url}/topics"
        if subject_id:
            url += f"?subject_id={subject_id}"
        r = requests.get(url)
        r.raise_for_status()
        return r.json()["topics"]
    
    def get_students(self, set_type: str = "mini_dev") -> List[Dict]:
        r = requests.get(f"{self.base_url}/students?set_type={set_type}")
        r.raise_for_status()
        return r.json()["students"]
    
    def get_student_topics(self, student_id: str) -> List[Dict]:
        r = requests.get(f"{self.base_url}/students/{student_id}/topics")
        r.raise_for_status()
        return r.json()["topics"]
    
    # ============ INTERACTIONS (Auth Required) ============
    
    def start_conversation(self, student_id: str, topic_id: str) -> Dict:
        r = requests.post(
            f"{self.base_url}/interact/start",
            headers=self.headers,
            json={"student_id": student_id, "topic_id": topic_id}
        )
        r.raise_for_status()
        return r.json()
    
    def send_message(self, conversation_id: str, tutor_message: str) -> Dict:
        payload = {
            "conversation_id": conversation_id,
            "tutor_message": tutor_message,
            "message": tutor_message
        }
        r = requests.post(
            f"{self.base_url}/interact",
            headers=self.headers,
            json=payload
        )
        if r.status_code == 422:
            print(f"⚠️  422 Unprocessable Entity: {r.text[:500]}")
        r.raise_for_status()
        return r.json()
    
    # ============ EVALUATION (Auth Required) ============
    
    def submit_predictions(self, predictions: List[Dict], set_type: str = "mini_dev") -> Dict:
        r = requests.post(
            f"{self.base_url}/evaluate/mse",
            headers=self.headers,
            json={"set_type": set_type, "predictions": predictions}
        )
        try:
            return r.json()
        except Exception:
            print(f"Error submitting predictions: {r.text}")
            raise
    
    def evaluate_tutoring(self, set_type: str = "mini_dev") -> Dict:
        """Get tutoring score with retry logic"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                r = requests.post(
                    f"{self.base_url}/evaluate/tutoring",
                    headers=self.headers,
                    json={"set_type": set_type},
                    timeout=120
                )
                
                # Try to parse JSON
                try:
                    return r.json()
                except requests.exceptions.JSONDecodeError:
                    if r.status_code == 504:
                        print(f"⚠️ Gateway Timeout (504) on attempt {attempt+1}. Retrying...")
                    else:
                        print(f"⚠️ API Error ({r.status_code}): {r.text[:200]}")
                        if attempt == max_retries - 1:
                            return {"score": 0.0, "error": "Failed to get score"}
                            
            except requests.exceptions.Timeout:
                print(f"⚠️ Request timed out on attempt {attempt+1}. Retrying...")
            except Exception as e:
                print(f"⚠️ Error: {e}")
            
            time.sleep(2)  # Wait before retry
            
        return {"score": 0.0, "error": "Evaluation failed after retries"}
    
    # ============ LEADERBOARDS ============
    
    def get_leaderboard(self, board_type: str = "combined") -> Dict:
        r = requests.get(f"{self.base_url}/evaluate/leaderboard/{board_type}")
        return r.json()