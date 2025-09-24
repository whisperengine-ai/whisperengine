"""
Event Handler Services Package

This package contains services that were extracted from the main events.py file
to improve code organization and maintainability.

Services:
- MessageProcessingService: Handles DM, guild, and mention message processing
"""

from .message_processing_service import MessageProcessingService

__all__ = [
    'MessageProcessingService',
]