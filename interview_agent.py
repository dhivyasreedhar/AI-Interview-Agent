import os
import json
import time
import datetime
from typing import Dict, Any, Optional, List, Tuple
import uuid
import csv

# Import our modules
from document_processor import DocumentProcessor
from question_generator import QuestionGenerator
from conversation_manager import ConversationManager

class InterviewAgent:
    """
    Main AI Interview Agent that coordinates the entire interview process.
    """
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.question_generator = QuestionGenerator()
        self.conversation_manager = None
        
        # Store processed documents
        self.job_info = None
        self.company_info = None
        self.candidate_info = None
        self.match_analysis = None
        
        # Interview state
        self.interview_in_progress = False
        self.interview_complete = False
        self.interview_summary = None
        self.interview_id = None
        
        # Interview timing
        self.interview_start_time = None
        self.interview_end_time = None
        self.interview_duration = None
        self.interview_max_duration = None  # In minutes
        
        # Debugging mode
        self.debug_mode = False
        
        # Make sure reports directory exists
        os.makedirs('data/reports', exist_ok=True)
    
    def enable_debug_mode(self):
        """Enable debugging mode for more verbose output"""
        self.debug_mode = True
        print("Debug mode enabled")
    
    def load_job_posting(self, job_posting_text: str) -> Dict[str, Any]:
        """
        Load and process a job posting.
        
        Args:
            job_posting_text: Raw text of the job posting
            
        Returns:
            Processed job information
        """
        if self.debug_mode:
            print(f"Processing job posting: {len(job_posting_text)} characters")
            
        self.job_info = self.document_processor.process_job_posting(job_posting_text)
        
        if self.debug_mode:
            print(f"Extracted job title: {self.job_info.get('title', 'Unknown')}")
            print(f"Identified {len(self.job_info.get('skills', []))} required skills")
            
        return self.job_info
    
    def load_company_profile(self, company_profile_text: str) -> Dict[str, Any]:
        """
        Load and process a company profile.
        
        Args:
            company_profile_text: Raw text of the company profile
            
        Returns:
            Processed company information
        """
        if self.debug_mode:
            print(f"Processing company profile: {len(company_profile_text)} characters")
            
        self.company_info = self.document_processor.process_company_profile(company_profile_text)
        
        if self.debug_mode:
            print(f"Extracted mission: {self.company_info.get('mission', 'None')[:50]}...")
            print(f"Identified {len(self.company_info.get('core_values', []))} core values")
            
        return self.company_info
    
    def load_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        Load and process a candidate resume.
        
        Args:
            resume_text: Raw text of the candidate's resume
            
        Returns:
            Processed candidate information
        """
        if self.debug_mode:
            print(f"Processing resume: {len(resume_text)} characters")
            
        self.candidate_info = self.document_processor.process_resume(resume_text)
        
        if self.debug_mode:
            print(f"Extracted candidate name: {self.candidate_info.get('name', 'Unknown')}")
            print(f"Identified {len(self.candidate_info.get('skills', []))} skills")
            print(f"Extracted {len(self.candidate_info.get('work_experience', []))} work experiences")
            
        return self.candidate_info
    
    def analyze_candidate_job_match(self) -> Dict[str, Any]:
        """
        Analyze how well the candidate matches the job requirements.
        
        Returns:
            Match analysis information
        """
        if not self.job_info or not self.candidate_info:
            raise ValueError("Job posting and resume must be loaded before analysis.")
        
        if self.debug_mode:
            print("Analyzing candidate-job match...")
            
        self.match_analysis = self.document_processor.analyze_match(self.job_info, self.candidate_info)
        
        if self.debug_mode:
            print(f"Skill match percentage: {self.match_analysis.get('skill_match_percentage', 0):.1f}%")
            print(f"Common skills: {len(self.match_analysis.get('common_skills', []))}")
            print(f"Missing skills: {len(self.match_analysis.get('missing_skills', []))}")
            
        return self.match_analysis
    
    def generate_interview_script(self) -> List[Dict[str, str]]:
        """
        Generate a personalized interview script based on the loaded documents.
        
        Returns:
            List of interview questions
        """
        if not self.job_info or not self.company_info or not self.candidate_info or not self.match_analysis:
            raise ValueError("All documents must be loaded and analyzed before generating an interview script.")
        
        if self.debug_mode:
            print("Generating interview script...")
            
        script = self.question_generator.generate_interview_script(
            self.job_info, 
            self.company_info, 
            self.candidate_info, 
            self.match_analysis
        )
        
        if self.debug_mode:
            print(f"Generated {len(script)} interview questions")
            for i, q in enumerate(script[:3], 1):
                print(f"Sample Q{i} ({q['type']}): {q['question'][:50]}...")
            if len(script) > 3:
                print("...")
                
        return script
    
    def set_interview_duration(self, max_minutes: int) -> None:
        """
        Set the maximum duration for the interview in minutes.
        
        Args:
            max_minutes: Maximum interview duration in minutes
        """
        if max_minutes <= 0:
            raise ValueError("Interview duration must be positive")
            
        self.interview_max_duration = max_minutes
        
        if self.debug_mode:
            print(f"Interview duration set to {max_minutes} minutes")
    
    def start_interview(self) -> str:
        """
        Start the interview process.
        
        Returns:
            The first interview question
        """
        if not self.job_info or not self.company_info or not self.candidate_info or not self.match_analysis:
            raise ValueError("All documents must be loaded and analyzed before starting an interview.")
        
        if self.debug_mode:
            print("Starting interview...")
        
        # Generate unique interview ID if not already set
        if not self.interview_id:
            self.interview_id = str(uuid.uuid4())
            
        # Record start time
        self.interview_start_time = time.time()
        
        self.conversation_manager = ConversationManager(
            self.question_generator,
            self.job_info,
            self.company_info,
            self.candidate_info,
            self.match_analysis
        )
        
        self.interview_in_progress = True
        self.interview_complete = False
        
        first_question = self.conversation_manager.start_interview()
        
        if self.debug_mode:
            print(f"First question: {first_question}")
            print(f"Interview started at: {datetime.datetime.fromtimestamp(self.interview_start_time).strftime('%Y-%m-%d %H:%M:%S')}")
            if self.interview_max_duration:
                print(f"Time limit: {self.interview_max_duration} minutes")
            
        return first_question
    
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
        Process the candidate's response and get the next question.
        
        Args:
            response: The candidate's response
            
        Returns:
            Dictionary with next question, interview status, and remaining time
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
            
        # Process the response normally
        next_question, is_complete = self.conversation_manager.process_candidate_response(response)
        
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
            "remaining_seconds": remaining_seconds if self.interview_max_duration else None,
            "time_limit_exceeded": False
        }
    
    def _generate_time_exceeded_conclusion(self) -> str:
        """
        Generate a conclusion message when the interview time is exceeded.
        
        Returns:
            Conclusion message
        """
        candidate_name = self.candidate_info.get('name', 'there')
        job_title = self.job_info.get('title', 'this position')
        
        return (
            f"I see we've reached the end of our allocated time for this interview, {candidate_name}. "
            f"Thank you for sharing your experiences and insights for the {job_title} position. "
            f"Although we couldn't get through all our questions, I've gathered valuable information about your background and skills. "
            f"Our team will review your candidacy and get back to you soon regarding next steps. "
            f"Do you have any brief final questions before we conclude?"
        )
    
    def get_interview_summary(self) -> Dict[str, Any]:
        """
        Get the interview summary.
        
        Returns:
            Interview summary information
        """
        if not self.interview_complete:
            raise ValueError("Interview is not complete.")
        
        # Add timing information to the summary
        if self.interview_summary and self.interview_start_time and self.interview_end_time:
            self.interview_summary['interview_start_time'] = self.interview_start_time
            self.interview_summary['interview_end_time'] = self.interview_end_time
            self.interview_summary['interview_duration_seconds'] = self.interview_duration
            self.interview_summary['interview_duration_minutes'] = self.interview_duration / 60
            
        return self.interview_summary
    
    def save_interview_data(self, file_path: str) -> None:
        """
        Save all interview data to a JSON file.
        
        Args:
            file_path: Path to save the JSON file
        """
        if not self.interview_complete:
            raise ValueError("Interview is not complete.")
        
        data = {
            "interview_id": self.interview_id,
            "job_info": self.job_info,
            "company_info": self.company_info,
            "candidate_info": self.candidate_info,
            "match_analysis": self.match_analysis,
            "interview_summary": self.interview_summary,
            "interview_start_time": self.interview_start_time,
            "interview_end_time": self.interview_end_time,
            "interview_duration": self.interview_duration,
            "timestamp": time.time()
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
            
        if self.debug_mode:
            print(f"Interview data saved to {file_path}")
    
    def save_interview_report(self) -> str:
        """
        Save the interview report to file.
        
        Returns:
            Path to the saved report file
        """
        if not self.interview_complete or not self.interview_summary:
            raise ValueError("Interview is not complete.")
            
        # Ensure we have an interview ID
        if not self.interview_id:
            self.interview_id = str(uuid.uuid4())
            
        # Create reports directory if it doesn't exist
        os.makedirs('data/reports', exist_ok=True)
            
        # Create a filename with date and candidate name
        candidate_name = self.candidate_info.get('name', 'Unknown').replace(' ', '_')
        job_title = self.job_info.get('title', 'Unknown').replace(' ', '_')
        date_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON report with full details
        json_filename = f"data/reports/{date_str}_{candidate_name}_{job_title}_{self.interview_id}.json"
        
        with open(json_filename, 'w') as f:
            json.dump(self.interview_summary, f, indent=2)
            
        # CSV summary for easy tracking
        self._update_summary_csv()
        
        if self.debug_mode:
            print(f"Interview report saved to {json_filename}")
            print(f"Summary updated in reports_summary.csv")
            
        return json_filename
    
    def _update_summary_csv(self) -> None:
        """Update the CSV summary file with this interview"""
        csv_file = "data/reports/reports_summary.csv"
        file_exists = os.path.isfile(csv_file)
        
        summary = self.interview_summary
        
        # Format data for CSV
        row = {
            'interview_id': self.interview_id,
            'date': datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d'),
            'time': datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S'),
            'candidate_name': summary.get('candidate_name', 'Unknown'),
            'job_title': summary.get('job_title', 'Unknown'),
            'overall_score': summary.get('overall_score', 0),
            'recommendation': summary.get('recommendation', 'Unknown'),
            'technical_score': summary.get('technical_score', 0),
            'cultural_fit_score': summary.get('cultural_fit_score', 0),
            'communication_score': summary.get('communication_score', 0),
            'experience_relevance_score': summary.get('experience_relevance_score', 0),
            'skill_match_score': summary.get('skill_match_score', 0),
            'skill_match_percentage': summary.get('skill_match_percentage', 0),
            'duration_minutes': self.interview_duration / 60 if self.interview_duration else 0,
            'strengths_count': len(summary.get('strengths', [])),
            'improvements_count': len(summary.get('areas_for_improvement', [])),
            'notes_count': len(summary.get('notes', []))
        }
        
        # Write to CSV
        with open(csv_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            
            # Write header if file doesn't exist
            if not file_exists:
                writer.writeheader()
                
            writer.writerow(row)
    
    def load_interview_data(self, file_path: str) -> Dict[str, Any]:
        """
        Load interview data from a JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Loaded interview data
        """
        if self.debug_mode:
            print(f"Loading interview data from {file_path}")
            
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        self.interview_id = data.get("interview_id")
        self.job_info = data.get("job_info")
        self.company_info = data.get("company_info")
        self.candidate_info = data.get("candidate_info")
        self.match_analysis = data.get("match_analysis")
        self.interview_summary = data.get("interview_summary")
        self.interview_start_time = data.get("interview_start_time")
        self.interview_end_time = data.get("interview_end_time")
        self.interview_duration = data.get("interview_duration")
        
        if self.interview_summary:
            self.interview_complete = True
            
        if self.debug_mode:
            print("Interview data loaded successfully")
            
        return data