"""
Pydantic Models for API Request/Response
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ==================== Drug Models ====================

class DrugBase(BaseModel):
    """Base drug information"""
    name: str
    generic_name: Optional[str] = None
    manufacturer: str


class DrugDetail(DrugBase):
    """Detailed drug information"""
    id: int
    set_id: str
    version: int
    is_current_version: bool
    status: str
    last_updated: Optional[datetime] = None
    created_at: datetime
    ner_summary: Dict[str, int]
    source_file: str
    
    class Config:
        from_attributes = True


class DrugListResponse(BaseModel):
    """Response for drug list endpoint"""
    total: int
    drugs: List[DrugDetail]


class DrugSection(BaseModel):
    """Drug label section"""
    id: int
    loinc_code: str
    title: str
    order: int
    content: str
    ner_entities: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class DrugWithSections(DrugDetail):
    """Drug with all sections"""
    sections: List[DrugSection]


# ==================== Search Models ====================

class SearchQuery(BaseModel):
    """Search query request"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results to return")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filters")


class SearchResult(BaseModel):
    """Single search result"""
    drug_id: int
    drug_name: str
    generic_name: Optional[str]
    manufacturer: str
    section_id: int
    section_title: str
    loinc_code: str
    chunk_text: str
    similarity_score: float
    
    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    """Search results response"""
    query: str
    total_results: int
    results: List[SearchResult]
    execution_time_ms: float


class DrugSimilarityResult(BaseModel):
    """Similar drug result for dashboard"""
    drug_id: int
    drug_name: str
    generic_name: Optional[str]
    manufacturer: str
    similarity_score: float
    ner_summary: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class DrugSimilarityResponse(BaseModel):
    """Drug similarity search response"""
    source_drug_id: int
    source_drug_name: str
    total_results: int
    similar_drugs: List[DrugSimilarityResult]
    execution_time_ms: float


# ==================== Chat Models ====================

class ChatMessage(BaseModel):
    """Chat message"""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    """Chat request with conversation history"""
    message: str = Field(..., min_length=1, max_length=1000)
    drug_id: Optional[int] = Field(default=None, description="Optional drug context")
    conversation_history: Optional[List[ChatMessage]] = Field(default=None, max_length=20)


class Citation(BaseModel):
    """Citation for chat response"""
    section_id: int
    drug_name: str
    section_title: str
    loinc_code: str
    chunk_text: str


class ChatResponse(BaseModel):
    """Chat response with citations"""
    response: str
    citations: List[Citation]
    conversation_id: Optional[str] = None


# ==================== Analytics Models ====================

class EntityStatistics(BaseModel):
    """Entity type statistics"""
    entity_type: str
    count: int
    percentage: float


class DrugAnalytics(BaseModel):
    """Analytics for a single drug"""
    drug_id: int
    drug_name: str
    total_sections: int
    total_entities: int
    entity_breakdown: List[EntityStatistics]
    most_common_entities: List[Dict[str, Any]]


class PlatformAnalytics(BaseModel):
    """Overall platform analytics"""
    total_drugs: int
    total_sections: int
    total_embeddings: int
    manufacturers: List[Dict[str, int]]
    drug_types: List[Dict[str, int]]
    entity_summary: Dict[str, int]
    last_updated: datetime


class ComparisonRequest(BaseModel):
    """Request to compare multiple drugs"""
    drug_ids: List[int] = Field(..., min_length=2, max_length=5)
    section_type: Optional[str] = Field(default=None, description="LOINC code to compare")


class DrugComparison(BaseModel):
    """Drug comparison data"""
    drug_id: int
    drug_name: str
    generic_name: Optional[str]
    manufacturer: str
    sections: Dict[str, str]  # loinc_code -> content
    entity_counts: Dict[str, int]


class ComparisonResponse(BaseModel):
    """Response for drug comparison"""
    drugs: List[DrugComparison]
    common_entities: Dict[str, int]
    unique_to_each: Dict[int, List[str]]  # drug_id -> unique entity types


# ==================== Error Models ====================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ValidationErrorDetail(BaseModel):
    """Validation error detail"""
    field: str
    message: str


class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    error: str = "Validation Error"
    details: List[ValidationErrorDetail]
