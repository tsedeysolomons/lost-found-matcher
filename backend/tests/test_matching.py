"""
Tests for the hybrid matching algorithm.
"""
import pytest
from datetime import date, timedelta
from app.models.report import Report, ReportType, ReportStatus
from app.services.matching_service import MatchingService, extract_keywords
from app.services.embedding_service import EmbeddingService
import numpy as np

@pytest.fixture
def embedding_service():
    """Fixture for embedding service."""
    return EmbeddingService()

@pytest.fixture
def matching_service(embedding_service):
    """Fixture for matching service."""
    return MatchingService(embedding_service)

def create_test_report(
    report_type: ReportType,
    item: str,
    category: str,
    color: str,
    location: str,
    report_date: date,
    details: str = ""
) -> Report:
    """Helper to create test reports."""
    report = Report(
        type=report_type,
        item=item,
        category=category,
        color=color,
        location=location,
        date=report_date,
        details=details,
        status=ReportStatus.SEARCHING
    )
    # Generate embedding for test
    embedding_service = EmbeddingService()
    full_text = f"{item} {category} {color} {location} {details}"
    report.embedding = embedding_service.generate_embedding(full_text).tolist()
    report.keywords = extract_keywords(f"{item} {details}")
    return report

class TestMatchingAlgorithm:
    """Test cases for the matching algorithm."""
    
    def test_perfect_match(self, matching_service):
        """Test that identical items score very high."""
        lost = create_test_report(
            ReportType.LOST,
            "AirPods Pro",
            "Electronics",
            "White",
            "Student Union",
            date.today(),
            "White case with blue sticker"
        )
        
        found = create_test_report(
            ReportType.FOUND,
            "AirPods Pro",
            "Electronics",
            "White",
            "Student Union",
            date.today(),
            "White case with blue sticker"
        )
        
        scores, reasons = matching_service.compute_match_score(lost, found)
        total_score = sum(scores.values())
        
        assert total_score > 80, f"Perfect match should score > 80, got {total_score}"
        assert "Same category" in ' '.join(reasons)
        assert "Same location" in ' '.join(reasons)
        assert "Same color" in ' '.join(reasons)
    
    def test_score_bounds(self, matching_service):
        """Test that scores are always within valid bounds."""
        lost = create_test_report(
            ReportType.LOST,
            "Random Item A",
            "Electronics",
            "Blue",
            "Building A",
            date.today()
        )
        
        found = create_test_report(
            ReportType.FOUND,
            "Completely Different Item",
            "Clothing",
            "Red",
            "Building Z",
            date.today() - timedelta(days=30)
        )
        
        scores, _ = matching_service.compute_match_score(lost, found)
        total_score = sum(scores.values())
        
        # Score should be within 0-100
        assert 0 <= total_score <= 100, f"Score out of bounds: {total_score}"
        
        # Each component should not exceed its weight
        assert scores['item_category'] <= 25.0
        assert scores['vector'] <= 25.0
        assert scores['keywords'] <= 15.0
        assert scores['location'] <= 15.0
        assert scores['color'] <= 10.0
        assert scores['date'] <= 10.0
    
    def test_same_category_bonus(self, matching_service):
        """Test that same category provides significant score boost."""
        lost1 = create_test_report(
            ReportType.LOST,
            "Phone",
            "Electronics",
            "Black",
            "Library",
            date.today()
        )
        
        found_same_category = create_test_report(
            ReportType.FOUND,
            "Charger",
            "Electronics",
            "White",
            "Gym",
            date.today()
        )
        
        found_diff_category = create_test_report(
            ReportType.FOUND,
            "Charger",
            "Personal items",
            "White",
            "Gym",
            date.today()
        )
        
        scores_same, _ = matching_service.compute_match_score(lost1, found_same_category)
        scores_diff, _ = matching_service.compute_match_score(lost1, found_diff_category)
        
        # Same category should score higher
        assert scores_same['item_category'] > scores_diff['item_category']
    
    def test_semantic_similarity(self, matching_service, embedding_service):
        """Test that semantically similar items match even with different words."""
        lost = create_test_report(
            ReportType.LOST,
            "AirPods",
            "Electronics",
            "White",
            "Library",
            date.today(),
            "Apple wireless earbuds"
        )
        
        found = create_test_report(
            ReportType.FOUND,
            "Wireless earbuds",
            "Electronics",
            "White",
            "Library",
            date.today(),
            "Small white charging case"
        )
        
        scores, reasons = matching_service.compute_match_score(lost, found)
        
        # Should have decent vector similarity even though exact words differ
        assert scores['vector'] > 10.0, "Semantic similarity should detect related items"
    
    def test_date_proximity_scoring(self, matching_service):
        """Test that date proximity affects scoring correctly."""
        lost = create_test_report(
            ReportType.LOST,
            "Wallet",
            "Personal items",
            "Brown",
            "Cafeteria",
            date.today()
        )
        
        # Same day
        found_same_day = create_test_report(
            ReportType.FOUND,
            "Wallet",
            "Personal items",
            "Brown",
            "Cafeteria",
            date.today()
        )
        
        # 2 days later
        found_2_days = create_test_report(
            ReportType.FOUND,
            "Wallet",
            "Personal items",
            "Brown",
            "Cafeteria",
            date.today() + timedelta(days=2)
        )
        
        # 10 days later
        found_10_days = create_test_report(
            ReportType.FOUND,
            "Wallet",
            "Personal items",
            "Brown",
            "Cafeteria",
            date.today() + timedelta(days=10)
        )
        
        scores_same, _ = matching_service.compute_match_score(lost, found_same_day)
        scores_2, _ = matching_service.compute_match_score(lost, found_2_days)
        scores_10, _ = matching_service.compute_match_score(lost, found_10_days)
        
        # Same day should score highest
        assert scores_same['date'] > scores_2['date']
        assert scores_2['date'] > scores_10['date']
        assert scores_10['date'] == 0.0

class TestKeywordExtraction:
    """Test cases for keyword extraction."""
    
    def test_basic_extraction(self):
        """Test basic keyword extraction."""
        text = "White AirPods case with blue sticker on the lid"
        keywords = extract_keywords(text)
        
        assert "white" in keywords
        assert "airpods" in keywords
        assert "case" in keywords
        assert "blue" in keywords
        assert "sticker" in keywords
    
    def test_stop_word_filtering(self):
        """Test that common stop words are filtered out."""
        text = "The wallet is black and has a card inside"
        keywords = extract_keywords(text)
        
        # Stop words should be removed
        assert "the" not in keywords
        assert "is" not in keywords
        assert "and" not in keywords
        assert "has" not in keywords
        
        # Meaningful words should remain
        assert "wallet" in keywords
        assert "black" in keywords
        assert "card" in keywords
    
    def test_short_word_filtering(self):
        """Test that words shorter than 3 characters are filtered."""
        text = "My ID is in a red case"
        keywords = extract_keywords(text)
        
        # Short words should be removed
        assert "my" not in keywords
        assert "is" not in keywords
        assert "in" not in keywords
        
        # Valid words should remain (note: "id" becomes "id" which is 2 chars)
        assert "red" in keywords
        assert "case" in keywords
    
    def test_deduplication(self):
        """Test that duplicate keywords are removed."""
        text = "Black phone black case black color"
        keywords = extract_keywords(text)
        
        # "black" should appear only once
        assert keywords.count("black") == 1
        assert "phone" in keywords
        assert "case" in keywords
        assert "color" in keywords

def test_threshold_filtering(matching_service):
    """Test that threshold filtering works correctly."""
    lost = create_test_report(
        ReportType.LOST,
        "Notebook",
        "Books",
        "Blue",
        "Library",
        date.today()
    )
    
    # High match
    found_high = create_test_report(
        ReportType.FOUND,
        "Notebook",
        "Books",
        "Blue",
        "Library",
        date.today()
    )
    
    # Low match
    found_low = create_test_report(
        ReportType.FOUND,
        "Jacket",
        "Clothing",
        "Red",
        "Gym",
        date.today() - timedelta(days=20)
    )
    
    candidates = [found_high, found_low]
    matches = matching_service.find_matches(lost, candidates, threshold=35.0)
    
    # Only high match should pass threshold
    assert len(matches) >= 1
    assert matches[0]['score'] >= 35.0
    
    # All matches should exceed threshold
    for match in matches:
        assert match['score'] >= 35.0
