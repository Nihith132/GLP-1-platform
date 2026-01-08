"""
Enhanced Database Schema for Professional Label Analysis
Supports structured navigation + rich content rendering + comparison
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Index, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from models.database import Base
import enum


class SectionImportance(str, enum.Enum):
    """Section importance levels for visual hierarchy"""
    CRITICAL = "critical"      # Red - Safety critical (Contraindications, Boxed Warnings)
    HIGH = "high"              # Orange - Important (Warnings, Dosage, Adverse Reactions)
    MEDIUM = "medium"          # Blue - Standard (Indications, Clinical Pharmacology)
    LOW = "low"                # Gray - Supplementary (How Supplied, Storage)


class SectionType(str, enum.Enum):
    """Section types for categorization"""
    SAFETY = "safety"                    # Safety information
    DOSING = "dosing"                    # Dosage and administration
    EFFICACY = "efficacy"                # Clinical studies, pharmacology
    DESCRIPTION = "description"          # Drug description, composition
    ADMINISTRATIVE = "administrative"    # Storage, packaging, etc.


class DrugSectionEnhanced(Base):
    """
    Enhanced section model for professional label rendering
    Stores both structured metadata AND rich HTML content
    """
    __tablename__ = "drug_sections_enhanced"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key
    drug_label_id = Column(Integer, ForeignKey("drug_labels.id", ondelete="CASCADE"), nullable=False)
    
    # Section Identification
    loinc_code = Column(String(50), nullable=False, index=True)
    section_code = Column(String(100))  # Additional FDA section code
    title = Column(String(500), nullable=False)
    
    # Hierarchy
    parent_section_id = Column(Integer, ForeignKey("drug_sections_enhanced.id"), nullable=True)
    level = Column(Integer, default=1)  # 1=main, 2=subsection, 3=sub-subsection
    order = Column(Integer, default=0)
    section_path = Column(String(200))  # e.g., "1.2.3" for navigation
    
    # Content (Multiple formats for flexibility)
    content_html = Column(Text, nullable=False)  # Rich HTML with styling
    content_text = Column(Text)  # Plain text for search/comparison
    content_xml = Column(Text)  # Original XML fragment for reference
    
    # Metadata for Smart Features
    importance = Column(Enum(SectionImportance), default=SectionImportance.MEDIUM)
    section_type = Column(Enum(SectionType), nullable=True)
    
    # Analysis Data
    word_count = Column(Integer, default=0)
    has_table = Column(Boolean, default=False)
    has_list = Column(Boolean, default=False)
    has_warning_keywords = Column(Boolean, default=False)
    has_dosage_keywords = Column(Boolean, default=False)
    
    # Extracted Entities (JSONB for flexible structure)
    extracted_data = Column(JSONB, default={})  # Dosages, drug names, conditions, etc.
    """
    Example structure:
    {
        "dosages": ["5mg", "10mg", "15mg"],
        "warnings": ["heart failure", "renal impairment"],
        "drug_interactions": ["insulin", "sulfonylurea"],
        "contraindications": ["pregnancy", "thyroid cancer"],
        "key_phrases": ["once daily", "subcutaneous injection"]
    }
    """
    
    # Comparison Support
    comparison_hash = Column(String(64))  # Hash for detecting changes between versions
    semantic_embedding = Column(Text)  # For AI-powered comparison
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    drug_label = relationship("DrugLabel", back_populates="sections_enhanced")
    parent_section = relationship("DrugSectionEnhanced", remote_side=[id], backref="subsections")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_section_enhanced_drug_loinc', 'drug_label_id', 'loinc_code'),
        Index('idx_section_enhanced_importance', 'importance'),
        Index('idx_section_enhanced_type', 'section_type'),
        Index('idx_section_enhanced_order', 'drug_label_id', 'order'),
    )
    
    def __repr__(self):
        return f"<DrugSectionEnhanced(title='{self.title}', importance='{self.importance}')>"
    
    @property
    def is_critical(self):
        """Check if section is safety critical"""
        return self.importance == SectionImportance.CRITICAL
    
    @property
    def hierarchy_level_indicator(self):
        """Visual indicator for hierarchy"""
        return "  " * (self.level - 1)


class LabelComparison(Base):
    """
    Store saved comparisons between drug labels
    Enables users to save and share comparison views
    """
    __tablename__ = "label_comparisons"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Comparison metadata
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Drugs being compared
    drug_label_ids = Column(JSONB, nullable=False)  # Array of drug IDs
    
    # Comparison settings
    comparison_mode = Column(String(50), default="side-by-side")  # side-by-side, inline, table
    highlight_differences = Column(Boolean, default=True)
    sync_scroll = Column(Boolean, default=True)
    
    # Selected sections for comparison
    selected_sections = Column(JSONB, default=[])  # Array of LOINC codes
    
    # User who created
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<LabelComparison(name='{self.name}')>"


class SectionComparisonResult(Base):
    """
    Pre-computed comparison results for performance
    Stores diff analysis between sections
    """
    __tablename__ = "section_comparison_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Sections being compared
    section_1_id = Column(Integer, ForeignKey("drug_sections_enhanced.id"), nullable=False)
    section_2_id = Column(Integer, ForeignKey("drug_sections_enhanced.id"), nullable=False)
    
    # Comparison results
    similarity_score = Column(Integer)  # 0-100
    difference_type = Column(String(50))  # major, minor, identical, not-comparable
    
    # Detailed diff data
    diff_data = Column(JSONB, default={})
    """
    {
        "added_content": [...],
        "removed_content": [...],
        "modified_content": [...],
        "key_differences": [
            {"type": "dosage", "drug1": "5mg", "drug2": "10mg"},
            {"type": "warning", "drug1": "may cause", "drug2": "will cause"}
        ]
    }
    """
    
    # Timestamps
    computed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    section_1 = relationship("DrugSectionEnhanced", foreign_keys=[section_1_id])
    section_2 = relationship("DrugSectionEnhanced", foreign_keys=[section_2_id])
    
    __table_args__ = (
        Index('idx_comparison_sections', 'section_1_id', 'section_2_id'),
    )
