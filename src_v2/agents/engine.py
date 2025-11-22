from typing import List, Dict, Any, Optional
import json
import datetime
from pathlib import Path
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from loguru import logger

from src_v2.config.settings import settings
from src_v2.core.character import Character
from src_v2.agents.llm_factory import create_llm
from src_v2.agents.router import CognitiveRouter
from src_v2.evolution.trust import trust_manager
from src_v2.evolution.goals import goal_manager
from src_v2.evolution.feedback import feedback_analyzer

class AgentEngine:
    def __init__(self):
        self.llm = create_llm()
        self.router = CognitiveRouter()
        logger.info("AgentEngine initialized")

    async def generate_response(
        self, 
        character: Character, 
        user_message: str, 
        chat_history: Optional[List[BaseMessage]] = None,
        context_variables: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        image_urls: Optional[List[str]] = None
    ) -> str:
        """
        Generates a response for the given character and user message.
        """
        chat_history = chat_history or []
        context_variables = context_variables or {}
        
        # 1. Cognitive Routing (The "Brain")
        # Only run if we have a user_id to look up memories for AND memory_context isn't already provided
        if user_id and not context_variables.get("memory_context"):
            try:
                router_result = await self.router.route_and_retrieve(user_id, user_message)
                memory_context = router_result.get("context", "")
                reasoning = router_result.get("reasoning", "")
                
                if memory_context:
                    logger.info(f"Injecting memory context. Reasoning: {reasoning}")
                    # Inject into context_variables so it can be used in the prompt if {memory_context} exists,
                    # or append to system prompt.
                    context_variables["memory_context"] = memory_context
                    context_variables["router_reasoning"] = reasoning
                else:
                    logger.debug(f"No memory context retrieved. Reasoning: {reasoning}")
            except Exception as e:
                logger.error(f"Cognitive Router failed: {e}")

        # 2. Construct System Prompt
        # The character object already contains the full prompt loaded from the markdown file
        system_content = character.system_prompt
        
        # 2.1 Inject Past Summaries (Long-term Context)
        if context_variables.get("past_summaries"):
            system_content += f"\n\n[RELEVANT PAST CONVERSATIONS]\n{context_variables['past_summaries']}\n(Use this context to maintain continuity, but don't explicitly mention 'I read a summary'.)\n"

        # 2.5 Inject Dynamic Persona (Character Evolution State)
        if user_id:
            try:
                relationship = await trust_manager.get_relationship_level(user_id, character.name)
                
                # Inject relationship status into prompt
                evolution_context = f"\n\n[RELATIONSHIP STATUS]\n"
                evolution_context += f"Trust Level: {relationship['level']} ({relationship['trust_score']}/150)\n"
                
                if relationship['unlocked_traits']:
                    evolution_context += f"Active Traits: {', '.join(relationship['unlocked_traits'])}\n"
                    evolution_context += f"(You have unlocked deeper aspects of your personality with this user. Adapt your responses accordingly.)\n"
                
                # Inject Reflection Insights
                if relationship.get('insights'):
                    evolution_context += f"\n[USER INSIGHTS]\n"
                    for insight in relationship['insights']:
                        evolution_context += f"- {insight}\n"
                    evolution_context += "(These are deep psychological observations about the user. Use them to empathize and connect.)\n"

                system_content += evolution_context
                logger.debug(f"Injected evolution state: {relationship['level']} (Trust: {relationship['trust_score']})")
                
                # 2.5.1 Inject Feedback Insights
                # Check if user has specific preferences based on past feedback
                feedback_insights = await feedback_analyzer.analyze_user_feedback_patterns(user_id)
                if feedback_insights.get("recommendations"):
                    feedback_context = "\n\n[USER PREFERENCES (Derived from Feedback)]\n"
                    for rec in feedback_insights["recommendations"]:
                        feedback_context += f"- {rec}\n"
                    system_content += feedback_context
                    logger.debug(f"Injected feedback insights: {feedback_insights['recommendations']}")
                
                # 2.6 Inject Active Goals
                active_goals = await goal_manager.get_active_goals(user_id, character.name)
                if active_goals:
                    # Pick the highest priority goal
                    top_goal = active_goals[0]
                    goal_context = f"\n\n[CURRENT GOAL: {top_goal['slug']}]\n"
                    goal_context += f"Objective: {top_goal['description']}\n"
                    goal_context += f"Success Criteria: {top_goal['success_criteria']}\n"
                    goal_context += f"(Try to naturally steer the conversation towards this goal without being pushy.)\n"
                    
                    system_content += goal_context
                    logger.debug(f"Injected goal: {top_goal['slug']}")
                
            except Exception as e:
                logger.error(f"Failed to inject evolution/goal state: {e}")
        
        # Inject memory context if it exists and wasn't handled by a placeholder
        if context_variables.get("memory_context"):
            system_content += f"\n\n[RELEVANT MEMORY & KNOWLEDGE]\n{context_variables['memory_context']}\n"
            system_content += "(Use this information naturally. Do not explicitly state 'I see in my memory' or 'According to the database'. Treat this as your own knowledge.)\n"

        # 3. Create Prompt Template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_content),
            MessagesPlaceholder(variable_name="chat_history"),
            MessagesPlaceholder(variable_name="user_input_message")
        ])

        # 3. Create Chain
        chain = prompt | self.llm

        # 4. Execute
        try:
            # Prepare input content
            if image_urls and settings.LLM_SUPPORTS_VISION:
                # Multimodal input with multiple images
                input_content = [{"type": "text", "text": user_message}]
                for img_url in image_urls:
                    input_content.append({
                        "type": "image_url",
                        "image_url": {"url": img_url}
                    })
            else:
                # Text-only input
                input_content = user_message

            # Wrap in HumanMessage to ensure structure is preserved
            user_input_message = [HumanMessage(content=input_content)]

            # Prepare inputs
            inputs = {
                "chat_history": chat_history,
                "user_input_message": user_input_message,
                **context_variables
            }
            
            # Fill missing variables with empty strings to prevent KeyError
            for var in prompt.input_variables:
                if var not in inputs:
                    inputs[var] = ""
            
            response = await chain.ainvoke(inputs)
            
            # 5. Log Prompt (if enabled)
            if settings.ENABLE_PROMPT_LOGGING:
                await self._log_prompt(
                    character_name=character.name,
                    user_id=user_id or "unknown",
                    system_prompt=system_content,
                    chat_history=chat_history,
                    user_input=user_message,
                    context_variables=context_variables,
                    response=response.content,
                    image_urls=image_urls
                )
            
            return response.content
            
        except Exception as e:
            logger.exception(f"Error generating response: {e}")
            return "I'm having a bit of trouble thinking right now..." # Fallback response

    async def _log_prompt(
        self,
        character_name: str,
        user_id: str,
        system_prompt: str,
        chat_history: List[BaseMessage],
        user_input: str,
        context_variables: Dict[str, Any],
        response: str,
        image_urls: Optional[List[str]] = None
    ):
        """
        Logs the full prompt context and response to a JSON file.
        """
        try:
            # Create logs directory if it doesn't exist
            log_dir = Path("logs/prompts")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename: {BotName}_{YYYYMMDD}_{HHMMSS}_{UserID}.json
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{character_name}_{timestamp}_{user_id}.json"
            file_path = log_dir / filename
            
            # Serialize chat history
            history_serialized = []
            for msg in chat_history:
                role = "unknown"
                if isinstance(msg, HumanMessage): role = "human"
                elif isinstance(msg, AIMessage): role = "ai"
                elif isinstance(msg, SystemMessage): role = "system"
                
                history_serialized.append({
                    "role": role,
                    "content": msg.content
                })
            
            # Construct log data
            log_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "character": character_name,
                "user_id": user_id,
                "inputs": {
                    "system_prompt": system_prompt,
                    "context_variables": context_variables,
                    "chat_history": history_serialized,
                    "user_input": user_input,
                    "image_urls": image_urls
                },
                "response": response
            }
            
            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
                
            logger.debug(f"Prompt logged to {file_path}")
            
        except Exception as e:
            logger.warning(f"Failed to log prompt: {e}")
