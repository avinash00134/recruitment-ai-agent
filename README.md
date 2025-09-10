# Recruitment AI Agent 🤖

An intelligent AI-powered recruitment system that automates job description generation, resume matching, candidate evaluation, and personalized email communication.

## 🌟 Features

### Core Functionality
- **🤖 AI-Powered Job Description Generation**: Create comprehensive job descriptions with customizable parameters
- **🎯 Resume Matching & Evaluation**: Automatically evaluate candidates against job requirements using AI
- **📊 Candidate Comparison Dashboard**: Visual analytics and scoring for multiple candidates
- **📧 Personalized Email Generation**: Create interview invitations and rejection emails with AI
- **📈 Advanced Analytics**: Interactive visualizations and insights for hiring decisions
- **📁 Multi-format Support**: Process PDF and DOC/DOCX files for both job descriptions and resumes

### Key Capabilities
- Intelligent resume parsing and analysis
- Skills gap identification and recommendations
- Automated candidate ranking and scoring
- Professional email template generation
- Real-time progress tracking
- Comprehensive evaluation reports

## 🚀 Quick Start

### Prerequisites

Ensure you have the following installed on your system:
- **Python 3.9+**
- **OpenAI API key** (required for AI functionality)
- **pip** (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/avinash00134/recruitment-ai-agent
   cd recruitment-ai-agent
   ```

2. **Create and activate virtual environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the root directory:
   ```bash
   # Create .env file with required configuration
   echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
   echo "MODEL_NAME=gpt-3.5-turbo" >> .env
   echo "DEBUG=False" >> .env
   echo "MAX_RESUMES=10" >> .env
   echo "APP_NAME=Recruitment AI Agent" >> .env
   echo "APP_VERSION=1.0.0" >> .env
   ```

### Running the Application

#### Option 1: Backend API Only
```bash
cd app
python main.py
```
✅ API server will be available at `http://localhost:8000`

#### Option 2: Frontend Only (requires backend running)
```bash
cd frontend
streamlit run streamlit_app.py
```
✅ Streamlit interface will be available at `http://localhost:8501`

#### Option 3: Full Application (Recommended)

**Terminal 1 - Start Backend:**
```bash
cd app
python main.py
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
streamlit run streamlit_app.py
```

Navigate to `http://localhost:8501` to access the complete application.

## 📁 Project Architecture

```
recruitment-ai-agent/
├── 📂 app/                    # FastAPI Backend
│   ├── 📄 __init__.py        # Package initialization
│   ├── 📄 main.py            # FastAPI application and API endpoints
│   ├── 📄 models.py          # Pydantic data models and schemas
│   ├── 📄 utils.py           # File processing and utility functions
│   ├── 📄 ai_services.py     # OpenAI integration and prompt templates
│   ├── 📄 config.py          # Configuration and settings management
│   └── 📄 logger.py          # Logging configuration and setup
├── 📂 frontend/
│   └── 📄 streamlit_app.py   # Streamlit web interface
├── 📂 logs/                   # Application log files (auto-generated)
├── 📄 requirements.txt        # Python package dependencies
├── 📄 .env                   # Environment variables (create manually)
└── 📄 README.md              # Project documentation
```

## ⚙️ Configuration

### Environment Variables

Configure your application by creating a `.env` file:

```env
# Required Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Model Configuration
MODEL_NAME=gpt-3.5-turbo        # Options: gpt-3.5-turbo, gpt-4

# Application Settings
DEBUG=False                      # Set to True for development
MAX_RESUMES=10                  # Maximum resumes to process simultaneously
APP_NAME=Recruitment AI Agent
APP_VERSION=1.0.0

# Optional Performance Settings
REQUEST_TIMEOUT=30              # API request timeout in seconds
MAX_RETRIES=3                   # Number of retry attempts for failed requests
```

### API Endpoints

The backend provides the following REST API endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/generate-job-description` | Generate AI-powered job descriptions |
| `POST` | `/upload-job-description` | Extract text from uploaded job description files |
| `POST` | `/match-candidates` | Evaluate and match resumes against job descriptions |
| `POST` | `/generate-email` | Create personalized candidate communication emails |
| `GET` | `/health` | Application health check and status |

## 🎯 How to Use

### Step 1: Create or Upload Job Description

**Option A: AI Generation**
1. Navigate to the "Job Description" section
2. Fill in job details (title, company, requirements, etc.)
3. Click "Generate with AI" for an intelligent job description

**Option B: Upload Existing**
1. Upload a job description file (PDF/DOCX format)
2. System automatically extracts and processes the content
3. Review and edit the extracted text if needed

**Option C: Manual Input**
1. Paste or type your job description directly
2. Ensure all key requirements are clearly specified

### Step 2: Upload Candidate Resumes

1. Navigate to the "Resume Upload" section
2. Upload multiple resume files (PDF/DOCX supported)
3. System processes and extracts candidate information
4. Progress bar shows real-time processing status

### Step 3: Analyze and Compare Candidates

1. Review the comprehensive candidate comparison dashboard
2. Examine individual candidate scores and rankings
3. Identify missing skills and areas of concern
4. Use interactive visualizations for detailed analysis
5. Export results for further review

### Step 4: Generate Professional Communications

1. Select candidates for interview invitations
2. Generate personalized interview emails with AI
3. Create professional rejection letters for unsuccessful candidates
4. Download email templates and customize as needed

## 🔬 Technical Specifications

### AI Models and Processing
- **Primary Model**: OpenAI GPT-3.5-turbo (configurable to GPT-4)
- **Prompt Engineering**: Custom-designed prompts for recruitment scenarios
- **Output Format**: Structured JSON responses for consistent data processing
- **Processing**: Parallel candidate evaluation for improved performance

### File Processing Capabilities
- **PDF Files**: Advanced text extraction using PyPDF2
- **Word Documents**: Native processing of DOC/DOCX files with python-docx
- **File Validation**: Comprehensive format checking and error handling
- **Size Limits**: Recommended maximum 5MB per file for optimal performance

### Performance Characteristics
- **Concurrent Processing**: Multiple resumes processed simultaneously
- **Progress Tracking**: Real-time updates and status indicators
- **Error Handling**: Robust retry logic and graceful failure management
- **Memory Optimization**: Efficient processing for large document batches

## 📊 Evaluation Framework

### Scoring Methodology

Candidates are evaluated using a comprehensive 100-point scoring system:

| Evaluation Category | Weight | Description |
|-------------------|--------|-------------|
| **Technical Skills Alignment** | 40% | Match between candidate skills and job requirements |
| **Experience Relevance** | 25% | Industry experience and role-specific background |
| **Education & Certifications** | 15% | Academic qualifications and professional certifications |
| **Cultural & Team Fit** | 10% | Soft skills and organizational alignment indicators |
| **Achievement & Impact Metrics** | 10% | Quantifiable accomplishments and career progression |

### Output Metrics
- **Overall Score**: Composite score from 0-100
- **Skill Gap Analysis**: Detailed breakdown of missing competencies
- **Recommendation Level**: Strong Recommend / Recommend / Consider / Not Recommended
- **Detailed Evaluation**: Narrative assessment of candidate strengths and concerns

## 🔒 Security and Privacy

### Data Protection
- **No Persistent Storage**: Candidate data is not stored permanently
- **Secure Transmission**: All API communications use secure protocols
- **Environment Variables**: Sensitive configuration stored securely
- **File Validation**: Comprehensive input sanitization and validation

### API Security
- **Key Management**: OpenAI API keys stored in environment variables only
- **Request Validation**: Input validation and sanitization on all endpoints
- **Error Handling**: Secure error responses without sensitive information disclosure

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. API Connection Problems
**Symptoms**: Connection refused, timeout errors
**Solutions**:
- Verify backend server is running on port 8000
- Check firewall settings and port availability
- Confirm OpenAI API key is valid and has sufficient credits

#### 2. File Upload Failures
**Symptoms**: Upload errors, processing failures
**Solutions**:
- Verify file format is PDF, DOC, or DOCX
- Check file size is under 5MB
- Ensure files are not password-protected or corrupted

#### 3. Memory and Performance Issues
**Symptoms**: Slow processing, application crashes
**Solutions**:
- Reduce `MAX_RESUMES` setting in configuration
- Process fewer candidates simultaneously
- Restart the application to clear memory

#### 4. AI Processing Errors
**Symptoms**: Empty responses, formatting issues
**Solutions**:
- Verify OpenAI API key and account status
- Check internet connectivity
- Review application logs for detailed error messages

### Logging and Debugging

- **Log Location**: `logs/recruitment_ai_YYYYMMDD.log`
- **Debug Mode**: Set `DEBUG=True` in `.env` for detailed logging
- **Log Rotation**: Daily log files with automatic cleanup
- **Error Tracking**: Comprehensive error logging with stack traces

## 📈 Performance Optimization

### Recommended Settings

**For Standard Use:**
- Model: `gpt-3.5-turbo`
- Max Resumes: `5-10`
- Processing: Sequential for accuracy

**For High Volume:**
- Model: `gpt-3.5-turbo` (cost-effective)
- Max Resumes: `3-5` per batch
- Processing: During off-peak hours

**For High Accuracy:**
- Model: `gpt-4` (premium quality)
- Max Resumes: `1-3` per batch
- Processing: Single-threaded for consistency

### Cost Optimization
- Use GPT-3.5-turbo for routine evaluations
- Reserve GPT-4 for executive-level positions
- Process candidates in smaller batches to optimize API usage
- Monitor API usage through OpenAI dashboard

## 🛠️ Development and Contributing

### Development Setup

1. **Fork and clone** the repository
2. **Create feature branch**: `git checkout -b feature/your-feature-name`
3. **Install development dependencies**: `pip install -r requirements-dev.txt`
4. **Enable debug mode**: Set `DEBUG=True` in `.env`
5. **Run tests**: `python -m pytest` (if test suite available)

### Code Standards
- Follow PEP 8 style guidelines
- Include comprehensive docstrings
- Add type hints where appropriate
- Write unit tests for new functionality

### Contribution Process
1. Create feature branch from main
2. Implement changes with proper documentation
3. Test thoroughly in development environment
4. Submit pull request with detailed description
5. Address review feedback promptly

## 📞 Support and Maintenance

### Getting Help

**For Technical Issues:**
1. Check this troubleshooting section first
2. Review application logs in `logs/` directory
3. Verify all dependencies are properly installed
4. Confirm API key configuration is correct

**For Feature Requests:**
1. Submit detailed feature request with use cases
2. Include expected behavior and benefits
3. Consider backwards compatibility implications

### System Requirements

**Minimum Requirements:**
- Python 3.9+
- 2GB RAM
- 500MB disk space
- Internet connection for AI services

**Recommended Requirements:**
- Python 3.10+
- 4GB RAM
- 1GB disk space
- High-speed internet connection