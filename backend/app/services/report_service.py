"""
Report service for managing report CRUD operations and matching orchestration.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.report import Report, ReportType, ReportStatus
from app.schemas.report import ReportCreate, ReportWithMatches, MatchResponse, ReportResponse
from app.services.embedding_service import EmbeddingService
from app.services.matching_service import MatchingService, extract_keywords
import logging

logger = logging.getLogger(__name__)

class ReportService:
    """
    Service for report business logic and matching orchestration.
    """
    
    def __init__(
        self,
        db: Session,
        embedding_service: EmbeddingService,
        matching_service: MatchingService
    ):
        self.db = db
        self.embedding_service = embedding_service
        self.matching_service = matching_service
    
    def create_report_with_matches(
        self,
        report_data: ReportCreate
    ) -> ReportWithMatches:
        """
        Create a new report and find potential matches.
        
        This implements the complete 13-step matching flow:
        1-2. Validate (done by Pydantic)
        3. Build rich searchable text
        4. Generate embedding
        5. Extract keywords
        6. Save report
        7-8. Fetch and filter candidates
        9-12. Hybrid matching and scoring
        13. Return matches with explanations
        
        Args:
            report_data: Validated report data
        
        Returns:
            ReportWithMatches containing report and potential matches
        """
        warning = None
        
        try:
            # Step 1-2: Create report instance (validation already done)
            report = Report(**report_data.model_dump())
            
            # Step 3: Build rich searchable text for embedding
            full_text = self._build_embedding_text(report)
            
            # Step 4: Generate embedding
            try:
                embedding = self.embedding_service.generate_embedding(full_text)
                report.embedding = embedding.tolist()
            except Exception as e:
                logger.error(f"Embedding generation failed: {e}")
                warning = "Embedding generation failed; matches may be limited"
                report.embedding = None
            
            # Step 5: Extract keywords
            keywords_text = f"{report.item} {report.details or ''}"
            report.keywords = extract_keywords(keywords_text)
            
            # Set initial status
            if report.type == ReportType.LOST:
                report.status = ReportStatus.SEARCHING
            else:
                report.status = ReportStatus.UNCLAIMED
            
            # Step 6: Save report to database
            self.db.add(report)
            self.db.flush()  # Get ID without committing
            self.db.commit()
            self.db.refresh(report)
            
            # Step 7-8: Find and filter candidate reports
            candidates = self._get_candidate_reports(report)
            
            # Step 9-12: Run hybrid matching
            matches = self.matching_service.find_matches(report, candidates)
            
            # Step 13: Convert to response format with explanations
            match_responses = [
                MatchResponse(
                    lost_report=ReportResponse.model_validate(match['lost_report']),
                    found_report=ReportResponse.model_validate(match['found_report']),
                    score=match['score'],
                    component_scores=match['component_scores'],
                    reasons=match['reasons']
                )
                for match in matches
            ]
            
            return ReportWithMatches(
                report=ReportResponse.model_validate(report),
                matches=match_responses,
                warning=warning
            )
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating report: {e}")
            raise
    
    def _build_embedding_text(self, report: Report) -> str:
        """
        Build rich text for embedding generation.
        Includes multiple fields for better semantic understanding.
        """
        return f"""
        Item: {report.item}
        Category: {report.category}
        Color: {report.color}
        Location: {report.location}
        Details: {report.details or ''}
        """.strip()
    
    def _get_candidate_reports(self, target_report: Report) -> List[Report]:
        """
        Fetch and filter candidate reports for matching.
        
        Smart filtering strategy:
        - Opposite type only (Lost ↔ Found)
        - Not resolved
        - Same category FIRST, cross-category LIMITED (top 50)
        
        This balances flexibility (don't miss "AirPods" vs "Wireless earbuds")
        with performance (limit unnecessary comparisons).
        """
        # Determine opposite type
        opposite_type = (
            ReportType.FOUND if target_report.type == ReportType.LOST 
            else ReportType.LOST
        )
        
        # Fetch all opposite-type unresolved reports
        all_candidates = self.db.query(Report).filter(
            Report.type == opposite_type,
            Report.status != ReportStatus.RESOLVED
        ).all()
        
        # Separate by category match
        same_category = [
            c for c in all_candidates 
            if c.category == target_report.category
        ]
        other_category = [
            c for c in all_candidates 
            if c.category != target_report.category
        ]
        
        # Prioritize same category, limit cross-category
        candidates = same_category + other_category[:50]
        
        return candidates
    
    def get_report(self, report_id: int) -> Optional[Report]:
        """Retrieve a single report by ID."""
        return self.db.query(Report).filter(Report.id == report_id).first()
    
    def list_reports(
        self,
        report_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Report]:
        """
        List reports with optional filtering and pagination.
        
        Args:
            report_type: Optional filter by type ("Lost" or "Found")
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of reports
        """
        query = self.db.query(Report)
        
        if report_type:
            query = query.filter(Report.type == report_type)
        
        return query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_matches_for_report(
        self,
        report_id: int,
        threshold: float = 35.0
    ) -> List[MatchResponse]:
        """
        Get potential matches for an existing report.
        
        Args:
            report_id: ID of the report to find matches for
            threshold: Minimum match score
        
        Returns:
            List of match responses
        """
        report = self.get_report(report_id)
        if not report:
            return []
        
        candidates = self._get_candidate_reports(report)
        matches = self.matching_service.find_matches(report, candidates, threshold)
        
        return [
            MatchResponse(
                lost_report=ReportResponse.model_validate(match['lost_report']),
                found_report=ReportResponse.model_validate(match['found_report']),
                score=match['score'],
                component_scores=match['component_scores'],
                reasons=match['reasons']
            )
            for match in matches
        ]
