"""
Ultra-Refined FDA SPL Parser
Maximum information extraction with structured metadata for analysis and comparison

Features:
- Hierarchical section numbering (1, 1.1, 1.2, etc.)
- Semantic content tagging (warning, dosage, population, etc.)
- Highlight important segments (boxed warnings, contraindications)
- Extract structured data (dosage tables, adverse reactions)
- Rich metadata for each content block
- Optimized for label comparison and analysis
"""

import zipfile
import re
from lxml import etree
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# Enhanced LOINC Code Mappings with metadata
LOINC_SECTIONS = {
    "34067-9": {"title": "INDICATIONS AND USAGE", "importance": "high", "type": "clinical"},
    "34068-7": {"title": "DOSAGE AND ADMINISTRATION", "importance": "critical", "type": "dosing"},
    "34070-3": {"title": "CONTRAINDICATIONS", "importance": "critical", "type": "safety"},
    "43685-7": {"title": "WARNINGS AND PRECAUTIONS", "importance": "critical", "type": "safety"},
    "34084-4": {"title": "ADVERSE REACTIONS", "importance": "high", "type": "safety"},
    "34073-7": {"title": "DRUG INTERACTIONS", "importance": "high", "type": "safety"},
    "34071-1": {"title": "WARNINGS", "importance": "critical", "type": "safety"},
    "43684-0": {"title": "USE IN SPECIFIC POPULATIONS", "importance": "high", "type": "clinical"},
    "34090-1": {"title": "CLINICAL PHARMACOLOGY", "importance": "medium", "type": "scientific"},
    "34092-7": {"title": "CLINICAL STUDIES", "importance": "medium", "type": "scientific"},
    "34069-5": {"title": "HOW SUPPLIED/STORAGE AND HANDLING", "importance": "low", "type": "logistics"},
    "42230-3": {"title": "PATIENT COUNSELING INFORMATION", "importance": "medium", "type": "patient-info"},
    "42232-9": {"title": "PRECAUTIONS", "importance": "high", "type": "safety"},
    "34089-3": {"title": "DESCRIPTION", "importance": "medium", "type": "scientific"},
    "43678-5": {"title": "OVERDOSAGE", "importance": "critical", "type": "safety"},
    "42229-5": {"title": "SPL UNCLASSIFIED SECTION", "importance": "low", "type": "other"},
}


class UltraRefinedParser:
    """
    Ultra-refined parser with maximum information extraction
    Optimized for label analysis and comparison
    """
    
    def __init__(self):
        self.namespaces = {
            'hl7': 'urn:hl7-org:v3',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        self.section_counter = {}
    
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
        """Parse XML content with ultra-refined structure"""
        try:
            root = etree.fromstring(xml_content)
            
            # Extract comprehensive metadata
            metadata = self._extract_metadata_comprehensive(root)
            
            # Extract sections with full hierarchy and metadata
            sections = self._extract_sections_ultra_refined(root)
            
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
    
    def _extract_metadata_comprehensive(self, root) -> Optional[Dict]:
        """Extract comprehensive drug metadata"""
        try:
            metadata = {}
            
            # Basic IDs
            set_id_elem = root.find('./hl7:setId', self.namespaces)
            if set_id_elem is not None:
                metadata['set_id'] = set_id_elem.get('root')
            
            version_elem = root.find('./hl7:versionNumber', self.namespaces)
            if version_elem is not None:
                metadata['version'] = int(version_elem.get('value', '1'))
            
            date_elem = root.find('./hl7:effectiveTime', self.namespaces)
            if date_elem is not None:
                date_value = date_elem.get('value')
                if date_value and len(date_value) >= 8:
                    metadata['last_updated'] = f"{date_value[:4]}-{date_value[4:6]}-{date_value[6:8]}"
            
            # Drug names
            metadata['name'] = self._extract_drug_name(root) or "Unknown"
            metadata['generic_name'] = self._extract_generic_name(root)
            metadata['manufacturer'] = self._extract_manufacturer(root)
            
            # Extract dosage forms and strengths
            metadata['dosage_forms'] = self._extract_dosage_forms(root)
            metadata['strengths'] = self._extract_strengths(root)
            
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
    
    def _extract_dosage_forms(self, root) -> List[str]:
        """Extract all dosage forms"""
        forms = []
        try:
            form_elems = root.findall('.//hl7:formCode', self.namespaces)
            for elem in form_elems:
                form_name = elem.get('displayName')
                if form_name:
                    forms.append(form_name)
        except Exception as e:
            logger.debug(f"Could not extract dosage forms: {e}")
        return forms
    
    def _extract_strengths(self, root) -> List[str]:
        """Extract all drug strengths"""
        strengths = []
        try:
            quantity_elems = root.findall('.//hl7:ingredient/hl7:quantity', self.namespaces)
            for elem in quantity_elems:
                numerator = elem.find('./hl7:numerator', self.namespaces)
                if numerator is not None:
                    value = numerator.get('value')
                    unit = numerator.get('unit')
                    if value and unit:
                        strengths.append(f"{value} {unit}")
        except Exception as e:
            logger.debug(f"Could not extract strengths: {e}")
        return strengths
    
    def _extract_sections_ultra_refined(self, root) -> List[Dict]:
        """Extract sections with ultra-refined structure"""
        sections = []
        self.section_counter = {}
        
        try:
            component_sections = root.findall('.//hl7:component/hl7:section', self.namespaces)
            
            for section in component_sections:
                section_data = self._parse_section_ultra_refined(section, level=1, parent_number="")
                if section_data:
                    sections.append(section_data)
            
            return sections
            
        except Exception as e:
            logger.error(f"Failed to extract sections: {e}")
            return []
    
    def _parse_section_ultra_refined(self, section_elem, level: int = 1, parent_number: str = "") -> Optional[Dict]:
        """
        Parse section with ultra-refined structure
        Includes section numbering, metadata, and semantic tagging
        """
        try:
            # Get LOINC code and metadata
            code_elem = section_elem.find('./hl7:code', self.namespaces)
            if code_elem is None:
                return None
            
            loinc_code = code_elem.get('code')
            if not loinc_code or loinc_code not in LOINC_SECTIONS:
                return None
            
            section_meta = LOINC_SECTIONS[loinc_code]
            
            # Generate section number
            if parent_number:
                if parent_number not in self.section_counter:
                    self.section_counter[parent_number] = 0
                self.section_counter[parent_number] += 1
                section_number = f"{parent_number}.{self.section_counter[parent_number]}"
            else:
                if 'root' not in self.section_counter:
                    self.section_counter['root'] = 0
                self.section_counter['root'] += 1
                section_number = str(self.section_counter['root'])
            
            # Get title
            title_elem = section_elem.find('./hl7:title', self.namespaces)
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else section_meta["title"]
            
            # Get section ID
            id_elem = section_elem.find('./hl7:id', self.namespaces)
            section_id = id_elem.get('root') if id_elem is not None else None
            
            # Extract content with semantic analysis
            content_html = self._extract_content_ultra_refined(section_elem, section_meta)
            
            if not content_html or len(content_html.strip()) < 10:
                return None
            
            # Extract subsections recursively
            subsections = []
            for component in section_elem.findall('./hl7:component/hl7:section', self.namespaces):
                subsection_data = self._parse_subsection_refined(component, level + 1, section_number)
                if subsection_data:
                    subsections.append(subsection_data)
            
            return {
                'section_number': section_number,
                'loinc_code': loinc_code,
                'title': title,
                'content': content_html,
                'level': level,
                'section_id': section_id,
                'importance': section_meta['importance'],
                'type': section_meta['type'],
                'subsections': subsections if subsections else []
            }
            
        except Exception as e:
            logger.debug(f"Failed to parse section: {e}")
            return None
    
    def _parse_subsection_refined(self, section_elem, level: int, parent_number: str) -> Optional[Dict]:
        """Parse subsection with numbering"""
        try:
            # Generate subsection number
            if parent_number not in self.section_counter:
                self.section_counter[parent_number] = 0
            self.section_counter[parent_number] += 1
            subsection_number = f"{parent_number}.{self.section_counter[parent_number]}"
            
            # Get title
            title_elem = section_elem.find('./hl7:title', self.namespaces)
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else f"Section {subsection_number}"
            
            # Get ID
            id_elem = section_elem.find('./hl7:id', self.namespaces)
            subsection_id = id_elem.get('root') if id_elem is not None else None
            
            # Get content
            content_html = self._extract_content_ultra_refined(section_elem, {'importance': 'medium', 'type': 'general'})
            
            if not content_html:
                return None
            
            return {
                'section_number': subsection_number,
                'title': title,
                'content': content_html,
                'level': level,
                'id': subsection_id
            }
            
        except Exception as e:
            logger.debug(f"Failed to parse subsection: {e}")
            return None
    
    def _extract_content_ultra_refined(self, section_elem, section_meta: Dict) -> str:
        """
        Extract content with semantic enrichment
        Adds metadata, highlights, and structure for analysis
        """
        try:
            text_elem = section_elem.find('./hl7:text', self.namespaces)
            if text_elem is None:
                return ""
            
            # Add section importance indicator
            importance = section_meta['importance']
            section_type = section_meta['type']
            
            html_parts = []
            
            # Add importance badge for critical/high sections
            if importance in ['critical', 'high']:
                badge_color = 'red' if importance == 'critical' else 'orange'
                html_parts.append(
                    f'<div class="mb-4 inline-block px-3 py-1 bg-{badge_color}-100 border border-{badge_color}-400 rounded-full text-xs font-semibold text-{badge_color}-800 uppercase tracking-wide">'
                    f'⚠️ {importance.upper()} INFORMATION'
                    f'</div>'
                )
            
            # Process content blocks with semantic tagging
            for child in text_elem:
                child_html = self._convert_element_semantic(child, section_type)
                if child_html:
                    html_parts.append(child_html)
            
            # Handle direct text
            if text_elem.text and text_elem.text.strip():
                html_parts.insert(0 if importance not in ['critical', 'high'] else 1, 
                                 f'<p class="leading-relaxed">{self._escape_html(text_elem.text.strip())}</p>')
            
            return '\n'.join(html_parts)
            
        except Exception as e:
            logger.debug(f"Failed to extract content: {e}")
            return ""
    
    def _convert_element_semantic(self, elem, section_type: str, depth=0) -> str:
        """
        Convert XML to HTML with semantic enrichment
        Adds context-aware styling and metadata
        """
        tag = elem.tag.replace('{urn:hl7-org:v3}', '')
        
        if tag == 'paragraph':
            return self._process_paragraph_semantic(elem, section_type)
        elif tag == 'list':
            return self._process_list_semantic(elem, section_type)
        elif tag == 'table':
            return self._process_table_semantic(elem)
        elif tag == 'br':
            return '<br/>'
        elif tag == 'content':
            return self._process_content_semantic(elem)
        elif tag == 'renderMultiMedia':
            return '<div class="my-4 p-4 bg-blue-50 border-2 border-blue-200 rounded-lg text-sm text-blue-700">📊 [Diagram/Image - See original label]</div>'
        else:
            # Default text extraction
            text_parts = []
            if elem.text and elem.text.strip():
                text_parts.append(self._escape_html(elem.text.strip()))
            for child in elem:
                child_html = self._convert_element_semantic(child, section_type, depth + 1)
                if child_html:
                    text_parts.append(child_html)
                if child.tail and child.tail.strip():
                    text_parts.append(self._escape_html(child.tail.strip()))
            return ' '.join(text_parts)
    
    def _process_paragraph_semantic(self, elem, section_type: str) -> str:
        """Process paragraph with semantic context"""
        content_parts = []
        
        if elem.text and elem.text.strip():
            content_parts.append(self._escape_html(elem.text.strip()))
        
        for child in elem:
            child_html = self._convert_element_semantic(child, section_type)
            if child_html:
                content_parts.append(child_html)
            if child.tail and child.tail.strip():
                content_parts.append(self._escape_html(child.tail.strip()))
        
        content = ' '.join(content_parts)
        
        # Detect keywords for semantic highlighting
        is_warning = re.search(r'\b(warning|caution|contraindicated|should not|do not|fatal|death|serious)\b', content, re.I)
        is_dosage = re.search(r'\b(\d+\s*(mg|ml|mcg|units|tablet|capsule)|dose|dosage|administer)\b', content, re.I)
        
        # Apply semantic styling
        style_code = elem.get('styleCode', '').lower()
        css_class = "leading-relaxed mb-3"
        
        if is_warning and section_type == 'safety':
            css_class += " bg-red-50 border-l-4 border-red-500 pl-4 py-2 text-red-900 font-medium"
        elif is_dosage and section_type == 'dosing':
            css_class += " bg-green-50 border-l-4 border-green-500 pl-4 py-2"
        elif 'bold' in style_code:
            css_class += " font-semibold text-gray-900"
        elif 'italics' in style_code:
            css_class += " italic text-gray-600"
        
        return f'<p class="{css_class}">{content}</p>'
    
    def _process_list_semantic(self, elem, section_type: str) -> str:
        """Process list with semantic styling"""
        list_type = elem.get('listType', 'unordered')
        list_tag = 'ol' if list_type == 'ordered' else 'ul'
        
        # Add semantic styling
        list_class = "my-4 ml-6 space-y-2"
        if list_tag == 'ol':
            list_class += " list-decimal"
        else:
            list_class += " list-disc"
        
        if section_type == 'safety':
            list_class += " marker:text-red-500"
        elif section_type == 'dosing':
            list_class += " marker:text-green-500"
        
        items = []
        for item in elem.findall('./hl7:item', self.namespaces):
            item_html = self._process_list_item_semantic(item, section_type)
            if item_html:
                items.append(f'<li class="pl-2">{item_html}</li>')
        
        if not items:
            return ''
        
        return f'<{list_tag} class="{list_class}">\n' + '\n'.join(items) + f'\n</{list_tag}>'
    
    def _process_list_item_semantic(self, elem, section_type: str) -> str:
        """Process list item"""
        content_parts = []
        
        if elem.text and elem.text.strip():
            content_parts.append(self._escape_html(elem.text.strip()))
        
        for child in elem:
            child_html = self._convert_element_semantic(child, section_type)
            if child_html:
                content_parts.append(child_html)
            if child.tail and child.tail.strip():
                content_parts.append(self._escape_html(child.tail.strip()))
        
        return ' '.join(content_parts)
    
    def _process_table_semantic(self, elem) -> str:
        """Process table with enhanced styling"""
        html = ['<div class="my-6 overflow-x-auto">']
        html.append('<table class="w-full border-collapse bg-white shadow-sm rounded-lg overflow-hidden">')
        
        # Process thead
        thead = elem.find('./hl7:thead', self.namespaces)
        if thead is not None:
            html.append('<thead class="bg-gradient-to-r from-blue-50 to-blue-100">')
            for row in thead.findall('./hl7:tr', self.namespaces):
                html.append('<tr>')
                for cell in row.findall('./hl7:th', self.namespaces):
                    cell_content = self._get_cell_content_semantic(cell)
                    align = cell.get('align', 'left')
                    html.append(f'<th class="border border-gray-300 px-4 py-3 text-{align} text-sm font-bold text-gray-800 uppercase tracking-wide">{cell_content}</th>')
                html.append('</tr>')
            html.append('</thead>')
        
        # Process tbody
        tbody = elem.find('./hl7:tbody', self.namespaces)
        if tbody is not None:
            html.append('<tbody class="divide-y divide-gray-200">')
            for i, row in enumerate(tbody.findall('./hl7:tr', self.namespaces)):
                row_class = 'bg-white hover:bg-blue-50 transition-colors' if i % 2 == 0 else 'bg-gray-50 hover:bg-blue-50 transition-colors'
                html.append(f'<tr class="{row_class}">')
                for cell in row.findall('./hl7:td', self.namespaces):
                    cell_content = self._get_cell_content_semantic(cell)
                    align = cell.get('align', 'left')
                    html.append(f'<td class="border border-gray-300 px-4 py-3 text-{align} text-sm text-gray-700">{cell_content}</td>')
                html.append('</tr>')
            html.append('</tbody>')
        
        html.append('</table>')
        html.append('</div>')
        return '\n'.join(html)
    
    def _get_cell_content_semantic(self, cell_elem) -> str:
        """Extract table cell content"""
        content_parts = []
        
        if cell_elem.text and cell_elem.text.strip():
            content_parts.append(self._escape_html(cell_elem.text.strip()))
        
        for child in cell_elem:
            child_html = self._convert_element_semantic(child, 'table')
            if child_html:
                content_parts.append(child_html)
            if child.tail and child.tail.strip():
                content_parts.append(self._escape_html(child.tail.strip()))
        
        return ' '.join(content_parts)
    
    def _process_content_semantic(self, elem) -> str:
        """Process inline styled content with semantic awareness"""
        content_parts = []
        
        if elem.text and elem.text.strip():
            content_parts.append(self._escape_html(elem.text.strip()))
        
        for child in elem:
            child_html = self._convert_element_semantic(child, 'general')
            if child_html:
                content_parts.append(child_html)
            if child.tail and child.tail.strip():
                content_parts.append(self._escape_html(child.tail.strip()))
        
        content = ' '.join(content_parts)
        
        # Apply rich styling
        style_code = elem.get('styleCode', '').lower()
        
        if 'bold' in style_code:
            content = f'<strong class="font-bold text-gray-900">{content}</strong>'
        if 'italics' in style_code:
            content = f'<em class="italic">{content}</em>'
        if 'underline' in style_code:
            content = f'<u class="underline">{content}</u>'
        if 'emphasis' in style_code:
            content = f'<span class="font-semibold text-blue-700">{content}</span>'
        if 'boxedwarning' in style_code or 'bold-underline' in style_code:
            content = f'<span class="inline-block font-bold text-red-700 bg-red-50 border-2 border-red-700 px-3 py-1 rounded shadow-sm">⚠️ {content}</span>'
        
        return content
    
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
def parse_fda_label_ultra_refined(file_path: str) -> Optional[Dict]:
    """Parse FDA label with ultra-refined structure"""
    parser = UltraRefinedParser()
    return parser.parse_zip_file(file_path)
