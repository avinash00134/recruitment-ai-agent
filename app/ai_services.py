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
    def get_jd_analysis_prompt(jd_text: str) -> str:
        """Generate prompt for analyzing job description and extracting evaluation criteria"""
        return f"""
        TASK: Analyze job description and extract evaluation criteria
        ROLE: Senior HR Analyst
        
        JOB DESCRIPTION:
        {jd_text}
        
        Analyze this job description thoroughly and extract:
        
        1. ROLE TYPE: Identify if this is a technical, business, creative, or operational role
        2. CRITICAL REQUIREMENTS: Extract must-have skills, experiences, and qualifications
        3. IMPORTANCE LEVELS: Determine which requirements are high, medium, or low priority
        4. INDUSTRY CONTEXT: Identify industry, company size, and team structure mentioned
        
        Return a JSON object with this structure:
        {{
          "role_type": "technical/business/creative/operational",
          "hard_skills": [
            {{
              "skill": "specific skill name",
              "importance": "high/medium/low",
              "description": "specific context from JD",
              "validation_approach": "how to verify this from resume"
            }}
          ],
          "soft_skills": [
            {{
              "skill": "specific skill name",
              "importance": "high/medium/low",
              "description": "specific context from JD",
              "validation_approach": "how to verify this from resume"
            }}
          ],
          "experience_requirements": [
            {{
              "requirement": "specific experience needed",
              "importance": "high/medium/low",
              "description": "details from JD"
            }}
          ],
          "industry_context": "description of industry/company context"
        }}
        
        Be extremely specific and ground every point in the actual JD text.
        """

    @staticmethod
    def get_dynamic_evaluation_prompt(jd_analysis: Dict[str, Any], jd_text: str, resume_text: str) -> str:
        """Generate dynamic evaluation prompt based on JD analysis"""

        evaluation_criteria = ""
        
        if jd_analysis.get('hard_skills'):
            evaluation_criteria += "HARD SKILLS EVALUATION:\n"
            for skill in jd_analysis['hard_skills']:
                evaluation_criteria += f"- {skill['skill']}: {skill['description']} (Importance: {skill['importance']})\n"
                evaluation_criteria += f"  Validation: {skill['validation_approach']}\n\n"
        
        if jd_analysis.get('soft_skills'):
            evaluation_criteria += "SOFT SKILLS EVALUATION:\n"
            for skill in jd_analysis['soft_skills']:
                evaluation_criteria += f"- {skill['skill']}: {skill['description']} (Importance: {skill['importance']})\n"
                evaluation_criteria += f"  Validation: {skill['validation_approach']}\n\n"
        
        if jd_analysis.get('experience_requirements'):
            evaluation_criteria += "EXPERIENCE REQUIREMENTS:\n"
            for req in jd_analysis['experience_requirements']:
                evaluation_criteria += f"- {req['requirement']}: {req['description']} (Importance: {req['importance']})\n\n"
        

        role_type = jd_analysis.get('role_type', '').lower()
        scoring_guidance = ""
        
        if 'technical' in role_type or 'developer' in role_type or 'engineer' in role_type:
            scoring_guidance = """
            TECHNICAL ROLE SCORING GUIDANCE:
            - Hard Skills: Weight heavily (0-10 scale, be strict about specific technologies)
            - Soft Skills: Secondary importance but still valuable
            - Experience: Critical for senior roles, important for all technical positions
            - Look for: Specific technologies, project experience, technical achievements
            """
        elif 'manager' in role_type or 'account' in role_type or 'business' in role_type:
            scoring_guidance = """
            BUSINESS ROLE SCORING GUIDANCE:
            - Soft Skills: Weight heavily (communication, leadership, client management)
            - Experience: Very important (industry experience, team size managed)
            - Hard Skills: Secondary but still relevant (tools, software, methodologies)
            - Look for: Revenue impact, team leadership, client relationships
            """
        elif 'creative' in role_type or 'design' in role_type:
            scoring_guidance = """
            CREATIVE ROLE SCORING GUIDANCE:
            - Portfolio quality: Most important (if mentioned in resume)
            - Technical skills: Tools and software proficiency
            - Soft Skills: Collaboration, creativity, communication
            - Look for: Project diversity, technical versatility, creative achievements
            """
        else:
            scoring_guidance = """
            GENERAL SCORING GUIDANCE:
            - Balance hard and soft skills based on apparent role requirements
            - Consider industry context and company needs
            - Prioritize requirements marked as 'high' importance
            """

        return f"""
        TASK: Comprehensive resume evaluation against job description
        ROLE: Senior Technical Recruiter
        
        JOB DESCRIPTION CONTEXT:
        {jd_text[:2000]}... [truncated if too long]
        
        JOB ANALYSIS:
        - Role Type: {jd_analysis.get('role_type', 'Not specified')}
        - Industry Context: {jd_analysis.get('industry_context', 'Not specified')}
        
        EVALUATION CRITERIA:
        {evaluation_criteria if evaluation_criteria else "No specific criteria extracted from JD."}
        
        SCORING APPROACH:
        {scoring_guidance}
        
        SCORING SCALE (0-10 for each criterion):
        - 0: No evidence or completely irrelevant
        - 1-3: Minimal exposure, below requirements
        - 4-6: Some relevant experience, meets basic requirements  
        - 7-8: Good match, meets most requirements well
        - 9-10: Excellent match, exceeds requirements with strong evidence
        
        CANDIDATE RESUME:
        {resume_text[:3000]}... [truncated if too long]
        
        EVALUATION INSTRUCTIONS:
        1. Evaluate the candidate against EACH specific criterion listed above
        2. For each criterion, provide:
           - Score (0-10)
           - Specific reason based on resume evidence
           - Direct quote or example from resume that supports your assessment
        3. Consider the importance level (high/medium/low) when scoring
        4. Provide an overall assessment considering role context and industry needs
        5. Be brutally honest - underestimate rather than overestimate qualifications
        
        OUTPUT FORMAT: Strict JSON structure
        {{
          "hard_skills": {{
            "<exact_criterion_name>": {{
              "score": <number>,
              "reason": "<specific justification>",
              "evidence": "<resume excerpt>",
              "importance": "<high/medium/low>"
            }}
          }},
          "soft_skills": {{
            "<exact_criterion_name>": {{
              "score": <number>, 
              "reason": "<specific justification>",
              "evidence": "<resume excerpt>",
              "importance": "<high/medium/low>"
            }}
          }},
          "experience_requirements": {{
            "<exact_criterion_name>": {{
              "score": <number>,
              "reason": "<specific justification>", 
              "evidence": "<resume excerpt>",
              "importance": "<high/medium/low>"
            }}
          }},
          "overall_assessment": {{
            "summary": "<2-3 sentence overall assessment>",
            "strengths": ["list of key strengths"],
            "concerns": ["list of potential gaps"],
            "recommendation": "<hire/consider/reject>"
          }},
          "calculated_score": <weighted_score_0-100>
        }}
        
        IMPORTANT: Use the exact same criterion names as listed in the evaluation criteria above.
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

def analyze_job_description(jd_text: str) -> Dict[str, Any]:
    """Analyze job description to extract evaluation criteria"""
    logger.info("Analyzing job description to extract evaluation criteria")
    
    try:
        prompt = PromptTemplates.get_jd_analysis_prompt(jd_text)
        
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": PromptTemplates.HR_PROFESSIONAL},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.1,
            top_p=0.95,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content.strip()
        jd_analysis = json.loads(result_text)
        
        logger.info("Job description analysis completed successfully")
        return jd_analysis
        
    except Exception as e:
        logger.error(f"Error analyzing job description: {str(e)}")

        return {
            "role_type": "general",
            "hard_skills": [],
            "soft_skills": [],
            "experience_requirements": [],
            "industry_context": "Unknown"
        }

def calculate_weighted_score(evaluation_data: Dict[str, Any]) -> float:
    """Calculate weighted score based on importance levels"""
    total_score = 0
    total_weight = 0
    criteria_count = 0
    
    for category in ['hard_skills', 'soft_skills', 'experience_requirements']:
        for criterion_name, evaluation in evaluation_data.get(category, {}).items():
            score = evaluation.get('score', 0)
            importance = evaluation.get('importance', 'medium').lower()
            

            if importance == 'high':
                weight = 1.5
            elif importance == 'medium':
                weight = 1.0
            else:  # low
                weight = 0.5
                
            total_score += score * weight
            total_weight += weight
            criteria_count += 1
    
    if total_weight == 0:
        return 0
    
    raw_score = (total_score / total_weight) * 10
    final_score = min(100, max(0, raw_score))
    
    return final_score

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
    """Evaluate a resume against a job description using AI with dynamic scoring"""
    logger.info("Evaluating resume against job description with dynamic scoring")
    
    try:
        jd_analysis = analyze_job_description(jd_text)
        
        prompt = PromptTemplates.get_dynamic_evaluation_prompt(jd_analysis, jd_text, resume_text)
        
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": PromptTemplates.TECHNICAL_RECRUITER},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
            temperature=0.2,
            top_p=0.95,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content.strip()
        logger.info("Received evaluation response from OpenAI")
        
        try:
            evaluation_data = json.loads(result_text)
            

            calculated_score = evaluation_data.get("calculated_score")
            if calculated_score is None:
                calculated_score = calculate_weighted_score(evaluation_data)
            
            missing_skills = []
            for category in ['hard_skills', 'soft_skills', 'experience_requirements']:
                for skill_name, skill_data in evaluation_data.get(category, {}).items():
                    if skill_data.get('score', 0) < 5: 
                        missing_skills.append(skill_name)
            
            overall = evaluation_data.get("overall_assessment", {})
            
            evaluation = EvaluationResult(
                score=float(calculated_score),
                missing_skills=missing_skills,
                strength_areas=overall.get("strengths", []),
                experience_gap_analysis={},
                cultural_fit_indicators=[],
                red_flags=overall.get("concerns", []),
                remarks=overall.get("summary", "Evaluation completed"),
                recommendation=overall.get("recommendation", "Further review needed"),
                interview_focus_areas=[]
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
    """Generate personalized email for candidate"""
    logger.info(f"Generating {email_type} email for {candidate_name}")
    
    try:
        logger.info(f"Calling OpenAI API for {email_type} email generation")
        
        if evaluation and isinstance(evaluation, dict):
            evaluation_data = evaluation
            evaluation = EvaluationResult(
                score=float(evaluation_data.get("score", 80)),
                missing_skills=evaluation_data.get("missing_skills", []),
                remarks=evaluation_data.get("remarks", "Strong candidate"),
                recommendation=evaluation_data.get("recommendation", "Consider for interview"),
                strength_areas=evaluation_data.get("strength_areas", []),
                experience_gap_analysis=evaluation_data.get("experience_gap_analysis", {}),
                cultural_fit_indicators=evaluation_data.get("cultural_fit_indicators", []),
                red_flags=evaluation_data.get("red_flags", []),
                interview_focus_areas=evaluation_data.get("interview_focus_areas", [])
            )
        elif not evaluation:

            evaluation = EvaluationResult(
                score=80,
                missing_skills=[],
                remarks="Strong candidate profile",
                recommendation="Consider for interview",
                strength_areas=[],
                experience_gap_analysis={},
                cultural_fit_indicators=[],
                red_flags=[],
                interview_focus_areas=[]
            )
        
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