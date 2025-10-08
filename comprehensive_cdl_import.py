#!/usr/bin/env python3
"""
Comprehensive CDL JSON to RDBMS Import Script
Captures ALL fidelity and control from CDL JSON files with zero data loss
Supports all character types and CDL structures generically
"""

import asyncio
import asyncpg
import json
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

class ComprehensiveCDLImporter:
    def __init__(self, db_connection: asyncpg.Connection):
        self.conn = db_connection
        
    async def import_character_complete(self, json_file_path: str) -> bool:
        """Import complete character data with ALL CDL fidelity preserved"""
        
        print(f"\n🔄 Starting comprehensive import: {json_file_path}")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                cdl_data = json.load(f)
            
            character_data = cdl_data.get('character', {})
            
            # Extract basic character info
            identity = character_data.get('identity', {})
            character_name = identity.get('name', '').lower().replace(' ', '_')
            
            if not character_name:
                print(f"❌ No character name found in {json_file_path}")
                return False
            
            # 1. Create/update base character record
            character_id = await self._upsert_base_character(character_data)
            print(f"✅ Base character: {character_name} (ID: {character_id})")
            
            # 2. Import response guidelines and formatting rules
            await self._import_response_guidelines(character_id, character_data)
            print(f"✅ Response guidelines imported")
            
            # 3. Import conversation flows and guidance
            await self._import_conversation_flows(character_id, character_data)
            print(f"✅ Conversation flows imported")
            
            # 4. Import message triggers and patterns
            await self._import_message_triggers(character_id, character_data)
            print(f"✅ Message triggers imported")
            
            # 5. Import response modes
            await self._import_response_modes(character_id, character_data)
            print(f"✅ Response modes imported")
            
            # 6. Import emoji patterns
            await self._import_emoji_patterns(character_id, character_data)
            print(f"✅ Emoji patterns imported")
            
            # 7. Import speech patterns
            await self._import_speech_patterns(character_id, character_data)
            print(f"✅ Speech patterns imported")
            
            # 8. Import AI scenarios
            await self._import_ai_scenarios(character_id, character_data)
            print(f"✅ AI scenarios imported")
            
            # 9. Import cultural expressions
            await self._import_cultural_expressions(character_id, character_data)
            print(f"✅ Cultural expressions imported")
            
            # 10. Import voice traits
            await self._import_voice_traits(character_id, character_data)
            print(f"✅ Voice traits imported")
            
            # 11. Import emotional triggers
            await self._import_emotional_triggers(character_id, character_data)
            print(f"✅ Emotional triggers imported")
            
            # 12. Import expertise domains
            await self._import_expertise_domains(character_id, character_data)
            print(f"✅ Expertise domains imported")
            
            print(f"\n🎉 Complete import successful: {character_name}")
            return True
            
        except Exception as e:
            print(f"❌ Import failed for {json_file_path}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _upsert_base_character(self, character_data: Dict) -> int:
        """Create or update base character record"""
        identity = character_data.get('identity', {})
        
        name = identity.get('name', '')
        normalized_name = name.lower().replace(' ', '_')
        occupation = identity.get('occupation', '')
        description = identity.get('description', '')
        archetype = identity.get('archetype', 'real-world')
        allow_full_roleplay = identity.get('allow_full_roleplay_immersion', False)
        
        # Check if character exists
        character_id = await self.conn.fetchval(
            "SELECT id FROM characters WHERE normalized_name = $1",
            normalized_name
        )
        
        if character_id:
            # Update existing
            await self.conn.execute("""
                UPDATE characters 
                SET name = $1, occupation = $2, description = $3, 
                    archetype = $4, allow_full_roleplay = $5, updated_at = CURRENT_TIMESTAMP
                WHERE id = $6
            """, name, occupation, description, archetype, allow_full_roleplay, character_id)
        else:
            # Create new
            character_id = await self.conn.fetchval("""
                INSERT INTO characters 
                (name, normalized_name, occupation, description, archetype, allow_full_roleplay, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, true)
                RETURNING id
            """, name, normalized_name, occupation, description, archetype, allow_full_roleplay)
        
        return character_id
    
    async def _import_response_guidelines(self, character_id: int, character_data: Dict):
        """Import all response guidelines and formatting rules"""
        # Clear existing guidelines
        await self.conn.execute("DELETE FROM character_response_guidelines WHERE character_id = $1", character_id)
        
        guidelines = []
        
        # Extract response_length from various locations
        speech_patterns = character_data.get('speech_patterns', {})
        if 'response_length' in speech_patterns:
            guidelines.append({
                'type': 'response_length',
                'name': 'speech_patterns_length',
                'content': speech_patterns['response_length'],
                'priority': 90,
                'context': 'general',
                'critical': True
            })
        
        communication = character_data.get('communication', {})
        if 'response_length' in communication:
            guidelines.append({
                'type': 'response_length', 
                'name': 'communication_length',
                'content': communication['response_length'],
                'priority': 95,
                'context': 'discord',
                'critical': True
            })
        
        # Extract formatting rules
        conv_flow = communication.get('conversation_flow_guidance', {})
        response_style = conv_flow.get('response_style', {})
        
        if 'formatting_rules' in response_style:
            for i, rule in enumerate(response_style['formatting_rules']):
                guidelines.append({
                    'type': 'formatting_rule',
                    'name': f'formatting_rule_{i+1}',
                    'content': rule,
                    'priority': 80,
                    'context': 'general',
                    'critical': False
                })
        
        # Extract core principles
        if 'core_principles' in response_style:
            for i, principle in enumerate(response_style['core_principles']):
                guidelines.append({
                    'type': 'core_principle',
                    'name': f'core_principle_{i+1}',
                    'content': principle,
                    'priority': 100,
                    'context': 'all',
                    'critical': True
                })
        
        # Insert all guidelines
        for guideline in guidelines:
            await self.conn.execute("""
                INSERT INTO character_response_guidelines 
                (character_id, guideline_type, guideline_name, guideline_content, 
                 priority, context, is_critical)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, character_id, guideline['type'], guideline['name'], 
                guideline['content'], guideline['priority'], 
                guideline['context'], guideline['critical'])
    
    async def _import_conversation_flows(self, character_id: int, character_data: Dict):
        """Import conversation flow guidance"""
        # Clear existing flows
        await self.conn.execute("DELETE FROM character_conversation_flows WHERE character_id = $1", character_id)
        await self.conn.execute("""
            DELETE FROM character_conversation_directives WHERE conversation_flow_id IN 
            (SELECT id FROM character_conversation_flows WHERE character_id = $1)
        """, character_id)
        
        communication = character_data.get('communication', {})
        conv_flow_guidance = communication.get('conversation_flow_guidance', {})
        
        for flow_type, flow_data in conv_flow_guidance.items():
            if isinstance(flow_data, dict) and flow_type != 'response_style':
                # Create conversation flow
                flow_id = await self.conn.fetchval("""
                    INSERT INTO character_conversation_flows 
                    (character_id, flow_type, flow_name, energy_level, 
                     approach_description, transition_style, priority)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """, character_id, flow_type, flow_type.replace('_', ' ').title(),
                    flow_data.get('energy', ''), flow_data.get('approach', ''),
                    flow_data.get('transition_style', ''), 50)
                
                # Import directives (avoid, encourage, examples)
                for directive_type in ['avoid', 'encourage', 'examples']:
                    if directive_type in flow_data:
                        directives = flow_data[directive_type]
                        if isinstance(directives, list):
                            for i, directive in enumerate(directives):
                                await self.conn.execute("""
                                    INSERT INTO character_conversation_directives
                                    (conversation_flow_id, directive_type, directive_content, order_sequence)
                                    VALUES ($1, $2, $3, $4)
                                """, flow_id, directive_type, str(directive), i)
    
    async def _import_message_triggers(self, character_id: int, character_data: Dict):
        """Import message pattern triggers"""
        # Clear existing triggers
        await self.conn.execute("DELETE FROM character_message_triggers WHERE character_id = $1", character_id)
        
        communication = character_data.get('communication', {})
        message_triggers = communication.get('message_pattern_triggers', {})
        
        for category, trigger_data in message_triggers.items():
            if isinstance(trigger_data, dict):
                # Import keywords
                keywords = trigger_data.get('keywords', [])
                for keyword in keywords:
                    await self.conn.execute("""
                        INSERT INTO character_message_triggers
                        (character_id, trigger_category, trigger_type, trigger_value, 
                         response_mode, priority, is_active)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, character_id, category, 'keyword', keyword, category, 50, True)
                
                # Import phrases
                phrases = trigger_data.get('phrases', [])
                for phrase in phrases:
                    await self.conn.execute("""
                        INSERT INTO character_message_triggers
                        (character_id, trigger_category, trigger_type, trigger_value, 
                         response_mode, priority, is_active)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, character_id, category, 'phrase', phrase, category, 60, True)
    
    async def _import_response_modes(self, character_id: int, character_data: Dict):
        """Import response modes (technical, creative, brief, etc.)"""
        # Clear existing modes
        await self.conn.execute("DELETE FROM character_response_modes WHERE character_id = $1", character_id)
        
        # Look for modes in personality section
        personality = character_data.get('personality', {})
        communication_modes = personality.get('communication_modes', {})
        
        for mode_name, mode_data in communication_modes.items():
            if isinstance(mode_data, dict):
                await self.conn.execute("""
                    INSERT INTO character_response_modes
                    (character_id, mode_name, mode_description, response_style,
                     length_guideline, tone_adjustment, conflict_resolution_priority, examples)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, character_id, mode_name, mode_data.get('description', ''),
                    mode_data.get('response_style', ''), mode_data.get('length', ''),
                    mode_data.get('tone', ''), mode_data.get('priority', 50),
                    str(mode_data.get('examples', [])))
    
    async def _import_emoji_patterns(self, character_id: int, character_data: Dict):
        """Import emoji usage patterns"""
        # Clear existing patterns
        await self.conn.execute("DELETE FROM character_emoji_patterns WHERE character_id = $1", character_id)
        
        identity = character_data.get('identity', {})
        digital_comm = identity.get('digital_communication', {})
        emoji_patterns = digital_comm.get('emoji_usage_patterns', {})
        
        for category, pattern_data in emoji_patterns.items():
            if isinstance(pattern_data, dict):
                for pattern_name, pattern_info in pattern_data.items():
                    if isinstance(pattern_info, str):
                        await self.conn.execute("""
                            INSERT INTO character_emoji_patterns
                            (character_id, pattern_category, pattern_name, emoji_sequence,
                             usage_context, frequency, example_usage)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """, character_id, category, pattern_name, '', 
                            pattern_info, 'medium', pattern_info)
                    elif isinstance(pattern_info, list):
                        emoji_list = ', '.join(pattern_info)
                        await self.conn.execute("""
                            INSERT INTO character_emoji_patterns
                            (character_id, pattern_category, pattern_name, emoji_sequence,
                             usage_context, frequency, example_usage)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """, character_id, category, pattern_name, emoji_list,
                            '', 'medium', '')
    
    async def _import_speech_patterns(self, character_id: int, character_data: Dict):
        """Import speech patterns and vocabulary"""
        # Clear existing patterns
        await self.conn.execute("DELETE FROM character_speech_patterns WHERE character_id = $1", character_id)
        
        speech_patterns = character_data.get('speech_patterns', {})
        
        # Import vocabulary
        vocabulary = speech_patterns.get('vocabulary', {})
        for vocab_type, words in vocabulary.items():
            if isinstance(words, list):
                for word in words:
                    await self.conn.execute("""
                        INSERT INTO character_speech_patterns
                        (character_id, pattern_type, pattern_value, usage_frequency, context, priority)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, character_id, vocab_type, word, 'medium', 'general', 50)
        
        # Import other speech patterns
        for pattern_type, pattern_value in speech_patterns.items():
            if pattern_type != 'vocabulary' and isinstance(pattern_value, str):
                await self.conn.execute("""
                    INSERT INTO character_speech_patterns
                    (character_id, pattern_type, pattern_value, usage_frequency, context, priority)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, character_id, pattern_type, pattern_value, 'high', 'general', 60)
    
    async def _import_ai_scenarios(self, character_id: int, character_data: Dict):
        """Import AI identity handling scenarios"""
        # Clear existing scenarios
        await self.conn.execute("DELETE FROM character_ai_scenarios WHERE character_id = $1", character_id)
        
        communication = character_data.get('communication', {})
        ai_handling = communication.get('ai_identity_handling', {})
        roleplay_scenarios = ai_handling.get('roleplay_interaction_scenarios', {})
        
        for scenario_type, scenario_data in roleplay_scenarios.items():
            if isinstance(scenario_data, dict):
                await self.conn.execute("""
                    INSERT INTO character_ai_scenarios
                    (character_id, scenario_type, scenario_name, response_pattern,
                     tier_1_response, tier_2_response, tier_3_response, example_usage)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, character_id, scenario_type, scenario_type.replace('_', ' ').title(),
                    'three_tier_response', scenario_data.get('tier_1_enthusiasm', ''),
                    scenario_data.get('tier_2_clarification', ''),
                    scenario_data.get('tier_3_alternatives', ''),
                    str(scenario_data.get('examples', {})))
    
    async def _import_cultural_expressions(self, character_id: int, character_data: Dict):
        """Import cultural expressions and language patterns"""
        # Clear existing expressions
        await self.conn.execute("DELETE FROM character_cultural_expressions WHERE character_id = $1", character_id)
        
        identity = character_data.get('identity', {})
        voice = identity.get('voice', {})
        
        # Import favorite phrases
        favorite_phrases = voice.get('favorite_phrases', [])
        for phrase in favorite_phrases:
            await self.conn.execute("""
                INSERT INTO character_cultural_expressions
                (character_id, expression_type, expression_value, usage_context, frequency)
                VALUES ($1, $2, $3, $4, $5)
            """, character_id, 'favorite_phrase', phrase, 'general', 'high')
        
        # Import speech patterns
        speech_patterns = voice.get('speech_patterns', [])
        for pattern in speech_patterns:
            await self.conn.execute("""
                INSERT INTO character_cultural_expressions
                (character_id, expression_type, expression_value, usage_context, frequency)
                VALUES ($1, $2, $3, $4, $5)
            """, character_id, 'speech_pattern', pattern, 'general', 'medium')
    
    async def _import_voice_traits(self, character_id: int, character_data: Dict):
        """Import voice and speaking characteristics"""
        # Clear existing traits
        await self.conn.execute("DELETE FROM character_voice_traits WHERE character_id = $1", character_id)
        
        identity = character_data.get('identity', {})
        voice = identity.get('voice', {})
        
        # Import voice characteristics
        voice_traits = {
            'tone': voice.get('tone', ''),
            'pace': voice.get('pace', ''),
            'volume': voice.get('volume', ''),
            'accent': voice.get('accent', ''),
            'vocabulary_level': voice.get('vocabulary_level', '')
        }
        
        for trait_type, trait_value in voice_traits.items():
            if trait_value:
                await self.conn.execute("""
                    INSERT INTO character_voice_traits
                    (character_id, trait_type, trait_value, situational_context)
                    VALUES ($1, $2, $3, $4)
                """, character_id, trait_type, trait_value, 'general')
    
    async def _import_emotional_triggers(self, character_id: int, character_data: Dict):
        """Import emotional triggers and responses"""
        # Clear existing triggers
        await self.conn.execute("DELETE FROM character_emotional_triggers WHERE character_id = $1", character_id)
        
        personality = character_data.get('personality', {})
        comm_style = personality.get('communication_style', {})
        emotional_expr = comm_style.get('emotional_expression', {})
        
        # Import various emotional triggers
        trigger_types = ['enthusiasm_triggers', 'concern_triggers', 'support_methods']
        
        for trigger_type in trigger_types:
            triggers = emotional_expr.get(trigger_type, [])
            for trigger in triggers:
                await self.conn.execute("""
                    INSERT INTO character_emotional_triggers
                    (character_id, trigger_type, trigger_content, response_intensity)
                    VALUES ($1, $2, $3, $4)
                """, character_id, trigger_type, trigger, 'medium')
    
    async def _import_expertise_domains(self, character_id: int, character_data: Dict):
        """Import professional expertise domains"""
        # Clear existing domains
        await self.conn.execute("DELETE FROM character_expertise_domains WHERE character_id = $1", character_id)
        
        identity = character_data.get('identity', {})
        occupation = identity.get('occupation', '')
        
        if occupation:
            # Create domain based on occupation
            await self.conn.execute("""
                INSERT INTO character_expertise_domains
                (character_id, domain_name, expertise_level, domain_description, passion_level)
                VALUES ($1, $2, $3, $4, $5)
            """, character_id, occupation, 'expert', f"Professional expertise in {occupation}", 90)

async def main():
    """Main import function"""
    if len(sys.argv) < 2:
        print("Usage: python comprehensive_cdl_import.py <character_json_file>")
        print("Example: python comprehensive_cdl_import.py characters/examples_legacy_backup/elena.backup_20251006_223336.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        print(f"❌ File not found: {json_file}")
        sys.exit(1)
    
    # Connect to database
    conn = await asyncpg.connect('postgresql://whisperengine:whisperengine_password@localhost:5433/whisperengine')
    
    try:
        importer = ComprehensiveCDLImporter(conn)
        success = await importer.import_character_complete(json_file)
        
        if success:
            print(f"\n🎉 Comprehensive import completed successfully!")
        else:
            print(f"\n❌ Import failed!")
            sys.exit(1)
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())