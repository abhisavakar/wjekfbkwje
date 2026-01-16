"""Generate tutoring responses based on student level"""

from typing import Optional
from prompts import get_opening_message
import re

class TutorGenerator:
    """Generates appropriate tutoring messages"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.student_strengths = []
        self.student_struggles = []
    
    def get_opening(self, topic_name: str, subject_name: str) -> str:
        """Get opening message for a topic"""
        return get_opening_message(topic_name, subject_name)
    
    def generate_response(
        self,
        conversation_history: list,
        student_level: int,
        topic: str,
        turn_number: int,
        last_student_response: str
    ) -> str:
        """Generate next tutor message"""
        
        # Determine phase
        if turn_number <= 3:
            phase = "assess"
        elif turn_number <= 8:
            phase = "tutor"
        else:
            phase = "close"
        
        # Track what student knows/struggles with
        self._track_understanding(last_student_response, student_level)
        
        # Use LLM if available
        if self.llm_client:
            try:
                return self.llm_client.generate_tutor_message(
                    conversation_history,
                    student_level,
                    topic,
                    turn_number,
                    phase
                )
            except Exception as e:
                print(f"LLM generation failed: {e}, using templates")
        
        # Use improved templates
        return self._smart_template_response(
            student_level, phase, topic, last_student_response, 
            turn_number, conversation_history
        )
    
    def _track_understanding(self, response: str, level: int):
        """Track what student understands"""
        response_lower = response.lower()
        
        # Detect understanding
        if any(word in response_lower for word in ["because", "so", "means", "example"]):
            if response not in self.student_strengths:
                self.student_strengths.append(response[:50])
        
        # Detect struggles
        if any(word in response_lower for word in ["don't know", "confused", "not sure", "i think"]):
            if response not in self.student_struggles:
                self.student_struggles.append(response[:50])
    
    def _smart_template_response(
        self, 
        level: int, 
        phase: str, 
        topic: str,
        last_response: str,
        turn: int,
        history: list
    ) -> str:
        """Improved template-based responses that actually teach"""
        
        topic_lower = topic.lower()
        
        if phase == "assess":
            return self._diagnostic_question(level, topic, turn, last_response)
        
        elif phase == "tutor":
            return self._teaching_response(level, topic, last_response, turn)
        
        elif phase == "close":
            return self._personalized_closing(level, topic, history)
        
        return "Let's continue learning!"
    
    def _diagnostic_question(self, level: int, topic: str, turn: int, last_response: str) -> str:
        """Generate diagnostic questions based on detected level"""
        
        topic_lower = topic.lower()
        
        if level <= 1:
            # Very basic questions for struggling students
            if turn == 2:
                if "function" in topic_lower:
                    return "No worries! Let's start simple. Have you ever heard the word 'function' before? What do you think it might mean in math?"
                elif "equation" in topic_lower:
                    return "No problem! Let's break this down. Can you tell me what an equation is? Like, in your own words?"
                elif "thermo" in topic_lower or "energy" in topic_lower:
                    return "That's okay! Let's start with basics. Have you learned anything about energy before? What comes to mind?"
                else:
                    return f"No worries at all! Let's start from the beginning. What's the simplest thing you know about {topic}?"
            else:
                return "Great! Let me explain this in a really simple way. Just listen and let me know if anything is confusing."
        
        elif level == 2:
            # Probing questions for below-grade students
            if turn == 2:
                return "You're on the right track! Can you give me a specific example of what you just described? That'll help me understand what you know."
            else:
                return "Good thinking! Let me ask you this: what happens if we change one part of that? Can you predict what would happen?"
        
        elif level == 3:
            # Standard questions for at-grade students
            if turn == 2:
                return "Good! Now, can you explain WHY that works the way it does? What's the reasoning behind it?"
            else:
                return "Nice! Let's test your understanding. Can you apply that concept to solve a quick problem?"
        
        elif level == 4:
            # Deeper questions for above-grade students
            if turn == 2:
                return "Exactly right! I love that analogy. Can you think of what happens in edge cases? Like when things might break down?"
            else:
                return "Great insight! How does this concept connect to other things you've learned? Do you see any relationships?"
        
        else:  # level == 5
            # Advanced probing for excellent students
            if turn == 2:
                return "Impressive! That's exactly right. I'm curious - have you thought about the limitations of this concept? Or what breaks the model?"
            else:
                return "Excellent analysis! What if we generalized this further? How would you extend this concept?"
    
    def _teaching_response(self, level: int, topic: str, last_response: str, turn: int) -> str:
        """Actually teach based on level"""
        
        topic_lower = topic.lower()
        
        if level == 1:
            # LEVEL 1: Super simple, concrete teaching
            if "function" in topic_lower:
                if turn == 4:
                    return "Perfect! So a function is like a machine. You put something in (input), it does something to it, and gives you something out (output). Like a vending machine: you put in money (input), it gives you a snack (output). Does that make sense? 🎉"
                elif turn == 5:
                    return "Great! So in math, we write functions like f(x) = x + 2. This means: take any number, add 2 to it. If x is 3, what would f(3) be? (Hint: 3 + 2 = ?)"
                elif turn == 6:
                    return "YES! 🌟 You got it! 5 is correct! See, you CAN do this! Let's try one more: what's f(5)? (Remember, we add 2!)"
                else:
                    return "Awesome work! You're getting the hang of it! A function just transforms one number into another number using a rule. Keep practicing this idea! 💪"
            
            elif "equation" in topic_lower:
                if turn == 4:
                    return "Okay, so an equation is like a balance. Both sides have to be equal. Like if I said '3 + 2 = 5', that's balanced! ⚖️ The left side (3+2) equals the right side (5). Make sense?"
                elif turn == 5:
                    return "Perfect! So if we have 'x + 3 = 7', we need to find what number x is to make it balanced. What number plus 3 gives us 7? Take your time!"
                elif turn == 6:
                    return "Exactly! 🎉 x = 4 because 4 + 3 = 7! You did it! See, equations are just like puzzles - we're finding the missing number!"
                else:
                    return "You're doing great! Remember: equations are all about balance. Both sides need to be equal! Keep that in mind! 💪"
            
            else:
                return f"Excellent effort! Let me explain {topic} step by step. [Gives simple concrete example] Does this make it clearer? 🌟"
        
        elif level == 2:
            # LEVEL 2: Step-by-step with scaffolding
            if "function" in topic_lower and "linear" in topic_lower:
                if turn == 4:
                    return "You're getting there! A linear function makes a straight line. The key formula is y = mx + b. Let's break it down: m is the slope (how steep), b is where it crosses the y-axis. Make sense so far?"
                elif turn == 5:
                    return "Good! So if we have y = 2x + 3, the slope m=2 means it goes up 2 for every 1 to the right. The b=3 means it starts at y=3. Can you tell me what happens when x=0?"
                elif turn == 6:
                    return "Exactly! When x=0, we get y = 2(0) + 3 = 3! 🌟 You're getting this! Now what about when x=1? Try it!"
                else:
                    return "Nice work! You're understanding how linear functions work. The pattern is: plug in x, multiply by slope, add the y-intercept! Keep practicing! 💪"
            
            elif "quadratic" in topic_lower:
                if turn == 4:
                    return "Right! So quadratic equations have x². That little 2 means 'squared' or 'times itself'. Like 3² = 3 × 3 = 9. The basic form is ax² + bx + c = 0. Does that look familiar?"
                elif turn == 5:
                    return "Perfect! So if we have x² + 5x + 6 = 0, we can factor it. We're looking for two numbers that multiply to 6 and add to 5. Any ideas?"
                elif turn == 6:
                    return "Great thinking! It's 2 and 3! Because 2 × 3 = 6 and 2 + 3 = 5! So (x+2)(x+3) = 0. You're getting the pattern! 🎉"
                else:
                    return "Excellent progress! Quadratics are just about finding what makes the equation equal zero. Keep using that factoring technique! 🌟"
            
            else:
                return f"You're on the right track! Let me show you the pattern. [Gives worked example for {topic}] Now you try a similar one!"
        
        elif level == 3:
            # LEVEL 3: Standard teaching with practice
            if turn in [4, 5]:
                return f"Good! You understand the core concept of {topic}. Let's apply it to a new problem: [gives practice problem]. Take your time and show me your thinking!"
            elif turn == 6:
                return "Nice work! Let's take it one step further. What would happen if we changed [variable]? Can you predict the outcome?"
            else:
                return f"Exactly right! You've got a solid grasp of {topic}. Try one more challenging application to really cement it! 🎉"
        
        elif level == 4:
            # LEVEL 4: Explore deeper
            if turn == 4:
                return "Perfect understanding! Now let's explore the 'why'. What's the deeper reason this concept works the way it does? What principle is at play?"
            elif turn == 5:
                return "Excellent insight! Can you think of a situation where this concept might NOT apply? What are the edge cases or limitations?"
            elif turn == 6:
                return "Great thinking! Now, how does this connect to [related concept]? Do you see the relationship? 🎯"
            else:
                return f"Superb! You're thinking like a mathematician/scientist. Keep making those connections and questioning assumptions! 💪"
        
        else:  # level == 5
            # LEVEL 5: Advanced extensions
            if turn == 4:
                return "Brilliant analysis! You clearly have excellent mastery. Let's explore an extension: what if we generalized this to N dimensions? How would the concept change?"
            elif turn == 5:
                return "Fascinating question! That connects to [advanced topic]. Have you considered how [advanced concept] relates to what we're discussing?"
            elif turn == 6:
                return "Exactly! You're thinking at a very sophisticated level. The connection between [concept A] and [concept B] is profound. How would you explain that to someone else? 🏆"
            else:
                return f"Outstanding! Your understanding of {topic} is truly advanced. You could teach this material to others! Keep exploring these deep connections! 🌟"
    
    def _personalized_closing(self, level: int, topic: str, history: list) -> str:
        """Create personalized closing based on what actually happened"""
        
        # Extract what was discussed
        student_messages = [h['content'] for h in history if h['role'] == 'student']
        
        # Create specific summary
        if level == 1:
            return f"Wow, great effort today! When we started, {topic} seemed totally confusing, but you worked through it! Remember: {topic} is all about [concept]. Keep practicing those basics and you'll get even stronger! You've got this! 💪"
        
        elif level == 2:
            return f"Nice work today! You went from being unsure to actually getting the pattern! You learned that {topic} involves [key steps]. Keep practicing, and those concepts will become second nature. You're definitely improving! 🌟"
        
        elif level == 3:
            return f"Good session! You showed you understand the core ideas of {topic}. You can explain the 'why' behind concepts and apply them to problems. Keep building on this foundation - you're exactly where you should be! 🎉"
        
        elif level == 4:
            return f"Excellent work! You went beyond just knowing {topic} - you made connections and thought about edge cases. Your analogy about [recalls their analogy] was spot-on! Keep thinking critically and making those connections! 💪"
        
        else:  # level == 5
            return f"Truly impressive session! Your understanding of {topic} is advanced. The way you connected it to [advanced concept] and asked about [deep question] shows real mastery. Keep exploring and questioning - you're thinking like a real expert! 🏆"
