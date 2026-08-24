"""
Matching service implementing the hybrid matching algorithm.
"""
from typing import List, Dict, Tuple
import re
from datetime import date
import numpy as np
from app.models.report import Report, ReportType
from app.services.embedding_service import EmbeddingService
from app.config import MATCH_WEIGHTS, FALLBACK_WEIGHTS, MATCH_THRESHOLD

class MatchingService:
    """
    Service for computing hybrid similarity scores between reports.
    Combines attribute matching, keyword matching, and vector similarity.
    """
    
    def __init__(self, embedding_service: EmbeddingService):
        """Initialize matching service with embedding service."""
        self.embedding_service = embedding_service
        self.weights = MATCH_WEIGHTS
        self.fallback_weights = FALLBACK_WEIGHTS
    
    def find_matches(
        self,
        target_report: Report,
        candidate_reports: List[Report],
        threshold: float = MATCH_THRESHOLD
    ) -> List[Dict]:
        """
        Find and score potential matches for target report.
        
        Args:
            target_report: Newly created report to match
            candidate_reports: List of opposite-type reports
            threshold: Minimum score to include in results
        
        Returns:
            Sorted list of matches exceeding threshold with explanations
        """
        matches = []
        
        for candidate in candidate_reports:
            # Compute component scores
            scores, reasons = self.compute_match_score(target_report, candidate)
            
            # Aggregate weighted score
            total_score = sum(scores.values())
            
            # Apply threshold filter
            if total_score >= threshold:
                # Determine which is lost and which is found
                if target_report.type == ReportType.LOST:
                    lost_report = target_report
                    found_report = candidate
                else:
                    lost_report = candidate
                    found_report = target_report
                
                matches.append({
                    'lost_report': lost_report,
                    'found_report': found_report,
                    'score': round(total_score, 2),
                    'component_scores': {k: round(v, 2) for k, v in scores.items()},
                    'reasons': reasons
                })
        
        # Sort by score descending
        matches.sort(key=lambda m: m['score'], reverse=True)
        
        return matches
    
    def compute_match_score(
        self,
        report1: Report,
        report2: Report
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Compute individual component scores using weighted algorithm.
        
        Args:
            report1: First report
            report2: Second report
        
        Returns:
            Tuple of (component_scores dict, reasons list)
        """
        scores = {}
        reasons = []
        
        # Check if embeddings are available
        has_embeddings = (
            report1.embedding is not None and 
            report2.embedding is not None and
            len(report1.embedding) > 0 and
            len(report2.embedding) > 0
        )
        
        # Use appropriate weights
        weights = self.weights if has_embeddings else self.fallback_weights
        
        # 1. Item/Category Similarity
        item_score, item_reasons = self._score_item_category(report1, report2, weights)
        scores['item_category'] = item_score
        reasons.extend(item_reasons)
        
        # 2. Vector Similarity (if available)
        if has_embeddings:
            vector_score, vector_reasons = self._score_vector_similarity(
                report1, report2, weights
            )
            scores['vector'] = vector_score
            reasons.extend(vector_reasons)
        
        # 3. Keyword Similarity
        keyword_score, keyword_reasons = self._score_keywords(report1, report2, weights)
        scores['keywords'] = keyword_score
        reasons.extend(keyword_reasons)
        
        # 4. Location Similarity
        location_score, location_reasons = self._score_location(report1, report2, weights)
        scores['location'] = location_score
        reasons.extend(location_reasons)
        
        # 5. Color Similarity
        color_score, color_reasons = self._score_color(report1, report2, weights)
        scores['color'] = color_score
        reasons.extend(color_reasons)
        
        # 6. Date Proximity
        date_score, date_reasons = self._score_date(report1, report2, weights)
        scores['date'] = date_score
        reasons.extend(date_reasons)
        
        return scores, reasons
    
    def _score_item_category(
        self, 
        r1: Report, 
        r2: Report,
        weights: Dict[str, float]
    ) -> Tuple[float, List[str]]:
        """Score based on item name and category similarity."""
        score = 0.0
        reasons = []
        max_score = weights['item_category'] * 100
        
        # Category match (60% of this component)
        if r1.category == r2.category:
            category_contribution = max_score * 0.6
            score += category_contribution
            reasons.append(f"Same category ({r1.category})")
        
        # Item name overlap using Jaccard similarity (40% of this component)
        words1 = set(r1.item.lower().split())
        words2 = set(r2.item.lower().split())
        
        if words1 and words2:
            intersection = words1 & words2
            union = words1 | words2
            
            if intersection and union:
                jaccard = len(intersection) / len(union)
                item_contribution = max_score * 0.4 * jaccard
                score += item_contribution
                
                if jaccard > 0.3:
                    reasons.append(f"Similar item names ({int(jaccard * 100)}% overlap)")
        
        return min(score, max_score), reasons
    
    def _score_vector_similarity(
        self,
        r1: Report,
        r2: Report,
        weights: Dict[str, float]
    ) -> Tuple[float, List[str]]:
        """Score based on embedding cosine similarity."""
        reasons = []
        max_score = weights['vector'] * 100
        
        # Compute cosine similarity
        similarity = self.embedding_service.compute_similarity(
            np.array(r1.embedding),
            np.array(r2.embedding)
        )
        
        score = similarity * max_score
        
        # Add reason if similarity is high
        if similarity > 0.7:
            reasons.append(f"Strong semantic similarity ({int(similarity * 100)}%)")
        elif similarity > 0.5:
            reasons.append(f"Moderate semantic similarity ({int(similarity * 100)}%)")
        
        return score, reasons
    
    def _score_keywords(
        self,
        r1: Report,
        r2: Report,
        weights: Dict[str, float]
    ) -> Tuple[float, List[str]]:
        """Score based on keyword overlap in descriptions."""
        reasons = []
        max_score = weights['keywords'] * 100
        
        if not r1.keywords or not r2.keywords:
            return 0.0, reasons
        
        keywords1 = set(r1.keywords)
        keywords2 = set(r2.keywords)
        
        if not keywords1 or not keywords2:
            return 0.0, reasons
        
        # Jaccard similarity
        intersection = keywords1 & keywords2
        union = keywords1 | keywords2
        
        if union:
            keyword_jaccard = len(intersection) / len(union)
            score = keyword_jaccard * max_score
            
            if intersection and keyword_jaccard > 0.2:
                common = ', '.join(list(intersection)[:3])
                reasons.append(f"Shared keywords: {common}")
            
            return score, reasons
        
        return 0.0, reasons
    
    def _score_location(
        self,
        r1: Report,
        r2: Report,
        weights: Dict[str, float]
    ) -> Tuple[float, List[str]]:
        """Score based on location proximity."""
        reasons = []
        max_score = weights['location'] * 100
        
        # Extract primary location (before comma)
        loc1_primary = r1.location.split(',')[0].strip().lower()
        loc2_primary = r2.location.split(',')[0].strip().lower()
        
        if loc1_primary == loc2_primary:
            reasons.append(f"Same location ({r1.location.split(',')[0].strip()})")
            return max_score, reasons
        
        return 0.0, reasons
    
    def _score_color(
        self,
        r1: Report,
        r2: Report,
        weights: Dict[str, float]
    ) -> Tuple[float, List[str]]:
        """Score based on color match."""
        reasons = []
        max_score = weights['color'] * 100
        
        color1 = r1.color.lower().strip()
        color2 = r2.color.lower().strip()
        
        if color1 == color2:
            reasons.append(f"Same color ({r1.color})")
            return max_score, reasons
        
        return 0.0, reasons
    
    def _score_date(
        self,
        r1: Report,
        r2: Report,
        weights: Dict[str, float]
    ) -> Tuple[float, List[str]]:
        """Score based on temporal proximity."""
        reasons = []
        max_score = weights['date'] * 100
        
        day_gap = abs((r1.date - r2.date).days)
        
        if day_gap == 0:
            reasons.append("Reported on same day")
            return max_score, reasons
        elif day_gap <= 2:
            reasons.append(f"Reported within {day_gap} day(s)")
            return max_score * 0.5, reasons
        elif day_gap <= 7:
            reasons.append(f"Reported within a week")
            return max_score * 0.2, reasons
        
        return 0.0, reasons

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract significant keywords from text for matching.
    
    Args:
        text: Input text to analyze
        max_keywords: Maximum number of keywords to return
    
    Returns:
        List of lowercase keywords sorted by significance
    """
    if not text:
        return []
    
    # Convert to lowercase
    text = text.lower()
    
    # Extract words (alphanumeric only)
    words = re.findall(r'\b[a-z0-9]+\b', text)
    
    # Common stop words to exclude
    stop_words = {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
    }
    
    # Filter keywords
    keywords = [
        word for word in words
        if len(word) >= 3 and word not in stop_words
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)
    
    return unique_keywords[:max_keywords]
