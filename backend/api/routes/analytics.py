"""
Analytics Endpoints
Platform statistics, drug analytics, and comparisons
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import text, func
from typing import List

from api.schemas import (
    PlatformAnalytics,
    DrugAnalytics,
    EntityStatistics,
    ComparisonRequest,
    ComparisonResponse,
    DrugComparison
)
from models.db_session import AsyncSessionLocal
from models.database import DrugLabel, DrugSection

router = APIRouter()


@router.get(
    "/platform",
    response_model=PlatformAnalytics,
    summary="Get platform statistics",
    description="Get overall platform statistics and insights"
)
async def get_platform_analytics():
    """
    Get platform-wide statistics
    
    Returns:
        - Total drugs in database
        - Total manufacturers and drug types
        - Active labels count
        - Manufacturers and drug types breakdown
    """
    async with AsyncSessionLocal() as session:
        try:
            # Total current drugs (active labels)
            drug_count_result = await session.execute(
                text("SELECT COUNT(*) as count FROM drug_labels WHERE is_current_version = true")
            )
            total_drugs = drug_count_result.scalar()
            active_labels = total_drugs  # Same as total_drugs
            
            # Total unique manufacturers
            manufacturer_count_result = await session.execute(
                text("""
                    SELECT COUNT(DISTINCT manufacturer) as count
                    FROM drug_labels
                    WHERE is_current_version = true
                """)
            )
            total_manufacturers = manufacturer_count_result.scalar()
            
            # Total unique drug types (generic names)
            drug_type_count_result = await session.execute(
                text("""
                    SELECT COUNT(DISTINCT generic_name) as count
                    FROM drug_labels
                    WHERE is_current_version = true AND generic_name IS NOT NULL
                """)
            )
            total_drug_types = drug_type_count_result.scalar()
            
            # Manufacturers breakdown (top 10)
            manufacturer_result = await session.execute(
                text("""
                    SELECT manufacturer, COUNT(*) as count 
                    FROM drug_labels 
                    WHERE is_current_version = true
                    GROUP BY manufacturer
                    ORDER BY count DESC
                    LIMIT 10
                """)
            )
            manufacturers = [{"name": row.manufacturer, "count": row.count} for row in manufacturer_result.fetchall()]
            
            # Drug types breakdown (top 10)
            drug_type_result = await session.execute(
                text("""
                    SELECT generic_name, COUNT(*) as count
                    FROM drug_labels
                    WHERE is_current_version = true AND generic_name IS NOT NULL
                    GROUP BY generic_name
                    ORDER BY count DESC
                    LIMIT 10
                """)
            )
            drug_types = [{"name": row.generic_name, "count": row.count} for row in drug_type_result.fetchall()]
            
            # Get latest updated date
            updated_result = await session.execute(
                text("""
                    SELECT MAX(last_updated) as last_update
                    FROM drug_labels
                    WHERE is_current_version = true
                """)
            )
            last_updated = updated_result.scalar()
            
            return PlatformAnalytics(
                total_drugs=total_drugs,
                total_manufacturers=total_manufacturers,
                total_drug_types=total_drug_types,
                active_labels=active_labels,
                manufacturers=manufacturers,
                drug_types=drug_types,
                last_updated=last_updated
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve platform analytics: {str(e)}"
            )


@router.get(
    "/drug/{drug_id}",
    response_model=DrugAnalytics,
    summary="Get drug analytics",
    description="Get detailed analytics for a specific drug"
)
async def get_drug_analytics(drug_id: int):
    """
    Get analytics for a specific drug
    
    Args:
        drug_id: Drug label ID
        
    Returns:
        - Section count and breakdown
        - Chunk count
        - Entity statistics (extracted terms)
        - Content length metrics
    """
    async with AsyncSessionLocal() as session:
        try:
            # Check drug exists
            drug_result = await session.execute(
                text("SELECT * FROM drug_labels WHERE id = :drug_id"),
                {"drug_id": drug_id}
            )
            drug = drug_result.fetchone()
            
            if not drug:
                raise HTTPException(
                    status_code=404,
                    detail=f"Drug with id {drug_id} not found"
                )
            
            # Section count
            section_count_result = await session.execute(
                text("SELECT COUNT(*) FROM drug_sections WHERE drug_label_id = :drug_id"),
                {"drug_id": drug_id}
            )
            section_count = section_count_result.scalar()
            
            # Chunk count
            chunk_count_result = await session.execute(
                text("""
                    SELECT COUNT(*) 
                    FROM section_embeddings se
                    JOIN drug_sections ds ON se.section_id = ds.id
                    WHERE ds.drug_label_id = :drug_id
                """),
                {"drug_id": drug_id}
            )
            chunk_count = chunk_count_result.scalar()
            
            # Section type breakdown
            section_breakdown_result = await session.execute(
                text("""
                    SELECT loinc_code, title, COUNT(*) as count
                    FROM drug_sections
                    WHERE drug_label_id = :drug_id
                    GROUP BY loinc_code, title
                """),
                {"drug_id": drug_id}
            )
            section_breakdown = {
                f"{row.title} ({row.loinc_code})": row.count
                for row in section_breakdown_result.fetchall()
            }
            
            # Average chunk size
            avg_chunk_result = await session.execute(
                text("""
                    SELECT AVG(LENGTH(se.chunk_text)) as avg_length
                    FROM section_embeddings se
                    JOIN drug_sections ds ON se.section_id = ds.id
                    WHERE ds.drug_label_id = :drug_id
                """),
                {"drug_id": drug_id}
            )
            avg_chunk_size = int(avg_chunk_result.scalar() or 0)
            
            # Total content length
            total_length_result = await session.execute(
                text("""
                    SELECT SUM(LENGTH(content)) as total_length
                    FROM drug_sections
                    WHERE drug_label_id = :drug_id
                """),
                {"drug_id": drug_id}
            )
            total_content_length = int(total_length_result.scalar() or 0)
            
            # Entity statistics from NER summary
            ner_summary = drug.ner_summary or {}
            total_entities = sum(ner_summary.values()) if ner_summary else 0
            
            # Create entity breakdown
            entity_breakdown = []
            if ner_summary:
                for entity_type, count in sorted(ner_summary.items(), key=lambda x: x[1], reverse=True)[:10]:
                    percentage = (count / total_entities * 100) if total_entities > 0 else 0
                    entity_breakdown.append(EntityStatistics(
                        entity_type=entity_type,
                        count=count,
                        percentage=round(percentage, 2)
                    ))
            
            # Most common entities (top entities across all types)
            most_common_entities = [
                {"entity_type": et, "count": c} 
                for et, c in sorted(ner_summary.items(), key=lambda x: x[1], reverse=True)[:5]
            ] if ner_summary else []
            
            return DrugAnalytics(
                drug_id=drug_id,
                drug_name=drug.name,
                total_sections=section_count,
                total_entities=total_entities,
                entity_breakdown=entity_breakdown,
                most_common_entities=most_common_entities
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve drug analytics: {str(e)}"
            )
