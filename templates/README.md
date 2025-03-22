# AI Interview Agent

A proof-of-concept AI-powered interview agent that simulates job interviews based on job postings and candidate resumes.

## Features

- **Document Analysis**: Extracts key information from job postings and resumes
- **Personalized Questions**: Generates interview questions tailored to the job and candidate
- **Natural Conversation**: Conducts a flowing interview with appropriate follow-up questions
- **Comprehensive Evaluation**: Provides detailed candidate assessment and scoring
- **Voice Interaction**: Supports text-to-speech for a more immersive interview experience

## Project Structure

```
ai-interview-agent/
├── app.py                      # Main Flask application
├── document_processor.py       # Document processing module
├── question_generator.py       # Question generation module
├── conversation_manager.py     # Interview conversation module
├── interview_agent.py          # Main interview agent class
├── run.py                      # Script to run the application
├── requirements.txt            # Project dependencies
├── README.md                   # Project documentation
├── data/                       # Directory for interview data
│   ├── interviews/             # Store interview sessions
│   └── uploads/                # Store uploaded files
└── templates/                  # HTML templates
    ├── base.html               # Base template
    ├── index.html              # Homepage
    ├── setup_interview.html    # Interview setup page
    ├── interview.html          # Interactive interview page
    └── report.html             # Interview report page
```

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/ai-interview-agent.git
cd ai-interview-agent
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Download NLTK data:

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

## Usage

1. Start the application:

```bash
python run.py
```

2. Open your browser and go to `http://localhost:5000`

3. Create a new interview by providing:
   - Job posting
   - Company profile
   - Candidate resume

4. Start the interview and answer the questions as the candidate

5. View the detailed evaluation report after the interview

## VS Code Setup

1. Install VS Code extensions:
   - Python
   - Pylance
   - Python Indent

2. Open the project folder in VS Code

3. Select the Python interpreter from your virtual environment
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Python: Select Interpreter"
   - Choose the interpreter from your virtual environment

4. Set up debugging:
   - Click on the Run and Debug icon in the sidebar
   - Click "create a launch.json file"
   - Select "Python" as the environment
   - Choose "Flask" as the debug configuration template
   - Modify the configuration to point to `app.py`

## Extending the Project

### Adding Voice Recognition

To add speech-to-text functionality:

1. Install additional dependencies:
```bash
pip install SpeechRecognition
pip install pyaudio
```

2. Update the web interface to capture audio and convert it to text

### Improving Question Generation

The question generation can be enhanced by:

- Integrating with a large language model API
- Adding industry-specific question templates
- Implementing more sophisticated follow-up question logic

### Adding Video Interviews

To support video interviews:

1. Integrate WebRTC for video streaming
2. Implement facial expression analysis for additional candidate evaluation
3. Add screen sharing capability for technical assessments

## License

MIT License