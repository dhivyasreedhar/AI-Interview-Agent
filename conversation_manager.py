from typing import Dict, List, Any, Optional, Tuple, Set
import time
import json
import random

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
        
        # Generate interview script
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
        self.current_question = question_data['question']
        
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
        """
        Normalize a question to help identify similar questions.
        
        Args:
            question: The question text
            
        Returns:
            Normalized question text for comparison
        """
        # Simple normalization - lowercase and remove punctuation
        normalized = question.lower()
        for char in '.,?!;:':
            normalized = normalized.replace(char, '')
        return normalized
    
    def _extract_topic_keywords(self, text: str) -> List[str]:
        """
        Extract key topic words from text.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of key topic words
        """
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
    
    def _is_similar_question(self, question1: str, question2: str) -> bool:
        """
        Check if two questions are similar to avoid repetition.
        
        Args:
            question1: First question
            question2: Second question
            
        Returns:
            True if questions are similar, False otherwise
        """
        # Normalize both questions
        q1 = self._normalize_question(question1)
        q2 = self._normalize_question(question2)
        
        # Check for high similarity
        # 1. Check if they're asking about the same general thing
        q1_keywords = self._extract_topic_keywords(q1)
        q2_keywords = self._extract_topic_keywords(q2)
        
        # If they share multiple keywords, they might be similar
        common_keywords = set(q1_keywords) & set(q2_keywords)
        if len(common_keywords) >= 2:
            return True
            
        # 2. Check for similarity in the question text
        # This is a simple check - in a real system, you might use more sophisticated
        # text similarity algorithms
        if q1[:20] == q2[:20]:  # If the first 20 chars match
            return True
            
        return False
    
    def process_candidate_response(self, response: str) -> Tuple[str, bool]:
        """
        Process the candidate's response and determine the next question.
        
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
        
        # Update context with response content
        response_keywords = self._extract_topic_keywords(response)
        if self.current_context:
            self.current_context['response_keywords'] = response_keywords
        
        # Save the current topic to previous topics list
        if self.current_context:
            self.previous_topics.append(self.current_context)
        
        # Evaluate candidate response
        self._evaluate_response(response)
        
        # Determine if we should ask a follow-up or move to the next question
        if not self.follow_up_status and random.random() < 0.3:  # 30% chance of follow-up
            # Generate follow-up that considers context
            follow_up = self._generate_contextual_follow_up(response)
            
            if follow_up:
                self.follow_up_status = True
                
                # Record follow-up question
                self.conversation_history.append({
                    'speaker': 'interviewer',
                    'text': follow_up,
                    'timestamp': time.time(),
                    'question_type': 'follow_up',
                    'parent_type': self.current_question_type
                })
                
                # Add to asked follow-ups
                self.asked_follow_ups.add(self._normalize_question(follow_up))
                
                return follow_up, False
        
        # Reset follow-up status and move to the next question
        self.follow_up_status = False
        
        # Find the next non-repetitive question
        next_question = None
        next_question_data = None
        attempts = 0
        max_attempts = len(self.interview_script)
        
        while attempts < max_attempts:
            self.current_question_index += 1
            
            # Check if we've reached the end of the script
            if self.current_question_index >= len(self.interview_script):
                return self._generate_interview_conclusion(), True
            
            next_question_data = self.interview_script[self.current_question_index]
            next_question = next_question_data['question']
            
            # Check if this is a repetitive question
            is_repetitive = any(self._is_similar_question(next_question, asked) for asked in self.asked_questions)
            
            if not is_repetitive:
                break
                
            attempts += 1
        
        # Update current question
        self.current_question_type = next_question_data['type']
        self.current_question = next_question
        
        # Update context
        self.current_context = {
            'topic': self.current_question_type,
            'focus': self._extract_topic_keywords(self.current_question)
        }
        
        # Record next question
        self.conversation_history.append({
            'speaker': 'interviewer',
            'text': self.current_question,
            'timestamp': time.time(),
            'question_type': self.current_question_type
        })
        
        # Add to asked questions
        self.asked_questions.add(self._normalize_question(self.current_question))
        
        return self.current_question, False
    
    def _generate_contextual_follow_up(self, response: str) -> str:
        """
        Generate a follow-up question that considers conversation context.
        
        Args:
            response: The candidate's response
            
        Returns:
            A contextually appropriate follow-up question
        """
        # First, get a candidate follow-up from the question generator
        base_follow_up = self.question_generator.generate_follow_up_question(
            self.current_question_type,
            self.current_question,
            response
        )
        
        # Check if this follow-up is repetitive
        if self._normalize_question(base_follow_up) in self.asked_follow_ups:
            # Try to generate a more contextual follow-up
            
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
        
    def _evaluate_response(self, response: str) -> None:
        """
        Evaluate the candidate's response and update evaluation scores.
        
        Args:
            response: The candidate's response to the current question
        """
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