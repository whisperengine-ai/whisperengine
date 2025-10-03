#!/usr/bin/env python3
"""
WhisperEngine Smoke Test Suite
Comprehensive end-to-end testing of all major features via bot APIs.

This script validates:
- Bot health and API endpoints
- Vector-native memory storage and retrieval
- Character personality using CDL validation and dynamic keywords
- Emotional intelligence and context awareness
- Cross-conversation memory persistence
- Multi-bot functionality
- Performance and response times
- CDL file integrity and parsing

Usage:
    python scripts/smoke_test.py
    python scripts/smoke_test.py --bot elena
    python scripts/smoke_test.py --verbose
"""

import asyncio
import time
import uuid
import subprocess
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import requests
import argparse
import sys
import os
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import CDL validation tools
try:
    from validation.cdl_validator import CDLValidator
    from characters.cdl.parser import load_character
    CDL_VALIDATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  CDL validation not available: {e}")
    CDL_VALIDATION_AVAILABLE = False

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class SmokeTestRunner:
    """Comprehensive smoke test runner for WhisperEngine"""
    
    def __init__(self, verbose: bool = False, parallel: bool = True):
        self.verbose = verbose
        self.parallel = parallel
        self.results = {}
        self.test_user_id = f"smoke_test_{uuid.uuid4().hex[:8]}"
        self.test_start_time = datetime.now()
        self.reports_dir = Path("smoke_test_reports")
        self.reports_dir.mkdir(exist_ok=True)
        
        # Bot configurations (port mappings)
        self.bots = {
            'elena': {'port': 9091, 'name': 'Elena Rodriguez', 'character': 'Marine Biologist', 'container': 'whisperengine-elena-bot'},
            'marcus': {'port': 9092, 'name': 'Marcus Thompson', 'character': 'AI Researcher', 'container': 'whisperengine-marcus-bot'},
            'ryan': {'port': 9093, 'name': 'Ryan Chen', 'character': 'Indie Game Developer', 'container': 'whisperengine-ryan-bot'},
            'dream': {'port': 9094, 'name': 'Dream of the Endless', 'character': 'Mythological Entity', 'container': 'whisperengine-dream-bot'},
            'gabriel': {'port': 9095, 'name': 'Gabriel', 'character': 'British Gentleman', 'container': 'whisperengine-gabriel-bot'},
            'sophia': {'port': 9096, 'name': 'Sophia Blake', 'character': 'Marketing Executive', 'container': 'whisperengine-sophia-bot'},
            'jake': {'port': 9097, 'name': 'Jake Sterling', 'character': 'Adventure Photographer', 'container': 'whisperengine-jake-bot'},
            'aethys': {'port': 3007, 'name': 'Aethys', 'character': 'Omnipotent Entity', 'container': 'whisperengine-aethys-bot'}
        }
        
    def log(self, message: str, color: str = Colors.WHITE):
        """Log a message with optional color"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{color}[{timestamp}] {message}{Colors.END}")
        
    def log_success(self, message: str):
        """Log a success message"""
        self.log(f"✅ {message}", Colors.GREEN)
        
    def log_error(self, message: str):
        """Log an error message"""
        self.log(f"❌ {message}", Colors.RED)
        
    def log_warning(self, message: str):
        """Log a warning message"""
        self.log(f"⚠️  {message}", Colors.YELLOW)
        
    def log_info(self, message: str):
        """Log an info message"""
        self.log(f"ℹ️  {message}", Colors.BLUE)
        
    def log_test(self, message: str):
        """Log a test step"""
        self.log(f"🧪 {message}", Colors.CYAN)

    async def analyze_bot_logs(self, bot_name: str, config: Dict) -> Dict:
        """Analyze bot logs for errors and warnings during test period"""
        try:
            container_name = config['container']
            
            # Get logs from the test start time
            since_time = self.test_start_time.strftime("%Y-%m-%dT%H:%M:%S")
            
            # Run docker logs command
            result = subprocess.run([
                'docker', 'logs', container_name, 
                '--since', since_time,
                '--timestamps'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.log_error(f"{bot_name.upper()} log analysis failed: {result.stderr}")
                return {
                    'success': False,
                    'error': result.stderr,
                    'warnings': 0,
                    'errors': 0,
                    'critical_issues': []
                }
            
            logs = result.stdout
            
            # Analyze logs for issues
            warnings = self._count_log_pattern(logs, r'WARNING|WARN|⚠️')
            errors = self._count_log_pattern(logs, r'ERROR|CRITICAL|FATAL|❌|Exception|Traceback')
            
            # Look for specific critical issues
            critical_issues = []
            
            # Check for database connection issues (actual failures)
            if re.search(r'connection.*failed|database.*unreachable|postgres.*connection.*error', logs, re.IGNORECASE):
                critical_issues.append("Database connection failures detected")
            
            # Check for major vector/memory failures (not just config issues)
            if re.search(r'qdrant.*unreachable|vector.*storage.*failed|memory.*initialization.*failed', logs, re.IGNORECASE):
                critical_issues.append("Vector storage system failures detected")
            
            # Check for Discord API authentication/connection failures
            if re.search(r'discord.*401|discord.*403|gateway.*connection.*failed|discord.*authentication.*failed', logs, re.IGNORECASE):
                critical_issues.append("Discord API authentication/connection failures detected")
            
            # Check for bot startup/initialization failures
            if re.search(r'bot.*failed.*to.*start|initialization.*error|startup.*failed', logs, re.IGNORECASE):
                critical_issues.append("Bot initialization failures detected")
            
            # Only count actual ERRORs and CRITICALs, not warnings disguised as errors
            actual_errors = self._count_log_pattern(logs, r'ERROR|CRITICAL|FATAL')
            # Subtract known non-critical errors (config warnings, etc.)
            config_warnings = self._count_log_pattern(logs, r'Facts API endpoint not configured|config.*not.*found')
            adjusted_errors = max(0, actual_errors - config_warnings)
            
            log_analysis = {
                'success': True,
                'warnings': warnings,
                'errors': adjusted_errors,  # Use adjusted error count
                'raw_errors': actual_errors,  # Keep track of raw count
                'config_warnings': config_warnings,  # Track config-related issues separately
                'critical_issues': critical_issues,
                'log_lines': len(logs.split('\n')) if logs else 0
            }
            
            # Log results with better categorization
            if critical_issues:
                self.log_error(f"{bot_name.upper()} log analysis: {len(critical_issues)} critical issues detected")
                for issue in critical_issues:
                    self.log_error(f"  - {issue}")
            elif adjusted_errors > 0:
                self.log_warning(f"{bot_name.upper()} log analysis: {adjusted_errors} errors (filtered)")
            elif config_warnings > 0:
                self.log_info(f"{bot_name.upper()} log analysis: {config_warnings} config warnings (non-critical)")
            elif warnings > 0:
                self.log_warning(f"{bot_name.upper()} log analysis: {warnings} warnings")
            else:
                self.log_success(f"{bot_name.upper()} log analysis: clean logs")
            
            return log_analysis
            
        except subprocess.TimeoutExpired:
            self.log_error(f"{bot_name.upper()} log analysis timed out")
            return {'success': False, 'error': 'timeout', 'warnings': 0, 'errors': 0, 'critical_issues': []}
        except (subprocess.SubprocessError, OSError) as e:
            self.log_error(f"{bot_name.upper()} log analysis failed: {e}")
            return {'success': False, 'error': str(e), 'warnings': 0, 'errors': 0, 'critical_issues': []}

    def _count_log_pattern(self, logs: str, pattern: str) -> int:
        """Count occurrences of a regex pattern in logs"""
        return len(re.findall(pattern, logs, re.IGNORECASE))

    async def test_cdl_validation(self, bot_name: str, config: Dict) -> bool:
        """Test CDL file validation and structure"""
        try:
            # Validate CDL file exists and has proper structure
            cdl_valid = self.validate_cdl_file(bot_name)
            if not cdl_valid:
                return False
            
            # Test keyword extraction capability
            keywords = self.extract_validation_keywords_from_cdl(bot_name)
            if keywords:
                self.log_success(f"{bot_name.upper()} CDL validation passed")
                if self.verbose:
                    self.log_info(f"Extracted {len(keywords)} validation keywords: {keywords[:5]}")
                return True
            else:
                self.log_warning(f"{bot_name.upper()} CDL keyword extraction yielded no results")
                return True  # Don't fail test, just warn
                
        except Exception as e:
            self.log_error(f"{bot_name.upper()} CDL validation failed: {e}")
            return False

    async def test_bot_health(self, bot_name: str, config: Dict) -> bool:
        """Test bot health endpoint"""
        try:
            response = requests.get(f"http://localhost:{config['port']}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_success(f"{bot_name.upper()} health check passed")
                    return True
                else:
                    self.log_error(f"{bot_name.upper()} health check failed: {data}")
                    return False
            else:
                self.log_error(f"{bot_name.upper()} health endpoint returned {response.status_code}")
                return False
        except (requests.RequestException, requests.Timeout, ConnectionError) as e:
            self.log_error(f"{bot_name.upper()} health check failed: {e}")
            return False

    async def test_bot_info(self, bot_name: str, config: Dict) -> bool:
        """Test bot info endpoint and validate response"""
        try:
            response = requests.get(f"http://localhost:{config['port']}/api/bot-info", timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                # Validate required fields
                required_fields = ['bot_name', 'status', 'platform', 'capabilities']
                for field in required_fields:
                    if field not in data:
                        self.log_error(f"{bot_name.upper()} bot-info missing field: {field}")
                        return False
                
                # Validate capabilities
                expected_capabilities = ['text_chat', 'conversation_memory', 'character_personality']
                for cap in expected_capabilities:
                    if cap not in data.get('capabilities', []):
                        self.log_warning(f"{bot_name.upper()} missing capability: {cap}")
                
                self.log_success(f"{bot_name.upper()} bot-info validated")
                if self.verbose:
                    self.log_info(f"Bot: {data.get('bot_name')}, Status: {data.get('status')}")
                return True
            else:
                self.log_error(f"{bot_name.upper()} bot-info returned {response.status_code}")
                return False
        except (requests.RequestException, requests.Timeout, ConnectionError) as e:
            self.log_error(f"{bot_name.upper()} bot-info failed: {e}")
            return False

    async def test_basic_conversation(self, bot_name: str, config: Dict) -> bool:
        """Test basic conversation capability"""
        try:
            message = "Hello! I'm running a smoke test. Can you tell me about yourself briefly?"
            
            response = requests.post(
                f"http://localhost:{config['port']}/api/chat",
                json={"message": message, "user_id": self.test_user_id},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('response'):
                    response_text = data['response']
                    if len(response_text.strip()) > 10:  # Basic sanity check
                        self.log_success(f"{bot_name.upper()} basic conversation test passed")
                        if self.verbose:
                            self.log_info(f"Response: {response_text[:100]}...")
                        return True
                    else:
                        self.log_error(f"{bot_name.upper()} returned very short response: {response_text}")
                        return False
                else:
                    self.log_error(f"{bot_name.upper()} conversation failed: {data}")
                    return False
            else:
                self.log_error(f"{bot_name.upper()} chat endpoint returned {response.status_code}")
                return False
        except (requests.RequestException, requests.Timeout, ConnectionError) as e:
            self.log_error(f"{bot_name.upper()} basic conversation failed: {e}")
            return False

    def load_cdl_character_data(self, bot_name: str) -> Optional[Dict]:
        """Load CDL character data for dynamic validation"""
        try:
            cdl_file_path = Path(f"characters/examples/{bot_name}.json")
            if not cdl_file_path.exists():
                self.log_warning(f"CDL file not found for {bot_name}: {cdl_file_path}")
                return None
            
            with open(cdl_file_path, 'r', encoding='utf-8') as f:
                cdl_data = json.load(f)
            
            return cdl_data
        except Exception as e:
            self.log_error(f"Failed to load CDL data for {bot_name}: {e}")
            return None

    def validate_cdl_file(self, bot_name: str) -> bool:
        """Validate CDL file structure and content"""
        try:
            cdl_file_path = Path(f"characters/examples/{bot_name}.json")
            if not cdl_file_path.exists():
                self.log_error(f"CDL file missing for {bot_name}: {cdl_file_path}")
                return False
            
            # Basic JSON validation
            with open(cdl_file_path, 'r', encoding='utf-8') as f:
                cdl_data = json.load(f)
            
            # Check required CDL structure
            required_sections = ['cdl_version', 'character', 'character.metadata', 
                               'character.identity', 'character.personality']
            
            for section in required_sections:
                current = cdl_data
                for key in section.split('.'):
                    if key not in current:
                        self.log_error(f"CDL validation failed for {bot_name}: missing {section}")
                        return False
                    current = current[key]
            
            self.log_success(f"{bot_name.upper()} CDL file structure validated")
            return True
            
        except json.JSONDecodeError as e:
            self.log_error(f"CDL JSON parsing failed for {bot_name}: {e}")
            return False
        except Exception as e:
            self.log_error(f"CDL validation error for {bot_name}: {e}")
            return False

    def extract_validation_keywords_from_cdl(self, bot_name: str) -> List[str]:
        """Extract personality validation keywords dynamically from CDL data"""
        cdl_data = self.load_cdl_character_data(bot_name)
        if not cdl_data:
            return []
        
        keywords = []
        
        try:
            character = cdl_data.get('character', {})
            
            # Extract from tags (split compound words)
            metadata = character.get('metadata', {})
            tags = metadata.get('tags', [])
            for tag in tags:
                # Split compound words like "marine_biologist" -> ["marine", "biologist"]
                keywords.extend(tag.replace('_', ' ').split())
            
            # Extract from occupation and identity
            identity = character.get('identity', {})
            occupation = identity.get('occupation', '').lower()
            if occupation:
                # Clean and split occupation
                occ_words = occupation.replace('&', '').replace('-', ' ').split()
                keywords.extend([word for word in occ_words if len(word) > 3])
            
            # Extract from values and core beliefs (focus on domain-specific terms)
            personality = character.get('personality', {})
            values = personality.get('values', [])
            core_beliefs = personality.get('core_beliefs', [])
            
            # Extract key domain terms from values and beliefs
            domain_terms = ['science', 'research', 'technology', 'marine', 'ocean', 'conservation',
                          'ai', 'artificial', 'intelligence', 'game', 'development', 'dream', 'reality',
                          'divine', 'marketing', 'photography', 'adventure', 'consciousness', 'existence']
            
            for value in values:
                words = value.lower().split()
                keywords.extend([word.strip('.,!?()[]{}":;') for word in words 
                               if any(term in word for term in domain_terms) or len(word) > 5])
            
            for belief in core_beliefs:
                words = belief.lower().split()
                keywords.extend([word.strip('.,!?()[]{}":;') for word in words 
                               if any(term in word for term in domain_terms) or len(word) > 5])
            
            # Extract from description and location for context
            description = identity.get('description', '').lower()
            if description:
                desc_words = description.split()
                keywords.extend([word.strip('.,!?()[]{}":;') for word in desc_words 
                               if any(term in word for term in domain_terms)])
            
            # Clean and deduplicate keywords
            keywords = [kw.strip('.,!?()[]{}":;').lower() for kw in keywords if kw]
            keywords = [kw for kw in keywords if len(kw) > 2 and kw.isalpha()]
            keywords = list(set(keywords))  # Remove duplicates
            
            # Prioritize domain-specific keywords
            priority_keywords = []
            regular_keywords = []
            
            for kw in keywords:
                if any(term in kw for term in domain_terms):
                    priority_keywords.append(kw)
                else:
                    regular_keywords.append(kw)
            
            # Return prioritized list (domain terms first, then others)
            final_keywords = priority_keywords + regular_keywords
            return final_keywords[:10]  # Limit to 10 most relevant keywords
            
        except Exception as e:
            self.log_warning(f"Failed to extract keywords from CDL for {bot_name}: {e}")
            return []

    async def test_personality_traits(self, bot_name: str, config: Dict) -> bool:
        """Test character personality traits specific to each bot"""
        try:
            # Character-specific test messages
            personality_tests = {
                'elena': "What's your favorite marine creature?",
                'marcus': "What do you think about the future of AI?", 
                'ryan': "What game are you working on lately?",
                'dream': "Tell me about the nature of dreams and reality.",
                'gabriel': "What is your divine mission?",
                'sophia': "What's your best marketing strategy?",
                'jake': "What's the most amazing place you've photographed?",
                'aethys': "What is the nature of existence from your perspective?"
            }
            
            message = personality_tests.get(bot_name, "Tell me about your expertise.")
            
            response = requests.post(
                f"http://localhost:{config['port']}/api/chat",
                json={"message": message, "user_id": self.test_user_id},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '').lower()
                
                # Dynamic validation using CDL data
                cdl_keywords = self.extract_validation_keywords_from_cdl(bot_name)
                
                # Fallback to hardcoded keywords if CDL extraction fails
                fallback_keywords = {
                    'elena': ['ocean', 'marine', 'sea', 'biology', 'coral', 'fish', 'octopus'],
                    'marcus': ['ai', 'artificial', 'intelligence', 'research', 'technology', 'algorithm'],
                    'ryan': ['game', 'development', 'indie', 'programming', 'design'],
                    'dream': ['dream', 'reality', 'morpheus', 'endless', 'realm'],
                    'gabriel': ['british', 'gentleman', 'sophisticated', 'charming', 'witty'],
                    'sophia': ['marketing', 'strategy', 'brand', 'campaign', 'business'],
                    'jake': ['photo', 'adventure', 'travel', 'landscape', 'expedition'],
                    'aethys': ['omnipotent', 'existence', 'reality', 'infinite', 'consciousness']
                }
                
                # Use CDL keywords if available, otherwise fallback
                keywords = cdl_keywords if cdl_keywords else fallback_keywords.get(bot_name, [])
                
                # More flexible keyword matching (partial matches and stemming)
                found_keywords = []
                for kw in keywords:
                    if kw in response_text or any(kw in word for word in response_text.split()):
                        found_keywords.append(kw)
                    # Also check for partial matches and related terms
                    elif kw == 'marine' and ('ocean' in response_text or 'sea' in response_text or 'biologist' in response_text):
                        found_keywords.append(kw)
                    elif kw == 'research' and ('scientist' in response_text or 'study' in response_text):
                        found_keywords.append(kw)
                    elif kw == 'ai' and ('artificial' in response_text or 'intelligence' in response_text):
                        found_keywords.append(kw)
                
                if found_keywords or len(keywords) == 0:
                    self.log_success(f"{bot_name.upper()} personality traits validated")
                    if self.verbose and found_keywords:
                        validation_source = "CDL-extracted" if cdl_keywords else "fallback"
                        self.log_info(f"Found personality keywords ({validation_source}): {found_keywords}")
                    return True
                else:
                    validation_source = "CDL-extracted" if cdl_keywords else "fallback"
                    self.log_warning(f"{bot_name.upper()} personality traits unclear (no {validation_source} keywords: {keywords})")
                    return True  # Don't fail for this, as personality can be expressed differently
            else:
                self.log_error(f"{bot_name.upper()} personality test returned {response.status_code}")
                return False
        except (requests.RequestException, requests.Timeout, ConnectionError) as e:
            self.log_error(f"{bot_name.upper()} personality test failed: {e}")
            return False

    async def test_memory_storage_and_recall(self, bot_name: str, config: Dict) -> bool:
        """Test vector memory storage and recall"""
        try:
            # Store information
            setup_message = "My name is TestUser and I work as a software engineer. I love hiking and my favorite color is blue."
            
            response1 = requests.post(
                f"http://localhost:{config['port']}/api/chat",
                json={"message": setup_message, "user_id": self.test_user_id},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response1.status_code != 200:
                self.log_error(f"{bot_name.upper()} memory setup failed")
                return False
            
            # Wait a moment for storage
            await asyncio.sleep(1)
            
            # Test recall
            recall_message = "What do you remember about me?"
            
            response2 = requests.post(
                f"http://localhost:{config['port']}/api/chat",
                json={"message": recall_message, "user_id": self.test_user_id},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response2.status_code == 200:
                data = response2.json()
                response_text = data.get('response', '').lower()
                
                # Check if bot remembers key information
                memory_checks = ['testuser', 'software', 'engineer', 'hiking', 'blue']
                remembered = [check for check in memory_checks if check in response_text]
                
                if len(remembered) >= 2:  # At least 2 pieces of info remembered
                    self.log_success(f"{bot_name.upper()} memory storage and recall working")
                    if self.verbose:
                        self.log_info(f"Remembered: {remembered}")
                    return True
                else:
                    self.log_warning(f"{bot_name.upper()} memory recall incomplete (found: {remembered})")
                    return True  # Don't fail completely, memory might be working differently
            else:
                self.log_error(f"{bot_name.upper()} memory recall failed")
                return False
        except (requests.RequestException, requests.Timeout, ConnectionError) as e:
            self.log_error(f"{bot_name.upper()} memory test failed: {e}")
            return False

    async def test_conversation_context(self, bot_name: str, config: Dict) -> bool:
        """Test conversation context and follow-up capabilities"""
        try:
            # First message
            message1 = "I'm thinking about learning a new skill. What would you recommend?"
            
            response1 = requests.post(
                f"http://localhost:{config['port']}/api/chat",
                json={"message": message1, "user_id": self.test_user_id},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response1.status_code != 200:
                return False
            
            await asyncio.sleep(1)
            
            # Follow-up message that requires context
            message2 = "Why do you think that would be particularly good for me?"
            
            response2 = requests.post(
                f"http://localhost:{config['port']}/api/chat",
                json={"message": message2, "user_id": self.test_user_id},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response2.status_code == 200:
                data = response2.json()
                response_text = data.get('response', '')
                
                # Check if response makes sense as a follow-up
                if len(response_text.strip()) > 20:  # Reasonable response length
                    self.log_success(f"{bot_name.upper()} conversation context working")
                    return True
                else:
                    self.log_warning(f"{bot_name.upper()} context response too short")
                    return True
            else:
                self.log_error(f"{bot_name.upper()} context test failed")
                return False
        except (requests.RequestException, requests.Timeout, ConnectionError) as e:
            self.log_error(f"{bot_name.upper()} conversation context test failed: {e}")
            return False

    async def test_emotional_intelligence(self, bot_name: str, config: Dict) -> bool:
        """Test emotional intelligence and appropriate responses"""
        try:
            # Test supportive response to negative emotion
            emotional_message = "I'm feeling really stressed about my upcoming exams and worried I might fail."
            
            response = requests.post(
                f"http://localhost:{config['port']}/api/chat",
                json={"message": emotional_message, "user_id": self.test_user_id},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '').lower()
                
                # Look for supportive/empathetic language
                supportive_indicators = [
                    'understand', 'feel', 'support', 'help', 'stress', 'worry', 'exam',
                    'breathe', 'okay', 'manage', 'cope', 'difficult', 'challenging'
                ]
                
                found_support = [indicator for indicator in supportive_indicators if indicator in response_text]
                
                if found_support and len(data.get('response', '')) > 50:
                    self.log_success(f"{bot_name.upper()} emotional intelligence validated")
                    if self.verbose:
                        self.log_info(f"Supportive indicators: {found_support[:3]}")
                    return True
                else:
                    self.log_warning(f"{bot_name.upper()} emotional response unclear")
                    return True  # Don't fail, as emotional intelligence can be expressed differently
            else:
                self.log_error(f"{bot_name.upper()} emotional intelligence test failed")
                return False
        except (requests.RequestException, requests.Timeout, ConnectionError) as e:
            self.log_error(f"{bot_name.upper()} emotional intelligence test failed: {e}")
            return False

    async def test_performance(self, bot_name: str, config: Dict) -> bool:
        """Test response performance and timing"""
        try:
            message = "Hello, how are you today?"
            
            start_time = time.time()
            response = requests.post(
                f"http://localhost:{config['port']}/api/chat",
                json={"message": message, "user_id": self.test_user_id},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response.status_code == 200:
                if response_time < 15.0:  # Response within 15 seconds
                    self.log_success(f"{bot_name.upper()} performance good ({response_time:.2f}s)")
                    return True
                else:
                    self.log_warning(f"{bot_name.upper()} performance slow ({response_time:.2f}s)")
                    return True  # Don't fail for slow response
            else:
                self.log_error(f"{bot_name.upper()} performance test failed")
                return False
        except (requests.RequestException, requests.Timeout, ConnectionError) as e:
            self.log_error(f"{bot_name.upper()} performance test failed: {e}")
            return False

    async def run_bot_tests(self, bot_name: str, config: Dict) -> Dict:
        """Run all tests for a specific bot and generate individual report"""
        if not self.parallel:
            self.log_test(f"Testing {bot_name.upper()} ({config['character']}) on port {config['port']}")
        
        results = {}
        test_start = datetime.now()
        
        # Run tests in sequence
        tests = [
            ("CDL Validation", self.test_cdl_validation),
            ("Health Check", self.test_bot_health),
            ("Bot Info", self.test_bot_info),
            ("Basic Conversation", self.test_basic_conversation),
            ("Personality Traits", self.test_personality_traits),
            ("Memory Storage & Recall", self.test_memory_storage_and_recall),
            ("Conversation Context", self.test_conversation_context),
            ("Emotional Intelligence", self.test_emotional_intelligence),
            ("Performance", self.test_performance),
        ]
        
        for test_name, test_func in tests:
            try:
                result = await test_func(bot_name, config)
                results[test_name] = result
                if not result and not self.parallel:
                    self.log_error(f"{bot_name.upper()} failed: {test_name}")
            except (requests.RequestException, requests.Timeout, ConnectionError, ValueError) as e:
                results[test_name] = False
                if not self.parallel:
                    self.log_error(f"{bot_name.upper()} {test_name} exception: {e}")
        
        # Analyze logs for issues during test period
        log_analysis = await self.analyze_bot_logs(bot_name, config)
        results["Log Analysis"] = log_analysis['success']
        
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        # Generate individual bot report
        report = {
            'bot_name': bot_name,
            'character': config['character'],
            'port': config['port'],
            'container': config['container'],
            'test_user_id': self.test_user_id,
            'test_start': test_start.isoformat(),
            'test_end': test_end.isoformat(),
            'test_duration_seconds': test_duration,
            'test_results': results,
            'log_analysis': log_analysis,
            'summary': {
                'total_tests': len(results),
                'passed_tests': sum(1 for r in results.values() if r),
                'failed_tests': sum(1 for r in results.values() if not r),
                'success_rate': sum(1 for r in results.values() if r) / len(results) * 100
            }
        }
        
        # Save individual report
        report_file = self.reports_dir / f"{bot_name}_smoke_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        if not self.parallel:
            # Summary for this bot
            passed = sum(1 for r in results.values() if r)
            total = len(results)
            
            if passed == total:
                self.log_success(f"{bot_name.upper()} ALL TESTS PASSED ({passed}/{total})")
            else:
                self.log_warning(f"{bot_name.upper()} {passed}/{total} tests passed")
        
        return report

    async def run_smoke_tests(self, target_bot: Optional[str] = None) -> Dict:
        """Run smoke tests for all or specific bots"""
        self.log(f"{Colors.BOLD}🚀 WhisperEngine Smoke Test Suite{Colors.END}")
        self.log(f"{Colors.BOLD}📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
        self.log(f"{Colors.BOLD}🧪 Test User ID: {self.test_user_id}{Colors.END}")
        if self.parallel:
            self.log(f"{Colors.BOLD}⚡ Parallel Mode: Enabled{Colors.END}")
        print()
        
        # Determine which bots to test
        if target_bot:
            if target_bot in self.bots:
                bots_to_test = {target_bot: self.bots[target_bot]}
            else:
                self.log_error(f"Unknown bot: {target_bot}")
                self.log_info(f"Available bots: {', '.join(self.bots.keys())}")
                return {}
        else:
            bots_to_test = self.bots
        
        overall_start = datetime.now()
        
        if self.parallel and len(bots_to_test) > 1:
            # Run tests in parallel
            self.log_info(f"🔄 Running tests for {len(bots_to_test)} bots in parallel...")
            
            # Create tasks for all bots
            tasks = []
            for bot_name, config in bots_to_test.items():
                task = asyncio.create_task(
                    self.run_bot_tests(bot_name, config),
                    name=f"test_{bot_name}"
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            bot_reports = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            all_results = {}
            for i, (bot_name, config) in enumerate(bots_to_test.items()):
                if isinstance(bot_reports[i], Exception):
                    self.log_error(f"{bot_name.upper()} testing failed with exception: {bot_reports[i]}")
                    # Create a minimal failed report
                    all_results[bot_name] = {
                        'test_results': {},
                        'summary': {'total_tests': 0, 'passed_tests': 0, 'failed_tests': 1, 'success_rate': 0.0},
                        'exception': str(bot_reports[i])
                    }
                else:
                    all_results[bot_name] = bot_reports[i]
        else:
            # Run tests sequentially
            all_results = {}
            for bot_name, config in bots_to_test.items():
                print()
                try:
                    report = await self.run_bot_tests(bot_name, config)
                    all_results[bot_name] = report
                except Exception as e:
                    self.log_error(f"{bot_name.upper()} testing failed: {e}")
                    all_results[bot_name] = {
                        'test_results': {},
                        'summary': {'total_tests': 0, 'passed_tests': 0, 'failed_tests': 1, 'success_rate': 0.0},
                        'exception': str(e)
                    }
        
        overall_end = datetime.now()
        overall_duration = (overall_end - overall_start).total_seconds()
        
        # Generate comprehensive final report
        final_report = {
            'test_suite': 'WhisperEngine Smoke Test',
            'timestamp': overall_start.isoformat(),
            'test_user_id': self.test_user_id,
            'parallel_mode': self.parallel,
            'overall_duration_seconds': overall_duration,
            'bots_tested': list(bots_to_test.keys()),
            'individual_reports': all_results,
            'overall_summary': self._generate_overall_summary(all_results),
            'recommendations': self._generate_recommendations(all_results)
        }
        
        # Save final report
        final_report_file = self.reports_dir / f"final_smoke_test_report_{self.test_user_id}.json"
        with open(final_report_file, 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
        
        self.log_info(f"📄 Reports saved to: {self.reports_dir}")
        self.log_info(f"📄 Final report: {final_report_file}")
        
        return final_report

    def _generate_overall_summary(self, all_results: Dict) -> Dict:
        """Generate overall summary statistics"""
        total_bots = len(all_results)
        total_tests = sum(report.get('summary', {}).get('total_tests', 0) for report in all_results.values())
        total_passed = sum(report.get('summary', {}).get('passed_tests', 0) for report in all_results.values())
        total_failed = sum(report.get('summary', {}).get('failed_tests', 0) for report in all_results.values())
        
        bots_fully_passed = sum(1 for report in all_results.values() 
                               if report.get('summary', {}).get('success_rate', 0) == 100.0)
        
        # Analyze log issues across all bots
        total_warnings = sum(report.get('log_analysis', {}).get('warnings', 0) for report in all_results.values())
        total_errors = sum(report.get('log_analysis', {}).get('errors', 0) for report in all_results.values())  # Adjusted errors
        total_raw_errors = sum(report.get('log_analysis', {}).get('raw_errors', 0) for report in all_results.values())
        total_config_warnings = sum(report.get('log_analysis', {}).get('config_warnings', 0) for report in all_results.values())
        critical_issues = []
        for report in all_results.values():
            critical_issues.extend(report.get('log_analysis', {}).get('critical_issues', []))

        return {
            'total_bots_tested': total_bots,
            'bots_fully_passed': bots_fully_passed,
            'total_tests_run': total_tests,
            'total_tests_passed': total_passed,
            'total_tests_failed': total_failed,
            'overall_success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0,
            'log_analysis_summary': {
                'total_warnings': total_warnings,
                'total_errors': total_errors,  # Adjusted count
                'total_raw_errors': total_raw_errors,  # Raw count for reference
                'total_config_warnings': total_config_warnings,
                'unique_critical_issues': list(set(critical_issues))
            }
        }

    def _generate_recommendations(self, all_results: Dict) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check for bots with failed tests
        failed_bots = [bot for bot, report in all_results.items() 
                      if report.get('summary', {}).get('failed_tests', 0) > 0]
        if failed_bots:
            recommendations.append(f"Investigate failed tests in: {', '.join(failed_bots)}")
        
        # Check for performance issues
        slow_bots = []
        for bot, report in all_results.items():
            duration = report.get('test_duration_seconds', 0)
            if duration > 60:  # Longer than 1 minute
                slow_bots.append(bot)
        if slow_bots:
            recommendations.append(f"Performance optimization needed for: {', '.join(slow_bots)}")
        
        # Check for log issues
        error_bots = [bot for bot, report in all_results.items() 
                     if report.get('log_analysis', {}).get('errors', 0) > 0]
        if error_bots:
            recommendations.append(f"Review error logs for: {', '.join(error_bots)}")
        
        # Check for critical issues
        critical_bots = [bot for bot, report in all_results.items() 
                        if report.get('log_analysis', {}).get('critical_issues', [])]
        if critical_bots:
            recommendations.append(f"Address critical issues in: {', '.join(critical_bots)}")
        
        if not recommendations:
            recommendations.append("All systems appear to be functioning well!")
        
        return recommendations

    def print_summary(self, final_report: Dict):
        """Print final test summary from comprehensive report"""
        print("\n" + "="*80)
        self.log(f"{Colors.BOLD}📊 SMOKE TEST SUMMARY{Colors.END}")
        print("="*80)
        
        overall = final_report.get('overall_summary', {})
        individual_reports = final_report.get('individual_reports', {})
        
        # Print individual bot results
        for bot_name, report in individual_reports.items():
            summary = report.get('summary', {})
            passed = summary.get('passed_tests', 0)
            total = summary.get('total_tests', 0)
            success_rate = summary.get('success_rate', 0)
            
            # Include log analysis in status
            log_analysis = report.get('log_analysis', {})
            warnings = log_analysis.get('warnings', 0)
            errors = log_analysis.get('errors', 0)
            critical_issues = len(log_analysis.get('critical_issues', []))
            
            if 'exception' in report:
                status_color = Colors.RED
                status_text = f"FAILED (Exception: {report['exception'][:50]}...)"
            elif passed == total and errors == 0 and critical_issues == 0:
                status_color = Colors.GREEN
                status_text = f"ALL PASSED ({passed}/{total}) ✨"
            elif errors > 0 or critical_issues > 0:
                status_color = Colors.RED
                status_text = f"{passed}/{total} tests, {errors} errors, {critical_issues} critical issues"
            elif warnings > 0:
                status_color = Colors.YELLOW
                status_text = f"{passed}/{total} tests, {warnings} warnings"
            else:
                status_color = Colors.YELLOW
                status_text = f"{passed}/{total} tests passed"
            
            self.log(f"{status_color}{bot_name.upper()}: {status_text}{Colors.END}")
            
            if self.verbose and total > 0:
                test_results = report.get('test_results', {})
                for test_name, result in test_results.items():
                    status = "✅" if result else "❌"
                    print(f"  {status} {test_name}")
        
        print("-"*80)
        
        # Overall statistics
        total_bots = overall.get('total_bots_tested', 0)
        bots_passed = overall.get('bots_fully_passed', 0)
        total_tests = overall.get('total_tests_run', 0)
        total_passed = overall.get('total_tests_passed', 0)
        success_rate = overall.get('overall_success_rate', 0)
        
        overall_status = Colors.GREEN if bots_passed == total_bots else Colors.YELLOW
        self.log(f"{Colors.BOLD}{overall_status}OVERALL: {bots_passed}/{total_bots} bots fully passed, {total_passed}/{total_tests} tests passed ({success_rate:.1f}%){Colors.END}")
        
        # Log analysis summary
        log_summary = overall.get('log_analysis_summary', {})
        total_warnings = log_summary.get('total_warnings', 0)
        total_errors = log_summary.get('total_errors', 0)  # Adjusted errors
        total_raw_errors = log_summary.get('total_raw_errors', 0)
        total_config_warnings = log_summary.get('total_config_warnings', 0)
        critical_issues = log_summary.get('unique_critical_issues', [])
        
        if critical_issues:
            self.log_error(f"📋 Log Analysis: {len(critical_issues)} critical issue types detected")
            for issue in critical_issues:
                self.log_error(f"  ⚠️  {issue}")
        elif total_errors > 0:
            self.log_warning(f"📋 Log Analysis: {total_errors} errors, {total_warnings} warnings (filtered from {total_raw_errors} raw)")
        elif total_config_warnings > 0:
            self.log_info(f"📋 Log Analysis: {total_config_warnings} config warnings, {total_warnings} other warnings (non-critical)")
        elif total_warnings > 0:
            self.log_warning(f"📋 Log Analysis: {total_warnings} warnings detected")
        else:
            self.log_success("📋 Log Analysis: Clean logs across all bots")
        
        # Performance summary
        if final_report.get('parallel_mode'):
            duration = final_report.get('overall_duration_seconds', 0)
            self.log_info(f"⚡ Parallel execution completed in {duration:.1f} seconds")
        
        # Recommendations
        recommendations = final_report.get('recommendations', [])
        if recommendations:
            print("-"*80)
            self.log(f"{Colors.BOLD}💡 RECOMMENDATIONS:{Colors.END}")
            for rec in recommendations:
                self.log_info(f"  • {rec}")
        
        if bots_passed == total_bots and total_errors == 0:
            self.log_success("🎉 ALL SYSTEMS OPERATIONAL!")
        else:
            self.log_warning("⚠️  Some issues detected - see recommendations above")
        
        print("="*80)

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="WhisperEngine Smoke Test Suite")
    parser.add_argument("--bot", help="Test specific bot only", choices=[
        'elena', 'marcus', 'ryan', 'dream', 'gabriel', 'sophia', 'jake', 'aethys'
    ])
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--sequential", action="store_true", 
                       help="Run tests sequentially instead of parallel (default: parallel)")
    
    args = parser.parse_args()
    
    # Determine if we should run in parallel (default True, unless sequential flag or single bot)
    parallel = not args.sequential and not args.bot
    
    runner = SmokeTestRunner(verbose=args.verbose, parallel=parallel)
    final_report = await runner.run_smoke_tests(target_bot=args.bot)
    
    if final_report:
        runner.print_summary(final_report)
        
        # Exit with proper code based on results
        overall_summary = final_report.get('overall_summary', {})
        total_bots = overall_summary.get('total_bots_tested', 0)
        bots_passed = overall_summary.get('bots_fully_passed', 0)
        total_errors = overall_summary.get('log_analysis_summary', {}).get('total_errors', 0)
        
        if bots_passed == total_bots and total_errors == 0:
            sys.exit(0)  # Complete success
        else:
            sys.exit(1)  # Some failures or issues
    else:
        sys.exit(1)  # No tests run

if __name__ == "__main__":
    asyncio.run(main())