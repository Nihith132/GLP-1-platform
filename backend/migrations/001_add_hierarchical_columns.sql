-- Migration: Add hierarchical structure columns to drug_sections
-- Date: 2026-01-08
-- Purpose: Enable parent-child relationships and section numbering for hierarchical display

-- Add new columns to drug_sections table
ALTER TABLE drug_sections
ADD COLUMN IF NOT EXISTS section_number VARCHAR(20),
ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS parent_section_id INTEGER REFERENCES drug_sections(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS content_html TEXT;

-- Add comments for documentation
COMMENT ON COLUMN drug_sections.section_number IS 'Hierarchical section number (e.g., "1", "1.1", "1.2.1")';
COMMENT ON COLUMN drug_sections.level IS 'Depth level in hierarchy (1=main, 2=sub, 3=subsub)';
COMMENT ON COLUMN drug_sections.parent_section_id IS 'Foreign key to parent section for hierarchy';
COMMENT ON COLUMN drug_sections.content_html IS 'HTML-formatted content for rich display';

-- Create index for hierarchical queries
CREATE INDEX IF NOT EXISTS idx_section_parent ON drug_sections(parent_section_id);
CREATE INDEX IF NOT EXISTS idx_section_level ON drug_sections(level);
CREATE INDEX IF NOT EXISTS idx_section_number ON drug_sections(drug_label_id, section_number);

-- Update existing loinc_code to allow NULL for subsections without LOINC codes
ALTER TABLE drug_sections ALTER COLUMN loinc_code DROP NOT NULL;

COMMENT ON TABLE drug_sections IS 'Drug label sections with hierarchical structure support';
