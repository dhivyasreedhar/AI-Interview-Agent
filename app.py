from flask import Flask, render_template, request, jsonify, session, send_from_directory, redirect, url_for
import os
import json
import uuid
from datetime import datetime
import time
import glob
from typing import Tuple  # Add this import

# Import our modules
from interview_agent import InterviewAgent


# Create the Flask application
app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)
os.makedirs('data/interviews', exist_ok=True)
os.makedirs('data/uploads', exist_ok=True)
os.makedirs('data/reports', exist_ok=True)

# Template context processors and filters
@app.template_filter('timestamp_to_datetime')
def timestamp_to_datetime(timestamp):
    """Convert Unix timestamp to formatted datetime string"""
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

@app.template_filter('duration_format')
def duration_format(seconds):
    """Format seconds into a readable duration"""
    if seconds is None:
        return "No limit"
    
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes}m {remaining_seconds}s"

@app.context_processor
def utility_processor():
    """Add utility functions to template context"""
    def now(format_string='%Y-%m-%d'):
        return datetime.now().strftime(format_string)
    
    return dict(now=now)

@app.route('/')
def index():
    """Render the homepage"""
    return render_template('index.html')

@app.route('/interview/<interview_id>')
def interview(interview_id):
    """Render the interview page"""
    interview_dir = os.path.join('data/interviews', interview_id)
    
    # Check if interview exists
    if not os.path.exists(interview_dir):
        return "Interview not found", 404
    
    # Load agent state
    try:
        with open(os.path.join(interview_dir, 'agent_state.json'), 'r') as f:
            agent_state = json.load(f)
        
        # Set session
        session['interview_id'] = interview_id
        
        # Get interview duration
        interview_duration = agent_state.get('interview_duration', 0)
        
        return render_template('interview.html', 
                              interview_id=interview_id,
                              job_title=agent_state['job_info'].get('title', 'Unknown'),
                              candidate_name=agent_state['candidate_info'].get('name', 'Unknown'),
                              interview_duration=interview_duration)
    except Exception as e:
        print(f"Error loading interview: {e}")
        return "Error loading interview data", 500
    
@app.route('/api/process-response', methods=['POST'])
def process_response():
    """Process a candidate's response"""
    try:
        interview_id = request.json.get('interview_id')
        response = request.json.get('response')
        
        if not interview_id or not response:
            return jsonify({'status': 'error', 'message': 'Interview ID and response are required'}), 400
        
        interview_dir = os.path.join('data/interviews', interview_id)
        
        # Check if interview exists
        if not os.path.exists(interview_dir):
            return jsonify({'status': 'error', 'message': 'Interview not found'}), 404
        
        # Load agent state
        with open(os.path.join(interview_dir, 'agent_state.json'), 'r') as f:
            agent_state = json.load(f)
        
        # Load conversation state
        with open(os.path.join(interview_dir, 'conversation.json'), 'r') as f:
            conversation_state = json.load(f)
        
        # Initialize agent with saved state
        agent = InterviewAgent()
        agent.job_info = agent_state['job_info']
        agent.company_info = agent_state['company_info']
        agent.candidate_info = agent_state['candidate_info']
        agent.match_analysis = agent_state['match_analysis']
        agent.interview_id = interview_id
        agent.interview_start_time = conversation_state.get('interview_start_time')
        
        # Set interview duration if specified
        interview_duration = agent_state.get('interview_duration', 0)
        if interview_duration > 0:
            agent.set_interview_duration(interview_duration)
        
        # Recreate conversation manager
        from conversation_manager import ConversationManager
        
        agent.conversation_manager = ConversationManager(
            agent.question_generator,
            agent.job_info,
            agent.company_info,
            agent.candidate_info,
            agent.match_analysis,
        )
        
        # Restore conversation state
        agent.conversation_manager.conversation_history = conversation_state['history']
        agent.conversation_manager.current_question_index = conversation_state['current_index']
        agent.interview_in_progress = True
        agent.interview_complete = conversation_state.get('complete', False)
        
        # Process the response
        print("DEBUG: Before calling process_candidate_response")
        result = agent.process_candidate_response(response)
        print(f"DEBUG: process_candidate_response result: {result}")
        print(f"DEBUG: result type: {type(result)}")
        print(f"DEBUG: result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        # Update conversation state
        with open(os.path.join(interview_dir, 'conversation.json'), 'w') as f:
            json.dump({
                'history': agent.conversation_manager.conversation_history,
                'current_index': agent.conversation_manager.current_question_index,
                'complete': agent.interview_complete,
                'interview_start_time': agent.interview_start_time
            }, f, indent=2)
        
        # If interview is complete, save summary
        if agent.interview_complete:
            print("DEBUG: Interview is complete. Generating summary.json...")
            with open(os.path.join(interview_dir, 'summary.json'), 'w') as f:
                json.dump(agent.interview_summary, f, indent=2)
        else:
            print("DEBUG: Interview is not complete. Skipping summary.json generation.")
        
        # We also need to fix time limit check here
        print("DEBUG: Checking for remaining_seconds in result")
        if 'remaining_seconds' in result:
            # Already properly formatted
            print(f"DEBUG: remaining_seconds found in result: {result['remaining_seconds']}")
        else:
            # Need to check time limit again
            print("DEBUG: Calling check_time_limit")
            time_info = agent.check_time_limit()
            print(f"DEBUG: time_info: {time_info}")
            print(f"DEBUG: time_info type: {type(time_info)}")
            
            time_exceeded = False
            remaining_seconds = interview_duration
            
            if isinstance(time_info, tuple):
                print(f"DEBUG: time_info is tuple with length: {len(time_info)}")
                if len(time_info) == 2:
                    time_exceeded, remaining_seconds = time_info
                elif len(time_info) == 3:
                    # If there's a third value, extract just what we need
                    print(f"DEBUG: time_info has 3 values: {time_info}")
                    time_exceeded, remaining_seconds = time_info[0], time_info[1]
                else:
                    # Default values if the tuple has unexpected length
                    print(f"DEBUG: time_info has unexpected length: {len(time_info)}")
            else:
                # Handle case where it's not returning a tuple
                print(f"DEBUG: time_info is not a tuple: {type(time_info)}")
            
            print(f"DEBUG: Extracted time_exceeded: {time_exceeded}, remaining_seconds: {remaining_seconds}")
            result['remaining_seconds'] = remaining_seconds
            result['time_limit_exceeded'] = time_exceeded
        
        response_data = {
            'status': 'success',
            'question': result['next_question'],
            'is_complete': result['is_complete'],
            'remaining_seconds': result.get('remaining_seconds'),
            'time_limit_exceeded': result.get('time_limit_exceeded', False)
        }
        print(f"DEBUG: Final response: {response_data}")
        return jsonify(response_data)
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error processing response: {e}")
        print(f"Error traceback: {error_traceback}")
        return jsonify({'status': 'error', 'message': f'An error occurred: {str(e)}'}), 500
    
@app.route('/setup-interview', methods=['GET', 'POST'])
def setup_interview():
    """Setup a new interview"""
    if request.method == 'POST':
        # Generate a unique ID for this interview
        interview_id = str(uuid.uuid4())
        session['interview_id'] = interview_id
        
        # Create directory for this interview
        interview_dir = os.path.join('data/interviews', interview_id)
        os.makedirs(interview_dir, exist_ok=True)
        
        # Save job posting
        job_posting = request.form.get('job_posting', '')
        with open(os.path.join(interview_dir, 'job_posting.txt'), 'w') as f:
            f.write(job_posting)
        
        # Save company profile
        company_profile = request.form.get('company_profile', '')
        with open(os.path.join(interview_dir, 'company_profile.txt'), 'w') as f:
            f.write(company_profile)
        
        # Save resume
        resume = request.form.get('resume', '')
        with open(os.path.join(interview_dir, 'resume.txt'), 'w') as f:
            f.write(resume)
        
        # Get interview duration
        interview_duration = request.form.get('interview_duration', '')
        try:
            interview_duration = int(interview_duration)
        except (ValueError, TypeError):
            interview_duration = 0  # No time limit
        
        # Process documents and prepare interview
        agent = InterviewAgent()
        agent.load_job_posting(job_posting)
        agent.load_company_profile(company_profile)
        agent.load_resume(resume)
        
        # Set interview duration if specified
        if interview_duration > 0:
            agent.set_interview_duration(interview_duration)
        
        # Analyze candidate-job match
        match_analysis = agent.analyze_candidate_job_match()
        
        # Generate interview script
        script = agent.generate_interview_script()
        
        # Save agent state
        with open(os.path.join(interview_dir, 'agent_state.json'), 'w') as f:
            json.dump({
                'job_info': agent.job_info,
                'company_info': agent.company_info,
                'candidate_info': agent.candidate_info,
                'match_analysis': agent.match_analysis,
                'script': script,
                'interview_duration': interview_duration,
                'created_at': datetime.now().isoformat()
            }, f, indent=2)
        
        return jsonify({
            'status': 'success',
            'interview_id': interview_id,
            'redirect': f'/interview/{interview_id}'
        })
    
    return render_template('setup_interview.html')

@app.route('/api/start-interview', methods=['POST'])
def start_interview():
    """Start the interview"""
    try:
        interview_id = request.json.get('interview_id')
        if not interview_id:
            return jsonify({'status': 'error', 'message': 'Interview ID is required'}), 400
        
        interview_dir = os.path.join('data/interviews', interview_id)
        
        # Check if interview exists
        if not os.path.exists(interview_dir):
            return jsonify({'status': 'error', 'message': 'Interview not found'}), 404
        
        # Load agent state
        with open(os.path.join(interview_dir, 'agent_state.json'), 'r') as f:
            agent_state = json.load(f)
        
        # Initialize agent with saved state
        agent = InterviewAgent()
        agent.job_info = agent_state['job_info']
        agent.company_info = agent_state['company_info']
        agent.candidate_info = agent_state['candidate_info']
        agent.match_analysis = agent_state['match_analysis']
        agent.interview_id = interview_id
        
        # Set interview duration if specified
        interview_duration = agent_state.get('interview_duration', 0)
        if interview_duration > 0:
            agent.set_interview_duration(interview_duration)
        
        # Start interview
        first_question = agent.start_interview()
        
        # Save conversation state
        with open(os.path.join(interview_dir, 'conversation.json'), 'w') as f:
            json.dump({
                'history': agent.conversation_manager.conversation_history,
                'current_index': agent.conversation_manager.current_question_index,
                'complete': False,
                'interview_start_time': agent.interview_start_time
            }, f, indent=2)
        
        # Get remaining time information - Fix for "too many values to unpack" error
        time_info = agent.check_time_limit()
        print(f"DEBUG: time_info: {time_info}")
        print(f"DEBUG: time_info type: {type(time_info)}")

        if isinstance(time_info, tuple):
            print(f"DEBUG: time_info is tuple with length: {len(time_info)}")
            if len(time_info) == 2:
                time_exceeded, remaining_seconds = time_info
                print(f"DEBUG: Unpacked 2 values: {time_exceeded}, {remaining_seconds}")
            elif len(time_info) == 3:
                # If there's a third value, extract just what we need
                print(f"DEBUG: time_info has 3 values: {time_info}")
                time_exceeded, remaining_seconds = time_info[0], time_info[1]
                print(f"DEBUG: Extracted first 2 of 3 values: {time_exceeded}, {remaining_seconds}")
            else:
                # Default values if the tuple has unexpected length
                print(f"DEBUG: time_info has unexpected length: {len(time_info)}")
                time_exceeded, remaining_seconds = False, interview_duration
        
        
        else:
            # Handle case where it's not returning a tuple
            time_exceeded = False
            remaining_seconds = interview_duration
        
        return jsonify({
            'status': 'success',
            'question': first_question,
            'remaining_seconds': remaining_seconds,
            'has_time_limit': interview_duration > 0
        })
    except Exception as e:
        print(f"Error starting interview: {e}")
        return jsonify({'status': 'error', 'message': f'An error occurred: {str(e)}'}), 500

@app.route('/report/<interview_id>')
def report(interview_id):
    """Serve the interview report for the given interview ID."""
    interview_dir = os.path.join('data/interviews', interview_id)
    
    # Check if the interview directory exists
    if not os.path.exists(interview_dir):
        return "Interview not found", 404
    
    # Check if the summary report exists
    summary_path = os.path.join(interview_dir, 'summary.json')
    if not os.path.exists(summary_path):
        return "Report not generated yet. The interview may not be complete.", 404
    
    # Load agent state and conversation history
    try:
        # Load summary
        with open(summary_path, 'r') as f:
            summary_data = json.load(f)
        
        # Load agent state
        with open(os.path.join(interview_dir, 'agent_state.json'), 'r') as f:
            agent_state = json.load(f)
        
        # Load conversation history
        conversation_path = os.path.join(interview_dir, 'conversation.json')
        conversation_transcript = []
        if os.path.exists(conversation_path):
            with open(conversation_path, 'r') as f:
                conversation_data = json.load(f)
                history = conversation_data.get('history', [])
                
                # Format conversation for transcript
                for entry in history:
                    conversation_transcript.append({
                        'speaker': entry.get('speaker', 'Unknown'),
                        'text': entry.get('text', ''),
                        'timestamp': conversation_data.get('interview_start_time', 0)
                    })
        
        # Add the conversation transcript to the summary data
        summary_data['conversation_transcript'] = conversation_transcript
        
        # Add interview date
        if 'interview_start_time' in conversation_data:
            try:
                start_time = float(conversation_data['interview_start_time'])
                summary_data['interview_date'] = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M')
            except (ValueError, TypeError) as e:
                print(f"Error formatting interview date: {e}")
                summary_data['interview_date'] = 'Unknown'
        
        # Get candidate name and job title
        candidate_name = agent_state['candidate_info'].get('name', 'Unknown')
        job_title = agent_state['job_info'].get('title', 'Unknown')
        
        # Make sure required fields exist in summary
        if 'areas_for_improvement' not in summary_data and 'areas_for_development' in summary_data:
            summary_data['areas_for_improvement'] = summary_data['areas_for_development']
        
        # Ensure all required score fields exist
        score_fields = ['overall_score', 'technical_score', 'experience_relevance_score', 
                       'skill_match_score', 'cultural_fit_score', 'communication_score']
        for field in score_fields:
            if field not in summary_data:
                summary_data[field] = 0
        
        # Set default recommendation if missing
        if 'recommendation' not in summary_data:
            summary_data['recommendation'] = "No Recommendation"
        
        # Calculate skill match percentage if missing
        if 'skill_match_percentage' not in summary_data:
            summary_data['skill_match_percentage'] = summary_data.get('skill_match_score', 0)
        
        print(f"DEBUG: Summary data keys: {summary_data.keys()}")
        
        return render_template('report.html', 
                               summary=summary_data, 
                               interview_id=interview_id,
                               candidate_name=candidate_name,
                               job_title=job_title)
    
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error generating report: {e}")
        print(f"Error traceback: {error_traceback}")
        return f"Error generating report: {str(e)}", 500

# Add the rest of your routes here

# Start the server when run directly
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

def check_time_limit(self) -> Tuple[bool, int]:
    """
    Check if the interview has exceeded the time limit.
    
    Returns:
        Tuple[bool, int]: A tuple containing:
            - time_exceeded (bool): Whether the time limit has been exceeded.
            - remaining_seconds (int): The remaining time in seconds, or 0 if exceeded.
    """
    if not self.interview_max_duration:
        # No time limit set
        return False, None

    elapsed_time = time.time() - self.interview_start_time
    remaining_seconds = int(self.interview_max_duration * 60 - elapsed_time)

    if remaining_seconds <= 0:
        return True, 0  # Time limit exceeded
    else:
        return False, remaining_seconds