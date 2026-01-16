"""
Tests for the AI Tutoring Agent
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from level_inference import LevelInferenceEngine, QuestionType, Response
from adaptive_tutor import AdaptiveTutor, TutoringStrategy, ResponseTone


class TestLevelInferenceEngine:
    """Tests for the level inference engine"""
    
    def test_initial_state(self):
        """Test initial state is Level 3 with low confidence"""
        engine = LevelInferenceEngine()
        level, confidence = engine.get_predicted_level()
        assert level == 3
        assert confidence < 0.5  # Low initial confidence
    
    def test_struggling_response(self):
        """Test detection of Level 1 struggling response"""
        engine = LevelInferenceEngine()
        
        response = engine.analyze_response(
            question="What is a fraction?",
            question_type=QuestionType.COMPREHENSION,
            answer="I don't know what that means"
        )
        
        assert response.score < 0.5
        level, _ = engine.get_predicted_level()
        assert level < 3
    
    def test_confident_response(self):
        """Test detection of confident correct response"""
        engine = LevelInferenceEngine()
        
        response = engine.analyze_response(
            question="What is a fraction?",
            question_type=QuestionType.COMPREHENSION,
            answer="A fraction represents part of a whole. The numerator is the top and denominator is the bottom because it denominates or divides the whole into equal parts.",
            expected_concepts=["part", "whole", "numerator", "denominator"]
        )
        
        assert response.score > 0.5
    
    def test_question_type_progression(self):
        """Test that question types adapt to responses"""
        engine = LevelInferenceEngine()
        
        # First question should be APPLICATION level
        q_type = engine.get_next_question_type()
        assert q_type in [QuestionType.APPLICATION, QuestionType.COMPREHENSION]
    
    def test_confidence_increases_with_responses(self):
        """Test that confidence increases as we get more responses"""
        engine = LevelInferenceEngine()
        
        initial_conf = engine.confidence
        
        engine.analyze_response(
            question="Q1",
            question_type=QuestionType.COMPREHENSION,
            answer="Good answer explaining the concept because I understand it"
        )
        
        assert engine.confidence > initial_conf
    
    def test_should_continue_assessment(self):
        """Test assessment continuation logic"""
        engine = LevelInferenceEngine()
        
        # Should continue initially
        assert engine.should_continue_assessment()
        
        # After reaching confidence threshold, should stop
        engine.confidence = 0.90
        assert not engine.should_continue_assessment()


class TestAdaptiveTutor:
    """Tests for the adaptive tutoring system"""
    
    def test_initial_level(self):
        """Test that tutor initializes at specified level"""
        tutor = AdaptiveTutor(initial_level=3)
        assert tutor.current_level == 3
        assert tutor.plan.strategy == TutoringStrategy.DIRECT
    
    def test_level_1_config(self):
        """Test Level 1 tutoring configuration"""
        tutor = AdaptiveTutor(initial_level=1)
        
        assert tutor.plan.strategy == TutoringStrategy.REMEDIATE
        assert tutor.plan.tone == ResponseTone.SUPPORTIVE
        assert tutor.plan.scaffolding_needed == True
        assert tutor.plan.examples_to_use >= 2
        assert "basic definitions" in tutor.plan.focus_areas
    
    def test_level_5_config(self):
        """Test Level 5 tutoring configuration"""
        tutor = AdaptiveTutor(initial_level=5)
        
        assert tutor.plan.strategy == TutoringStrategy.EXTEND
        assert tutor.plan.tone == ResponseTone.CHALLENGING
        assert tutor.plan.scaffolding_needed == False
        assert "extensions" in tutor.plan.focus_areas
    
    def test_update_level(self):
        """Test level update changes teaching plan"""
        tutor = AdaptiveTutor(initial_level=3)
        
        assert tutor.plan.strategy == TutoringStrategy.DIRECT
        
        tutor.update_level(1)
        
        assert tutor.current_level == 1
        assert tutor.plan.strategy == TutoringStrategy.REMEDIATE
    
    def test_greeting_varies_by_level(self):
        """Test that greetings are appropriate for level"""
        tutor_l1 = AdaptiveTutor(initial_level=1)
        tutor_l5 = AdaptiveTutor(initial_level=5)
        
        greeting_l1 = tutor_l1.generate_greeting("fractions")
        greeting_l5 = tutor_l5.generate_greeting("fractions")
        
        # Level 1 should have more supportive language
        assert "step by step" in greeting_l1.lower() or "basics" in greeting_l1.lower()
        # Level 5 should mention going deep
        assert "deep" in greeting_l5.lower() or "explore" in greeting_l5.lower()
    
    def test_record_response_adapts_level(self):
        """Test that recording responses can adapt level"""
        tutor = AdaptiveTutor(initial_level=3)
        
        # Record several successes
        for _ in range(4):
            tutor.record_response(was_correct=True)
        
        # Should have moved up
        assert tutor.current_level > 3
    
    def test_hint_threshold_by_level(self):
        """Test that hint thresholds vary by level"""
        tutor_l1 = AdaptiveTutor(initial_level=1)
        tutor_l5 = AdaptiveTutor(initial_level=5)
        
        # Level 1 should get hints sooner
        assert tutor_l1.should_provide_hint(attempts=1) == True
        assert tutor_l5.should_provide_hint(attempts=1) == False
        assert tutor_l5.should_provide_hint(attempts=4) == True
    
    def test_scaffolding_level_by_level(self):
        """Test scaffolding amount varies by level"""
        for level in range(1, 6):
            tutor = AdaptiveTutor(initial_level=level)
            scaffolding = tutor.get_scaffolding_level()
            
            if level <= 2:
                assert scaffolding >= 2
            else:
                assert scaffolding <= 1


class TestResponseAnalysis:
    """Tests for response pattern analysis"""
    
    def test_uncertainty_detection(self):
        """Test detection of uncertainty markers"""
        engine = LevelInferenceEngine()
        
        uncertain_response = engine.analyze_response(
            question="What is X?",
            question_type=QuestionType.COMPREHENSION,
            answer="I think maybe it's... like... something?"
        )
        
        confident_response = engine.analyze_response(
            question="What is X?",
            question_type=QuestionType.COMPREHENSION,
            answer="X is definitely this because of that reason."
        )
        
        assert uncertain_response.confidence < confident_response.confidence
    
    def test_dont_know_detection(self):
        """Test detection of 'I don't know' responses"""
        engine = LevelInferenceEngine()
        
        response = engine.analyze_response(
            question="What is calculus?",
            question_type=QuestionType.RECALL,
            answer="I don't know what that is"
        )
        
        assert "L1-" in str(response.indicators) or response.score < 0.3


def run_tests():
    """Run all tests"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()
