"""
Comprehensive ETL Pipeline for All 19 Drugs
- Parse with hierarchical parser
- Update database with new sections
- Generate vector embeddings
- Update section_embeddings table
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from datetime import datetime
from typing import List, Dict
from models.db_session import AsyncSessionLocal
from models.database import DrugLabel, DrugSection, SectionEmbedding
from etl.parser_hierarchical import HierarchicalParser
from etl.vector_service import VectorService
from sqlalchemy import select, delete, text
import logging
from collections import Counter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Drug mapping: ZIP filename -> (Drug Name, Generic Name)
DRUG_MAPPING = {
    "20181010_6c57f874-73b4-4769-8947-0b0b3c5dac1d.zip": ("Diethylpropion HCl Controlled-Release", "diethylpropion hydrochloride"),
    "20230419_375bfe83-c893-3ea7-e054-00144ff88e88.zip": ("PHENTERMINE HCL", "phentermine hydrochloride"),
    "20231228_f6d9b369-4b64-4d3f-844d-5d60dd257c55.zip": ("Benzphetamine Hydrochloride", "benzphetamine hydrochloride"),
    "20240117_a2d3bd73-f3af-4ea5-a57c-66b0004cfe4f.zip": ("ALLI", "orlistat"),
    "20240215_3b44d104-a7d0-4366-9d42-63f784f3cb22.zip": ("Phentermine Hydrochloride", "phentermine hydrochloride"),
    "20240709_6240792b-9224-2d10-e053-2a91aa0a2c3e.zip": ("Xenical", "orlistat"),
    "20250906_53d03c03-ebf7-418d-88a8-533eabd2ee4f.zip": ("Byetta", "exenatide"),
    "20250910_40dd5602-53da-45ac-bb4b-15789aba40f9.zip": ("Qsymia", "phentermine and topiramate"),
    "20250921_cd4f2b19-8752-4fed-81f3-d3074ade613c.zip": ("Diethylpropion Hydrochloride", "diethylpropion hydrochloride"),
    "20251102_27f15fac-7d98-4114-a2ec-92494a91da98.zip": ("RYBELSUS", "semaglutide"),
    "20251102_3946d389-0926-4f77-a708-0acb8153b143.zip": ("Saxenda", "liraglutide"),
    "20251102_5a9ef4ea-c76a-4d34-a604-27c5b505f5a4.zip": ("Victoza", "liraglutide"),
    "20251102_adec4fd2-6858-4c99-91d4-531f5f2a2d79.zip": ("Ozempic", "semaglutide"),
    "20251112_485ff360-32c8-11df-928b-0002a5d5c51b.zip": ("Contrave", "naltrexone and bupropion"),
    "20251205_ee06186f-2aa3-4990-a760-757579d8f77b.zip": ("WEGOVY", "semaglutide"),
    "20251221_463050bd-2b1c-40f5-b3c3-0a04bb433309.zip": ("Trulicity", "dulaglutide"),
    "20251221_70c3ccf7-4df0-4c75-ba07-fede9970c8d9.zip": ("Imcivree", "setmelanotide"),
    "20251231_487cd7e7-434c-4925-99fa-aa80b1cc776b.zip": ("ZEPBOUND", "tirzepatide"),
    "20251231_d2d7da5d-ad07-4228-955f-cf7e355c8cc0.zip": ("MOUNJARO", "tirzepatide"),
}


def chunk_text(text: str, max_chars: int = 2000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks for embedding
    
    Args:
        text: Text to chunk
        max_chars: Maximum characters per chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_chars
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for period, question mark, or exclamation within last 100 chars
            chunk_end = text[start:end].rfind('.')
            if chunk_end > max_chars - 100:
                end = start + chunk_end + 1
        
        chunks.append(text[start:end].strip())
        start = end - overlap
    
    return chunks


async def parse_drug(zip_path: Path, drug_name: str, generic_name: str) -> Dict:
    """Parse a single drug with hierarchical parser"""
    
    parser = HierarchicalParser()
    logger.info(f"📦 Parsing: {drug_name}")
    
    result = parser.parse_zip_file(str(zip_path))
    
    if not result:
        logger.error(f"❌ Failed to parse {drug_name}")
        return None
    
    metadata = result['metadata']
    sections = result['sections']
    
    # Check for duplicates
    title_counts = Counter(s['title'] for s in sections)
    duplicates = {title: count for title, count in title_counts.items() if count > 1}
    
    logger.info(f"   ✅ {len(sections)} sections ({len([s for s in sections if s['level'] == 1])} main)")
    if duplicates:
        logger.info(f"   ⚠️  {len(duplicates)} duplicate titles")
    
    return {
        'name': drug_name,
        'generic_name': generic_name,
        'metadata': metadata,
        'sections': sections,
        'zip_file': zip_path.name
    }


async def save_to_database(drug_data: Dict) -> int:
    """Save drug and sections to database"""
    
    logger.info(f"💾 Saving {drug_data['name']} to database...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if drug exists
            existing = await session.execute(
                select(DrugLabel).where(DrugLabel.name == drug_data['name'])
            )
            existing_drug = existing.scalar_one_or_none()
            
            if existing_drug:
                logger.info(f"   Found existing {drug_data['name']} (ID: {existing_drug.id})")
                
                # Delete old sections and embeddings
                await session.execute(
                    delete(DrugSection).where(DrugSection.drug_label_id == existing_drug.id)
                )
                
                # Update metadata
                existing_drug.set_id = drug_data['metadata']['set_id']
                existing_drug.version = drug_data['metadata']['version']
                existing_drug.manufacturer = drug_data['metadata']['manufacturer']
                existing_drug.generic_name = drug_data['generic_name']
                existing_drug.last_updated = datetime.utcnow()
                existing_drug.source_file = drug_data['zip_file']
                
                drug = existing_drug
            else:
                # Create new drug
                drug = DrugLabel(
                    name=drug_data['name'],
                    generic_name=drug_data['generic_name'],
                    manufacturer=drug_data['metadata']['manufacturer'],
                    set_id=drug_data['metadata']['set_id'],
                    version=drug_data['metadata']['version'],
                    is_current_version=True,
                    status="active",
                    last_updated=datetime.utcnow(),
                    source_file=drug_data['zip_file']
                )
                session.add(drug)
                await session.flush()
                logger.info(f"   Created new drug (ID: {drug.id})")
            
            # Save sections
            sections = drug_data['sections']
            section_map = {}  # Map section_number to DB ID
            
            logger.info(f"   Saving {len(sections)} sections...")
            
            # First pass: save all sections
            for section_data in sections:
                section = DrugSection(
                    drug_label_id=drug.id,
                    section_number=section_data['section_number'],
                    level=section_data['level'],
                    parent_section_id=None,
                    loinc_code=section_data.get('loinc_code'),
                    title=section_data['title'],
                    content=section_data['content'],
                    content_html=section_data.get('content_html', ''),
                    order=section_data.get('order', 0)
                )
                session.add(section)
                await session.flush()
                section_map[section_data['section_number']] = section.id
            
            # Second pass: set parent relationships
            parent_count = 0
            for section_data in sections:
                section_num = section_data['section_number']
                
                if '.' in section_num:
                    parts = section_num.split('.')
                    parent_num = '.'.join(parts[:-1])
                    
                    if parent_num in section_map:
                        section_id = section_map[section_num]
                        result = await session.execute(
                            select(DrugSection).where(DrugSection.id == section_id)
                        )
                        section = result.scalar_one()
                        section.parent_section_id = section_map[parent_num]
                        parent_count += 1
            
            await session.commit()
            
            logger.info(f"   ✅ Saved {len(sections)} sections, {parent_count} parent links")
            return drug.id
            
        except Exception as e:
            await session.rollback()
            logger.error(f"   ❌ Database error: {e}")
            raise


async def generate_embeddings(drug_id: int, drug_name: str):
    """Generate and save vector embeddings for all sections"""
    
    logger.info(f"🔮 Generating embeddings for {drug_name}...")
    
    # Initialize vector service
    vector_service = VectorService()
    vector_service.initialize()
    
    async with AsyncSessionLocal() as session:
        try:
            # Get all sections for this drug
            result = await session.execute(
                select(DrugSection).where(DrugSection.drug_label_id == drug_id)
            )
            sections = list(result.scalars().all())
            
            logger.info(f"   Processing {len(sections)} sections...")
            
            # Delete old embeddings
            for section in sections:
                await session.execute(
                    delete(SectionEmbedding).where(SectionEmbedding.section_id == section.id)
                )
            
            total_chunks = 0
            
            # Generate embeddings for each section
            for section in sections:
                # Skip empty sections
                if not section.content or len(section.content.strip()) < 50:
                    continue
                
                # Chunk the section content
                chunks = chunk_text(section.content, max_chars=2000, overlap=200)
                
                # Generate embeddings for each chunk
                for chunk_idx, chunk in enumerate(chunks):
                    # Generate embedding
                    embedding = vector_service.generate_section_embedding(
                        chunk,
                        section_title=section.title
                    )
                    
                    # Save to database
                    section_embedding = SectionEmbedding(
                        section_id=section.id,
                        chunk_index=chunk_idx,
                        chunk_text=chunk,
                        embedding=embedding.tolist(),
                        drug_name=drug_name,
                        section_loinc=section.loinc_code
                    )
                    session.add(section_embedding)
                    total_chunks += 1
            
            await session.commit()
            logger.info(f"   ✅ Generated {total_chunks} embeddings")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"   ❌ Embedding error: {e}")
            raise


async def process_all_drugs():
    """Main ETL pipeline - process all 19 drugs"""
    
    print("\n" + "="*80)
    print("🚀 COMPREHENSIVE ETL PIPELINE - ALL 19 DRUGS")
    print("="*80 + "\n")
    
    data_dir = Path(__file__).parent.parent.parent / 'data' / 'raw'
    
    # Statistics
    stats = {
        'total': len(DRUG_MAPPING),
        'success': 0,
        'failed': 0,
        'total_sections': 0,
        'total_embeddings': 0
    }
    
    start_time = datetime.now()
    
    # Process each drug
    for idx, (zip_file, (drug_name, generic_name)) in enumerate(DRUG_MAPPING.items(), 1):
        print(f"\n{'='*80}")
        print(f"📊 Processing {idx}/{len(DRUG_MAPPING)}: {drug_name}")
        print(f"{'='*80}\n")
        
        zip_path = data_dir / zip_file
        
        if not zip_path.exists():
            logger.error(f"❌ File not found: {zip_file}")
            stats['failed'] += 1
            continue
        
        try:
            # Step 1: Parse XML
            drug_data = await parse_drug(zip_path, drug_name, generic_name)
            if not drug_data:
                stats['failed'] += 1
                continue
            
            stats['total_sections'] += len(drug_data['sections'])
            
            # Step 2: Save to database
            drug_id = await save_to_database(drug_data)
            
            # Step 3: Generate embeddings
            await generate_embeddings(drug_id, drug_name)
            
            # Count embeddings
            async with AsyncSessionLocal() as session:
                count_result = await session.execute(
                    text("SELECT COUNT(*) FROM section_embeddings se JOIN drug_sections ds ON se.section_id = ds.id WHERE ds.drug_label_id = :drug_id"),
                    {"drug_id": drug_id}
                )
                embedding_count = count_result.scalar()
                stats['total_embeddings'] += embedding_count
            
            stats['success'] += 1
            logger.info(f"✅ {drug_name} complete!\n")
            
        except Exception as e:
            logger.error(f"❌ Failed to process {drug_name}: {e}")
            stats['failed'] += 1
            continue
    
    # Final summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "="*80)
    print("📊 FINAL SUMMARY")
    print("="*80)
    print(f"Total drugs: {stats['total']}")
    print(f"✅ Success: {stats['success']}")
    print(f"❌ Failed: {stats['failed']}")
    print(f"📝 Total sections: {stats['total_sections']}")
    print(f"🔮 Total embeddings: {stats['total_embeddings']}")
    print(f"⏱️  Duration: {duration:.0f} seconds ({duration/60:.1f} minutes)")
    print("="*80 + "\n")
    
    if stats['success'] == stats['total']:
        print("🎉 ALL DRUGS PROCESSED SUCCESSFULLY!")
    else:
        print(f"⚠️  {stats['failed']} drugs failed to process")
    
    print("\n✅ ETL Pipeline Complete!")
    print("   - Database updated with hierarchical sections")
    print("   - Vector embeddings generated and saved")
    print("   - RAG system ready to use")
    print(f"   - View drugs at: http://localhost:3000/\n")


if __name__ == "__main__":
    asyncio.run(process_all_drugs())
