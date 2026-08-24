"""
API routes for report endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.report import (
    ReportCreate,
    ReportResponse,
    ReportWithMatches,
    MatchResponse
)
from app.services.embedding_service import get_embedding_service
from app.services.matching_service import MatchingService
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/reports", tags=["reports"])

def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    """Dependency to get report service with all dependencies."""
    embedding_service = get_embedding_service()
    matching_service = MatchingService(embedding_service)
    return ReportService(db, embedding_service, matching_service)

@router.post("", response_model=ReportWithMatches, status_code=201)
async def create_report(
    report: ReportCreate,
    service: ReportService = Depends(get_report_service)
) -> ReportWithMatches:
    """
    Create a new lost or found report and return potential matches.
    
    This endpoint implements the complete hybrid matching flow:
    - Validates input data
    - Generates semantic embeddings
    - Extracts keywords
    - Saves report to database
    - Finds and scores potential matches
    - Returns explainable match results
    """
    try:
        return service.create_report_with_matches(report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[ReportResponse])
async def list_reports(
    report_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    service: ReportService = Depends(get_report_service)
) -> List[ReportResponse]:
    """
    Retrieve all reports with optional filtering.
    
    Query parameters:
    - report_type: Filter by "Lost" or "Found" (optional)
    - skip: Number of records to skip for pagination (default: 0)
    - limit: Maximum records to return (default: 100, max: 100)
    """
    if limit > 100:
        limit = 100
    
    reports = service.list_reports(report_type, skip, limit)
    return [ReportResponse.model_validate(report) for report in reports]

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    service: ReportService = Depends(get_report_service)
) -> ReportResponse:
    """
    Retrieve a single report by ID.
    """
    report = service.get_report(report_id)
    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"Report with ID {report_id} not found"
        )
    return ReportResponse.model_validate(report)

@router.get("/{report_id}/matches", response_model=List[MatchResponse])
async def get_matches(
    report_id: int,
    threshold: float = 35.0,
    service: ReportService = Depends(get_report_service)
) -> List[MatchResponse]:
    """
    Get potential matches for a specific report.
    
    Query parameters:
    - threshold: Minimum match score (default: 35.0, range: 0-100)
    """
    report = service.get_report(report_id)
    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"Report with ID {report_id} not found"
        )
    
    if threshold < 0 or threshold > 100:
        raise HTTPException(
            status_code=400,
            detail="Threshold must be between 0 and 100"
        )
    
    return service.get_matches_for_report(report_id, threshold)
