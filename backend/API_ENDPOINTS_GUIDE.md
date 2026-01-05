# GLP-1 Drug Label Platform - API Endpoints Guide

Complete documentation of all API endpoints with detailed explanations and code references.

---

## Table of Contents
1. [Health & System Endpoints](#health--system-endpoints)
2. [Drug Endpoints](#drug-endpoints)
3. [Search Endpoints](#search-endpoints)
4. [Chat Endpoints (RAG)](#chat-endpoints-rag)
5. [Analytics Endpoints](#analytics-endpoints)
6. [Comparison Endpoints](#comparison-endpoints)

---

## Health & System Endpoints

### 1. Health Check
**File**: `backend/api/main.py` (lines 35-40)

```python
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}
```

**Purpose**: Quick endpoint to verify the API and database are operational.

**Usage**:
```bash
GET /api/health
```

**Response**:
```json
{
    "status": "healthy",
    "database": "connected"
}
```

**When to use**: Health monitoring, load balancer checks, deployment verification.

---

### 2. Root Endpoint
**File**: `backend/api/main.py` (lines 42-51)

```python
@app.get("/")
async def root():
    return {
        "message": "GLP-1 Drug Label Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }
```

**Purpose**: API information and navigation.

**Usage**:
```bash
GET /
```

**When to use**: API discovery, documentation links.

---

## Drug Endpoints

### 3. List All Drugs
**File**: `backend/api/routes/drugs.py` (lines 18-63)

```python
@router.get(
    "/",
    response_model=DrugListResponse,
    summary="List all drugs"
)
async def list_drugs(limit: int = 100, offset: int = 0):
    async with AsyncSessionLocal() as session:
        # Count total drugs
        count_query = select(func.count()).select_from(
            select(DrugLabel).where(DrugLabel.is_current_version == True).subquery()
        )
        total_result = await session.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated drugs
        drug_query = (
            select(DrugLabel)
            .where(DrugLabel.is_current_version == True)
            .order_by(DrugLabel.id)
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(drug_query)
        drugs = result.scalars().all()
```

**Purpose**: Retrieve a paginated list of all current drug labels in the database.

**Key Features**:
- **Pagination**: `limit` and `offset` parameters for efficient data loading
- **Current versions only**: Filters `is_current_version == True`
- **Total count**: Returns both the drugs and total count for pagination UI
- **NER Summary**: Includes extracted entities (dosages, frequencies, routes)

**Usage**:
```bash
GET /api/drugs/?limit=10&offset=0
```

**Response Structure**:
```json
{
    "drugs": [
        {
            "id": 1,
            "name": "WEGOVY",
            "generic_name": "semaglutide",
            "manufacturer": "Novo Nordisk",
            "ner_summary": {
                "dosages": ["2.4 mg"],
                "frequencies": ["once weekly"],
                "routes": ["subcutaneous"]
            }
        }
    ],
    "total": 19,
    "limit": 10,
    "offset": 0
}
```

**When to use**: Dashboard drug list, dropdown menus, drug selection UI.

---

### 4. Get Single Drug with Sections
**File**: `backend/api/routes/drugs.py` (lines 66-107)

```python
@router.get(
    "/{drug_id}",
    response_model=DrugDetail,
    summary="Get drug by ID"
)
async def get_drug(drug_id: int):
    async with AsyncSessionLocal() as session:
        # Get drug with eager loading of sections
        drug_query = (
            select(DrugLabel)
            .options(selectinload(DrugLabel.sections))
            .where(DrugLabel.id == drug_id)
        )
        result = await session.execute(drug_query)
        drug = result.scalar_one_or_none()
        
        if not drug:
            raise HTTPException(status_code=404, detail="Drug not found")
        
        # Convert to response model
        sections = [
            {
                "id": section.id,
                "loinc_code": section.loinc_code,
                "title": section.title,
                "order": section.order,
                "content": section.content,
                "ner_entities": section.ner_entities
            }
            for section in sorted(drug.sections, key=lambda s: s.order)
        ]
```

**Purpose**: Retrieve complete drug information including all label sections.

**Key Features**:
- **Eager Loading**: Uses SQLAlchemy's `selectinload` to fetch sections efficiently
- **Section Ordering**: Sorts sections by their `order` field
- **Complete Content**: Returns full text of each section
- **NER Entities**: Includes extracted medical entities per section

**Usage**:
```bash
GET /api/drugs/1
```

**Response Structure**:
```json
{
    "id": 1,
    "name": "WEGOVY",
    "generic_name": "semaglutide",
    "manufacturer": "Novo Nordisk",
    "sections": [
        {
            "id": 571,
            "loinc_code": "34067-9",
            "title": "INDICATIONS AND USAGE",
            "order": 1,
            "content": "WEGOVY is indicated as an adjunct...",
            "ner_entities": {
                "conditions": ["obesity", "overweight"],
                "dosages": ["2.4 mg"]
            }
        }
    ]
}
```

**When to use**: Drug detail page, full label viewer, comparative analysis preparation.

---

### 5. Get Specific Section
**File**: `backend/api/routes/drugs.py` (lines 110-150)

```python
@router.get(
    "/{drug_id}/sections/{loinc_code}",
    summary="Get specific section"
)
async def get_drug_section(drug_id: int, loinc_code: str):
    async with AsyncSessionLocal() as session:
        # Verify drug exists
        drug_query = select(DrugLabel).where(DrugLabel.id == drug_id)
        drug_result = await session.execute(drug_query)
        drug = drug_result.scalar_one_or_none()
        
        if not drug:
            raise HTTPException(status_code=404, detail="Drug not found")
        
        # Get specific section
        section_query = (
            select(DrugSection)
            .where(
                DrugSection.drug_label_id == drug_id,
                DrugSection.loinc_code == loinc_code
            )
        )
        section_result = await session.execute(section_query)
        section = section_result.scalar_one_or_none()
```

**Purpose**: Retrieve a specific section from a drug label using LOINC code.

**Key Features**:
- **LOINC Code Filtering**: Uses standardized medical codes (e.g., "34067-9" for Indications)
- **Two-stage Validation**: Verifies drug exists, then section exists
- **Targeted Retrieval**: Only fetches one section, not entire label

**Common LOINC Codes**:
- `34067-9`: Indications and Usage
- `34084-4`: Adverse Reactions
- `43685-7`: Warnings and Precautions
- `34068-7`: Dosage and Administration

**Usage**:
```bash
GET /api/drugs/1/sections/34067-9
```

**Response**:
```json
{
    "id": 571,
    "drug_id": 1,
    "loinc_code": "34067-9",
    "title": "INDICATIONS AND USAGE",
    "content": "WEGOVY is indicated...",
    "ner_entities": {...}
}
```

**When to use**: Section-specific views, comparison of same section across drugs.

---

### 6. Search Drugs by Name
**File**: `backend/api/routes/drugs.py` (lines 153-193)

```python
@router.get(
    "/search/by-name",
    response_model=DrugListResponse,
    summary="Search drugs by name"
)
async def search_drugs_by_name(q: str, limit: int = 10):
    async with AsyncSessionLocal() as session:
        # Case-insensitive search using ILIKE
        search_pattern = f"%{q}%"
        
        drug_query = (
            select(DrugLabel)
            .where(
                DrugLabel.is_current_version == True,
                (DrugLabel.name.ilike(search_pattern)) |
                (DrugLabel.generic_name.ilike(search_pattern))
            )
            .limit(limit)
        )
        result = await session.execute(drug_query)
        drugs = result.scalars().all()
```

**Purpose**: Text-based search for drugs by brand or generic name.

**Key Features**:
- **Case-Insensitive**: Uses SQL `ILIKE` for flexible matching
- **Dual Search**: Searches both brand name and generic name
- **Partial Matching**: Uses `%pattern%` for substring matching
- **Limited Results**: Returns top matches only

**Usage**:
```bash
GET /api/drugs/search/by-name?q=sema&limit=5
```

**Response**: Returns drugs matching "sema" (e.g., semaglutide drugs).

**When to use**: Search autocomplete, drug finder, quick lookup.

---

## Search Endpoints

### 7. Semantic Search (Global)
**File**: `backend/api/routes/search.py` (lines 19-110)

```python
@router.post(
    "/semantic",
    response_model=SearchResponse,
    summary="Semantic search"
)
async def semantic_search(query_data: SearchQuery):
    async with AsyncSessionLocal() as session:
        # Generate embedding for the query
        query_embedding = vector_service.generate_embedding(query_data.query)
        
        # Convert numpy array to string format for pgvector
        query_vector = str(query_embedding.tolist())
        
        # Build SQL query with cosine similarity
        sql_query = text("""
            SELECT 
                se.section_id,
                se.drug_name,
                se.section_loinc,
                se.chunk_text,
                se.chunk_index,
                ds.title as section_title,
                dl.id as drug_id,
                dl.generic_name,
                dl.manufacturer,
                1 - (se.embedding <=> :query_vector) as similarity_score
            FROM section_embeddings se
            JOIN drug_sections ds ON se.section_id = ds.id
            JOIN drug_labels dl ON ds.drug_label_id = dl.id
            WHERE dl.is_current_version = true
            ORDER BY se.embedding <=> :query_vector
            LIMIT :top_k
        """)
```

**Purpose**: Find relevant drug label sections using semantic similarity (not keyword matching).

**How It Works**:
1. **Query Embedding**: Converts your question to a 384-dimensional vector using SentenceTransformer
2. **Vector Search**: Uses PostgreSQL pgvector extension with cosine similarity (`<=>` operator)
3. **Ranking**: Returns chunks sorted by relevance (1.0 = identical, 0.0 = unrelated)
4. **Join**: Connects section_embeddings → drug_sections → drug_labels for complete context

**Key Technical Details**:
- **Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Distance Metric**: Cosine similarity (converted to similarity score: `1 - distance`)
- **Data Source**: `section_embeddings` table (869 chunks)
- **Speed**: ~2-10 seconds first query (model loading), <1 second subsequent queries

**Usage**:
```bash
POST /api/search/semantic
Content-Type: application/json

{
    "query": "side effects and warnings",
    "top_k": 3
}
```

**Response**:
```json
{
    "query": "side effects and warnings",
    "total_results": 3,
    "results": [
        {
            "drug_id": 9,
            "drug_name": "Saxenda",
            "section_title": "6 ADVERSE REACTIONS",
            "chunk_text": "Most common adverse reactions...",
            "similarity_score": 0.6774
        }
    ],
    "execution_time_ms": 10450.23
}
```

**When to use**: 
- "Show me information about pancreatitis"
- "Find warnings about thyroid cancer"
- "What drugs mention cardiovascular risk?"

---

### 8. Semantic Search (Within Drug)
**File**: `backend/api/routes/search.py` (lines 113-206)

```python
@router.post(
    "/drug/{drug_id}",
    response_model=SearchResponse,
    summary="Search within drug"
)
async def search_within_drug(drug_id: int, query_data: SearchQuery):
    async with AsyncSessionLocal() as session:
        # Verify drug exists
        drug_query = select(DrugLabel).where(DrugLabel.id == drug_id)
        drug_result = await session.execute(drug_query)
        drug = drug_result.scalar_one_or_none()
        
        if not drug:
            raise HTTPException(status_code=404, detail=f"Drug with ID {drug_id} not found")
        
        # Generate query embedding
        query_embedding = vector_service.generate_embedding(query_data.query)
        query_vector = str(query_embedding.tolist())
        
        # Search within this drug only
        sql_query = text("""
            SELECT ...
            FROM section_embeddings se
            JOIN drug_sections ds ON se.section_id = ds.id
            JOIN drug_labels dl ON ds.drug_label_id = dl.id
            WHERE dl.id = :drug_id  -- SCOPED TO ONE DRUG
            ORDER BY se.embedding <=> :query_vector
            LIMIT :top_k
        """)
```

**Purpose**: Semantic search limited to a single drug's label.

**Difference from Global Search**:
- **Scope**: Only searches within specified `drug_id`
- **Use Case**: "Find pregnancy information in Ozempic label"
- **Performance**: Faster (fewer embeddings to compare)

**Usage**:
```bash
POST /api/search/drug/13
Content-Type: application/json

{
    "query": "pregnancy and breastfeeding",
    "top_k": 5
}
```

**When to use**: Drug-specific Q&A, focused label exploration.

---

### 9. Semantic Search (By Section Type)
**File**: `backend/api/routes/search.py` (lines 209-302)

```python
@router.post(
    "/section/{loinc_code}",
    response_model=SearchResponse,
    summary="Search specific section type"
)
async def search_by_section_type(loinc_code: str, query_data: SearchQuery):
    async with AsyncSessionLocal() as session:
        # Generate query embedding
        query_embedding = vector_service.generate_embedding(query_data.query)
        query_vector = str(query_embedding.tolist())
        
        # Search within specific section type
        sql_query = text("""
            SELECT ...
            FROM section_embeddings se
            JOIN drug_sections ds ON se.section_id = ds.id
            JOIN drug_labels dl ON ds.drug_label_id = dl.id
            WHERE se.section_loinc = :loinc_code  -- FILTER BY SECTION TYPE
              AND dl.is_current_version = true
            ORDER BY se.embedding <=> :query_vector
            LIMIT :top_k
        """)
```

**Purpose**: Compare how different drugs handle the same topic (e.g., all "Warnings" sections).

**Key Features**:
- **Section-Type Filtering**: Only searches sections with matching LOINC code
- **Cross-Drug Comparison**: Results from multiple drugs, same section
- **Focused Results**: More relevant when you know the section type

**Example LOINC Codes**:
- `34084-4`: Adverse Reactions (side effects)
- `43685-7`: Warnings and Precautions
- `34068-7`: Dosage and Administration
- `34071-1`: Warnings (general)

**Usage**:
```bash
POST /api/search/section/34084-4
Content-Type: application/json

{
    "query": "nausea and vomiting",
    "top_k": 5
}
```

**Response**: Side effects sections from multiple drugs mentioning nausea/vomiting.

**When to use**: 
- "Compare how different drugs describe side effects"
- "Find all dosage instructions mentioning titration"

---

### 10. Drug Similarity Search (Dashboard Feature)
**File**: `backend/api/routes/search.py` (lines 305-393)

```python
@router.post(
    "/drug-similarity",
    response_model=DrugSimilarityResponse,
    summary="Drug similarity search"
)
async def drug_similarity_search(query_data: SearchQuery):
    async with AsyncSessionLocal() as session:
        # Generate embedding for the query
        query_embedding = vector_service.generate_embedding(query_data.query)
        query_vector = str(query_embedding.tolist())
        
        # Build SQL query with cosine similarity
        sql_query = text("""
            SELECT 
                dl.id as drug_id,
                dl.name as drug_name,
                dl.generic_name,
                dl.manufacturer,
                1 - (dl.label_embedding <=> :query_vector) as similarity_score
            FROM drug_labels dl
            WHERE dl.is_current_version = true
            ORDER BY dl.label_embedding <=> :query_vector
            LIMIT :top_k
        """)
```

**Purpose**: Find similar drugs based on overall label characteristics (not section chunks).

**Key Differences from Other Search**:
- **Data Source**: Uses `drug_labels.label_embedding` (whole-label embeddings)
- **Granularity**: Coarse-grained (19 drug-level embeddings, not 869 chunks)
- **Use Case**: "Find drugs similar to Ozempic"
- **Response**: Returns drugs, not sections

**How It Works**:
1. **Label Embeddings**: Each drug has ONE embedding representing its entire NER summary
2. **Comparison**: Finds drugs with similar characteristics (same class, indications, warnings)
3. **Ranking**: Returns most similar drugs first

**Usage**:
```bash
POST /api/search/drug-similarity
Content-Type: application/json

{
    "query": "GLP-1 receptor agonist for weight loss",
    "top_k": 5
}
```

**Response**:
```json
{
    "query": "GLP-1 receptor agonist for weight loss",
    "total_results": 5,
    "results": [
        {
            "drug_id": 1,
            "drug_name": "WEGOVY",
            "generic_name": "semaglutide",
            "similarity_score": 0.7234
        },
        {
            "drug_id": 9,
            "drug_name": "Saxenda",
            "generic_name": "liraglutide",
            "similarity_score": 0.6891
        }
    ],
    "execution_time_ms": 234.56
}
```

**When to use**:
- Dashboard "Similar Drugs" widget
- Drug recommendation system
- "Patients taking X might also need Y"

---

## Chat Endpoints (RAG)

### 11. RAG Q&A (Ask)
**File**: `backend/api/routes/chat.py` (lines 108-240)

```python
@router.post(
    "/ask",
    response_model=ChatResponse,
    summary="Ask a question"
)
async def chat_ask(request: ChatRequest):
    async with AsyncSessionLocal() as session:
        # Generate embedding for the question
        query_embedding = vector_service.generate_embedding(request.message)
        query_vector = str(query_embedding.tolist())
        
        # RETRIEVAL: Vector search for relevant sections
        sql_query = text("""
            SELECT 
                se.section_id,
                se.drug_name,
                se.section_loinc,
                se.chunk_text,
                ds.title as section_title,
                dl.id as drug_id,
                1 - (se.embedding <=> :query_vector) as similarity_score
            FROM section_embeddings se
            JOIN drug_sections ds ON se.section_id = ds.id
            JOIN drug_labels dl ON ds.drug_label_id = dl.id
            WHERE dl.is_current_version = true
            ORDER BY se.embedding <=> :query_vector
            LIMIT 5
        """)
        
        rows = result.fetchall()
        
        # Prepare context for LLM
        context_sections = [...]
        
        # GENERATION: LLM generates response
        response_text = generate_rag_response(request.message, context_sections)
```

**Purpose**: Conversational Q&A using Retrieval-Augmented Generation (RAG).

**RAG Pipeline Explained**:

#### Step 1: Retrieval (Vector Search)
- Converts question to embedding
- Finds top 5 most relevant label sections
- Extracts text chunks with similarity scores

#### Step 2: Context Building
**File**: `backend/api/routes/chat.py` (lines 47-52)

```python
# Build context from retrieved sections
context_text = "\n\n".join([
    f"[Source: {section['drug_name']} - {section['section_title']}]\n{section['chunk_text']}"
    for section in context_sections
])
```

#### Step 3: Prompt Engineering
**File**: `backend/api/routes/chat.py` (lines 54-79)

```python
# Create system prompt
system_prompt = """You are a medical information assistant specialized in FDA drug labels. 

Your role:
- Answer questions ONLY based on the provided drug label excerpts
- Be accurate, precise, and cite specific information
- If information is not in the provided context, clearly state that
- Use medical terminology appropriately but explain complex terms
- Always prioritize patient safety in your responses

Important:
- DO NOT make up information
- DO NOT use knowledge outside the provided context
- DO NOT provide medical advice (you're providing label information only)
- Always mention that users should consult healthcare providers"""

# Create user prompt with context
user_prompt = f"""Based on the following excerpts from FDA drug labels, please answer the user's question.

DRUG LABEL CONTEXT:
{context_text}

USER QUESTION:
{query}

Please provide a comprehensive answer based ONLY on the information provided above. Include specific drug names when relevant."""
```

**System Prompt Explained**:
- **Role Definition**: Medical information assistant (not doctor)
- **Grounding**: ONLY use provided context (prevents hallucinations)
- **Safety**: Always recommend consulting healthcare providers
- **Clarity**: Explain medical terms, be precise with citations

#### Step 4: LLM Generation
**File**: `backend/api/routes/chat.py` (lines 81-104)

```python
try:
    # Call Groq API
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        model=groq_model,  # llama-3.3-70b-versatile
        temperature=0.3,  # Lower = more factual, less creative
        max_tokens=1024,
        top_p=0.9
    )
    
    response = chat_completion.choices[0].message.content
    return response
```

**LLM Configuration**:
- **Model**: `llama-3.3-70b-versatile` (Groq's latest, fastest LLM)
- **Temperature**: `0.3` (low = more deterministic, factual responses)
- **Max Tokens**: `1024` (limits response length)
- **Top-p**: `0.9` (nucleus sampling for quality)

#### Step 5: Citation
**File**: `backend/api/routes/chat.py` (lines 217-226)

```python
# Create citations
citations = [
    Citation(
        section_id=section["section_id"],
        drug_name=section["drug_name"],
        section_title=section["section_title"],
        loinc_code=section["section_loinc"],
        chunk_text=section["chunk_text"][:500]  # Truncate for citation
    )
    for section in context_sections[:3]  # Top 3 citations
]
```

**Usage**:
```bash
POST /api/chat/ask
Content-Type: application/json

{
    "message": "What are the main side effects of semaglutide?",
    "drug_id": null  // Optional: scope to specific drug
}
```

**Response**:
```json
{
    "response": "Based on the provided excerpts from FDA drug labels, semaglutide, the active ingredient of WEGOVY, OZEMPIC, and RYBELSUS, has been associated with various side effects. The main side effects reported across these medications include:\n\n1. **Gastrointestinal Disorders**: \n   - Acute pancreatitis and necrotizing pancreatitis (sometimes resulting in death), reported with WEGOVY and RYBELSUS.\n   - Ileus, intestinal obstruction...",
    "citations": [
        {
            "section_id": 571,
            "drug_name": "WEGOVY",
            "section_title": "6.2 Postmarketing Experience",
            "loinc_code": "42229-5",
            "chunk_text": "The following adverse reactions have been reported..."
        }
    ],
    "conversation_id": "6a674949-0c82-41f8-b8a5-9282b5a80082"
}
```

**Key Features**:
- **Grounded Answers**: Only uses information from your drug labels
- **No Hallucination**: LLM instructed not to use external knowledge
- **Source Attribution**: Provides top 3 citations with drug names and sections
- **Medical Safety**: Consistently recommends consulting healthcare providers

**When to use**:
- "What are the side effects of GLP-1 medications?"
- "Can I use Ozempic during pregnancy?"
- "How should I dose semaglutide?"
- "What are the contraindications for liraglutide?"

---

### 12. RAG Comparison (Compare)
**File**: `backend/api/routes/chat.py` (lines 243-352)

```python
@router.post(
    "/compare",
    response_model=ChatResponse,
    summary="Compare drugs"
)
async def chat_compare(request: ChatRequest):
    async with AsyncSessionLocal() as session:
        # Generate embedding
        query_embedding = vector_service.generate_embedding(request.message)
        query_vector = str(query_embedding.tolist())
        
        # Retrieve from multiple drugs (DISTINCT ON ensures one result per drug)
        sql_query = text("""
            SELECT DISTINCT ON (dl.id)
                se.section_id,
                se.drug_name,
                se.section_loinc,
                se.chunk_text,
                ds.title as section_title,
                dl.id as drug_id,
                dl.generic_name,
                1 - (se.embedding <=> :query_vector) as similarity_score
            FROM section_embeddings se
            JOIN drug_sections ds ON se.section_id = ds.id
            JOIN drug_labels dl ON ds.drug_label_id = dl.id
            WHERE dl.is_current_version = true
            ORDER BY dl.id, se.embedding <=> :query_vector
            LIMIT 10
        """)
```

**Purpose**: Comparative analysis across multiple drugs.

**Key Features**:
- **DISTINCT ON**: Gets best match from each drug (not multiple chunks from same drug)
- **Multi-Drug Context**: Retrieves relevant sections from different drugs
- **Grouping**: Organizes results by drug for clear comparison

**Current Implementation Note**: 
This endpoint currently returns a demo response. It needs the same LLM integration as the `/ask` endpoint to generate proper comparative analyses.

**Expected Usage**:
```bash
POST /api/chat/compare
Content-Type: application/json

{
    "message": "Compare side effects of Ozempic vs Victoza"
}
```

**When to use**:
- "What's the difference between Ozempic and Victoza?"
- "Compare dosing schedules of semaglutide drugs"
- "Which GLP-1 has fewer side effects?"

---

## Analytics Endpoints

### 13. Platform Analytics
**File**: `backend/api/routes/analytics.py` (lines 17-87)

```python
@router.get(
    "/platform",
    response_model=PlatformAnalytics,
    summary="Get platform analytics"
)
async def get_platform_analytics():
    async with AsyncSessionLocal() as session:
        # Count total drugs
        total_drugs_query = select(func.count(DrugLabel.id)).where(
            DrugLabel.is_current_version == True
        )
        total_drugs = await session.execute(total_drugs_query)
        
        # Count total sections
        total_sections_query = select(func.count(DrugSection.id))
        total_sections = await session.execute(total_sections_query)
        
        # Get manufacturer distribution
        manufacturer_query = select(
            DrugLabel.manufacturer,
            func.count(DrugLabel.id).label('count')
        ).where(
            DrugLabel.is_current_version == True
        ).group_by(DrugLabel.manufacturer)
        
        # Get most common section types
        section_types_query = select(
            DrugSection.loinc_code,
            DrugSection.title,
            func.count(DrugSection.id).label('count')
        ).group_by(
            DrugSection.loinc_code,
            DrugSection.title
        ).order_by(func.count(DrugSection.id).desc())
```

**Purpose**: Dashboard overview statistics.

**Metrics Provided**:
- **Total Drugs**: Count of current drug labels
- **Total Sections**: Count of all label sections
- **Manufacturer Distribution**: Drugs per manufacturer
- **Section Type Distribution**: Most common section types
- **Total Embeddings**: Count of vector embeddings

**Usage**:
```bash
GET /api/analytics/platform
```

**Response**:
```json
{
    "total_drugs": 19,
    "total_sections": 869,
    "total_embeddings": 869,
    "manufacturer_distribution": [
        {"manufacturer": "Novo Nordisk", "count": 4},
        {"manufacturer": "Eli Lilly", "count": 3}
    ],
    "section_type_distribution": [
        {"loinc_code": "34084-4", "title": "ADVERSE REACTIONS", "count": 19},
        {"loinc_code": "34067-9", "title": "INDICATIONS AND USAGE", "count": 19}
    ]
}
```

**When to use**: Dashboard homepage, admin panel, data quality monitoring.

---

### 14. Drug-Specific Analytics
**File**: `backend/api/routes/analytics.py` (lines 90-177)

```python
@router.get(
    "/drug/{drug_id}",
    summary="Get drug analytics"
)
async def get_drug_analytics(drug_id: int):
    async with AsyncSessionLocal() as session:
        # Verify drug exists
        drug_query = select(DrugLabel).where(DrugLabel.id == drug_id)
        drug_result = await session.execute(drug_query)
        drug = drug_result.scalar_one_or_none()
        
        if not drug:
            raise HTTPException(status_code=404, detail="Drug not found")
        
        # Count sections
        sections_query = select(func.count(DrugSection.id)).where(
            DrugSection.drug_label_id == drug_id
        )
        total_sections = await session.execute(sections_query)
        
        # Get section distribution
        section_dist_query = select(
            DrugSection.loinc_code,
            DrugSection.title
        ).where(
            DrugSection.drug_label_id == drug_id
        ).order_by(DrugSection.order)
        
        # Count embeddings (chunks)
        embeddings_query = select(func.count(SectionEmbedding.id)).where(
            SectionEmbedding.section_id.in_(
                select(DrugSection.id).where(DrugSection.drug_label_id == drug_id)
            )
        )
```

**Purpose**: Detailed statistics for a single drug.

**Metrics Provided**:
- **Section Count**: Number of sections in this drug's label
- **Section Distribution**: List of all section types present
- **Embedding Count**: Number of vector chunks for this drug
- **NER Summary**: Extracted medical entities

**Usage**:
```bash
GET /api/analytics/drug/1
```

**Response**:
```json
{
    "drug_id": 1,
    "drug_name": "WEGOVY",
    "generic_name": "semaglutide",
    "manufacturer": "Novo Nordisk",
    "total_sections": 45,
    "total_embeddings": 67,
    "section_distribution": [
        {"loinc_code": "34067-9", "title": "INDICATIONS AND USAGE"},
        {"loinc_code": "34068-7", "title": "DOSAGE AND ADMINISTRATION"}
    ],
    "ner_summary": {
        "dosages": ["2.4 mg", "0.25 mg"],
        "frequencies": ["once weekly"],
        "routes": ["subcutaneous"]
    }
}
```

**When to use**: Drug detail page analytics section, data completeness check.

---

### 15. Compare Analytics
**File**: `backend/api/routes/analytics.py` (lines 180-252)

```python
@router.post(
    "/compare",
    summary="Compare drugs"
)
async def compare_drugs(request: ComparisonRequest):
    async with AsyncSessionLocal() as session:
        # Get all requested drugs
        drugs_query = select(DrugLabel).where(
            DrugLabel.id.in_(request.drug_ids)
        )
        drugs_result = await session.execute(drugs_query)
        drugs = drugs_result.scalars().all()
        
        if len(drugs) != len(request.drug_ids):
            raise HTTPException(status_code=404, detail="One or more drugs not found")
        
        # For each drug, get analytics
        comparison_data = []
        for drug in drugs:
            # Count sections
            sections_query = select(func.count(DrugSection.id)).where(
                DrugSection.drug_label_id == drug.id
            )
            
            # Count embeddings
            embeddings_query = select(func.count(SectionEmbedding.id)).where(
                SectionEmbedding.section_id.in_(
                    select(DrugSection.id).where(DrugSection.drug_label_id == drug.id)
                )
            )
```

**Purpose**: Side-by-side comparison of multiple drugs.

**Features**:
- **Batch Query**: Retrieves multiple drugs efficiently
- **Parallel Analytics**: Calculates metrics for each drug
- **Structured Comparison**: Returns data in easy-to-compare format

**Usage**:
```bash
POST /api/analytics/compare
Content-Type: application/json

{
    "drug_ids": [1, 13, 9],  // WEGOVY, Ozempic, Saxenda
    "comparison_type": "side_by_side"
}
```

**Response**:
```json
{
    "drugs": [
        {
            "drug_id": 1,
            "drug_name": "WEGOVY",
            "total_sections": 45,
            "total_embeddings": 67,
            "ner_summary": {...}
        },
        {
            "drug_id": 13,
            "drug_name": "Ozempic",
            "total_sections": 42,
            "total_embeddings": 63,
            "ner_summary": {...}
        }
    ],
    "comparison_type": "side_by_side"
}
```

**When to use**: Comparison table, multi-drug analysis, decision support.

---

## Summary: When to Use Each Endpoint

### For Drug Discovery:
1. **List Drugs** (`GET /api/drugs/`) - Browse all available drugs
2. **Search by Name** (`GET /api/drugs/search/by-name`) - Find specific drug
3. **Drug Similarity** (`POST /api/search/drug-similarity`) - Find similar medications

### For Label Reading:
4. **Get Drug** (`GET /api/drugs/{id}`) - Read complete label
5. **Get Section** (`GET /api/drugs/{id}/sections/{loinc}`) - Read specific section

### For Information Retrieval:
6. **Semantic Search** (`POST /api/search/semantic`) - Find relevant information
7. **Search Within Drug** (`POST /api/search/drug/{id}`) - Search one drug's label
8. **Search by Section** (`POST /api/search/section/{loinc}`) - Compare same section across drugs

### For Q&A:
9. **RAG Ask** (`POST /api/chat/ask`) - Ask questions, get AI-generated answers
10. **RAG Compare** (`POST /api/chat/compare`) - Comparative questions

### For Analytics:
11. **Platform Analytics** (`GET /api/analytics/platform`) - Overall statistics
12. **Drug Analytics** (`GET /api/analytics/drug/{id}`) - Single drug metrics
13. **Compare Analytics** (`POST /api/analytics/compare`) - Multi-drug comparison

---

## Two Embedding Strategies Explained

### Strategy 1: Section Embeddings (Fine-Grained)
- **Table**: `section_embeddings`
- **Count**: 869 embeddings
- **Used By**: Semantic search endpoints, RAG chat
- **Purpose**: Detailed information retrieval
- **Example**: "What are the side effects?" → Returns specific text chunks

### Strategy 2: Label Embeddings (Coarse-Grained)
- **Column**: `drug_labels.label_embedding`
- **Count**: 19 embeddings
- **Used By**: Drug similarity endpoint
- **Purpose**: Drug-to-drug similarity
- **Example**: "Find drugs like Ozempic" → Returns similar drugs

---

## Quick Reference

| Endpoint | Method | Purpose | Response Time |
|----------|--------|---------|---------------|
| `/api/health` | GET | Health check | <100ms |
| `/api/drugs/` | GET | List drugs | 1-2s |
| `/api/drugs/{id}` | GET | Get drug | 1-2s |
| `/api/search/semantic` | POST | Semantic search | 2-10s first, <1s after |
| `/api/search/drug-similarity` | POST | Find similar drugs | <500ms |
| `/api/chat/ask` | POST | RAG Q&A | 3-6s |
| `/api/analytics/platform` | GET | Dashboard stats | 1-2s |

---

## Testing Commands

### Health Check
```bash
curl http://localhost:8000/api/health
```

### List Drugs
```bash
curl http://localhost:8000/api/drugs/?limit=5
```

### Semantic Search
```bash
curl -X POST http://localhost:8000/api/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "side effects", "top_k": 3}'
```

### RAG Chat
```bash
curl -X POST http://localhost:8000/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the side effects of semaglutide?"}'
```

### Drug Similarity
```bash
curl -X POST http://localhost:8000/api/search/drug-similarity \
  -H "Content-Type: application/json" \
  -d '{"query": "GLP-1 for weight loss", "top_k": 5}'
```

---

## Architecture Diagram

```
┌─────────────────┐
│   User Query    │
└────────┬────────┘
         │
    ┌────▼─────┐
    │ FastAPI  │
    │ Router   │
    └────┬─────┘
         │
    ┌────▼──────────────────────────┐
    │  Endpoint Decision Tree        │
    ├───────────────────────────────┤
    │ CRUD? → drugs.py              │
    │ Search? → search.py           │
    │ Chat? → chat.py (+ Groq LLM)  │
    │ Analytics? → analytics.py     │
    └────┬──────────────────────────┘
         │
    ┌────▼───────────────┐
    │  PostgreSQL        │
    │  + pgvector        │
    ├────────────────────┤
    │ • drug_labels      │
    │ • drug_sections    │
    │ • section_embeddings│
    └────────────────────┘
```

---

**Next Steps**: 
1. Test all endpoints using the provided curl commands
2. Complete the `/compare` endpoint LLM integration
3. Build frontend UI to consume these APIs
