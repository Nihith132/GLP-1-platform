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
    content_html: Optional[str] = None
    section_number: Optional[str] = None
    level: Optional[int] = None
    parent_section_id: Optional[int] = None
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


class DashboardSearchResponse(BaseModel):
    """Dashboard semantic search response - returns drugs, not sections"""
    query: str
    total_results: int
    results: List[DrugSimilarityResult]
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
    drug_ids: Optional[List[int]] = Field(default=None, description="Optional list of drug IDs to compare")
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
    total_manufacturers: int
    total_drug_types: int
    active_labels: int
    manufacturers: List[Dict[str, Any]]
    drug_types: List[Dict[str, Any]]
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


# ==================== Comparison Workspace Models ====================

class CompareLoadRequest(BaseModel):
    """Request to load drugs for comparison"""
    source_drug_id: int = Field(..., description="Source drug (your product)")
    competitor_drug_ids: List[int] = Field(..., min_length=1, max_length=5, description="Competitor drugs")


class CompareLoadResponse(BaseModel):
    """Response with loaded drugs for comparison"""
    source_drug: DrugWithSections
    competitors: List[DrugWithSections]


class LexicalDiffRequest(BaseModel):
    """Request for lexical (text-based) differencing"""
    source_drug_id: int
    competitor_drug_id: int
    section_loinc: Optional[str] = Field(default=None, description="Specific section to compare")


class TextChange(BaseModel):
    """Individual text change (addition/deletion)"""
    change_type: str = Field(..., pattern="^(addition|deletion)$")
    text: str
    start_char: int
    end_char: int


class LexicalDiffResult(BaseModel):
    """Lexical diff result for a section"""
    section_loinc: str
    section_title: str
    source_text: str
    competitor_text: str
    additions: List[TextChange]  # Green in competitor (new text)
    deletions: List[TextChange]  # Red in source (removed text)


class LexicalDiffResponse(BaseModel):
    """Response with lexical differences"""
    source_drug_name: str
    competitor_drug_name: str
    diffs: List[LexicalDiffResult]


class SemanticDiffRequest(BaseModel):
    """Request for semantic (meaning-based) differencing"""
    source_drug_id: int
    competitor_drug_id: int
    section_loinc: Optional[str] = Field(default=None, description="Specific section to compare")
    similarity_threshold: float = Field(default=0.65, ge=0.0, le=1.0)


class SemanticSegment(BaseModel):
    """Semantic segment with highlighting info"""
    text: str
    start_char: int
    end_char: int
    highlight_color: str = Field(..., pattern="^(green|yellow|red|blue)$")
    underline_style: Optional[str] = Field(default=None, pattern="^(wavy)$")
    diff_type: str = Field(..., pattern="^(high_similarity|partial_match|unique_to_source|omission|conflict)$")


class SemanticMatch(BaseModel):
    """Semantic match between source and competitor segments"""
    source_segment: Optional[SemanticSegment] = None
    competitor_segment: Optional[SemanticSegment] = None
    similarity_score: Optional[float] = None
    explanation: str


class SemanticDiffResult(BaseModel):
    """Semantic diff result for a section"""
    section_loinc: str
    section_title: str
    matches: List[SemanticMatch]


class SemanticDiffSummary(BaseModel):
    """Summary statistics for semantic diff"""
    total_matches: int
    high_similarity: int
    partial_matches: int
    unique_to_source: int
    omissions: int
    conflicts: int


class SemanticDiffResponse(BaseModel):
    """Response with semantic differences"""
    source_drug_name: str
    competitor_drug_name: str
    diffs: List[SemanticDiffResult]
    summary: SemanticDiffSummary


class ExplainSegmentRequest(BaseModel):
    """Request to explain a specific segment difference"""
    source_drug_id: int
    competitor_drug_id: int
    section_loinc: str
    source_text: Optional[str] = None
    competitor_text: Optional[str] = None


class ExplainSegmentResponse(BaseModel):
    """Detailed explanation of segment difference"""
    explanation: str
    clinical_significance: str
    marketing_implication: str
    action_items: List[str]


class SummarizeDiffsRequest(BaseModel):
    """Request to summarize all differences"""
    source_drug_id: int
    competitor_drug_id: int


class DiffCategorySummary(BaseModel):
    """Summary for a category of differences"""
    category: str  # e.g., "Indications", "Dosing", "Safety"
    advantages: List[str]  # Green - unique to source
    gaps: List[str]  # Blue - omissions
    conflicts: List[str]  # Red - contradictions


class SummarizeDiffsResponse(BaseModel):
    """Summary of all differences"""
    source_drug_name: str
    competitor_drug_name: str
    executive_summary: str
    category_summaries: List[DiffCategorySummary]
    overall_statistics: SemanticDiffSummary


class CompareSearchRequest(BaseModel):
    """Search within comparison context"""
    source_drug_id: int
    competitor_drug_ids: List[int] = Field(..., min_length=1, max_length=5)
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=10, ge=1, le=50)


class CompareSearchResult(BaseModel):
    """Search result in comparison context"""
    drug_id: int
    drug_name: str
    drug_type: str = Field(..., pattern="^(source|competitor)$")
    section_id: int
    section_title: str
    loinc_code: str
    chunk_text: str
    similarity_score: float


class CompareSearchResponse(BaseModel):
    """Response for comparison search"""
    query: str
    results: List[CompareSearchResult]


# ==================== Reports Models ====================

class ReportMetadata(BaseModel):
    """User-provided report metadata"""
    title: str = Field(..., min_length=1, max_length=500)
    type_category: str = Field(..., pattern="^(competitive_analysis|safety_review|efficacy_study|regulatory_prep|general_analysis)$")
    tags: List[str] = Field(default=[], max_length=10)
    description: Optional[str] = Field(default=None, max_length=2000)


class WorkspaceStateAnalysis(BaseModel):
    """Workspace state for analysis report"""
    drug_id: int
    drug_name: str
    active_section: Optional[str] = None  # LOINC code
    scroll_position: Optional[int] = 0


class WorkspaceStateComparison(BaseModel):
    """Workspace state for comparison report"""
    source_drug_id: int
    source_drug_name: str
    competitor_drug_ids: List[int]
    competitor_drug_names: List[str]
    active_comparison: Optional[Dict[str, Any]] = None
    scroll_position: Optional[int] = 0


class CreateReportRequest(BaseModel):
    """Request to create new report"""
    report_type: str = Field(..., pattern="^(analysis|comparison)$")
    metadata: ReportMetadata
    workspace_state: Dict[str, Any]


class ReportSummary(BaseModel):
    """Summary info for report list"""
    id: str
    report_type: str
    title: str
    type_category: str
    tags: List[str]
    created_at: datetime
    last_modified: datetime
    drug_names: List[str]


class ReportDetail(BaseModel):
    """Full report with all components"""
    id: str
    report_type: str
    metadata: ReportMetadata
    workspace_state: Dict[str, Any]
    created_at: datetime
    last_modified: datetime
    flagged_chats: List[Dict[str, Any]]
    flagged_summaries: List[Dict[str, Any]]
    highlights: List[Dict[str, Any]]
    quick_notes: List[Dict[str, Any]]


class FlagChatRequest(BaseModel):
    """Flag a chat Q&A pair"""
    question: str = Field(..., max_length=1000)
    answer: str
    citations: List[Citation]


class FlagSummaryRequest(BaseModel):
    """Flag a comparison summary/insight"""
    summary_type: str = Field(..., pattern="^(executive_summary|segment_explanation)$")
    competitor_id: Optional[int] = None
    competitor_name: Optional[str] = None
    content: str
    metadata: Optional[Dict[str, Any]] = None


class CreateHighlightRequest(BaseModel):
    """Create text highlight in label"""
    drug_id: int
    section_id: int
    loinc_code: str
    start_char: int
    end_char: int
    color: str = Field(..., pattern="^(red|blue)$")
    annotation: Optional[str] = Field(default=None, max_length=500)
    highlighted_text: str


class CreateQuickNoteRequest(BaseModel):
    """Create quick note (citation-linked or standalone)"""
    note_type: str = Field(..., pattern="^(citation_linked|standalone)$")
    content: str = Field(..., min_length=1, max_length=500)
    drug_id: Optional[int] = None
    drug_name: Optional[str] = None
    section_id: Optional[int] = None
    section_title: Optional[str] = None
    loinc_code: Optional[str] = None
    highlighted_text: Optional[str] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    highlight_color: Optional[str] = Field(default=None, pattern="^(red|blue)$")


class UpdateQuickNoteRequest(BaseModel):
    """Update note content"""
    content: str = Field(..., min_length=1, max_length=500)


class QuickNoteDetail(BaseModel):
    """Quick note with all fields"""
    id: str
    note_type: str
    content: str
    created_at: datetime
    updated_at: datetime
    citation: Optional[Dict[str, Any]] = None


class NavigateToCitationResponse(BaseModel):
    """Navigation data for citation"""
    drug_id: int
    drug_name: str
    section_id: int
    section_title: str
    loinc_code: str
    start_char: int
    end_char: int
    highlight_color: str


class ExportReportRequest(BaseModel):
    """Export report as PDF/Word"""
    format: str = Field(..., pattern="^(pdf|docx)$")
    include_metadata: bool = True
    include_notes: bool = True
    include_highlights: bool = True


class ShareReportRequest(BaseModel):
    """Share report with colleagues"""
    recipient_emails: List[str]
    message: Optional[str] = None


# ==================== Version Check Models ====================

class VersionCheckResult(BaseModel):
    """Result from a version check"""
    drug_id: int
    drug_name: str
    current_version: int
    new_version: Optional[int] = None
    has_update: bool
    changes: Optional[str] = None
    checked_at: datetime
    
    class Config:
        from_attributes = True


class VersionHistory(BaseModel):
    """Version history record"""
    id: int
    drug_id: int
    drug_name: str
    old_version: int
    new_version: int
    changes_detected: Optional[str] = None
    checked_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
