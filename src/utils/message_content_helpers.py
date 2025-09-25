#!/usr/bin/env python3
"""
Message Content Helpers
Utility functions for safely handling message content that can be either strings or lists (for vision messages)
"""

from typing import Union, List, Dict, Any


def extract_text_content(content: Union[str, List[Dict[str, Any]]]) -> str:
    """
    Extract text content from message content that could be string or list (for vision messages)
    
    Args:
        content: Message content that could be a string or list of content parts
        
    Returns:
        String representation of the text content
    """
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # Extract text from multimodal content
        text_parts = []
        for part in content:
            if isinstance(part, dict):
                if part.get("type") == "text" and part.get("text"):
                    text_parts.append(part["text"])
            elif isinstance(part, str):
                text_parts.append(part)
        return " ".join(text_parts)
    else:
        # Convert other types to string
        return str(content) if content else ""


def safe_lower(content: Union[str, List[Dict[str, Any]]]) -> str:
    """
    Safely call .lower() on content that might be a string or list
    
    Args:
        content: Message content that could be a string or list of content parts
        
    Returns:
        Lowercase string representation of the text content
    """
    return extract_text_content(content).lower()


def content_contains(content: Union[str, List[Dict[str, Any]]], search_term: str) -> bool:
    """
    Check if content contains a search term, handling both string and list content
    
    Args:
        content: Message content that could be a string or list
        search_term: Term to search for
        
    Returns:
        True if the search term is found in the text content
    """
    return search_term in extract_text_content(content)


def content_contains_any(content: Union[str, List[Dict[str, Any]]], search_terms: List[str]) -> bool:
    """
    Check if content contains any of the search terms
    
    Args:
        content: Message content that could be a string or list
        search_terms: List of terms to search for
        
    Returns:
        True if any search term is found in the text content
    """
    text_content = extract_text_content(content).lower()
    return any(term.lower() in text_content for term in search_terms)