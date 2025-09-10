import os
import openai
import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import settings
from logger import logger
from models import EvaluationResult

client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

class PromptTemplates:
    """Centralized prompt templates for consistent terminology and formatting"""
    
    # System roles
    HR_PROFESSIONAL = "You are an experienced HR professional and technical writer specializing in creating compelling job descriptions and candidate communications."
    TECHNICAL_RECRUITER = "You are an expert technical recruiter with 10+ years of experience evaluating candidates across various industries. Be thorough, objective, and provide actionable insights."
    EMPLOYER_BRANDING = "You are an HR professional writing professional, compassionate emails to candidates while maintaining excellent employer branding and positive candidate experience."
    
    @staticmethod
    def get_job_description_prompt(jd_input: Dict[str, Any]) -> str:
        """Generate dynamic job description prompt"""
        return f"""
        ROLE: Senior HR Content Specialist
        TASK: Create a comprehensive, professional job description
        FORMAT: Professional business document with clear section headers
        TONE: Engaging, professional, and detailed
        
        INPUT PARAMETERS:
        - Job Title: {jd_input.get('job_title', 'Not specified')}
        - Years of Experience: {jd_input.get('years_of_experience', 'Not specified')}
        - Must-have Skills: {', '.join(jd_input.get('must_have_skills', [])) if isinstance(jd_input.get('must_have_skills'), list) else jd_input.get('must_have_skills', 'Not specified')}
        - Nice-to-have Skills: {', '.join(jd_input.get('nice_to_have_skills', [])) if isinstance(jd_input.get('nice_to_have_skills'), list) else jd_input.get('nice_to_have_skills', 'Not specified')}
        - Company Name: {jd_input.get('company_name', 'Not specified')}
        - Employment Type: {jd_input.get('employment_type', 'Full-time')}
        - Industry: {jd_input.get('industry', 'Not specified')}
        - Location: {jd_input.get('location', 'Not specified')}
        - Salary Range: {jd_input.get('salary_range', 'Competitive')}
        - Remote Policy: {jd_input.get('remote_policy', 'Not specified')}
        
        REQUIRED SECTIONS:
        1. Company Overview - Brief company background, mission, values, and culture
        2. Position Summary - Overall purpose and objectives of the role
        3. Key Responsibilities - 5-8 bullet points of primary duties
        4. Required Qualifications - Must-have skills, experience, and education
        5. Preferred Qualifications - Nice-to-have assets
        6. Compensation & Benefits - Salary range, benefits package, perks
        7. Application Process - Next steps and timeline
        
        GUIDELINES:
        - Use inclusive language and diversity statements
        - Highlight growth opportunities and career progression
        - Mention team structure and reporting lines if available
        - Include equal employment opportunity statement
        - Keep paragraphs concise and scannable
        - Use action-oriented language for responsibilities
        """

    @staticmethod
    def get_evaluation_prompt(resume_text: str, jd_text: str) -> str:
        """Generate dynamic resume evaluation prompt"""
        return f"""
        TASK: Comprehensive resume evaluation against job description
        ROLE: Senior Technical Recruiter
        EVALUATION FRAMEWORK: STAR method (Situation, Task, Action, Result)
        
        JOB DESCRIPTION CONTEXT:
        {jd_text[:2000]}... [truncated if too long]
        
        RESUME CONTENT:
        {resume_text[:3000]}... [truncated if too long]
        
        OUTPUT FORMAT: Strict JSON structure
        {{
            "score": 85.5,
            "strength_areas": ["Backend Development", "System Architecture", "Team Leadership"],
            "missing_skills": ["Python", "AWS", "Docker"],
            "experience_gap_analysis": {{
                "years_match": true,
                "industry_relevance": "High",
                "skill_transferability": "Medium"
            }},
            "cultural_fit_indicators": ["Startup experience", "Agile methodology", "Open source contributions"],
            "red_flags": ["Employment gaps", "Job hopping pattern"],
            "remarks": "Candidate shows strong backend development experience but lacks cloud infrastructure skills. Good cultural fit based on previous company experience.",
            "recommendation": "Proceed to technical screening",
            "interview_focus_areas": ["Cloud experience", "Scalability challenges", "Team management approach"]
        }}
        
        EVALUATION CRITERIA:
        1. Technical Skills Alignment (40% weight)
        2. Experience Relevance (25% weight)
        3. Education & Certifications (15% weight)
        4. Cultural & Team Fit (10% weight)
        5. Achievement & Impact Metrics (10% weight)
        
        SCORING GUIDELINES:
        - 90-100: Exceptional match, exceeds requirements
        - 80-89: Strong candidate, meets all key requirements
        - 70-79: Good potential, some skill gaps
        - 60-69: Marginal candidate, significant gaps
        - Below 60: Poor match, does not meet requirements
        
        BE OBJECTIVE AND CONSTRUCTIVE:
        - Provide specific examples from resume
        - Highlight transferable skills
        - Note potential overqualification
        - Consider career progression patterns
        - Assess communication quality through resume structure
        """

    @staticmethod
    def get_interview_email_prompt(candidate_name: str, position: str, evaluation: EvaluationResult) -> str:
        """Generate interview invitation email prompt"""
        return f"""
        TASK: Compose personalized interview invitation email
        ROLE: Talent Acquisition Specialist
        TONE: Warm, professional, enthusiastic
        
        CANDIDATE: {candidate_name}
        POSITION: {position}
        EVALUATION SCORE: {evaluation.score}/100
        STRENGTHS: {evaluation.remarks.split('.')[0] if evaluation.remarks else 'Strong technical background'}
        
        EMAIL COMPONENTS:
        1. Personalized greeting with candidate name
        2. Specific compliment referencing their experience/skills
        3. Clear excitement about their application
        4. Interview details (duration, format, participants)
        5. Preparation suggestions or topics to expect
        6. Next steps in hiring process
        7. Contact information for questions
        8. Professional closing with enthusiasm
        
        KEY MESSAGES TO INCLUDE:
        - "We were impressed with your experience in..."
        - "Your background in [specific skill] aligns well with..."
        - "We'd like to learn more about your experience with..."
        - "The interview will focus on..."
        - "We're excited about the possibility of you joining our team"
        
        FORMATTING:
        - Professional email structure
        - Appropriate line breaks and paragraphs
        - Mobile-responsive formatting
        - Clear subject line with position title
        """

    @staticmethod
    def get_rejection_email_prompt(candidate_name: str, position: str, evaluation: Optional[EvaluationResult] = None) -> str:
        """Generate rejection email prompt"""
        feedback_note = ""
        if evaluation and evaluation.score > 70:
            feedback_note = f" While your background in {evaluation.remarks.split(' ')[:5] if evaluation.remarks else 'certain areas'} was impressive, we've chosen candidates whose experience more closely matches our current needs."
        
        return f"""
        TASK: Compose compassionate rejection email
        ROLE: HR Business Partner
        TONE: Professional, kind, future-oriented
        
        CANDIDATE: {candidate_name}
        POSITION: {position}
        {f'EVALUATION NOTES: {feedback_note}' if feedback_note else ''}
        
        EMAIL COMPONENTS:
        1. Appreciation for time and interest
        2. Positive note about their qualifications
        3. Gentle notification of decision
        4. Encouragement for future opportunities
        5. Offer to keep resume on file
        6. Best wishes for job search
        7. Optional: Feedback availability statement
        
        KEY MESSAGES:
        - "Thank you for your interest in [Company]"
        - "We appreciate the time you invested in your application"
        - "While your background is impressive..."
        - "We encourage you to apply for future positions"
        - "We'll keep your resume in our database for..."
        - "We wish you the best in your job search"
        
        GUIDELINES:
        - Avoid generic phrases like "we had many qualified applicants"
        - Don't make false promises
        - Maintain positive employer branding
        - Be concise but compassionate
        - No specific criticism of candidate
        """

def generate_job_description(jd_input: Dict[str, Any]) -> str:
    """Generate a job description using AI"""
    logger.info(f"Generating job description with input: {jd_input}")
    
    try:
        logger.info("Calling OpenAI API for job description generation")
        
        prompt = PromptTemplates.get_job_description_prompt(jd_input)
        
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": PromptTemplates.HR_PROFESSIONAL},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2500,
            temperature=0.8,
            top_p=0.9
        )
        
        job_description = response.choices[0].message.content.strip()
        logger.info("Job description generated successfully")
        return job_description
    
    except Exception as e:
        logger.error(f"Error generating job description: {str(e)}")
        raise Exception(f"Job description generation failed: {str(e)}")

def evaluate_resume(resume_text: str, jd_text: str) -> EvaluationResult:
    """Evaluate a resume against a job description using AI"""
    logger.info("Evaluating resume against job description")
    
    try:
        logger.info("Calling OpenAI API for resume evaluation")
        
        prompt = PromptTemplates.get_evaluation_prompt(resume_text, jd_text)
        
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": PromptTemplates.TECHNICAL_RECRUITER},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.2,  # Lower temperature for more consistent evaluations
            top_p=0.95,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content.strip()
        logger.info("Received evaluation response from OpenAI")
        
        try:
            evaluation_data = json.loads(result_text)
            
            evaluation = EvaluationResult(
                score=float(evaluation_data.get("score", 0)),
                missing_skills=evaluation_data.get("missing_skills", []),
                strength_areas=evaluation_data.get("strength_areas", []),
                experience_gap_analysis=evaluation_data.get("experience_gap_analysis", {}),
                cultural_fit_indicators=evaluation_data.get("cultural_fit_indicators", []),
                red_flags=evaluation_data.get("red_flags", []),
                remarks=evaluation_data.get("remarks", "Evaluation completed"),
                recommendation=evaluation_data.get("recommendation", "Further review needed"),
                interview_focus_areas=evaluation_data.get("interview_focus_areas", [])
            )
            
            logger.info(f"Resume evaluation completed. Score: {evaluation.score}")
            return evaluation
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Error parsing evaluation response: {str(e)}")
            return EvaluationResult(
                score=0,
                missing_skills=["Evaluation Error"],
                remarks="Failed to parse evaluation results. Please try again."
            )
    
    except Exception as e:
        logger.error(f"Error evaluating resume: {str(e)}")
        return EvaluationResult(
            score=0,
            missing_skills=["Processing Error"],
            remarks=f"Evaluation failed due to technical error: {str(e)}"
        )

def generate_email(candidate_name: str, position: str, email_type: str, 
                  evaluation: Optional[EvaluationResult] = None) -> str:
    """Generate personalized email for interview call or rejection"""
    logger.info(f"Generating {email_type} email for {candidate_name}")
    
    try:
        logger.info(f"Calling OpenAI API for {email_type} email generation")
        
        if email_type == "interview" and evaluation:
            prompt = PromptTemplates.get_interview_email_prompt(candidate_name, position, evaluation)
            system_role = PromptTemplates.EMPLOYER_BRANDING
        else:
            prompt = PromptTemplates.get_rejection_email_prompt(candidate_name, position, evaluation)
            system_role = PromptTemplates.EMPLOYER_BRANDING
        
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": system_role},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7,
            top_p=0.95
        )
        
        email_content = response.choices[0].message.content.strip()
        logger.info(f"{email_type.capitalize()} email generated successfully")
        return email_content
    
    except Exception as e:
        logger.error(f"Error generating {email_type} email: {str(e)}")
        return f"We encountered an error generating your email. Please try again or contact support.\n\nError: {str(e)}"

def optimize_prompt_for_model(prompt: str, model_name: str) -> str:
    """Optimize prompts based on specific model capabilities"""
    if "gpt-4" in model_name:
        return prompt + "\n\nNOTE: Provide comprehensive, detailed analysis with specific examples."
    elif "gpt-3.5" in model_name:
        return prompt + "\n\nPlease provide clear, structured responses following the specified format exactly."
    else:
        return prompt