"""
Chat Endpoints
RAG-based conversational interface for drug label questions
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
import uuid
import os
from groq import Groq

from api.schemas import ChatRequest, ChatResponse, Citation
from models.db_session import AsyncSessionLocal
from etl.vector_service import VectorService

router = APIRouter()

# Initialize vector service
vector_service = VectorService()

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
# Using llama-3.3-70b-versatile (newer model replacing llama-3.1-70b-versatile)
groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def generate_rag_response(query: str, context_sections: list) -> str:
    """
    Generate response using Groq LLM with retrieved context
    
    Uses RAG approach:
    1. Takes user question
    2. Takes retrieved relevant sections from drug labels
    3. Sends both to Groq LLM with specific instructions
    4. Returns grounded, accurate response
    
    Args:
        query: User question
        context_sections: Retrieved relevant sections from vector search
        
    Returns:
        LLM-generated response grounded in the retrieved context
    """
    if not context_sections:
        return "I couldn't find relevant information to answer your question in the drug labels."
    
    # Build context from retrieved sections
    context_text = "\n\n".join([
        f"[Source: {section['drug_name']} - {section['section_title']}]\n{section['chunk_text']}"
        for section in context_sections
    ])
    
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
            model=groq_model,
            temperature=0.3,  # Lower temperature for more factual responses
            max_tokens=1024,
            top_p=0.9
        )
        
        response = chat_completion.choices[0].message.content
        return response
        
    except Exception as e:
        # Fallback to basic response if Groq fails
        return f"Error generating response: {str(e)}\n\nRetrieved context:\n{context_text[:500]}..."


def generate_comparative_response(query: str, drugs_data: dict) -> str:
    """
    Generate comparative analysis using Groq LLM
    
    Compares multiple drugs based on retrieved sections and user question.
    Designed for comparative queries like:
    - "What are the differences between Drug A and Drug B?"
    - "Compare side effects of these medications"
    - "Which drug has better cardiovascular outcomes?"
    
    Args:
        query: User's comparative question
        drugs_data: Dictionary of drug names to their sections
                   {drug_name: {"generic_name": str, "sections": [...]}}
        
    Returns:
        LLM-generated comparative analysis
    """
    if not drugs_data:
        return "I couldn't find relevant information to compare the drugs."
    
    # Build comparative context
    context_parts = []
    for drug_name, data in drugs_data.items():
        drug_context = f"\n{'='*80}\nDRUG: {drug_name} ({data['generic_name']})\n{'='*80}\n"
        
        # Add top sections from this drug
        for i, section in enumerate(data['sections'][:2], 1):  # Top 2 sections per drug
            drug_context += f"\n[Section {i}: {section['section_title']}]\n"
            drug_context += f"{section['chunk_text']}\n"
        
        context_parts.append(drug_context)
    
    context_text = "\n".join(context_parts)
    
    # Create comparative system prompt
    system_prompt = """You are a medical information assistant specialized in comparative analysis of FDA drug labels.

Your role:
- Compare drugs ONLY based on the provided label excerpts
- Identify key similarities and differences
- Organize comparison by relevant categories (indications, dosing, safety, etc.)
- Be precise and cite specific information from each drug
- Highlight clinically significant differences
- Use clear, structured formatting for easy reading

Important:
- DO NOT make up information
- DO NOT use knowledge outside the provided context
- DO NOT provide medical advice or treatment recommendations
- Always mention that prescribing decisions should be made by healthcare providers
- If a particular aspect is not covered in the provided context, state that clearly"""

    # Create comparative user prompt
    user_prompt = f"""Based on the following excerpts from FDA drug labels, please provide a detailed comparison addressing the user's question.

DRUG LABEL EXCERPTS:
{context_text}

USER QUESTION:
{query}

Please provide a structured comparison that:
1. Directly answers the user's comparative question
2. Highlights key similarities across the drugs
3. Identifies important differences between the drugs
4. Organizes information by relevant categories (if applicable)
5. Uses bullet points or tables for clarity

Format your response with clear headings and cite specific drug names."""

    try:
        # Call Groq API for comparative analysis
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
            model=groq_model,
            temperature=0.3,  # Lower temperature for factual comparison
            max_tokens=1500,  # More tokens for detailed comparison
            top_p=0.9
        )
        
        response = chat_completion.choices[0].message.content
        return response
        
    except Exception as e:
        # Fallback to basic comparison if Groq fails
        fallback = f"Error generating comparative analysis: {str(e)}\n\n"
        fallback += f"Comparing {len(drugs_data)} drugs:\n\n"
        
        for drug_name, data in drugs_data.items():
            fallback += f"**{drug_name}** ({data['generic_name']}):\n"
            if data['sections']:
                fallback += f"- {data['sections'][0]['section_title']}: "
                fallback += f"{data['sections'][0]['chunk_text'][:200]}...\n\n"
        
        return fallback


@router.post(
    "/ask",
    response_model=ChatResponse,
    summary="Ask a question",
    description="Ask questions about drug labels using RAG (Retrieval-Augmented Generation)"
)
async def chat_ask(request: ChatRequest):
    """
    Ask a question about drug labels
    
    Uses RAG approach:
    1. Retrieve relevant sections using vector search
    2. Generate response using LLM with retrieved context
    3. Provide citations
    
    Args:
        request: Chat request with question and optional context
        
    Returns:
        - AI-generated response
        - Citations from drug labels
        - Conversation ID for follow-ups
    """
    async with AsyncSessionLocal() as session:
        try:
            # Generate embedding for the question
            query_embedding = vector_service.generate_embedding(request.message)
            query_vector = str(query_embedding.tolist())
            
            # Build retrieval query
            if request.drug_id:
                # Search within specific drug
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
                    WHERE dl.id = :drug_id
                    ORDER BY se.embedding <=> :query_vector
                    LIMIT 5
                """)
                
                result = await session.execute(
                    sql_query,
                    {
                        "query_vector": query_vector,
                        "drug_id": request.drug_id
                    }
                )
            else:
                # Search across all drugs
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
                
                result = await session.execute(
                    sql_query,
                    {"query_vector": query_vector}
                )
            
            rows = result.fetchall()
            
            if not rows:
                raise HTTPException(
                    status_code=404,
                    detail="No relevant information found"
                )
            
            # Prepare context for LLM
            context_sections = [
                {
                    "section_id": row.section_id,
                    "drug_name": row.drug_name,
                    "section_title": row.section_title,
                    "section_loinc": row.section_loinc,
                    "chunk_text": row.chunk_text,
                    "similarity_score": float(row.similarity_score)
                }
                for row in rows
            ]
            
            # Generate response (placeholder for LLM integration)
            response_text = generate_rag_response(request.message, context_sections)
            
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
            
            # Generate conversation ID
            conversation_id = str(uuid.uuid4())
            
            return ChatResponse(
                response=response_text,
                citations=citations,
                conversation_id=conversation_id
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Chat request failed: {str(e)}"
            )


@router.post(
    "/compare",
    response_model=ChatResponse,
    summary="Compare drugs",
    description="Ask comparative questions about multiple drugs"
)
async def chat_compare(request: ChatRequest):
    """
    Ask comparative questions about drugs
    
    Example: "What are the differences in side effects between Ozempic and Victoza?"
    
    Args:
        request: Chat request with comparative question
        
    Returns:
        - Comparative analysis
        - Citations from multiple drugs
    """
    async with AsyncSessionLocal() as session:
        try:
            # Generate embedding
            query_embedding = vector_service.generate_embedding(request.message)
            query_vector = str(query_embedding.tolist())
            
            # Retrieve from multiple drugs
            # Filter by drug_ids if provided to compare only selected drugs
            if request.drug_ids and len(request.drug_ids) > 0:
                # Get top sections from each selected drug (3 per drug)
                sql_query = text("""
                    SELECT 
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
                    WHERE dl.id = ANY(:drug_ids)
                    ORDER BY dl.id, se.embedding <=> :query_vector
                    LIMIT :limit_per_drug
                """)
                
                result = await session.execute(
                    sql_query,
                    {
                        "query_vector": query_vector,
                        "drug_ids": request.drug_ids,  # Pass as list, not tuple
                        "limit_per_drug": len(request.drug_ids) * 3  # 3 sections per drug
                    }
                )
            else:
                # Fallback to all current versions if no drug_ids specified
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
                
                result = await session.execute(
                    sql_query,
                    {"query_vector": query_vector}
                )
            
            rows = result.fetchall()
            
            if not rows:
                raise HTTPException(
                    status_code=404,
                    detail="No relevant information found for comparison"
                )
            
            # Group by drug
            drugs_data = {}
            for row in rows:
                if row.drug_name not in drugs_data:
                    drugs_data[row.drug_name] = {
                        "generic_name": row.generic_name,
                        "sections": []
                    }
                drugs_data[row.drug_name]["sections"].append({
                    "section_id": row.section_id,
                    "drug_name": row.drug_name,
                    "section_title": row.section_title,
                    "section_loinc": row.section_loinc,
                    "chunk_text": row.chunk_text,
                    "similarity_score": float(row.similarity_score)
                })
            
            # Generate comparative response using Groq LLM
            response_text = generate_comparative_response(request.message, drugs_data)
            
            # Create citations from all drugs
            citations = []
            for drug_name, data in drugs_data.items():
                if data['sections']:
                    section = data['sections'][0]
                    citations.append(Citation(
                        section_id=section["section_id"],
                        drug_name=section["drug_name"],
                        section_title=section["section_title"],
                        loinc_code=section["section_loinc"],
                        chunk_text=section["chunk_text"][:300]
                    ))
            
            return ChatResponse(
                response=response_text,
                citations=citations,
                conversation_id=str(uuid.uuid4())
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Comparison failed: {str(e)}"
            )
