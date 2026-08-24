"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from datetime import date, datetime

class ReportCreate(BaseModel):
    """Schema for creating a new report."""
    type: str = Field(..., pattern="^(Lost|Found)$")
    item: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    color: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=500)
    date: date
    details: Optional[str] = Field(None, max_length=2000)
    
    @field_validator('date')
    @classmethod
    def date_not_future(cls, v):
        """Validate that date is not in the future."""
        if v > date.today():
            raise ValueError('Date cannot be in the future')
        return v
    
    @field_validator('category')
    @classmethod
    def valid_category(cls, v):
        """Validate that category is one of the allowed values."""
        valid_categories = [
            'Electronics', 'Clothing', 'Personal items',
            'Keys & cards', 'Books'
        ]
        if v not in valid_categories:
            raise ValueError(f'Category must be one of: {", ".join(valid_categories)}')
        return v

class ReportResponse(BaseModel):
    """Schema for report response."""
    id: int
    type: str
    item: str
    category: str
    color: str
    location: str
    date: date
    status: str
    details: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class MatchResponse(BaseModel):
    """Schema for match response with explainability."""
    lost_report: ReportResponse
    found_report: ReportResponse
    score: float
    component_scores: Dict[str, float]
    reasons: List[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "lost_report": {
                    "id": 1,
                    "item": "AirPods Pro",
                    "type": "Lost"
                },
                "found_report": {
                    "id": 2,
                    "item": "Apple AirPods case",
                    "type": "Found"
                },
                "score": 78.5,
                "component_scores": {
                    "item_category": 22.0,
                    "vector": 24.0,
                    "keywords": 10.0,
                    "location": 15.0,
                    "color": 5.0,
                    "date": 2.5
                },
                "reasons": [
                    "Strong semantic similarity (96%)",
                    "Same location (Student Union)",
                    "Similar item description",
                    "Reported within 1 day"
                ]
            }
        }

class ReportWithMatches(BaseModel):
    """Schema for report creation response with matches."""
    report: ReportResponse
    matches: List[MatchResponse]
    warning: Optional[str] = None
