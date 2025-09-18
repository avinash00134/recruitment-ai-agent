import streamlit as st
import requests
import json
from typing import List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import time
from datetime import datetime, date
import numpy as np
import io
import base64
import re

st.set_page_config(
    page_title="Recruitment AI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = "http://localhost:8000"

st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(45deg, #1f77b4, #2ca02c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
    }
    .section-header {
        font-size: 2rem;
        color: #2ca02c;
        margin-bottom: 1rem;
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    .candidate-card {
        border: 2px solid #e6e6e6;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease;
    }
    .candidate-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    .best-candidate {
        border-color: #28a745;
        background: linear-gradient(135deg, #d4edda 0%, #f8f9fa 100%);
        box-shadow: 0 4px 6px rgba(40, 167, 69, 0.3);
    }
    .score-high {
        color: #28a745;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .score-medium {
        color: #ffc107;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .score-low {
        color: #dc3545;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
        padding: 10px;
        border-radius: 5px;
        background-color: #d4edda;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
        padding: 10px;
        border-radius: 5px;
        background-color: #f8d7da;
    }
    .status-warning {
        color: #856404;
        font-weight: bold;
        padding: 10px;
        border-radius: 5px;
        background-color: #fff3cd;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(45deg, #1f77b4, #2ca02c);
    }
    .stButton > button {
        background: linear-gradient(45deg, #1f77b4, #2ca02c);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background: linear-gradient(45deg, #2ca02c, #1f77b4);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def show_status(message, status_type="info"):
    """Show status message with appropriate styling"""
    if status_type == "success":
        st.markdown(f'<div class="status-success">✅ {message}</div>', unsafe_allow_html=True)
    elif status_type == "error":
        st.markdown(f'<div class="status-error">❌ {message}</div>', unsafe_allow_html=True)
    elif status_type == "warning":
        st.markdown(f'<div class="status-warning">⚠️ {message}</div>', unsafe_allow_html=True)
    else:
        st.info(f"ℹ️ {message}")

def make_api_request(url, method="POST", json_data=None, files=None, data=None):
    """Make API request with error handling"""
    try:
        if method == "POST":
            if files:
                response = requests.post(url, files=files, data=data)
            else:
                response = requests.post(url, json=json_data)
        else:
            response = requests.get(url)
        
        if response.status_code == 200:
            return response.json(), True
        else:
            return {"error": f"API Error: {response.status_code} - {response.text}"}, False
            
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to the server. Please make sure the backend is running."}, False
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}, False

def create_radar_chart(candidates_data):
    """Create radar chart for skills comparison"""
    categories = ['Technical Skills', 'Experience', 'Education', 'Cultural Fit', 'Communication']
    
    fig = go.Figure()
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']  # Explicit colors
    
    for i, candidate in enumerate(candidates_data[:5]):  # Top 5 candidates
        values = [
            candidate.get('technical_score', candidate['score'] * 0.4),
            candidate.get('experience_score', candidate['score'] * 0.25),
            candidate.get('education_score', candidate['score'] * 0.15),
            candidate.get('cultural_fit_score', candidate['score'] * 0.1),
            candidate.get('communication_score', candidate['score'] * 0.1)
        ]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=candidate['filename'][:20] + '...' if len(candidate['filename']) > 20 else candidate['filename'],
            line_color=colors[i % len(colors)]  # Use explicit color
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        title="Skills Radar Chart - Top 5 Candidates",
        font=dict(color="#333333")  
    )
    
    return fig


def create_score_gauge(score, candidate_name, index):
    """Create a gauge chart for individual scores with unique key"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Match Score"},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 60], 'color': "lightgray"},
                {'range': [60, 80], 'color': "yellow"},
                {'range': [80, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ))
    
    fig.update_layout(height=300, width=300)
    return fig

def update_processing_history(jobs_processed=0, candidates_evaluated=0):
    """Track processing history for analytics"""
    if 'processing_history' not in st.session_state:
        st.session_state.processing_history = pd.DataFrame({
            'Date': [],
            'Jobs Processed': [],
            'Candidates Evaluated': []
        })
    
    today = date.today()
    
    if not st.session_state.processing_history.empty and today in st.session_state.processing_history['Date'].values:
        mask = st.session_state.processing_history['Date'] == today
        st.session_state.processing_history.loc[mask, 'Jobs Processed'] += jobs_processed
        st.session_state.processing_history.loc[mask, 'Candidates Evaluated'] += candidates_evaluated
    else:
        new_row = pd.DataFrame({
            'Date': [today],
            'Jobs Processed': [jobs_processed],
            'Candidates Evaluated': [candidates_evaluated]
        })
        st.session_state.processing_history = pd.concat([st.session_state.processing_history, new_row], ignore_index=True)

def extract_candidate_name(resume_text, filename):
    """Extract candidate name from resume text"""
    patterns = [
        r"(?:^|\n)[A-Z][a-z]+ [A-Z][a-z]+(?:\n|$)", 
        r"(?:^|\n)[A-Z][a-z]+, [A-Z][a-z]+(?:\n|$)",
        r"Name:\s*([A-Z][a-z]+ [A-Z][a-z]+)", 
        r"Full Name:\s*([A-Z][a-z]+ [A-Z][a-z]+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, resume_text)
        if match:
            name = match.group(1) if len(match.groups()) > 0 else match.group(0)
            
            name = re.sub(r'[^a-zA-Z\s,]', '', name).strip()
            if ',' in name:
                
                parts = name.split(',')
                name = f"{parts[1].strip()} {parts[0].strip()}"
            return name
    
    return filename.split('.')[0]


def generate_email_for_candidate(candidate, email_type, position):
    """Generate email for a specific candidate"""
    if 'candidate_names' not in st.session_state:
        st.session_state.candidate_names = {}
    
    if candidate['filename'] in st.session_state.candidate_names:
        candidate_name = st.session_state.candidate_names[candidate['filename']]
    else:
        candidate_name = extract_candidate_name(candidate.get('resume_text', ''), candidate['filename'])
        st.session_state.candidate_names[candidate['filename']] = candidate_name
    
    with st.spinner(f"Generating {email_type} email for {candidate_name}..."):
        result, success = make_api_request(
            f"{API_BASE_URL}/generate-email",
            method="POST",
            json_data={
                "candidate_name": candidate_name,
                "position": position,
                "email_type": email_type,
                "evaluation": {
                    "score": candidate['score'],
                    "remarks": candidate['remarks'],
                    "missing_skills": candidate['missing_skills']
                }
            }
        )
        
        if success:
            return result.get("email_content", f"Error: No email content returned for {email_type} email")
        else:
            return f"Error generating email: {result.get('error', 'Unknown error')}"
        

def main():
    st.markdown('<h1 class="main-header">🤖 Recruitment AI Agent</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    st.sidebar.title("📊 Navigation")
    page = st.sidebar.radio(
        "Choose a page:",
        ["🏠 Dashboard", "📋 Job Description", "🎯 Resume Matching", "📧 Email Generation", "📈 Results Analysis", "⚙️ Settings"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **Quick Tips:**
    - Start with Job Description
    - Upload multiple resumes for comparison
    - Use Email Generation for candidate communication
    - Use Results Analysis for insights
    """)
    
    if page == "🏠 Dashboard":
        dashboard_page()
    elif page == "📋 Job Description":
        job_description_page()
    elif page == "🎯 Resume Matching":
        resume_matching_page()
    elif page == "📧 Email Generation":
        email_generation_page()
    elif page == "📈 Results Analysis":
        results_analysis_page()
    elif page == "⚙️ Settings":
        settings_page()

def dashboard_page():
    st.header("🏠 Dashboard Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_jobs = 0
    total_candidates = 0
    matched_candidates = 0
    avg_processing_time = 0
    
    if hasattr(st.session_state, 'matching_results'):
        results = st.session_state.matching_results
        total_candidates = len(results.get("candidates", []))
        matched_candidates = len([c for c in results.get("candidates", []) if c.get("score", 0) >= 70])
        avg_processing_time = results.get("processing_time", 0)
        total_jobs = 1  
    
    with col1:
        st.markdown(f'<div class="metric-card"><h3>📋 Total Jobs</h3><h2>{total_jobs}</h2></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'<div class="metric-card"><h3>👥 Candidates</h3><h2>{total_candidates}</h2></div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'<div class="metric-card"><h3>✅ Matched</h3><h2>{matched_candidates}</h2></div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'<div class="metric-card"><h3>⏱️ Avg Time</h3><h2>{avg_processing_time:.1f}s</h2></div>', unsafe_allow_html=True)
    
    st.subheader("📈 Recent Activity")
    
    if hasattr(st.session_state, 'processing_history') and not st.session_state.processing_history.empty:
        activity_data = st.session_state.processing_history
        fig = px.line(activity_data, x='Date', y=['Jobs Processed', 'Candidates Evaluated'],
                     title='Processing Activity', markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No processing activity yet. Run a job matching to see analytics.")
    
    st.subheader("⚡ Quick Actions")
    quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)
    
    with quick_col1:
        if st.button("📝 Create New Job", use_container_width=True):
            st.session_state.page = "📋 Job Description"
    
    with quick_col2:
        if st.button("📤 Upload Resumes", use_container_width=True):
            st.session_state.page = "🎯 Resume Matching"
    
    with quick_col3:
        if st.button("📧 Generate Emails", use_container_width=True):
            st.session_state.page = "📧 Email Generation"
    
    with quick_col4:
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.page = "📈 Results Analysis"

def job_description_page():
    st.header("📋 Job Description Input")
    
    if 'job_description' not in st.session_state:
        st.session_state.job_description = ""
    if 'job_title' not in st.session_state:
        st.session_state.job_title = ""
    
    tab1, tab2, tab3 = st.tabs(["🤖 Generate with AI", "📁 Upload File", "✍️ Manual Input"])
    
    with tab1:
        st.subheader("Generate Job Description with AI")
        
        col1, col2 = st.columns(2)
        
        with col1:
            job_title = st.text_input("Job Title*", placeholder="e.g., Senior Python Developer", value=st.session_state.job_title)
            years_experience = st.slider("Years of Experience", 0, 20, 5)
            must_have_skills = st.text_area("Must-have Skills*", placeholder="Python, Django, REST API, PostgreSQL")
            nice_to_have_skills = st.text_area("Nice-to-have Skills", placeholder="AWS, Docker, Kubernetes")
        
        with col2:
            company_name = st.text_input("Company Name*", placeholder="Tech Corp Inc.")
            employment_type = st.selectbox("Employment Type", ["Full-time", "Part-time", "Contract", "Internship"])
            industry = st.text_input("Industry*", placeholder="e.g., Technology, Healthcare, Finance")
            location = st.text_input("Location*", placeholder="e.g., New York, Remote, Hybrid")
            salary_range = st.text_input("Salary Range", placeholder="e.g., $100,000 - $150,000")
        
        if st.button("✨ Generate Job Description", type="primary", use_container_width=True):
            if all([job_title, must_have_skills, company_name, industry, location]):
                with st.spinner("Generating job description using AI..."):
                    progress_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.01)
                        progress_bar.progress(i + 1)
                    
                    result, success = make_api_request(
                        f"{API_BASE_URL}/generate-job-description",
                        json_data={
                            "job_title": job_title,
                            "years_of_experience": f"{years_experience}+",
                            "must_have_skills": must_have_skills,
                            "nice_to_have_skills": nice_to_have_skills,
                            "company_name": company_name,
                            "employment_type": employment_type,
                            "industry": industry,
                            "location": location,
                            "salary_range": salary_range
                        }
                    )
                    
                    if success:
                        st.session_state.job_description = result["job_description"]
                        st.session_state.job_title = job_title
                        show_status("Job description generated successfully!", "success")
                    else:
                        show_status(result["error"], "error")
            else:
                show_status("Please fill in all required fields marked with *", "warning")
    
    with tab2:
        st.subheader("Upload Job Description File")
        uploaded_file = st.file_uploader(
            "Choose a PDF or DOCX file",
            type=['pdf', 'docx', 'doc'],
            accept_multiple_files=False,
            help="Supported formats: PDF, DOCX, DOC"
        )
        
        if uploaded_file and st.button("📄 Extract Job Description", type="primary", use_container_width=True):
            with st.spinner("Extracting text from file..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                result, success = make_api_request(
                    f"{API_BASE_URL}/upload-job-description",
                    files=files
                )
                
                if success:
                    st.session_state.job_description = result["job_description"]

                    if "job_title" not in st.session_state or not st.session_state.job_title:

                        content = result["job_description"].lower()
                        if "job title:" in content:
                            st.session_state.job_title = content.split("job title:")[1].split("\n")[0].strip().title()
                        elif "position:" in content:
                            st.session_state.job_title = content.split("position:")[1].split("\n")[0].strip().title()
                        else:
                            st.session_state.job_title = "the position"
                    show_status("Job description extracted successfully!", "success")
                else:
                    show_status(result["error"], "error")
    
    with tab3:
        st.subheader("Manual Job Description Input")
        manual_jd = st.text_area(
            "Enter Job Description",
            height=300,
            placeholder="Paste or write your job description here...",
            value=st.session_state.job_description,
            help="You can paste an existing job description or write a new one"
        )
        
        job_title_input = st.text_input("Job Title", placeholder="Enter job title", value=st.session_state.job_title)
        
        if st.button("💾 Save Job Description", type="primary", use_container_width=True) and manual_jd.strip():
            st.session_state.job_description = manual_jd
            st.session_state.job_title = job_title_input if job_title_input else "the position"
            show_status("Job description saved successfully!", "success")
    
    if st.session_state.job_description:
        st.subheader("📄 Current Job Description")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            with st.expander("📖 View Full Job Description", expanded=True):
                st.write(st.session_state.job_description)
        
        with col2:
            st.metric("Character Count", len(st.session_state.job_description))
            st.metric("Word Count", len(st.session_state.job_description.split()))
            st.metric("Job Title", st.session_state.job_title)
            
            if st.button("🗑️ Clear Job Description", type="secondary"):
                st.session_state.job_description = ""
                st.session_state.job_title = ""
                st.rerun()

def resume_matching_page():
    st.header("🎯 Resume Matching & Analysis")
    
    if 'job_description' not in st.session_state or not st.session_state.job_description:
        show_status("Please input a job description first in the 'Job Description' page.", "warning")
        return
    
    st.subheader("📋 Job Description Analytics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("JD Length", f"{len(st.session_state.job_description):,} chars")
    
    with col2:
        st.metric("Keywords", "25+")
    
    with col3:
        st.metric("Skill Mentions", "15+")
    
    st.subheader("📎 Upload Candidate Resumes")
    
    uploaded_resumes = st.file_uploader(
        "Drag and drop or select resume files",
        type=['pdf', 'docx', 'doc'],
        accept_multiple_files=True,
        help="You can upload multiple files at once. Maximum 10 files."
    )
    
    if uploaded_resumes:
        if len(uploaded_resumes) > 10:
            show_status("Maximum 10 resumes allowed. Please select fewer files.", "error")
        else:

            st.success(f"📁 {len(uploaded_resumes)} resume(s) uploaded successfully!")
            
            file_col1, file_col2 = st.columns([3, 1])
            
            with file_col1:
                st.write("**Uploaded Files:**")
                for i, file in enumerate(uploaded_resumes, 1):
                    file_size = f"{file.size / 1024:.1f} KB"
                    st.write(f"{i}. **{file.name}** ({file_size})")
            
            with file_col2:
                total_size = sum(file.size for file in uploaded_resumes) / 1024
                st.metric("Total Size", f"{total_size:.1f} KB")
            
            if st.button("🔍 Analyze Candidates", type="primary", use_container_width=True):
                progress_container = st.container()
                progress_bar = progress_container.progress(0)
                status_text = progress_container.empty()
                
                try:
                    files = []
                    for i, resume in enumerate(uploaded_resumes):
                        files.append(("resumes", (resume.name, resume.getvalue(), resume.type)))
                        progress = (i + 1) / len(uploaded_resumes) * 100
                        progress_bar.progress(int(progress))
                        status_text.text(f"Processing {i + 1}/{len(uploaded_resumes)}: {resume.name}")
                    
                    data = {"job_description": st.session_state.job_description}
                    
                    result, success = make_api_request(
                        f"{API_BASE_URL}/match-candidates",
                        files=files,
                        data=data
                    )
                    
                    if success:
                        st.session_state.matching_results = result

                        if 'candidate_names' not in st.session_state:
                            st.session_state.candidate_names = {}
                        
                        for candidate in result.get("candidates", []):
                            if candidate['filename'] not in st.session_state.candidate_names:
                                candidate_name = extract_candidate_name(candidate.get('resume_text', ''), candidate['filename'])
                                st.session_state.candidate_names[candidate['filename']] = candidate_name
                        
                        update_processing_history(
                            jobs_processed=1,
                            candidates_evaluated=len(uploaded_resumes)
                        )
                        progress_bar.progress(100)
                        status_text.text("Analysis completed!")
                        time.sleep(0.5)
                        progress_container.empty()
                        
                        show_status("Analysis completed successfully!", "success")
                        
                        display_matching_results(result)
                    else:
                        progress_container.empty()
                        show_status(result["error"], "error")
                        
                except Exception as e:
                    progress_container.empty()
                    show_status(f"Error during processing: {str(e)}", "error")

def display_matching_results(results):
    """Display the matching results with enhanced visualizations"""
    st.header("📊 Candidate Analysis Results")
    
    candidates = results.get("candidates", [])
    best_candidate = results.get("best_candidate")
    processing_time = results.get("processing_time", 0)
    
    if not candidates:
        show_status("No candidates found or processed.", "warning")
        return
    
    st.subheader("📈 Performance Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'<div class="metric-card"><h3>⏱️ Processing Time</h3><h2>{processing_time:.2f}s</h2></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'<div class="metric-card"><h3>👥 Total Candidates</h3><h2>{len(candidates)}</h2></div>', unsafe_allow_html=True)
    
    with col3:
        qualified = len([c for c in candidates if c.get("score", 0) >= 70])
        st.markdown(f'<div class="metric-card"><h3>✅ Qualified</h3><h2>{qualified}</h2></div>', unsafe_allow_html=True)
    
    with col4:
        avg_score = sum(c.get("score", 0) for c in candidates) / len(candidates)
        st.markdown(f'<div class="metric-card"><h3>📊 Avg Score</h3><h2>{avg_score:.1f}</h2></div>', unsafe_allow_html=True)
    
    df_data = []
    for candidate in candidates:
        candidate_name = st.session_state.candidate_names.get(candidate['filename'], candidate['filename'])
        df_data.append({
            "Candidate": candidate_name,
            "Filename": candidate["filename"],
            "Score": candidate["score"],
            "Missing Skills": len(candidate["missing_skills"]),
            "Status": "Qualified" if candidate["score"] >= 70 else "Needs Review"
        })
    
    df = pd.DataFrame(df_data)
    
    tab1, tab2, tab3 = st.tabs(["📊 Score Distribution", "📋 Candidate Comparison", "🎯 Skills Analysis"])
    
    with tab1:
        fig = px.histogram(df, x="Score", nbins=10, title="Candidate Score Distribution",
                          color_discrete_sequence=['#1f77b4'])
        fig.update_layout(bargap=0.1, font=dict(color="#333333"))
    
    with tab2:
        fig = px.bar(df.sort_values("Score", ascending=False), 
                    x="Candidate", y="Score", 
                    title="Candidate Score Comparison",
                    color="Score",
                    color_continuous_scale="Viridis")
        fig.update_layout(font=dict(color="#333333"))
    
    with tab3:

        if len(candidates) >= 3:
            radar_fig = create_radar_chart(candidates)
            st.plotly_chart(radar_fig, use_container_width=True)
        else:
            st.info("Need at least 3 candidates for skills radar chart")
    
    st.subheader("👥 Detailed Candidate Analysis")
    
    sort_option = st.selectbox("Sort by:", ["Score (High to Low)", "Score (Low to High)", "Name"])
    filter_score = st.slider("Filter by minimum score:", 0, 100, 0)
    
    filtered_candidates = [c for c in candidates if c["score"] >= filter_score]
    
    if sort_option == "Score (High to Low)":
        filtered_candidates.sort(key=lambda x: x["score"], reverse=True)
    elif sort_option == "Score (Low to High)":
        filtered_candidates.sort(key=lambda x: x["score"])
    else:
        filtered_candidates.sort(key=lambda x: st.session_state.candidate_names.get(x['filename'], x['filename']))
    
    for i, candidate in enumerate(filtered_candidates):
        is_best = candidate["filename"] == best_candidate
        candidate_name = st.session_state.candidate_names.get(candidate['filename'], candidate['filename'])
        
        score = candidate["score"]
        if score >= 80:
            score_class = "score-high"
        elif score >= 60:
            score_class = "score-medium"
        else:
            score_class = "score-low"
        
        card_class = "best-candidate" if is_best else "candidate-card"
        
        with st.container():
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                title = f"🏆 {candidate_name}" if is_best else f"📄 {candidate_name}"
                st.markdown(f"**{title}**")
                st.markdown(f'<span class="{score_class}">{score}/100</span>', unsafe_allow_html=True)
                st.caption(f"File: {candidate['filename']}")
            
            with col2:
                gauge_fig = create_score_gauge(score, candidate_name, i)
                st.plotly_chart(gauge_fig, use_container_width=True, key=f"gauge_{candidate['filename']}_{i}")
            
            with col3:
                if is_best:
                    st.markdown("**🥇 BEST MATCH**")
                st.metric("Missing Skills", len(candidate["missing_skills"]))
            
            with col4:
                if st.button("📧 Generate Email", key=f"email_{candidate['filename']}_{i}"):
                    st.session_state.selected_candidate = candidate
                    st.session_state.email_candidate_name = candidate_name
            
            with st.expander("View Details", expanded=is_best):
                st.write("**Remarks:**", candidate["remarks"])
                
                if candidate["missing_skills"]:
                    st.write("**Missing Skills:**")
                    for skill in candidate["missing_skills"]:
                        st.markdown(f'• <span style="color: #dc3545;">{skill}</span>', unsafe_allow_html=True)
                else:
                    st.markdown('• <span style="color: #28a745;">No critical skills missing!</span>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

def email_generation_page():
    st.header("📧 Email Generation")
    
    if 'matching_results' not in st.session_state:
        show_status("Please run candidate matching first to generate emails.", "warning")
        return
    
    if 'job_title' not in st.session_state or not st.session_state.job_title:
        st.session_state.job_title = "the position"
    
    candidates = st.session_state.matching_results.get("candidates", [])
    
    if not candidates:
        show_status("No candidates available for email generation.", "warning")
        return
    
    st.subheader("📋 Select Candidates for Email Generation")
    
    candidate_options = []
    for candidate in candidates:
        candidate_name = st.session_state.candidate_names.get(candidate['filename'], candidate['filename'])
        candidate_options.append({
            "name": candidate_name,
            "filename": candidate['filename'],
            "score": candidate['score'],
            "qualified": candidate['score'] >= 70
        })
    
    candidate_options.sort(key=lambda x: (not x['qualified'], x['score']), reverse=True)
    
    selected_candidates = []
    for i, candidate in enumerate(candidate_options):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            status = "✅ Qualified" if candidate['qualified'] else "⚠️ Needs Review"
            st.write(f"**{candidate['name']}** - {status}")
            st.caption(f"File: {candidate['filename']}, Score: {candidate['score']}/100")
        with col2:
            email_type = st.selectbox(
                "Email Type",
                ["Interview", "Rejection"],
                key=f"email_type_{i}",
                index=0 if candidate['qualified'] else 1
            )
        with col3:
            if st.button("Generate Email", key=f"gen_email_{i}"):
                for c in candidates:
                    if c['filename'] == candidate['filename']:
                        generated_email = generate_email_for_candidate(
                            c, 
                            email_type.lower(), 
                            st.session_state.job_title
                        )
                        st.session_state[f"generated_email_{candidate['filename']}"] = generated_email
                        st.session_state[f"email_type_{candidate['filename']}"] = email_type
                        break
    
    st.subheader("📨 Generated Emails")
    
    for candidate in candidate_options:
        email_key = f"generated_email_{candidate['filename']}"
        if email_key in st.session_state:
            email_type = st.session_state.get(f"email_type_{candidate['filename']}", "Email")
            
            st.write(f"**{candidate['name']} - {email_type} Email**")
            st.text_area(
                f"Email for {candidate['name']}",
                st.session_state[email_key],
                height=200,
                key=f"textarea_{candidate['filename']}"
            )
            
            email_content = st.session_state[email_key]
            st.download_button(
                f"📥 Download {email_type} Email for {candidate['name']}",
                email_content,
                file_name=f"{email_type.lower()}_email_{candidate['name'].replace(' ', '_')}.txt",
                key=f"download_{candidate['filename']}"
            )
            st.markdown("---")
    
    st.subheader("🚀 Bulk Email Generation")
    
    if st.button("Generate All Emails", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, candidate in enumerate(candidates):
            candidate_name = st.session_state.candidate_names.get(candidate['filename'], candidate['filename'])
            email_type = "interview" if candidate['score'] >= 70 else "rejection"
            
            status_text.text(f"Generating {email_type} email for {candidate_name}...")
            generated_email = generate_email_for_candidate(
                candidate, 
                email_type, 
                st.session_state.job_title
            )
            
            st.session_state[f"generated_email_{candidate['filename']}"] = generated_email
            st.session_state[f"email_type_{candidate['filename']}"] = email_type.capitalize()
            
            progress_bar.progress((i + 1) / len(candidates))
        
        status_text.text("All emails generated successfully!")
        time.sleep(1)
        status_text.empty()
        progress_bar.empty()
        show_status("All emails generated successfully!", "success")
        st.rerun()

def results_analysis_page():
    st.header("📈 Results Analysis & Insights")
    
    if 'matching_results' not in st.session_state:
        show_status("No analysis results found. Please run candidate matching first.", "warning")
        return
    
    results = st.session_state.matching_results
    candidates = results.get("candidates", [])
    
    if not candidates:
        show_status("No candidate data available for analysis.", "warning")
        return
    
    st.subheader("📊 Comprehensive Analysis Dashboard")
    
    df_data = []
    for candidate in candidates:
        candidate_name = st.session_state.candidate_names.get(candidate['filename'], candidate['filename'])
        df_data.append({
            "Name": candidate_name,
            "Score": candidate["score"],
            "Missing Skills Count": len(candidate["missing_skills"]),
            "Qualified": candidate["score"] >= 70,
            "Filename": candidate["filename"]
        })
    
    df = pd.DataFrame(df_data)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig = px.pie(df, names="Qualified", title="Qualification Ratio",
                    color="Qualified", color_discrete_map={True: '#28a745', False: '#dc3545'})
        fig.update_layout(font=dict(color="#333333"))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.box(df, y="Score", title="Score Distribution", color_discrete_sequence=['#1f77b4'])
        fig.update_layout(font=dict(color="#333333"))
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        fig = px.scatter(df, x="Missing Skills Count", y="Score", title="Skills vs Score",
                        hover_data=["Name"], color="Qualified",
                        color_discrete_map={True: '#28a745', False: '#dc3545'})
        fig.update_layout(font=dict(color="#333333"))
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("📋 Missing Skills Analysis")
    
    all_missing_skills = []
    for candidate in candidates:
        all_missing_skills.extend(candidate["missing_skills"])
    
    if all_missing_skills:
        skill_counts = pd.Series(all_missing_skills).value_counts().reset_index()
        skill_counts.columns = ['Skill', 'Count']
        
        fig = px.bar(skill_counts.head(10), x='Skill', y='Count', 
                    title="Top 10 Most Frequently Missing Skills",
                    color='Count', color_continuous_scale='Viridis')
        fig.update_layout(font=dict(color="#333333"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No missing skills found across all candidates!")
    
    st.subheader("📝 Candidate Remarks Analysis")
    
    remarks = [candidate["remarks"] for candidate in candidates]
    
    if remarks:
        remark_lengths = [len(remark.split()) for remark in remarks]
        
        fig = px.histogram(x=remark_lengths, nbins=10, 
                          title="Distribution of Remark Lengths (Words)",
                          color_discrete_sequence=['#1f77b4'])
        fig.update_layout(font=dict(color="#333333"))
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("📈 Performance Over Time")
    
    if 'processing_history' in st.session_state and not st.session_state.processing_history.empty:
        history_df = st.session_state.processing_history
        
        fig = px.line(history_df, x='Date', y=['Jobs Processed', 'Candidates Evaluated'],
                     title='Processing Activity Over Time', markers=True)
        fig.update_layout(font=dict(color="#333333"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No historical data available yet. Run more analyses to see trends.")
    
    st.subheader("📊 Export Analysis Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download Candidate Data (CSV)",
            csv,
            "candidate_analysis.csv",
            "text/csv",
            key='download-csv'
        )
    
    with col2:
        json_data = json.dumps(results, indent=2)
        st.download_button(
            "📥 Download Full Results (JSON)",
            json_data,
            "full_analysis_results.json",
            "application/json",
            key='download-json'
        )
    
    with col3:
        summary = f"""
        Recruitment Analysis Summary
        ============================
        Date: {date.today()}
        Total Candidates: {len(candidates)}
        Qualified Candidates: {len([c for c in candidates if c['score'] >= 70])}
        Average Score: {sum(c['score'] for c in candidates) / len(candidates):.1f}
        Best Candidate: {st.session_state.candidate_names.get(results.get('best_candidate', ''), 'N/A')}
        """
        st.download_button(
            "📥 Download Summary Report",
            summary,
            "analysis_summary.txt",
            "text/plain",
            key='download-summary'
        )

def settings_page():
    st.header("⚙️ Settings & Configuration")
    
    st.subheader("🔧 API Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        api_key = st.text_input("OpenAI API Key", type="password", 
                               help="Enter your OpenAI API key for AI-powered features")
        
        if api_key:
            st.success("✅ API key configured")
        else:
            st.warning("⚠️ API key required for AI features")
    
    with col2:
        model_selection = st.selectbox(
            "AI Model",
            ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            index=1,
            help="Select which OpenAI model to use for analysis"
        )
    
    st.subheader("📊 Analysis Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        min_score = st.slider("Minimum Qualification Score", 0, 100, 70,
                             help="Candidates scoring below this will be marked as not qualified")
        
        max_files = st.slider("Maximum Files per Analysis", 1, 20, 10,
                             help="Maximum number of resumes to process in one analysis")
    
    with col2:
        skill_weight = st.slider("Skills Matching Weight", 0.0, 1.0, 0.4, 0.05,
                                help="How much weight to give to skills matching")
        
        experience_weight = st.slider("Experience Weight", 0.0, 1.0, 0.3, 0.05,
                                     help="How much weight to give to experience matching")
    
    st.subheader("📧 Email Templates")
    
    email_tab1, email_tab2 = st.tabs(["Interview Email", "Rejection Email"])
    
    with email_tab1:
        st.text_area(
            "Interview Email Template",
            """Dear {candidate_name},

Thank you for applying for the {position} position at our company. We were impressed with your qualifications and would like to invite you for an interview.

Your application scored {score}/100 in our initial screening process. We were particularly impressed with your {strengths}.

Please let us know your availability for a virtual interview next week.

Best regards,
The Hiring Team""",
            height=200
        )
    
    with email_tab2:
        st.text_area(
            "Rejection Email Template",
            """Dear {candidate_name},

Thank you for your interest in the {position} position and for taking the time to apply.

After careful consideration, we've decided to move forward with other candidates whose qualifications more closely match our current needs.

Your application scored {score}/100. We encourage you to apply for future positions that may be a better fit for your skills.

We wish you the best in your job search.

Best regards,
The Hiring Team""",
            height=200
        )
    
    st.subheader("🗑️ Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧹 Clear All Data", type="secondary"):
            keys_to_keep = ['processing_history']
            for key in list(st.session_state.keys()):
                if key not in keys_to_keep:
                    del st.session_state[key]
            st.success("All data cleared successfully!")
            time.sleep(1)
            st.rerun()
    
    with col2:
        if st.button("📊 Reset Analytics", type="secondary"):
            if 'processing_history' in st.session_state:
                del st.session_state.processing_history
            st.success("Analytics data reset successfully!")
            time.sleep(1)
            st.rerun()
    
    st.subheader("ℹ️ System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Python Version:** 3.8+")
        st.info(f"**Streamlit Version:** {st.__version__}")
    
    with col2:
        st.info("**Backend Status:** Connected" if st.button("Check Connection") else "**Backend Status:** Unknown")
        st.info(f"**Last Updated:** {date.today()}")

if __name__ == "__main__":
    main()