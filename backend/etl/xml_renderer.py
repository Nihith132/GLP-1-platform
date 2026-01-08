"""
Direct XML to HTML Renderer for FDA Drug Labels
Renders SPL XML as a professional document without parsing complexity
"""

from lxml import etree
from typing import Dict, Optional
import zipfile
from pathlib import Path


class XMLRenderer:
    """
    Renders FDA SPL XML directly to styled HTML
    Preserves original label structure and formatting
    """
    
    # Namespace for SPL documents
    NS = {
        'hl7': 'urn:hl7-org:v3',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }
    
    # Section code to display name mapping
    SECTION_NAMES = {
        '34066-1': 'BOXED WARNING',
        '34067-9': 'INDICATIONS AND USAGE',
        '34068-7': 'DOSAGE AND ADMINISTRATION',
        '34069-5': 'HOW SUPPLIED/STORAGE AND HANDLING',
        '34070-3': 'CONTRAINDICATIONS',
        '34071-1': 'WARNINGS',
        '34072-9': 'PRECAUTIONS',
        '34073-7': 'DRUG INTERACTIONS',
        '34074-5': 'PREGNANCY',
        '34075-2': 'NURSING MOTHERS',
        '34076-0': 'PEDIATRIC USE',
        '34077-8': 'GERIATRIC USE',
        '34078-6': 'OVERDOSAGE',
        '34084-4': 'ADVERSE REACTIONS',
        '34089-3': 'DESCRIPTION',
        '34090-1': 'CLINICAL PHARMACOLOGY',
        '34091-9': 'ANIMAL PHARMACOLOGY AND/OR TOXICOLOGY',
        '34092-7': 'CLINICAL STUDIES',
        '43678-2': 'MECHANISM OF ACTION',
        '43679-0': 'PHARMACODYNAMICS',
        '43680-8': 'PHARMACOKINETICS',
        '42229-5': 'GENERAL INFORMATION',
        '43685-7': 'WARNINGS AND PRECAUTIONS',
        '43684-0': 'USE IN SPECIFIC POPULATIONS',
        '34093-5': 'REFERENCES',
    }
    
    def __init__(self):
        self.css_styles = self._generate_css()
    
    def _generate_css(self) -> str:
        """Generate professional CSS for FDA label rendering"""
        return """
        <style>
            .fda-label {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                line-height: 1.6;
                color: #1a202c;
                max-width: 900px;
                margin: 0 auto;
                background: white;
                padding: 2rem;
            }
            
            .fda-header {
                border-bottom: 3px solid #2563eb;
                padding-bottom: 1.5rem;
                margin-bottom: 2rem;
            }
            
            .fda-title {
                font-size: 2rem;
                font-weight: 700;
                color: #1e293b;
                margin-bottom: 0.5rem;
            }
            
            .fda-subtitle {
                font-size: 1.125rem;
                color: #64748b;
                margin-bottom: 0.25rem;
            }
            
            .fda-section {
                margin-bottom: 2.5rem;
                scroll-margin-top: 80px;
            }
            
            .fda-section-title {
                font-size: 1.5rem;
                font-weight: 700;
                color: #1e293b;
                margin-bottom: 1rem;
                padding-bottom: 0.5rem;
                border-bottom: 2px solid #e2e8f0;
            }
            
            .fda-section-title.level-1 {
                font-size: 1.5rem;
                color: #1e40af;
            }
            
            .fda-section-title.level-2 {
                font-size: 1.25rem;
                color: #1e293b;
                margin-left: 1rem;
            }
            
            .fda-section-title.level-3 {
                font-size: 1.125rem;
                color: #475569;
                margin-left: 2rem;
            }
            
            .fda-paragraph {
                margin-bottom: 1rem;
                text-align: justify;
            }
            
            .fda-list {
                margin: 1rem 0 1rem 2rem;
            }
            
            .fda-list-item {
                margin-bottom: 0.5rem;
                line-height: 1.6;
            }
            
            .fda-table {
                width: 100%;
                border-collapse: collapse;
                margin: 1.5rem 0;
                font-size: 0.875rem;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            .fda-table th {
                background: linear-gradient(to bottom, #3b82f6, #2563eb);
                color: white;
                padding: 0.75rem;
                text-align: left;
                font-weight: 600;
                border: 1px solid #2563eb;
            }
            
            .fda-table td {
                padding: 0.75rem;
                border: 1px solid #e2e8f0;
            }
            
            .fda-table tr:nth-child(even) {
                background: #f8fafc;
            }
            
            .fda-table tr:hover {
                background: #f1f5f9;
            }
            
            .fda-emphasis {
                font-weight: 600;
                color: #1e293b;
            }
            
            .fda-boxed-warning {
                background: #fef2f2;
                border: 3px solid #dc2626;
                border-radius: 0.5rem;
                padding: 1.5rem;
                margin: 2rem 0;
            }
            
            .fda-boxed-warning-title {
                color: #dc2626;
                font-size: 1.25rem;
                font-weight: 700;
                margin-bottom: 1rem;
                text-transform: uppercase;
            }
            
            .fda-highlight-box {
                background: #fef3c7;
                border-left: 4px solid #f59e0b;
                padding: 1rem;
                margin: 1rem 0;
            }
            
            .fda-image-placeholder {
                background: #f1f5f9;
                border: 2px dashed #cbd5e1;
                padding: 2rem;
                text-align: center;
                color: #64748b;
                border-radius: 0.5rem;
                margin: 1rem 0;
            }
        </style>
        """
    
    def render_xml_to_html(self, xml_path: str) -> Dict[str, str]:
        """
        Render FDA SPL XML directly to styled HTML
        
        Args:
            xml_path: Path to XML file (can be inside ZIP)
            
        Returns:
            Dict with 'html' content and 'metadata'
        """
        # Extract XML from ZIP if needed
        if xml_path.endswith('.zip'):
            xml_content = self._extract_xml_from_zip(xml_path)
        else:
            with open(xml_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
        
        # Parse XML
        tree = etree.fromstring(xml_content.encode('utf-8'))
        
        # Extract metadata
        metadata = self._extract_metadata(tree)
        
        # Render to HTML
        html = self._render_document(tree, metadata)
        
        return {
            'html': html,
            'metadata': metadata
        }
    
    def _extract_xml_from_zip(self, zip_path: str) -> str:
        """Extract XML file from ZIP"""
        with zipfile.ZipFile(zip_path, 'r') as zf:
            xml_files = [f for f in zf.namelist() if f.endswith('.xml')]
            if not xml_files:
                raise ValueError("No XML file found in ZIP")
            
            with zf.open(xml_files[0]) as f:
                return f.read().decode('utf-8')
    
    def _extract_metadata(self, tree: etree.Element) -> Dict:
        """Extract drug metadata from XML"""
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
        
        return metadata
    
    def _render_document(self, tree: etree.Element, metadata: Dict) -> str:
        """Render complete document as HTML"""
        html_parts = [self.css_styles]
        html_parts.append('<div class="fda-label">')
        
        # Header
        html_parts.append('<div class="fda-header">')
        html_parts.append(f'<h1 class="fda-title">{metadata.get("name", "Drug Label")}</h1>')
        if metadata.get('manufacturer'):
            html_parts.append(f'<div class="fda-subtitle">Manufacturer: {metadata["manufacturer"]}</div>')
        if metadata.get('version'):
            html_parts.append(f'<div class="fda-subtitle">Version: {metadata["version"]}</div>')
        html_parts.append('</div>')
        
        # Render all sections
        component = tree.find('.//hl7:component/hl7:structuredBody', self.NS)
        if component is not None:
            for section in component.findall('.//hl7:component/hl7:section', self.NS):
                html_parts.append(self._render_section(section, level=1))
        
        html_parts.append('</div>')
        return ''.join(html_parts)
    
    def _render_section(self, section: etree.Element, level: int = 1) -> str:
        """Recursively render a section"""
        html_parts = []
        
        # Get section code
        code_elem = section.find('.//hl7:code', self.NS)
        section_code = code_elem.get('code', '') if code_elem is not None else ''
        
        # Get section title
        title_elem = section.find('./hl7:title', self.NS)
        title = self._get_text_content(title_elem) if title_elem is not None else ''
        
        # Use known section name if title is empty
        if not title and section_code in self.SECTION_NAMES:
            title = self.SECTION_NAMES[section_code]
        
        # Render section container
        section_id = f"section-{section_code or 'unknown'}"
        html_parts.append(f'<div class="fda-section" id="{section_id}">')
        
        # Render title
        if title:
            html_parts.append(f'<h{level + 1} class="fda-section-title level-{level}">{title}</h{level + 1}>')
        
        # Check for boxed warning
        is_boxed = section_code == '34066-1'
        if is_boxed:
            html_parts.append('<div class="fda-boxed-warning">')
            if title:
                html_parts.append(f'<div class="fda-boxed-warning-title">⚠️ {title}</div>')
        
        # Render text content
        text_elem = section.find('./hl7:text', self.NS)
        if text_elem is not None:
            html_parts.append(self._render_text_element(text_elem))
        
        if is_boxed:
            html_parts.append('</div>')
        
        # Render subsections
        for subsection in section.findall('./hl7:component/hl7:section', self.NS):
            html_parts.append(self._render_section(subsection, level + 1))
        
        html_parts.append('</div>')
        return ''.join(html_parts)
    
    def _render_text_element(self, text_elem: etree.Element) -> str:
        """Render text content with formatting"""
        html_parts = []
        
        # Process all child elements
        for child in text_elem:
            if child.tag.endswith('paragraph'):
                html_parts.append(self._render_paragraph(child))
            elif child.tag.endswith('list'):
                html_parts.append(self._render_list(child))
            elif child.tag.endswith('table'):
                html_parts.append(self._render_table(child))
            elif child.tag.endswith('renderMultiMedia'):
                html_parts.append(self._render_image_placeholder(child))
        
        # Handle direct text
        if text_elem.text and text_elem.text.strip():
            html_parts.insert(0, f'<p class="fda-paragraph">{text_elem.text.strip()}</p>')
        
        return ''.join(html_parts)
    
    def _render_paragraph(self, para: etree.Element) -> str:
        """Render a paragraph"""
        content = self._get_text_content(para)
        if content.strip():
            return f'<p class="fda-paragraph">{content}</p>'
        return ''
    
    def _render_list(self, list_elem: etree.Element) -> str:
        """Render a list"""
        list_type = list_elem.get('listType', 'unordered')
        tag = 'ol' if list_type == 'ordered' else 'ul'
        
        html_parts = [f'<{tag} class="fda-list">']
        
        for item in list_elem.findall('.//hl7:item', self.NS):
            content = self._get_text_content(item)
            if content.strip():
                html_parts.append(f'<li class="fda-list-item">{content}</li>')
        
        html_parts.append(f'</{tag}>')
        return ''.join(html_parts)
    
    def _render_table(self, table: etree.Element) -> str:
        """Render a table"""
        html_parts = ['<table class="fda-table">']
        
        # Render thead
        thead = table.find('.//hl7:thead', self.NS)
        if thead is not None:
            html_parts.append('<thead><tr>')
            for th in thead.findall('.//hl7:th', self.NS):
                content = self._get_text_content(th)
                html_parts.append(f'<th>{content}</th>')
            html_parts.append('</tr></thead>')
        
        # Render tbody
        tbody = table.find('.//hl7:tbody', self.NS)
        if tbody is not None:
            html_parts.append('<tbody>')
            for tr in tbody.findall('.//hl7:tr', self.NS):
                html_parts.append('<tr>')
                for td in tr.findall('.//hl7:td', self.NS):
                    content = self._get_text_content(td)
                    html_parts.append(f'<td>{content}</td>')
                html_parts.append('</tr>')
            html_parts.append('</tbody>')
        
        html_parts.append('</table>')
        return ''.join(html_parts)
    
    def _render_image_placeholder(self, elem: etree.Element) -> str:
        """Render image placeholder"""
        return '<div class="fda-image-placeholder">📊 [Image/Diagram - See original label]</div>'
    
    def _get_text_content(self, elem: etree.Element) -> str:
        """Extract all text content from element"""
        if elem is None:
            return ''
        
        # Get direct text
        parts = [elem.text or '']
        
        # Process children
        for child in elem:
            # Handle emphasis/bold
            if child.tag.endswith('content'):
                style_code = child.get('styleCode', '')
                text = self._get_text_content(child)
                
                if 'bold' in style_code.lower() or 'emphasis' in style_code.lower():
                    parts.append(f'<strong class="fda-emphasis">{text}</strong>')
                elif 'italics' in style_code.lower():
                    parts.append(f'<em>{text}</em>')
                elif 'underline' in style_code.lower():
                    parts.append(f'<u>{text}</u>')
                else:
                    parts.append(text)
            else:
                parts.append(self._get_text_content(child))
            
            # Add tail text
            if child.tail:
                parts.append(child.tail)
        
        return ''.join(parts)


# Usage example
if __name__ == "__main__":
    renderer = XMLRenderer()
    
    # Test with a ZIP file
    zip_path = "/path/to/drug.zip"
    result = renderer.render_xml_to_html(zip_path)
    
    print("Metadata:", result['metadata'])
    print("\nHTML length:", len(result['html']))
