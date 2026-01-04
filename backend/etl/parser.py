"""
FDA XML Parser
Extracts structured data from FDA SPL (Structured Product Labeling) XML files
Uses LOINC codes to identify specific sections
"""

import zipfile
import io
from lxml import etree
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# LOINC Code Mappings - FDA Standard Section Identifiers
LOINC_SECTIONS = {
    "34067-9": "Indications and Usage",
    "34068-7": "Dosage and Administration",
    "34070-3": "Contraindications",
    "43685-7": "Warnings and Precautions",
    "34084-4": "Adverse Reactions",
    "34073-7": "Drug Interactions",
    "34071-1": "Warnings",
    "43684-0": "Use in Specific Populations",
    "34090-1": "Clinical Pharmacology",
    "34092-7": "Clinical Studies",
    "34069-5": "How Supplied/Storage and Handling",
    "42230-3": "Patient Counseling Information",
    "42232-9": "Precautions",
    "34089-3": "Description",
    "43678-5": "Overdosage",
    "42229-5": "SPL Unclassified Section",
}


class FDAXMLParser:
    """
    Parser for FDA SPL XML files
    Extracts metadata, sections, and clean text
    """
    
    def __init__(self):
        self.namespaces = {
            'hl7': 'urn:hl7-org:v3',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
    
    def parse_zip_file(self, zip_path: str) -> Optional[Dict]:
        """
        Parse an FDA label from a zip file
        
        Args:
            zip_path: Path to the .zip file
            
        Returns:
            Dictionary with extracted data or None if failed
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                # Find the XML file inside the zip
                xml_files = [f for f in zip_file.namelist() if f.endswith('.xml')]
                
                if not xml_files:
                    logger.error(f"No XML file found in {zip_path}")
                    return None
                
                # Use the first XML file (usually only one)
                xml_filename = xml_files[0]
                xml_content = zip_file.read(xml_filename)
                
                return self.parse_xml_content(xml_content)
                
        except Exception as e:
            logger.error(f"Failed to parse zip file {zip_path}: {e}")
            return None
    
    def parse_xml_content(self, xml_content: bytes) -> Optional[Dict]:
        """
        Parse XML content and extract structured data
        
        Args:
            xml_content: Raw XML bytes
            
        Returns:
            Dictionary with metadata and sections
        """
        try:
            # Parse XML
            root = etree.fromstring(xml_content)
            
            # Extract metadata
            metadata = self._extract_metadata(root)
            
            # Extract sections
            sections = self._extract_sections(root)
            
            if not metadata or not sections:
                logger.warning("Failed to extract metadata or sections")
                return None
            
            return {
                'metadata': metadata,
                'sections': sections
            }
            
        except Exception as e:
            logger.error(f"Failed to parse XML content: {e}")
            return None
    
    def _extract_metadata(self, root) -> Optional[Dict]:
        """
        Extract drug metadata from XML
        
        Returns:
            Dict with set_id, name, manufacturer, etc.
        """
        try:
            metadata = {}
            
            # Set ID (unique FDA identifier)
            set_id_elem = root.find('.//hl7:setId', self.namespaces)
            if set_id_elem is not None:
                metadata['set_id'] = set_id_elem.get('root', '')
            
            # Version Number
            version_elem = root.find('.//hl7:versionNumber', self.namespaces)
            if version_elem is not None:
                version_value = version_elem.get('value', '1')
                try:
                    metadata['version'] = int(version_value)
                except ValueError:
                    metadata['version'] = 1
            else:
                metadata['version'] = 1
            
            # Effective Time (Last Updated)
            effective_elem = root.find('.//hl7:effectiveTime', self.namespaces)
            if effective_elem is not None:
                metadata['effective_time'] = effective_elem.get('value', '')
            
            # Drug Name (from title)
            title_elem = root.find('.//hl7:title', self.namespaces)
            if title_elem is not None and title_elem.text:
                # Clean up the title
                drug_name = title_elem.text.strip()
                # Remove common suffixes
                drug_name = drug_name.replace(' - ', ' ').split(' (')[0]
                metadata['name'] = drug_name
            
            # Generic Name (active ingredient)
            generic_name = self._extract_generic_name(root)
            if generic_name:
                metadata['generic_name'] = generic_name
            
            # Manufacturer
            manufacturer = self._extract_manufacturer(root)
            if manufacturer:
                metadata['manufacturer'] = manufacturer
            
            logger.info(f"Extracted metadata for: {metadata.get('name', 'Unknown')}")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to extract metadata: {e}")
            return None
    
    def _extract_generic_name(self, root) -> Optional[str]:
        """Extract generic/active ingredient name"""
        try:
            # Look for active ingredient
            ingredient_elem = root.find('.//hl7:activeIngredient/hl7:name', self.namespaces)
            if ingredient_elem is not None and ingredient_elem.text:
                return ingredient_elem.text.strip()
            
            # Alternative: look in ingredient section
            moiety_elem = root.find('.//hl7:activeMoiety/hl7:name', self.namespaces)
            if moiety_elem is not None and moiety_elem.text:
                return moiety_elem.text.strip()
                
        except Exception as e:
            logger.debug(f"Could not extract generic name: {e}")
        
        return None
    
    def _extract_manufacturer(self, root) -> Optional[str]:
        """Extract manufacturer/company name"""
        try:
            # Look for manufacturer name
            manu_elem = root.find('.//hl7:author/hl7:assignedEntity/hl7:representedOrganization/hl7:name', 
                                  self.namespaces)
            if manu_elem is not None and manu_elem.text:
                return manu_elem.text.strip()
            
            # Alternative path
            manu_elem2 = root.find('.//hl7:manufacturerOrganization/hl7:name', self.namespaces)
            if manu_elem2 is not None and manu_elem2.text:
                return manu_elem2.text.strip()
                
        except Exception as e:
            logger.debug(f"Could not extract manufacturer: {e}")
        
        return "Unknown Manufacturer"
    
    def _extract_sections(self, root) -> List[Dict]:
        """
        Extract all labeled sections using LOINC codes
        
        Returns:
            List of section dictionaries with loinc_code, title, content
        """
        sections = []
        order = 0
        
        try:
            # Find all component sections
            component_sections = root.findall('.//hl7:component/hl7:section', self.namespaces)
            
            for section in component_sections:
                section_data = self._parse_section(section, order)
                if section_data:
                    sections.append(section_data)
                    order += 1
            
            logger.info(f"Extracted {len(sections)} sections")
            return sections
            
        except Exception as e:
            logger.error(f"Failed to extract sections: {e}")
            return []
    
    def _parse_section(self, section_elem, order: int) -> Optional[Dict]:
        """
        Parse a single section element
        
        Returns:
            Dict with loinc_code, title, content, order
        """
        try:
            # Get LOINC code
            code_elem = section_elem.find('.//hl7:code', self.namespaces)
            if code_elem is None:
                return None
            
            loinc_code = code_elem.get('code', '')
            
            # Only process known LOINC codes
            if loinc_code not in LOINC_SECTIONS:
                return None
            
            # Get title
            title_elem = section_elem.find('./hl7:title', self.namespaces)
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else LOINC_SECTIONS[loinc_code]
            
            # Extract text content
            content = self._extract_text_content(section_elem)
            
            if not content or len(content.strip()) < 10:
                return None
            
            return {
                'loinc_code': loinc_code,
                'title': title,
                'content': content,
                'order': order
            }
            
        except Exception as e:
            logger.debug(f"Failed to parse section: {e}")
            return None
    
    def _extract_text_content(self, section_elem) -> str:
        """
        Extract clean text from a section, removing XML tags
        Handles nested sections and tables
        """
        text_parts = []
        
        try:
            # Find all text elements
            text_elems = section_elem.findall('.//hl7:text', self.namespaces)
            
            for text_elem in text_elems:
                # Get all text content, including nested elements
                text = self._get_element_text(text_elem)
                if text:
                    text_parts.append(text)
            
            # Join with double newline for readability
            content = '\n\n'.join(text_parts)
            
            # Clean up whitespace
            content = self._clean_text(content)
            
            return content
            
        except Exception as e:
            logger.debug(f"Failed to extract text content: {e}")
            return ""
    
    def _get_element_text(self, elem) -> str:
        """
        Recursively extract all text from an element and its children
        """
        text_parts = []
        
        # Get direct text
        if elem.text:
            text_parts.append(elem.text.strip())
        
        # Get text from children
        for child in elem:
            child_text = self._get_element_text(child)
            if child_text:
                text_parts.append(child_text)
            
            # Get tail text (text after child element)
            if child.tail:
                text_parts.append(child.tail.strip())
        
        return ' '.join(text_parts)
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        """
        if not text:
            return ""
        
        # Replace multiple spaces with single space
        text = ' '.join(text.split())
        
        # Replace multiple newlines with double newline
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n\n'.join(lines)
        
        return text.strip()


# Convenience function
def parse_fda_label(file_path: str) -> Optional[Dict]:
    """
    Quick function to parse an FDA label file
    
    Args:
        file_path: Path to .zip file
        
    Returns:
        Parsed data dictionary or None
    """
    parser = FDAXMLParser()
    return parser.parse_zip_file(file_path)
