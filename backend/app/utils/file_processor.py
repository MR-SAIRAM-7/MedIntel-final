"""
File processing utilities for MedIntel application.
"""
from PyPDF2 import PdfReader
from fastapi import HTTPException
import logging

logger = logging.getLogger("medintel.utils.file_processor")


def extract_text_from_pdf(path: str) -> str:
    """
    Extract text content from PDF file.
    
    Args:
        path: Path to the PDF file
        
    Returns:
        Extracted text content
        
    Raises:
        HTTPException: If PDF extraction fails
    """
    try:
        reader = PdfReader(path)
        text_parts = []
        
        for page in reader.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text_parts.append(extracted_text)
        
        text = "\n".join(text_parts)
        
        if not text.strip():
            raise ValueError("No text could be extracted from PDF")
        
        return text
        
    except Exception as e:
        logger.error(f"PDF extraction failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to extract text from PDF: {str(e)}"
        )


def validate_file_size(file_size: int, max_size: int) -> bool:
    """
    Validate file size against maximum allowed size.
    
    Args:
        file_size: Size of the file in bytes
        max_size: Maximum allowed size in bytes
        
    Returns:
        True if file size is valid, False otherwise
    """
    return file_size <= max_size


def get_file_type_category(content_type: str) -> str:
    """
    Categorize file type based on MIME type.
    
    Args:
        content_type: MIME type of the file
        
    Returns:
        Category string: 'image', 'pdf', 'text', or 'unknown'
    """
    if content_type.startswith("image/"):
        return "image"
    elif content_type == "application/pdf":
        return "pdf"
    elif content_type.startswith("text/"):
        return "text"
    else:
        return "unknown"
