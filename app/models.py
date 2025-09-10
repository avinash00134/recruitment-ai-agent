from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class JobDescriptionRequest(BaseModel):
    job_title: str = Field(..., description="Job title")
    years_of_experience: str = Field(..., description="Years of experience required")
    must_have_skills: str = Field(..., description="Comma-separated must-have skills")
    company_name: Optional[str] = Field(None, description="Company name")
    employment_type: Optional[str] = Field("Full-time", description="Employment type")
    industry: Optional[str] = Field(None, description="Industry")
    location: Optional[str] = Field(None, description="Location")

class EvaluationResult(BaseModel):
    score: float = Field(..., ge=0, le=100, description="Matching score out of 100")
    missing_skills: List[str] = Field(..., description="List of missing skills")
    remarks: str = Field(..., description="Evaluation remarks")

class CandidateResult(BaseModel):
    filename: str = Field(..., description="Resume filename")
    score: float = Field(..., ge=0, le=100, description="Matching score")
    missing_skills: List[str] = Field(..., description="Missing skills")
    remarks: str = Field(..., description="Evaluation remarks")
    resume_text: str = Field(..., description="Extracted resume text")

class MatchingResponse(BaseModel):
    candidates: List[CandidateResult] = Field(..., description="List of evaluated candidates")
    best_candidate: Optional[str] = Field(None, description="Filename of best candidate")
    interview_email: Optional[str] = Field(None, description="Generated interview email")
    rejection_email: Optional[str] = Field(None, description="Generated rejection email")
    processing_time: float = Field(..., description="Total processing time in seconds")

class HealthCheck(BaseModel):
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Current timestamp")