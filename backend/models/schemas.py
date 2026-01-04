"""
Pydantic Models - The Data Contract
Defines the shape and validation rules for all data flowing through the system
"""

from pydantic import BaseModel, Field, UUID4, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ===== Enums =====

class DrugStatus(str, Enum):
    """Status of drug label in the system"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    PROCESSING = "processing"


class SectionType(str, Enum):
    """Standard FDA label sections (LOINC codes)"""
    INDICATIONS = "34067-9"  # Indications and Usage
    DOSAGE = "34068-7"  # Dosage and Administration
    DOSAGE_FORMS = "42073-5"  # Dosage Forms and Strengths
    CONTRAINDICATIONS = "34070-3"  # Contraindications
    WARNINGS = "43685-7"  # Warnings and Precautions
    ADVERSE_REACTIONS = "34084-4"  # Adverse Reactions
    DRUG_INTERACTIONS = "34073-7"  # Drug Interactions
    USE_IN_SPECIFIC = "43684-0"  # Use in Specific Populations
    CLINICAL_PHARMACOLOGY = "34090-1"  # Clinical Pharmacology
    CLINICAL_STUDIES = "34092-7"  # Clinical Studies
    HOW_SUPPLIED = "34069-5"  # How Supplied/Storage
    PATIENT_INFO = "34076-0"  # Patient Counseling Information


class EntityLabel(str, Enum):
    """Named Entity Recognition labels for drug information"""
    STRENGTH = "strength"  # e.g., "0.5 mg", "1 mg"
    ROUTE = "route"  # e.g., "subcutaneous", "oral"
    FREQUENCY = "frequency"  # e.g., "once weekly", "daily"
    SIDE_EFFECT = "side_effect"  # e.g., "nausea", "vomiting"
    CONTRAINDICATION = "contraindication"
    DRUG_NAME = "drug_name"
    CONDITION = "condition"  # e.g., "type 2 diabetes"


# ===== Core Data Models =====

class NEREntity(BaseModel):
    """Named Entity extracted from label text"""
    label: EntityLabel = Field(..., description="Type of entity")
    text: str = Field(..., description="Actual text extracted")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score")
    start_char: Optional[int] = Field(None, description="Start position in text")
    end_char: Optional[int] = Field(None, description="End position in text")
    
    class Config:
        json_schema_extra = {
            "example": {
                "label": "strength",
                "text": "0.5 mg",
                "confidence": 0.95,
                "start_char": 125,
                "end_char": 131
            }
        }


class DrugSection(BaseModel):
    """A single section from the drug label"""
    loinc_code: str = Field(..., description="LOINC code identifying the section")
    title: str = Field(..., description="Human-readable section title")
    content: str = Field(..., description="Clean text content (HTML stripped)")
    order: int = Field(..., description="Display order in label")
    entities: List[NEREntity] = Field(default_factory=list, description="Extracted entities from this section")
    
    @field_validator('content')
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "loinc_code": "34068-7",
                "title": "Dosage and Administration",
                "content": "Inject 0.5 mg subcutaneously once weekly...",
                "order": 2,
                "entities": []
            }
        }


class DrugMetadata(BaseModel):
    """Core metadata for a drug label"""
    set_id: str = Field(..., description="FDA SetID (unique identifier)")
    version: int = Field(..., ge=1, description="Label version number")
    name: str = Field(..., description="Drug brand name")
    generic_name: Optional[str] = Field(None, description="Generic/chemical name")
    manufacturer: str = Field(..., description="Manufacturing company")
    approval_date: Optional[datetime] = Field(None, description="FDA approval date")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    status: DrugStatus = Field(default=DrugStatus.ACTIVE)
    is_current_version: bool = Field(default=True, description="Is this the latest version?")
    
    class Config:
        json_schema_extra = {
            "example": {
                "set_id": "1b4d3d6f-c78e-4e5f-a8b7-1234567890ab",
                "version": 3,
                "name": "Ozempic",
                "generic_name": "semaglutide",
                "manufacturer": "Novo Nordisk",
                "approval_date": "2017-12-05T00:00:00Z",
                "status": "active",
                "is_current_version": True
            }
        }


class DrugLabel(BaseModel):
    """Complete drug label - The Master Object"""
    metadata: DrugMetadata
    sections: List[DrugSection] = Field(..., description="All sections of the label")
    ner_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Entity counts for quick stats: {'strength': 5, 'side_effect': 23}"
    )
    
    @property
    def total_entities(self) -> int:
        """Total number of entities across all sections"""
        return sum(len(section.entities) for section in self.sections)
    
    def get_section_by_loinc(self, loinc_code: str) -> Optional[DrugSection]:
        """Retrieve a specific section by its LOINC code"""
        return next((s for s in self.sections if s.loinc_code == loinc_code), None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "set_id": "abc-123",
                    "version": 1,
                    "name": "Ozempic",
                    "manufacturer": "Novo Nordisk",
                    "status": "active"
                },
                "sections": [],
                "ner_summary": {"strength": 5, "side_effect": 23}
            }
        }


# ===== API Request/Response Models =====

class DrugListResponse(BaseModel):
    """Response for GET /drugs endpoint"""
    drugs: List[DrugMetadata]
    total: int
    
    
class DrugDetailResponse(BaseModel):
    """Response for GET /drugs/{id} endpoint"""
    label: DrugLabel


class ChatMessage(BaseModel):
    """A single message in the chat"""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Request body for POST /chat endpoint"""
    query: str = Field(..., min_length=1, max_length=1000)
    drug_id: Optional[str] = Field(None, description="Filter search to specific drug")
    conversation_history: List[ChatMessage] = Field(default_factory=list, max_length=10)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Does Ozempic cause thyroid tumors?",
                "drug_id": "abc-123",
                "conversation_history": []
            }
        }


class Citation(BaseModel):
    """Source citation for RAG response"""
    drug_name: str
    section_title: str
    text_snippet: str
    loinc_code: str
    confidence_score: float


class ChatResponse(BaseModel):
    """Response for POST /chat endpoint"""
    answer: str
    citations: List[Citation]
    processing_time_ms: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Yes, Ozempic has a boxed warning...",
                "citations": [],
                "processing_time_ms": 245.3
            }
        }


# ===== Comparison Models =====

class ComparisonRequest(BaseModel):
    """Request for comparing two drugs"""
    drug_id_a: str
    drug_id_b: str
    comparison_type: str = Field(..., pattern="^(lexical|semantic)$")


class TextDiff(BaseModel):
    """Represents a difference in text comparison"""
    type: str = Field(..., pattern="^(added|removed|unchanged)$")
    text: str
    position: int


class SectionComparison(BaseModel):
    """Comparison result for a single section"""
    loinc_code: str
    title: str
    drug_a_text: str
    drug_b_text: str
    similarity_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    diffs: Optional[List[TextDiff]] = None
    semantic_category: Optional[str] = Field(None, pattern="^(match|partial|unique)$")


class ComparisonResponse(BaseModel):
    """Response for comparison endpoint"""
    drug_a: DrugMetadata
    drug_b: DrugMetadata
    section_comparisons: List[SectionComparison]
    overall_similarity: float


# ===== ETL & Processing Models =====

class ProcessingStatus(BaseModel):
    """Status of a processing job"""
    job_id: str
    drug_name: str
    stage: str  # "downloading", "parsing", "ner", "vectorizing", "complete"
    progress_percent: float
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
