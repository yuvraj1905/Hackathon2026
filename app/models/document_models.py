"""
Document Models

Pydantic models for document upload and management.
"""

from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


DocumentStatus = Literal["uploaded", "processing", "completed", "failed"]
FileType = Literal["pdf", "docx", "xlsx", "xls"]
BuildOption = Literal["mobile", "web", "design", "backend", "admin"]


class DocumentBase(BaseModel):
    """Base document model with common fields."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    filename: Optional[str] = Field(None, description="Original filename")
    file_type: Optional[FileType] = Field(None, description="File type (pdf, docx, etc.)")
    manual_input: Optional[str] = Field(None, description="Manual text input from user")
    build_options: List[BuildOption] = Field(
        default_factory=list,
        description="What to build: mobile, web, design, backend, admin"
    )


class DocumentCreate(DocumentBase):
    """Model for creating a new document record."""
    extracted_text: str = Field(..., description="Text extracted from document")
    fused_description: Optional[str] = Field(None, description="Combined manual + extracted text")


class DocumentInDB(DocumentBase):
    """Document model as stored in database."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: UUID = Field(..., description="Document unique identifier")
    user_id: UUID = Field(..., description="Owner user ID")
    extracted_text: str = Field(..., description="Text extracted from document")
    fused_description: Optional[str] = Field(None, description="Combined manual + extracted text")
    status: DocumentStatus = Field(default="uploaded", description="Processing status")
    created_at: datetime = Field(..., description="Upload timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class DocumentResponse(BaseModel):
    """Document model for API responses."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: UUID = Field(..., description="Document unique identifier")
    filename: Optional[str] = Field(None, description="Original filename")
    file_type: Optional[FileType] = Field(None, description="File type")
    build_options: List[BuildOption] = Field(default_factory=list, description="Build options")
    status: DocumentStatus = Field(..., description="Processing status")
    extracted_preview: str = Field(..., description="Preview of extracted text (first 500 chars)")
    created_at: datetime = Field(..., description="Upload timestamp")


class DocumentUploadResponse(BaseModel):
    """Response model for document upload endpoint."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    document_id: UUID = Field(..., description="Created document ID")
    filename: Optional[str] = Field(None, description="Original filename")
    file_type: Optional[FileType] = Field(None, description="Detected file type")
    extracted_preview: str = Field(..., description="Preview of extracted text (first 500 chars)")
    status: DocumentStatus = Field(default="uploaded", description="Document status")


class DocumentListResponse(BaseModel):
    """Response model for listing user's documents."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    documents: List[DocumentResponse] = Field(..., description="List of user's documents")
    total: int = Field(..., description="Total count")
