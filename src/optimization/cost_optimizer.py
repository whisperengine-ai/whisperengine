"""
Cost Optimization Engine for WhisperEngine
Intelligent model selection and token usage optimization based on real usage patterns.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

from src.database.database_integration import DatabaseIntegrationManager


class ModelTier(Enum):
    """Model performance and cost tiers"""
    ECONOMY = "economy"      # GPT-4o-mini, free models
    BALANCED = "balanced"    # GPT-4o, Claude-3.5-sonnet  
    PREMIUM = "premium"      # GPT-4o, Claude-3-opus
    FLAGSHIP = "flagship"    # Grok-4, GPT-o1-preview


@dataclass
class ModelProfile:
    """Model characteristics and pricing"""
    name: str
    tier: ModelTier
    cost_per_1k_input: float
    cost_per_1k_output: float
    max_tokens: int
    strengths: List[str]
    use_cases: List[str]
    avg_response_time_ms: int = 1000


@dataclass
class RequestContext:
    """Context for intelligent model selection"""
    user_id: str
    conversation_length: int
    prompt_tokens: int
    expected_output_tokens: int
    conversation_type: str  # casual, technical, creative, etc.
    user_preference: Optional[str] = None
    max_cost_cents: Optional[int] = None
    priority: str = "normal"  # low, normal, high, urgent


@dataclass
class CostPrediction:
    """Predicted cost and performance for a request"""
    model_name: str
    estimated_cost: float
    estimated_tokens_in: int
    estimated_tokens_out: int
    estimated_response_time_ms: int
    confidence: float


class CostOptimizationEngine:
    """Intelligent cost optimization and model selection"""
    
    def __init__(self, db_manager: DatabaseIntegrationManager):
        self.db_manager = db_manager
        self.model_profiles = self._initialize_model_profiles()
        self.usage_history = {}
        # Note: Usage patterns will be loaded when first needed
    
    def _initialize_model_profiles(self) -> Dict[str, ModelProfile]:
        """Initialize model profiles based on current OpenRouter pricing"""
        return {
            "openai/gpt-4o-mini": ModelProfile(
                name="openai/gpt-4o-mini",
                tier=ModelTier.ECONOMY,
                cost_per_1k_input=0.000150,
                cost_per_1k_output=0.000600,
                max_tokens=128000,
                strengths=["fast", "cost-effective", "reliable"],
                use_cases=["casual chat", "simple questions", "quick responses"],
                avg_response_time_ms=300
            ),
            
            "openai/gpt-4o": ModelProfile(
                name="openai/gpt-4o",
                tier=ModelTier.BALANCED,
                cost_per_1k_input=0.005000,
                cost_per_1k_output=0.015000,
                max_tokens=128000,
                strengths=["high quality", "reasoning", "versatile"],
                use_cases=["complex questions", "analysis", "creative tasks"],
                avg_response_time_ms=1000
            ),
            
            "anthropic/claude-3.5-sonnet": ModelProfile(
                name="anthropic/claude-3.5-sonnet",
                tier=ModelTier.BALANCED,
                cost_per_1k_input=0.003000,
                cost_per_1k_output=0.015000,
                max_tokens=200000,
                strengths=["analysis", "writing", "long context"],
                use_cases=["detailed analysis", "document review", "writing"],
                avg_response_time_ms=1200
            ),
            
            "x-ai/grok-4-07-09": ModelProfile(
                name="x-ai/grok-4-07-09",
                tier=ModelTier.FLAGSHIP,
                cost_per_1k_input=0.030000,
                cost_per_1k_output=0.120000,
                max_tokens=128000,
                strengths=["cutting-edge", "reasoning", "creative"],
                use_cases=["complex reasoning", "research", "special requests"],
                avg_response_time_ms=2000
            ),
            
            "google/gemini-pro": ModelProfile(
                name="google/gemini-pro",
                tier=ModelTier.ECONOMY,
                cost_per_1k_input=0.001250,
                cost_per_1k_output=0.005000,
                max_tokens=128000,
                strengths=["multimodal", "fast", "google integration"],
                use_cases=["general chat", "quick tasks", "multimodal"],
                avg_response_time_ms=500
            )
        }
    
    async def _load_usage_patterns(self):
        """Load historical usage patterns for optimization"""
        try:
            # Load user preferences and usage patterns
            result = await self.db_manager.get_database_manager().query("""
                SELECT 
                    user_id,
                    model_name,
                    AVG(cost_usd) as avg_cost,
                    AVG(input_tokens) as avg_input,
                    AVG(output_tokens) as avg_output,
                    COUNT(*) as usage_count
                FROM token_usage_log 
                WHERE timestamp >= :since
                GROUP BY user_id, model_name
            """, {"since": (datetime.now() - timedelta(days=30)).isoformat()})
            
            # Build usage patterns
            for row in result.rows:
                user_id = row['user_id']
                if user_id not in self.usage_history:
                    self.usage_history[user_id] = {}
                
                self.usage_history[user_id][row['model_name']] = {
                    'avg_cost': row['avg_cost'],
                    'avg_input': row['avg_input'],
                    'avg_output': row['avg_output'],
                    'usage_count': row['usage_count']
                }
        
        except Exception as e:
            logging.warning(f"Could not load usage patterns: {e}")
    
    async def select_optimal_model(self, context: RequestContext) -> str:
        """Select the optimal model for a given context"""
        
        # Get cost predictions for all suitable models
        predictions = await self._get_cost_predictions(context)
        
        # Apply selection logic based on context
        selected_model = self._apply_selection_logic(context, predictions)
        
        return selected_model
    
    async def _get_cost_predictions(self, context: RequestContext) -> List[CostPrediction]:
        """Get cost predictions for all suitable models"""
        predictions = []
        
        for model_name, profile in self.model_profiles.items():
            # Skip models that can't handle the token count
            if context.prompt_tokens > profile.max_tokens * 0.7:  # Leave room for response
                continue
            
            # Calculate estimated cost
            input_cost = (context.prompt_tokens / 1000) * profile.cost_per_1k_input
            output_cost = (context.expected_output_tokens / 1000) * profile.cost_per_1k_output
            total_cost = input_cost + output_cost
            
            # Skip if over budget
            if context.max_cost_cents and total_cost * 100 > context.max_cost_cents:
                continue
            
            # Calculate confidence based on historical performance
            confidence = self._calculate_confidence(context.user_id, model_name, context)
            
            predictions.append(CostPrediction(
                model_name=model_name,
                estimated_cost=total_cost,
                estimated_tokens_in=context.prompt_tokens,
                estimated_tokens_out=context.expected_output_tokens,
                estimated_response_time_ms=profile.avg_response_time_ms,
                confidence=confidence
            ))
        
        return sorted(predictions, key=lambda p: p.estimated_cost)
    
    def _calculate_confidence(self, user_id: str, model_name: str, context: RequestContext) -> float:
        """Calculate confidence score for model selection"""
        base_confidence = 0.7
        
        # Boost confidence for models with good user history
        if user_id in self.usage_history and model_name in self.usage_history[user_id]:
            usage_data = self.usage_history[user_id][model_name]
            if usage_data['usage_count'] > 5:
                base_confidence += 0.2
        
        # Adjust based on conversation type and model strengths
        model_profile = self.model_profiles[model_name]
        
        if context.conversation_type in ['technical', 'analysis'] and 'reasoning' in model_profile.strengths:
            base_confidence += 0.1
        
        if context.conversation_type == 'casual' and model_profile.tier == ModelTier.ECONOMY:
            base_confidence += 0.1
        
        if context.priority == 'urgent' and model_profile.avg_response_time_ms < 600:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _apply_selection_logic(self, context: RequestContext, predictions: List[CostPrediction]) -> str:
        """Apply selection logic to choose the best model"""
        
        if not predictions:
            # Fallback to most economical model
            return "openai/gpt-4o-mini"
        
        # Priority-based selection
        if context.priority == "urgent":
            # Choose fastest model within budget
            fast_models = [p for p in predictions if p.estimated_response_time_ms < 800]
            if fast_models:
                return max(fast_models, key=lambda p: p.confidence).model_name
        
        elif context.priority == "low":
            # Choose most economical model
            return predictions[0].model_name  # Already sorted by cost
        
        # Default: balance cost, performance, and confidence
        scored_predictions = []
        for pred in predictions:
            # Normalize scores (0-1)
            cost_score = 1 - (pred.estimated_cost / max(p.estimated_cost for p in predictions))
            confidence_score = pred.confidence
            speed_score = 1 - (pred.estimated_response_time_ms / max(p.estimated_response_time_ms for p in predictions))
            
            # Weighted composite score
            composite_score = (
                cost_score * 0.4 +
                confidence_score * 0.4 +
                speed_score * 0.2
            )
            
            scored_predictions.append((pred.model_name, composite_score))
        
        # Return model with highest composite score
        return max(scored_predictions, key=lambda x: x[1])[0]
    
    async def estimate_monthly_cost(self, user_id: str) -> Dict[str, Any]:
        """Estimate monthly cost for a user based on usage patterns"""
        try:
            # Get last 30 days of usage
            result = await self.db_manager.get_database_manager().query("""
                SELECT 
                    COUNT(*) as request_count,
                    AVG(cost_usd) as avg_cost_per_request,
                    SUM(cost_usd) as total_cost,
                    AVG(total_tokens) as avg_tokens_per_request
                FROM token_usage_log 
                WHERE user_id = :user_id 
                AND timestamp >= :since
            """, {
                "user_id": user_id,
                "since": (datetime.now() - timedelta(days=30)).isoformat()
            })
            
            if not result.rows or result.rows[0]['request_count'] == 0:
                return {
                    "monthly_estimate": 0.0,
                    "daily_estimate": 0.0,
                    "requests_per_day": 0,
                    "avg_cost_per_request": 0.0,
                    "confidence": "low"
                }
            
            data = result.rows[0]
            daily_requests = data['request_count'] / 30
            monthly_estimate = data['total_cost'] * (30 / 30)  # Current month projection
            
            return {
                "monthly_estimate": round(monthly_estimate, 4),
                "daily_estimate": round(monthly_estimate / 30, 4),
                "requests_per_day": round(daily_requests, 1),
                "avg_cost_per_request": round(data['avg_cost_per_request'], 6),
                "avg_tokens_per_request": round(data['avg_tokens_per_request'], 1),
                "confidence": "high" if data['request_count'] > 50 else "medium"
            }
        
        except Exception as e:
            logging.error(f"Failed to estimate monthly cost: {e}")
            return {"error": str(e)}
    
    async def get_cost_optimization_suggestions(self, user_id: str) -> List[str]:
        """Get personalized cost optimization suggestions"""
        suggestions = []
        
        try:
            # Analyze user's model usage
            result = await self.db_manager.get_database_manager().query("""
                SELECT 
                    model_name,
                    COUNT(*) as usage_count,
                    SUM(cost_usd) as total_cost,
                    AVG(cost_usd) as avg_cost,
                    AVG(input_tokens) as avg_input_tokens
                FROM token_usage_log 
                WHERE user_id = :user_id 
                AND timestamp >= :since
                GROUP BY model_name
                ORDER BY total_cost DESC
            """, {
                "user_id": user_id,
                "since": (datetime.now() - timedelta(days=30)).isoformat()
            })
            
            total_cost = sum(row['total_cost'] for row in result.rows)
            
            for row in result.rows:
                model_name = row['model_name']
                cost_percentage = (row['total_cost'] / total_cost) * 100 if total_cost > 0 else 0
                
                # High cost model suggestions
                if 'grok' in model_name.lower() and cost_percentage > 20:
                    suggestions.append(
                        f"Consider using GPT-4o instead of Grok for routine tasks. "
                        f"Grok accounts for {cost_percentage:.1f}% of your costs."
                    )
                
                # High usage suggestions
                if row['usage_count'] > 100 and row['avg_cost'] > 0.01:
                    suggestions.append(
                        f"You use {model_name} frequently ({row['usage_count']} times). "
                        f"Consider GPT-4o-mini for simpler queries to save 80% on costs."
                    )
                
                # Large prompt suggestions
                if row['avg_input_tokens'] > 5000:
                    suggestions.append(
                        f"Your prompts to {model_name} average {row['avg_input_tokens']:.0f} tokens. "
                        f"Consider summarizing context to reduce input costs."
                    )
            
            # General suggestions if no specific issues found
            if not suggestions:
                suggestions.append("Your usage patterns look efficient! Consider setting monthly budget alerts.")
            
            return suggestions
        
        except Exception as e:
            logging.error(f"Failed to generate suggestions: {e}")
            return ["Could not analyze usage patterns for suggestions."]
    
    async def set_user_budget(self, user_id: str, monthly_budget_cents: int) -> bool:
        """Set monthly budget limit for a user"""
        try:
            await self.db_manager.get_database_manager().query("""
                INSERT OR REPLACE INTO user_budgets (user_id, monthly_budget_cents, created_at)
                VALUES (:user_id, :budget, :timestamp)
            """, {
                "user_id": user_id,
                "budget": monthly_budget_cents,
                "timestamp": datetime.now().isoformat()
            })
            return True
        except Exception as e:
            logging.error(f"Failed to set user budget: {e}")
            return False
    
    async def check_budget_status(self, user_id: str) -> Dict[str, Any]:
        """Check current budget status for a user"""
        try:
            # Get budget
            budget_result = await self.db_manager.get_database_manager().query("""
                SELECT monthly_budget_cents FROM user_budgets WHERE user_id = :user_id
            """, {"user_id": user_id})
            
            if not budget_result.rows:
                return {"status": "no_budget_set"}
            
            monthly_budget = budget_result.rows[0]['monthly_budget_cents'] / 100
            
            # Get current month spending
            first_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            spending_result = await self.db_manager.get_database_manager().query("""
                SELECT SUM(cost_usd) as current_spending
                FROM token_usage_log 
                WHERE user_id = :user_id 
                AND timestamp >= :since
            """, {
                "user_id": user_id,
                "since": first_of_month.isoformat()
            })
            
            current_spending = spending_result.rows[0]['current_spending'] or 0.0
            percentage_used = (current_spending / monthly_budget) * 100 if monthly_budget > 0 else 0
            
            status = "on_track"
            if percentage_used > 90:
                status = "over_budget"
            elif percentage_used > 75:
                status = "warning"
            
            return {
                "status": status,
                "monthly_budget": monthly_budget,
                "current_spending": current_spending,
                "remaining_budget": monthly_budget - current_spending,
                "percentage_used": percentage_used,
                "days_remaining": (datetime.now().replace(month=datetime.now().month+1, day=1) - datetime.now()).days
            }
        
        except Exception as e:
            logging.error(f"Failed to check budget status: {e}")
            return {"error": str(e)}


# Factory function
def create_cost_optimizer(db_manager: DatabaseIntegrationManager) -> CostOptimizationEngine:
    """Factory function to create cost optimization engine"""
    return CostOptimizationEngine(db_manager)


# Example usage and testing
async def main():
    """Example usage of cost optimization engine"""
    from src.config.adaptive_config import AdaptiveConfigManager
    
    # Create components
    config_manager = AdaptiveConfigManager()
    db_manager = DatabaseIntegrationManager(config_manager)
    await db_manager.initialize()
    
    cost_optimizer = create_cost_optimizer(db_manager)
    
    # Example request context
    context = RequestContext(
        user_id="test_user",
        conversation_length=5,
        prompt_tokens=2500,
        expected_output_tokens=200,
        conversation_type="technical",
        priority="normal"
    )
    
    # Select optimal model
    selected_model = await cost_optimizer.select_optimal_model(context)
    print(f"Selected model: {selected_model}")
    
    # Get cost estimate
    monthly_estimate = await cost_optimizer.estimate_monthly_cost("test_user")
    print(f"Monthly cost estimate: {monthly_estimate}")
    
    # Get optimization suggestions
    suggestions = await cost_optimizer.get_cost_optimization_suggestions("test_user")
    print(f"Optimization suggestions: {suggestions}")
    
    await db_manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())