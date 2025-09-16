#!/usr/bin/env python3
"""
Test script for ChatGPT History Import functionality

This script tests the import_chatgpt_history.py script with sample data.
"""

import unittest
import json
import tempfile
import os
from datetime import datetime
from unittest.mock import patch, MagicMock

# Import the modules we're testing
from import_chatgpt_history import ChatGPTImporter
from memory_manager import UserMemoryManager


class TestChatGPTImporter(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.chromadb_path = os.path.join(self.temp_dir, "test_chromadb")

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_sample_chatgpt_export(self) -> str:
        """Create a sample ChatGPT export JSON file"""
        sample_data = [
            {
                "id": "conv-123",
                "title": "Test Conversation 1",
                "create_time": 1609459200,  # Jan 1, 2021
                "update_time": 1609459800,
                "mapping": {
                    "node1": {
                        "message": {
                            "id": "msg1",
                            "author": {"role": "user", "name": None},
                            "content": {
                                "parts": ["Hello, I'm John and I like programming in Python."]
                            },
                            "create_time": 1609459200,
                        }
                    },
                    "node2": {
                        "message": {
                            "id": "msg2",
                            "author": {"role": "assistant", "name": None},
                            "content": {
                                "parts": [
                                    "Hello John! It's great to meet someone who enjoys Python programming. What kind of projects do you like to work on?"
                                ]
                            },
                            "create_time": 1609459300,
                        }
                    },
                    "node3": {
                        "message": {
                            "id": "msg3",
                            "author": {"role": "user", "name": None},
                            "content": {
                                "parts": [
                                    "I work as a software engineer and I'm 25 years old. I enjoy building web applications."
                                ]
                            },
                            "create_time": 1609459400,
                        }
                    },
                    "node4": {
                        "message": {
                            "id": "msg4",
                            "author": {"role": "assistant", "name": None},
                            "content": {
                                "parts": [
                                    "That sounds exciting! Web development is a great field. What technologies do you prefer for your web applications?"
                                ]
                            },
                            "create_time": 1609459500,
                        }
                    },
                },
            },
            {
                "id": "conv-456",
                "title": "Test Conversation 2",
                "create_time": 1609545600,  # Jan 2, 2021
                "update_time": 1609546200,
                "mapping": {
                    "node1": {
                        "message": {
                            "id": "msg5",
                            "author": {"role": "user", "name": None},
                            "content": {
                                "parts": [
                                    "I live in San Francisco and I have a cat named Whiskers."
                                ]
                            },
                            "create_time": 1609545600,
                        }
                    },
                    "node2": {
                        "message": {
                            "id": "msg6",
                            "author": {"role": "assistant", "name": None},
                            "content": {
                                "parts": [
                                    "That's wonderful! San Francisco is a beautiful city. Tell me more about Whiskers - what kind of cat is he or she?"
                                ]
                            },
                            "create_time": 1609545700,
                        }
                    },
                },
            },
        ]

        # Write to temporary file
        temp_file = os.path.join(self.temp_dir, "sample_export.json")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(sample_data, f, indent=2)

        return temp_file

    def test_load_chatgpt_export(self):
        """Test loading ChatGPT export file"""
        # Create sample file
        export_file = self.create_sample_chatgpt_export()

        # Mock the memory manager to avoid ChromaDB initialization
        with patch("import_chatgpt_history.UserMemoryManager"):
            importer = ChatGPTImporter(chromadb_path=self.chromadb_path)

            # Test loading
            data = importer.load_chatgpt_export(export_file)

            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]["id"], "conv-123")
            self.assertEqual(data[1]["id"], "conv-456")

    def test_parse_conversations(self):
        """Test parsing conversations from export data"""
        # Create sample file and load data
        export_file = self.create_sample_chatgpt_export()

        with patch("import_chatgpt_history.UserMemoryManager"):
            importer = ChatGPTImporter(chromadb_path=self.chromadb_path)

            export_data = importer.load_chatgpt_export(export_file)
            conversations = importer.parse_conversations(export_data)

            # Verify parsing
            self.assertEqual(len(conversations), 2)

            # Check first conversation
            conv1 = conversations[0]
            self.assertEqual(conv1["id"], "conv-123")
            self.assertEqual(conv1["title"], "Test Conversation 1")
            self.assertEqual(len(conv1["turns"]), 2)

            # Check conversation turns
            turn1 = conv1["turns"][0]
            self.assertIn("John", turn1[0])  # User message
            self.assertIn("Python programming", turn1[1])  # Assistant response

            turn2 = conv1["turns"][1]
            self.assertIn("software engineer", turn2[0])
            self.assertIn("25 years old", turn2[0])

    def test_extract_messages_from_mapping(self):
        """Test extracting messages from ChatGPT mapping structure"""
        with patch("import_chatgpt_history.UserMemoryManager"):
            importer = ChatGPTImporter(chromadb_path=self.chromadb_path)

            # Sample mapping with correct ChatGPT format
            mapping = {
                "node1": {
                    "message": {
                        "id": "msg1",
                        "author": {"role": "user", "name": None},
                        "content": {"parts": ["Hello there"]},
                        "create_time": 1609459200,
                    }
                },
                "node2": {
                    "message": {
                        "id": "msg2",
                        "author": {"role": "assistant", "name": None},
                        "content": {"parts": ["Hi! How can I help you?"]},
                        "create_time": 1609459300,
                    }
                },
            }

            messages = importer._extract_messages_from_mapping(mapping)

            self.assertEqual(len(messages), 2)
            self.assertEqual(messages[0]["role"], "user")
            self.assertEqual(messages[0]["content"], "Hello there")
            self.assertEqual(messages[1]["role"], "assistant")
            self.assertEqual(messages[1]["content"], "Hi! How can I help you?")

    def test_convert_to_conversation_turns(self):
        """Test converting messages to conversation turns"""
        with patch("import_chatgpt_history.UserMemoryManager"):
            importer = ChatGPTImporter(chromadb_path=self.chromadb_path)

            messages = [
                {"role": "user", "content": "What's 2+2?"},
                {"role": "assistant", "content": "2+2 equals 4."},
                {"role": "user", "content": "What about 3+3?"},
                {"role": "assistant", "content": "3+3 equals 6."},
            ]

            turns = importer._convert_to_conversation_turns(messages)

            self.assertEqual(len(turns), 2)
            self.assertEqual(turns[0][0], "What's 2+2?")
            self.assertEqual(turns[0][1], "2+2 equals 4.")
            self.assertEqual(turns[1][0], "What about 3+3?")
            self.assertEqual(turns[1][1], "3+3 equals 6.")

    def test_is_system_message(self):
        """Test system message detection"""
        with patch("import_chatgpt_history.UserMemoryManager"):
            importer = ChatGPTImporter(chromadb_path=self.chromadb_path)

            # Test system messages
            self.assertTrue(importer._is_system_message("I'm an AI assistant created by Anthropic"))
            self.assertTrue(
                importer._is_system_message("I don't have the ability to browse the internet")
            )
            self.assertTrue(importer._is_system_message("As an AI, I cannot access real-time data"))

            # Test regular messages
            self.assertFalse(importer._is_system_message("Hello, how are you today?"))
            self.assertFalse(importer._is_system_message("I like programming in Python"))
            self.assertFalse(importer._is_system_message("What's the weather like?"))

    def test_validate_user_id(self):
        """Test user ID validation"""
        with patch("import_chatgpt_history.UserMemoryManager"):
            importer = ChatGPTImporter(chromadb_path=self.chromadb_path)

            # Valid user IDs
            self.assertEqual(importer.validate_user_id("123456789012345678"), "123456789012345678")
            self.assertEqual(importer.validate_user_id("  987654321  "), "987654321")

            # Invalid user IDs
            with self.assertRaises(Exception):
                importer.validate_user_id("invalid_id")
            with self.assertRaises(Exception):
                importer.validate_user_id("123abc456")

    @patch("import_chatgpt_history.UserMemoryManager")
    def test_import_conversations_dry_run(self, mock_memory_manager):
        """Test dry run import functionality"""
        # Setup mock
        mock_instance = MagicMock()
        mock_memory_manager.return_value = mock_instance

        importer = ChatGPTImporter(chromadb_path=self.chromadb_path)

        # Sample conversations
        conversations = [
            {
                "id": "test-conv",
                "title": "Test",
                "turns": [
                    ("Hello, I'm John", "Hi John, nice to meet you!"),
                    ("I like cats", "Cats are wonderful pets!"),
                ],
            }
        ]

        # Test dry run
        stats = importer.import_conversations(
            user_id="123456789", conversations=conversations, dry_run=True
        )

        # Verify stats
        self.assertEqual(stats["total_conversations"], 1)
        self.assertEqual(stats["total_turns"], 2)
        self.assertEqual(stats["imported_turns"], 2)
        self.assertEqual(stats["skipped_turns"], 0)

        # Verify no actual storage calls were made
        mock_instance.store_conversation.assert_not_called()


def create_sample_export_files():
    """Create sample export files for manual testing"""

    # Sample with standard mapping format
    standard_format = [
        {
            "id": "conversation-123",
            "title": "Learning Python",
            "create_time": 1609459200,
            "mapping": {
                "node1": {
                    "message": {
                        "role": "user",
                        "content": {
                            "parts": [
                                "Hi, I'm learning Python programming. I'm 28 years old and work as a data analyst."
                            ]
                        },
                        "create_time": 1609459200,
                    }
                },
                "node2": {
                    "message": {
                        "role": "assistant",
                        "content": {
                            "parts": [
                                "That's great! Python is an excellent language for data analysis. What specific areas are you focusing on?"
                            ]
                        },
                        "create_time": 1609459300,
                    }
                },
                "node3": {
                    "message": {
                        "role": "user",
                        "content": {
                            "parts": [
                                "I'm interested in machine learning and data visualization. I live in New York and have a dog named Max."
                            ]
                        },
                        "create_time": 1609459400,
                    }
                },
                "node4": {
                    "message": {
                        "role": "assistant",
                        "content": {
                            "parts": [
                                "Machine learning and data visualization are fascinating fields! Have you worked with libraries like pandas, matplotlib, or scikit-learn?"
                            ]
                        },
                        "create_time": 1609459500,
                    }
                },
            },
        }
    ]

    # Alternative format with direct messages array
    simple_format = {
        "conversations": [
            {
                "id": "conv-456",
                "title": "Cooking Discussion",
                "messages": [
                    {
                        "role": "user",
                        "content": "I love cooking Italian food. I'm a chef at a restaurant in Boston.",
                    },
                    {
                        "role": "assistant",
                        "content": "Italian cuisine is wonderful! What are some of your favorite dishes to prepare?",
                    },
                    {
                        "role": "user",
                        "content": "I specialize in pasta dishes and I'm 35 years old. I also have two cats, Luna and Felix.",
                    },
                    {
                        "role": "assistant",
                        "content": "Pasta is such a versatile foundation for so many delicious meals! Do you make your pasta from scratch?",
                    },
                ],
            }
        ]
    }

    # Save sample files
    with open("sample_chatgpt_standard.json", "w") as f:
        json.dump(standard_format, f, indent=2)

    with open("sample_chatgpt_simple.json", "w") as f:
        json.dump(simple_format, f, indent=2)

    print("Created sample files:")
    print("- sample_chatgpt_standard.json (standard ChatGPT export format)")
    print("- sample_chatgpt_simple.json (simplified format)")
    print("\nExample usage:")
    print(
        "python import_chatgpt_history.py 123456789012345678 sample_chatgpt_standard.json --dry-run"
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "create-samples":
        create_sample_export_files()
    else:
        unittest.main()
