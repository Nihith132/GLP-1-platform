"""
Search Endpoints
Dashboard semantic search for drug discovery
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
import time

from api.schemas import SearchQuery, DashboardSearchResponse, DrugSimilarityResult
from models.db_session import AsyncSessionLocal
from etl.vector_service import VectorService

router = APIRouter()

# Initialize vector service for generating query embeddings
vector_service = VectorService()


@router.post(
    "/dashboard",
    response_model=DashboardSearchResponse,
    summary="Dashboard semantic search",
    description="Semantic search for dashboard - returns drugs ranked by relevance to user query"
)
async def dashboard_semantic_search(query_data: SearchQuery):
    """
    Semantic search specifically designed for the dashboard search bar.
    
    Unlike section-level search, this endpoint:
    - Returns DRUGS (not sections)
    - Uses label_embedding column (coarse-grained, whole-drug embeddings)
    - Handles semantic queries like "weekly injection for weight loss"
    - Maps user intent to the most relevant drugs
    
    Perfect for queries like:
    - "medication for weight management"
    - "GLP-1 with cardiovascular benefits"
    - "once-weekly diabetes injection"
    - "semaglutide alternatives"
    
    Args:
        query_data: SearchQuery with user's semantic statement
        
    Returns:
        - Ranked list of drugs matching the semantic query
        - Similarity scores (higher = more relevant)
        - Execution time
        
    Example:
        Query: "medication for chronic weight management"
        Returns: [WEGOVY (0.82), Saxenda (0.76), Zepbound (0.71), ...]
    """
    start_time = time.time()
    
    async with AsyncSessionLocal() as session:
        try:
            # Generate embedding for the user's semantic query
            query_embedding = vector_service.generate_embedding(query_data.query)
            
            # Convert numpy array to string format for pgvector
            query_vector = str(query_embedding.tolist())
            
            # Build SQL query - searches drug_labels.label_embedding column
            # This gives us drug-level semantic similarity
            sql_query = text("""
                SELECT 
                    dl.id as drug_id,
                    dl.name as drug_name,
                    dl.generic_name,
                    dl.manufacturer,
                    dl.ner_summary,
                    1 - (dl.label_embedding <=> :query_vector) as similarity_score
                FROM drug_labels dl
                WHERE dl.is_current_version = true
                  AND dl.label_embedding IS NOT NULL
                ORDER BY dl.label_embedding <=> :query_vector
                LIMIT :top_k
            """)
            
            # Execute query
            result = await session.execute(
                sql_query,
                {
                    "query_vector": query_vector,
                    "top_k": query_data.top_k
                }
            )
            
            rows = result.fetchall()
            
            # Convert to response objects
            drug_results = []
            for row in rows:
                drug_results.append(DrugSimilarityResult(
                    drug_id=row.drug_id,
                    drug_name=row.drug_name,
                    generic_name=row.generic_name,
                    manufacturer=row.manufacturer,
                    similarity_score=round(float(row.similarity_score), 4)
                ))
            
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return DashboardSearchResponse(
                query=query_data.query,
                total_results=len(drug_results),
                results=drug_results,
                execution_time_ms=round(execution_time, 2)
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Dashboard search failed: {str(e)}"
            )
