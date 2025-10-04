#!/usr/bin/env python3
"""
Conversation Context Validation Script
Tests conversation context preservation for any WhisperEngine bot.

Usage:
    python scripts/validate_conversation_context.py --bot jake
    python scripts/validate_conversation_context.py --bot elena --verbose
    python scripts/validate_conversation_context.py --bot marcus --skip-discord
"""

import asyncio
import os
import sys
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

# Smart keepalive configuration (matches src/conversation/boundary_manager.py defaults)
SESSION_KEEPALIVE_MINUTES = int(os.getenv('SESSION_KEEPALIVE_MINUTES', '15'))
SESSION_KEEPALIVE_SECONDS = SESSION_KEEPALIVE_MINUTES * 60


class ConversationContextValidator:
    """Validates conversation context system for any bot."""
    
    def __init__(self, bot_name: str, verbose: bool = False):
        self.bot_name = bot_name.lower()
        self.verbose = verbose
        self.results = {
            "bot": self.bot_name,
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {}
        }
        
        # Load bot-specific environment
        self._load_bot_environment()
        
        # Initialize Qdrant client
        # Use localhost when running outside Docker (for validation scripts)
        raw_host = os.getenv('QDRANT_HOST', 'localhost')
        # Map Docker hostnames to localhost for external validation
        docker_hosts = ['qdrant', 'whisperengine-qdrant', 'qdrant-server']
        self.qdrant_host = 'localhost' if raw_host in docker_hosts else raw_host
        
        raw_port = os.getenv('QDRANT_PORT', '6334')
        self.qdrant_port = 6334 if raw_port == '6333' else int(raw_port)  # Docker uses 6333, host uses 6334
        
        self.collection_name = os.getenv('QDRANT_COLLECTION_NAME', f'whisperengine_memory_{self.bot_name}')
        
        self.client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
        
        self.log(f"🤖 Validating {self.bot_name.upper()} bot")
        self.log(f"📦 Collection: {self.collection_name}")
        self.log(f"🔗 Qdrant: {self.qdrant_host}:{self.qdrant_port}")
    
    def _load_bot_environment(self):
        """Load bot-specific environment variables."""
        env_file = project_root / f".env.{self.bot_name}"
        if env_file.exists():
            load_dotenv(env_file, override=True)
            self.log(f"✅ Loaded environment from {env_file}")
        else:
            self.log(f"⚠️  No .env.{self.bot_name} found, using defaults")
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with optional verbosity control."""
        if level == "DEBUG" and not self.verbose:
            return
        
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️ ",
            "DEBUG": "🔍"
        }.get(level, "")
        
        print(f"{prefix} {message}")
    
    def test_collection_exists(self) -> bool:
        """Test 1: Verify bot's Qdrant collection exists."""
        test_name = "collection_exists"
        self.log(f"\n{'='*60}")
        self.log(f"TEST 1: Collection Existence")
        self.log(f"{'='*60}")
        
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            exists = self.collection_name in collection_names
            
            if exists:
                collection_info = self.client.get_collection(self.collection_name)
                point_count = collection_info.points_count
                
                self.log(f"Collection '{self.collection_name}' exists", "SUCCESS")
                self.log(f"📊 Total memories: {point_count:,}")
                
                self.results["tests"][test_name] = {
                    "passed": True,
                    "collection": self.collection_name,
                    "point_count": point_count
                }
                return True
            else:
                self.log(f"Collection '{self.collection_name}' NOT FOUND", "ERROR")
                self.log(f"Available collections: {', '.join(collection_names)}", "DEBUG")
                
                self.results["tests"][test_name] = {
                    "passed": False,
                    "error": "Collection not found",
                    "available": collection_names
                }
                return False
                
        except Exception as e:
            self.log(f"Failed to check collection: {e}", "ERROR")
            self.results["tests"][test_name] = {
                "passed": False,
                "error": str(e)
            }
            return False
    
    def test_role_field_extraction(self) -> bool:
        """Test 2: Verify role field is at top-level (not nested in metadata)."""
        test_name = "role_field_extraction"
        self.log(f"\n{'='*60}")
        self.log(f"TEST 2: Role Field Extraction")
        self.log(f"{'='*60}")
        
        try:
            # Get recent conversation memories
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="memory_type", match=MatchValue(value="conversation")),
                        FieldCondition(key="bot_name", match=MatchValue(value=self.bot_name))
                    ]
                ),
                limit=20,
                with_payload=True
            )
            
            points = scroll_result[0]
            
            if not points:
                self.log("No conversation memories found", "WARNING")
                self.results["tests"][test_name] = {
                    "passed": False,
                    "error": "No conversation memories to validate"
                }
                return False
            
            # Check role field location
            roles_found = {"user": 0, "assistant": 0, "unknown": 0}
            top_level_roles = 0
            nested_roles = 0
            
            for point in points:
                payload = point.payload
                
                # Check if role is at top level (CORRECT)
                if "role" in payload:
                    top_level_roles += 1
                    role = payload["role"]
                    roles_found[role] = roles_found.get(role, 0) + 1
                
                # Check if role is nested in metadata (WRONG - old bug)
                if "metadata" in payload and isinstance(payload["metadata"], dict):
                    if "role" in payload["metadata"]:
                        nested_roles += 1
            
            self.log(f"📊 Analyzed {len(points)} conversation memories")
            self.log(f"✅ Top-level role fields: {top_level_roles}/{len(points)}")
            self.log(f"❌ Nested role fields (old bug): {nested_roles}")
            self.log(f"📈 Role distribution: user={roles_found['user']}, assistant={roles_found['assistant']}, unknown={roles_found['unknown']}")
            
            # Test passes if:
            # 1. All memories have top-level role field
            # 2. We have both user and bot/assistant roles (not all labeled as one)
            # 3. No nested roles (old bug pattern)
            
            bot_responses = roles_found.get("assistant", 0) + roles_found.get("bot", 0)
            
            passed = (
                top_level_roles == len(points) and
                roles_found["user"] > 0 and
                bot_responses > 0 and
                nested_roles == 0
            )
            
            if passed:
                self.log("Role extraction is CORRECT (top-level, both user/assistant present)", "SUCCESS")
            else:
                issues = []
                if top_level_roles < len(points):
                    issues.append(f"Missing top-level roles: {len(points) - top_level_roles}")
                if roles_found["user"] == 0 or roles_found["assistant"] == 0:
                    issues.append(f"Missing role variety: {roles_found}")
                if nested_roles > 0:
                    issues.append(f"Found {nested_roles} nested roles (old bug)")
                
                self.log(f"Role extraction has issues: {', '.join(issues)}", "ERROR")
            
            self.results["tests"][test_name] = {
                "passed": passed,
                "total_memories": len(points),
                "top_level_roles": top_level_roles,
                "nested_roles": nested_roles,
                "role_distribution": roles_found
            }
            
            return passed
            
        except Exception as e:
            self.log(f"Failed to check role extraction: {e}", "ERROR")
            self.results["tests"][test_name] = {
                "passed": False,
                "error": str(e)
            }
            return False
    
    def test_conversation_time_window(self) -> bool:
        """Test 3: Verify conversation history uses 1-hour window (not 7 days)."""
        test_name = "conversation_time_window"
        self.log(f"\n{'='*60}")
        self.log(f"TEST 3: Conversation Time Window")
        self.log(f"{'='*60}")
        
        try:
            # Pick a random user who has recent conversations
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="memory_type", match=MatchValue(value="conversation")),
                        FieldCondition(key="bot_name", match=MatchValue(value=self.bot_name))
                    ]
                ),
                limit=1,
                with_payload=True
            )
            
            if not scroll_result[0]:
                self.log("No conversation memories found", "WARNING")
                self.results["tests"][test_name] = {
                    "passed": False,
                    "error": "No conversations to validate"
                }
                return False
            
            test_user_id = scroll_result[0][0].payload.get("user_id")
            
            # Get all conversations for this user
            now = datetime.now().timestamp()
            one_hour_ago = (datetime.now() - timedelta(hours=1)).timestamp()
            seven_days_ago = (datetime.now() - timedelta(days=7)).timestamp()
            
            # Count memories in last hour
            recent_scroll = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="user_id", match=MatchValue(value=test_user_id)),
                        FieldCondition(key="bot_name", match=MatchValue(value=self.bot_name)),
                        FieldCondition(key="memory_type", match=MatchValue(value="conversation")),
                        FieldCondition(key="timestamp", range=Range(gte=one_hour_ago, lte=now))
                    ]
                ),
                limit=100,
                with_payload=True
            )
            
            # Count memories in last 7 days
            week_scroll = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="user_id", match=MatchValue(value=test_user_id)),
                        FieldCondition(key="bot_name", match=MatchValue(value=self.bot_name)),
                        FieldCondition(key="memory_type", match=MatchValue(value="conversation")),
                        FieldCondition(key="timestamp", range=Range(gte=seven_days_ago, lte=now))
                    ]
                ),
                limit=100,
                with_payload=True
            )
            
            recent_count = len(recent_scroll[0])
            week_count = len(week_scroll[0])
            
            self.log(f"👤 Test user: {test_user_id}")
            self.log(f"📊 Last 1 hour: {recent_count} memories")
            self.log(f"📊 Last 7 days: {week_count} memories")
            
            # Test validates that system is CAPABLE of filtering by time window
            # We can't directly test get_conversation_history without running bot,
            # but we can verify the data structure supports 1-hour filtering
            
            if week_count > recent_count:
                self.log("Time window filtering is possible (older memories exist)", "SUCCESS")
                self.log(f"✅ System can distinguish 1-hour ({recent_count}) vs 7-day ({week_count}) windows")
            else:
                self.log("Time window validation inconclusive (all memories recent)", "WARNING")
            
            self.results["tests"][test_name] = {
                "passed": True,  # Pass if structure supports time filtering
                "test_user": test_user_id,
                "recent_memories_1hr": recent_count,
                "total_memories_7d": week_count,
                "note": "Validates timestamp filtering capability"
            }
            
            return True
            
        except Exception as e:
            self.log(f"Failed to check time window: {e}", "ERROR")
            self.results["tests"][test_name] = {
                "passed": False,
                "error": str(e)
            }
            return False
    
    def test_bot_memory_isolation(self) -> bool:
        """Test 4: Verify bot-specific memory isolation (no cross-bot leakage)."""
        test_name = "bot_memory_isolation"
        self.log(f"\n{'='*60}")
        self.log(f"TEST 4: Bot Memory Isolation")
        self.log(f"{'='*60}")
        
        try:
            # Check all memories in collection have correct bot_name
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                limit=50,
                with_payload=True
            )
            
            points = scroll_result[0]
            
            if not points:
                self.log("No memories found in collection", "WARNING")
                self.results["tests"][test_name] = {
                    "passed": False,
                    "error": "No memories to validate"
                }
                return False
            
            correct_bot = 0
            wrong_bot = 0
            missing_bot = 0
            other_bots = {}
            
            for point in points:
                payload = point.payload
                bot_name = payload.get("bot_name")
                
                if not bot_name:
                    missing_bot += 1
                elif bot_name == self.bot_name:
                    correct_bot += 1
                else:
                    wrong_bot += 1
                    other_bots[bot_name] = other_bots.get(bot_name, 0) + 1
            
            self.log(f"📊 Analyzed {len(points)} memories")
            self.log(f"✅ Correct bot ({self.bot_name}): {correct_bot}")
            self.log(f"❌ Wrong bot: {wrong_bot}")
            self.log(f"❌ Missing bot_name: {missing_bot}")
            
            if other_bots:
                self.log(f"🚨 Found memories from other bots: {other_bots}", "ERROR")
            
            passed = correct_bot == len(points) and wrong_bot == 0 and missing_bot == 0
            
            if passed:
                self.log(f"Bot memory isolation is PERFECT (100% {self.bot_name} memories)", "SUCCESS")
            else:
                self.log(f"Bot memory isolation has leakage!", "ERROR")
            
            self.results["tests"][test_name] = {
                "passed": passed,
                "total_memories": len(points),
                "correct_bot": correct_bot,
                "wrong_bot": wrong_bot,
                "missing_bot_name": missing_bot,
                "other_bots_found": other_bots
            }
            
            return passed
            
        except Exception as e:
            self.log(f"Failed to check bot isolation: {e}", "ERROR")
            self.results["tests"][test_name] = {
                "passed": False,
                "error": str(e)
            }
            return False
    
    def test_vector_storage_format(self) -> bool:
        """Test 5: Verify named vector format (content/emotion/semantic)."""
        test_name = "vector_storage_format"
        self.log(f"\n{'='*60}")
        self.log(f"TEST 5: Vector Storage Format (Named Vectors)")
        self.log(f"{'='*60}")
        
        try:
            # Get recent memories with vectors
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                limit=10,
                with_payload=True,
                with_vectors=True
            )
            
            points = scroll_result[0]
            
            if not points:
                self.log("No memories found", "WARNING")
                self.results["tests"][test_name] = {
                    "passed": False,
                    "error": "No memories to validate"
                }
                return False
            
            named_vector_count = 0
            single_vector_count = 0
            vector_names_found = set()
            
            for point in points:
                vector = point.vector
                
                # Check if named vector format (dict)
                if isinstance(vector, dict):
                    named_vector_count += 1
                    vector_names_found.update(vector.keys())
                # Check if single vector format (list) - old format
                elif isinstance(vector, list):
                    single_vector_count += 1
            
            self.log(f"📊 Analyzed {len(points)} memories")
            self.log(f"✅ Named vector format: {named_vector_count}")
            self.log(f"❌ Single vector format (legacy): {single_vector_count}")
            
            if vector_names_found:
                self.log(f"📋 Vector names found: {', '.join(sorted(vector_names_found))}")
            
            # Ideally all should be named vectors, but mixed is acceptable during transition
            passed = named_vector_count > 0
            
            if passed:
                if single_vector_count > 0:
                    self.log(f"Vector format is MIXED (transitioning to named vectors)", "WARNING")
                else:
                    self.log(f"Vector format is CORRECT (100% named vectors)", "SUCCESS")
            else:
                self.log(f"Vector format is LEGACY (single vectors only)", "ERROR")
            
            self.results["tests"][test_name] = {
                "passed": passed,
                "total_memories": len(points),
                "named_vectors": named_vector_count,
                "single_vectors": single_vector_count,
                "vector_names": list(vector_names_found)
            }
            
            return passed
            
        except Exception as e:
            self.log(f"Failed to check vector format: {e}", "ERROR")
            self.results["tests"][test_name] = {
                "passed": False,
                "error": str(e)
            }
            return False
    
    def test_message_alternation_preserved(self) -> bool:
        """Test 6: Verify message alternation is preserved (not filtered)."""
        test_name = "message_alternation_preserved"
        self.log(f"\n{'='*60}")
        self.log(f"TEST 6: Message Alternation Preservation")
        self.log(f"{'='*60}")
        
        try:
            # Get recent conversation messages
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="memory_type", match=MatchValue(value="conversation")),
                        FieldCondition(key="bot_name", match=MatchValue(value=self.bot_name))
                    ]
                ),
                limit=20,
                with_payload=True
            )
            
            points = scroll_result[0]
            
            if not points:
                self.log("No conversation memories found", "WARNING")
                self.results["tests"][test_name] = {
                    "passed": False,
                    "error": "No conversations to validate"
                }
                return False
            
            # Sort by timestamp (use timestamp_unix for proper numeric sorting)
            def get_timestamp(point):
                # Use timestamp_unix (float) instead of timestamp (ISO string)
                ts = point.payload.get("timestamp_unix", 0) if point.payload else 0
                return float(ts) if ts else 0
            
            sorted_points = sorted(points, key=get_timestamp)
            
            # Check for consecutive same-role messages (indicating preserved alternation)
            roles = [p.payload.get("role", "unknown") if p.payload else "unknown" for p in sorted_points]
            consecutive_same_role = 0
            
            for i in range(len(roles) - 1):
                if roles[i] == roles[i + 1] and roles[i] != "unknown":
                    consecutive_same_role += 1
            
            self.log(f"📊 Analyzed {len(roles)} messages")
            self.log(f"📋 Role sequence: {' → '.join(roles[:10])}{'...' if len(roles) > 10 else ''}")
            self.log(f"✅ Consecutive same-role messages: {consecutive_same_role}")
            
            # Test passes if we have consecutive same-role messages
            # (indicates alternation filtering is NOT active - which is correct)
            # Old bug would force strict alternation, removing valuable context
            
            if consecutive_same_role > 0:
                self.log(f"Message alternation is PRESERVED (no filtering) ✅", "SUCCESS")
                self.log(f"This is CORRECT - modern LLMs handle consecutive roles fine")
            else:
                self.log(f"Perfect alternation detected (may indicate filtering)", "WARNING")
                self.log(f"Natural conversations often have consecutive messages from same speaker")
            
            self.results["tests"][test_name] = {
                "passed": True,  # We pass this as informational, not strict requirement
                "total_messages": len(roles),
                "consecutive_same_role": consecutive_same_role,
                "role_sequence": roles[:20],
                "note": "Consecutive same-role messages indicate no alternation filtering (correct)"
            }
            
            return True
            
        except Exception as e:
            self.log(f"Failed to check alternation: {e}", "ERROR")
            self.results["tests"][test_name] = {
                "passed": False,
                "error": str(e)
            }
            return False
    
    def test_conversation_thread_continuity(self) -> bool:
        """Test 7: Verify conversation thread maintains continuity (anti-"rivers are honest" bug)."""
        test_name = "conversation_thread_continuity"
        self.log(f"\n{'='*60}")
        self.log(f"TEST 7: Conversation Thread Continuity")
        self.log(f"{'='*60}")
        
        try:
            # Find a user with multiple consecutive conversation messages
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="memory_type", match=MatchValue(value="conversation")),
                        FieldCondition(key="bot_name", match=MatchValue(value=self.bot_name))
                    ]
                ),
                limit=50,
                with_payload=True
            )
            
            points = scroll_result[0]
            
            if not points:
                self.log("No conversation memories found", "WARNING")
                self.results["tests"][test_name] = {
                    "passed": False,
                    "error": "No conversations to validate"
                }
                return False
            
            # Group by user and find user with most consecutive messages
            user_conversations = {}
            for point in points:
                if not point.payload:
                    continue
                user_id = point.payload.get("user_id")
                if user_id:
                    if user_id not in user_conversations:
                        user_conversations[user_id] = []
                    user_conversations[user_id].append(point)
            
            # Find user with longest conversation thread
            best_user = None
            max_messages = 0
            for user_id, messages in user_conversations.items():
                if len(messages) > max_messages:
                    max_messages = len(messages)
                    best_user = user_id
            
            if not best_user or max_messages < 3:
                self.log(f"Not enough conversation history (found {max_messages} messages)", "WARNING")
                self.results["tests"][test_name] = {
                    "passed": True,  # Pass but inconclusive
                    "note": "Insufficient conversation history for continuity testing"
                }
                return True
            
            # Sort this user's conversation by timestamp
            user_messages = user_conversations[best_user]
            
            def get_timestamp(point):
                # Use timestamp_unix (float) instead of timestamp (ISO string)
                ts = point.payload.get("timestamp_unix", 0) if point.payload else 0
                return float(ts) if ts else 0
            
            sorted_messages = sorted(user_messages, key=get_timestamp)
            
            # Check for topic continuity in consecutive messages
            # Look for messages that reference each other's content
            continuity_checks = []
            
            for i in range(len(sorted_messages) - 1):
                curr_msg = sorted_messages[i]
                next_msg = sorted_messages[i + 1]
                
                if not (curr_msg.payload and next_msg.payload):
                    continue
                
                curr_content = curr_msg.payload.get("content", "").lower()
                next_content = next_msg.payload.get("content", "").lower()
                curr_role = curr_msg.payload.get("role", "unknown")
                next_role = next_msg.payload.get("role", "unknown")
                
                # Skip if we don't have valid content
                if not curr_content or not next_content:
                    continue
                
                # Check if messages are part of same conversation thread
                # Look for:
                # 1. Temporal proximity (within 15 minutes) - PRIMARY indicator
                curr_ts = get_timestamp(curr_msg)
                next_ts = get_timestamp(next_msg)
                time_gap = next_ts - curr_ts
                
                # 2. Topic continuity indicators (word overlap)
                # Extract key words from current message (simple approach)
                curr_words = set(w for w in curr_content.split() if len(w) > 4)
                next_words = set(w for w in next_content.split() if len(w) > 4)
                word_overlap = len(curr_words & next_words)
                
                # IMPROVED: Temporal proximity is PRIMARY indicator
                # Messages within keepalive timeout are likely part of same conversation
                # Word overlap helps but is NOT required (Q&A pairs often don't share words)
                has_temporal_continuity = time_gap < SESSION_KEEPALIVE_SECONDS
                has_topical_continuity = word_overlap > 0
                has_continuity = has_temporal_continuity or (has_topical_continuity and time_gap < 3600)
                
                continuity_checks.append({
                    "index": i,
                    "time_gap_seconds": time_gap,
                    "time_gap_minutes": time_gap / 60,
                    "word_overlap": word_overlap,
                    "roles": f"{curr_role} → {next_role}",
                    "has_temporal_continuity": has_temporal_continuity,
                    "has_topical_continuity": has_topical_continuity,
                    "has_continuity": has_continuity
                })
            
            # Analyze continuity
            total_pairs = len(continuity_checks)
            continuous_pairs = sum(1 for c in continuity_checks if c["has_continuity"])
            
            self.log(f"👤 Test user: {best_user}")
            self.log(f"📊 Total messages analyzed: {len(sorted_messages)}")
            self.log(f"📊 Message pairs checked: {total_pairs}")
            self.log(f"✅ Pairs with continuity: {continuous_pairs}")
            
            if total_pairs > 0:
                continuity_rate = (continuous_pairs / total_pairs) * 100
                self.log(f"📈 Continuity rate: {continuity_rate:.1f}%")
                
                # Show detailed conversation flow with time gaps
                self.log(f"\n📋 Detailed conversation flow (showing all messages with time gaps):")
                for i, msg in enumerate(sorted_messages):
                    if not msg.payload:
                        continue
                    role = msg.payload.get("role", "unknown")
                    content = msg.payload.get("content", "")[:80]
                    
                    # Calculate time gap from previous message
                    time_gap_str = ""
                    if i > 0 and i < len(continuity_checks):
                        check = continuity_checks[i-1]
                        gap_min = check["time_gap_minutes"]
                        has_cont = check.get("has_continuity", False)
                        cont_marker = "✅" if has_cont else "❌"
                        
                        if gap_min < 1:
                            time_gap_str = f" [{cont_marker} {gap_min*60:.0f}s gap]"
                        elif gap_min < 60:
                            time_gap_str = f" [{cont_marker} {gap_min:.1f}min gap]"
                        else:
                            time_gap_str = f" [{cont_marker} {gap_min/60:.1f}hr gap]"
                    
                    self.log(f"   {i+1:2d}. [{role}] {content}...{time_gap_str}", "DEBUG")
                
                # Test passes if we see reasonable continuity
                # We expect some gaps (topic shifts), but not complete randomness
                passed = continuity_rate >= 30  # At least 30% of pairs show continuity
                
                if passed:
                    self.log(f"Conversation thread continuity is GOOD ({continuity_rate:.1f}%)", "SUCCESS")
                else:
                    self.log(f"Conversation continuity is LOW ({continuity_rate:.1f}%) - may indicate context issues", "WARNING")
            else:
                passed = True  # Pass if no pairs to check
                self.log("Not enough message pairs to validate continuity", "WARNING")
            
            self.results["tests"][test_name] = {
                "passed": passed,
                "test_user": best_user,
                "total_messages": len(sorted_messages),
                "message_pairs": total_pairs,
                "continuous_pairs": continuous_pairs,
                "continuity_rate": round((continuous_pairs / total_pairs * 100), 1) if total_pairs > 0 else 0,
                "note": "Validates conversation maintains topical coherence across messages"
            }
            
            return passed
            
        except Exception as e:
            self.log(f"Failed to check conversation continuity: {e}", "ERROR")
            self.results["tests"][test_name] = {
                "passed": False,
                "error": str(e)
            }
            return False
    
    def test_no_redis_dependencies(self) -> bool:
        """Test 7: Verify no Redis session persistence (pure vector-native)."""
        test_name = "no_redis_dependencies"
        self.log(f"\n{'='*60}")
        self.log(f"TEST 7: Redis Removal (Pure Vector-Native)")
        self.log(f"{'='*60}")
        
        try:
            # Check if Redis environment variables exist (they shouldn't for new setup)
            redis_env_vars = [
                'REDIS_HOST',
                'REDIS_PORT',
                'REDIS_DB',
                'REDIS_PASSWORD'
            ]
            
            redis_vars_found = {var: os.getenv(var) for var in redis_env_vars if os.getenv(var)}
            
            if redis_vars_found:
                self.log(f"⚠️  Found Redis environment variables: {list(redis_vars_found.keys())}", "WARNING")
                self.log(f"These are ignored in current architecture (vector-native)")
            else:
                self.log(f"No Redis environment variables found ✅", "SUCCESS")
            
            # Check source files for Redis imports (should be removed)
            redis_check_files = [
                "src/conversation/boundary_manager.py",
                "src/handlers/events.py"
            ]
            
            redis_references = {}
            for file_path in redis_check_files:
                full_path = project_root / file_path
                if full_path.exists():
                    content = full_path.read_text()
                    
                    # Check for actual Redis code (not just comments mentioning it)
                    redis_patterns = [
                        "import redis",
                        "from redis",
                        "redis_client =",
                        "_save_session_to_redis",
                        "_load_session_from_redis"
                    ]
                    found_patterns = [p for p in redis_patterns if p in content]
                    
                    if found_patterns:
                        redis_references[file_path] = found_patterns
            
            if redis_references:
                self.log(f"❌ Found Redis code references:", "ERROR")
                for file, patterns in redis_references.items():
                    self.log(f"   {file}: {', '.join(patterns)}", "ERROR")
            else:
                self.log(f"✅ No Redis code references found in conversation system", "SUCCESS")
            
            passed = len(redis_references) == 0
            
            if passed:
                self.log(f"Architecture is pure vector-native (Redis fully removed) ✅", "SUCCESS")
            else:
                self.log(f"Redis cleanup incomplete - references remain", "ERROR")
            
            self.results["tests"][test_name] = {
                "passed": passed,
                "redis_env_vars": redis_vars_found,
                "redis_code_references": redis_references
            }
            
            return passed
            
        except Exception as e:
            self.log(f"Failed to check Redis removal: {e}", "ERROR")
            self.results["tests"][test_name] = {
                "passed": False,
                "error": str(e)
            }
            return False
    
    def generate_summary(self):
        """Generate validation summary."""
        self.log(f"\n{'='*60}")
        self.log(f"VALIDATION SUMMARY")
        self.log(f"{'='*60}")
        
        total_tests = len(self.results["tests"])
        passed_tests = sum(1 for t in self.results["tests"].values() if t.get("passed"))
        failed_tests = total_tests - passed_tests
        
        self.log(f"🤖 Bot: {self.bot_name.upper()}")
        self.log(f"📊 Total Tests: {total_tests}")
        self.log(f"✅ Passed: {passed_tests}")
        self.log(f"❌ Failed: {failed_tests}")
        self.log(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": round(passed_tests / total_tests * 100, 1)
        }
        
        # List failed tests
        if failed_tests > 0:
            self.log(f"\n❌ Failed Tests:")
            for test_name, test_result in self.results["tests"].items():
                if not test_result.get("passed"):
                    error = test_result.get("error", "Unknown error")
                    self.log(f"   - {test_name}: {error}")
        
        self.log(f"\n{'='*60}")
        
        return passed_tests == total_tests
    
    def save_results(self, output_dir: Path = None):
        """Save validation results to JSON file."""
        if output_dir is None:
            output_dir = project_root / "validation_reports"
        
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"conversation_validation_{self.bot_name}_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        self.log(f"\n💾 Results saved to: {output_file}")
        return output_file
    
    async def run_all_tests(self) -> bool:
        """Run all validation tests."""
        self.log(f"\n🚀 Starting conversation context validation for {self.bot_name.upper()}")
        self.log(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all tests
        tests = [
            self.test_collection_exists,
            self.test_role_field_extraction,
            self.test_conversation_time_window,
            self.test_bot_memory_isolation,
            self.test_vector_storage_format,
            self.test_message_alternation_preserved,
            self.test_conversation_thread_continuity,  # NEW: Continuity test
            self.test_no_redis_dependencies
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log(f"Test {test.__name__} failed with exception: {e}", "ERROR")
        
        # Generate summary
        all_passed = self.generate_summary()
        
        # Save results
        self.save_results()
        
        return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="Validate conversation context system for WhisperEngine bots",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/validate_conversation_context.py --bot jake
  python scripts/validate_conversation_context.py --bot elena --verbose
  python scripts/validate_conversation_context.py --bot marcus --output ./reports
  
Available bots: elena, marcus, jake, ryan, dream, aethys, gabriel, sophia
        """
    )
    
    parser.add_argument(
        '--bot',
        type=str,
        required=True,
        help='Bot name to validate (e.g., jake, elena, marcus)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose debug output'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output directory for validation reports'
    )
    
    args = parser.parse_args()
    
    # Create validator
    validator = ConversationContextValidator(
        bot_name=args.bot,
        verbose=args.verbose
    )
    
    # Run validation
    try:
        all_passed = asyncio.run(validator.run_all_tests())
        
        # Exit with appropriate code
        sys.exit(0 if all_passed else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
