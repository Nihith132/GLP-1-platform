"""
Comparison Workspace Endpoints
For side-by-side drug label comparison with lexical and semantic differencing
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from typing import List, Dict, Optional
import difflib
import os
import numpy as np
import json
from groq import Groq

from api.schemas import (
    CompareLoadRequest, CompareLoadResponse,
    LexicalDiffRequest, LexicalDiffResponse, LexicalDiffResult, TextChange,
    SemanticDiffRequest, SemanticDiffResponse, SemanticDiffResult, 
    SemanticMatch, SemanticSegment, SemanticDiffSummary,
    ExplainSegmentRequest, ExplainSegmentResponse,
    SummarizeDiffsRequest, SummarizeDiffsResponse, DiffCategorySummary,
    DrugWithSections, DrugSection
)
from models.db_session import AsyncSessionLocal
from etl.vector_service import VectorService

router = APIRouter()

# Initialize services
vector_service = VectorService()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


async def load_drug_with_sections(session, drug_id: int):
    """Helper to load drug with all sections"""
    # Get drug info
    drug_query = text("""
        SELECT id, name, generic_name, manufacturer, set_id, version,
               is_current_version, status, last_updated, created_at,
               ner_summary, source_file
        FROM drug_labels
        WHERE id = :drug_id
    """)
    drug_result = await session.execute(drug_query, {"drug_id": drug_id})
    drug_row = drug_result.fetchone()
    
    if not drug_row:
        raise HTTPException(status_code=404, detail=f"Drug {drug_id} not found")
    
    # Get sections
    sections_query = text("""
        SELECT id, loinc_code, title, "order", content, content_html, 
               section_number, level, parent_section_id, ner_entities
        FROM drug_sections
        WHERE drug_label_id = :drug_id
    """)
    sections_result = await session.execute(sections_query, {"drug_id": drug_id})
    sections_rows = list(sections_result.fetchall())
    
    # Sort sections hierarchically by section_number
    def parse_section_number(section_num):
        """Convert section_number like '1.2.3' to tuple (1, 2, 3) for sorting"""
        if not section_num:
            return (999999,)
        try:
            return tuple(int(x) for x in str(section_num).split('.'))
        except:
            return (999999,)
    
    sections_rows.sort(key=lambda row: parse_section_number(row.section_number))
    
    sections = [
        DrugSection(
            id=row.id,
            loinc_code=row.loinc_code,
            title=row.title,
            order=row.order,
            content=row.content,
            content_html=row.content_html,
            section_number=row.section_number,
            level=row.level,
            parent_section_id=row.parent_section_id,
            ner_entities=row.ner_entities or []
        )
        for row in sections_rows
    ]
    
    drug = DrugWithSections(
        id=drug_row.id,
        name=drug_row.name,
        generic_name=drug_row.generic_name,
        manufacturer=drug_row.manufacturer,
        set_id=drug_row.set_id,
        version=drug_row.version,
        is_current_version=drug_row.is_current_version,
        status=drug_row.status,
        last_updated=drug_row.last_updated,
        created_at=drug_row.created_at,
        ner_summary=drug_row.ner_summary or {},
        source_file=drug_row.source_file,
        sections=sections
    )
    
    return drug


@router.post(
    "/load",
    response_model=CompareLoadResponse,
    summary="Load drugs for comparison",
    description="Load source drug and competitors with all sections for comparison workspace"
)
async def compare_load(request: CompareLoadRequest):
    """
    Load drugs for comparison workspace
    
    Args:
        request: Source drug ID and list of competitor drug IDs
        
    Returns:
        Source drug and competitors with all sections
    """
    async with AsyncSessionLocal() as session:
        try:
            # Load source drug
            source_drug = await load_drug_with_sections(session, request.source_drug_id)
            
            # Load competitors
            competitors = []
            for competitor_id in request.competitor_drug_ids:
                competitor = await load_drug_with_sections(session, competitor_id)
                competitors.append(competitor)
            
            return CompareLoadResponse(
                source_drug=source_drug,
                competitors=competitors
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load drugs for comparison: {str(e)}"
            )


@router.post(
    "/lexical",
    response_model=LexicalDiffResponse,
    summary="Lexical differencing",
    description="Text-based diff showing additions (green) and deletions (red)"
)
async def compare_lexical(request: LexicalDiffRequest):
    """
    Perform lexical (text-based) differencing
    
    Shows character-level differences:
    - Red in source = text deleted (in source but not in competitor)
    - Green in competitor = text added (in competitor but not in source)
    
    Args:
        request: Source and competitor drug IDs, optional section filter
        
    Returns:
        Lexical differences with character positions for highlighting
    """
    async with AsyncSessionLocal() as session:
        try:
            # Load both drugs
            source_drug = await load_drug_with_sections(session, request.source_drug_id)
            competitor_drug = await load_drug_with_sections(session, request.competitor_drug_id)
            
            # Build section mapping
            source_sections = {s.loinc_code: s for s in source_drug.sections}
            competitor_sections = {s.loinc_code: s for s in competitor_drug.sections}
            
            # Get common sections (or specific section)
            if request.section_loinc:
                common_loincs = [request.section_loinc] if request.section_loinc in source_sections else []
            else:
                common_loincs = list(set(source_sections.keys()) & set(competitor_sections.keys()))
            
            diffs = []
            for loinc in sorted(common_loincs):
                source_section = source_sections[loinc]
                competitor_section = competitor_sections[loinc]
                
                # Use difflib to compute differences
                source_text = source_section.content
                competitor_text = competitor_section.content
                
                # Compute sequence matcher
                sm = difflib.SequenceMatcher(None, source_text, competitor_text)
                
                deletions = []  # Red in source
                additions = []  # Green in competitor
                
                for tag, i1, i2, j1, j2 in sm.get_opcodes():
                    if tag == 'delete':
                        deletions.append(TextChange(
                            change_type="deletion",
                            text=source_text[i1:i2],
                            start_char=i1,
                            end_char=i2
                        ))
                    elif tag == 'insert':
                        additions.append(TextChange(
                            change_type="addition",
                            text=competitor_text[j1:j2],
                            start_char=j1,
                            end_char=j2
                        ))
                    elif tag == 'replace':
                        deletions.append(TextChange(
                            change_type="deletion",
                            text=source_text[i1:i2],
                            start_char=i1,
                            end_char=i2
                        ))
                        additions.append(TextChange(
                            change_type="addition",
                            text=competitor_text[j1:j2],
                            start_char=j1,
                            end_char=j2
                        ))
                
                diffs.append(LexicalDiffResult(
                    section_loinc=loinc,
                    section_title=source_section.title,
                    source_text=source_text,
                    competitor_text=competitor_text,
                    additions=additions,
                    deletions=deletions
                ))
            
            return LexicalDiffResponse(
                source_drug_name=source_drug.name,
                competitor_drug_name=competitor_drug.name,
                diffs=diffs
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Lexical diff failed: {str(e)}"
            )


@router.post(
    "/semantic",
    response_model=SemanticDiffResponse,
    summary="Semantic differencing",
    description="Meaning-based comparison with competitive advantage highlighting"
)
async def compare_semantic(request: SemanticDiffRequest):
    """
    Perform semantic (meaning-based) differencing
    
    Color coding:
    - Green in source = Unique to source (competitive advantage) OR high similarity match
    - Yellow = Partial match (similar but different)
    - Red in competitor = Conflict (contradictory information)
    - Blue underline in competitor = Omission (gap to address)
    
    Args:
        request: Source and competitor drug IDs, optional section filter
        
    Returns:
        Semantic matches with color-coded segments and explanations
    """
    async with AsyncSessionLocal() as session:
        try:
            # Load both drugs
            source_drug = await load_drug_with_sections(session, request.source_drug_id)
            competitor_drug = await load_drug_with_sections(session, request.competitor_drug_id)
            
            # Build section mapping
            source_sections = {s.loinc_code: s for s in source_drug.sections}
            competitor_sections = {s.loinc_code: s for s in competitor_drug.sections}
            
            # Get common sections
            if request.section_loinc:
                common_loincs = [request.section_loinc] if request.section_loinc in source_sections else []
            else:
                common_loincs = list(set(source_sections.keys()) & set(competitor_sections.keys()))
            
            diffs = []
            total_stats = {
                "high_similarity": 0,
                "partial_matches": 0,
                "unique_to_source": 0,
                "omissions": 0,
                "conflicts": 0
            }
            
            for loinc in sorted(common_loincs):
                source_section = source_sections[loinc]
                competitor_section = competitor_sections[loinc]
                
                print(f"\n=== Processing section {loinc} ===")
                print(f"Source section ID: {source_section.id}, Title: {source_section.title}")
                print(f"Competitor section ID: {competitor_section.id}, Title: {competitor_section.title}")
                
                # Get pre-stored embeddings from database
                source_embeddings_query = text("""
                    SELECT chunk_text, embedding
                    FROM section_embeddings
                    WHERE section_id = :section_id
                    ORDER BY chunk_index
                """)
                competitor_embeddings_query = text("""
                    SELECT chunk_text, embedding
                    FROM section_embeddings
                    WHERE section_id = :section_id
                    ORDER BY chunk_index
                """)
                
                source_emb_result = await session.execute(source_embeddings_query, {"section_id": source_section.id})
                competitor_emb_result = await session.execute(competitor_embeddings_query, {"section_id": competitor_section.id})
                
                source_rows = source_emb_result.fetchall()
                competitor_rows = competitor_emb_result.fetchall()
                
                print(f"Query returned: {len(source_rows)} source embeddings, {len(competitor_rows)} competitor embeddings")
                
                # ONLY use pre-stored embeddings - skip sections without them
                if not source_rows or not competitor_rows:
                    print(f"⊗ SKIPPING section {loinc} - embeddings not found in database")
                    print(f"  Source section ID {source_section.id}: {len(source_rows)} embeddings")
                    print(f"  Competitor section ID {competitor_section.id}: {len(competitor_rows)} embeddings")
                    continue
                
                # Extract sentences and embeddings from database
                # pgvector returns embeddings as strings, need to parse them
                source_sentences = [row[0] for row in source_rows]
                source_embeddings = [np.array(json.loads(str(row[1]))) for row in source_rows]
                competitor_sentences = [row[0] for row in competitor_rows]
                competitor_embeddings = [np.array(json.loads(str(row[1]))) for row in competitor_rows]
                print(f"✓ Using pre-stored embeddings for section {loinc} ({len(source_rows)} source, {len(competitor_rows)} competitor)")
                
                matches = []
                
                # Track matched sentences
                matched_source = set()
                matched_competitor = set()
                
                # Find matches
                for i, src_emb in enumerate(source_embeddings):
                    best_match_idx = None
                    best_score = 0.0
                    
                    for j, comp_emb in enumerate(competitor_embeddings):
                        # Cosine similarity
                        similarity = float(src_emb @ comp_emb / (
                            (src_emb @ src_emb) ** 0.5 * (comp_emb @ comp_emb) ** 0.5
                        ))
                        
                        if similarity > best_score and similarity >= request.similarity_threshold:
                            best_score = similarity
                            best_match_idx = j
                    
                    if best_match_idx is not None:
                        # Matched
                        matched_source.add(i)
                        matched_competitor.add(best_match_idx)
                        
                        if best_score >= 0.85:
                            # High similarity match
                            diff_type = "high_similarity"
                            color = "green"
                            explanation = f"Both drugs have similar information (similarity: {best_score:.2f})"
                            total_stats["high_similarity"] += 1
                        else:
                            # Partial match
                            diff_type = "partial_match"
                            color = "yellow"
                            explanation = f"Similar but with differences (similarity: {best_score:.2f})"
                            total_stats["partial_matches"] += 1
                        
                        matches.append(SemanticMatch(
                            source_segment=SemanticSegment(
                                text=source_sentences[i],
                                start_char=0,  # TODO: Calculate actual position
                                end_char=len(source_sentences[i]),
                                highlight_color=color,
                                diff_type=diff_type
                            ),
                            competitor_segment=SemanticSegment(
                                text=competitor_sentences[best_match_idx],
                                start_char=0,
                                end_char=len(competitor_sentences[best_match_idx]),
                                highlight_color=color,
                                diff_type=diff_type
                            ),
                            similarity_score=best_score,
                            explanation=explanation
                        ))
                
                # Find unique to source (competitive advantages)
                for i in range(len(source_sentences)):
                    if i not in matched_source:
                        matches.append(SemanticMatch(
                            source_segment=SemanticSegment(
                                text=source_sentences[i],
                                start_char=0,
                                end_char=len(source_sentences[i]),
                                highlight_color="green",
                                diff_type="unique_to_source"
                            ),
                            competitor_segment=None,
                            similarity_score=None,
                            explanation="FDA-approved claim unique to your product - competitive advantage ✅"
                        ))
                        total_stats["unique_to_source"] += 1
                
                # Find omissions (gaps in source)
                for j in range(len(competitor_sentences)):
                    if j not in matched_competitor:
                        matches.append(SemanticMatch(
                            source_segment=None,
                            competitor_segment=SemanticSegment(
                                text=competitor_sentences[j],
                                start_char=0,
                                end_char=len(competitor_sentences[j]),
                                highlight_color="blue",
                                underline_style="wavy",
                                diff_type="omission"
                            ),
                            similarity_score=None,
                            explanation="Competitor has this information but your product doesn't - gap to address 🔍"
                        ))
                        total_stats["omissions"] += 1
                
                diffs.append(SemanticDiffResult(
                    section_loinc=loinc,
                    section_title=source_section.title,
                    matches=matches
                ))
            
            summary = SemanticDiffSummary(
                total_matches=sum(total_stats.values()),
                high_similarity=total_stats["high_similarity"],
                partial_matches=total_stats["partial_matches"],
                unique_to_source=total_stats["unique_to_source"],
                omissions=total_stats["omissions"],
                conflicts=total_stats["conflicts"]
            )
            
            return SemanticDiffResponse(
                source_drug_name=source_drug.name,
                competitor_drug_name=competitor_drug.name,
                diffs=diffs,
                summary=summary
            )
            
        except HTTPException:
            raise
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"ERROR in semantic diff: {error_details}")
            raise HTTPException(
                status_code=500,
                detail=f"Semantic diff failed: {str(e)}"
            )


@router.post(
    "/semantic/explain",
    response_model=ExplainSegmentResponse,
    summary="Explain segment difference",
    description="Get detailed LLM explanation of a specific segment difference"
)
async def explain_segment(request: ExplainSegmentRequest):
    """
    Explain a specific segment difference using LLM
    
    Provides:
    - Detailed explanation of the difference
    - Clinical significance
    - Marketing implications
    - Recommended actions
    """
    async with AsyncSessionLocal() as session:
        try:
            # Load drugs
            source_drug = await load_drug_with_sections(session, request.source_drug_id)
            competitor_drug = await load_drug_with_sections(session, request.competitor_drug_id)
            
            # Build prompt
            system_prompt = """You are a pharmaceutical regulatory and marketing expert analyzing FDA drug label differences.

Provide:
1. Clear explanation of what differs
2. Clinical significance (safety, efficacy, patient impact)
3. Marketing implications (advantage, gap, or neutral)
4. Specific action items

Be concise, precise, and actionable."""

            user_prompt = f"""Analyze this difference between two drug labels:

SOURCE DRUG: {source_drug.name}
Text: {request.source_text or "[No matching text]"}

COMPETITOR DRUG: {competitor_drug.name}
Text: {request.competitor_text or "[No matching text]"}

Section: {request.section_loinc}

Provide:
1. Explanation of the difference
2. Clinical significance
3. Marketing implication
4. Action items (2-3 specific recommendations)"""

            # Call LLM
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=groq_model,
                temperature=0.3,
                max_tokens=800
            )
            
            response_text = chat_completion.choices[0].message.content
            
            # Parse response (simple split for now)
            lines = response_text.split('\n')
            explanation = ""
            clinical = ""
            marketing = ""
            actions = []
            
            current_section = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if "explanation" in line.lower() or "difference" in line.lower():
                    current_section = "explanation"
                elif "clinical" in line.lower():
                    current_section = "clinical"
                elif "marketing" in line.lower():
                    current_section = "marketing"
                elif "action" in line.lower():
                    current_section = "actions"
                elif current_section == "explanation":
                    explanation += line + " "
                elif current_section == "clinical":
                    clinical += line + " "
                elif current_section == "marketing":
                    marketing += line + " "
                elif current_section == "actions":
                    if line.startswith(('-', '•', '*')) or line[0].isdigit():
                        actions.append(line.lstrip('-•*0123456789. '))
            
            return ExplainSegmentResponse(
                explanation=explanation.strip() or response_text[:500],
                clinical_significance=clinical.strip() or "Review clinical data",
                marketing_implication=marketing.strip() or "Assess competitive positioning",
                action_items=actions or ["Review with medical affairs team", "Consider for future label updates"]
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to explain segment: {str(e)}"
            )


@router.post(
    "/semantic/summary",
    response_model=SummarizeDiffsResponse,
    summary="Summarize all differences",
    description="Get executive summary of all differences between two drugs"
)
async def summarize_diffs(request: SummarizeDiffsRequest):
    """
    Generate executive summary of all differences
    
    Returns:
    - High-level executive summary
    - Category-by-category breakdown (Indications, Dosing, Safety, etc.)
    - Overall statistics
    """
    async with AsyncSessionLocal() as session:
        try:
            # First, get semantic diff
            semantic_request = SemanticDiffRequest(
                source_drug_id=request.source_drug_id,
                competitor_drug_id=request.competitor_drug_id
            )
            semantic_result = await compare_semantic(semantic_request)
            
            # Organize by category
            categories = {}
            for diff_result in semantic_result.diffs:
                category = diff_result.section_title
                if category not in categories:
                    categories[category] = {
                        "advantages": [],
                        "gaps": [],
                        "conflicts": []
                    }
                
                for match in diff_result.matches:
                    if match.source_segment and match.source_segment.diff_type == "unique_to_source":
                        categories[category]["advantages"].append(match.source_segment.text[:200])
                    elif match.competitor_segment and match.competitor_segment.diff_type == "omission":
                        categories[category]["gaps"].append(match.competitor_segment.text[:200])
                    elif match.competitor_segment and match.competitor_segment.diff_type == "conflict":
                        categories[category]["conflicts"].append(match.competitor_segment.text[:200])
            
            # Generate executive summary using LLM
            context = f"""
SOURCE: {semantic_result.source_drug_name}
COMPETITOR: {semantic_result.competitor_drug_name}

STATISTICS:
- Advantages (unique to source): {semantic_result.summary.unique_to_source}
- Gaps (omissions): {semantic_result.summary.omissions}
- Conflicts: {semantic_result.summary.conflicts}
- Matches: {semantic_result.summary.high_similarity + semantic_result.summary.partial_matches}
"""

            system_prompt = """You are a pharmaceutical executive advisor. Create a concise executive summary of drug label differences for strategic decision-making."""
            
            user_prompt = f"""{context}

Create a 3-paragraph executive summary covering:
1. Overall competitive position
2. Key strengths and advantages
3. Critical gaps and recommended actions"""

            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=groq_model,
                temperature=0.4,
                max_tokens=600
            )
            
            executive_summary = chat_completion.choices[0].message.content
            
            # Build category summaries
            category_summaries = [
                DiffCategorySummary(
                    category=cat,
                    advantages=data["advantages"][:5],
                    gaps=data["gaps"][:5],
                    conflicts=data["conflicts"][:5]
                )
                for cat, data in categories.items()
                if data["advantages"] or data["gaps"] or data["conflicts"]
            ]
            
            return SummarizeDiffsResponse(
                source_drug_name=semantic_result.source_drug_name,
                competitor_drug_name=semantic_result.competitor_drug_name,
                executive_summary=executive_summary,
                category_summaries=category_summaries,
                overall_statistics=semantic_result.summary
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to summarize differences: {str(e)}"
            )
