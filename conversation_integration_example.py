"""
Integration Example: Persistent Conversation Manager with WhisperEngine

This shows how to integrate the new persistent conversation tracking
with WhisperEngine's existing sophisticated conversation engines.
"""

# Example integration in src/handlers/events.py

async def _generate_and_send_response(self, message, user_id, channel):
    """Enhanced message handling with persistent conversation tracking"""
    
    # ... existing WhisperEngine code ...
    
    # 🆕 NEW: Get persistent conversation manager
    from src.conversation.persistent_conversation_manager import create_persistent_conversation_manager
    conversation_manager = await create_persistent_conversation_manager(self.memory_manager)
    
    # 🆕 NEW: Process user message for answered questions
    conversation_analysis = await conversation_manager.process_user_response(
        user_id=user_id,
        user_message=message.content,
        current_topic=self._extract_current_topic(message.content)  # You'd implement this
    )
    
    # 🆕 NEW: Check for conversation issues
    conversation_health = await conversation_manager.detect_conversation_issues(user_id)
    
    # Generate bot response using existing WhisperEngine systems
    bot_response = await self.llm_client.generate_completion_with_retry(
        messages=prepared_messages,
        temperature=0.7,
        max_tokens=2000
    )
    
    # 🆕 NEW: Track questions asked by bot
    questions_in_response = self._extract_questions_from_response(bot_response)
    for question in questions_in_response:
        await conversation_manager.track_bot_question(
            user_id=user_id,
            question_text=question["text"],
            question_type=question["type"],  # You'd classify this
            priority=question["priority"],   # You'd determine this
            current_topic=current_topic,
            user_context=message.content[:200]  # Context that prompted question
        )
    
    # 🆕 NEW: Add gentle reminders if appropriate
    if conversation_health["health_score"] > 0.7:  # Good conversation health
        reminder_suggestions = await conversation_manager.get_reminder_suggestions(user_id)
        if reminder_suggestions and random.random() < 0.3:  # 30% chance
            # Naturally incorporate a reminder
            bot_response += f"\\n\\n{random.choice(reminder_suggestions)}"
    
    # ... send response using existing WhisperEngine code ...
    
    return bot_response


def _extract_questions_from_response(self, response: str) -> List[Dict]:
    """Extract questions from bot response for tracking"""
    questions = []
    
    # Simple question detection (could be enhanced)
    sentences = response.split('.')
    for sentence in sentences:
        if '?' in sentence:
            question_text = sentence.strip()
            
            # Classify question type
            question_type = self._classify_question_type(question_text)
            priority = self._determine_question_priority(question_text)
            
            questions.append({
                "text": question_text,
                "type": question_type,
                "priority": priority
            })
    
    return questions


def _classify_question_type(self, question: str) -> QuestionType:
    """Classify the type of question for appropriate handling"""
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['what do you think', 'your opinion', 'how do you feel']):
        return QuestionType.OPINION
    elif any(word in question_lower for word in ['tell me more', 'can you elaborate', 'what else']):
        return QuestionType.FOLLOWUP
    elif any(word in question_lower for word in ['prefer', 'choose', 'would you rather']):
        return QuestionType.CHOICE
    elif any(word in question_lower for word in ['what', 'where', 'when', 'who']):
        return QuestionType.FACTUAL
    elif any(word in question_lower for word in ['how did', 'what was it like', 'how do you']):
        return QuestionType.PERSONAL
    else:
        return QuestionType.CLARIFICATION


def _determine_question_priority(self, question: str) -> QuestionPriority:
    """Determine how important it is to get an answer"""
    question_lower = question.lower()
    
    # High priority: Essential for character development or important clarification
    if any(word in question_lower for word in ['important', 'curious', 'wondering', 'love to know']):
        return QuestionPriority.HIGH
    
    # Low priority: Casual, optional questions  
    elif any(word in question_lower for word in ['by the way', 'incidentally', 'just wondering']):
        return QuestionPriority.LOW
    
    # Medium priority: Standard follow-up questions
    else:
        return QuestionPriority.MEDIUM


# Example integration with existing ProactiveEngagementEngine

class EnhancedProactiveEngagement:
    """Enhanced version that works with persistent question tracking"""
    
    def __init__(self, conversation_manager: PersistentConversationManager):
        self.conversation_manager = conversation_manager
        # ... existing initialization ...
    
    async def suggest_engagement_prompts(self, user_id: str) -> List[str]:
        """Enhanced engagement that considers unanswered questions"""
        
        # Get conversation health
        health = await self.conversation_manager.detect_conversation_issues(user_id)
        
        if "too_many_pending_questions" in health["issues"]:
            # Don't suggest new topics, focus on current conversation
            return ["Let's continue with what we were discussing..."]
        
        elif "low_question_engagement" in health["issues"]:
            # User doesn't like questions, suggest statement-based engagement
            return self._generate_statement_based_prompts(user_id)
        
        elif "topic_avoidance" in health["issues"]:
            # User jumping topics, follow their lead
            return ["I'm interested in whatever you'd like to talk about"]
        
        else:
            # Normal proactive engagement
            return await self._generate_normal_prompts(user_id)


# Example conversation flow:

# Bot: "Elena here! I'm fascinated by your interest in marine conservation. 
#       What specific ocean issues concern you most?"
# → Track: QuestionType.OPINION, QuestionPriority.HIGH

# User: "Oh, I just saw this cool documentary about space!"
# → Process: Question not answered, topic changed abruptly

# Bot: "Space documentaries can be amazing! The vastness reminds me of ocean depths.
#       Speaking of conservation - I'm still curious what ocean issues matter to you?"
# → Natural callback to unanswered question

# User: "Actually, plastic pollution really bothers me"
# → Process: Question answered! Mark resolved, high quality answer

# Bot: "That's such an important issue! I've seen the impact firsthand in my research.
#       What first made you aware of plastic pollution in our oceans?"
# → Track: QuestionType.PERSONAL, QuestionPriority.MEDIUM

# This creates much more natural, persistent conversation flow!