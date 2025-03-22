from flask import Flask, render_template, request, jsonify, session, send_from_directory, redirect, url_for
import os
import json
import uuid
from datetime import datetime
import time
import glob

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

@app.route('/interview/<interview_id>')
def interview(interview_id):
    """Render the interview page"""
    interview_dir = os.path.join('data/interviews', interview_id)
    
    # Check if interview exists
    if not os.path.exists(interview_dir):
        return "Interview not found", 404
    
    # Load agent state
    with open(os.path.join(interview_dir, 'agent_state.json'), 'r') as f:
        agent_state = json.load(f)
    
    # Set session
    session['interview_id'] = interview_id
    
    # Get interview duration
    interview_duration = agent_state.get('interview_duration', 0)
    
    return render_template('interview.html', 
                          interview_id=interview_id,
                          job_title=agent_state['job_info']['title'],
                          candidate_name=agent_state['candidate_info']['name'],
                          interview_duration=interview_duration)

@app.route('/report/<interview_id>')
def report(interview_id):
    """Render the interview report page"""
    interview_dir = os.path.join('data/interviews', interview_id)
    
    # Check if interview exists
    if not os.path.exists(interview_dir):
        return "Interview not found", 404
    
    # Check if summary exists
    summary_path = os.path.join(interview_dir, 'summary.json')
    if not os.path.exists(summary_path):
        return "Interview not complete", 400
    
    # Load summary
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    
    # Load agent state for additional information
    with open(os.path.join(interview_dir, 'agent_state.json'), 'r') as f:
        agent_state = json.load(f)
    
    return render_template('report.html', 
                         interview_id=interview_id,
                         summary=summary,
                         job_title=agent_state['job_info']['title'],
                         candidate_name=agent_state['candidate_info']['name'])

@app.route('/reports')
def reports_list():
    """List all interview reports"""
    # Get all report files
    report_files = glob.glob('data/reports/*.json')
    reports = []
    
    for file_path in report_files:
        try:
            with open(file_path, 'r') as f:
                report_data = json.load(f)
                
            # Extract filename for the report ID
            filename = os.path.basename(file_path)
            
            # Basic report info
            report_info = {
                'report_id': filename,
                'candidate_name': report_data.get('candidate_name', 'Unknown'),
                'job_title': report_data.get('job_title', 'Unknown'),
                'interview_date': report_data.get('interview_date', 'Unknown'),
                'overall_score': report_data.get('overall_score', 0),
                'recommendation': report_data.get('recommendation', 'Unknown'),
                'interview_duration_minutes': report_data.get('interview_duration_minutes', 0)
            }
            
            reports.append(report_info)
        except Exception as e:
            # Skip files with errors
            continue
    
    # Sort by date (newest first)
    reports.sort(key=lambda x: x['interview_date'], reverse=True)
    
    return render_template('reports_list.html', reports=reports)

@app.route('/view-report/<report_id>')
def view_report(report_id):
    """View a specific report"""
    report_path = os.path.join('data/reports', report_id)
    
    if not os.path.exists(report_path):
        return "Report not found", 404
        
    with open(report_path, 'r') as f:
        report_data = json.load(f)
        
    return render_template('view_report.html', report=report_data, report_id=report_id)

@app.route('/api/reports/download/<report_id>')
def download_report(report_id):
    """Download a report file"""
    return send_from_directory('data/reports', report_id, as_attachment=True)

@app.route('/api/start-interview', methods=['POST'])
def start_interview():
    """Start the interview"""
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
    
    # Get remaining time information
    time_exceeded, remaining_seconds = agent.check_time_limit()
    
    return jsonify({
        'status': 'success',
        'question': first_question,
        'remaining_seconds': remaining_seconds,
        'has_time_limit': interview_duration > 0
    })

@app.route('/api/process-response', methods=['POST'])
def process_response():
    """Process a candidate's response"""
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
        agent.match_analysis
    )
    
    # Restore conversation state
    agent.conversation_manager.conversation_history = conversation_state['history']
    agent.conversation_manager.current_question_index = conversation_state['current_index']
    agent.interview_in_progress = True
    agent.interview_complete = conversation_state.get('complete', False)
    
    # Process the response
    result = agent.process_candidate_response(response)
    
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
        with open(os.path.join(interview_dir, 'summary.json'), 'w') as f:
            json.dump(agent.interview_summary, f, indent=2)
    
    return jsonify({
        'status': 'success',
        'question': result['next_question'],
        'is_complete': result['is_complete'],
        'remaining_seconds': result.get('remaining_seconds'),
        'time_limit_exceeded': result.get('time_limit_exceeded', False)
    })

@app.route('/api/interview-summary/<interview_id>')
def get_interview_summary(interview_id):
    """Get the interview summary data"""
    interview_dir = os.path.join('data/interviews', interview_id)
    
    # Check if interview exists
    if not os.path.exists(interview_dir):
        return jsonify({'status': 'error', 'message': 'Interview not found'}), 404
    
    # Check if summary exists
    summary_path = os.path.join(interview_dir, 'summary.json')
    if not os.path.exists(summary_path):
        return jsonify({'status': 'error', 'message': 'Interview not complete'}), 400
    
    # Load summary
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    
    return jsonify({
        'status': 'success',
        'summary': summary
    })

# Start the server when run directly
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)