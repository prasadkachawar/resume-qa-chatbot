"""
Resume NER Service using yashpwr/resume-ner-bert-v2
Extracts structured information from resume text using BERT-based NER
"""
import logging
from typing import Dict, List, Any, Optional
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import re

logger = logging.getLogger(__name__)

class ResumeNERService:
    """Service for Named Entity Recognition on resume text"""
    
    def __init__(self):
        """Initialize the Resume NER model"""
        self.model_name = "yashpwr/resume-ner-bert-v2"
        self.model = None
        self.tokenizer = None
        self.ner_pipeline = None
        self.entity_labels = {
            'PERSON': 'Person Names',
            'ORG': 'Organizations/Companies',
            'GPE': 'Locations/Places', 
            'SKILL': 'Technical Skills',
            'EMAIL': 'Email Addresses',
            'PHONE': 'Phone Numbers',
            'DESIGNATION': 'Job Titles/Positions',
            'COLLEGE': 'Educational Institutions',
            'DEGREE': 'Academic Degrees',
            'EXPERIENCE': 'Work Experience',
            'CERTIFICATION': 'Certifications',
            'LANGUAGE': 'Programming Languages',
            'LOCATION': 'Geographic Locations'
        }
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the NER model and tokenizer"""
        try:
            logger.info(f"Loading Resume NER model: {self.model_name}")
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForTokenClassification.from_pretrained(self.model_name)
            
            # Create NER pipeline
            self.ner_pipeline = pipeline(
                "ner",
                model=self.model,
                tokenizer=self.tokenizer,
                aggregation_strategy="simple",
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("✅ Resume NER model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Resume NER model: {e}")
            self.model = None
            self.tokenizer = None
            self.ner_pipeline = None
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract named entities from resume text
        
        Args:
            text: Resume text to analyze
            
        Returns:
            Dictionary with extracted entities organized by type
        """
        if not self.ner_pipeline:
            return self._fallback_extraction(text)
        
        try:
            # Run NER on the text
            entities = self.ner_pipeline(text)
            
            # Organize entities by type
            organized_entities = self._organize_entities(entities)
            
            # Post-process and clean entities
            cleaned_entities = self._clean_entities(organized_entities, text)
            
            return {
                'success': True,
                'entities': cleaned_entities,
                'total_entities': sum(len(v) for v in cleaned_entities.values()),
                'model_used': self.model_name,
                'message': 'Entities extracted successfully'
            }
            
        except Exception as e:
            logger.error(f"Error in NER extraction: {e}")
            return {
                'success': False,
                'error': str(e),
                'entities': {},
                'message': 'Failed to extract entities'
            }
    
    def _organize_entities(self, entities: List[Dict]) -> Dict[str, List[str]]:
        """Organize extracted entities by type"""
        organized = {}
        
        for entity in entities:
            entity_type = entity['entity_group']
            entity_text = entity['word'].strip()
            confidence = entity['score']
            
            # Only include high-confidence entities
            if confidence > 0.7 and len(entity_text) > 1:
                if entity_type not in organized:
                    organized[entity_type] = []
                
                # Avoid duplicates
                if entity_text not in organized[entity_type]:
                    organized[entity_type].append(entity_text)
        
        return organized
    
    def _clean_entities(self, entities: Dict[str, List[str]], original_text: str) -> Dict[str, List[str]]:
        """Clean and post-process extracted entities"""
        cleaned = {}
        
        for entity_type, entity_list in entities.items():
            cleaned_list = []
            
            for entity in entity_list:
                # Remove special characters and clean up
                cleaned_entity = re.sub(r'^[^\w]+|[^\w]+$', '', entity)
                
                # Skip very short entities
                if len(cleaned_entity) < 2:
                    continue
                
                # Additional cleaning based on entity type
                if entity_type in ['EMAIL', 'PHONE']:
                    cleaned_entity = self._extract_contact_info(original_text, entity_type)
                elif entity_type in ['SKILL', 'LANGUAGE']:
                    cleaned_entity = self._clean_skill(cleaned_entity)
                
                if cleaned_entity and cleaned_entity not in cleaned_list:
                    cleaned_list.append(cleaned_entity)
            
            if cleaned_list:
                # Map to human-readable labels
                readable_type = self.entity_labels.get(entity_type, entity_type)
                cleaned[readable_type] = cleaned_list
        
        return cleaned
    
    def _extract_contact_info(self, text: str, info_type: str) -> Optional[str]:
        """Extract contact information using regex patterns"""
        if info_type == 'EMAIL':
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text)
            return emails[0] if emails else None
        
        elif info_type == 'PHONE':
            phone_pattern = r'[\+]?[1-9]?[\-.\s]?\(?[0-9]{3}\)?[\-.\s]?[0-9]{3}[\-.\s]?[0-9]{4,6}'
            phones = re.findall(phone_pattern, text)
            return phones[0] if phones else None
        
        return None
    
    def _clean_skill(self, skill: str) -> str:
        """Clean and standardize skill names"""
        # Common skill mappings
        skill_mappings = {
            'js': 'JavaScript',
            'ts': 'TypeScript',
            'py': 'Python',
            'cpp': 'C++',
            'c++': 'C++',
            'reactjs': 'React',
            'nodejs': 'Node.js',
            'mysql': 'MySQL',
            'postgresql': 'PostgreSQL',
            'mongodb': 'MongoDB'
        }
        
        skill_lower = skill.lower().strip()
        return skill_mappings.get(skill_lower, skill.strip())
    
    def _fallback_extraction(self, text: str) -> Dict[str, Any]:
        """Fallback entity extraction when NER model is not available"""
        entities = {}
        
        # Extract emails
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if emails:
            entities['Email Addresses'] = emails
        
        # Extract phone numbers
        phones = re.findall(r'[\+]?[1-9]?[\-.\s]?\(?[0-9]{3}\)?[\-.\s]?[0-9]{3}[\-.\s]?[0-9]{4,6}', text)
        if phones:
            entities['Phone Numbers'] = phones
        
        # Extract common programming languages
        prog_languages = []
        lang_patterns = ['Python', 'JavaScript', 'Java', 'C++', 'React', 'Node.js', 'SQL', 'HTML', 'CSS']
        for lang in lang_patterns:
            if re.search(rf'\b{re.escape(lang)}\b', text, re.IGNORECASE):
                prog_languages.append(lang)
        
        if prog_languages:
            entities['Programming Languages'] = prog_languages
        
        return {
            'success': True,
            'entities': entities,
            'total_entities': sum(len(v) for v in entities.values()),
            'model_used': 'fallback_regex',
            'message': 'Entities extracted using fallback method'
        }
    
    def get_entity_summary(self, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Generate a summary of extracted entities"""
        summary = {
            'total_entities': sum(len(v) for v in entities.values()),
            'entity_types': len(entities),
            'breakdown': {}
        }
        
        for entity_type, entity_list in entities.items():
            summary['breakdown'][entity_type] = {
                'count': len(entity_list),
                'items': entity_list[:5]  # Show first 5 items
            }
        
        return summary
    
    def search_entities_by_type(self, entities: Dict[str, List[str]], search_type: str) -> List[str]:
        """Search for specific type of entities"""
        for entity_type, entity_list in entities.items():
            if search_type.lower() in entity_type.lower():
                return entity_list
        return []
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the NER model"""
        return {
            'model_name': self.model_name,
            'model_loaded': self.model is not None,
            'supported_entities': list(self.entity_labels.keys()),
            'entity_descriptions': self.entity_labels,
            'device': 'cuda' if torch.cuda.is_available() else 'cpu'
        }


# Global service instance
resume_ner_service = None

def get_resume_ner_service() -> ResumeNERService:
    """Get or create global Resume NER service instance"""
    global resume_ner_service
    if resume_ner_service is None:
        resume_ner_service = ResumeNERService()
    return resume_ner_service
