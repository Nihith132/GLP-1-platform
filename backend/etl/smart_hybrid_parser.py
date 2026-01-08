"""
Smart Hybrid Parser - Best of Both Worlds
Extracts structured navigation + renders rich HTML per section
"""

from lxml import etree
from typing import Dict, List, Optional, Tuple
import hashlib
import re
from dataclasses import dataclass
from enum import Enum


class ImportanceLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SectionType(Enum):
    SAFETY = "safety"
    DOSING = "dosing"
    EFFICACY = "efficacy"
    DESCRIPTION = "description"
    ADMINISTRATIVE = "administrative"


@dataclass
class ParsedSection:
    """Represents a fully parsed section with all metadata"""
    # Identification
    loinc_code: str
    section_code: str
    title: str
    
    # Hierarchy
    parent_id: Optional[str]
    level: int
    order: int
    section_path: str
    
    # Content (multiple formats)
    content_html: str
    content_text: str
    content_xml: str
    
    # Metadata
    importance: ImportanceLevel
    section_type: Optional[SectionType]
    
    # Analysis
    word_count: int
    has_table: bool
    has_list: bool
    has_warning_keywords: bool
    has_dosage_keywords: bool
    
    # Extracted data
    extracted_data: Dict
    
    # For comparison
    comparison_hash: str


class SmartHybridParser:
    """
    Professional parser that:
    1. Extracts clean section hierarchy for navigation
    2. Renders rich HTML for each section
    3. Extracts metadata for smart features
    4. Preserves original XML for reference
    """
    
    NS = {
        'hl7': 'urn:hl7-org:v3',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }
    
    # Section importance mapping
    IMPORTANCE_MAP = {
        '34066-1': ImportanceLevel.CRITICAL,  # Boxed Warning
        '34070-3': ImportanceLevel.CRITICAL,  # Contraindications
        '34068-7': ImportanceLevel.CRITICAL,  # Dosage and Administration
        '34071-1': ImportanceLevel.CRITICAL,  # Warnings
        '43685-7': ImportanceLevel.CRITICAL,  # Warnings and Precautions
        '34084-4': ImportanceLevel.HIGH,      # Adverse Reactions
        '34073-7': ImportanceLevel.HIGH,      # Drug Interactions
        '34067-9': ImportanceLevel.HIGH,      # Indications and Usage
        '43684-0': ImportanceLevel.HIGH,      # Use in Specific Populations
        '34090-1': ImportanceLevel.MEDIUM,    # Clinical Pharmacology
        '34092-7': ImportanceLevel.MEDIUM,    # Clinical Studies
        '34089-3': ImportanceLevel.MEDIUM,    # Description
        '34069-5': ImportanceLevel.LOW,       # How Supplied
        '34093-5': ImportanceLevel.LOW,       # References
    }
    
    # Section type mapping
    TYPE_MAP = {
        '34066-1': SectionType.SAFETY,
        '34070-3': SectionType.SAFETY,
        '34071-1': SectionType.SAFETY,
        '43685-7': SectionType.SAFETY,
        '34068-7': SectionType.DOSING,
        '34067-9': SectionType.EFFICACY,
        '34090-1': SectionType.EFFICACY,
        '34092-7': SectionType.EFFICACY,
        '34089-3': SectionType.DESCRIPTION,
        '34069-5': SectionType.ADMINISTRATIVE,
    }
    
    # Known section titles
    SECTION_TITLES = {
        '34066-1': 'BOXED WARNING',
        '34067-9': 'INDICATIONS AND USAGE',
        '34068-7': 'DOSAGE AND ADMINISTRATION',
        '34069-5': 'HOW SUPPLIED/STORAGE AND HANDLING',
        '34070-3': 'CONTRAINDICATIONS',
        '34071-1': 'WARNINGS',
        '43685-7': 'WARNINGS AND PRECAUTIONS',
        '34072-9': 'PRECAUTIONS',
        '34073-7': 'DRUG INTERACTIONS',
        '34084-4': 'ADVERSE REACTIONS',
        '34089-3': 'DESCRIPTION',
        '34090-1': 'CLINICAL PHARMACOLOGY',
        '34092-7': 'CLINICAL STUDIES',
        '43684-0': 'USE IN SPECIFIC POPULATIONS',
    }
    
    # Warning keywords for detection
    WARNING_KEYWORDS = [
        'warning', 'caution', 'contraindicated', 'avoid', 'risk',
        'serious', 'fatal', 'death', 'adverse', 'emergency',
        'discontinue', 'monitor', 'alert', 'danger'
    ]
    
    # Dosage keywords for detection
    DOSAGE_KEYWORDS = [
        'mg', 'dose', 'dosage', 'administer', 'injection', 'tablet',
        'daily', 'weekly', 'twice', 'once', 'subcutaneous', 'oral',
        'capsule', 'ml', 'units'
    ]
    
    def __init__(self):
        self.css_styles = self._generate_css()
    
    def parse_zip_file(self, zip_path: str) -> Dict:
        """Parse ZIP file and return structured data"""
        import zipfile
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            xml_files = [f for f in zf.namelist() if f.endswith('.xml')]
            if not xml_files:
                return None
            
            with zf.open(xml_files[0]) as f:
                xml_content = f.read().decode('utf-8')
        
        return self.parse_xml_content(xml_content)
    
    def parse_xml_content(self, xml_content: str) -> Dict:
        """Main parsing method"""
        tree = etree.fromstring(xml_content.encode('utf-8'))
        
        # Extract metadata
        metadata = self._extract_metadata(tree)
        
        # Parse all sections with hierarchy
        sections = self._parse_sections_recursive(tree)
        
        return {
            'metadata': metadata,
            'sections': sections
        }
    
    def _extract_metadata(self, tree: etree.Element) -> Dict:
        """Extract drug metadata"""
        metadata = {}
        
        # Drug name
        name_elem = tree.find('.//hl7:manufacturedProduct//hl7:name', self.NS)
        if name_elem is not None:
            metadata['name'] = name_elem.text or 'Unknown Drug'
        
        # SET ID
        set_id = tree.find('.//hl7:setId', self.NS)
        if set_id is not None:
            metadata['set_id'] = set_id.get('root', '')
        
        # Version
        version = tree.find('.//hl7:versionNumber', self.NS)
        if version is not None:
            metadata['version'] = version.get('value', '')
        
        # Manufacturer
        manufacturer = tree.find('.//hl7:representedOrganization//hl7:name', self.NS)
        if manufacturer is not None:
            metadata['manufacturer'] = manufacturer.text or ''
        
        # Effective time
        effective_time = tree.find('.//hl7:effectiveTime', self.NS)
        if effective_time is not None:
            metadata['effective_date'] = effective_time.get('value', '')
        
        return metadata
    
    def _parse_sections_recursive(
        self,
        tree: etree.Element,
        parent_id: Optional[str] = None,
        level: int = 1,
        section_path_prefix: str = ""
    ) -> List[ParsedSection]:
        """Recursively parse sections maintaining hierarchy"""
        sections = []
        
        # Find structured body
        if level == 1:
            component = tree.find('.//hl7:component/hl7:structuredBody', self.NS)
            if component is None:
                return sections
            section_elements = component.findall('.//hl7:component/hl7:section', self.NS)
        else:
            section_elements = tree.findall('./hl7:component/hl7:section', self.NS)
        
        for idx, section_elem in enumerate(section_elements, 1):
            # Get section code
            code_elem = section_elem.find('./hl7:code', self.NS)
            loinc_code = code_elem.get('code', f'UNKNOWN-{level}-{idx}') if code_elem is not None else f'UNKNOWN-{level}-{idx}'
            section_code = code_elem.get('codeSystem', '') if code_elem is not None else ''
            
            # Get title
            title_elem = section_elem.find('./hl7:title', self.NS)
            title = self._get_text_content(title_elem) if title_elem is not None else ''
            
            # Use known title if empty
            if not title and loinc_code in self.SECTION_TITLES:
                title = self.SECTION_TITLES[loinc_code]
            
            # Skip if still no title and it's "SPL UNCLASSIFIED"
            if not title or 'SPL UNCLASSIFIED' in title.upper():
                # Try to infer from first paragraph
                text_elem = section_elem.find('./hl7:text', self.NS)
                if text_elem is not None:
                    first_para = text_elem.find('.//hl7:paragraph', self.NS)
                    if first_para is not None:
                        potential_title = self._get_text_content(first_para)[:100]
                        if len(potential_title) < 50:  # Short enough to be a title
                            title = potential_title
                
                # Still no good title? Use a generic one
                if not title or 'SPL UNCLASSIFIED' in title.upper():
                    title = f"Section {section_path_prefix}{idx}" if section_path_prefix else f"Section {idx}"
            
            # Build section path
            section_path = f"{section_path_prefix}{idx}" if section_path_prefix else f"{idx}"
            
            # Get importance and type
            importance = self.IMPORTANCE_MAP.get(loinc_code, ImportanceLevel.MEDIUM)
            section_type = self.TYPE_MAP.get(loinc_code)
            
            # Render content in multiple formats
            text_elem = section_elem.find('./hl7:text', self.NS)
            content_html = self._render_section_html(section_elem, importance, title, loinc_code)
            content_text = self._extract_plain_text(text_elem) if text_elem is not None else ''
            content_xml = etree.tostring(section_elem, encoding='unicode')
            
            # Analyze content
            word_count = len(content_text.split())
            has_table = section_elem.find('.//hl7:table', self.NS) is not None
            has_list = section_elem.find('.//hl7:list', self.NS) is not None
            has_warning_keywords = any(kw in content_text.lower() for kw in self.WARNING_KEYWORDS)
            has_dosage_keywords = any(kw in content_text.lower() for kw in self.DOSAGE_KEYWORDS)
            
            # Extract structured data
            extracted_data = self._extract_structured_data(content_text, section_elem)
            
            # Generate hash for comparison
            comparison_hash = hashlib.sha256(content_text.encode()).hexdigest()
            
            # Create parsed section
            parsed_section = ParsedSection(
                loinc_code=loinc_code,
                section_code=section_code,
                title=title,
                parent_id=parent_id,
                level=level,
                order=idx,
                section_path=section_path,
                content_html=content_html,
                content_text=content_text,
                content_xml=content_xml,
                importance=importance,
                section_type=section_type,
                word_count=word_count,
                has_table=has_table,
                has_list=has_list,
                has_warning_keywords=has_warning_keywords,
                has_dosage_keywords=has_dosage_keywords,
                extracted_data=extracted_data,
                comparison_hash=comparison_hash
            )
            
            sections.append(parsed_section)
            
            # Parse subsections recursively
            subsections = self._parse_sections_recursive(
                section_elem,
                parent_id=loinc_code,
                level=level + 1,
                section_path_prefix=f"{section_path}."
            )
            sections.extend(subsections)
        
        return sections
    
    def _render_section_html(self, section_elem: etree.Element, importance: ImportanceLevel, title: str, loinc_code: str) -> str:
        """Render section as rich HTML"""
        html_parts = []
        
        # Add importance badge
        badge_colors = {
            ImportanceLevel.CRITICAL: 'bg-red-100 border-red-400 text-red-800',
            ImportanceLevel.HIGH: 'bg-orange-100 border-orange-400 text-orange-800',
            ImportanceLevel.MEDIUM: 'bg-blue-100 border-blue-400 text-blue-800',
            ImportanceLevel.LOW: 'bg-gray-100 border-gray-400 text-gray-800',
        }
        
        badge_labels = {
            ImportanceLevel.CRITICAL: '⚠️ CRITICAL',
            ImportanceLevel.HIGH: '⚠️ HIGH IMPORTANCE',
            ImportanceLevel.MEDIUM: 'ℹ️ INFORMATION',
            ImportanceLevel.LOW: '📋 REFERENCE',
        }
        
        badge_class = badge_colors.get(importance, 'bg-gray-100')
        badge_label = badge_labels.get(importance, 'INFORMATION')
        
        html_parts.append(f'<div class="importance-badge {badge_class}">{badge_label}</div>')
        
        # Render content
        text_elem = section_elem.find('./hl7:text', self.NS)
        if text_elem is not None:
            html_parts.append(self._render_text_element(text_elem))
        
        return ''.join(html_parts)
    
    def _render_text_element(self, text_elem: etree.Element) -> str:
        """Render text content as HTML"""
        html_parts = []
        
        for child in text_elem:
            if child.tag.endswith('paragraph'):
                html_parts.append(f'<p class="mb-4 leading-relaxed">{self._get_text_content(child)}</p>')
            elif child.tag.endswith('list'):
                html_parts.append(self._render_list(child))
            elif child.tag.endswith('table'):
                html_parts.append(self._render_table(child))
        
        if text_elem.text and text_elem.text.strip():
            html_parts.insert(0, f'<p class="mb-4 leading-relaxed">{text_elem.text.strip()}</p>')
        
        return ''.join(html_parts)
    
    def _render_list(self, list_elem: etree.Element) -> str:
        """Render list"""
        list_type = list_elem.get('listType', 'unordered')
        tag = 'ol' if list_type == 'ordered' else 'ul'
        
        items = []
        for item in list_elem.findall('.//hl7:item', self.NS):
            content = self._get_text_content(item)
            if content.strip():
                items.append(f'<li class="mb-2">{content}</li>')
        
        return f'<{tag} class="ml-6 mb-4">{"".join(items)}</{tag}>'
    
    def _render_table(self, table: etree.Element) -> str:
        """Render table with professional styling"""
        html = ['<div class="overflow-x-auto mb-4"><table class="min-w-full border-collapse">']
        
        # Thead
        thead = table.find('.//hl7:thead', self.NS)
        if thead is not None:
            html.append('<thead class="bg-gradient-to-r from-blue-500 to-blue-600"><tr>')
            for th in thead.findall('.//hl7:th', self.NS):
                html.append(f'<th class="border px-4 py-2 text-white text-left">{self._get_text_content(th)}</th>')
            html.append('</tr></thead>')
        
        # Tbody
        tbody = table.find('.//hl7:tbody', self.NS)
        if tbody is not None:
            html.append('<tbody>')
            for idx, tr in enumerate(tbody.findall('.//hl7:tr', self.NS)):
                row_class = 'bg-gray-50' if idx % 2 == 0 else 'bg-white'
                html.append(f'<tr class="{row_class} hover:bg-blue-50">')
                for td in tr.findall('.//hl7:td', self.NS):
                    html.append(f'<td class="border px-4 py-2">{self._get_text_content(td)}</td>')
                html.append('</tr>')
            html.append('</tbody>')
        
        html.append('</table></div>')
        return ''.join(html)
    
    def _extract_plain_text(self, elem: etree.Element) -> str:
        """Extract plain text for analysis"""
        return ' '.join(elem.itertext()) if elem is not None else ''
    
    def _get_text_content(self, elem: etree.Element) -> str:
        """Get formatted text content"""
        if elem is None:
            return ''
        
        parts = [elem.text or '']
        for child in elem:
            if child.tag.endswith('content'):
                style = child.get('styleCode', '')
                text = self._get_text_content(child)
                if 'bold' in style.lower():
                    parts.append(f'<strong>{text}</strong>')
                elif 'italics' in style.lower():
                    parts.append(f'<em>{text}</em>')
                else:
                    parts.append(text)
            else:
                parts.append(self._get_text_content(child))
            if child.tail:
                parts.append(child.tail)
        
        return ''.join(parts)
    
    def _extract_structured_data(self, text: str, section_elem: etree.Element) -> Dict:
        """Extract structured data for smart features"""
        data = {}
        
        # Extract dosages
        dosage_pattern = r'\b\d+\.?\d*\s*(mg|mcg|g|ml|units?)\b'
        dosages = list(set(re.findall(dosage_pattern, text, re.IGNORECASE)))
        if dosages:
            data['dosages'] = [f"{d[0]}{d[1]}" for d in dosages]
        
        # Extract warnings (sentences containing warning keywords)
        warning_sentences = []
        for sentence in text.split('.'):
            if any(kw in sentence.lower() for kw in self.WARNING_KEYWORDS[:5]):
                warning_sentences.append(sentence.strip())
        if warning_sentences:
            data['warnings'] = warning_sentences[:5]
        
        return data
    
    def _generate_css(self) -> str:
        """CSS styles for rendered content"""
        return """
        <style>
            .importance-badge {
                display: inline-block;
                padding: 0.5rem 1rem;
                border-radius: 9999px;
                border-width: 2px;
                font-size: 0.75rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 1rem;
            }
        </style>
        """
