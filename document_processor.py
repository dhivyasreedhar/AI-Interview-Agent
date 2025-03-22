import re
from typing import Dict, List, Any
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')

class DocumentProcessor:
    """
    Process job postings and resumes to extract relevant information
    for generating personalized interview questions.
    """
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        
    def process_job_posting(self, job_post: str) -> Dict[str, Any]:
        """
        Extract structured information from a job posting.
        
        Args:
            job_post: Raw text of the job posting
            
        Returns:
            Dictionary with extracted job information
        """
        # Extract job title
        title_match = re.search(r'(Position|Job Title|Title):\s*(.*?)(?:\n|$)', job_post, re.IGNORECASE)
        title = title_match.group(2).strip() if title_match else ""
        
        # Extract required skills
        skills = self._extract_skills(job_post)
        
        # Extract required experience level
        experience_match = re.search(r'(\d+)[\+\-]?\s*(?:years|yrs)(?:\s*of)?\s*experience', job_post, re.IGNORECASE)
        experience_years = int(experience_match.group(1)) if experience_match else 0
        
        # Extract educational requirements
        education = self._extract_education(job_post)
        
        # Extract key responsibilities
        responsibilities = self._extract_responsibilities(job_post)
        
        return {
            "title": title,
            "skills": skills,
            "experience_years": experience_years,
            "education": education,
            "responsibilities": responsibilities,
            "raw_text": job_post
        }
    
    def process_company_profile(self, company_profile: str) -> Dict[str, Any]:
        """
        Extract structured information from a company profile.
        
        Args:
            company_profile: Raw text of the company profile
            
        Returns:
            Dictionary with extracted company information
        """
        # Extract company mission
        mission_match = re.search(r'Mission:?\s*(.*?)(?:\n\n|\n[A-Z]|$)', company_profile, re.IGNORECASE | re.DOTALL)
        mission = mission_match.group(1).strip() if mission_match else ""
        
        # Extract company vision
        vision_match = re.search(r'Vision:?\s*(.*?)(?:\n\n|\n[A-Z]|$)', company_profile, re.IGNORECASE | re.DOTALL)
        vision = vision_match.group(1).strip() if vision_match else ""
        
        # Extract core values
        values_match = re.search(r'(?:Core\s*)?Values:?\s*(.*?)(?:\n\n|\n[A-Z]|$)', company_profile, re.IGNORECASE | re.DOTALL)
        values_text = values_match.group(1).strip() if values_match else ""
        values = [v.strip() for v in re.split(r'[,•\n]', values_text) if v.strip()]
        
        return {
            "mission": mission,
            "vision": vision,
            "core_values": values,
            "raw_text": company_profile
        }
    
    def process_resume(self, resume: str) -> Dict[str, Any]:
        """
        Extract structured information from a resume.
        
        Args:
            resume: Raw text of the candidate's resume
            
        Returns:
            Dictionary with extracted candidate information
        """
        # Extract candidate name
        name_match = re.search(r'^([A-Z][a-z]+(?: [A-Z][a-z]+){1,2})', resume)
        name = name_match.group(1) if name_match else ""
        
        # Extract email
        email_match = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', resume)
        email = email_match.group(1) if email_match else ""
        
        # Extract skills
        skills = self._extract_skills(resume)
        
        # Extract work experience
        work_exp = self._extract_work_experience(resume)
        
        # Extract education
        education = self._extract_education(resume)
        
        return {
            "name": name,
            "email": email,
            "skills": skills,
            "work_experience": work_exp,
            "education": education,
            "raw_text": resume
        }
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from text."""
        # Look for skills section
        skills_section_match = re.search(r'(?:Technical\s*)?Skills:?\s*(.*?)(?:\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
        
        if skills_section_match:
            skills_text = skills_section_match.group(1)
            # Split by commas, bullet points, or new lines
            skills = [s.strip() for s in re.split(r'[,•\n]', skills_text) if s.strip()]
            return skills
        
        # If no specific skills section, try to extract common technical skills
        common_skills = [
            'Python', 'Java', 'JavaScript', 'C++', 'React', 'Angular', 'Vue', 'Node.js', 
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'SQL', 'NoSQL', 'MongoDB',
            'TensorFlow', 'PyTorch', 'ML', 'AI', 'Project Management', 'Agile', 'Scrum',
            'Communication', 'Leadership', 'Problem Solving', 'Critical Thinking'
        ]
        
        found_skills = [skill for skill in common_skills if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE)]
        return found_skills
    
    def _extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information from text."""
        education_list = []
        
        # Find education section
        education_section_match = re.search(r'Education:?\s*(.*?)(?:\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
        if education_section_match:
            education_text = education_section_match.group(1)
            
            # Look for degree patterns
            degree_patterns = [
                r'(Bachelor|Master|PhD|Doctorate|B\.S\.|M\.S\.|B\.A\.|M\.A\.|M\.B\.A\.)\s+(?:of|in)?\s+([^,\n]+)',
                r'([^,\n]+) (University|College|Institute|School)'
            ]
            
            for pattern in degree_patterns:
                for match in re.finditer(pattern, education_text, re.IGNORECASE):
                    education_list.append({
                        "degree": match.group(0).strip(),
                        "year": self._extract_year(match.group(0))
                    })
        
        return education_list
    
    def _extract_work_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience information from text."""
        experience_list = []
        
        # Find experience section
        experience_section_match = re.search(
            r'(?:Work\s*)?Experience:?\s*(.*?)(?:\n\n|\n[A-Z]|$)', 
            text, 
            re.IGNORECASE | re.DOTALL
        )
        
        if experience_section_match:
            experience_text = experience_section_match.group(1)
            
            # Split by double newline to get each position
            positions = re.split(r'\n\n', experience_text)
            
            for position in positions:
                if not position.strip():
                    continue
                    
                # Extract company name (usually at the beginning of a line)
                company_match = re.search(r'^([^,\n]+)', position)
                company = company_match.group(1).strip() if company_match else ""
                
                # Extract position title
                title_match = re.search(r'(Developer|Engineer|Manager|Director|Analyst|Designer|Consultant|Specialist)', position, re.IGNORECASE)
                title = title_match.group(0) if title_match else ""
                
                # Extract dates
                date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*-\s*(?:(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|Present)', position, re.IGNORECASE)
                dates = date_match.group(0) if date_match else ""
                
                # Extract duration
                years_match = re.search(r'(\d+)\s*(?:years|yrs)', position, re.IGNORECASE)
                duration_years = int(years_match.group(1)) if years_match else 0
                
                experience_list.append({
                    "company": company,
                    "title": title,
                    "dates": dates,
                    "duration_years": duration_years
                })
        
        return experience_list
    
    def _extract_responsibilities(self, text: str) -> List[str]:
        """Extract job responsibilities from text."""
        # Find responsibilities section
        resp_section_match = re.search(
            r'(?:Key\s*)?Responsibilities:?\s*(.*?)(?:\n\n|\n[A-Z]|$)', 
            text, 
            re.IGNORECASE | re.DOTALL
        )
        
        if resp_section_match:
            resp_text = resp_section_match.group(1)
            # Split by bullet points or new lines
            responsibilities = [r.strip() for r in re.split(r'[•\n]', resp_text) if r.strip()]
            return responsibilities
        
        return []
    
    def _extract_year(self, text: str) -> str:
        """Extract year from text."""
        year_match = re.search(r'(19|20)\d{2}', text)
        return year_match.group(0) if year_match else ""
    
    def analyze_match(self, job_info: Dict[str, Any], candidate_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze how well the candidate matches the job requirements.
        
        Args:
            job_info: Extracted job posting information
            candidate_info: Extracted resume information
            
        Returns:
            Dictionary with match analysis
        """
        # Match skills
        common_skills = set(s.lower() for s in job_info['skills']) & set(s.lower() for s in candidate_info['skills'])
        missing_skills = set(s.lower() for s in job_info['skills']) - set(s.lower() for s in candidate_info['skills'])
        
        # Check experience
        total_experience = sum(exp.get('duration_years', 0) for exp in candidate_info['work_experience'])
        experience_match = total_experience >= job_info['experience_years']
        
        # Check education
        education_match = False
        if job_info['education'] and candidate_info['education']:
            for job_edu in job_info['education']:
                for candidate_edu in candidate_info['education']:
                    if job_edu['degree'].lower() in candidate_edu['degree'].lower():
                        education_match = True
                        break
        
        return {
            "skill_match_percentage": len(common_skills) / max(len(job_info['skills']), 1) * 100,
            "common_skills": list(common_skills),
            "missing_skills": list(missing_skills),
            "experience_match": experience_match,
            "education_match": education_match
        }