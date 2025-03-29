import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any, List, Tuple
import time
import json  # Add this import
import random  # Add this import

# Load environment variables
load_dotenv()

class OpenAIProxy:
    """
    A proxy service to interact with OpenAI API for generating interview questions,
    follow-ups, and evaluating candidate responses.
    """
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_url = 'https://api.openai.com/v1/chat/completions'
        self.model = 'gpt-3.5-turbo-0125'  # You can change this to a different model
        self.conversation_histories = {}
        
    def get_response(self, user_id, message, system_prompt=None, conversation_context=None):
        """
        Get a response from OpenAI API for the given message.
        
        Args:
            user_id (str): Unique identifier for the interview session
            message (str): User's message or context for question generation
            system_prompt (str, optional): System prompt to guide AI behavior
            conversation_context (dict, optional): Additional context about the conversation
            
        Returns:
            str: AI response
        """
        if not system_prompt:
            system_prompt = "You are an AI interview agent conducting a technical interview. Ask relevant questions and provide constructive feedback."
        
        # Initialize conversation history for new users
        if user_id not in self.conversation_histories:
            self.conversation_histories[user_id] = []
        
        # Prepare the full message with any additional context
        full_message = message
        if conversation_context:
            context_str = "\n\nAdditional context:\n"
            for key, value in conversation_context.items():
                context_str += f"- {key}: {value}\n"
            full_message += context_str
        
        # Add user message to history
        self.conversation_histories[user_id].append({
            'role': 'user',
            'content': full_message
        })
        
        # Prepare messages for OpenAI API
        messages = [
            {'role': 'system', 'content': system_prompt},
            *self.conversation_histories[user_id][-10:]  # Keep last 10 messages
        ]
        
        try:
            # Call OpenAI API
            response = requests.post(
                self.api_url,
                json={
                    'model': self.model,
                    'messages': messages,
                    'temperature': 0.7,
                    'max_tokens': 500
                },
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
            )
            
            response_data = response.json()
            
            if 'choices' in response_data and len(response_data['choices']) > 0:
                ai_response = response_data['choices'][0]['message']['content']
                
                # Add AI response to conversation history
                self.conversation_histories[user_id].append({
                    'role': 'assistant',
                    'content': ai_response
                })
                
                return ai_response
            else:
                error_msg = f"Invalid response from OpenAI API: {response_data}"
                print(error_msg)
                return "I'm having trouble generating a proper response right now."
        
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            return "I encountered an issue while processing your request."
        
    def process_candidate_response(self, response: str) -> Dict[str, Any]:
        """
        Process the candidate's response and get the next question.
        
        Args:
            response: The candidate's response.
            
        Returns:
            Dictionary with next question, interview status, and remaining time.
        """
        if not self.interview_in_progress:
            raise ValueError("Interview is not in progress.")
        
        if self.debug_mode:
            print(f"Processing candidate response: {response[:50]}...")
        
        # Check if we've exceeded the time limit
        time_exceeded, remaining_seconds = self.check_time_limit()
        if time_exceeded:
            self.interview_in_progress = False
            self.interview_complete = True
            self.interview_end_time = time.time()
            self.interview_duration = self.interview_end_time - self.interview_start_time
            
            # Generate a time-exceeded conclusion
            conclusion = self._generate_time_exceeded_conclusion()
            
            # Get interview summary
            self.interview_summary = self.conversation_manager.get_interview_summary()
            
            # Save the report automatically
            self.save_interview_report()
            
            if self.debug_mode:
                print("Interview completed due to time limit")
                print(f"Duration: {self.interview_duration/60:.1f} minutes")
                    
            return {
                "next_question": conclusion,
                "is_complete": True,
                "remaining_seconds": 0,
                "time_limit_exceeded": True
            }
        conversation_result = self.conversation_manager.process_candidate_response(response)
        
        # Process the response normally
        if isinstance(conversation_result, tuple):
                if len(conversation_result) == 2:
                    next_question, is_complete = conversation_result
                elif len(conversation_result) == 3:
                    next_question, is_complete, _ = conversation_result  # Ignore the third value
                else:
                    raise ValueError(f"Unexpected return format from conversation manager: {conversation_result}")
        else:
                raise ValueError(f"Unexpected return type from conversation manager: {type(conversation_result)}")
        
        # Extract values from the result dictionary
        next_question = result.get("next_question")
        is_complete = result.get("is_complete")
        remaining_seconds = result.get("remaining_seconds", None)
        time_limit_exceeded = result.get("time_limit_exceeded", False)
        
        if is_complete:
            self.interview_in_progress = False
            self.interview_complete = True
            self.interview_end_time = time.time()
            self.interview_duration = self.interview_end_time - self.interview_start_time
            self.interview_summary = self.conversation_manager.get_interview_summary()
            
            # Save the report automatically
            self.save_interview_report()
            
            if self.debug_mode:
                print("Interview complete")
                print(f"Duration: {self.interview_duration/60:.1f} minutes")
                print(f"Overall score: {self.interview_summary.get('overall_score', 0):.1f}")
                print(f"Recommendation: {self.interview_summary.get('recommendation', 'Unknown')}")
        else:
            if self.debug_mode:
                print(f"Next question: {next_question}")
                if self.interview_max_duration:
                    print(f"Remaining time: {remaining_seconds//60} minutes, {remaining_seconds%60} seconds")
        
        return {
            "next_question": next_question,
            "is_complete": is_complete,
            "remaining_seconds": remaining_seconds,
            "time_limit_exceeded": time_limit_exceeded
        }
    
    def generate_interview_question(self, interview_id, question_type, job_info, candidate_info=None):
        """
        Generate an interview question based on the job and candidate information.
        
        Args:
            interview_id (str): Unique identifier for the interview session
            question_type (str): Type of question to generate (technical, behavioral, etc.)
            job_info (dict): Information about the job
            candidate_info (dict, optional): Information about the candidate
            
        Returns:
            str: Generated interview question
        """
        prompt = f"Generate a {question_type} interview question for a {job_info.get('title', 'job')} position."
        
        # Add more context based on the question type
        if question_type == 'technical':
            if 'skills' in job_info:
                prompt += f" The required skills are: {', '.join(job_info.get('skills', []))}."
        elif question_type == 'behavioral':
            prompt += " Focus on how the candidate has handled past situations."
        elif question_type == 'company_culture':
            if 'core_values' in job_info:
                prompt += f" Our company values are: {', '.join(job_info.get('core_values', []))}."
        
        # Add candidate context if available
        context = {}
        if candidate_info:
            context['candidate_skills'] = candidate_info.get('skills', [])
            context['candidate_experience'] = candidate_info.get('experience', [])
        
        return self.get_response(interview_id, prompt, system_prompt="You are an expert technical interviewer. Generate only the interview question without any additional text or explanations.", conversation_context=context)
    
    def generate_follow_up_question(self, interview_id, question_type, original_question, candidate_response):
        """
        Generate a follow-up question based on the candidate's response.
        
        Args:
            interview_id (str): Unique identifier for the interview session
            question_type (str): Type of the original question
            original_question (str): The original question asked
            candidate_response (str): The candidate's response
            
        Returns:
            str: Generated follow-up question
        """
        prompt = f"""
Original {question_type} question: "{original_question}"

Candidate response: "{candidate_response}"

Generate a follow-up question that probes deeper into the candidate's response.
"""
        
        return self.get_response(interview_id, prompt, system_prompt="You are an expert technical interviewer. Generate only the follow-up question without any additional text or explanations.")
    
    def evaluate_response(self, interview_id, question_type, question, response, job_info):
        """
        Evaluate the candidate's response and provide a score and analysis.
        
        Args:
            interview_id (str): Unique identifier for the interview session
            question_type (str): Type of question asked
            question (str): The question asked
            response (str): The candidate's response
            job_info (dict): Information about the job
            
        Returns:
            dict: Evaluation results including score and analysis
        """
        prompt = f"""
Question type: {question_type}
Question: "{question}"
Candidate response: "{response}"

Evaluate the candidate's response on a scale of 1-5 for relevance, completeness, and accuracy.
Provide a brief analysis of the strengths and weaknesses of the response.

The job requires these skills: {', '.join(job_info.get('skills', []))}
Job responsibilities include: {', '.join(job_info.get('responsibilities', []))}
"""
        
        eval_response = self.get_response(interview_id, prompt, system_prompt="You are an expert at evaluating interview responses. Provide a JSON object with 'score' (number 1-5) and 'analysis' (string).")
        
        try:
            # Try to parse as JSON
            eval_data = json.loads(eval_response)
            return eval_data
        except json.JSONDecodeError:
            # If response is not valid JSON, extract score using simple heuristics
            if "score: " in eval_response.lower():
                score_text = eval_response.lower().split("score: ")[1].split("\n")[0]
                try:
                    score = float(score_text.strip())
                except ValueError:
                    score = 3.0  # Default score
            else:
                score = 3.0  # Default score
                
            return {
                "score": score,
                "analysis": eval_response
            }
    
    def clear_history(self, user_id):
        """Clear conversation history for a user"""
        if user_id in self.conversation_histories:
            del self.conversation_histories[user_id]
            return True
        return False

# --------- UPDATED CONVERSATION MANAGER ---------

class ConversationManager:
    
    """
    Manage the interview conversation flow, track state,
    and generate appropriate responses.
    """
    
    def __init__(self, question_generator, job_info, company_info, candidate_info, match_analysis):
        """
        Initialize the conversation manager with job and candidate information.
        
        Args:
            question_generator: Instance of QuestionGenerator
            job_info: Processed job information
            company_info: Processed company information
            candidate_info: Processed candidate information
            match_analysis: Analysis of candidate's match to job requirements
        """
        self.question_generator = question_generator
        self.job_info = job_info
        self.company_info = company_info
        self.candidate_info = candidate_info
        self.match_analysis = match_analysis
        
        # Initialize OpenAI proxy
        self.openai_proxy = OpenAIProxy()
        
        # Generate interview script - You can use either your existing method or use OpenAI
        self.interview_script = question_generator.generate_interview_script(
            job_info, company_info, candidate_info, match_analysis
        )
        
        # Conversation state
        self.current_question_index = 0
        self.conversation_history = []
        self.follow_up_status = False
        self.current_question_type = None
        self.current_question = None
        
        # Tracking previous questions to avoid repetition
        self.asked_questions = set()
        self.asked_follow_ups = set()
        self.previous_topics = []
        
        # Context tracking
        self.current_context = None

        self.debug_mode = False

        # Interview state
        self.interview_in_progress = True
        self.interview_complete = False
        self.interview_summary = None
        self.interview_start_time = None
        self.interview_end_time = None
        self.interview_duration = None
        self.interview_max_duration = None  # In minutes
        
        
        # Candidate response evaluation
        self.candidate_evaluation = {
            'technical_score': 0,
            'cultural_fit_score': 0,
            'communication_score': 0,
            'experience_relevance_score': 0,
            'skill_match_score': 0,
            'question_count': 0,
            'notes': []
        }
        
        # Create a unique interview ID
        self.interview_id = f"interview_{time.time()}"

    def check_time_limit(self) -> Tuple[bool, int]:
        """
        Check if the interview has exceeded its time limit.
        
        Returns:
            Tuple of (time_exceeded, remaining_seconds)
        """
        if not self.interview_in_progress or not self.interview_max_duration or not self.interview_start_time:
            return False, None
            
        elapsed_seconds = time.time() - self.interview_start_time
        elapsed_minutes = elapsed_seconds / 60
        
        remaining_seconds = max(0, (self.interview_max_duration * 60) - elapsed_seconds)
        
        if elapsed_minutes >= self.interview_max_duration:
            return True, 0
        else:
            return False, int(remaining_seconds)

    def process_candidate_response(self, response: str) -> Dict[str, Any]:
        """
        Process the candidate's response and determine the next question.
        
        Args:
            response: The candidate's response to the current question.
            
        Returns:
            Dict[str, Any]: A dictionary containing:
                - next_question (str): The next question to ask.
                - is_complete (bool): Whether the interview is complete.
                - remaining_seconds (int): Remaining time in seconds.
                - time_limit_exceeded (bool): Whether the time limit has been exceeded.
        """
        if not self.interview_in_progress:
            raise ValueError("Interview is not in progress.")
        
        if self.debug_mode:
            print(f"Processing candidate response: {response[:50]}...")
        
        # Check if we've exceeded the time limit
        time_exceeded, remaining_seconds = self.check_time_limit()
        if time_exceeded:
            self.interview_in_progress = False
            self.interview_complete = True
            self.interview_end_time = time.time()
            self.interview_duration = self.interview_end_time - self.interview_start_time
            
            # Generate a time-exceeded conclusion
            conclusion = self._generate_time_exceeded_conclusion()
            
            # Get interview summary
            
            self.interview_summary = self.get_interview_summary()
            
            # Save the report automatically
            self.save_interview_report()
            
            if self.debug_mode:
                print("Interview completed due to time limit")
                print(f"Duration: {self.interview_duration/60:.1f} minutes")
            
            return {
                "next_question": conclusion,
                "is_complete": True,
                "remaining_seconds": 0,
                "time_limit_exceeded": True
            }
        
        # Process the response normally
        next_question, is_complete = self._process_response_and_get_next_question(response)
        
        return {
            "next_question": next_question,
            "is_complete": is_complete,
            "remaining_seconds": remaining_seconds if self.interview_max_duration else None,
            "time_limit_exceeded": False
        }
    
    def _process_response_and_get_next_question(self, response: str) -> Tuple[str, bool]:
        """
        Helper method to process the candidate's response and determine the next question.
        
        Args:
            response: The candidate's response to the current question
            
        Returns:
            Tuple of (next_question, is_interview_complete)
        """
        # Record candidate response
        self.conversation_history.append({
            'speaker': 'candidate',
            'text': response,
            'timestamp': time.time(),
            'in_response_to': self.current_question_type
        })
        
        # Debugging: Check current state
        print(f"DEBUG: current_question_index={self.current_question_index}, interview_script_length={len(self.interview_script)}")
        
        # Check if we've reached the end of the script
        if self.current_question_index >= len(self.interview_script) - 1:
            print("DEBUG: Reached the end of the interview script.")
            return self._generate_interview_conclusion(), True
        
        # Increment question index and get the next question
        self.current_question_index += 1
        next_question_data = self.interview_script[self.current_question_index]
        next_question = next_question_data['question']
        
        # Update current question type and context
        self.current_question_type = next_question_data['type']
        self.current_context = {
            'topic': self.current_question_type,
            'focus': self._extract_topic_keywords(next_question)
        }
        
        # Record next question
        self.conversation_history.append({
            'speaker': 'interviewer',
            'text': next_question,
            'timestamp': time.time(),
            'question_type': self.current_question_type
        })
        
        return next_question, False
    
    def start_interview(self) -> str:
        """
        Start the interview with the first question.
        
        Returns:
            The first question to ask the candidate
        """
        if not self.interview_script:
            return "I don't have any questions prepared for this interview."
        
        question_data = self.interview_script[self.current_question_index]
        self.current_question_type = question_data['type']
        
        # Option to use OpenAI to enhance or rephrase the question
        original_question = question_data['question']
        enhanced_prompt = f"""
Rephrase this {self.current_question_type} interview question to make it more engaging and natural:
"{original_question}"

Include specific details from the job description where relevant.
"""
        
        try:
            # Try to enhance the question with OpenAI
            self.current_question = self.openai_proxy.get_response(
                self.interview_id, 
                enhanced_prompt,
                system_prompt="You are an expert technical interviewer. Respond only with the rephrased question."
            )
            
            # Fallback to original if OpenAI fails or returns something strange
            if not self.current_question or len(self.current_question) < 10:
                self.current_question = original_question
        except Exception:
            # Fallback to original question if there's any error
            self.current_question = original_question
        
        # Record in conversation history
        self.conversation_history.append({
            'speaker': 'interviewer',
            'text': self.current_question,
            'timestamp': time.time(),
            'question_type': self.current_question_type
        })
        
        # Add to asked questions
        self.asked_questions.add(self._normalize_question(self.current_question))
        self.current_context = {'topic': self.current_question_type, 'focus': self._extract_topic_keywords(self.current_question)}
        
        return self.current_question
    
    def _normalize_question(self, question: str) -> str:
        # Simple normalization - lowercase and remove punctuation
        normalized = question.lower()
        for char in '.,?!;:':
            normalized = normalized.replace(char, '')
        return normalized
    
    def _generate_contextual_follow_up(self, response: str) -> str:
        """
        Generate a follow-up question that considers conversation context.
        
        Args:
            response: The candidate's response
            
        Returns:
            A contextually appropriate follow-up question
        """
        # Use OpenAI to generate a more contextual follow-up
        try:
            follow_up = self.openai_proxy.generate_follow_up_question(
                self.interview_id,
                self.current_question_type,
                self.current_question,
                response
            )
            
            # If we got a valid response, return it
            if follow_up and len(follow_up) > 10:
                return follow_up
        except Exception as e:
            print(f"Error generating follow-up with OpenAI: {str(e)}")
            
        # Fallback to original method if OpenAI fails
        base_follow_up = self.question_generator.generate_follow_up_question(
            self.current_question_type,
            self.current_question,
            response
        )
        
        # Check if this follow-up is repetitive
        if self._normalize_question(base_follow_up) in self.asked_follow_ups:
            # Try to generate a more contextual follow-up using the original method
            
            # Key phrases that might appear in the response
            interesting_phrases = [
                "challenge", "problem", "success", "learn", "difficult",
                "change", "improve", "team", "process", "approach",
                "solution", "result", "impact", "stakeholder", "customer"
            ]
            
            # Check if any interesting phrases are in the response
            found_phrases = [phrase for phrase in interesting_phrases if phrase in response.lower()]
            
            if found_phrases:
                # Use the first found phrase to generate a more specific follow-up
                topic = found_phrases[0]
                
                contextual_follow_ups = {
                    "challenge": "What specific strategies did you use to overcome that challenge?",
                    "problem": "How did you identify the root cause of that problem?",
                    "success": "What factors do you think were most critical to that success?",
                    "learn": "How have you applied that learning in subsequent situations?",
                    "difficult": "How did that difficult situation affect your approach to similar scenarios?",
                    "change": "What was the most significant impact of that change?",
                    "improve": "Can you quantify the results of that improvement?",
                    "team": "How did you ensure everyone on the team was aligned with that approach?",
                    "process": "What metrics did you use to evaluate the effectiveness of that process?",
                    "approach": "What alternatives did you consider before choosing that approach?",
                    "solution": "How did you validate that the solution would meet all requirements?",
                    "result": "How did those results compare to your initial expectations?",
                    "impact": "How did you communicate that impact to stakeholders?",
                    "stakeholder": "How did you manage differing priorities among stakeholders?",
                    "customer": "How did you gather and incorporate customer feedback?"
                }
                
                if topic in contextual_follow_ups:
                    return contextual_follow_ups[topic]
        
        # If no contextual follow-up was generated, return the base follow-up
        return base_follow_up
    
    def _extract_topic_keywords(self, text: str) -> List[str]:
        # Simple keyword extraction
        keywords = []
        # Common keywords for different question types
        topic_keywords = {
            'technical': ['code', 'debug', 'develop', 'architecture', 'design', 'algorithm', 'testing'],
            'experience': ['experience', 'project', 'role', 'job', 'responsibility', 'team'],
            'behavioral': ['situation', 'challenge', 'problem', 'conflict', 'difficult', 'success'],
            'skill': ['skill', 'proficiency', 'expertise', 'knowledge', 'ability'],
            'company_culture': ['value', 'culture', 'mission', 'vision', 'belief']
        }
        
        # Extract any matching keywords
        text_lower = text.lower()
        for category, words in topic_keywords.items():
            for word in words:
                if word in text_lower:
                    keywords.append(word)
        
        return keywords
       
    

        
    def _evaluate_response(self, response: str) -> None:
        """
        Evaluate the candidate's response and update evaluation scores.
        
        Args:
            response: The candidate's response to the current question
        """
        # Option to use OpenAI for evaluation
        try:
            openai_evaluation = self.openai_proxy.evaluate_response(
                self.interview_id,
                self.current_question_type,
                self.current_question,
                response,
                self.job_info
            )
            
            # If we got a valid evaluation, use it to supplement our scoring
            if openai_evaluation and 'score' in openai_evaluation:
                # Scale from 1-5 to 0-1
                ai_score = (openai_evaluation['score'] - 1) / 4
                
                # Add the note if provided
                if 'analysis' in openai_evaluation and openai_evaluation['analysis']:
                    self.candidate_evaluation['notes'].append(openai_evaluation['analysis'])
                
                # Don't evaluate if no response or very short response
                if not response or len(response) < 10:
                    return
                
                # Increment question count
                self.candidate_evaluation['question_count'] += 1
                
                # Update scores based on question type and AI evaluation
                if self.current_question_type == 'technical':
                    self.candidate_evaluation['technical_score'] += ai_score
                    
                elif self.current_question_type == 'company_culture':
                    self.candidate_evaluation['cultural_fit_score'] += ai_score
                    
                elif self.current_question_type in ['skill', 'missing_skill']:
                    self.candidate_evaluation['skill_match_score'] += ai_score
                    
                elif self.current_question_type == 'experience':
                    self.candidate_evaluation['experience_relevance_score'] += ai_score
                
                # Communication score applies to all question types
                self.candidate_evaluation['communication_score'] += ai_score
                
                # Early return since we've handled the evaluation
                return
        except Exception as e:
            # If OpenAI evaluation fails, fall back to the original method
            print(f"Error using OpenAI for evaluation: {str(e)}")
        
        # Original evaluation method as fallback
        # Simple heuristics for evaluation
        # In a real implementation, this would use more sophisticated NLP
        
        # Don't evaluate if no response or very short response
        if not response or len(response) < 10:
            return
        
       
        # Increment question count
        self.candidate_evaluation['question_count'] += 1
        
        # Basic response quality indicators
        response_length = len(response)
        specific_details = any(term in response.lower() for term in 
                              ['specifically', 'example', 'instance', 'case', 'project', 'situation'])
        quantifiable_results = any(term in response.lower() for term in 
                                  ['percent', '%', 'increase', 'decrease', 'reduced', 'improved', 'saved', 'generated'])
        
        # Check for communication quality
        clear_communication = response_length > 100 and response_length < 500
        structured_response = any(term in response.lower() for term in 
                                 ['first', 'second', 'finally', 'additionally', 'however', 'therefore'])
        
        # Update scores based on question type
        if self.current_question_type == 'technical':
            technical_terms_count = sum(1 for skill in self.job_info.get('skills', []) 
                                      if skill.lower() in response.lower())
            technical_score = min(5, 2 + technical_terms_count + specific_details * 1 + quantifiable_results * 1) / 5
            self.candidate_evaluation['technical_score'] += technical_score
            
            if technical_score >= 0.8:
                self.candidate_evaluation['notes'].append(f"Strong technical knowledge demonstrated in response to: {self.current_question[:50]}...")
            elif technical_score <= 0.4:
                self.candidate_evaluation['notes'].append(f"Limited technical knowledge in response to: {self.current_question[:50]}...")
        
        elif self.current_question_type == 'company_culture':
            culture_match = any(value.lower() in response.lower() for value in self.company_info.get('core_values', []))
            mission_match = any(word.lower() in response.lower() for word in self.company_info.get('mission', '').split() 
                              if len(word) > 4)
            
            culture_score = min(5, 2 + culture_match * 1.5 + mission_match * 1.5) / 5
            self.candidate_evaluation['cultural_fit_score'] += culture_score
            
            if culture_score >= 0.8:
                self.candidate_evaluation['notes'].append("Shows strong alignment with company values and mission")
            elif culture_score <= 0.4:
                self.candidate_evaluation['notes'].append("Limited demonstration of alignment with company culture")
        
        elif self.current_question_type in ['skill', 'missing_skill']:
            skill_terms = sum(1 for skill in self.job_info.get('skills', []) 
                             if skill.lower() in response.lower())
            
            skill_score = min(5, 2 + skill_terms + specific_details * 1 + quantifiable_results * 1) / 5
            self.candidate_evaluation['skill_match_score'] += skill_score
            
            if self.current_question_type == 'missing_skill' and skill_score >= 0.6:
                self.candidate_evaluation['notes'].append(f"Demonstrated knowledge in missing skill area: {self.current_question.split()[0]}")
        
        elif self.current_question_type == 'experience':
            # Check if their experience relates to job responsibilities
            relevance_count = sum(1 for resp in self.job_info.get('responsibilities', [])
                                if any(word.lower() in response.lower() for word in resp.split() if len(word) > 4))
            
            relevance_score = min(5, 2 + relevance_count * 0.5 + specific_details * 1 + quantifiable_results * 1) / 5
            self.candidate_evaluation['experience_relevance_score'] += relevance_score
            
            if relevance_score >= 0.8:
                self.candidate_evaluation['notes'].append("Past experience highly relevant to role requirements")
            elif relevance_score <= 0.4:
                self.candidate_evaluation['notes'].append("Limited relevance of past experience to this role")
        
        # Communication score applies to all question types
        communication_score = min(5, 2 + clear_communication * 1 + structured_response * 1 + specific_details * 1) / 5
        self.candidate_evaluation['communication_score'] += communication_score
    
    def _generate_interview_conclusion(self) -> str:
        """
        Generate a conclusion for the interview.
        
        Returns:
            Conclusion text
        """
        candidate_name = self.candidate_info.get('name', 'there')
        job_title = self.job_info.get('title', 'this position')
        
        conclusion_templates = [
            f"Thank you, {candidate_name}, for taking the time to interview for the {job_title} role today. "
            f"We've covered a lot of ground, and I appreciate your thoughtful responses. "
            f"Our team will review your candidacy and get back to you within the next week regarding next steps. "
            f"Do you have any final questions before we wrap up?",
            
            f"That concludes the formal part of our interview, {candidate_name}. "
            f"I've enjoyed learning more about your background and how you might contribute to our team in the {job_title} role. "
            f"We'll be in touch soon with feedback and any next steps. "
            f"Is there anything else you'd like to know about the role or our company?",
            
            f"We've come to the end of our scheduled time, {candidate_name}. "
            f"Thank you for sharing your experiences and insights related to the {job_title} position. "
            f"Our hiring team will evaluate all candidates and reach out to you shortly. "
            f"Before we end, do you have any remaining questions about the role or what it's like to work here?"
        ]
        
        return random.choice(conclusion_templates)
    
    def get_interview_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of the interview.
        
        Returns:
            Dictionary with interview summary information
        """
        # Calculate overall score (weighted average)
        weights = {
            'technical_score': 0.25,
            'cultural_fit_score': 0.2,
            'communication_score': 0.15,
            'experience_relevance_score': 0.25,
            'skill_match_score': 0.15
        }
        
        if self.candidate_evaluation['question_count'] == 0:
            overall_score = 0
        else:
            overall_score = sum(
                self.candidate_evaluation[key] * weight 
                for key, weight in weights.items()
            ) / self.candidate_evaluation['question_count']
            # Normalize to 0-100 scale
            overall_score = min(100, overall_score * 20)
        
        # Generate strengths and areas for improvement
        strengths = []
        improvements = []
        
        scores = {
            'technical_score': ('Technical knowledge', 'technical expertise'),
            'cultural_fit_score': ('Cultural fit', 'alignment with company values'),
            'communication_score': ('Communication skills', 'communication ability'),
            'experience_relevance_score': ('Relevant experience', 'experience directly related to this role'),
            'skill_match_score': ('Skill match', 'specific skills required for this position')
        }
        
        for score_key, (strength_text, improvement_text) in scores.items():
            normalized_score = self.candidate_evaluation[score_key] * 20  # Scale to 0-100
            if normalized_score >= 75:  # Strong areas
                strengths.append(strength_text)
            elif normalized_score <= 50:  # Areas for improvement
                improvements.append(improvement_text)
        
        # Recommendation based on overall score
        recommendation = 'Reject'
        if overall_score >= 85:
            recommendation = 'Strong Hire'
        elif overall_score >= 70:
            recommendation = 'Hire'
        elif overall_score >= 60:
            recommendation = 'Consider with Reservations'
        
        return {
            'candidate_name': self.candidate_info.get('name', 'Candidate'),
            'job_title': self.job_info.get('title', 'Position'),
            'interview_date': time.strftime('%Y-%m-%d'),
            'overall_score': round(overall_score, 1),
            'technical_score': round(self.candidate_evaluation['technical_score'] * 20, 1),
            'cultural_fit_score': round(self.candidate_evaluation['cultural_fit_score'] * 20, 1),
            'communication_score': round(self.candidate_evaluation['communication_score'] * 20, 1),
            'experience_relevance_score': round(self.candidate_evaluation['experience_relevance_score'] * 20, 1),
            'skill_match_score': round(self.candidate_evaluation['skill_match_score'] * 20, 1),
            'strengths': strengths,
            'areas_for_improvement': improvements,
            'recommendation': recommendation,
            'notes': self.candidate_evaluation['notes'],
            'skill_match_percentage': self.match_analysis.get('skill_match_percentage', 0),
            'conversation_transcript': self.conversation_history
        }