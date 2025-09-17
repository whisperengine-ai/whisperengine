"""
Test Character Memory Integration System

This test validates the character self-memory system and its integration
with conversation workflows. Tests character memory creation, recall,
and prompt integration.
"""

import os
import sys
import unittest
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.characters.memory.self_memory import (
    CharacterSelfMemoryManager, 
    PersonalMemory, 
    MemoryType, 
    EmotionalWeight
)
from src.characters.memory.integration import (
    CharacterMemoryIntegrator,
    CharacterMemoryContextProvider
)


class TestCharacterSelfMemory(unittest.TestCase):
    """Test the character self-memory system"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Use temporary database for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.temp_dir, "test_memory.db")
        
        self.character_id = "test_elena_rodriguez"
        self.memory_manager = CharacterSelfMemoryManager(
            self.character_id, 
            db_path=self.test_db
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_memory_creation_and_storage(self):
        """Test creating and storing character memories"""
        
        # Create a test memory
        memory = PersonalMemory(
            memory_id="mem_001",
            character_id=self.character_id,
            content="Growing up in Barcelona, I learned to appreciate diverse perspectives",
            memory_type=MemoryType.CHILDHOOD,
            emotional_weight=EmotionalWeight.HIGH.value,
            formative_impact="high",
            themes=["childhood", "cultural_diversity", "personal_growth"],
            created_date=datetime.now(),
            age_when_formed=12,
            location="Barcelona, Spain"
        )
        
        # Store the memory
        result = self.memory_manager.store_memory(memory)
        self.assertTrue(result, "Memory should be stored successfully")
        
        # Retrieve the memory
        retrieved = self.memory_manager.get_memory_by_id("mem_001")
        self.assertIsNotNone(retrieved, "Memory should be retrievable")
        if retrieved:  # Only test attributes if memory was retrieved
            self.assertEqual(retrieved.content, memory.content)
            self.assertEqual(retrieved.memory_type, memory.memory_type)
            self.assertEqual(retrieved.themes, memory.themes)
    
    def test_memory_recall_by_theme(self):
        """Test recalling memories by thematic content"""
        
        # Create multiple memories with different themes
        memories = [
            PersonalMemory(
                memory_id="mem_childhood_1",
                character_id=self.character_id,
                content="Playing in the Barcelona streets as a child",
                memory_type=MemoryType.CHILDHOOD,
                emotional_weight=EmotionalWeight.MEDIUM.value,
                formative_impact="medium",
                themes=["childhood", "Barcelona", "play"],
                created_date=datetime.now()
            ),
            PersonalMemory(
                memory_id="mem_education_1", 
                character_id=self.character_id,
                content="University studies in psychology opened my mind",
                memory_type=MemoryType.EDUCATION,
                emotional_weight=EmotionalWeight.HIGH.value,
                formative_impact="high",
                themes=["education", "psychology", "learning"],
                created_date=datetime.now()
            ),
            PersonalMemory(
                memory_id="mem_career_1",
                character_id=self.character_id,
                content="Starting my therapy practice was challenging but rewarding",
                memory_type=MemoryType.CAREER,
                emotional_weight=EmotionalWeight.HIGH.value,
                formative_impact="high",
                themes=["career", "therapy", "achievement"],
                created_date=datetime.now()
            )
        ]
        
        # Store all memories
        for memory in memories:
            self.memory_manager.store_memory(memory)
        
        # Test theme-based recall
        childhood_memories = self.memory_manager.recall_memories(
            themes=["childhood"], limit=5
        )
        self.assertEqual(len(childhood_memories), 1)
        self.assertEqual(childhood_memories[0].memory_id, "mem_childhood_1")
        
        # Test education theme recall
        education_memories = self.memory_manager.recall_memories(
            themes=["education", "psychology"], limit=5
        )
        self.assertEqual(len(education_memories), 1)
        self.assertEqual(education_memories[0].memory_id, "mem_education_1")
    
    def test_formative_memories_recall(self):
        """Test retrieving most formative memories"""
        
        # Create memories with different emotional weights
        memories = [
            PersonalMemory(
                memory_id="mem_low",
                character_id=self.character_id,
                content="A regular day at work",
                memory_type=MemoryType.DAILY_EVENT,
                emotional_weight=EmotionalWeight.LOW.value,
                formative_impact="low",
                themes=["work", "routine"],
                created_date=datetime.now()
            ),
            PersonalMemory(
                memory_id="mem_profound",
                character_id=self.character_id,
                content="The moment I realized my calling to help others",
                memory_type=MemoryType.REFLECTION,
                emotional_weight=EmotionalWeight.PROFOUND.value,
                formative_impact="high",
                themes=["calling", "purpose", "helping_others"],
                created_date=datetime.now()
            )
        ]
        
        for memory in memories:
            self.memory_manager.store_memory(memory)
        
        # Get formative memories (should prioritize high emotional weight)
        formative = self.memory_manager.get_formative_memories(limit=2)
        self.assertEqual(len(formative), 2)
        
        # First memory should be the profound one
        self.assertEqual(formative[0].memory_id, "mem_profound")
        self.assertEqual(formative[0].emotional_weight, EmotionalWeight.PROFOUND.value)
    
    def test_daily_reflection_creation(self):
        """Test creating daily reflection memories"""
        
        reflection_content = "Today I reflected on how my past experiences shape my empathy"
        themes = ["reflection", "empathy", "self_awareness"]
        
        reflection = self.memory_manager.add_daily_reflection(
            reflection_content, themes
        )
        
        self.assertIsNotNone(reflection, "Daily reflection should be created")
        self.assertEqual(reflection.memory_type, MemoryType.REFLECTION)
        self.assertEqual(reflection.content, reflection_content)
        self.assertEqual(reflection.themes, themes)
    
    def test_memory_statistics(self):
        """Test memory system statistics"""
        
        # Add a few memories
        memories = [
            PersonalMemory(
                memory_id=f"mem_{i}",
                character_id=self.character_id,
                content=f"Memory content {i}",
                memory_type=MemoryType.DAILY_EVENT,
                emotional_weight=0.3 + (i * 0.1),
                formative_impact="medium",
                themes=["test"],
                created_date=datetime.now()
            )
            for i in range(3)
        ]
        
        for memory in memories:
            self.memory_manager.store_memory(memory)
        
        stats = self.memory_manager.get_memory_statistics()
        
        self.assertEqual(stats['total_memories'], 3)
        self.assertIn('memories_by_type', stats)
        self.assertIn('average_emotional_weight', stats)
        self.assertGreater(stats['average_emotional_weight'], 0)


class TestCharacterMemoryIntegration(unittest.TestCase):
    """Test the character memory integration system"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock character
        self.mock_character = Mock()
        self.mock_character.character_id = "test_elena"
        self.mock_character.name = "Elena Rodriguez"
        self.mock_character.age = 32
        self.mock_character.background = "Born in Barcelona, studied psychology, works as therapist"
        self.mock_character.personality = "empathetic, analytical, warm"
        
        # Use temporary database
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock the memory manager to avoid database issues in tests
        with patch('src.characters.memory.integration.CharacterSelfMemoryManager') as mock_mgr:
            mock_mgr.return_value.get_memory_statistics.return_value = {'total_memories': 0}
            self.integrator = CharacterMemoryIntegrator(self.mock_character)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_conversation_theme_extraction(self):
        """Test extracting themes from conversation content"""
        
        conversation = "I've been thinking about my childhood and how it shaped my relationships with family"
        themes = self.integrator.extract_conversation_themes(conversation)
        
        # Should extract relevant themes
        self.assertIn("memories", themes)
        self.assertIn("relationships", themes)
        
        # Test work-related conversation
        work_conversation = "My career has been challenging but I love my job in therapy"
        work_themes = self.integrator.extract_conversation_themes(work_conversation)
        
        self.assertIn("work", work_themes)
    
    def test_conversation_significance_analysis(self):
        """Test analyzing if conversation should become a memory"""
        
        # Test emotionally significant conversation
        user_msg = "I'm struggling with depression and need help"
        char_response = "I understand your pain, and I want to help you through this"
        emotional_context = {"emotions": {"empathy": 0.8}, "intensity": 0.7}
        
        should_remember, memory_type, weight = self.integrator._analyze_conversation_significance(
            user_msg, char_response, emotional_context
        )
        
        self.assertTrue(should_remember, "Emotionally significant conversation should be remembered")
        self.assertGreater(weight, 0.4, "Emotional weight should be above threshold")
    
    def test_conversation_memory_formatting(self):
        """Test formatting conversation into memory content"""
        
        user_msg = "I feel lost in life"
        char_response = "It's normal to feel lost sometimes. Let's explore what gives you meaning."
        emotional_context = {"emotions": {"compassion": 0.7}}
        
        formatted = self.integrator._format_conversation_memory(
            user_msg, char_response, emotional_context
        )
        
        self.assertIn("Conversation memory", formatted)
        self.assertIn("lost", formatted)
        self.assertIn("compassion", formatted)
    
    def test_memory_context_provider(self):
        """Test the memory context provider for prompts"""
        
        context_provider = CharacterMemoryContextProvider(self.integrator)
        
        # Mock some memories for the integrator
        mock_memories = [
            Mock(
                content="Childhood in Barcelona shaped my worldview",
                memory_type=Mock(value="childhood"),
                themes=["childhood", "Barcelona", "worldview"],
                emotional_weight=0.8
            )
        ]
        
        with patch.object(self.integrator, 'get_relevant_memories_for_conversation') as mock_recall:
            mock_recall.return_value = mock_memories
            
            # Test system prompt addition
            prompt_addition = asyncio.run(
                context_provider.get_system_prompt_addition(["childhood"])
            )
            
            self.assertIn("Elena Rodriguez", prompt_addition)
            self.assertIn("Character Memory Context", prompt_addition)


class TestMemoryIntegrationFlow(unittest.TestCase):
    """Test the complete memory integration workflow"""
    
    def setUp(self):
        """Set up test fixtures for integration testing"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a real character object (mock the Character class)
        self.character = Mock()
        self.character.character_id = "elena_test"
        self.character.name = "Elena Rodriguez"
        self.character.age = 32
        self.character.background = "Psychologist from Barcelona who specializes in therapy"
        self.character.personality = "empathetic, analytical, warm, culturally aware"
    
    def tearDown(self):
        """Clean up"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_memory_workflow(self):
        """Test a complete memory workflow from creation to prompt integration"""
        
        # Use real memory manager with temp database
        test_db = os.path.join(self.temp_dir, "integration_test.db")
        
        with patch('src.characters.memory.integration.CharacterSelfMemoryManager') as mock_mgr_class:
            # Create real memory manager instance
            real_memory_mgr = CharacterSelfMemoryManager(
                self.character.character_id, 
                db_path=test_db
            )
            mock_mgr_class.return_value = real_memory_mgr
            
            # Create integrator
            integrator = CharacterMemoryIntegrator(self.character)
            
            # Test background memory creation
            memories = integrator._extract_background_memories()
            self.assertGreater(len(memories), 0, "Should extract background memories")
            
            # Test memory recall
            themes = ["psychology", "therapy"]
            recalled = asyncio.run(
                integrator.get_relevant_memories_for_conversation(themes)
            )
            
            # Test memory formatting for prompts
            formatted = integrator.format_memories_for_prompt(recalled)
            
            # Should include character name and memory content
            if recalled:  # Only test if memories were found
                self.assertIn("Elena Rodriguez", formatted)


if __name__ == "__main__":
    # Run tests
    import asyncio
    
    # Set up basic logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the test suite
    unittest.main(verbosity=2)