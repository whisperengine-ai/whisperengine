"""
ChatGPT Import Package for WhisperEngine

This package provides tools to import ChatGPT conversation history
into WhisperEngine's memory system, allowing users to transfer their
conversation context and personality insights.
"""

__version__ = "1.0.0"
__author__ = "WhisperEngine Team"

from .importer import ChatGPTImporter

__all__ = ['ChatGPTImporter']