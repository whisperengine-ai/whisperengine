"""
Roleplay subsystem for WhisperEngine

Provides lightweight state management for transactional roleplay interactions.
"""

from src.roleplay.transaction_manager import (
    TransactionManager,
    RoleplayTransaction,
    TransactionState,
    create_transaction_manager,
)

from src.roleplay.workflow_manager import (
    WorkflowManager,
    WorkflowFile,
    WorkflowTriggerResult,
)

__all__ = [
    "TransactionManager",
    "RoleplayTransaction",
    "TransactionState",
    "create_transaction_manager",
    "WorkflowManager",
    "WorkflowFile",
    "WorkflowTriggerResult",
]
