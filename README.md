# Recruitment AI Agent

A full-stack application that helps HR professionals evaluate candidates by comparing resumes against job descriptions using AI.

## Features

- **Multiple JD Input Methods**: Upload files, manual input, or AI-generated job descriptions
- **Resume Evaluation**: Compare up to 10 resumes against a job description
- **AI-Powered Analysis**: Get matching scores, missing skills, and remarks
- **Email Generation**: Create personalized interview and rejection emails
- **User-Friendly Interface**: Streamlit frontend with clear results display

## AI Model Choices

This project uses OpenAI's GPT-3.5-turbo model for all AI functionalities:

1. **Job Description Generation**: 
   - Why: GPT-3.5-turbo produces coherent, structured job descriptions from minimal inputs
   - Performance: Fast response times, high-quality output
   - Cost: Lower cost compared to GPT-4 while maintaining good quality

2. **Resume Evaluation**:
   - Why: Strong pattern recognition for matching skills and experiences
   - Performance: Consistent scoring with explainable results
   - Cost: Efficient for batch processing multiple resumes

3. **Email Generation**:
   - Why: Natural language generation for professional, personalized emails
   - Performance: Creates context-aware emails quickly
   - Cost: Minimal tokens required for email generation

## Setup Instructions
