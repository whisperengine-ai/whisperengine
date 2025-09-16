"""
PII Detection System for Privacy-Aware Fact Classification

This module provides automatic detection of personally identifiable information (PII)
and sensitive content in facts to ensure appropriate privacy classification.
"""

import re
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum, IntEnum

logger = logging.getLogger(__name__)


class PIIType(Enum):
    """Types of PII that can be detected"""
    PERSONAL_NAME = "personal_name"
    EMAIL_ADDRESS = "email_address"
    PHONE_NUMBER = "phone_number" 
    ADDRESS = "address"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    MEDICAL_INFO = "medical_info"
    MENTAL_HEALTH = "mental_health"
    FINANCIAL_INFO = "financial_info"
    PERSONAL_RELATIONSHIP = "personal_relationship"
    PERSONAL_PREFERENCE = "personal_preference"
    LOCATION_SPECIFIC = "location_specific"
    TEMPORAL_PERSONAL = "temporal_personal"


class SensitivityLevel(IntEnum):
    """Levels of sensitivity for detected content (ordered by sensitivity)"""
    PUBLIC = 1                           # Safe to share anywhere
    PERSONAL = 2                         # User-specific but not highly sensitive
    SENSITIVE = 3                        # Requires privacy protection
    HIGHLY_SENSITIVE = 4                 # Requires maximum privacy


@dataclass
class PIIDetection:
    """Result of PII detection analysis"""
    pii_type: PIIType
    confidence: float
    matched_text: str
    sensitivity_level: SensitivityLevel
    reason: str


@dataclass
class PIIAnalysis:
    """Complete PII analysis of a fact"""
    contains_pii: bool
    highest_sensitivity: SensitivityLevel
    detections: List[PIIDetection]
    recommended_security_level: str
    analysis_confidence: float


class PIIDetector:
    """
    Detects personally identifiable information and sensitive content in facts
    """
    
    def __init__(self):
        self.setup_patterns()
        self.setup_keywords()
    
    def setup_patterns(self):
        """Setup regex patterns for PII detection"""
        self.patterns = {
            PIIType.EMAIL_ADDRESS: re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            PIIType.PHONE_NUMBER: re.compile(r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
            PIIType.SSN: re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            PIIType.CREDIT_CARD: re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
        }
    
    def setup_keywords(self):
        """Setup keyword sets for content classification"""
        self.keywords = {
            PIIType.MENTAL_HEALTH: {
                'depression', 'anxiety', 'bipolar', 'ptsd', 'panic attacks', 'therapy', 
                'therapist', 'psychiatrist', 'antidepressant', 'mental health',
                'suicidal', 'self-harm', 'eating disorder', 'addiction', 'trauma'
            },
            PIIType.MEDICAL_INFO: {
                'diabetes', 'cancer', 'surgery', 'medication', 'doctor', 'hospital',
                'prescription', 'diagnosis', 'symptoms', 'treatment', 'illness',
                'disease', 'medical', 'health condition', 'allergic', 'chronic'
            },
            PIIType.FINANCIAL_INFO: {
                'salary', 'income', 'debt', 'loan', 'mortgage', 'bankruptcy',
                'credit score', 'bank account', 'investment', 'retirement',
                'financial', 'money problems', 'unemployed', 'fired'
            },
            PIIType.PERSONAL_RELATIONSHIP: {
                'my wife', 'my husband', 'my boyfriend', 'my girlfriend', 'my partner',
                'my ex', 'my mother', 'my father', 'my brother', 'my sister',
                'my child', 'my kid', 'my family', 'my friend', 'relationship problems'
            },
            PIIType.LOCATION_SPECIFIC: {
                'my address', 'my home', 'my workplace', 'my school', 'my office',
                'where I live', 'where I work', 'my neighborhood', 'my city'
            }
        }
        
        # Personal indicators that suggest user-specific content
        self.personal_indicators = {
            'i am', 'i have', 'i was', 'i will', 'i like', 'i dislike', 'i love',
            'i hate', 'my', 'mine', 'myself', 'i feel', 'i think', 'i believe',
            'i went', 'i do', 'i did', 'i work', 'i live', 'i study'
        }
        
        # Temporal personal indicators
        self.temporal_personal = {
            'yesterday i', 'today i', 'last week i', 'last month i', 'recently i',
            'this morning i', 'tonight i', 'tomorrow i', 'next week i'
        }
    
    def analyze_fact_for_pii(self, fact_text: str) -> PIIAnalysis:
        """
        Analyze a fact for PII and sensitive content
        
        Args:
            fact_text: The fact text to analyze
            
        Returns:
            PIIAnalysis with detection results and recommendations
        """
        try:
            detections = []
            fact_lower = fact_text.lower().strip()
            
            # Check regex patterns
            detections.extend(self._check_patterns(fact_text))
            
            # Check keyword categories
            detections.extend(self._check_keywords(fact_lower))
            
            # Check personal indicators
            detections.extend(self._check_personal_indicators(fact_lower))
            
            # Check temporal personal indicators
            detections.extend(self._check_temporal_indicators(fact_lower))
            
            # Determine overall analysis
            analysis = self._analyze_detections(detections, fact_text)
            
            logger.debug(f"PII analysis for '{fact_text[:50]}...': "
                        f"PII={analysis.contains_pii}, "
                        f"Sensitivity={analysis.highest_sensitivity.value}, "
                        f"Detections={len(detections)}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in PII analysis: {e}")
            # Default to highly sensitive for safety
            return PIIAnalysis(
                contains_pii=True,
                highest_sensitivity=SensitivityLevel.HIGHLY_SENSITIVE,
                detections=[],
                recommended_security_level="private_dm",
                analysis_confidence=0.5
            )
    
    def _check_patterns(self, fact_text: str) -> List[PIIDetection]:
        """Check regex patterns for PII"""
        detections = []
        
        for pii_type, pattern in self.patterns.items():
            matches = pattern.findall(fact_text)
            for match in matches:
                detections.append(PIIDetection(
                    pii_type=pii_type,
                    confidence=0.95,
                    matched_text=match,
                    sensitivity_level=SensitivityLevel.HIGHLY_SENSITIVE,
                    reason=f"Regex pattern match for {pii_type.value}"
                ))
        
        return detections
    
    def _check_keywords(self, fact_lower: str) -> List[PIIDetection]:
        """Check keyword categories for sensitive content"""
        detections = []
        
        for pii_type, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword in fact_lower:
                    sensitivity = self._get_keyword_sensitivity(pii_type)
                    detections.append(PIIDetection(
                        pii_type=pii_type,
                        confidence=0.8,
                        matched_text=keyword,
                        sensitivity_level=sensitivity,
                        reason=f"Keyword match for {pii_type.value}: '{keyword}'"
                    ))
        
        return detections
    
    def _check_personal_indicators(self, fact_lower: str) -> List[PIIDetection]:
        """Check for personal indicators that suggest user-specific content"""
        detections = []
        
        for indicator in self.personal_indicators:
            if indicator in fact_lower:
                detections.append(PIIDetection(
                    pii_type=PIIType.PERSONAL_PREFERENCE,
                    confidence=0.7,
                    matched_text=indicator,
                    sensitivity_level=SensitivityLevel.PERSONAL,
                    reason=f"Personal indicator: '{indicator}'"
                ))
        
        return detections
    
    def _check_temporal_indicators(self, fact_lower: str) -> List[PIIDetection]:
        """Check for temporal personal indicators"""
        detections = []
        
        for indicator in self.temporal_personal:
            if indicator in fact_lower:
                detections.append(PIIDetection(
                    pii_type=PIIType.TEMPORAL_PERSONAL,
                    confidence=0.85,
                    matched_text=indicator,
                    sensitivity_level=SensitivityLevel.SENSITIVE,
                    reason=f"Temporal personal indicator: '{indicator}'"
                ))
        
        return detections
    
    def _get_keyword_sensitivity(self, pii_type: PIIType) -> SensitivityLevel:
        """Get sensitivity level for keyword categories"""
        sensitivity_map = {
            PIIType.MENTAL_HEALTH: SensitivityLevel.HIGHLY_SENSITIVE,
            PIIType.MEDICAL_INFO: SensitivityLevel.HIGHLY_SENSITIVE,
            PIIType.FINANCIAL_INFO: SensitivityLevel.SENSITIVE,
            PIIType.PERSONAL_RELATIONSHIP: SensitivityLevel.SENSITIVE,
            PIIType.LOCATION_SPECIFIC: SensitivityLevel.SENSITIVE,
        }
        return sensitivity_map.get(pii_type, SensitivityLevel.PERSONAL)
    
    def _analyze_detections(self, detections: List[PIIDetection], fact_text: str) -> PIIAnalysis:
        """Analyze all detections to create final assessment"""
        if not detections:
            # No PII detected - check if it's general knowledge
            return PIIAnalysis(
                contains_pii=False,
                highest_sensitivity=SensitivityLevel.PUBLIC,
                detections=[],
                recommended_security_level="cross_context_safe",
                analysis_confidence=0.8
            )
        
        # Find highest sensitivity level
        highest_sensitivity = max(d.sensitivity_level for d in detections)
        
        # Calculate average confidence
        avg_confidence = sum(d.confidence for d in detections) / len(detections)
        
        # Determine recommended security level
        security_map = {
            SensitivityLevel.PUBLIC: "cross_context_safe",
            SensitivityLevel.PERSONAL: "server_private", 
            SensitivityLevel.SENSITIVE: "private_dm",
            SensitivityLevel.HIGHLY_SENSITIVE: "private_dm"
        }
        
        recommended_security = security_map[highest_sensitivity]
        
        return PIIAnalysis(
            contains_pii=True,
            highest_sensitivity=highest_sensitivity,
            detections=detections,
            recommended_security_level=recommended_security,
            analysis_confidence=avg_confidence
        )
    
    def is_general_knowledge(self, fact_text: str) -> bool:
        """
        Determine if a fact represents general knowledge safe for sharing
        
        Args:
            fact_text: The fact to analyze
            
        Returns:
            True if the fact appears to be general knowledge
        """
        fact_lower = fact_text.lower()
        
        # Check for personal indicators
        for indicator in self.personal_indicators:
            if indicator in fact_lower:
                return False
        
        # Check for temporal personal indicators
        for indicator in self.temporal_personal:
            if indicator in fact_lower:
                return False
        
        # Check for sensitive keywords
        for keywords in self.keywords.values():
            for keyword in keywords:
                if keyword in fact_lower:
                    return False
        
        # If no personal/sensitive content detected, likely general knowledge
        return True


def get_pii_detector() -> PIIDetector:
    """Get a PII detector instance (singleton pattern)"""
    if not hasattr(get_pii_detector, '_instance'):
        get_pii_detector._instance = PIIDetector()
    return get_pii_detector._instance