from pydantic import BaseModel, Field, ConfigDict
from typing import List


class FeatureInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    
    name: str = Field(..., description="Feature name")
    category: str = Field(..., description="Feature category")
    complexity: str = Field(..., description="Feature complexity")


class ModificationRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    
    current_features: List[FeatureInput] = Field(..., description="Current feature list")
    instruction: str = Field(..., min_length=3, description="Modification instruction")


class ModificationResponse(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    
    total_hours: float = Field(..., ge=0, description="Total estimated hours")
    min_hours: float = Field(..., ge=0, description="Minimum hours estimate")
    max_hours: float = Field(..., ge=0, description="Maximum hours estimate")
    features: List[dict] = Field(..., description="Updated feature list")
    changes_summary: str = Field(..., description="Summary of changes made")
