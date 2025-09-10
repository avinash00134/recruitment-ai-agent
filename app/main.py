from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import tempfile
import os
from pathlib import Path
import time
from datetime import datetime

import models
import utils
import ai_services
from config import settings
from logger import logger

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered recruitment system for job matching and candidate evaluation",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirects to docs"""
    return {"message": f"{settings.APP_NAME} v{settings.APP_VERSION}", "docs": "/docs"}

@app.get("/health", response_model=models.HealthCheck, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now()
    }

@app.post("/generate-job-description", tags=["Job Description"])
async def generate_job_description(request: models.JobDescriptionRequest):
    """Generate job description using AI"""
    logger.info(f"Received job description generation request: {request.dict()}")
    
    try:
        job_description = ai_services.generate_job_description(request.dict())
        logger.info("Job description generated successfully")
        
        return {"job_description": job_description}
    
    except Exception as e:
        logger.error(f"Error generating job description: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating job description: {str(e)}"
        )

@app.post("/upload-job-description", tags=["Job Description"])
async def upload_job_description(file: UploadFile = File(...)):
    """Upload and extract job description from file"""
    logger.info(f"Received job description upload: {file.filename}")
    
    if not file.filename:
        logger.error("No filename provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file selected"
        )
    
    if not utils.validate_file_extension(file.filename):
        logger.error(f"Invalid file extension: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload PDF or DOC/DOCX files."
        )
    
    try:
        job_description = utils.extract_text_from_file(file)
        logger.info(f"Job description extracted successfully from {file.filename}")
        
        return {"job_description": job_description}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing file {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )

@app.post("/match-candidates", response_model=models.MatchingResponse, tags=["Matching"])
async def match_candidates(
    job_description: str = Form(..., description="Job description text"),
    resumes: List[UploadFile] = File(..., description="Resume files to evaluate")
):
    """Match candidates against job description"""
    start_time = time.time()
    logger.info(f"Received candidate matching request for {len(resumes)} resumes")
    
    if len(resumes) > settings.MAX_RESUMES:
        logger.error(f"Too many resumes uploaded: {len(resumes)} (max: {settings.MAX_RESUMES})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {settings.MAX_RESUMES} resumes allowed"
        )
    
    candidates = []
    processed_files = 0
    
    for resume in resumes:
        if not resume.filename:
            logger.warning("Skipping resume with no filename")
            continue
        
        if not utils.validate_file_extension(resume.filename):
            logger.warning(f"Skipping invalid file: {resume.filename}")
            continue
        
        try:
            logger.info(f"Processing resume: {resume.filename}")
            
            resume_text = utils.extract_text_from_file(resume)
            
            evaluation = ai_services.evaluate_resume(resume_text, job_description)
            
            candidate = models.CandidateResult(
                filename=resume.filename,
                score=evaluation.score,
                missing_skills=evaluation.missing_skills,
                remarks=evaluation.remarks,
                resume_text=resume_text[:500] + "..." if len(resume_text) > 500 else resume_text
            )
            
            candidates.append(candidate)
            processed_files += 1
            logger.info(f"Successfully processed {resume.filename} - Score: {evaluation.score}")
            
        except Exception as e:
            logger.error(f"Error processing resume {resume.filename}: {str(e)}")
            error_candidate = models.CandidateResult(
                filename=resume.filename,
                score=0,
                missing_skills=["Processing Error"],
                remarks=f"Error processing resume: {str(e)}",
                resume_text=""
            )
            candidates.append(error_candidate)
    
    best_candidate = None
    if candidates:
        best_candidate = max(candidates, key=lambda x: x.score)
        logger.info(f"Best candidate: {best_candidate.filename} with score {best_candidate.score}")
    
    interview_email = None
    rejection_email = None
    
    if best_candidate and best_candidate.score >= 70:
        logger.info("Generating interview email for best candidate")
        interview_email = ai_services.generate_email(
            candidate_name=best_candidate.filename,
            position="the position",
            email_type="interview",
            evaluation=best_candidate
        )
    
    logger.info("Generating rejection email template")
    rejection_email = ai_services.generate_email(
        candidate_name="Candidate",
        position="the position",
        email_type="rejection"
    )
    
    processing_time = time.time() - start_time
    logger.info(f"Candidate matching completed. Processed {processed_files} files in {processing_time:.2f} seconds")
    
    return models.MatchingResponse(
        candidates=candidates,
        best_candidate=best_candidate.filename if best_candidate else None,
        interview_email=interview_email,
        rejection_email=rejection_email,
        processing_time=processing_time
    )

@app.post("/generate-email", tags=["Email"])
async def generate_email(request: dict):
    """Generate personalized email for candidate"""
    logger.info(f"Received email generation request: {request}")
    
    try:
        candidate_name = request.get("candidate_name", "Candidate")
        position = request.get("position", "the position")
        email_type = request.get("email_type", "interview")
        
        evaluation_data = request.get("evaluation", {})
        evaluation = models.EvaluationResult(
            score=float(evaluation_data.get("score", 80)),
            missing_skills=evaluation_data.get("missing_skills", []),
            remarks=evaluation_data.get("remarks", "Strong candidate")
        )
        
        email_content = ai_services.generate_email(
            candidate_name=candidate_name,
            position=position,
            email_type=email_type,
            evaluation=evaluation
        )
        
        logger.info(f"Email generated successfully for {candidate_name}")
        return {"email_content": email_content}
    
    except Exception as e:
        logger.error(f"Error generating email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating email: {str(e)}"
        )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Recruitment AI Agent server")
    uvicorn.run(app, host="0.0.0.0", port=8000)