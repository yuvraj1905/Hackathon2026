"""
Document Models

Pydantic models for document storage (linked to projects).
"""

from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


FileType = Literal["pdf", "docx", "xlsx", "xls"]


class DocumentBase(BaseModel):
    """Base document model with common fields."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    filename: Optional[str] = Field(None, description="Original filename")
    file_type: Optional[FileType] = Field(None, description="File type (pdf, docx, etc.)")


class DocumentCreate(DocumentBase):
    """Model for creating a new document record."""
    project_id: UUID = Field(..., description="Associated project ID")
    extracted_text: str = Field(..., description="Text extracted from document")


class DocumentInDB(DocumentBase):
    """Document model as stored in database."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: UUID = Field(..., description="Document unique identifier")
    user_id: UUID = Field(..., description="Owner user ID")
    project_id: UUID = Field(..., description="Associated project ID")
    extracted_text: str = Field(..., description="Text extracted from document")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class DocumentResponse(BaseModel):
    """Document model for API responses."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: UUID = Field(..., description="Document unique identifier")
    project_id: UUID = Field(..., description="Associated project ID")
    filename: Optional[str] = Field(None, description="Original filename")
    file_type: Optional[FileType] = Field(None, description="File type")
    extracted_preview: str = Field(..., description="Preview of extracted text (first 500 chars)")
    created_at: datetime = Field(..., description="Creation timestamp")


class DocumentListResponse(BaseModel):
    """Response model for listing documents."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total count")
