"""
ETL Builder - Orchestrates the complete ETL pipeline
Extract → Transform → Load

Process:
1. Parse FDA XML file
2. Extract medical entities (NER)
3. Generate vector embeddings
4. Save to database (drug_labels, drug_sections, section_embeddings)
"""

from typing import Dict, Optional, List
from datetime import datetime
import logging
from pathlib import Path

from backend.etl.parser import FDAXMLParser
from backend.etl.ner import get_ner_service
from backend.etl.vector_service import get_vector_service
from backend.models.database import DrugLabel, DrugSection, SectionEmbedding, ProcessingLog
from backend.models.db_session import AsyncSessionLocal
from sqlalchemy import select

logger = logging.getLogger(__name__)


class ETLBuilder:
    """
    Orchestrates the complete ETL pipeline for FDA drug labels
    """
    
    def __init__(self):
        self.parser = FDAXMLParser()
        self.ner_service = get_ner_service()
        self.vector_service = get_vector_service()
    
    async def process_fda_label(
        self, 
        file_path: str, 
        source_filename: str = None
    ) -> Optional[int]:
        """
        Process a single FDA label file through the complete ETL pipeline
        
        Args:
            file_path: Path to the .zip file
            source_filename: Optional source filename for tracking
            
        Returns:
            Drug label ID if successful, None if failed
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting ETL for: {file_path}")
            
            # STEP 1: EXTRACT - Parse XML
            logger.info("Step 1/4: Parsing XML...")
            parsed_data = self.parser.parse_zip_file(file_path)
            
            if not parsed_data:
                logger.error("Failed to parse XML file")
                await self._log_failure(source_filename, "Parse failed")
                return None
            
            metadata = parsed_data['metadata']
            sections = parsed_data['sections']
            
            logger.info(f"✅ Parsed: {metadata.get('name')} with {len(sections)} sections")
            
            # STEP 2: TRANSFORM - Extract entities with NER
            logger.info("Step 2/4: Extracting medical entities...")
            sections_with_entities = await self._extract_entities(sections)
            logger.info(f"✅ Extracted entities from {len(sections_with_entities)} sections")
            
            # STEP 3: TRANSFORM - Generate embeddings
            logger.info("Step 3/4: Generating vector embeddings...")
            label_embedding, section_embeddings = await self._generate_embeddings(
                metadata, sections_with_entities
            )
            logger.info(f"✅ Generated 1 label embedding + {len(section_embeddings)} section embeddings")
            
            # STEP 4: LOAD - Save to database
            logger.info("Step 4/4: Saving to database...")
            drug_label_id = await self._save_to_database(
                metadata=metadata,
                sections=sections_with_entities,
                label_embedding=label_embedding,
                section_embeddings=section_embeddings,
                source_file=source_filename or file_path
            )
            
            if drug_label_id:
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                logger.info(f"✅ ETL complete! Drug label ID: {drug_label_id} ({elapsed:.2f}s)")
                await self._log_success(source_filename, drug_label_id, elapsed)
                return drug_label_id
            else:
                logger.error("Failed to save to database")
                await self._log_failure(source_filename, "Database save failed")
                return None
                
        except Exception as e:
            logger.error(f"ETL pipeline failed: {e}", exc_info=True)
            await self._log_failure(source_filename, str(e))
            return None
    
    async def _extract_entities(self, sections: List[Dict]) -> List[Dict]:
        """
        Extract medical entities from all sections using NER
        
        Returns:
            Sections with added 'entities' field
        """
        sections_with_entities = []
        
        for section in sections:
            # Extract entities for this section
            entities = self.ner_service.extract_entities(
                text=section['content'],
                section_type=section['loinc_code']
            )
            
            # Convert numpy types to Python native types for JSON serialization
            entities_json_safe = []
            for entity in entities:
                entity_safe = entity.copy()
                # Convert numpy.float32 to Python float
                if 'confidence' in entity_safe:
                    entity_safe['confidence'] = float(entity_safe['confidence'])
                entities_json_safe.append(entity_safe)
            
            # Add entities to section data
            section_data = section.copy()
            section_data['entities'] = entities_json_safe
            sections_with_entities.append(section_data)
        
        return sections_with_entities
    
    async def _generate_embeddings(
        self, 
        metadata: Dict, 
        sections: List[Dict]
    ) -> tuple:
        """
        Generate both label-level and section-level embeddings
        
        Returns:
            (label_embedding, list of section_embeddings)
        """
        # 1. Label-level embedding (for dashboard search)
        # Find indications section for summary
        indications_section = next(
            (s for s in sections if s['loinc_code'] == '34067-9'),
            None
        )
        
        drug_data = {
            'name': metadata.get('name'),
            'generic_name': metadata.get('generic_name'),
            'manufacturer': metadata.get('manufacturer'),
            'indications': indications_section['content'][:1000] if indications_section else None
        }
        
        label_embedding = self.vector_service.generate_label_embedding(drug_data)
        
        # 2. Section-level embeddings (for RAG chatbot)
        section_texts = [
            f"{s['title']}: {s['content'][:2000]}"
            for s in sections
        ]
        
        section_embeddings = self.vector_service.generate_batch_embeddings(section_texts)
        
        return label_embedding, section_embeddings
    
    async def _save_to_database(
        self,
        metadata: Dict,
        sections: List[Dict],
        label_embedding,
        section_embeddings,
        source_file: str
    ) -> Optional[int]:
        """
        Save all data to PostgreSQL database
        
        Order:
        1. drug_labels (parent)
        2. drug_sections (children)
        3. section_embeddings (grandchildren)
        
        Returns:
            Drug label ID if successful
        """
        async with AsyncSessionLocal() as session:
            try:
                # **DUPLICATE CHECK**: Check if this drug label already exists
                set_id = metadata.get('set_id')
                version = metadata.get('version', 1)
                
                existing_label = await session.execute(
                    select(DrugLabel).where(
                        DrugLabel.set_id == set_id,
                        DrugLabel.version == version
                    )
                )
                existing = existing_label.scalar_one_or_none()
                
                if existing:
                    logger.warning(f"⚠️  Drug label already exists: {existing.name} (SET_ID: {set_id}, Version: {version})")
                    logger.warning(f"   Skipping to avoid duplicate. Existing ID: {existing.id}")
                    return existing.id  # Return existing ID instead of creating duplicate
                
                # Calculate NER summary
                all_entities = []
                for section in sections:
                    all_entities.extend(section.get('entities', []))
                
                ner_summary = self.ner_service.summarize_entities(all_entities)
                
                # Convert effectiveTime to datetime
                effective_time_str = metadata.get('effective_time', '')
                last_updated_date = None
                if effective_time_str:
                    try:
                        # Parse FDA date format: YYYYMMDD
                        from datetime import datetime
                        last_updated_date = datetime.strptime(effective_time_str, '%Y%m%d')
                    except ValueError:
                        logger.warning(f"Could not parse effective_time: {effective_time_str}")
                
                # 1. Create DrugLabel record
                drug_label = DrugLabel(
                    set_id=metadata.get('set_id'),
                    version=metadata.get('version', 1),
                    name=metadata.get('name'),
                    generic_name=metadata.get('generic_name'),
                    manufacturer=metadata.get('manufacturer'),
                    is_current_version=True,
                    status='active',
                    last_updated=last_updated_date,  # FDA publication date
                    ner_summary=ner_summary,
                    label_embedding=label_embedding.tolist(),  # Convert numpy to list
                    source_file=source_file
                )
                
                session.add(drug_label)
                await session.flush()  # Get the ID without committing
                
                logger.debug(f"Created drug_label: {drug_label.name} (ID: {drug_label.id})")
                
                # 2. Create DrugSection records
                drug_sections = []
                for i, section in enumerate(sections):
                    drug_section = DrugSection(
                        drug_label_id=drug_label.id,
                        loinc_code=section['loinc_code'],
                        title=section['title'],
                        order=section['order'],
                        content=section['content'],
                        ner_entities=section.get('entities', [])  # Store as JSONB
                    )
                    session.add(drug_section)
                    drug_sections.append(drug_section)
                
                await session.flush()  # Get section IDs
                
                logger.debug(f"Created {len(drug_sections)} drug_sections")
                
                # 3. Create SectionEmbedding records
                for i, drug_section in enumerate(drug_sections):
                    section_embedding = SectionEmbedding(
                        section_id=drug_section.id,
                        chunk_index=i,  # Sequential index based on section order
                        chunk_text=drug_section.content[:2000],  # Store text used for embedding
                        embedding=section_embeddings[i].tolist(),  # Convert numpy to list
                        drug_name=drug_label.name,
                        section_loinc=drug_section.loinc_code
                    )
                    session.add(section_embedding)
                
                logger.debug(f"Created {len(section_embeddings)} section_embeddings")
                
                # Commit all changes
                await session.commit()
                
                logger.info(f"💾 Saved to database: {drug_label.name} (ID: {drug_label.id})")
                return drug_label.id
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Database save failed: {e}", exc_info=True)
                return None
    
    async def _log_success(self, filename: str, drug_label_id: int, elapsed_seconds: float):
        """Log successful processing"""
        async with AsyncSessionLocal() as session:
            try:
                import uuid
                log = ProcessingLog(
                    job_id=str(uuid.uuid4()),
                    source_file=filename,
                    drug_name=filename,  # Will be improved later
                    stage='complete',
                    status='completed',
                    progress_percent=100.0,
                    completed_at=datetime.utcnow()
                )
                session.add(log)
                await session.commit()
            except Exception as e:
                logger.warning(f"Failed to log success: {e}")
    
    async def _log_failure(self, filename: str, error_message: str):
        """Log failed processing"""
        async with AsyncSessionLocal() as session:
            try:
                import uuid
                log = ProcessingLog(
                    job_id=str(uuid.uuid4()),
                    source_file=filename,
                    stage='failed',
                    status='failed',
                    error_message=error_message,
                    completed_at=datetime.utcnow()
                )
                session.add(log)
                await session.commit()
            except Exception as e:
                logger.warning(f"Failed to log failure: {e}")
    
    async def process_batch(self, file_paths: List[str]) -> Dict[str, int]:
        """
        Process multiple FDA label files
        
        Returns:
            Dict with success/failure counts
        """
        results = {
            'success': 0,
            'failed': 0,
            'drug_label_ids': []
        }
        
        for file_path in file_paths:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing: {Path(file_path).name}")
            logger.info(f"{'='*60}")
            
            drug_label_id = await self.process_fda_label(file_path, Path(file_path).name)
            
            if drug_label_id:
                results['success'] += 1
                results['drug_label_ids'].append(drug_label_id)
            else:
                results['failed'] += 1
        
        logger.info(f"\n{'='*60}")
        logger.info(f"BATCH COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"✅ Success: {results['success']}")
        logger.info(f"❌ Failed: {results['failed']}")
        logger.info(f"{'='*60}\n")
        
        return results


# Convenience function
async def process_fda_label(file_path: str) -> Optional[int]:
    """
    Quick function to process a single FDA label
    
    Args:
        file_path: Path to .zip file
        
    Returns:
        Drug label ID if successful
    """
    builder = ETLBuilder()
    return await builder.process_fda_label(file_path)
