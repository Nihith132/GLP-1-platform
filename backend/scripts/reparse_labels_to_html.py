"""
Script to re-parse all existing drug labels to generate HTML content
Preserves XML structure instead of plain text
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.db_session import get_db_sync
from etl.parser import FDAXMLParser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reparse_all_labels():
    """Re-parse all drug labels to generate HTML content"""
    
    db = next(get_db_sync())
    parser = FDAXMLParser()
    
    try:
        # Get all drugs with their source files
        drugs = db.execute("""
            SELECT id, name, source_file 
            FROM drugs 
            WHERE source_file IS NOT NULL
            ORDER BY id
        """).fetchall()
        
        logger.info(f"Found {len(drugs)} drugs to reparse")
        
        for drug_id, drug_name, source_file in drugs:
            logger.info(f"Reparsing {drug_name} (ID: {drug_id})")
            
            # Find the source file
            file_path = Path("/Users/nihithreddy/slickbit label analyzer/data/raw") / source_file
            
            if not file_path.exists():
                logger.warning(f"  ✗ Source file not found: {file_path}")
                continue
            
            # Parse the file
            parsed_data = parser.parse_zip_file(str(file_path))
            
            if not parsed_data or 'sections' not in parsed_data:
                logger.warning(f"  ✗ Failed to parse file")
                continue
            
            # Update sections in database
            sections_updated = 0
            for section_data in parsed_data['sections']:
                loinc_code = section_data['loinc_code']
                new_content = section_data['content']
                
                result = db.execute("""
                    UPDATE sections 
                    SET content = %s
                    WHERE drug_id = %s AND loinc_code = %s
                """, (new_content, drug_id, loinc_code))
                
                sections_updated += result.rowcount
            
            db.commit()
            logger.info(f"  ✓ Updated {sections_updated} sections")
        
        logger.info("✓ All labels reparsed successfully!")
        
    except Exception as e:
        logger.error(f"✗ Error reparsing labels: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    reparse_all_labels()
