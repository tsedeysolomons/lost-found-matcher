"""
API endpoint tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from app.main import app
from app.database import Base, get_db

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    """Create and drop test database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

class TestReportAPI:
    """Test cases for report API endpoints."""
    
    def test_create_lost_report(self):
        """Test creating a lost item report."""
        report_data = {
            "type": "Lost",
            "item": "AirPods Pro",
            "category": "Electronics",
            "color": "White",
            "location": "Student Union, 2nd floor",
            "date": date.today().isoformat(),
            "details": "White case with blue sticker"
        }
        
        response = client.post("/api/reports", json=report_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert "report" in data
        assert "matches" in data
        assert data["report"]["type"] == "Lost"
        assert data["report"]["item"] == "AirPods Pro"
        assert isinstance(data["matches"], list)
    
    def test_create_found_report(self):
        """Test creating a found item report."""
        report_data = {
            "type": "Found",
            "item": "Blue Notebook",
            "category": "Books",
            "color": "Blue",
            "location": "Library",
            "date": date.today().isoformat(),
            "details": "Found on table near windows"
        }
        
        response = client.post("/api/reports", json=report_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["report"]["type"] == "Found"
        assert data["report"]["status"] == "Unclaimed"
    
    def test_validation_future_date(self):
        """Test that future dates are rejected."""
        report_data = {
            "type": "Lost",
            "item": "Wallet",
            "category": "Personal items",
            "color": "Brown",
            "location": "Cafeteria",
            "date": "2030-01-01",  # Future date
            "details": "Leather wallet"
        }
        
        response = client.post("/api/reports", json=report_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_validation_invalid_category(self):
        """Test that invalid categories are rejected."""
        report_data = {
            "type": "Lost",
            "item": "Thing",
            "category": "Invalid Category",  # Not in allowed list
            "color": "Blue",
            "location": "Somewhere",
            "date": date.today().isoformat()
        }
        
        response = client.post("/api/reports", json=report_data)
        
        assert response.status_code == 422
    
    def test_list_reports(self):
        """Test listing all reports."""
        # Create a couple of reports
        report1 = {
            "type": "Lost",
            "item": "Wallet",
            "category": "Personal items",
            "color": "Brown",
            "location": "Library",
            "date": date.today().isoformat()
        }
        
        report2 = {
            "type": "Found",
            "item": "Keys",
            "category": "Keys & cards",
            "color": "Silver",
            "location": "Gym",
            "date": date.today().isoformat()
        }
        
        client.post("/api/reports", json=report1)
        client.post("/api/reports", json=report2)
        
        # List all reports
        response = client.get("/api/reports")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 2
    
    def test_list_reports_filter_by_type(self):
        """Test filtering reports by type."""
        # Create lost and found reports
        lost_report = {
            "type": "Lost",
            "item": "Phone",
            "category": "Electronics",
            "color": "Black",
            "location": "Cafeteria",
            "date": date.today().isoformat()
        }
        
        found_report = {
            "type": "Found",
            "item": "Charger",
            "category": "Electronics",
            "color": "White",
            "location": "Library",
            "date": date.today().isoformat()
        }
        
        client.post("/api/reports", json=lost_report)
        client.post("/api/reports", json=found_report)
        
        # Filter by Lost
        response = client.get("/api/reports?report_type=Lost")
        data = response.json()
        
        assert all(r["type"] == "Lost" for r in data)
        
        # Filter by Found
        response = client.get("/api/reports?report_type=Found")
        data = response.json()
        
        assert all(r["type"] == "Found" for r in data)
    
    def test_get_report_by_id(self):
        """Test retrieving a specific report."""
        report_data = {
            "type": "Lost",
            "item": "Backpack",
            "category": "Personal items",
            "color": "Black",
            "location": "Student Union",
            "date": date.today().isoformat()
        }
        
        # Create report
        create_response = client.post("/api/reports", json=report_data)
        report_id = create_response.json()["report"]["id"]
        
        # Get report by ID
        response = client.get(f"/api/reports/{report_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == report_id
        assert data["item"] == "Backpack"
    
    def test_get_nonexistent_report(self):
        """Test that requesting non-existent report returns 404."""
        response = client.get("/api/reports/99999")
        
        assert response.status_code == 404
    
    def test_matching_between_lost_and_found(self):
        """Test end-to-end matching between lost and found reports."""
        # Create a lost report
        lost_data = {
            "type": "Lost",
            "item": "AirPods Pro",
            "category": "Electronics",
            "color": "White",
            "location": "Student Union",
            "date": date.today().isoformat(),
            "details": "White case with small blue sticker"
        }
        
        lost_response = client.post("/api/reports", json=lost_data)
        assert lost_response.status_code == 201
        
        # Create a matching found report
        found_data = {
            "type": "Found",
            "item": "Apple AirPods case",
            "category": "Electronics",
            "color": "White",
            "location": "Student Union",
            "date": date.today().isoformat(),
            "details": "Found near coffee shop, white with sticker"
        }
        
        found_response = client.post("/api/reports", json=found_data)
        assert found_response.status_code == 201
        
        found_result = found_response.json()
        
        # Should have at least one match
        assert len(found_result["matches"]) > 0
        
        # Check match structure
        match = found_result["matches"][0]
        assert "score" in match
        assert "component_scores" in match
        assert "reasons" in match
        assert "lost_report" in match
        assert "found_report" in match
        
        # Score should be reasonable (high similarity)
        assert match["score"] > 35.0
        
        # Should have reasons
        assert len(match["reasons"]) > 0
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert data["status"] == "operational"
