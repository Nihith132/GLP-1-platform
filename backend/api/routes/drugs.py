"""
Drug Endpoints
CRUD operations for drug labels
"""

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func
from typing import Optional, List

from api.schemas import (
    DrugListResponse,
    DrugDetail,
    DrugWithSections,
    DrugSection,
    ErrorResponse
)
from models.database import DrugLabel, DrugSection as DBDrugSection
from models.db_session import AsyncSessionLocal

router = APIRouter()


@router.get(
    "/",
    response_model=DrugListResponse,
    summary="Get all drugs",
    description="Retrieve a paginated list of all drug labels in the database"
)
async def get_all_drugs(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of records to return"),
    manufacturer: Optional[str] = Query(default=None, description="Filter by manufacturer"),
    generic_name: Optional[str] = Query(default=None, description="Filter by generic name")
):
    """
    Get all drug labels with optional filtering and pagination
    
    Returns:
        - List of drugs with metadata
        - Total count
    """
    async with AsyncSessionLocal() as session:
        try:
            # Build query
            query = select(DrugLabel).where(DrugLabel.is_current_version == True)
            
            # Apply filters
            if manufacturer:
                query = query.where(DrugLabel.manufacturer.ilike(f"%{manufacturer}%"))
            if generic_name:
                query = query.where(DrugLabel.generic_name.ilike(f"%{generic_name}%"))
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar()
            
            # Apply pagination and order
            query = query.order_by(DrugLabel.id).offset(skip).limit(limit)
            
            # Execute query
            result = await session.execute(query)
            drugs = result.scalars().all()
            
            return DrugListResponse(
                total=total,
                drugs=[DrugDetail.model_validate(drug) for drug in drugs]
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve drugs: {str(e)}"
            )


@router.get(
    "/{drug_id}",
    response_model=DrugWithSections,
    summary="Get drug by ID",
    description="Retrieve detailed information about a specific drug including all sections"
)
async def get_drug_by_id(drug_id: int):
    """
    Get a single drug with all its sections
    
    Args:
        drug_id: Drug label ID
        
    Returns:
        - Drug metadata
        - All labeled sections with content
    """
    async with AsyncSessionLocal() as session:
        try:
            # Get drug with sections
            query = select(DrugLabel).where(DrugLabel.id == drug_id)
            result = await session.execute(query)
            drug = result.scalar_one_or_none()
            
            if not drug:
                raise HTTPException(
                    status_code=404,
                    detail=f"Drug with ID {drug_id} not found"
                )
            
            # Get sections
            sections_query = select(DBDrugSection).where(
                DBDrugSection.drug_label_id == drug_id
            ).order_by(DBDrugSection.order)
            
            sections_result = await session.execute(sections_query)
            sections = sections_result.scalars().all()
            
            # Convert to response model
            drug_dict = DrugDetail.model_validate(drug).model_dump()
            drug_dict['sections'] = [
                DrugSection.model_validate(section) for section in sections
            ]
            
            return DrugWithSections(**drug_dict)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve drug: {str(e)}"
            )


@router.get(
    "/{drug_id}/sections/{loinc_code}",
    response_model=DrugSection,
    summary="Get specific section",
    description="Retrieve a specific section of a drug label by LOINC code"
)
async def get_drug_section(
    drug_id: int,
    loinc_code: str
):
    """
    Get a specific section from a drug label
    
    Args:
        drug_id: Drug label ID
        loinc_code: LOINC section code
        
    Returns:
        - Section content with NER entities
    """
    async with AsyncSessionLocal() as session:
        try:
            # Verify drug exists
            drug_query = select(DrugLabel).where(DrugLabel.id == drug_id)
            drug_result = await session.execute(drug_query)
            drug = drug_result.scalar_one_or_none()
            
            if not drug:
                raise HTTPException(
                    status_code=404,
                    detail=f"Drug with ID {drug_id} not found"
                )
            
            # Get section
            section_query = select(DBDrugSection).where(
                DBDrugSection.drug_label_id == drug_id,
                DBDrugSection.loinc_code == loinc_code
            )
            
            section_result = await session.execute(section_query)
            section = section_result.scalar_one_or_none()
            
            if not section:
                raise HTTPException(
                    status_code=404,
                    detail=f"Section with LOINC code {loinc_code} not found for this drug"
                )
            
            return DrugSection.model_validate(section)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve section: {str(e)}"
            )


@router.get(
    "/search/by-name",
    response_model=List[DrugDetail],
    summary="Search drugs by name",
    description="Search for drugs by brand or generic name"
)
async def search_drugs_by_name(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(default=10, ge=1, le=50)
):
    """
    Search drugs by name (brand or generic)
    
    Args:
        q: Search query
        limit: Maximum results
        
    Returns:
        - List of matching drugs
    """
    async with AsyncSessionLocal() as session:
        try:
            query = select(DrugLabel).where(
                DrugLabel.is_current_version == True
            ).where(
                (DrugLabel.name.ilike(f"%{q}%")) |
                (DrugLabel.generic_name.ilike(f"%{q}%"))
            ).order_by(DrugLabel.name).limit(limit)
            
            result = await session.execute(query)
            drugs = result.scalars().all()
            
            return [DrugDetail.model_validate(drug) for drug in drugs]
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Search failed: {str(e)}"
            )
