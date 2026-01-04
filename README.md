# 🏥 GLP-1 Regulatory Intelligence Platform

> AI-powered pharmaceutical regulatory intelligence dashboard for analyzing FDA drug labels with semantic search and comparison capabilities.

## 🎯 Project Overview

This platform analyzes and compares FDA labels for GLP-1 medications (Ozempic, Mounjaro, Wegovy, etc.) using:
- **Named Entity Recognition (NER)** with BioBERT
- **Semantic Search** with RAG (Retrieval-Augmented Generation)
- **Lexical & Semantic Comparison** tools
- **Automated version tracking** with watchdog pipeline

## 🏗️ Architecture

### Phase A: Data Pipeline (Offline)
```
FDA DailyMed XML → AWS S3 → builder.py →
├─ PostgreSQL (clean text, metadata, NER)
└─ Pinecone (embeddings for semantic search)
```

### Phase B: Application (Online)
```
React Frontend ↔ FastAPI Backend ↔ Databases
                                   ├─ PostgreSQL (text retrieval)
                                   └─ Pinecone (vector search)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend)
- AWS account with S3 access
- Supabase account (free PostgreSQL)
- Pinecone account (free tier)
- Groq API key (free tier)

### 1. Clone & Setup Environment

```bash
cd "slickbit label analyzer"

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# - AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY
# - DATABASE_URL (from Supabase)
# - PINECONE_API_KEY
# - GROQ_API_KEY
```

### 2. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r backend/requirements.txt
```

### 3. Upload Raw FDA Files

```bash
# After downloading XML files from FDA DailyMed:
python backend/scripts/upload_to_s3.py
```

### 4. Run ETL Pipeline

```bash
# Process all drugs and populate databases
python backend/etl/builder.py
```

### 5. Start Backend API

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 6. Start Frontend (Coming Soon)

```bash
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
slickbit label analyzer/
├── backend/
│   ├── core/
│   │   └── config.py          # Configuration management
│   ├── models/
│   │   ├── schemas.py         # Pydantic models
│   │   └── database.py        # SQLAlchemy models
│   ├── services/
│   │   ├── s3_client.py       # AWS S3 operations
│   │   ├── vector_store.py    # Pinecone operations
│   │   └── llm_service.py     # Groq LLM integration
│   ├── etl/
│   │   ├── builder.py         # Main ETL pipeline
│   │   ├── parser.py          # XML parsing logic
│   │   └── ner.py             # Named Entity Recognition
│   ├── api/
│   │   └── routes.py          # FastAPI endpoints
│   ├── main.py                # FastAPI app entry point
│   └── requirements.txt
├── frontend/
│   └── (React + Vite + Tailwind)
├── data/                      # Local temp storage (gitignored)
├── .env                       # Your credentials (gitignored)
└── README.md
```

## 🔑 Key Features

### 1. Single Drug Analysis
- Rich-text reader with section navigation
- NER-highlighted entities (dosages, side effects)
- Clean, readable format (not raw PDF/XML)

### 2. Drug Comparison
- **Lexical Mode**: Track-changes style red-lining
- **Semantic Mode**: Color-coded similarity (🟢🟡🔴)
- Side-by-side split-pane layout

### 3. RAG Chatbot
- Context-aware semantic search
- Citations with auto-scroll to source
- Powered by Groq's Llama 3.1 (70B)

### 4. Automated Updates
- Watchdog script polls FDA for new versions
- Silent background updates
- Version history preserved

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI + Python 3.11 |
| Frontend | React + Vite + Tailwind CSS |
| Database | PostgreSQL (Supabase) |
| Vector DB | Pinecone (free tier) |
| Storage | AWS S3 |
| NER | BioBERT (dmis-lab) |
| Embeddings | SentenceTransformers |
| LLM | Groq (Llama 3.1 70B) |

## 📊 Data Flow

1. **Ingestion**: FDA XML → S3 → Parse (lxml) → Extract (BioBERT) → Vectorize (SentenceTransformers)
2. **Storage**: Clean text + metadata → PostgreSQL, Embeddings → Pinecone
3. **Retrieval**: User query → Vector search → LLM synthesis → Response with citations

## 🔐 Environment Variables

See `.env.example` for all required variables:
- AWS credentials for S3
- Database connection string
- API keys (Pinecone, Groq)
- Model configurations

## 📝 API Endpoints

```
GET  /drugs                    # List all drugs
GET  /drugs/{id}               # Get single drug details
POST /chat                     # RAG chatbot query
POST /compare                  # Compare two drugs
GET  /health                   # Health check
```

## 🧪 Development Status

- [x] Project structure
- [x] Configuration management
- [x] Data models (Pydantic + SQLAlchemy)
- [x] S3 client service
- [ ] XML parser
- [ ] NER integration
- [ ] Vector store service
- [ ] ETL pipeline
- [ ] FastAPI endpoints
- [ ] Frontend React app
- [ ] Watchdog automation

## 📚 Resources

- [FDA DailyMed](https://dailymed.nlm.nih.gov/)
- [LOINC Codes](https://loinc.org/)
- [Supabase Docs](https://supabase.com/docs)
- [Pinecone Docs](https://docs.pinecone.io/)
- [Groq API](https://console.groq.com/)

## 📄 License

MIT License

---

**Built with ❤️ for regulatory intelligence and patient safety**
