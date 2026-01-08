# Archived Scripts & Documentation Reference

**Project**: GLP-1 Regulatory Intelligence Platform  
**Created**: January 7, 2026  
**Purpose**: Comprehensive reference for deleted scripts, tests, and documentation

This document preserves knowledge about all testing scripts, data processing utilities, one-time migrations, and documentation that were removed to clean up the project structure. Keep this for future reference when similar operations are needed.

---

## Table of Contents
1. [Test & Debug Scripts](#test--debug-scripts)
2. [Data Processing Scripts](#data-processing-scripts)
3. [One-Time Migration Scripts](#one-time-migration-scripts)
4. [Documentation Files](#documentation-files)
5. [Utility Scripts](#utility-scripts)

---

## Test & Debug Scripts

### 1. **backend/test_api.py**
**Purpose**: Comprehensive API endpoint testing  
**What it did**:
- Tested all 31 FastAPI endpoints (13 original + 18 Reports)
- Validated request/response schemas
- Checked authentication and error handling
- Tested database connections and queries

**Key Test Coverage**:
- `/drugs` - List all drugs
- `/drugs/{drug_id}` - Get specific drug
- `/drugs/{drug_id}/label` - Get label sections
- `/search/semantic` - Semantic search across labels
- `/search/keyword` - Keyword search
- `/compare/drugs` - Drug comparison
- `/compare/changes` - Track label changes
- `/analytics/*` - All analytics endpoints
- `/chat/query` - RAG chat functionality
- `/reports/*` - All 18 report generation endpoints

**How to recreate**: Use FastAPI's TestClient or pytest with httpx
```python
from fastapi.testclient import TestClient
from backend.api.main import app
client = TestClient(app)
response = client.get("/drugs")
assert response.status_code == 200
```

---

### 2. **backend/test_dashboard_direct.py**
**Purpose**: Direct testing of dashboard search functionality  
**What it did**:
- Tested semantic search with vector embeddings
- Validated keyword search with filters
- Checked pagination and sorting
- Tested multi-drug search scenarios

**Key Features Tested**:
- Vector similarity search using pgvector
- Full-text search with PostgreSQL
- Filter by drug names, sections, date ranges
- Combined semantic + keyword search
- Results ranking and relevance scoring

**Sample Test Case**:
```python
# Test semantic search for "side effects of diabetes medication"
results = search_service.semantic_search(
    query="side effects of diabetes medication",
    limit=10,
    drug_filter=["OZEMPIC", "WEGOVY"]
)
```

---

### 3. **backend/test_dashboard_search.py**
**Purpose**: Integration testing for dashboard search API  
**What it did**:
- End-to-end testing of search endpoints
- Tested `/search/semantic` and `/search/keyword` routes
- Validated response formatting and pagination
- Checked error handling for invalid queries

**Why it was needed**: Ensured search functionality worked correctly with real database data and API layer

---

### 4. **backend/scripts/check_response.py**
**Purpose**: Debug script for DailyMed API testing  
**What it did**:
- Tested DailyMed download endpoints
- Verified ZIP file download functionality
- Checked HTTP response codes and headers
- Validated content types

**Final Working URL Discovered**:
```
https://dailymed.nlm.nih.gov/dailymed/downloadzipfile.cfm?setId={SET_ID}
```
Note: `setId` parameter is case-sensitive (capital 'I')

---

### 5. **backend/scripts/test_database_connection.py**
**Purpose**: Database connectivity verification  
**What it did**:
- Tested PostgreSQL connection to Supabase
- Validated connection pooler settings
- Checked SSL/TLS configuration
- Verified authentication credentials
- Tested query execution

**Connection String Format**:
```
postgresql://postgres.{ref}:{password}@aws-1-{region}.pooler.supabase.com:5432/postgres
```

**Sample Test**:
```python
from sqlalchemy import create_engine, text
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print("✓ Database connection successful")
```

---

### 6. **backend/scripts/test_download.py**
**Purpose**: Test DailyMed ZIP file downloads  
**What it did**:
- Downloaded ZIP files using SET_ID
- Verified ZIP file integrity
- Listed contents of downloaded archives
- Tested with multiple SET_IDs (OZEMPIC, SAXENDA, WEGOVY)

**Correct Saxenda SET_ID**: `3946d389-0926-4f77-a708-0acb8153b143`

**Download Process**:
1. Call DailyMed API with SET_ID
2. Verify HTTP 200 response
3. Check Content-Type: application/zip
4. Save to temp directory
5. Validate ZIP structure with zipfile module

---

### 7. **backend/scripts/test_etl_pipeline.py**
**Purpose**: Test complete ETL (Extract, Transform, Load) pipeline  
**What it did**:
- Tested label parsing from XML files
- Validated section extraction (warnings, dosage, etc.)
- Tested NER (Named Entity Recognition) for drug names
- Verified vector embedding generation
- Checked database insertion

**ETL Pipeline Stages**:
1. **Extract**: Parse XML from ZIP files
2. **Transform**: 
   - Extract structured sections
   - Generate embeddings using sentence-transformers
   - Run NER to identify entities
   - Create chunks for vector search
3. **Load**: Insert into PostgreSQL with pgvector

**Models Used**:
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- NER: `dmis-lab/biobert-base-cased-v1.2`

---

### 8. **backend/scripts/test_ner.py**
**Purpose**: Test Named Entity Recognition functionality  
**What it did**:
- Tested entity extraction from drug labels
- Validated entity types (DRUG, DISEASE, SYMPTOM, DOSAGE)
- Checked confidence thresholds (>0.7)
- Tested batch processing

**Entity Types Detected**:
- Drug names and active ingredients
- Medical conditions and diseases
- Symptoms and side effects
- Dosage information
- Drug interactions

**Sample Output**:
```python
entities = [
    {"text": "liraglutide", "type": "DRUG", "confidence": 0.95},
    {"text": "diabetes mellitus", "type": "DISEASE", "confidence": 0.89},
    {"text": "nausea", "type": "SYMPTOM", "confidence": 0.87}
]
```

---

### 9. **backend/scripts/test_parser.py**
**Purpose**: Test XML label parsing functionality  
**What it did**:
- Parsed FDA SPL (Structured Product Labeling) XML
- Extracted standard sections (34067-9, 43678-2, etc.)
- Handled nested XML structures
- Validated section titles and content
- Tested error handling for malformed XML

**Standard Section LOINC Codes**:
- `34067-9`: INDICATIONS & USAGE
- `34084-4`: ADVERSE REACTIONS
- `34068-7`: DOSAGE & ADMINISTRATION
- `34071-1`: WARNINGS AND PRECAUTIONS
- `34073-7`: DRUG INTERACTIONS
- `43678-2`: CLINICAL PHARMACOLOGY

---

### 10. **backend/scripts/test_s3_connection.py**
**Purpose**: Test AWS S3 connectivity and operations  
**What it did**:
- Tested S3 bucket access (glp1-raw-labels)
- Validated AWS credentials
- Tested file upload/download
- Checked bucket permissions
- Verified regional configuration (eu-north-1)

**S3 Operations Tested**:
```python
# Upload
s3_client.upload_file('local.zip', 'glp1-raw-labels', 'labels/active/SET_ID/v1/label.zip')

# Download
s3_client.download_file('glp1-raw-labels', 'labels/active/SET_ID/v1/label.zip', 'local.zip')

# List
response = s3_client.list_objects_v2(Bucket='glp1-raw-labels', Prefix='labels/')
```

---

### 11. **backend/scripts/test_vector_service.py**
**Purpose**: Test vector embedding and similarity search  
**What it did**:
- Tested embedding generation for text chunks
- Validated vector dimensions (384 for all-MiniLM-L6-v2)
- Tested pgvector similarity search
- Checked cosine similarity calculations
- Validated vector index performance

**Vector Search Process**:
1. Generate query embedding
2. Search using pgvector `<=>` operator (cosine distance)
3. Return top K most similar chunks
4. Include metadata (drug, section, text)

**Sample Query**:
```sql
SELECT text, drug_name, section_title, 
       1 - (embedding <=> query_embedding) as similarity
FROM label_chunks
ORDER BY embedding <=> query_embedding
LIMIT 10;
```

---

### 12. **backend/scripts/verify_database.py**
**Purpose**: Database schema and data verification  
**What it did**:
- Verified all tables exist (drug_labels, label_sections, etc.)
- Checked column types and constraints
- Validated foreign key relationships
- Counted records in each table
- Checked for data integrity issues

**Tables Verified**:
- `drug_labels`: 15 drugs (OZEMPIC, WEGOVY, SAXENDA, etc.)
- `label_sections`: ~100+ sections per drug
- `label_chunks`: ~500+ chunks for vector search
- `drug_version_history`: Version tracking
- `report_generation_log`: Report history
- `report_access_log`: Report access tracking

---

## Data Processing Scripts

### 13. **backend/scripts/cleanup_database.py**
**Purpose**: Clean up test data and duplicates  
**What it did**:
- Removed duplicate drug entries
- Cleaned up orphaned label sections
- Deleted test records
- Optimized database by running VACUUM
- Reset sequences

**When it was run**: During initial development after multiple test uploads

**Cleanup Operations**:
```sql
-- Remove duplicates
DELETE FROM drug_labels 
WHERE id NOT IN (SELECT MIN(id) FROM drug_labels GROUP BY set_id);

-- Remove orphaned sections
DELETE FROM label_sections 
WHERE drug_id NOT IN (SELECT id FROM drug_labels);

-- Vacuum
VACUUM FULL ANALYZE;
```

---

### 14. **backend/scripts/cleanup_duplicates.py**
**Purpose**: Specific duplicate removal for drug labels  
**What it did**:
- Identified duplicate entries by set_id
- Kept the most recent version
- Removed older duplicates
- Updated foreign key references

**Duplicate Detection Logic**:
- Group by `set_id`
- Keep record with highest `version` number
- Keep record with most recent `processed_at` timestamp
- Delete others

---

### 15. **backend/scripts/process_all_labels.py**
**Purpose**: Initial batch processing of all drug labels  
**What it did**:
- Processed all 15 GLP-1 drug labels from S3
- Extracted sections from XML
- Generated embeddings for all content
- Ran NER on all text
- Inserted into database

**Processing Steps**:
1. List all ZIP files in S3 bucket
2. Download each ZIP
3. Extract XML files
4. Parse SPL structure
5. Extract sections
6. Generate embeddings (batch processing)
7. Run NER
8. Insert into PostgreSQL

**Runtime**: ~20-30 minutes for 15 drugs

---

### 16. **backend/scripts/process_new_labels.py**
**Purpose**: Process newly uploaded drug labels  
**What it did**:
- Processed individual drug labels manually
- Updated existing drugs with new versions
- Added new drugs to the system
- Re-generated embeddings if needed

**Usage**:
```bash
python backend/scripts/process_new_labels.py --drug MOUNJARO --version 1
```

---

### 17. **backend/scripts/reprocess_labels.py**
**Purpose**: Reprocess labels after schema or model changes  
**What it did**:
- Re-parsed labels with updated parsers
- Re-generated embeddings with new models
- Re-ran NER with updated thresholds
- Updated existing database records

**When it was used**:
- After adding `label_embedding` column
- After switching embedding models
- After NER model updates
- After parser improvements

---

### 18. **backend/scripts/upload_fda_labels.py**
**Purpose**: Upload FDA label ZIP files to S3  
**What it did**:
- Downloaded labels from DailyMed
- Validated ZIP file structure
- Uploaded to S3 with proper naming convention
- Created metadata records
- Organized in folder structure

**S3 Folder Structure**:
```
glp1-raw-labels/
├── labels/
│   ├── active/
│   │   ├── {SET_ID}/
│   │   │   ├── v1/
│   │   │   │   └── label.zip
│   │   │   ├── v2/
│   │   │   │   └── label.zip
│   └── archive/
│       └── {SET_ID}/
│           └── old_versions/
```

**File Naming**: `{SET_ID}_v{VERSION}.zip`

---

## One-Time Migration Scripts

### 19. **backend/scripts/migrate_database.py**
**Purpose**: Initial database schema creation  
**What it did**:
- Created all base tables
- Set up primary keys and indexes
- Created foreign key constraints
- Added initial data

**Tables Created**:
- `drug_labels`: Main drug information
- `label_sections`: Structured label content
- `label_chunks`: Vector search chunks
- `drug_comparisons`: Comparison cache

**Indexes Created**:
- B-tree indexes on `drug_id`, `set_id`
- GIN indexes for full-text search
- IVFFLAT indexes for vector search

---

### 20. **backend/scripts/migrate_add_label_embedding.py**
**Purpose**: Add label_embedding column for full-label vectors  
**What it did**:
- Added `label_embedding` column to `label_sections`
- Type: `vector(384)` for pgvector
- Generated embeddings for all existing labels
- Created vector index for similarity search

**Migration SQL**:
```sql
ALTER TABLE label_sections 
ADD COLUMN label_embedding vector(384);

-- Generate embeddings for existing data
UPDATE label_sections 
SET label_embedding = generate_embedding(full_text);

-- Create index
CREATE INDEX idx_label_embedding_ivfflat 
ON label_sections USING ivfflat (label_embedding vector_cosine_ops);
```

**Why it was needed**: To support full-section semantic search instead of just chunks

---

### 21. **backend/scripts/migrate_unique_constraint.py**
**Purpose**: Add unique constraint on set_id  
**What it did**:
- Added unique constraint to prevent duplicate drugs
- Cleaned up existing duplicates first
- Created unique index for performance

**Migration SQL**:
```sql
-- Clean duplicates first
DELETE FROM drug_labels 
WHERE id NOT IN (
    SELECT MIN(id) FROM drug_labels GROUP BY set_id
);

-- Add constraint
ALTER TABLE drug_labels 
ADD CONSTRAINT unique_set_id UNIQUE (set_id);
```

**Why it was needed**: Prevent accidental duplicate drug entries during uploads

---

### 22. **backend/scripts/migrations/remove_redundant_column.py**
**Purpose**: Remove duplicate version tracking column  
**What it did**:
- Removed `current_label_version` column
- Kept existing `version` column (INTEGER)
- Migrated data if needed

**Issue**: Initially created `current_label_version` column when `version` already existed

**Migration SQL**:
```sql
ALTER TABLE drug_labels DROP COLUMN current_label_version;
```

---

### 23. **backend/scripts/migrations/add_reports_tables.py**
**Purpose**: Create tables for Reports Component Phase 1  
**What it did**:
- Created `report_generation_log` table
- Created `report_access_log` table
- Set up foreign keys to `drug_labels`
- Created indexes for query performance

**Tables Created**:

**report_generation_log**:
- `id`: UUID primary key
- `report_type`: Type of report (comparison, timeline, etc.)
- `parameters`: JSONB with report parameters
- `generated_at`: Timestamp
- `generated_by`: User identifier
- `status`: success/failed/pending
- `file_path`: S3 path (future use)

**report_access_log**:
- `id`: UUID primary key
- `report_id`: Foreign key to report_generation_log
- `accessed_at`: Timestamp
- `accessed_by`: User identifier
- `access_type`: view/download/export

---

### 24. **backend/scripts/migrations/add_watchdog_tables.py**
**Purpose**: Create tables for Watchdog Pipeline  
**What it did**:
- Added columns to `drug_labels` table
- Created `drug_version_history` table
- Set up foreign keys and indexes

**Columns Added to drug_labels**:
- `version_check_enabled`: BOOLEAN (default false)
- `last_version_check`: TIMESTAMP

**drug_version_history Table**:
- `id`: SERIAL primary key
- `drug_id`: Foreign key to drug_labels
- `old_version`: VARCHAR (previous version)
- `new_version`: VARCHAR (new version)
- `s3_key`: VARCHAR (S3 path to new label)
- `publish_date`: DATE (DailyMed publish date)
- `detected_at`: TIMESTAMP (when we detected it)
- `processed`: BOOLEAN (ETL processed?)
- `notes`: TEXT (optional notes)

**Why it was needed**: Enable automated label version monitoring via GitHub Actions

---

### 25. **backend/scripts/migrations/sql/add_reports_tables.sql**
**Purpose**: SQL file for report tables creation  
**Content**: Pure SQL version of add_reports_tables.py migration

**Usage**: Can be run directly in Supabase SQL editor or via psql:
```bash
psql $DATABASE_URL < backend/scripts/migrations/sql/add_reports_tables.sql
```

---

## Documentation Files

### 26. **Root Documentation (12 files)**

#### **RESUME_TOMORROW.md**
Session notes and next-day tasks. Tracked:
- Last completed features
- Blockers encountered
- Next steps planned
- Questions to resolve

#### **SESSION_SUMMARY.md**
Detailed session summaries including:
- Features implemented
- Bugs fixed
- Decisions made
- Code changes

#### **PROGRESS.md**
Overall project progress tracking:
- Completed milestones
- Pending tasks
- Feature roadmap
- Timeline estimates

#### **WATCHDOG_ARCHITECTURE.md**
Technical architecture for Watchdog Pipeline:
- System components (VersionChecker, S3Uploader, Notifier)
- Data flow diagrams
- API integration details
- Database schema for version tracking

#### **WATCHDOG_SETUP_GUIDE.md**
Step-by-step setup instructions:
1. Create GitHub Secrets (DATABASE_URL, AWS credentials)
2. Run database migrations
3. Enable drugs for monitoring
4. Test manual workflow
5. Verify daily automation

#### **WATCHDOG_START_HERE.md**
Quick start guide for Watchdog:
- Prerequisites
- 5-minute setup
- First test run
- Troubleshooting common issues

#### **WATCHDOG_TESTING_GUIDE.md**
Comprehensive testing procedures:
- Manual workflow testing
- API endpoint testing
- Database verification
- S3 upload validation
- Email notification testing

#### **WATCHDOG_QUICK_REFERENCE.md**
Quick reference card:
- GitHub Actions URLs
- Important SET_IDs
- Common commands
- API endpoints
- SQL queries

#### **forgithub.pdf**
GitHub Actions documentation reference (external resource)

#### **SETUP_GUIDE.py**
Python-based interactive setup script:
- Collected environment variables
- Tested database connection
- Validated AWS credentials
- Created .env file
- Ran initial migrations

---

### 27. **Backend Documentation (7 files)**

#### **backend/API_ENDPOINTS_GUIDE.md**
Complete API documentation:
- All 31 endpoints with descriptions
- Request/response schemas
- Query parameters
- Error codes
- Example curl commands

**Key Sections**:
- Drug Management (5 endpoints)
- Search (2 endpoints)
- Comparison (3 endpoints)
- Analytics (8 endpoints)
- Chat/RAG (1 endpoint)
- Reports (18 endpoints)

#### **backend/API_README.md**
API overview and quick start:
- Authentication (future)
- Base URL structure
- Common headers
- Response formats
- Pagination
- Error handling

#### **backend/COMPLETE_WORKFLOW_ANALYSIS.md**
Deep dive into application workflows:
- User journey maps
- Data flow diagrams
- Component interactions
- State management
- Caching strategies

#### **backend/DASHBOARD_SEARCH_CLARIFICATION.md**
Search functionality specifications:
- Semantic vs keyword search
- Ranking algorithms
- Filter combinations
- Performance optimizations
- Future enhancements

#### **backend/FINAL_API_ARCHITECTURE.md**
API architecture design:
- FastAPI project structure
- Route organization
- Dependency injection
- Database session management
- Error handling patterns
- CORS configuration

#### **backend/SEMANTIC_DIFF_COLOR_SYSTEM.md**
Color coding system for label comparisons:
- Red: Deletions
- Green: Additions
- Yellow: Modifications
- Blue: Moved sections
- Gray: Unchanged content

**Use Case**: Visual representation of label changes in comparison reports

#### **backend/TEST_RESULTS.md**
Test execution results:
- Test coverage percentages
- Passed/failed tests
- Performance benchmarks
- Known issues
- Test environment details

---

### 28. **docs/DATABASE_FIXES.md**
Database troubleshooting guide:
- Common errors and solutions
- Migration rollback procedures
- Data corruption fixes
- Performance tuning
- Backup/restore procedures

**Common Fixes Documented**:
- Duplicate key violations
- Foreign key constraint errors
- Vector index issues
- Connection pool exhaustion
- Slow query optimization

---

## Utility Scripts

### 29. **add_host.sh**
**Purpose**: Add Supabase host to /etc/hosts  
**What it did**:
```bash
echo "0.0.0.0 aws-1-eu-north-1.pooler.supabase.com" >> /etc/hosts
```

**Why it existed**: Troubleshooting DNS resolution issues during development

---

### 30. **backend/scripts/init_database.py**
**Purpose**: Initialize database with base data  
**Status**: **KEPT** - Still needed for fresh installations

**What it does**:
- Creates all tables
- Inserts reference data
- Sets up indexes
- Validates schema

---

### 31. **backend/scripts/enable_saxenda.py**
**Purpose**: Enable Saxenda for version monitoring  
**Status**: **KEPT** - Example for enabling other drugs

**What it does**:
```python
UPDATE drug_labels 
SET version_check_enabled = true 
WHERE set_id = '3946d389-0926-4f77-a708-0acb8153b143';
```

---

## Key Learnings & Important Notes

### Database Schema Evolution
1. **Initial Schema**: Basic drug_labels and label_sections
2. **Added**: Vector embeddings for semantic search
3. **Added**: Version tracking for Watchdog
4. **Added**: Reports logging tables
5. **Fixed**: Removed redundant columns, added unique constraints

### API Development Journey
1. Started with 13 core endpoints
2. Added semantic search (2 endpoints)
3. Added comparison features (3 endpoints)
4. Added analytics (8 endpoints)
5. Added comprehensive reports (18 endpoints)
6. **Total**: 31 production endpoints

### Watchdog Pipeline Development
1. **Initial Approach**: Tried `/spls/{SET_ID}.json` - Failed (415 error)
2. **Second Attempt**: Used `/spls/{SET_ID}/media.json` - Complex two-step process
3. **Final Solution**: Direct download `downloadzipfile.cfm?setId={SET_ID}` - Works perfectly
4. **Key Learning**: `setId` parameter is case-sensitive!

### SET_IDs - Common Mistakes
- **WRONG**: `5946d389-0926-4f77-a708-0acb8153b143` (doesn't exist)
- **CORRECT**: `3946d389-0926-4f77-a708-0acb8153b143` (Saxenda)
- **Tip**: Always verify SET_IDs in database before using in workflows

### S3 Bucket Organization
```
glp1-raw-labels/
├── labels/
│   ├── active/          ← Current versions
│   │   └── {SET_ID}/
│   │       └── v{N}/
│   └── archive/         ← Old versions (keep last 5)
│       └── {SET_ID}/
└── logs/                ← Watchdog execution logs
    └── {YYYY-MM-DD}/
```

### GitHub Actions Secrets Required
1. `DATABASE_URL` - PostgreSQL connection string
2. `AWS_ACCESS_KEY_ID` - S3 access key
3. `AWS_SECRET_ACCESS_KEY` - S3 secret key
4. `AWS_REGION` - eu-north-1
5. `S3_BUCKET_NAME` - glp1-raw-labels
6. `SENDGRID_API_KEY` - Optional for email notifications

### Performance Optimizations Applied
1. **Vector Search**: IVFFLAT index with 100 lists
2. **Full-Text Search**: GIN index on tsvector columns
3. **Connection Pooling**: Supabase connection pooler
4. **Batch Processing**: Process embeddings in batches of 50
5. **Caching**: Redis planned for future (not implemented yet)

### Common Troubleshooting

**Issue**: "difflib module not found"  
**Solution**: Remove from requirements.txt (built-in module)

**Issue**: "415 Unsupported Media Type" from DailyMed  
**Solution**: Use correct endpoint with proper case: `downloadzipfile.cfm?setId=`

**Issue**: Duplicate drug entries  
**Solution**: Add unique constraint on set_id, run cleanup script

**Issue**: Slow semantic search  
**Solution**: Create IVFFLAT index on vector columns

**Issue**: Vector dimension mismatch  
**Solution**: Ensure all embeddings use same model (384 dimensions for all-MiniLM-L6-v2)

---

## Future Reference Commands

### Run ETL Pipeline
```bash
cd backend
python scripts/process_new_labels.py --drug MOUNJARO --version 1
```

### Test Watchdog Locally
```bash
cd backend
python scripts/run_watchdog.py --mode manual --set-id 3946d389-0926-4f77-a708-0acb8153b143
```

### Database Queries

**Check enabled drugs**:
```sql
SELECT name, set_id, version, version_check_enabled 
FROM drug_labels 
WHERE version_check_enabled = true;
```

**View version history**:
```sql
SELECT dl.name, dvh.old_version, dvh.new_version, dvh.detected_at
FROM drug_version_history dvh
JOIN drug_labels dl ON dvh.drug_id = dl.id
ORDER BY dvh.detected_at DESC;
```

**Check report generation**:
```sql
SELECT report_type, COUNT(*) as count, MAX(generated_at) as last_generated
FROM report_generation_log
GROUP BY report_type;
```

### AWS S3 Commands

**List labels**:
```bash
aws s3 ls s3://glp1-raw-labels/labels/active/
```

**Download label**:
```bash
aws s3 cp s3://glp1-raw-labels/labels/active/3946d389.../v1/label.zip ./
```

**Upload label**:
```bash
aws s3 cp label.zip s3://glp1-raw-labels/labels/active/{SET_ID}/v{N}/
```

---

## Conclusion

This document preserves institutional knowledge from 45 deleted files. All scripts served important purposes during development but are no longer needed for production operation. The knowledge has been consolidated here for future reference.

**Key Takeaway**: If you need to implement similar functionality in the future, refer to this document for patterns, gotchas, and proven solutions.

**Document Status**: ✅ Complete - Safe to delete original files  
**Last Updated**: January 7, 2026  
**Maintained By**: Development Team
