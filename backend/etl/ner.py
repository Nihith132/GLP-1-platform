"""
Named Entity Recognition (NER) Service
Extracts medical entities from drug label text using BioBERT
Entities: dosage, side effects, contraindications, routes, etc.
"""

import re
from typing import List, Dict, Optional
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import torch
import logging

logger = logging.getLogger(__name__)


class MedicalNER:
    """
    Medical Named Entity Recognition using BioBERT
    Extracts structured medical information from text
    """
    
    def __init__(self, model_name: str = "d4data/biomedical-ner-all"):
        """
        Initialize the NER model
        
        Args:
            model_name: HuggingFace model to use for biomedical NER
        """
        self.model_name = model_name
        self.ner_pipeline = None
        self.pattern_extractor = None
        self._initialized = False
        
        # Entity type mappings from model labels to our schema
        self.entity_mappings = {
            'Chemical': 'drug_name',
            'Disease': 'condition',
            'Gene': 'gene',
            'Species': 'species',
            'Protein': 'protein',
            'CellLine': 'cell_line',
            'CellType': 'cell_type',
            'DNA': 'dna',
            'RNA': 'rna'
        }
    
    def initialize(self):
        """
        Lazy initialization - load BioBERT NER model
        Downloads ~400MB on first run, cached afterwards
        """
        if self._initialized:
            return
        
        try:
            logger.info(f"Loading BioBERT NER model: {self.model_name}")
            logger.info("This may take 30-60 seconds on first run (downloading model)...")
            
            # Load tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForTokenClassification.from_pretrained(self.model_name)
            
            # Create NER pipeline
            self.ner_pipeline = pipeline(
                "ner",
                model=model,
                tokenizer=tokenizer,
                aggregation_strategy="simple",  # Merge subword tokens
                device=0 if torch.cuda.is_available() else -1  # GPU if available
            )
            
            # Initialize pattern extractor for structured data (dosages, routes, etc.)
            self.pattern_extractor = PatternExtractor()
            
            self._initialized = True
            device = "GPU" if torch.cuda.is_available() else "CPU"
            logger.info(f"✅ BioBERT NER model loaded successfully on {device}")
            
        except Exception as e:
            logger.error(f"Failed to initialize NER model: {e}")
            raise
    
    def extract_entities(self, text: str, section_type: str = None) -> List[Dict]:
        """
        Extract medical entities from text using BioBERT + patterns
        
        Args:
            text: Text to analyze
            section_type: Type of section (for context-aware extraction)
            
        Returns:
            List of entity dictionaries with label, text, start, end, confidence
        """
        if not self._initialized:
            self.initialize()
        
        entities = []
        
        # 1. BioBERT NER - extract medical concepts
        try:
            # Split long text into chunks (BioBERT has 512 token limit)
            chunks = self._chunk_text(text, max_length=400)
            
            offset = 0
            for chunk in chunks:
                model_entities = self.ner_pipeline(chunk)
                
                # Convert model output to our format
                for entity in model_entities:
                    label = entity['entity_group']
                    mapped_label = self.entity_mappings.get(label, label.lower())
                    
                    entities.append({
                        'label': mapped_label,
                        'text': entity['word'].strip(),
                        'start_char': entity['start'] + offset,
                        'end_char': entity['end'] + offset,
                        'confidence': entity['score']
                    })
                
                offset += len(chunk)
        except Exception as e:
            logger.warning(f"BioBERT extraction failed: {e}, falling back to patterns")
        
        # 2. Pattern-based extraction for structured data
        # These are highly reliable for standardized medical formats
        pattern_entities = self.pattern_extractor.extract_all(text, section_type)
        entities.extend(pattern_entities)
        
        # 3. Deduplicate overlapping entities
        entities = self._deduplicate_entities(entities)
        
        return entities
    
    def _chunk_text(self, text: str, max_length: int = 400) -> List[str]:
        """
        Split text into chunks for BioBERT processing
        Splits on sentence boundaries to preserve context
        """
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        sentences = re.split(r'[.!?]\s+', text)
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """
        Remove duplicate/overlapping entities, keeping higher confidence ones
        """
        if not entities:
            return []
        
        # Sort by start position
        entities = sorted(entities, key=lambda e: e['start_char'])
        
        deduplicated = []
        for entity in entities:
            # Check if overlaps with existing entities
            overlap = False
            for existing in deduplicated:
                # Check for overlap
                if (entity['start_char'] < existing['end_char'] and 
                    entity['end_char'] > existing['start_char']):
                    # Keep the one with higher confidence
                    if entity['confidence'] > existing['confidence']:
                        deduplicated.remove(existing)
                    else:
                        overlap = True
                        break
            
            if not overlap:
                deduplicated.append(entity)
        
        return deduplicated
    
    def summarize_entities(self, entities: List[Dict]) -> Dict[str, int]:
        """
        Create a summary count of entity types
        
        Returns:
            Dict with entity counts: {'drug_name': 5, 'condition': 23}
        """
        summary = {}
        
        for entity in entities:
            label = entity['label']
            summary[label] = summary.get(label, 0) + 1
        
        return summary


class PatternExtractor:
    """
    Pattern-based extraction for highly structured medical data
    Complements BioBERT for dosages, routes, frequencies
    """
    
    def extract_all(self, text: str, section_type: str = None) -> List[Dict]:
        """Extract all pattern-based entities"""
        entities = []
        
        # Extract different types based on section
        if section_type in ['34068-7', '34067-9']:  # Dosage or Indications
            entities.extend(self._extract_dosages(text))
            entities.extend(self._extract_routes(text))
            entities.extend(self._extract_frequencies(text))
        
        if section_type in ['34084-4', '43685-7']:  # Adverse Reactions or Warnings
            entities.extend(self._extract_side_effects(text))
        
        if section_type == '34070-3':  # Contraindications
            entities.extend(self._extract_contraindications(text))
        
        return entities
    
    def _extract_dosages(self, text: str) -> List[Dict]:
        """
        Extract dosage/strength information
        Examples: "0.5 mg", "1.0 mg", "2.4 mg"
        """
        entities = []
        
        # Pattern: number + unit
        pattern = r'\b(\d+\.?\d*\s*(?:mg|g|ml|mcg|units?|IU)\b)'
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            entities.append({
                'label': 'strength',
                'text': match.group(1),
                'start_char': match.start(),
                'end_char': match.end(),
                'confidence': 0.9
            })
        
        return entities
    
    def _extract_routes(self, text: str) -> List[Dict]:
        """
        Extract administration routes
        Examples: "subcutaneous", "oral", "intravenous"
        """
        entities = []
        
        routes = [
            'subcutaneous', 'subcutaneously', 'oral', 'orally',
            'intravenous', 'intravenously', 'intramuscular', 'intramuscularly',
            'topical', 'topically', 'injection', 'injected'
        ]
        
        pattern = r'\b(' + '|'.join(routes) + r')\b'
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            entities.append({
                'label': 'route',
                'text': match.group(1),
                'start_char': match.start(),
                'end_char': match.end(),
                'confidence': 0.95
            })
        
        return entities
    
    def _extract_frequencies(self, text: str) -> List[Dict]:
        """
        Extract dosing frequency
        Examples: "once daily", "twice weekly", "every 4 hours"
        """
        entities = []
        
        # Pattern: frequency expressions
        patterns = [
            r'once\s+(?:daily|weekly|monthly)',
            r'twice\s+(?:daily|weekly|monthly)',
            r'three\s+times\s+(?:daily|weekly|monthly)',
            r'every\s+\d+\s+(?:hours?|days?|weeks?)',
            r'\d+\s+times?\s+(?:daily|per\s+day|weekly|per\s+week)'
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({
                    'label': 'frequency',
                    'text': match.group(0),
                    'start_char': match.start(),
                    'end_char': match.end(),
                    'confidence': 0.9
                })
        
        return entities
    
    def _extract_side_effects(self, text: str) -> List[Dict]:
        """
        Extract side effects/adverse reactions
        """
        entities = []
        
        # Common side effects
        side_effects = [
            'nausea', 'vomiting', 'diarrhea', 'headache', 'dizziness',
            'fatigue', 'constipation', 'abdominal pain', 'injection site reaction',
            'hypoglycemia', 'pancreatitis', 'thyroid tumors', 'gallbladder disease',
            'kidney problems', 'allergic reaction', 'rash', 'itching'
        ]
        
        pattern = r'\b(' + '|'.join(side_effects) + r')\b'
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            entities.append({
                'label': 'side_effect',
                'text': match.group(1),
                'start_char': match.start(),
                'end_char': match.end(),
                'confidence': 0.85
            })
        
        return entities
    
    def _extract_contraindications(self, text: str) -> List[Dict]:
        """
        Extract contraindications
        """
        entities = []
        
        contraindications = [
            'pregnancy', 'breastfeeding', 'renal impairment', 'hepatic impairment',
            'heart failure', 'hypersensitivity', 'allergy', 'diabetes',
            'thyroid cancer', 'medullary thyroid carcinoma', 'MEN 2'
        ]
        
        pattern = r'\b(' + '|'.join(contraindications) + r')\b'
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            entities.append({
                'label': 'contraindication',
                'text': match.group(1),
                'start_char': match.start(),
                'end_char': match.end(),
                'confidence': 0.8
            })
        
        return entities
    
    def _extract_conditions(self, text: str) -> List[Dict]:
        """
        Extract medical conditions/diseases
        """
        entities = []
        
        conditions = [
            'type 2 diabetes', 'diabetes mellitus', 'obesity', 'cardiovascular disease',
            'heart disease', 'hypertension', 'high blood pressure', 'pancreatitis'
        ]
        
        pattern = r'\b(' + '|'.join(conditions) + r')\b'
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            entities.append({
                'label': 'condition',
                'text': match.group(1),
                'start_char': match.start(),
                'end_char': match.end(),
                'confidence': 0.85
            })
        
        return entities


# Global instance
_ner_service = None


def get_ner_service() -> MedicalNER:
    """
    Get or create global NER service instance
    Singleton pattern to avoid loading model multiple times
    """
    global _ner_service
    
    if _ner_service is None:
        _ner_service = MedicalNER()
        _ner_service.initialize()
    
    return _ner_service
