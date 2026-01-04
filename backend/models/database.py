"""
SQLAlchemy Database Models
Defines the database schema for drug labels, sections, and vector embeddings
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Index, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from pgvector.sqlalchemy import Vector

Base = declarative_base()


class DrugLabel(Base):
    """
    Main drug label table - stores metadata and references to sections
    """
    __tablename__ = "drug_labels"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # FDA Identifiers (The Link)
    set_id = Column(String(255), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    
    # Drug Information
    name = Column(String(255), nullable=False, index=True)
    generic_name = Column(String(255))
    manufacturer = Column(String(255), nullable=False)
    
    # Status & Versioning
    is_current_version = Column(Boolean, default=True, index=True)
    status = Column(String(50), default="active", index=True)
    
    # Dates
    approval_date = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # NER Summary (JSONB for fast queries)
    ner_summary = Column(JSONB, default={})
    
    # Label-Level Vector Embedding (for dashboard search)
    # Stores a summary embedding of the entire drug label
    label_embedding = Column(Vector(384), nullable=True)
    
    # Source file reference
    source_file = Column(String(500))
    
    # Relationships
    sections = relationship("DrugSection", back_populates="drug_label", cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_drug_set_version', 'set_id', 'version'),
        Index('idx_drug_current', 'is_current_version', 'status'),
    )
    
    def __repr__(self):
        return f"<DrugLabel(name='{self.name}', version={self.version})>"


class DrugSection(Base):
    """
    Individual sections of a drug label (e.g., Dosage, Warnings)
    """
    __tablename__ = "drug_sections"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key to DrugLabel
    drug_label_id = Column(Integer, ForeignKey("drug_labels.id", ondelete="CASCADE"), nullable=False)
    
    # Section Identification
    loinc_code = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    order = Column(Integer, default=0)
    
    # Content
    content = Column(Text, nullable=False)
    
    # NER Data (JSONB for extracted entities)
    ner_entities = Column(JSONB, default=[])
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    drug_label = relationship("DrugLabel", back_populates="sections")
    embeddings = relationship("SectionEmbedding", back_populates="section", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_section_drug_loinc', 'drug_label_id', 'loinc_code'),
    )
    
    def __repr__(self):
        return f"<DrugSection(title='{self.title}', loinc='{self.loinc_code}')>"


class SectionEmbedding(Base):
    """
    Vector embeddings for semantic search using pgvector
    """
    __tablename__ = "section_embeddings"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key to DrugSection
    section_id = Column(Integer, ForeignKey("drug_sections.id", ondelete="CASCADE"), nullable=False)
    
    # Chunk information (sections are split into chunks for embedding)
    chunk_index = Column(Integer, default=0)
    chunk_text = Column(Text, nullable=False)
    
    # Vector embedding (384 dimensions for all-MiniLM-L6-v2)
    embedding = Column(Vector(384), nullable=False)
    
    # Metadata for filtering
    drug_name = Column(String(255), index=True)
    section_loinc = Column(String(50), index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    section = relationship("DrugSection", back_populates="embeddings")
    
    # Indexes for vector similarity search
    __table_args__ = (
        Index('idx_embedding_drug', 'drug_name'),
        Index('idx_embedding_loinc', 'section_loinc'),
    )
    
    def __repr__(self):
        return f"<SectionEmbedding(drug='{self.drug_name}', chunk={self.chunk_index})>"


class ProcessingLog(Base):
    """
    Logs for ETL pipeline processing jobs
    """
    __tablename__ = "processing_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Job information
    job_id = Column(String(255), unique=True, nullable=False)
    drug_name = Column(String(255))
    source_file = Column(String(500))
    
    # Status tracking
    stage = Column(String(50))  # downloading, parsing, ner, vectorizing, complete, failed
    status = Column(String(50))  # running, completed, failed
    progress_percent = Column(Float, default=0.0)
    
    # Error handling
    error_message = Column(Text)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Indexes
    __table_args__ = (
        Index('idx_log_status', 'status', 'started_at'),
    )
    
    def __repr__(self):
        return f"<ProcessingLog(job='{self.job_id}', status='{self.status}')>"
