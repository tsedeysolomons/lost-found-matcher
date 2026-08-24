# Lost and Found Matching Backend

Hybrid matching system for lost and found items using semantic embeddings, keyword matching, and attribute comparison.

## Architecture

```
Next.js Frontend → FastAPI Backend → PostgreSQL + pgvector
                         ↓
                  Matching Engine
                  ├── Attribute Matcher (25%)
                  ├── Vector Similarity (25%)
                  ├── Keyword Matcher (15%)
                  ├── Location Matcher (15%)
                  ├── Color Matcher (10%)
                  └── Date Proximity (10%)
```

## Features

- **Hybrid Matching Algorithm**: Combines structured attributes, keywords, and semantic embeddings
- **Explainable Scores**: Returns component breakdown and human-readable reasons
- **Real-time Matching**: Matches computed immediately on report submission
- **Smart Candidate Filtering**: Prioritizes same-category, limits cross-category
- **Rich Embeddings**: Uses all-MiniLM-L6-v2 (384d) for semantic understanding

## Prerequisites

- Python 3.10+
- PostgreSQL 15+ with pgvector extension
- 4GB RAM (for embedding model)
- ~500MB disk space

## Setup

### 1. Install PostgreSQL with pgvector

**Windows:**
```cmd
# Install PostgreSQL from https://www.postgresql.org/download/windows/
# Then install pgvector extension
```

**macOS:**
```bash
brew install postgresql@15 pgvector
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt install postgresql-15 postgresql-15-pgvector
sudo systemctl start postgresql
```

### 2. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE lost_found_db;

# Connect to database
\c lost_found_db

# Enable pgvector extension
CREATE EXTENSION vector;

# Exit
\q
```

### 3. Install Python Dependencies

```cmd
cd backend
pip install -r requirements.txt
```

This will download:
- FastAPI and dependencies
- PostgreSQL drivers
- Sentence Transformers model (~90MB, downloaded automatically on first run)

### 4. Configure Environment

```cmd
copy .env.example .env
```

Edit `.env`:
```
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/lost_found_db
EMBEDDING_MODEL=all-MiniLM-L6-v2
MATCH_THRESHOLD=35.0
CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 5. Run the Backend

```cmd
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## API Endpoints

### POST /api/reports
Create a new report and get potential matches.

**Request:**
```json
{
  "type": "Lost",
  "item": "AirPods Pro",
  "category": "Electronics",
  "color": "White",
  "location": "Student Union, 2nd floor",
  "date": "2024-04-18",
  "details": "White case with small blue sticker"
}
```

**Response:**
```json
{
  "report": {
    "id": 1,
    "type": "Lost",
    "item": "AirPods Pro",
    ...
  },
  "matches": [
    {
      "lost_report": {...},
      "found_report": {...},
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
  ]
}
```

### GET /api/reports
List all reports with optional filtering.

Query params:
- `report_type`: "Lost" or "Found" (optional)
- `skip`: Pagination offset (default: 0)
- `limit`: Max results (default: 100)

### GET /api/reports/{id}
Get a single report by ID.

### GET /api/reports/{id}/matches
Get potential matches for a specific report.

Query params:
- `threshold`: Minimum match score (default: 35.0)

## Testing

```cmd
cd backend
pytest tests/ -v
```

Test coverage:
- Matching algorithm (score bounds, components, semantic similarity)
- Keyword extraction (stop words, filtering, deduplication)
- Threshold filtering
- Date proximity scoring

## Matching Algorithm Details

### Weights Configuration
```python
# app/config.py
MATCH_WEIGHTS = {
    'item_category': 0.25,  # Category + item name overlap
    'vector': 0.25,         # Semantic embedding similarity
    'keywords': 0.15,       # Keyword overlap
    'location': 0.15,       # Location proximity
    'color': 0.10,          # Exact color match
    'date': 0.10            # Temporal proximity
}
```

### Candidate Filtering
1. Fetch opposite type (Lost ↔ Found)
2. Exclude resolved reports
3. Prioritize same-category candidates
4. Limit cross-category to top 50
5. Run hybrid scoring

### Explainability
Every match includes:
- **Total score**: 0-100 weighted aggregate
- **Component scores**: Individual contribution breakdown
- **Reasons**: Human-readable explanations

Example reasons:
- "Strong semantic similarity (96%)"
- "Same category (Electronics)"
- "Same location (Student Union)"
- "Similar item names (75% overlap)"
- "Reported within 2 day(s)"

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI application
│   ├── config.py                # Configuration & weights
│   ├── database.py              # Database connection
│   │
│   ├── api/
│   │   └── reports.py           # Report endpoints
│   │
│   ├── models/
│   │   └── report.py            # SQLAlchemy ORM
│   │
│   ├── schemas/
│   │   └── report.py            # Pydantic validation
│   │
│   └── services/
│       ├── embedding_service.py # Sentence Transformers
│       ├── matching_service.py  # Hybrid algorithm
│       └── report_service.py    # Business logic
│
├── tests/
│   └── test_matching.py         # Algorithm tests
│
├── requirements.txt
└── README.md
```

## Troubleshooting

### pgvector not found
```bash
# PostgreSQL 15+
CREATE EXTENSION vector;

# If extension not available, install pgvector
# See: https://github.com/pgvector/pgvector
```

### Embedding model download fails
```cmd
# Manual download
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### CORS errors
Check `CORS_ORIGINS` in `.env` matches your frontend URL.

### Database connection fails
Verify PostgreSQL is running and credentials in `.env` are correct.

## Performance

**MVP Scale**: Hundreds to few thousand reports

Expected performance:
- Report creation: < 1s (including embedding + matching)
- Matching: < 200ms for ~100-500 candidates
- Embedding generation: ~50-100ms per report

## Future Enhancements

Not included in MVP but documented for future:
- ONNX runtime (2-3x faster inference)
- pgvector indexes (IVFFlat/HNSW for vector search)
- Rate limiting (slowapi)
- Authentication (JWT)
- Background job processing
- Async endpoints
- Image upload and matching
- Email/SMS notifications

## License

Assessment project - Educational purposes
