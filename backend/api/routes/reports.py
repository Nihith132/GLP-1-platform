"""
Reports Management Endpoints
For saving, loading, and managing analysis/comparison reports
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from typing import List, Optional
import uuid
from datetime import datetime
import json

from api.schemas import (
    CreateReportRequest, ReportSummary, ReportDetail,
    FlagChatRequest, FlagSummaryRequest,
    CreateHighlightRequest, CreateQuickNoteRequest, UpdateQuickNoteRequest,
    QuickNoteDetail, NavigateToCitationResponse,
    ExportReportRequest, ShareReportRequest,
    ReportMetadata
)
from models.db_session import AsyncSessionLocal

router = APIRouter()


# ==================== Core CRUD Operations ====================

@router.post("/create", response_model=ReportDetail, summary="Create new report")
async def create_report(request: CreateReportRequest):
    """
    Create a new report
    
    Saves workspace state, metadata, and returns report ID
    """
    async with AsyncSessionLocal() as session:
        try:
            report_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            # Insert report
            insert_query = text("""
                INSERT INTO reports (
                    id, report_type, title, type_category, description, tags,
                    created_at, last_modified, workspace_state
                )
                VALUES (
                    :id, :report_type, :title, :type_category, :description, :tags,
                    :created_at, :last_modified, :workspace_state
                )
                RETURNING *
            """)
            
            result = await session.execute(
                insert_query,
                {
                    "id": report_id,
                    "report_type": request.report_type,
                    "title": request.metadata.title,
                    "type_category": request.metadata.type_category,
                    "description": request.metadata.description,
                    "tags": request.metadata.tags,
                    "created_at": now,
                    "last_modified": now,
                    "workspace_state": json.dumps(request.workspace_state) if isinstance(request.workspace_state, dict) else request.workspace_state
                }
            )
            
            await session.commit()
            
            row = result.fetchone()
            
            # Return full report detail (empty components initially)
            workspace_data = row.workspace_state if isinstance(row.workspace_state, dict) else json.loads(row.workspace_state)
            
            return ReportDetail(
                id=str(row.id),
                report_type=row.report_type,
                metadata=ReportMetadata(
                    title=row.title,
                    type_category=row.type_category,
                    tags=row.tags or [],
                    description=row.description
                ),
                workspace_state=workspace_data,
                created_at=row.created_at,
                last_modified=row.last_modified,
                flagged_chats=[],
                flagged_summaries=[],
                highlights=[],
                quick_notes=[]
            )
            
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create report: {str(e)}")


@router.get("/", response_model=List[ReportSummary], summary="List all reports")
async def list_reports(
    skip: int = 0,
    limit: int = 50,
    report_type: Optional[str] = None
):
    """
    List all reports with pagination
    
    Optional filtering by report_type
    """
    async with AsyncSessionLocal() as session:
        try:
            # Build query with optional filter
            if report_type:
                query = text("""
                    SELECT * FROM reports
                    WHERE report_type = :report_type
                    ORDER BY last_modified DESC
                    LIMIT :limit OFFSET :skip
                """)
                result = await session.execute(query, {
                    "report_type": report_type,
                    "limit": limit,
                    "skip": skip
                })
            else:
                query = text("""
                    SELECT * FROM reports
                    ORDER BY last_modified DESC
                    LIMIT :limit OFFSET :skip
                """)
                result = await session.execute(query, {"limit": limit, "skip": skip})
            
            rows = result.fetchall()
            
            # Extract drug names from workspace_state
            summaries = []
            for row in rows:
                workspace_state = row.workspace_state if isinstance(row.workspace_state, dict) else json.loads(row.workspace_state)
                
                # Extract drug names based on report type
                if row.report_type == 'analysis':
                    drug_names = [workspace_state.get('drug_name', 'Unknown')]
                else:  # comparison
                    drug_names = [workspace_state.get('source_drug_name', 'Unknown')]
                    drug_names.extend(workspace_state.get('competitor_drug_names', []))
                
                summaries.append(ReportSummary(
                    id=str(row.id),
                    report_type=row.report_type,
                    title=row.title,
                    type_category=row.type_category,
                    tags=row.tags or [],
                    created_at=row.created_at,
                    last_modified=row.last_modified,
                    drug_names=drug_names
                ))
            
            return summaries
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list reports: {str(e)}")


@router.get("/{report_id}", response_model=ReportDetail, summary="Get specific report")
async def get_report(report_id: str):
    """
    Get full report with all components
    
    Returns workspace state and all flagged items, highlights, and notes
    """
    async with AsyncSessionLocal() as session:
        try:
            # Get main report
            report_query = text("SELECT * FROM reports WHERE id = :report_id")
            report_result = await session.execute(report_query, {"report_id": report_id})
            report_row = report_result.fetchone()
            
            if not report_row:
                raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
            
            # Get flagged chats
            chats_query = text("SELECT * FROM report_flagged_chats WHERE report_id = :report_id ORDER BY flagged_at")
            chats_result = await session.execute(chats_query, {"report_id": report_id})
            flagged_chats = [dict(row._mapping) for row in chats_result.fetchall()]
            
            # Get flagged summaries
            summaries_query = text("SELECT * FROM report_flagged_summaries WHERE report_id = :report_id ORDER BY flagged_at")
            summaries_result = await session.execute(summaries_query, {"report_id": report_id})
            flagged_summaries = [dict(row._mapping) for row in summaries_result.fetchall()]
            
            # Get highlights
            highlights_query = text("SELECT * FROM report_highlights WHERE report_id = :report_id ORDER BY created_at")
            highlights_result = await session.execute(highlights_query, {"report_id": report_id})
            highlights = [dict(row._mapping) for row in highlights_result.fetchall()]
            
            # Get quick notes
            notes_query = text("SELECT * FROM report_quick_notes WHERE report_id = :report_id ORDER BY created_at")
            notes_result = await session.execute(notes_query, {"report_id": report_id})
            quick_notes = [dict(row._mapping) for row in notes_result.fetchall()]
            
            # Convert UUID and datetime to strings for JSON serialization
            for item_list in [flagged_chats, flagged_summaries, highlights, quick_notes]:
                for item in item_list:
                    item['id'] = str(item['id'])
                    item['report_id'] = str(item['report_id'])
                    for key, value in item.items():
                        if isinstance(value, datetime):
                            item[key] = value.isoformat()
            
            return ReportDetail(
                id=str(report_row.id),
                report_type=report_row.report_type,
                metadata=ReportMetadata(
                    title=report_row.title,
                    type_category=report_row.type_category,
                    tags=report_row.tags or [],
                    description=report_row.description
                ),
                workspace_state=report_row.workspace_state if isinstance(report_row.workspace_state, dict) else json.loads(report_row.workspace_state),
                created_at=report_row.created_at,
                last_modified=report_row.last_modified,
                flagged_chats=flagged_chats,
                flagged_summaries=flagged_summaries,
                highlights=highlights,
                quick_notes=quick_notes
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")


@router.put("/{report_id}/metadata", summary="Update report metadata")
async def update_report_metadata(report_id: str, metadata: ReportMetadata):
    """
    Update report title, description, tags, or type
    
    Also updates last_modified timestamp
    """
    async with AsyncSessionLocal() as session:
        try:
            update_query = text("""
                UPDATE reports
                SET title = :title,
                    type_category = :type_category,
                    description = :description,
                    tags = :tags,
                    last_modified = :last_modified
                WHERE id = :report_id
                RETURNING *
            """)
            
            result = await session.execute(
                update_query,
                {
                    "report_id": report_id,
                    "title": metadata.title,
                    "type_category": metadata.type_category,
                    "description": metadata.description,
                    "tags": metadata.tags,
                    "last_modified": datetime.utcnow()
                }
            )
            
            await session.commit()
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
            
            return {"message": "Report metadata updated successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update metadata: {str(e)}")


@router.delete("/{report_id}", summary="Delete report")
async def delete_report(report_id: str):
    """
    Delete report and all associated data
    
    CASCADE deletes all flagged items, highlights, and notes
    """
    async with AsyncSessionLocal() as session:
        try:
            delete_query = text("DELETE FROM reports WHERE id = :report_id")
            result = await session.execute(delete_query, {"report_id": report_id})
            await session.commit()
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
            
            return {"message": "Report deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete report: {str(e)}")


# ==================== Flagged Chats ====================

@router.post("/{report_id}/flag-chat", summary="Flag chat Q&A")
async def flag_chat(report_id: str, request: FlagChatRequest):
    """
    Add flagged chat Q&A pair to report
    """
    async with AsyncSessionLocal() as session:
        try:
            chat_id = str(uuid.uuid4())
            
            insert_query = text("""
                INSERT INTO report_flagged_chats (
                    id, report_id, question, answer, citations, flagged_at
                )
                VALUES (
                    :id, :report_id, :question, :answer, :citations, :flagged_at
                )
                RETURNING *
            """)
            
            result = await session.execute(
                insert_query,
                {
                    "id": chat_id,
                    "report_id": report_id,
                    "question": request.question,
                    "answer": request.answer,
                    "citations": json.dumps([c.dict() for c in request.citations]),
                    "flagged_at": datetime.utcnow()
                }
            )
            
            # Update report last_modified
            await session.execute(
                text("UPDATE reports SET last_modified = :now WHERE id = :report_id"),
                {"now": datetime.utcnow(), "report_id": report_id}
            )
            
            await session.commit()
            
            row = result.fetchone()
            return {
                "id": str(row.id),
                "message": "Chat flagged successfully"
            }
            
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to flag chat: {str(e)}")


@router.delete("/{report_id}/flag-chat/{chat_id}", summary="Unflag chat")
async def unflag_chat(report_id: str, chat_id: str):
    """
    Remove flagged chat from report
    """
    async with AsyncSessionLocal() as session:
        try:
            delete_query = text("""
                DELETE FROM report_flagged_chats
                WHERE id = :chat_id AND report_id = :report_id
            """)
            result = await session.execute(delete_query, {
                "chat_id": chat_id,
                "report_id": report_id
            })
            
            # Update report last_modified
            await session.execute(
                text("UPDATE reports SET last_modified = :now WHERE id = :report_id"),
                {"now": datetime.utcnow(), "report_id": report_id}
            )
            
            await session.commit()
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Flagged chat not found")
            
            return {"message": "Chat unflagged successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to unflag chat: {str(e)}")


# ==================== Flagged Summaries ====================

@router.post("/{report_id}/flag-summary", summary="Flag summary/insight")
async def flag_summary(report_id: str, request: FlagSummaryRequest):
    """
    Add flagged comparison summary/insight to report
    """
    async with AsyncSessionLocal() as session:
        try:
            summary_id = str(uuid.uuid4())
            
            insert_query = text("""
                INSERT INTO report_flagged_summaries (
                    id, report_id, summary_type, competitor_id, competitor_name,
                    content, metadata, flagged_at
                )
                VALUES (
                    :id, :report_id, :summary_type, :competitor_id, :competitor_name,
                    :content, :metadata, :flagged_at
                )
                RETURNING *
            """)
            
            result = await session.execute(
                insert_query,
                {
                    "id": summary_id,
                    "report_id": report_id,
                    "summary_type": request.summary_type,
                    "competitor_id": request.competitor_id,
                    "competitor_name": request.competitor_name,
                    "content": request.content,
                    "metadata": json.dumps(request.metadata) if request.metadata else None,
                    "flagged_at": datetime.utcnow()
                }
            )
            
            # Update report last_modified
            await session.execute(
                text("UPDATE reports SET last_modified = :now WHERE id = :report_id"),
                {"now": datetime.utcnow(), "report_id": report_id}
            )
            
            await session.commit()
            
            row = result.fetchone()
            return {
                "id": str(row.id),
                "message": "Summary flagged successfully"
            }
            
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to flag summary: {str(e)}")


@router.delete("/{report_id}/flag-summary/{summary_id}", summary="Unflag summary")
async def unflag_summary(report_id: str, summary_id: str):
    """
    Remove flagged summary from report
    """
    async with AsyncSessionLocal() as session:
        try:
            delete_query = text("""
                DELETE FROM report_flagged_summaries
                WHERE id = :summary_id AND report_id = :report_id
            """)
            result = await session.execute(delete_query, {
                "summary_id": summary_id,
                "report_id": report_id
            })
            
            # Update report last_modified
            await session.execute(
                text("UPDATE reports SET last_modified = :now WHERE id = :report_id"),
                {"now": datetime.utcnow(), "report_id": report_id}
            )
            
            await session.commit()
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Flagged summary not found")
            
            return {"message": "Summary unflagged successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to unflag summary: {str(e)}")


# ==================== Highlights ====================

@router.post("/{report_id}/highlights", summary="Create highlight")
async def create_highlight(report_id: str, request: CreateHighlightRequest):
    """
    Create text highlight in label
    """
    async with AsyncSessionLocal() as session:
        try:
            highlight_id = str(uuid.uuid4())
            
            insert_query = text("""
                INSERT INTO report_highlights (
                    id, report_id, drug_id, section_id, loinc_code,
                    start_char, end_char, color, annotation, highlighted_text, created_at
                )
                VALUES (
                    :id, :report_id, :drug_id, :section_id, :loinc_code,
                    :start_char, :end_char, :color, :annotation, :highlighted_text, :created_at
                )
                RETURNING *
            """)
            
            result = await session.execute(
                insert_query,
                {
                    "id": highlight_id,
                    "report_id": report_id,
                    "drug_id": request.drug_id,
                    "section_id": request.section_id,
                    "loinc_code": request.loinc_code,
                    "start_char": request.start_char,
                    "end_char": request.end_char,
                    "color": request.color,
                    "annotation": request.annotation,
                    "highlighted_text": request.highlighted_text,
                    "created_at": datetime.utcnow()
                }
            )
            
            # Update report last_modified
            await session.execute(
                text("UPDATE reports SET last_modified = :now WHERE id = :report_id"),
                {"now": datetime.utcnow(), "report_id": report_id}
            )
            
            await session.commit()
            
            row = result.fetchone()
            return {
                "id": str(row.id),
                "message": "Highlight created successfully"
            }
            
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create highlight: {str(e)}")


@router.put("/{report_id}/highlights/{highlight_id}", summary="Update highlight annotation")
async def update_highlight_annotation(report_id: str, highlight_id: str, annotation: str):
    """
    Update highlight annotation text
    """
    async with AsyncSessionLocal() as session:
        try:
            update_query = text("""
                UPDATE report_highlights
                SET annotation = :annotation
                WHERE id = :highlight_id AND report_id = :report_id
                RETURNING *
            """)
            
            result = await session.execute(update_query, {
                "annotation": annotation,
                "highlight_id": highlight_id,
                "report_id": report_id
            })
            
            # Update report last_modified
            await session.execute(
                text("UPDATE reports SET last_modified = :now WHERE id = :report_id"),
                {"now": datetime.utcnow(), "report_id": report_id}
            )
            
            await session.commit()
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Highlight not found")
            
            return {"message": "Highlight annotation updated successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update highlight: {str(e)}")


@router.delete("/{report_id}/highlights/{highlight_id}", summary="Delete highlight")
async def delete_highlight(report_id: str, highlight_id: str):
    """
    Remove highlight from report
    """
    async with AsyncSessionLocal() as session:
        try:
            delete_query = text("""
                DELETE FROM report_highlights
                WHERE id = :highlight_id AND report_id = :report_id
            """)
            result = await session.execute(delete_query, {
                "highlight_id": highlight_id,
                "report_id": report_id
            })
            
            # Update report last_modified
            await session.execute(
                text("UPDATE reports SET last_modified = :now WHERE id = :report_id"),
                {"now": datetime.utcnow(), "report_id": report_id}
            )
            
            await session.commit()
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Highlight not found")
            
            return {"message": "Highlight deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete highlight: {str(e)}")


# ==================== Quick Notes ====================

@router.post("/{report_id}/notes", response_model=QuickNoteDetail, summary="Create note")
async def create_note(report_id: str, request: CreateQuickNoteRequest):
    """
    Create quick note (citation-linked or standalone)
    """
    async with AsyncSessionLocal() as session:
        try:
            note_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            insert_query = text("""
                INSERT INTO report_quick_notes (
                    id, report_id, note_type, content,
                    drug_id, drug_name, section_id, section_title, loinc_code,
                    highlighted_text, start_char, end_char, highlight_color,
                    created_at, updated_at
                )
                VALUES (
                    :id, :report_id, :note_type, :content,
                    :drug_id, :drug_name, :section_id, :section_title, :loinc_code,
                    :highlighted_text, :start_char, :end_char, :highlight_color,
                    :created_at, :updated_at
                )
                RETURNING *
            """)
            
            result = await session.execute(
                insert_query,
                {
                    "id": note_id,
                    "report_id": report_id,
                    "note_type": request.note_type,
                    "content": request.content,
                    "drug_id": request.drug_id,
                    "drug_name": request.drug_name,
                    "section_id": request.section_id,
                    "section_title": request.section_title,
                    "loinc_code": request.loinc_code,
                    "highlighted_text": request.highlighted_text,
                    "start_char": request.start_char,
                    "end_char": request.end_char,
                    "highlight_color": request.highlight_color,
                    "created_at": now,
                    "updated_at": now
                }
            )
            
            # Update report last_modified
            await session.execute(
                text("UPDATE reports SET last_modified = :now WHERE id = :report_id"),
                {"now": now, "report_id": report_id}
            )
            
            await session.commit()
            
            row = result.fetchone()
            
            # Build citation if citation-linked
            citation = None
            if row.note_type == 'citation_linked':
                citation = {
                    "drug_id": row.drug_id,
                    "drug_name": row.drug_name,
                    "section_id": row.section_id,
                    "section_title": row.section_title,
                    "loinc_code": row.loinc_code,
                    "highlighted_text": row.highlighted_text,
                    "start_char": row.start_char,
                    "end_char": row.end_char,
                    "highlight_color": row.highlight_color
                }
            
            return QuickNoteDetail(
                id=str(row.id),
                note_type=row.note_type,
                content=row.content,
                created_at=row.created_at,
                updated_at=row.updated_at,
                citation=citation
            )
            
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create note: {str(e)}")


@router.get("/{report_id}/notes", response_model=List[QuickNoteDetail], summary="List notes")
async def list_notes(report_id: str, note_type: Optional[str] = None):
    """
    List all notes for report
    
    Optional filter by note_type (citation_linked or standalone)
    """
    async with AsyncSessionLocal() as session:
        try:
            if note_type:
                query = text("""
                    SELECT * FROM report_quick_notes
                    WHERE report_id = :report_id AND note_type = :note_type
                    ORDER BY created_at
                """)
                result = await session.execute(query, {
                    "report_id": report_id,
                    "note_type": note_type
                })
            else:
                query = text("""
                    SELECT * FROM report_quick_notes
                    WHERE report_id = :report_id
                    ORDER BY created_at
                """)
                result = await session.execute(query, {"report_id": report_id})
            
            rows = result.fetchall()
            
            notes = []
            for row in rows:
                citation = None
                if row.note_type == 'citation_linked':
                    citation = {
                        "drug_id": row.drug_id,
                        "drug_name": row.drug_name,
                        "section_id": row.section_id,
                        "section_title": row.section_title,
                        "loinc_code": row.loinc_code,
                        "highlighted_text": row.highlighted_text,
                        "start_char": row.start_char,
                        "end_char": row.end_char,
                        "highlight_color": row.highlight_color
                    }
                
                notes.append(QuickNoteDetail(
                    id=str(row.id),
                    note_type=row.note_type,
                    content=row.content,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    citation=citation
                ))
            
            return notes
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list notes: {str(e)}")


@router.put("/{report_id}/notes/{note_id}", summary="Update note")
async def update_note(report_id: str, note_id: str, request: UpdateQuickNoteRequest):
    """
    Edit note content
    """
    async with AsyncSessionLocal() as session:
        try:
            now = datetime.utcnow()
            
            update_query = text("""
                UPDATE report_quick_notes
                SET content = :content, updated_at = :updated_at
                WHERE id = :note_id AND report_id = :report_id
                RETURNING *
            """)
            
            result = await session.execute(update_query, {
                "content": request.content,
                "updated_at": now,
                "note_id": note_id,
                "report_id": report_id
            })
            
            # Update report last_modified
            await session.execute(
                text("UPDATE reports SET last_modified = :now WHERE id = :report_id"),
                {"now": now, "report_id": report_id}
            )
            
            await session.commit()
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Note not found")
            
            return {"message": "Note updated successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update note: {str(e)}")


@router.delete("/{report_id}/notes/{note_id}", summary="Delete note")
async def delete_note(report_id: str, note_id: str):
    """
    Delete note
    """
    async with AsyncSessionLocal() as session:
        try:
            delete_query = text("""
                DELETE FROM report_quick_notes
                WHERE id = :note_id AND report_id = :report_id
            """)
            result = await session.execute(delete_query, {
                "note_id": note_id,
                "report_id": report_id
            })
            
            # Update report last_modified
            await session.execute(
                text("UPDATE reports SET last_modified = :now WHERE id = :report_id"),
                {"now": datetime.utcnow(), "report_id": report_id}
            )
            
            await session.commit()
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Note not found")
            
            return {"message": "Note deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete note: {str(e)}")


@router.get("/{report_id}/notes/{note_id}/navigate", response_model=NavigateToCitationResponse, summary="Get navigation data")
async def get_note_navigation(report_id: str, note_id: str):
    """
    Get navigation data for citation-linked note
    """
    async with AsyncSessionLocal() as session:
        try:
            query = text("""
                SELECT * FROM report_quick_notes
                WHERE id = :note_id AND report_id = :report_id AND note_type = 'citation_linked'
            """)
            result = await session.execute(query, {
                "note_id": note_id,
                "report_id": report_id
            })
            
            row = result.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Citation-linked note not found")
            
            return NavigateToCitationResponse(
                drug_id=row.drug_id,
                drug_name=row.drug_name,
                section_id=row.section_id,
                section_title=row.section_title,
                loinc_code=row.loinc_code,
                start_char=row.start_char,
                end_char=row.end_char,
                highlight_color=row.highlight_color
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get navigation data: {str(e)}")


# ==================== Export & Share ====================

@router.post("/{report_id}/export", summary="Export report")
async def export_report(report_id: str, request: ExportReportRequest):
    """
    Export report as PDF or Word document
    
    TODO: Implement PDF/Word generation using reportlab/python-docx
    """
    # Placeholder for Phase 3
    raise HTTPException(
        status_code=501,
        detail="Export functionality will be implemented in Phase 3"
    )


@router.post("/{report_id}/share", summary="Share report")
async def share_report(report_id: str, request: ShareReportRequest):
    """
    Share report with colleagues via email
    
    TODO: Implement email sending using aiosmtplib
    """
    # Placeholder for Phase 3
    raise HTTPException(
        status_code=501,
        detail="Share functionality will be implemented in Phase 3"
    )
