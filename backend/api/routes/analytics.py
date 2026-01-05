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
        - Total sections and embeddings
        - Unique manufacturers
        - Drug class distribution
        - Most common section types
    """
    async with AsyncSessionLocal() as session:
        try:
            # Total drugs
            drug_count_result = await session.execute(
                text("SELECT COUNT(*) as count FROM drug_labels WHERE is_current_version = true")
            )
            total_drugs = drug_count_result.scalar()
            
            # Total sections
            section_count_result = await session.execute(
                text("SELECT COUNT(*) as count FROM drug_sections")
            )
            total_sections = section_count_result.scalar()
            
            # Total embeddings
            embedding_count_result = await session.execute(
                text("SELECT COUNT(*) as count FROM section_embeddings")
            )
            total_embeddings = embedding_count_result.scalar()
            
            # Unique manufacturers
            manufacturer_result = await session.execute(
                text("""
                    SELECT COUNT(DISTINCT manufacturer) as count 
                    FROM drug_labels 
                    WHERE is_current_version = true
                """)
            )
            unique_manufacturers = manufacturer_result.scalar()
            
            # Drug classes (generic names are used as proxy)
            class_result = await session.execute(
                text("""
                    SELECT generic_name, COUNT(*) as count
                    FROM drug_labels
                    WHERE is_current_version = true
                    GROUP BY generic_name
                    ORDER BY count DESC
                    LIMIT 10
                """)
            )
            drug_classes = {row.generic_name: row.count for row in class_result.fetchall()}
            
            # Most common section types
            section_type_result = await session.execute(
                text("""
                    SELECT loinc_code, title, COUNT(*) as count
                    FROM drug_sections
                    GROUP BY loinc_code, title
                    ORDER BY count DESC
                    LIMIT 10
                """)
            )
            section_types = {
                f"{row.title} ({row.loinc_code})": row.count 
                for row in section_type_result.fetchall()
            }
            
            return PlatformAnalytics(
                total_drugs=total_drugs,
                total_sections=total_sections,
                total_embeddings=total_embeddings,
                unique_manufacturers=unique_manufacturers,
                drug_classes=drug_classes,
                common_sections=section_types
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
            
            # Placeholder for entity statistics
            # In production, this would extract drug names, dosages, conditions, etc.
            entity_stats = EntityStatistics(
                drug_names=[drug.brand_name, drug.generic_name],
                conditions=[],  # TODO: Extract from indications section
                dosages=[],     # TODO: Extract from dosage section
                warnings=[]     # TODO: Extract from warnings section
            )
            
            return DrugAnalytics(
                drug_id=drug_id,
                drug_name=drug.brand_name,
                section_count=section_count,
                chunk_count=chunk_count,
                section_breakdown=section_breakdown,
                entity_statistics=entity_stats,
                avg_chunk_size=avg_chunk_size,
                total_content_length=total_content_length
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve drug analytics: {str(e)}"
            )


@router.post(
    "/compare",
    response_model=ComparisonResponse,
    summary="Compare drugs",
    description="Compare multiple drugs side-by-side across various attributes"
)
async def compare_drugs(request: ComparisonRequest):
    """
    Compare multiple drugs
    
    Args:
        request: Comparison request with drug IDs and comparison type
        
    Returns:
        - Side-by-side comparison
        - Similarities and differences
        - Specific attribute comparisons
    """
    async with AsyncSessionLocal() as session:
        try:
            if len(request.drug_ids) < 2:
                raise HTTPException(
                    status_code=400,
                    detail="At least 2 drugs are required for comparison"
                )
            
            comparisons = []
            
            for drug_id in request.drug_ids:
                # Get drug info
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
                
                # Get sections for comparison
                sections_result = await session.execute(
                    text("""
                        SELECT loinc_code, title, content
                        FROM drug_sections
                        WHERE drug_label_id = :drug_id
                    """),
                    {"drug_id": drug_id}
                )
                sections = sections_result.fetchall()
                
                # Build attributes dictionary
                attributes = {
                    "brand_name": drug.brand_name,
                    "generic_name": drug.generic_name,
                    "manufacturer": drug.manufacturer,
                    "dosage_form": drug.dosage_form,
                    "route": drug.route,
                    "marketing_status": drug.marketing_status,
                    "sections": [{"loinc": s.loinc_code, "title": s.title} for s in sections]
                }
                
                # Add specific section content if requested
                if request.attributes:
                    for attr in request.attributes:
                        for section in sections:
                            if attr.lower() in section.title.lower():
                                attributes[attr] = section.content[:500]  # Truncate
                                break
                
                comparisons.append(
                    DrugComparison(
                        drug_id=drug_id,
                        drug_name=drug.brand_name,
                        attributes=attributes
                    )
                )
            
            # Identify similarities and differences
            similarities = []
            differences = []
            
            # Compare generic names
            generic_names = [c.attributes.get("generic_name") for c in comparisons]
            if len(set(generic_names)) == 1:
                similarities.append(f"All drugs contain {generic_names[0]}")
            else:
                differences.append(f"Different active ingredients: {', '.join(set(generic_names))}")
            
            # Compare manufacturers
            manufacturers = [c.attributes.get("manufacturer") for c in comparisons]
            if len(set(manufacturers)) == 1:
                similarities.append(f"All manufactured by {manufacturers[0]}")
            else:
                differences.append(f"Different manufacturers: {', '.join(set(manufacturers))}")
            
            # Compare dosage forms
            dosage_forms = [c.attributes.get("dosage_form") for c in comparisons]
            if len(set(dosage_forms)) == 1:
                similarities.append(f"Same dosage form: {dosage_forms[0]}")
            else:
                differences.append(f"Different dosage forms: {', '.join(set(filter(None, dosage_forms)))}")
            
            return ComparisonResponse(
                comparisons=comparisons,
                similarities=similarities,
                differences=differences
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Comparison failed: {str(e)}"
            )
