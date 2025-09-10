import os
import tempfile
from typing import IO
from fastapi import UploadFile, HTTPException
import PyPDF2
import docx
import io
from pathlib import Path
from logger import logger

def extract_text_from_file(file: UploadFile) -> str:
    """Extract text from PDF or DOC/DOCX file"""
    logger.info(f"Extracting text from file: {file.filename}")
    
    try:
        content = file.file.read()
        
        if file.filename.lower().endswith('.pdf'):
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                logger.info(f"Successfully extracted text from PDF: {file.filename}")
                return text
            except Exception as e:
                logger.error(f"Error reading PDF {file.filename}: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")
        
        elif file.filename.lower().endswith(('.doc', '.docx')):
            try:
                doc = docx.Document(io.BytesIO(content))
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                logger.info(f"Successfully extracted text from Word document: {file.filename}")
                return text
            except Exception as e:
                logger.error(f"Error reading Word document {file.filename}: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Error reading Word document: {str(e)}")
        
        else:
            logger.error(f"Unsupported file format: {file.filename}")
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF or DOC/DOCX files.")
    
    except Exception as e:
        logger.error(f"Unexpected error processing file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

def validate_file_extension(filename: str) -> bool:
    """Validate file extension"""
    allowed_extensions = ['.pdf', '.doc', '.docx']
    file_extension = Path(filename).suffix.lower()
    return file_extension in allowed_extensions

def save_upload_file(upload_file: UploadFile, destination: str) -> None:
    """Save uploaded file to destination"""
    try:
        with open(destination, "wb") as buffer:
            buffer.write(upload_file.file.read())
        logger.info(f"File saved successfully: {destination}")
    except Exception as e:
        logger.error(f"Error saving file {upload_file.filename}: {str(e)}")
        raise
    finally:
        upload_file.file.close()