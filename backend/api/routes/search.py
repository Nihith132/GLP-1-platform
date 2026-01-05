"""
Search Endpoints
Semantic search using vector embeddings
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import select, text
import time

from api.schemas import SearchQuery, SearchResponse, SearchResult, DrugSimilarityResponse, DrugSimilarityResult
from models.database import SectionEmbedding, DrugSection, DrugLabel
from models.db_session import AsyncSessionLocal
from etl.vector_service import VectorService

router = APIRouter()

# Initialize vector service for generating query embeddings
vector_service = VectorService()


@router.post(
    "/semantic",
    response_model=SearchResponse,
    summary="Semantic search",
    description="Search drug labels using semantic similarity (vector search)"
)
async def semantic_search(query_data: SearchQuery):
    """
    Perform semantic search across all drug label sections
    
    Uses vector embeddings to find most relevant sections based on meaning,
    not just keyword matching.
    
    Args:
        query_data: Search query with optional filters
        
    Returns:
        - Ranked list of relevant sections
        - Similarity scores
        - Execution time
    """
    start_time = time.time()
    
    async with AsyncSessionLocal() as session:
        try:
            # Generate embedding for the query
            query_embedding = vector_service.generate_embedding(query_data.query)
            
            # Convert numpy array to string format for pgvector
            # pgvector expects format: '[0.1, 0.2, 0.3, ...]'
            query_vector = str(query_embedding.tolist())
            
            # Build SQL query with cosine similarity
            # Using pgvector's <=> operator for cosine distance
            # Lower distance = higher similarity
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
            search_results = []
            for row in rows:
                search_results.append(SearchResult(
                    drug_id=row.drug_id,
                    drug_name=row.drug_name,
                    generic_name=row.generic_name,
                    manufacturer=row.manufacturer,
                    section_id=row.section_id,
                    section_title=row.section_title,
                    loinc_code=row.section_loinc,
                    chunk_text=row.chunk_text,
                    similarity_score=round(float(row.similarity_score), 4)
                ))
            
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return SearchResponse(
                query=query_data.query,
                total_results=len(search_results),
                results=search_results,
                execution_time_ms=round(execution_time, 2)
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Search failed: {str(e)}"
            )


@router.post(
    "/drug/{drug_id}",
    response_model=SearchResponse,
    summary="Search within drug",
    description="Search within a specific drug's sections"
)
async def search_within_drug(drug_id: int, query_data: SearchQuery):
    """
    Search within a specific drug label only
    
    Args:
        drug_id: Drug label ID to search within
        query_data: Search query
        
    Returns:
        - Relevant sections from this drug only
    """
    start_time = time.time()
    
    async with AsyncSessionLocal() as session:
        try:
            # Verify drug exists
            drug_query = select(DrugLabel).where(DrugLabel.id == drug_id)
            drug_result = await session.execute(drug_query)
            drug = drug_result.scalar_one_or_none()
            
            if not drug:
                raise HTTPException(
                    status_code=404,
                    detail=f"Drug with ID {drug_id} not found"
                )
            
            # Generate query embedding
            query_embedding = vector_service.generate_embedding(query_data.query)
            query_vector = str(query_embedding.tolist())
            
            # Search within this drug only
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
                WHERE dl.id = :drug_id
                ORDER BY se.embedding <=> :query_vector
                LIMIT :top_k
            """)
            
            result = await session.execute(
                sql_query,
                {
                    "query_vector": query_vector,
                    "drug_id": drug_id,
                    "top_k": query_data.top_k
                }
            )
            
            rows = result.fetchall()
            
            search_results = []
            for row in rows:
                search_results.append(SearchResult(
                    drug_id=row.drug_id,
                    drug_name=row.drug_name,
                    generic_name=row.generic_name,
                    manufacturer=row.manufacturer,
                    section_id=row.section_id,
                    section_title=row.section_title,
                    loinc_code=row.section_loinc,
                    chunk_text=row.chunk_text,
                    similarity_score=round(float(row.similarity_score), 4)
                ))
            
            execution_time = (time.time() - start_time) * 1000
            
            return SearchResponse(
                query=query_data.query,
                total_results=len(search_results),
                results=search_results,
                execution_time_ms=round(execution_time, 2)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Search failed: {str(e)}"
            )


@router.post(
    "/section/{loinc_code}",
    response_model=SearchResponse,
    summary="Search specific section type",
    description="Search within a specific section type across all drugs (e.g., all 'Warnings' sections)"
)
async def search_by_section_type(loinc_code: str, query_data: SearchQuery):
    """
    Search within a specific section type across all drugs
    
    Useful for comparing how different drugs handle the same topic
    
    Args:
        loinc_code: LOINC code for section type (e.g., '34067-9' for Indications)
        query_data: Search query
        
    Returns:
        - Relevant sections of this type from all drugs
    """
    start_time = time.time()
    
    async with AsyncSessionLocal() as session:
        try:
            # Generate query embedding
            query_embedding = vector_service.generate_embedding(query_data.query)
            query_vector = str(query_embedding.tolist())
            
            # Search within specific section type
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
                WHERE se.section_loinc = :loinc_code
                  AND dl.is_current_version = true
                ORDER BY se.embedding <=> :query_vector
                LIMIT :top_k
            """)
            
            result = await session.execute(
                sql_query,
                {
                    "query_vector": query_vector,
                    "loinc_code": loinc_code,
                    "top_k": query_data.top_k
                }
            )
            
            rows = result.fetchall()
            
            if not rows:
                raise HTTPException(
                    status_code=404,
                    detail=f"No sections found with LOINC code {loinc_code}"
                )
            
            search_results = []
            for row in rows:
                search_results.append(SearchResult(
                    drug_id=row.drug_id,
                    drug_name=row.drug_name,
                    generic_name=row.generic_name,
                    manufacturer=row.manufacturer,
                    section_id=row.section_id,
                    section_title=row.section_title,
                    loinc_code=row.section_loinc,
                    chunk_text=row.chunk_text,
                    similarity_score=round(float(row.similarity_score), 4)
                ))
            
            execution_time = (time.time() - start_time) * 1000
            
            return SearchResponse(
                query=query_data.query,
                total_results=len(search_results),
                results=search_results,
                execution_time_ms=round(execution_time, 2)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Search failed: {str(e)}"
            )


@router.post(
    "/drug-similarity",
    response_model=DrugSimilarityResponse,
    summary="Drug similarity search",
    description="Find similar drugs based on label embeddings"
)
async def drug_similarity_search(query_data: SearchQuery):
    """
    Find similar drugs based on label embeddings
    
    Args:
        query_data: Search query with optional filters
        
    Returns:
        - Ranked list of similar drugs
        - Similarity scores
        - Execution time
    """
    start_time = time.time()
    
    async with AsyncSessionLocal() as session:
        try:
            # Generate embedding for the query
            query_embedding = vector_service.generate_embedding(query_data.query)
            
            # Convert numpy array to string format for pgvector
            query_vector = str(query_embedding.tolist())
            
            # Build SQL query with cosine similarity
            sql_query = text("""
                SELECT 
                    dl.id as drug_id,
                    dl.drug_name,
                    dl.generic_name,
                    dl.manufacturer,
                    1 - (dl.embedding <=> :query_vector) as similarity_score
                FROM drug_labels dl
                WHERE dl.is_current_version = true
                ORDER BY dl.embedding <=> :query_vector
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
            similarity_results = []
            for row in rows:
                similarity_results.append(DrugSimilarityResult(
                    drug_id=row.drug_id,
                    drug_name=row.drug_name,
                    generic_name=row.generic_name,
                    manufacturer=row.manufacturer,
                    similarity_score=round(float(row.similarity_score), 4)
                ))
            
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return DrugSimilarityResponse(
                query=query_data.query,
                total_results=len(similarity_results),
                results=similarity_results,
                execution_time_ms=round(execution_time, 2)
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Similarity search failed: {str(e)}"
            )


@router.get(
    "/similar-drugs/{drug_id}",
    response_model=DrugSimilarityResponse,
    summary="Find similar drugs",
    description="Find drugs similar to a given drug using label embeddings (dashboard feature)"
)
async def find_similar_drugs(
    drug_id: int,
    top_k: int = 5
):
    """
    Find drugs similar to a given drug based on overall label similarity
    
    Uses label_embedding column (whole-drug embeddings) rather than section_embeddings.
    This is designed for dashboard semantic search: "Show me drugs similar to Ozempic"
    
    Args:
        drug_id: Source drug ID to find similar drugs for
        top_k: Number of similar drugs to return (default 5)
        
    Returns:
        - List of similar drugs ranked by similarity
        - Similarity scores
        - Drug metadata
    """
    start_time = time.time()
    
    async with AsyncSessionLocal() as session:
        try:
            # Get the source drug and its label embedding
            source_drug_query = select(DrugLabel).where(
                DrugLabel.id == drug_id,
                DrugLabel.is_current_version == True
            )
            source_drug_result = await session.execute(source_drug_query)
            source_drug = source_drug_result.scalar_one_or_none()
            
            if not source_drug:
                raise HTTPException(
                    status_code=404,
                    detail=f"Drug with ID {drug_id} not found"
                )
            
            # Check if label_embedding exists (it's a numpy array or None)
            if source_drug.label_embedding is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Drug '{source_drug.name}' does not have a label embedding. Run embedding generation first."
                )
            
            # Find similar drugs using label embeddings
            # Using pgvector cosine similarity on whole-drug embeddings
            sql_query = text("""
                SELECT 
                    dl.id as drug_id,
                    dl.name as drug_name,
                    dl.generic_name,
                    dl.manufacturer,
                    dl.ner_summary,
                    1 - (dl.label_embedding <=> :source_embedding) as similarity_score
                FROM drug_labels dl
                WHERE dl.is_current_version = true
                    AND dl.id != :source_drug_id
                    AND dl.label_embedding IS NOT NULL
                ORDER BY dl.label_embedding <=> :source_embedding
                LIMIT :top_k
            """)
            
            # Convert source embedding (numpy array) to string format for pgvector
            source_embedding_str = str(source_drug.label_embedding.tolist())
            
            result = await session.execute(
                sql_query,
                {
                    "source_embedding": source_embedding_str,
                    "source_drug_id": drug_id,
                    "top_k": top_k
                }
            )
            
            rows = result.fetchall()
            
            if not rows:
                raise HTTPException(
                    status_code=404,
                    detail="No similar drugs found with embeddings"
                )
            
            # Convert to response objects
            similar_drugs = []
            for row in rows:
                similar_drugs.append(DrugSimilarityResult(
                    drug_id=row.drug_id,
                    drug_name=row.drug_name,
                    generic_name=row.generic_name,
                    manufacturer=row.manufacturer,
                    similarity_score=round(float(row.similarity_score), 4),
                    ner_summary=row.ner_summary
                ))
            
            execution_time = (time.time() - start_time) * 1000
            
            return DrugSimilarityResponse(
                source_drug_id=source_drug.id,
                source_drug_name=source_drug.name,
                total_results=len(similar_drugs),
                similar_drugs=similar_drugs,
                execution_time_ms=round(execution_time, 2)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Similarity search failed: {str(e)}"
            )
