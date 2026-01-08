-- Migration: Add Reports Tables
-- Purpose: Enable saving and managing analysis/comparison reports
-- Date: 2026-01-06

-- Main reports table
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_type VARCHAR(20) NOT NULL CHECK (report_type IN ('analysis', 'comparison')),
    
    -- User-provided metadata
    title VARCHAR(500) NOT NULL,
    type_category VARCHAR(100) NOT NULL,
    description TEXT,
    tags TEXT[],
    
    -- Auto-captured metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_modified TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Workspace state (stores entire workspace snapshot)
    workspace_state JSONB NOT NULL
);

-- Flagged chat Q&A pairs
CREATE TABLE IF NOT EXISTS report_flagged_chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    citations JSONB,
    flagged_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Flagged comparison summaries/insights
CREATE TABLE IF NOT EXISTS report_flagged_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    summary_type VARCHAR(50) NOT NULL,
    competitor_id INTEGER,
    competitor_name VARCHAR(500),
    content TEXT NOT NULL,
    metadata JSONB,
    flagged_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Text highlights in labels
CREATE TABLE IF NOT EXISTS report_highlights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    drug_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    loinc_code VARCHAR(20) NOT NULL,
    start_char INTEGER NOT NULL,
    end_char INTEGER NOT NULL,
    color VARCHAR(10) NOT NULL CHECK (color IN ('red', 'blue')),
    annotation TEXT,
    highlighted_text TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Quick notes (both citation-linked and standalone)
CREATE TABLE IF NOT EXISTS report_quick_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    
    note_type VARCHAR(20) NOT NULL CHECK (note_type IN ('citation_linked', 'standalone')),
    content TEXT NOT NULL CHECK (length(content) <= 500),
    
    -- Citation data (NULL for standalone notes)
    drug_id INTEGER,
    drug_name VARCHAR(500),
    section_id INTEGER,
    section_title VARCHAR(500),
    loinc_code VARCHAR(20),
    highlighted_text TEXT,
    start_char INTEGER,
    end_char INTEGER,
    highlight_color VARCHAR(10) CHECK (highlight_color IN ('red', 'blue')),
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(report_type);
CREATE INDEX IF NOT EXISTS idx_reports_modified ON reports(last_modified DESC);
CREATE INDEX IF NOT EXISTS idx_reports_tags ON reports USING GIN(tags);

CREATE INDEX IF NOT EXISTS idx_flagged_chats_report ON report_flagged_chats(report_id);
CREATE INDEX IF NOT EXISTS idx_flagged_summaries_report ON report_flagged_summaries(report_id);
CREATE INDEX IF NOT EXISTS idx_highlights_report ON report_highlights(report_id);
CREATE INDEX IF NOT EXISTS idx_quick_notes_report ON report_quick_notes(report_id);
CREATE INDEX IF NOT EXISTS idx_quick_notes_type ON report_quick_notes(report_id, note_type);

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Reports tables created successfully';
END $$;
