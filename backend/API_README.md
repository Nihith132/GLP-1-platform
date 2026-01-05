# FastAPI Backend - GLP-1 Drug Label Platform

Complete RESTful API for drug label search, analysis, and comparison.

## 🚀 Quick Start

### 1. Start the API Server

```bash
./start-api.sh
```

Or manually:

```bash
cd backend
source venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Access API Documentation

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/api/health

### 3. Run Tests

```bash
cd backend
python test_api.py
```

---

## 📋 API Endpoints Overview

### **Health & Status**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root health check |
| GET | `/api/health` | Detailed health status |

---

## 🏷️ Drug Endpoints

### **1. List All Drugs**

```http
GET /api/drugs/
```

**Query Parameters:**
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Max records to return (default: 100, max: 1000)
- `manufacturer` (str, optional): Filter by manufacturer
- `generic_name` (str, optional): Filter by generic name

**Response:**
```json
{
  "drugs": [
    {
      "id": 1,
      "brand_name": "Ozempic",
      "generic_name": "semaglutide",
      "manufacturer": "Novo Nordisk",
      "dosage_form": "Solution",
      "route": "Subcutaneous",
      "marketing_status": "Prescription"
    }
  ],
  "total": 19,
  "skip": 0,
  "limit": 100
}
```

### **2. Get Drug by ID**

```http
GET /api/drugs/{drug_id}
```

**Response:** Full drug details with all sections

### **3. Get Specific Section**

```http
GET /api/drugs/{drug_id}/sections/{loinc_code}
```

**Example:** `GET /api/drugs/1/sections/34066-1` (Boxed Warning)

### **4. Search Drugs by Name**

```http
GET /api/drugs/search/by-name?query=ozempic
```

---

## 🔍 Search Endpoints

### **1. Semantic Search (All Drugs)**

```http
POST /api/search/semantic
```

**Request Body:**
```json
{
  "query": "What are the cardiovascular benefits?",
  "top_k": 5,
  "filters": {
    "manufacturer": "Novo Nordisk"
  }
}
```

**Response:**
```json
{
  "results": [
    {
      "section_id": 123,
      "drug_name": "Ozempic",
      "section_title": "Clinical Studies",
      "loinc_code": "34092-7",
      "chunk_text": "...",
      "similarity_score": 0.89
    }
  ],
  "total_results": 5,
  "execution_time_ms": 45.2
}
```

### **2. Search Within Specific Drug**

```http
POST /api/search/drug/{drug_id}
```

### **3. Search by Section Type**

```http
POST /api/search/section/{loinc_code}
```

**Example:** Search all "Warnings and Precautions" sections
```http
POST /api/search/section/43685-7
```

---

## 💬 Chat Endpoints (RAG)

### **1. Ask a Question**

```http
POST /api/chat/ask
```

**Request Body:**
```json
{
  "message": "What are the most common side effects of GLP-1 medications?",
  "conversation_id": null,
  "drug_id": null
}
```

**Response:**
```json
{
  "response": "Based on the drug label information...",
  "citations": [
    {
      "section_id": 456,
      "drug_name": "Ozempic",
      "section_title": "Adverse Reactions",
      "loinc_code": "34084-4",
      "chunk_text": "..."
    }
  ],
  "conversation_id": "uuid-here"
}
```

### **2. Compare Drugs**

```http
POST /api/chat/compare
```

**Request Body:**
```json
{
  "message": "Compare side effects of Ozempic and Victoza",
  "conversation_id": null
}
```

---

## 📊 Analytics Endpoints

### **1. Platform Analytics**

```http
GET /api/analytics/platform
```

**Response:**
```json
{
  "total_drugs": 19,
  "total_sections": 869,
  "total_embeddings": 869,
  "unique_manufacturers": 8,
  "drug_classes": {
    "semaglutide": 4,
    "dulaglutide": 3,
    "liraglutide": 2
  },
  "common_sections": {
    "Warnings and Precautions (43685-7)": 19,
    "Adverse Reactions (34084-4)": 19
  }
}
```

### **2. Drug Analytics**

```http
GET /api/analytics/drug/{drug_id}
```

**Response:**
```json
{
  "drug_id": 1,
  "drug_name": "Ozempic",
  "section_count": 45,
  "chunk_count": 48,
  "section_breakdown": {
    "Warnings and Precautions (43685-7)": 1,
    "Adverse Reactions (34084-4)": 1
  },
  "entity_statistics": {
    "drug_names": ["Ozempic", "semaglutide"],
    "conditions": [],
    "dosages": [],
    "warnings": []
  },
  "avg_chunk_size": 450,
  "total_content_length": 125000
}
```

### **3. Compare Drugs**

```http
POST /api/analytics/compare
```

**Request Body:**
```json
{
  "drug_ids": [1, 2, 3],
  "comparison_type": "side_by_side",
  "attributes": ["indications", "warnings", "dosage"]
}
```

**Response:**
```json
{
  "comparisons": [
    {
      "drug_id": 1,
      "drug_name": "Ozempic",
      "attributes": {
        "brand_name": "Ozempic",
        "generic_name": "semaglutide",
        "manufacturer": "Novo Nordisk",
        "indications": "..."
      }
    }
  ],
  "similarities": [
    "All drugs contain semaglutide",
    "Same dosage form: Solution"
  ],
  "differences": [
    "Different manufacturers: Novo Nordisk, Eli Lilly"
  ]
}
```

---

## 🔧 Common LOINC Codes

| Code | Section Title |
|------|---------------|
| 34066-1 | Boxed Warning |
| 34067-9 | Indications and Usage |
| 34068-7 | Dosage and Administration |
| 34070-3 | Contraindications |
| 43685-7 | Warnings and Precautions |
| 34084-4 | Adverse Reactions |
| 34088-5 | Overdosage |
| 34089-3 | Description |
| 34090-1 | Clinical Pharmacology |
| 34092-7 | Clinical Studies |

---

## 🧪 Testing Examples

### Using cURL

```bash
# Get all drugs
curl http://localhost:8000/api/drugs/

# Semantic search
curl -X POST http://localhost:8000/api/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "cardiovascular benefits", "top_k": 3}'

# Ask a question
curl -X POST http://localhost:8000/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What are common side effects?"}'

# Get analytics
curl http://localhost:8000/api/analytics/platform
```

### Using Python

```python
import httpx

async with httpx.AsyncClient() as client:
    # Semantic search
    response = await client.post(
        "http://localhost:8000/api/search/semantic",
        json={"query": "side effects", "top_k": 5}
    )
    results = response.json()
    
    # Chat
    response = await client.post(
        "http://localhost:8000/api/chat/ask",
        json={"message": "Compare Ozempic and Victoza"}
    )
    answer = response.json()
```

---

## 🏗️ Architecture

```
backend/
├── api/
│   ├── main.py              # FastAPI app entry point
│   ├── schemas.py           # Pydantic models
│   └── routes/
│       ├── drugs.py         # Drug CRUD endpoints
│       ├── search.py        # Vector search endpoints
│       ├── chat.py          # RAG chat endpoints
│       └── analytics.py     # Analytics & comparison
├── models/
│   ├── drug_label.py        # SQLAlchemy models
│   └── db_session.py        # Database session
├── etl/
│   └── vector_service.py    # Embedding generation
└── test_api.py              # API tests
```

---

## 🚨 Error Handling

All endpoints return structured error responses:

```json
{
  "detail": "Error message here",
  "status_code": 404
}
```

Common status codes:
- `200` - Success
- `400` - Bad request (invalid parameters)
- `404` - Resource not found
- `500` - Internal server error

---

## 🔐 Authentication (TODO)

Currently no authentication. For production:

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@router.get("/protected")
async def protected_route(credentials = Depends(security)):
    # Verify token
    pass
```

---

## 🚀 Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key
CORS_ORIGINS=http://localhost:3000,https://your-domain.com
```

---

## 📚 Next Steps

1. **Add LLM Integration**: Replace chat placeholder with OpenAI/Claude API
2. **Add Authentication**: JWT tokens or API keys
3. **Add Rate Limiting**: Protect endpoints from abuse
4. **Add Caching**: Redis for frequently accessed data
5. **Add Monitoring**: Logging, metrics, alerting
6. **Frontend Integration**: Connect React app to API

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Database Connection Issues

Check `backend/.env` has correct credentials:
```bash
SUPABASE_URL=https://...
SUPABASE_KEY=...
```

### Import Errors

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📞 Support

For issues or questions, refer to the main project documentation.
