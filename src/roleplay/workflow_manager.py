"""
Workflow Manager
================

Manages YAML-based workflows for transaction-oriented character interactions.

This module implements a hybrid approach to transaction management:
1. Declarative workflows (YAML-defined patterns and state machines)
2. Dynamic LLM fallback (for edge cases not covered by workflows)

Key Features:
- YAML workflow file loading
- Regex pattern and keyword matching for intent detection
- Context extraction from messages (regex groups, lookups, literals)
- State transition detection and management
- Prompt injection for LLM guidance
- Optional LLM validation for ambiguous intents
"""

import re
import yaml
import json
import logging
import asyncio
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple

from src.roleplay.transaction_manager import TransactionManager


@dataclass
class WorkflowFile:
    """Represents a loaded workflow YAML file"""
    version: str
    character: str
    description: str
    workflows: Dict[str, Any]
    lookup_tables: Dict[str, Any]
    config: Dict[str, Any]
    file_path: str


@dataclass
class WorkflowTriggerResult:
    """Result of workflow intent detection"""
    workflow_name: str
    workflow_def: Dict[str, Any]
    extracted_context: Dict[str, Any]
    match_confidence: float
    pattern_match: Optional[re.Match] = None


class WorkflowManager:
    """
    Manages YAML-based workflows for characters
    
    Responsibilities:
    - Load workflow YAML files referenced in CDL
    - Detect workflow triggers (patterns, keywords, LLM validation)
    - Extract context from messages (regex groups, lookups)
    - Execute workflow actions (create/update/complete transactions)
    - Manage state transitions
    - Generate prompt injections for LLM guidance
    """
    
    def __init__(self, transaction_manager: TransactionManager, llm_client=None):
        """
        Initialize WorkflowManager
        
        Args:
            transaction_manager: TransactionManager instance for state persistence
            llm_client: Optional LLM client for intent validation and tool calling
        """
        self.transaction_manager = transaction_manager
        self.llm_client = llm_client
        self.loaded_workflows: Dict[str, WorkflowFile] = {}
        self.logger = logging.getLogger(__name__)
    
    # =========================================================================
    # Workflow Loading
    # =========================================================================
    
    async def load_workflows_for_character(self, character_name: str) -> bool:
        """
        Load workflows from database-based character configuration
        
        Args:
            character_name: Character name (e.g., 'jake', 'elena')
            
        Returns:
            True if workflows loaded successfully, False otherwise
        """
        try:
            # 1. Load character data from database to get workflow file references
            character_data = await self._load_character_from_database(character_name)
            
            # Look for transaction_config in character data
            transaction_config = character_data.get("transaction_config", {})
            workflow_files = transaction_config.get("workflow_files", [])
            
            if not workflow_files:
                self.logger.info(f"No workflow files configured for character '{character_name}'")
                return False
            
            # 2. Load each workflow file
            for workflow_file_path in workflow_files:
                await self._load_workflow_file(workflow_file_path, character_name)
            
            self.logger.info(f"✅ Loaded {len(workflow_files)} workflow file(s) for {character_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load workflows for character '{character_name}': {e}")
            return False
    
    async def _load_character_from_database(self, character_name: str) -> Dict[str, Any]:
        """Load character data from database - NO-OP during CDL migration"""
        # TODO: Implement workflow-specific character data loading once CDL migration is complete
        # For now, return empty transaction_config to allow system to work without workflows
        self.logger.info("📝 Workflow Manager: CDL migration in progress - no workflows configured for '%s'", character_name)
        
        return {
            "identity": {
                "name": character_name
            },
            "transaction_config": {
                "workflow_files": []  # No workflows during migration
            }
        }
    
    async def _load_workflow_file(self, workflow_file: str, character_name: str):
        """
        Load YAML workflow file
        
        Args:
            workflow_file: Path to YAML workflow file
            character_name: Name of character (for indexing)
        """
        file_path = Path(workflow_file)
        if not file_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_file}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            workflow_data = yaml.safe_load(f)
        
        # Validate schema
        required_fields = ["version", "workflows"]
        for field in required_fields:
            if field not in workflow_data:
                raise ValueError(f"Workflow file missing required field: {field}")
        
        # Store loaded workflow
        workflow_file_obj = WorkflowFile(
            version=workflow_data.get("version"),
            character=workflow_data.get("character", character_name),
            description=workflow_data.get("description", ""),
            workflows=workflow_data.get("workflows", {}),
            lookup_tables=workflow_data.get("lookup_tables", {}),
            config=workflow_data.get("config", {}),
            file_path=str(file_path)
        )
        
        # Index by character name for quick lookup
        self.loaded_workflows[character_name.lower()] = workflow_file_obj
        
        workflow_count = len(workflow_file_obj.workflows)
        self.logger.info(f"✅ Loaded workflow file: {workflow_file} ({workflow_count} workflows)")
    
    # =========================================================================
    # Intent Detection
    # =========================================================================
    
    async def detect_intent(
        self, 
        message: str, 
        user_id: str, 
        bot_name: str
    ) -> Optional[WorkflowTriggerResult]:
        """
        Detect if message triggers any workflow
        
        Args:
            message: User message
            user_id: User ID
            bot_name: Bot name
            
        Returns:
            WorkflowTriggerResult if workflow triggered, None otherwise
        """
        # Get workflows for this bot
        workflow_file = self.loaded_workflows.get(bot_name.lower())
        if not workflow_file:
            return None
        
        # Check if user already has pending transaction
        pending = await self.transaction_manager.check_pending_transaction(user_id, bot_name)
        
        if pending:
            # Check for state transition in existing workflow
            return await self._check_state_transition(
                pending, workflow_file, message, user_id, bot_name
            )
        
        # Check each workflow for new trigger
        for workflow_name, workflow_def in workflow_file.workflows.items():
            trigger_result = await self._check_workflow_trigger(
                workflow_name, workflow_def, workflow_file, message, user_id, bot_name
            )
            
            if trigger_result:
                return trigger_result
        
        return None
    
    async def _check_workflow_trigger(
        self, 
        workflow_name: str, 
        workflow_def: Dict[str, Any],
        workflow_file: WorkflowFile,
        message: str, 
        user_id: str, 
        bot_name: str
    ) -> Optional[WorkflowTriggerResult]:
        """
        Check if message triggers a specific workflow
        
        Args:
            workflow_name: Name of workflow
            workflow_def: Workflow definition dict
            workflow_file: Loaded workflow file
            message: User message
            user_id: User ID
            bot_name: Bot name
            
        Returns:
            WorkflowTriggerResult if triggered, None otherwise
        """
        triggers = workflow_def.get("triggers", {})
        
        # 1. Pattern matching (regex)
        patterns = triggers.get("patterns", [])
        pattern_match = None
        
        self.logger.debug(f"🔍 WORKFLOW: Checking workflow '{workflow_name}' with {len(patterns)} patterns")
        
        for pattern in patterns:
            try:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    pattern_match = match
                    self.logger.info(f"✅ WORKFLOW: Pattern matched for '{workflow_name}': {pattern}")
                    break
                else:
                    self.logger.debug(f"❌ WORKFLOW: Pattern '{pattern}' did not match message")
            except re.error as e:
                self.logger.warning(f"Invalid regex pattern '{pattern}': {e}")
                continue
        
        # 2. Keyword matching
        keywords = triggers.get("keywords", [])
        keyword_found = any(kw.lower() in message.lower() for kw in keywords)
        
        # 3. Must match pattern OR keyword (unless both required)
        if not pattern_match and not keyword_found:
            return None
        
        # 4. Extract context from match
        extracted_context = await self._extract_context(
            workflow_def, workflow_file, message, pattern_match
        )
        
        # 5. Validate extracted context
        if not await self._validate_context(workflow_def, extracted_context):
            return None
        
        # 6. LLM validation (if required)
        llm_validation = triggers.get("llm_validation", {})
        if llm_validation.get("enabled", False):
            if not self.llm_client:
                self.logger.warning("LLM validation required but no LLM client available")
                return None
            
            llm_confirms = await self._llm_validate_intent(
                llm_validation, message, workflow_name
            )
            if not llm_confirms:
                self.logger.debug(f"LLM rejected workflow trigger: {workflow_name}")
                return None
        
        # Trigger confirmed!
        confidence = 0.95 if pattern_match else 0.75
        
        return WorkflowTriggerResult(
            workflow_name=workflow_name,
            workflow_def=workflow_def,
            extracted_context=extracted_context,
            match_confidence=confidence,
            pattern_match=pattern_match
        )
    
    async def _check_state_transition(
        self,
        pending_transaction,
        workflow_file: WorkflowFile,
        message: str,
        user_id: str,
        bot_name: str
    ) -> Optional[WorkflowTriggerResult]:
        """
        Check if message triggers state transition for pending transaction
        
        Args:
            pending_transaction: Pending transaction object
            workflow_file: Loaded workflow file
            message: User message
            user_id: User ID
            bot_name: Bot name
            
        Returns:
            WorkflowTriggerResult if state transition detected, None otherwise
        """
        workflow_name = pending_transaction.transaction_type
        workflow_def = workflow_file.workflows.get(workflow_name)
        
        if not workflow_def:
            self.logger.warning(f"Pending transaction has unknown workflow: {workflow_name}")
            return None
        
        current_state = pending_transaction.state
        states = workflow_def.get("states", {})
        current_state_def = states.get(current_state, {})
        
        # Check transitions
        transitions = current_state_def.get("transitions", [])
        for transition in transitions:
            if await self._check_transition_trigger(transition, message):
                # State transition detected!
                return WorkflowTriggerResult(
                    workflow_name=workflow_name,
                    workflow_def=workflow_def,
                    extracted_context={"transition": transition},
                    match_confidence=0.9,
                    pattern_match=None
                )
        
        return None
    
    async def _check_transition_trigger(
        self, 
        transition: Dict[str, Any], 
        message: str
    ) -> bool:
        """Check if message triggers a state transition"""
        triggers = transition.get("triggers", {})
        
        # Pattern matching
        patterns = triggers.get("patterns", [])
        for pattern in patterns:
            try:
                if re.search(pattern, message, re.IGNORECASE):
                    return True
            except re.error as e:
                self.logger.warning(f"Invalid transition pattern '{pattern}': {e}")
                continue
        
        # Keyword matching
        keywords = triggers.get("keywords", [])
        if any(kw.lower() in message.lower() for kw in keywords):
            return True
        
        return False
    
    # =========================================================================
    # Context Extraction
    # =========================================================================
    
    async def _extract_context(
        self, 
        workflow_def: Dict[str, Any],
        workflow_file: WorkflowFile,
        message: str, 
        pattern_match: Optional[re.Match]
    ) -> Dict[str, Any]:
        """
        Extract context from message based on workflow definition
        
        Args:
            workflow_def: Workflow definition
            workflow_file: Loaded workflow file (for lookup tables)
            message: User message
            pattern_match: Regex match object (if pattern matched)
            
        Returns:
            Extracted context dict
        """
        on_trigger = workflow_def.get("on_trigger", {})
        extract_config = on_trigger.get("extract_context", {})
        
        context = {}
        
        for field_name, extract_def in extract_config.items():
            from_type = extract_def.get("from")
            
            if from_type == "pattern_group" and pattern_match:
                # Extract from regex capture group
                group_num = extract_def.get("group", 1)
                try:
                    value = pattern_match.group(group_num)
                    if value:
                        value = value.strip()
                        # Apply transform if specified
                        transform = extract_def.get("transform")
                        if transform == "lowercase":
                            value = value.lower()
                        elif transform == "uppercase":
                            value = value.upper()
                        context[field_name] = value
                    else:
                        context[field_name] = extract_def.get("default", "")
                except (IndexError, AttributeError):
                    context[field_name] = extract_def.get("default", "")
            
            elif from_type == "lookup":
                # Look up value in table
                table_name = extract_def.get("table")
                key_template = extract_def.get("key", "")
                
                # Format key with already extracted context
                try:
                    key = key_template.format(**context)
                except KeyError:
                    key = key_template
                
                if table_name in workflow_file.lookup_tables:
                    lookup_table = workflow_file.lookup_tables[table_name]
                    context[field_name] = lookup_table.get(key, extract_def.get("default", 0))
                else:
                    context[field_name] = extract_def.get("default", 0)
            
            elif from_type == "message":
                # Use full message
                context[field_name] = message
            
            elif from_type == "literal":
                # Use literal value
                context[field_name] = extract_def.get("value")
        
        return context
    
    async def _validate_context(
        self, 
        workflow_def: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> bool:
        """
        Validate extracted context against workflow rules
        
        Args:
            workflow_def: Workflow definition
            context: Extracted context
            
        Returns:
            True if valid, False otherwise
        """
        on_trigger = workflow_def.get("on_trigger", {})
        validation_rules = on_trigger.get("validation", [])
        
        for rule in validation_rules:
            field = rule.get("field")
            rule_type = rule.get("rule")
            on_fail = rule.get("on_fail", "reject")
            
            if field not in context:
                continue
            
            value = context[field]
            
            if rule_type == "in_list":
                allowed_values = rule.get("values", [])
                # Case-insensitive comparison
                if value.lower() not in [v.lower() for v in allowed_values]:
                    if on_fail == "reject":
                        self.logger.debug(f"Validation failed: {value} not in {allowed_values}")
                        return False
                    elif on_fail == "use_default":
                        context[field] = rule.get("default", value)
        
        return True
    
    async def _llm_validate_intent(
        self, 
        llm_validation: Dict[str, Any], 
        message: str, 
        workflow_name: str
    ) -> bool:
        """
        Use LLM to validate if intent matches workflow
        
        Args:
            llm_validation: LLM validation config
            message: User message
            workflow_name: Workflow name
            
        Returns:
            True if LLM confirms intent, False otherwise
        """
        prompt_template = llm_validation.get("prompt", "")
        prompt = prompt_template.format(message=message)
        threshold = llm_validation.get("confidence_threshold", 0.7)
        
        # Skip if no LLM client configured
        if not self.llm_client:
            self.logger.error("Skipping LLM validation - no LLM client available")
            return False
        
        try:
            # Use generate_completion for yes/no validation
            response = self.llm_client.generate_completion(
                prompt=prompt,
                max_tokens=10,
                temperature=0.1
            )
            
            # Extract text from completion response
            if "choices" not in response:
                self.logger.error(f"Invalid LLM response format - missing 'choices' key")
                return False
                
            text = response["choices"][0]["text"].strip()
            self.logger.info(f"🎯 LLM VALIDATION RESULT: {text}")
            
            # Check if answer indicates "yes"
            answer = text.lower()
            is_yes = "yes" in answer or "true" in answer
            
            return is_yes
            
        except Exception as e:
            self.logger.error(f"LLM validation failed: {e}")
            return False  # Fail closed
    
    # =========================================================================
    # Workflow Execution
    # =========================================================================
    
    async def execute_workflow_action(
        self, 
        trigger_result: WorkflowTriggerResult, 
        user_id: str, 
        bot_name: str, 
        message: str
    ) -> Dict[str, Any]:
        """
        Execute workflow action (create transaction, update state, etc.)
        
        Args:
            trigger_result: Workflow trigger result
            user_id: User ID
            bot_name: Bot name
            message: User message
            
        Returns:
            Result dict with transaction_id, state, prompt_injection, etc.
        """
        workflow_name = trigger_result.workflow_name
        workflow_def = trigger_result.workflow_def
        extracted_context = trigger_result.extracted_context
        
        # Check for pending transaction
        pending = await self.transaction_manager.check_pending_transaction(user_id, bot_name)
        
        if pending and "transition" in extracted_context:
            # Existing transaction - handle state transition
            return await self._handle_state_transition(
                pending, workflow_def, message, extracted_context
            )
        elif not pending:
            # New transaction - execute on_trigger action
            return await self._handle_new_workflow(
                workflow_name, workflow_def, user_id, bot_name, extracted_context
            )
        else:
            # Pending transaction exists but no transition detected
            return {
                "no_action": True,
                "reason": "Pending transaction exists but no transition detected"
            }
    
    async def _handle_new_workflow(
        self,
        workflow_name: str,
        workflow_def: Dict[str, Any],
        user_id: str,
        bot_name: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle new workflow trigger - create transaction
        
        Args:
            workflow_name: Workflow name
            workflow_def: Workflow definition
            user_id: User ID
            bot_name: Bot name
            context: Extracted context
            
        Returns:
            Result dict with transaction details
        """
        on_trigger = workflow_def.get("on_trigger", {})
        action = on_trigger.get("action")
        
        if action == "create_transaction":
            initial_state = workflow_def.get("initial_state", "pending")
            
            # Create transaction
            transaction_id = await self.transaction_manager.create_transaction(
                user_id=user_id,
                bot_name=bot_name,
                transaction_type=workflow_name,
                context=context,
                state=initial_state
            )
            
            # Get prompt injection for initial state
            prompt_injection = self._get_state_prompt_injection(
                workflow_def, initial_state, context
            )
            
            self.logger.info(
                f"✅ Created transaction {transaction_id}: {workflow_name} "
                f"for user {user_id} (state: {initial_state})"
            )
            
            return {
                "transaction_id": transaction_id,
                "workflow_name": workflow_name,
                "state": initial_state,
                "prompt_injection": prompt_injection,
                "context": context,
                "action": "created"
            }
        
        return {"no_action": True, "reason": f"Unknown action: {action}"}
    
    async def _handle_state_transition(
        self,
        pending_transaction,
        workflow_def: Dict[str, Any],
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle state transition for existing transaction
        
        Args:
            pending_transaction: Pending transaction object
            workflow_def: Workflow definition
            message: User message
            context: Extracted context (includes transition info)
            
        Returns:
            Result dict with state transition details
        """
        transition = context.get("transition", {})
        next_state = transition.get("to_state")
        action = transition.get("action")
        
        if not next_state:
            return {"no_action": True, "reason": "No next state specified"}
        
        # Merge existing context with any new context
        updated_context = {**pending_transaction.context, **context}
        updated_context.pop("transition", None)  # Remove transition metadata
        
        # Execute action
        if action == "complete_transaction":
            await self.transaction_manager.complete_transaction(
                pending_transaction.id,
                final_context=updated_context
            )
            action_type = "completed"
        elif action == "cancel_transaction":
            await self.transaction_manager.cancel_transaction(
                pending_transaction.id,
                reason="User cancelled"
            )
            action_type = "cancelled"
        else:
            # Update to next state
            await self.transaction_manager.update_transaction_state(
                pending_transaction.id,
                new_state=next_state,
                context_updates=updated_context
            )
            action_type = "updated"
        
        # Get prompt injection for next state
        prompt_injection = self._get_state_prompt_injection(
            workflow_def, next_state, updated_context
        )
        
        self.logger.info(
            f"✅ {action_type.capitalize()} transaction {pending_transaction.id}: "
            f"{pending_transaction.transaction_type} → {next_state}"
        )
        
        return {
            "transaction_id": pending_transaction.id,
            "workflow_name": pending_transaction.transaction_type,
            "state": next_state,
            "prompt_injection": prompt_injection,
            "context": updated_context,
            "action": action_type
        }
    
    def _get_state_prompt_injection(
        self, 
        workflow_def: Dict[str, Any], 
        state: str, 
        context: Dict[str, Any]
    ) -> str:
        """
        Get prompt injection for a specific workflow state
        
        Args:
            workflow_def: Workflow definition
            state: State name
            context: Transaction context
            
        Returns:
            Formatted prompt injection string
        """
        states = workflow_def.get("states", {})
        state_def = states.get(state, {})
        prompt_injection = state_def.get("prompt_injection", "")
        
        # Format with context (use SimpleNamespace for dot notation)
        try:
            from types import SimpleNamespace
            context_obj = SimpleNamespace(**context)
            return prompt_injection.format(context=context_obj)
        except (KeyError, AttributeError) as e:
            self.logger.warning(f"Context formatting error: {e}")
            # Fallback: try dict-style formatting
            try:
                return prompt_injection.format(**context)
            except KeyError:
                return prompt_injection
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def get_workflow_prompt_injection(
        self, 
        bot_name: str, 
        pending_transaction
    ) -> str:
        """
        Get prompt injection for current transaction state
        
        Args:
            bot_name: Bot name
            pending_transaction: Pending transaction object
            
        Returns:
            Formatted prompt injection string
        """
        workflow_file = self.loaded_workflows.get(bot_name.lower())
        if not workflow_file:
            return ""
        
        workflow_name = pending_transaction.transaction_type
        workflow_def = workflow_file.workflows.get(workflow_name)
        if not workflow_def:
            return ""
        
        return self._get_state_prompt_injection(
            workflow_def, 
            pending_transaction.state, 
            pending_transaction.context
        )
    
    def get_workflow_count(self, bot_name: str) -> int:
        """Get number of loaded workflows for bot"""
        workflow_file = self.loaded_workflows.get(bot_name.lower())
        return len(workflow_file.workflows) if workflow_file else 0
    
    def is_loaded(self, bot_name: str) -> bool:
        """Check if workflows are loaded for bot"""
        return bot_name.lower() in self.loaded_workflows
