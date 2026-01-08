"""
Enhanced FDA SPL XML Parser
Preserves full document structure with hierarchical sections, styling, and metadata
Follows SPL specification for rich label representation
"""

import zipfile
from lxml import etree
from typing import Dict, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# LOINC Code Mappings - FDA Standard Section Identifiers
LOINC_SECTIONS = {
    "34067-9": "INDICATIONS AND USAGE",
    "34068-7": "DOSAGE AND ADMINISTRATION",
    "34070-3": "CONTRAINDICATIONS",
    "43685-7": "WARNINGS AND PRECAUTIONS",
    "34084-4": "ADVERSE REACTIONS",
    "34073-7": "DRUG INTERACTIONS",
    "34071-1": "WARNINGS",
    "43684-0": "USE IN SPECIFIC POPULATIONS",
    "34090-1": "CLINICAL PHARMACOLOGY",
    "34092-7": "CLINICAL STUDIES",
    "34069-5": "HOW SUPPLIED/STORAGE AND HANDLING",
    "42230-3": "PATIENT COUNSELING INFORMATION",
    "42232-9": "PRECAUTIONS",
    "34089-3": "DESCRIPTION",
    "43678-5": "OVERDOSAGE",
    "42229-5": "SPL UNCLASSIFIED SECTION",
}


class EnhancedFDAParser:
    """
    Enhanced parser that preserves full SPL document structure
    Creates rich HTML with proper hierarchy, styling, and metadata
    """
    
    def __init__(self):
        self.namespaces = {
            'hl7': 'urn:hl7-org:v3',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
    
    def parse_zip_file(self, zip_path: str) -> Optional[Dict]:
        """Parse an FDA label from a zip file"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                xml_files = [f for f in zip_file.namelist() if f.endswith('.xml')]
                
                if not xml_files:
                    logger.error(f"No XML file found in {zip_path}")
                    return None
                
                xml_content = zip_file.read(xml_files[0])
                return self.parse_xml_content(xml_content)
                
        except Exception as e:
            logger.error(f"Failed to parse zip file {zip_path}: {e}")
            return None
    
    def parse_xml_content(self, xml_content: bytes) -> Optional[Dict]:
        """Parse XML content and extract structured data"""
        try:
            root = etree.fromstring(xml_content)
            
            # Extract metadata
            metadata = self._extract_metadata(root)
            
            # Extract sections with full structure
            sections = self._extract_sections_enhanced(root)
            
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
        """Extract drug metadata"""
        try:
            metadata = {}
            
            # SET ID (unique identifier)
            set_id_elem = root.find('./hl7:setId', self.namespaces)
            if set_id_elem is not None:
                metadata['set_id'] = set_id_elem.get('root')
            
            # Version
            version_elem = root.find('./hl7:versionNumber', self.namespaces)
            if version_elem is not None:
                metadata['version'] = int(version_elem.get('value', '1'))
            
            # Effective Time (last updated)
            date_elem = root.find('./hl7:effectiveTime', self.namespaces)
            if date_elem is not None:
                date_value = date_elem.get('value')
                if date_value and len(date_value) >= 8:
                    metadata['last_updated'] = f"{date_value[:4]}-{date_value[4:6]}-{date_value[6:8]}"
            
            # Drug Name
            metadata['name'] = self._extract_drug_name(root) or "Unknown"
            
            # Generic Name
            metadata['generic_name'] = self._extract_generic_name(root)
            
            # Manufacturer
            metadata['manufacturer'] = self._extract_manufacturer(root)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to extract metadata: {e}")
            return None
    
    def _extract_drug_name(self, root) -> Optional[str]:
        """Extract drug brand name"""
        try:
            name_elem = root.find('.//hl7:manufacturedProduct/hl7:manufacturedProduct/hl7:name', self.namespaces)
            if name_elem is not None and name_elem.text:
                return name_elem.text.strip()
        except Exception as e:
            logger.debug(f"Could not extract drug name: {e}")
        return None
    
    def _extract_generic_name(self, root) -> Optional[str]:
        """Extract generic/active ingredient name"""
        try:
            ingredient_elem = root.find('.//hl7:activeIngredient/hl7:name', self.namespaces)
            if ingredient_elem is not None and ingredient_elem.text:
                return ingredient_elem.text.strip()
        except Exception as e:
            logger.debug(f"Could not extract generic name: {e}")
        return None
    
    def _extract_manufacturer(self, root) -> Optional[str]:
        """Extract manufacturer name"""
        try:
            manu_elem = root.find('.//hl7:author/hl7:assignedEntity/hl7:representedOrganization/hl7:name', self.namespaces)
            if manu_elem is not None and manu_elem.text:
                return manu_elem.text.strip()
        except Exception as e:
            logger.debug(f"Could not extract manufacturer: {e}")
        return "Unknown Manufacturer"
    
    def _extract_sections_enhanced(self, root) -> List[Dict]:
        """
        Extract all sections with full hierarchical structure
        Preserves subsections, formatting, tables, lists, etc.
        """
        sections = []
        order = 0
        
        try:
            # Find all top-level component sections
            component_sections = root.findall('.//hl7:component/hl7:section', self.namespaces)
            
            for section in component_sections:
                section_data = self._parse_section_enhanced(section, order)
                if section_data:
                    sections.append(section_data)
                    order += 1
            
            return sections
            
        except Exception as e:
            logger.error(f"Failed to extract sections: {e}")
            return []
    
    def _parse_section_enhanced(self, section_elem, order: int) -> Optional[Dict]:
        """
        Parse a section with full structure preservation
        Returns section with subsections, metadata, and rich HTML content
        """
        try:
            # Get LOINC code
            code_elem = section_elem.find('./hl7:code', self.namespaces)
            if code_elem is None:
                return None
            
            loinc_code = code_elem.get('code')
            if not loinc_code or loinc_code not in LOINC_SECTIONS:
                return None
            
            # Get title
            title_elem = section_elem.find('./hl7:title', self.namespaces)
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else LOINC_SECTIONS[loinc_code]
            
            # Get section ID for reference
            id_elem = section_elem.find('./hl7:id', self.namespaces)
            section_id = id_elem.get('root') if id_elem is not None else None
            
            # Extract content with full structure
            content_html = self._extract_section_content_enhanced(section_elem)
            
            if not content_html or len(content_html.strip()) < 10:
                return None
            
            # Extract subsections (nested components)
            subsections = []
            for component in section_elem.findall('./hl7:component/hl7:section', self.namespaces):
                subsection_data = self._parse_subsection(component)
                if subsection_data:
                    subsections.append(subsection_data)
            
            return {
                'loinc_code': loinc_code,
                'title': title,
                'content': content_html,
                'order': order,
                'section_id': section_id,
                'subsections': subsections if subsections else None
            }
            
        except Exception as e:
            logger.debug(f"Failed to parse section: {e}")
            return None
    
    def _parse_subsection(self, section_elem) -> Optional[Dict]:
        """Parse a nested subsection"""
        try:
            # Get title
            title_elem = section_elem.find('./hl7:title', self.namespaces)
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else "Subsection"
            
            # Get ID
            id_elem = section_elem.find('./hl7:id', self.namespaces)
            subsection_id = id_elem.get('root') if id_elem is not None else None
            
            # Get content
            content_html = self._extract_section_content_enhanced(section_elem)
            
            if not content_html:
                return None
            
            return {
                'id': subsection_id,
                'title': title,
                'content': content_html
            }
            
        except Exception as e:
            logger.debug(f"Failed to parse subsection: {e}")
            return None
    
    def _extract_section_content_enhanced(self, section_elem) -> str:
        """
        Extract section content with full HTML structure
        Preserves all formatting, lists, tables, highlights, etc.
        """
        try:
            # Find text element
            text_elem = section_elem.find('./hl7:text', self.namespaces)
            if text_elem is None:
                return ""
            
            # Convert to rich HTML
            html_parts = []
            
            # Process all children recursively
            for child in text_elem:
                child_html = self._convert_element_to_html(child)
                if child_html:
                    html_parts.append(child_html)
            
            # Handle direct text content
            if text_elem.text and text_elem.text.strip():
                html_parts.insert(0, f'<p>{self._escape_html(text_elem.text.strip())}</p>')
            
            return '\n'.join(html_parts)
            
        except Exception as e:
            logger.debug(f"Failed to extract section content: {e}")
            return ""
    
    def _convert_element_to_html(self, elem, depth=0) -> str:
        """
        Recursively convert SPL XML elements to semantic HTML
        Handles paragraphs, lists, tables, content styling, etc.
        """
        tag = elem.tag.replace('{urn:hl7-org:v3}', '')
        
        # Paragraph
        if tag == 'paragraph':
            return self._process_paragraph(elem)
        
        # Lists
        elif tag == 'list':
            return self._process_list(elem)
        
        # Tables
        elif tag == 'table':
            return self._process_table(elem)
        
        # Line break
        elif tag == 'br':
            return '<br/>'
        
        # Styled content (inline)
        elif tag == 'content':
            return self._process_content(elem)
        
        # Rendered multimedia (images)
        elif tag == 'renderMultiMedia':
            return self._process_multimedia(elem)
        
        # Default: extract text recursively
        else:
            text_parts = []
            if elem.text:
                text_parts.append(self._escape_html(elem.text.strip()))
            for child in elem:
                child_html = self._convert_element_to_html(child, depth + 1)
                if child_html:
                    text_parts.append(child_html)
                if child.tail:
                    text_parts.append(self._escape_html(child.tail.strip()))
            return ' '.join(text_parts)
    
    def _process_paragraph(self, elem) -> str:
        """Convert paragraph to HTML <p> tag"""
        content_parts = []
        
        if elem.text and elem.text.strip():
            content_parts.append(self._escape_html(elem.text.strip()))
        
        for child in elem:
            child_html = self._convert_element_to_html(child)
            if child_html:
                content_parts.append(child_html)
            if child.tail and child.tail.strip():
                content_parts.append(self._escape_html(child.tail.strip()))
        
        content = ' '.join(content_parts)
        
        # Check for special paragraph styles (caption, footnote, etc.)
        style_code = elem.get('styleCode', '')
        
        if 'italics' in style_code.lower():
            return f'<p class="italic text-gray-600">{content}</p>'
        elif 'bold' in style_code.lower():
            return f'<p class="font-semibold">{content}</p>'
        else:
            return f'<p>{content}</p>'
    
    def _process_list(self, elem) -> str:
        """Convert list to HTML <ul> or <ol>"""
        list_type = elem.get('listType', 'unordered')
        list_tag = 'ol' if list_type == 'ordered' else 'ul'
        
        items = []
        for item in elem.findall('./hl7:item', self.namespaces):
            item_html = self._process_list_item(item)
            if item_html:
                items.append(f'<li>{item_html}</li>')
        
        if not items:
            return ''
        
        return f'<{list_tag} class="list-item">\n' + '\n'.join(items) + f'\n</{list_tag}>'
    
    def _process_list_item(self, elem) -> str:
        """Process list item content"""
        content_parts = []
        
        if elem.text and elem.text.strip():
            content_parts.append(self._escape_html(elem.text.strip()))
        
        for child in elem:
            child_html = self._convert_element_to_html(child)
            if child_html:
                content_parts.append(child_html)
            if child.tail and child.tail.strip():
                content_parts.append(self._escape_html(child.tail.strip()))
        
        return ' '.join(content_parts)
    
    def _process_table(self, elem) -> str:
        """Convert SPL table to HTML table with proper styling"""
        html = ['<table class="w-full border-collapse my-4">']
        
        # Process thead
        thead = elem.find('./hl7:thead', self.namespaces)
        if thead is not None:
            html.append('<thead class="bg-gray-50">')
            for row in thead.findall('./hl7:tr', self.namespaces):
                html.append('<tr>')
                for cell in row.findall('./hl7:th', self.namespaces):
                    cell_content = self._get_cell_content(cell)
                    align = cell.get('align', 'left')
                    html.append(f'<th class="border border-gray-300 px-4 py-2 text-{align} text-sm font-semibold text-gray-700">{cell_content}</th>')
                html.append('</tr>')
            html.append('</thead>')
        
        # Process tbody
        tbody = elem.find('./hl7:tbody', self.namespaces)
        if tbody is not None:
            html.append('<tbody>')
            for row in tbody.findall('./hl7:tr', self.namespaces):
                html.append('<tr class="hover:bg-gray-50">')
                for cell in row.findall('./hl7:td', self.namespaces):
                    cell_content = self._get_cell_content(cell)
                    align = cell.get('align', 'left')
                    html.append(f'<td class="border border-gray-300 px-4 py-2 text-{align} text-sm text-gray-600">{cell_content}</td>')
                html.append('</tr>')
            html.append('</tbody>')
        
        html.append('</table>')
        return '\n'.join(html)
    
    def _get_cell_content(self, cell_elem) -> str:
        """Extract content from table cell"""
        content_parts = []
        
        if cell_elem.text and cell_elem.text.strip():
            content_parts.append(self._escape_html(cell_elem.text.strip()))
        
        for child in cell_elem:
            child_html = self._convert_element_to_html(child)
            if child_html:
                content_parts.append(child_html)
            if child.tail and child.tail.strip():
                content_parts.append(self._escape_html(child.tail.strip()))
        
        return ' '.join(content_parts)
    
    def _process_content(self, elem) -> str:
        """Process inline styled content (bold, italics, underline, etc.)"""
        content_parts = []
        
        if elem.text and elem.text.strip():
            content_parts.append(self._escape_html(elem.text.strip()))
        
        for child in elem:
            child_html = self._convert_element_to_html(child)
            if child_html:
                content_parts.append(child_html)
            if child.tail and child.tail.strip():
                content_parts.append(self._escape_html(child.tail.strip()))
        
        content = ' '.join(content_parts)
        
        # Apply styling based on styleCode
        style_code = elem.get('styleCode', '').lower()
        
        if 'bold' in style_code:
            content = f'<strong>{content}</strong>'
        if 'italics' in style_code:
            content = f'<em>{content}</em>'
        if 'underline' in style_code:
            content = f'<u>{content}</u>'
        
        # Handle highlights/emphasis
        if 'emphasis' in style_code:
            content = f'<span class="font-semibold text-gray-900">{content}</span>'
        
        # Handle warnings/boxed warnings
        if 'boxedwarning' in style_code or 'bold-underline' in style_code:
            content = f'<span class="font-bold text-red-700 border-2 border-red-700 px-2 py-1 inline-block">{content}</span>'
        
        return content
    
    def _process_multimedia(self, elem) -> str:
        """Process multimedia elements (images, diagrams)"""
        # For now, return a placeholder
        # In production, you'd extract the image reference and include it
        return '<div class="my-4 p-4 bg-gray-50 border border-gray-200 rounded text-sm text-gray-500">[Image/Diagram]</div>'
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        if not text:
            return ""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))


# Convenience function
def parse_fda_label_enhanced(file_path: str) -> Optional[Dict]:
    """Quick function to parse an FDA label file with enhanced structure"""
    parser = EnhancedFDAParser()
    return parser.parse_zip_file(file_path)
