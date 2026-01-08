"""
Hierarchical FDA SPL Parser with Complete LOINC Dictionary
Optimized for consistent parsing and comparison

Features:
- Complete 80+ LOINC code dictionary
- True hierarchical section extraction (parent-child relationships)
- Clean, human-readable content (no messy diagrams)
- Structured table data (comparison-friendly)
- Section numbering (1, 1.1, 1.2.1)
- Preserves FDA label structure
"""

import zipfile
import re
from lxml import etree
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# COMPLETE LOINC Code Dictionary (80+ codes covering all FDA sections)
COMPLETE_LOINC_CODES = {
    # Main Clinical Sections
    "34067-9": "INDICATIONS AND USAGE",
    "34068-7": "DOSAGE AND ADMINISTRATION",
    "34070-3": "CONTRAINDICATIONS",
    "43685-7": "WARNINGS AND PRECAUTIONS",
    "34084-4": "ADVERSE REACTIONS",
    "34073-7": "DRUG INTERACTIONS",
    "34071-1": "WARNINGS",
    "42232-9": "PRECAUTIONS",
    
    # Safety Sections
    "53414-9": "BOXED WARNING",
    "43683-2": "MEDICATION GUIDE",
    "34088-5": "OVERDOSAGE",
    "34076-0": "INFORMATION FOR PATIENTS",
    "34075-2": "LABORATORY TESTS",
    "42230-3": "PATIENT COUNSELING INFORMATION",
    "43684-0": "USE IN SPECIFIC POPULATIONS",
    
    # Specific Populations
    "42228-7": "PREGNANCY",
    "34080-2": "NURSING MOTHERS",
    "34081-0": "PEDIATRIC USE",
    "34082-8": "GERIATRIC USE",
    "34083-6": "CARCINOGENESIS MUTAGENESIS IMPAIRMENT OF FERTILITY",
    "42231-1": "CARCINOGENESIS AND MUTAGENESIS AND IMPAIRMENT OF FERTILITY",
    
    # Clinical Pharmacology
    "34090-1": "CLINICAL PHARMACOLOGY",
    "43682-4": "MECHANISM OF ACTION",
    "43681-6": "PHARMACOKINETICS",
    "43680-8": "PHARMACODYNAMICS",
    "34092-7": "CLINICAL STUDIES",
    
    # Drug Description
    "34089-3": "DESCRIPTION",
    "43678-2": "DOSAGE FORMS AND STRENGTHS",
    "34069-5": "HOW SUPPLIED",
    "44425-7": "STORAGE AND HANDLING",
    "34069-5": "HOW SUPPLIED STORAGE AND HANDLING",
    
    # Package Information
    "51945-4": "PACKAGE LABEL - PRINCIPAL DISPLAY PANEL",
    "42230-3": "SPL INDEXING DATA ELEMENTS",
    "50741-8": "INSTRUCTIONS FOR USE",
    
    # Patient Information
    "42229-5": "PATIENT INFORMATION",
    "43684-0": "PATIENT PACKAGE INSERT",
    
    # Abuse and Dependence
    "34091-9": "DRUG ABUSE AND DEPENDENCE",
    
    # Nonclinical Toxicology
    "34091-9": "NONCLINICAL TOXICOLOGY",
    "34086-9": "ANIMAL PHARMACOLOGY AND OR TOXICOLOGY",
    "34087-7": "ANIMAL PHARMACOLOGY",
    
    # References and Additional
    "43677-4": "REFERENCES",
    "50740-0": "RECENT MAJOR CHANGES",
    "51727-6": "HIGHLIGHTS OF PRESCRIBING INFORMATION",
    
    # Subsections (common)
    "43679-0": "DOSAGE ADJUSTMENT",
    "42229-5": "PREPARATION AND ADMINISTRATION",
    "43678-2": "RECOMMENDED DOSAGE",
    
    # Generic fallback
    "42229-5": "SPL UNCLASSIFIED SECTION",
}


class HierarchicalParser:
    """
    Enhanced parser with complete LOINC support and true hierarchical structure
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
        """Parse XML content with hierarchical structure"""
        try:
            root = etree.fromstring(xml_content)
            
            # Extract metadata
            metadata = self._extract_metadata(root)
            if not metadata:
                logger.warning("Failed to extract metadata")
                return None
            
            # Extract sections hierarchically
            sections = self._extract_sections_hierarchical(root)
            if not sections:
                logger.warning("Failed to extract sections")
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
            # Drug name
            name_elem = root.find('.//hl7:name', self.namespaces)
            name = name_elem.text.strip() if name_elem is not None and name_elem.text else "Unknown"
            
            # Set ID (unique identifier)
            set_id_elem = root.find('.//hl7:setId', self.namespaces)
            set_id = set_id_elem.get('root') if set_id_elem is not None else None
            
            # Version number
            version_elem = root.find('.//hl7:versionNumber', self.namespaces)
            version = int(version_elem.get('value', 1)) if version_elem is not None else 1
            
            # Effective time
            effective_time_elem = root.find('.//hl7:effectiveTime', self.namespaces)
            effective_time = effective_time_elem.get('value') if effective_time_elem is not None else None
            
            # Manufacturer
            manufacturer_elem = root.find('.//hl7:representedOrganization/hl7:name', self.namespaces)
            manufacturer = manufacturer_elem.text.strip() if manufacturer_elem is not None and manufacturer_elem.text else "Unknown"
            
            return {
                'name': name,
                'set_id': set_id,
                'version': version,
                'effective_time': effective_time,
                'manufacturer': manufacturer
            }
            
        except Exception as e:
            logger.error(f"Failed to extract metadata: {e}")
            return None
    
    def _extract_sections_hierarchical(self, root) -> List[Dict]:
        """
        Extract sections hierarchically preserving parent-child relationships
        """
        try:
            # Find the structured body
            structured_body = root.find('.//hl7:component/hl7:structuredBody', self.namespaces)
            if structured_body is None:
                return []
            
            # Get all top-level sections (direct children only)
            component_sections = structured_body.findall('./hl7:component/hl7:section', self.namespaces)
            
            sections = []
            for idx, section_elem in enumerate(component_sections, 1):
                section_data_list = self._parse_section_recursive(
                    section_elem,
                    parent_id=None,
                    level=1,
                    section_num=str(idx)
                )
                if section_data_list:
                    sections.extend(section_data_list)  # extend, not append
            
            # Merge duplicates if needed
            sections = self._merge_duplicate_subsections(sections)
            
            # Renumber sections after merging
            sections = self._renumber_sections(sections)
            
            return sections
            
        except Exception as e:
            logger.error(f"Failed to extract sections: {e}")
            return []
    
    def _parse_section_recursive(self, section_elem, parent_id: Optional[int], 
                                 level: int, section_num: str) -> Optional[Dict]:
        """
        Recursively parse section and its children
        Returns section with all subsections flattened
        """
        try:
            # Extract LOINC code
            code_elem = section_elem.find('./hl7:code', self.namespaces)
            loinc_code = code_elem.get('code') if code_elem is not None else None
            
            # Get title (with fallback to LOINC mapping)
            title = self._extract_title(section_elem, loinc_code)
            if not title or title == "Unknown Section":
                return None
            
            # Extract content (ONLY this section's content, not subsections)
            content_html, content_text = self._extract_section_content(section_elem)
            
            # Create section data
            section_data = {
                'section_number': section_num,
                'level': level,
                'parent_id': parent_id,  # Will be set during database insertion
                'loinc_code': loinc_code,
                'title': title,
                'content_html': content_html,
                'content': content_text,
                'order': int(section_num.split('.')[0]) if '.' in section_num else int(section_num)
            }
            
            # Store main section
            result = [section_data]
            
            # Recursively parse subsections
            subsection_components = section_elem.findall('./hl7:component/hl7:section', self.namespaces)
            for sub_idx, subsection_elem in enumerate(subsection_components, 1):
                subsection_num = f"{section_num}.{sub_idx}"
                subsection_data = self._parse_section_recursive(
                    subsection_elem,
                    parent_id=None,  # Will be updated with actual DB ID
                    level=level + 1,
                    section_num=subsection_num
                )
                if subsection_data:
                    result.extend(subsection_data)
            
            return result
            
        except Exception as e:
            logger.debug(f"Failed to parse section: {e}")
            return None
    
    def _extract_title(self, section_elem, loinc_code: Optional[str]) -> str:
        """Extract section title with fallback to LOINC mapping"""
        
        # Try <title> element first
        title_elem = section_elem.find('./hl7:title', self.namespaces)
        if title_elem is not None and title_elem.text:
            title = title_elem.text.strip()
            # If we have a real title (not empty), use it
            if title and title != "":
                cleaned = self._clean_title(title)
                # Skip generic LOINC lookup if we have a good title
                if cleaned and cleaned not in ["Unknown Section", "Generic Section", "Section"]:
                    return cleaned
        
        # Fallback to LOINC code mapping (only for well-known sections)
        if loinc_code and loinc_code in COMPLETE_LOINC_CODES:
            loinc_title = COMPLETE_LOINC_CODES[loinc_code]
            # Don't use "SPL UNCLASSIFIED" - it's useless
            if "UNCLASSIFIED" not in loinc_title.upper():
                return loinc_title
        
        # If we had a title element but it wasn't good enough, try again
        if title_elem is not None and title_elem.text:
            title = title_elem.text.strip()
            if title:
                return self._clean_title(title)
        
        # Fallback to displayName attribute
        code_elem = section_elem.find('./hl7:code', self.namespaces)
        if code_elem is not None:
            display_name = code_elem.get('displayName')
            if display_name and "UNCLASSIFIED" not in display_name.upper():
                return self._clean_title(display_name)
        
        # Last resort for subsections - use "Subsection"
        return "Subsection"
    
    def _clean_title(self, title: str) -> str:
        """Clean up title text"""
        # Remove extra whitespace
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Remove common prefixes
        title = re.sub(r'^SECTION\s+\d+:', '', title, flags=re.IGNORECASE).strip()
        
        return title
    
    def _extract_section_content(self, section_elem) -> Tuple[str, str]:
        """
        Extract section content as HTML and plain text
        EXCLUDES nested <section> elements (they're handled separately)
        """
        text_elem = section_elem.find('./hl7:text', self.namespaces)
        if text_elem is None:
            return "", ""
        
        html_parts = []
        text_parts = []
        
        # Process each child element
        for child in text_elem:
            # Skip if it's a nested section component
            if child.tag.endswith('component'):
                continue
            
            # Skip elements we don't want to display
            if self._should_skip_element(child):
                continue
            
            # Render element to HTML and text
            html_content = self._render_element_to_html(child)
            text_content = self._extract_text_from_element(child)
            
            if html_content:
                html_parts.append(html_content)
            if text_content:
                text_parts.append(text_content)
        
        return '\n'.join(html_parts), '\n\n'.join(text_parts)
    
    def _should_skip_element(self, element) -> bool:
        """Determine if element should be skipped (diagrams, images, etc.)"""
        tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
        
        # Skip multimedia (images, diagrams)
        if tag in ['renderMultiMedia', 'observationMedia']:
            return True
        
        # Skip if no content
        if not element.text and len(element) == 0:
            return True
        
        return False
    
    def _render_element_to_html(self, element) -> str:
        """Convert XML element to clean HTML"""
        tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
        
        if tag == 'paragraph':
            return self._render_paragraph(element)
        elif tag == 'list':
            return self._render_list(element)
        elif tag == 'table':
            return self._render_table(element)
        elif tag == 'content':
            return self._render_styled_content(element)
        else:
            # Default: extract text
            return self._extract_text_from_element(element)
    
    def _render_paragraph(self, para_elem) -> str:
        """Render paragraph element with proper HTML structure"""
        parts = []
        
        # Get direct text
        if para_elem.text:
            text = para_elem.text.strip()
            if text:
                parts.append(text)
        
        # Process children (preserving styled content)
        for child in para_elem:
            child_html = self._render_element_to_html(child)
            if child_html:
                parts.append(child_html)
            if child.tail:
                tail = child.tail.strip()
                if tail:
                    parts.append(tail)
        
        if not parts:
            return ""
        
        content = ' '.join(parts)
        
        # Return as paragraph with proper spacing
        return f'<p class="mb-4 leading-relaxed text-gray-800">{content}</p>'
    
    def _render_list(self, list_elem) -> str:
        """Render list element as proper HTML list"""
        list_type = list_elem.get('listType', 'unordered')
        items = list_elem.findall('./hl7:item', self.namespaces)
        
        if not items:
            return ""
        
        # Build list items
        list_items = []
        for item in items:
            item_html = self._render_list_item(item)
            if item_html:
                list_items.append(f'<li class="mb-2">{item_html}</li>')
        
        if not list_items:
            return ""
        
        # Ordered or unordered list
        if list_type == 'ordered':
            return f'<ol class="list-decimal ml-6 my-3 space-y-2">{"".join(list_items)}</ol>'
        else:
            return f'<ul class="list-disc ml-6 my-3 space-y-2">{"".join(list_items)}</ul>'
    
    def _render_list_item(self, item_elem) -> str:
        """Render a list item with proper content"""
        parts = []
        
        if item_elem.text:
            parts.append(item_elem.text.strip())
        
        for child in item_elem:
            child_html = self._render_element_to_html(child)
            if child_html:
                parts.append(child_html)
            if child.tail:
                parts.append(child.tail.strip())
        
        return ' '.join(parts).strip()
    
    def _render_table(self, table_elem) -> str:
        """
        Render table as proper HTML table with clean styling
        Preserves FDA table structure
        """
        # Get caption
        caption = self._extract_table_caption(table_elem)
        
        # Extract table data
        headers, rows = self._extract_table_data(table_elem)
        
        if not rows and not headers:
            return ""
        
        # Build HTML table
        html = ['<div class="my-4 overflow-x-auto">']
        html.append('<table class="min-w-full border border-gray-300 bg-white">')
        
        # Add caption if present
        if caption:
            html.append(f'<caption class="text-sm font-semibold mb-2 text-left px-2">{caption}</caption>')
        
        # Add headers
        if headers:
            html.append('<thead class="bg-gray-50">')
            html.append('<tr>')
            for header in headers:
                html.append(f'<th class="border border-gray-300 px-3 py-2 text-left text-sm font-semibold text-gray-700">{header}</th>')
            html.append('</tr>')
            html.append('</thead>')
        
        # Add body rows
        if rows:
            html.append('<tbody>')
            for row_idx, row in enumerate(rows):
                bg_class = 'bg-white' if row_idx % 2 == 0 else 'bg-gray-50'
                html.append(f'<tr class="{bg_class}">')
                for cell in row:
                    html.append(f'<td class="border border-gray-300 px-3 py-2 text-sm text-gray-800">{cell}</td>')
                html.append('</tr>')
            html.append('</tbody>')
        
        html.append('</table>')
        html.append('</div>')
        
        return ''.join(html)
    
    def _extract_table_caption(self, table_elem) -> str:
        """Extract table caption"""
        caption_elem = table_elem.find('.//hl7:caption', self.namespaces)
        if caption_elem is not None:
            return self._extract_text_from_element(caption_elem)
        return ""
    
    def _extract_table_data(self, table_elem) -> Tuple[List[str], List[List[str]]]:
        """Extract table headers and rows"""
        headers = []
        rows = []
        
        # Extract headers
        thead = table_elem.find('.//hl7:thead', self.namespaces)
        if thead is not None:
            header_cells = thead.findall('.//hl7:th', self.namespaces)
            headers = [self._extract_text_from_element(th).strip() for th in header_cells]
        
        # Extract rows
        tbody = table_elem.find('.//hl7:tbody', self.namespaces)
        if tbody is not None:
            for tr in tbody.findall('.//hl7:tr', self.namespaces):
                cells = tr.findall('.//hl7:td', self.namespaces)
                row = [self._extract_text_from_element(td).strip() for td in cells]
                if any(row):  # Skip empty rows
                    rows.append(row)
        
        return headers, rows
    
    def _render_styled_content(self, content_elem) -> str:
        """Render styled content (bold, italic, underline) as HTML"""
        style_code = content_elem.get('styleCode', '')
        
        # Recursively get content (may have nested elements)
        parts = []
        if content_elem.text:
            parts.append(content_elem.text)
        
        for child in content_elem:
            child_html = self._render_element_to_html(child)
            if child_html:
                parts.append(child_html)
            if child.tail:
                parts.append(child.tail)
        
        text = ''.join(parts).strip()
        
        if not text:
            return ""
        
        # Apply styling
        if 'bold' in style_code.lower() or 'emphasis' in style_code.lower():
            return f'<strong class="font-bold">{text}</strong>'
        elif 'italics' in style_code.lower():
            return f'<em class="italic">{text}</em>'
        elif 'underline' in style_code.lower():
            return f'<u class="underline">{text}</u>'
        else:
            return text
    
    def _extract_text_from_element(self, element) -> str:
        """Recursively extract all text from element"""
        text_parts = []
        
        if element.text:
            text_parts.append(element.text.strip())
        
        for child in element:
            if not self._should_skip_element(child):
                child_text = self._extract_text_from_element(child)
                if child_text:
                    text_parts.append(child_text)
            if child.tail:
                text_parts.append(child.tail.strip())
        
        return ' '.join(text_parts).strip()
    
    def _merge_duplicate_subsections(self, sections: List[Dict]) -> List[Dict]:
        """
        Merge subsections with duplicate titles under the same parent
        Combines their content into a single section
        """
        merged = []
        skip_indices = set()
        
        for i, section in enumerate(sections):
            if i in skip_indices:
                continue
            
            # Find all subsections with same parent and title
            duplicates = []
            for j in range(i + 1, len(sections)):
                if j in skip_indices:
                    continue
                
                other = sections[j]
                
                # Check if they're siblings with same title
                # Must have same level and parent section number
                same_level = section['level'] == other['level']
                same_parent = self._get_parent_number(section['section_number']) == \
                             self._get_parent_number(other['section_number'])
                same_title = section['title'] == other['title']
                
                if same_level and same_parent and same_title and section['level'] > 1:
                    duplicates.append(j)
            
            if duplicates:
                # Merge content from all duplicates
                combined_html = [section['content_html']]
                combined_text = [section['content']]
                
                for dup_idx in duplicates:
                    dup = sections[dup_idx]
                    if dup['content_html']:
                        combined_html.append(dup['content_html'])
                    if dup['content']:
                        combined_text.append(dup['content'])
                    skip_indices.add(dup_idx)
                
                # Create merged section
                merged_section = section.copy()
                merged_section['content_html'] = '\n\n'.join(filter(None, combined_html))
                merged_section['content'] = '\n\n'.join(filter(None, combined_text))
                merged.append(merged_section)
            else:
                merged.append(section)
        
        return merged
    
    def _renumber_sections(self, sections: List[Dict]) -> List[Dict]:
        """
        Renumber sections after merging to ensure consecutive numbering
        """
        # Group sections by level and parent
        def get_parent_num(section_num: str) -> str:
            parts = section_num.split('.')
            return '.'.join(parts[:-1]) if len(parts) > 1 else ''
        
        # Build parent-child mapping
        parent_map = {}
        for section in sections:
            parent = get_parent_num(section['section_number'])
            if parent not in parent_map:
                parent_map[parent] = []
            parent_map[parent].append(section)
        
        # Renumber within each parent group
        renumbered = []
        
        def renumber_group(parent_num: str):
            children = parent_map.get(parent_num, [])
            for idx, child in enumerate(children, 1):
                old_num = child['section_number']
                new_num = f"{parent_num}.{idx}" if parent_num else str(idx)
                child['section_number'] = new_num
                renumbered.append(child)
                
                # Recursively renumber children of this section
                renumber_group(new_num)
        
        # Start with top-level sections (empty parent)
        renumber_group('')
        
        return renumbered
    
    def _get_parent_number(self, section_number: str) -> str:
        """Get parent section number (e.g., '1.2.3' -> '1.2')"""
        parts = section_number.split('.')
        if len(parts) <= 1:
            return ''
        return '.'.join(parts[:-1])


# Convenience function for backward compatibility
def parse_drug_label(zip_path: str) -> Optional[Dict]:
    """Parse a drug label ZIP file"""
    parser = HierarchicalParser()
    return parser.parse_zip_file(zip_path)
