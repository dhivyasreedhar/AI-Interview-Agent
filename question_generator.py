from typing import Dict, List, Any, Set
import random
import re

class QuestionGenerator:
    """
    Generate personalized interview questions based on job post, 
    company profile, and candidate resume.
    """
    
    def __init__(self):
        # Templates for different question types
        self.introduction_templates = [
            "Hello {candidate_name}, thanks for joining us today to discuss the {job_title} position at our company. Could you start by telling me a bit about yourself and why you're interested in this role?",
            "Welcome, {candidate_name}. I'm excited to learn more about you for the {job_title} position. Can you briefly introduce yourself and share what attracted you to this opportunity?",
            "Hi {candidate_name}, thank you for your interest in the {job_title} role. Let's start by having you tell me about your background and what excites you about this position."
        ]
        
        self.experience_templates = [
            "I see you've worked at {company} as a {title}. Could you tell me about your main responsibilities there and how they relate to our {job_title} position?",
            "Your experience at {company} looks interesting. What were some of the key challenges you faced in your role as {title}, and how did you overcome them?",
            "Can you elaborate on your time at {company}? What specific skills or lessons did you develop there that you believe would be valuable for our {job_title} role?"
        ]
        
        self.skill_templates = [
            "I see {skill} listed on your resume. Could you tell me about a specific project where you applied this skill?",
            "How would you rate your proficiency in {skill} on a scale of 1-10, and why? Can you give an example of how you've used it in your work?",
            "You mentioned {skill} as one of your skills. How have you kept this skill up-to-date with the latest developments in the field?"
        ]
        
        self.missing_skill_templates = [
            "Our {job_title} role requires experience with {skill}, which I don't see explicitly mentioned on your resume. Do you have any experience with this that you'd like to share?",
            "We're looking for someone with knowledge of {skill} for this position. Could you tell me about any exposure you've had to this, even if it's not listed on your resume?",
            "The team uses {skill} regularly in their work. What's your familiarity with this, and how quickly do you think you could get up to speed if needed?"
        ]
        
        self.behavioral_templates = [
            "Can you tell me about a time when you had to deal with a difficult team member or stakeholder? How did you handle the situation?",
            "Describe a situation where you had to meet a tight deadline. How did you prioritize your tasks and manage your time?",
            "Tell me about a project that didn't go as planned. What went wrong, and what did you learn from the experience?",
            "Can you share an example of a time when you had to think creatively to solve a problem?",
            "Describe a situation where you received constructive criticism. How did you respond to it?"
        ]
        
        self.company_culture_templates = [
            "One of our core values is {value}. Can you share an example from your past experience that demonstrates how you embody this value?",
            "Our company mission is centered around {mission_keyword}. How does this align with your personal or professional values?",
            "We pride ourselves on {culture_aspect}. Can you tell me about a work environment where you've thrived and why?"
        ]
        
        self.technical_templates = {
            "programming": [
                "Could you walk me through your approach to debugging a complex issue in a large codebase?",
                "How do you ensure the code you write is maintainable and can be understood by other team members?",
                "What's your experience with code reviews, both giving and receiving feedback?"
            ],
            "data_science": [
                "Can you explain your process for cleaning and preparing a dataset for analysis?",
                "How do you approach feature selection when building a machine learning model?",
                "How would you explain a complex model's results to non-technical stakeholders?"
            ],
            "management": [
                "How do you approach delegating tasks within a team?",
                "Describe your method for providing feedback to team members.",
                "How do you handle conflicts within your team?"
            ],
            "design": [
                "Walk me through your design process from concept to delivery.",
                "How do you incorporate user feedback into your designs?",
                "How do you balance aesthetic considerations with functional requirements?"
            ]
        }
        
        self.situational_templates = [
            "Imagine you're assigned a project with unclear requirements. How would you proceed to clarify what needs to be done?",
            "If you found a critical bug in production code, what steps would you take to address it?",
            "How would you handle a situation where you disagree with a team decision but are outvoted?",
            "If you were falling behind on a deadline, what would your approach be?",
            "Suppose you identify a process that could be significantly improved. How would you go about implementing that change?"
        ]
        
        self.closing_templates = [
            "Is there anything else you'd like to share that we haven't covered that you think would be relevant for the {job_title} position?",
            "Do you have any questions for me about the {job_title} role or about working at our company?",
            "We've covered a lot of ground today. Is there anything you'd like me to clarify about the role or the next steps in our process?"
        ]
        
        # Enhanced follow-up templates with more context awareness
        self.follow_up_templates = {
            "general": [
                "That's interesting. Could you elaborate a bit more on that?",
                "Can you give me a specific example of when you did that?",
                "How did that experience affect your approach to similar situations later?",
                "What would you say was the most important thing you learned from that?",
                "If you could go back and do things differently, would you? How?"
            ],
            "technical_deep_dive": [
                "Could you walk me through the technical details of how you implemented that solution?",
                "What specific technologies or tools did you use in that process?",
                "Were there any performance considerations you had to address?",
                "How did you test that implementation to ensure it worked correctly?",
                "What were the most challenging technical obstacles you encountered?"
            ],
            "process_oriented": [
                "How did you measure the success of that approach?",
                "What was your methodology for tracking progress during that project?",
                "How did you communicate updates to stakeholders throughout that process?",
                "What documentation practices did you follow for that project?",
                "How did you ensure quality control during that process?"
            ],
            "team_dynamics": [
                "How did your team respond to that approach?",
                "What role did you play in the team during that situation?",
                "How did you handle any disagreements within the team?",
                "What strategies did you use to build consensus among team members?",
                "How did you ensure everyone on the team was properly recognized for their contributions?"
            ],
            "problem_solving": [
                "What alternatives did you consider before choosing that solution?",
                "How did you identify the root cause of that problem?",
                "What criteria did you use to evaluate different potential solutions?",
                "Were there any constraints that limited your options in addressing that issue?",
                "How did you validate that your solution would actually solve the problem?"
            ],
            "reflection": [
                "Looking back, what would you say was the biggest challenge in that situation?",
                "How has that experience influenced your approach to similar situations since then?",
                "What would you do differently if you encountered a similar situation in the future?",
                "What are the most important lessons you learned from that experience?",
                "How have you applied those insights in your subsequent work?"
            ]
        }
        
        # Keep track of used questions to avoid repetition
        self.used_questions = set()
    
    def _is_similar_to_used(self, question: str, threshold: float = 0.7) -> bool:
        """
        Check if a question is similar to any previously used question.
        
        Args:
            question: The question to check
            threshold: Similarity threshold (0-1)
            
        Returns:
            True if similar to a used question, False otherwise
        """
        # Simple word-based similarity check
        question_words = set(re.findall(r'\b\w+\b', question.lower()))
        
        for used in self.used_questions:
            used_words = set(re.findall(r'\b\w+\b', used.lower()))
            
            # Calculate Jaccard similarity
            if len(question_words) > 0 and len(used_words) > 0:
                intersection = len(question_words & used_words)
                union = len(question_words | used_words)
                similarity = intersection / union
                
                if similarity > threshold:
                    return True
        
        return False
    
    def generate_interview_script(self, 
                                  job_info: Dict[str, Any], 
                                  company_info: Dict[str, Any], 
                                  candidate_info: Dict[str, Any],
                                  match_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate a personalized interview script based on the job post, 
        company profile, and candidate resume.
        
        Args:
            job_info: Extracted job posting information
            company_info: Extracted company profile information
            candidate_info: Extracted resume information
            match_analysis: Analysis of candidate's match to job requirements
            
        Returns:
            List of question dictionaries with 'type' and 'question' keys
        """
        script = []
        self.used_questions = set()  # Reset used questions
        
        # Add introduction
        intro_template = random.choice(self.introduction_templates)
        intro_question = intro_template.format(
            candidate_name=candidate_info.get('name', 'there'),
            job_title=job_info.get('title', 'open position')
        )
        script.append({
            'type': 'introduction',
            'question': intro_question
        })
        self.used_questions.add(intro_question)
        
        # Create a balanced script with diverse question types
        # Shuffle the order a bit to make it less predictable
        question_categories = []
        
        # Add experience questions
        for exp in candidate_info.get('work_experience', [])[:2]:  # Limit to 2 experiences
            if 'company' in exp and 'title' in exp:
                exp_template = random.choice(self.experience_templates)
                exp_question = exp_template.format(
                    company=exp['company'],
                    title=exp['title'],
                    job_title=job_info.get('title', 'open position')
                )
                
                if not self._is_similar_to_used(exp_question):
                    question_categories.append({
                        'type': 'experience',
                        'question': exp_question,
                        'priority': random.uniform(0.7, 0.9)  # High priority
                    })
                    self.used_questions.add(exp_question)
        
        # Add skill questions
        for skill in match_analysis.get('common_skills', [])[:3]:  # Limit to 3 skills
            skill_template = random.choice(self.skill_templates)
            skill_question = skill_template.format(skill=skill)
            
            if not self._is_similar_to_used(skill_question):
                question_categories.append({
                    'type': 'skill',
                    'question': skill_question,
                    'priority': random.uniform(0.5, 0.7)  # Medium priority
                })
                self.used_questions.add(skill_question)
        
        # Add missing skill questions
        for skill in match_analysis.get('missing_skills', [])[:2]:  # Limit to 2 missing skills
            missing_skill_template = random.choice(self.missing_skill_templates)
            missing_skill_question = missing_skill_template.format(
                skill=skill,
                job_title=job_info.get('title', 'open position')
            )
            
            if not self._is_similar_to_used(missing_skill_question):
                question_categories.append({
                    'type': 'missing_skill',
                    'question': missing_skill_question,
                    'priority': random.uniform(0.6, 0.8)  # Medium-high priority
                })
                self.used_questions.add(missing_skill_question)
        
        # Add technical questions based on job title
        job_title = job_info.get('title', '').lower()
        technical_category = 'programming'  # Default
        
        if any(term in job_title for term in ['data', 'scientist', 'analyst', 'machine learning']):
            technical_category = 'data_science'
        elif any(term in job_title for term in ['manager', 'director', 'lead']):
            technical_category = 'management'
        elif any(term in job_title for term in ['designer', 'ux', 'ui']):
            technical_category = 'design'
        
        # Add 2 technical questions
        used_technical_questions = set()
        for _ in range(2):
            # Choose a question we haven't used yet
            available_questions = [q for q in self.technical_templates[technical_category] 
                                  if q not in used_technical_questions]
            
            if not available_questions:
                break
                
            technical_template = random.choice(available_questions)
            used_technical_questions.add(technical_template)
            
            if not self._is_similar_to_used(technical_template):
                question_categories.append({
                    'type': 'technical',
                    'question': technical_template,
                    'priority': random.uniform(0.7, 0.9)  # High priority
                })
                self.used_questions.add(technical_template)
        
        # Add behavioral questions
        used_behavioral_questions = set()
        for _ in range(3):  # Add 3 behavioral questions
            available_questions = [q for q in self.behavioral_templates 
                                  if q not in used_behavioral_questions]
            
            if not available_questions:
                break
                
            behavioral_template = random.choice(available_questions)
            used_behavioral_questions.add(behavioral_template)
            
            if not self._is_similar_to_used(behavioral_template):
                question_categories.append({
                    'type': 'behavioral',
                    'question': behavioral_template,
                    'priority': random.uniform(0.6, 0.8)  # Medium-high priority
                })
                self.used_questions.add(behavioral_template)
        
        # Add company culture questions
        if company_info.get('core_values'):
            value = random.choice(company_info['core_values'])
            culture_template = self.company_culture_templates[0]  # Use the value-specific template
            culture_question = culture_template.format(value=value)
            
            if not self._is_similar_to_used(culture_question):
                question_categories.append({
                    'type': 'company_culture',
                    'question': culture_question,
                    'priority': random.uniform(0.5, 0.7)  # Medium priority
                })
                self.used_questions.add(culture_question)
        
        if company_info.get('mission'):
            mission_keywords = [word for word in company_info['mission'].split() 
                               if len(word) > 4 and word.lower() not in {'about', 'their', 'would', 'should'}]
            if mission_keywords:
                mission_keyword = random.choice(mission_keywords)
                culture_template = self.company_culture_templates[1]  # Use the mission-specific template
                culture_question = culture_template.format(mission_keyword=mission_keyword)
                
                if not self._is_similar_to_used(culture_question):
                    question_categories.append({
                        'type': 'company_culture',
                        'question': culture_question,
                        'priority': random.uniform(0.5, 0.7)  # Medium priority
                    })
                    self.used_questions.add(culture_question)
        
        # Add situational questions
        used_situational_questions = set()
        for _ in range(2):  # Add 2 situational questions
            available_questions = [q for q in self.situational_templates 
                                 if q not in used_situational_questions]
            
            if not available_questions:
                break
                
            situational_template = random.choice(available_questions)
            used_situational_questions.add(situational_template)
            
            if not self._is_similar_to_used(situational_template):
                question_categories.append({
                    'type': 'situational',
                    'question': situational_template,
                    'priority': random.uniform(0.4, 0.6)  # Medium-low priority
                })
                self.used_questions.add(situational_template)
        
        # Sort questions by priority (higher priority first)
        # Then shuffle within similar priority ranges to add variety
        question_categories.sort(key=lambda x: x['priority'], reverse=True)
        
        # Group questions by priority ranges and shuffle within groups
        priority_groups = [
            [q for q in question_categories if q['priority'] >= 0.8],  # Very high
            [q for q in question_categories if 0.6 <= q['priority'] < 0.8],  # High
            [q for q in question_categories if 0.4 <= q['priority'] < 0.6],  # Medium
            [q for q in question_categories if q['priority'] < 0.4]  # Low
        ]
        
        for group in priority_groups:
            random.shuffle(group)
        
        # Reconstruct the question list
        balanced_questions = []
        for group in priority_groups:
            balanced_questions.extend(group)
        
        # Add all questions to script, removing the priority field
        for question_data in balanced_questions:
            script.append({
                'type': question_data['type'],
                'question': question_data['question']
            })
        
        # Add closing
        closing_template = random.choice(self.closing_templates)
        closing_question = closing_template.format(
            job_title=job_info.get('title', 'open position')
        )
        script.append({
            'type': 'closing',
            'question': closing_question
        })
        
        return script
    
    def generate_follow_up_question(self, 
                                   question_type: str, 
                                   original_question: str,
                                   candidate_response: str) -> str:
        """
        Generate a follow-up question based on the candidate's response.
        
        Args:
            question_type: Type of the original question
            original_question: The original question that was asked
            candidate_response: The candidate's response to the original question
            
        Returns:
            A follow-up question
        """
        # Choose appropriate follow-up category based on question type and response content
        follow_up_category = "general"  # Default
        
        # Analyze response for keywords to determine best follow-up category
        response_lower = candidate_response.lower()
        
        # Map of keywords to follow-up categories
        category_keywords = {
            "technical_deep_dive": ["code", "algorithm", "architecture", "implementation", "system", "database", "framework"],
            "process_oriented": ["process", "methodology", "approach", "workflow", "procedure", "steps", "tracking"],
            "team_dynamics": ["team", "collaborate", "peer", "colleague", "manager", "stakeholder", "communication"],
            "problem_solving": ["problem", "solution", "resolve", "challenge", "issue", "fix", "troubleshoot"],
            "reflection": ["learn", "improve", "retrospective", "reflection", "insight", "growth", "development"]
        }
        
        # Check which category has the most keyword matches in the response
        category_scores = {category: 0 for category in self.follow_up_templates.keys()}
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in response_lower:
                    category_scores[category] += 1
        
        # Also consider the original question type
        type_category_mapping = {
            'technical': "technical_deep_dive",
            'experience': "reflection",
            'skill': "technical_deep_dive",
            'behavioral': "reflection",
            'company_culture': "team_dynamics",
            'situational': "problem_solving",
            'missing_skill': "reflection"
        }
        
        # Boost the score for the category that matches the question type
        if question_type in type_category_mapping:
            matched_category = type_category_mapping[question_type]
            category_scores[matched_category] += 2
        
        # Find the category with the highest score
        max_score = max(category_scores.values())
        if max_score > 0:
            # Get all categories with the max score
            best_categories = [category for category, score in category_scores.items() if score == max_score]
            follow_up_category = random.choice(best_categories)
        
        # Get a follow-up question from the appropriate category
        follow_up_options = self.follow_up_templates[follow_up_category]
        
        # Return a random follow-up from the selected category
        return random.choice(follow_up_options)