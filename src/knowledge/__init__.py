"""
Knowledge Management Module

Handles structured factual knowledge and semantic relationships.
"""

from .semantic_router import (
    SemanticKnowledgeRouter,
    QueryIntent,
    IntentAnalysisResult,
    create_semantic_knowledge_router
)

__all__ = [
    "SemanticKnowledgeRouter",
    "QueryIntent", 
    "IntentAnalysisResult",
    "create_semantic_knowledge_router"
]
