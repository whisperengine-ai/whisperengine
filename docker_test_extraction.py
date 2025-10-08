#!/usr/bin/env python3
"""Test personal knowledge extraction in Docker with real database"""
import os
import sys

os.environ['DISCORD_BOT_NAME'] = os.getenv('BOT_NAME', 'aetheris')
os.environ['BOT_NAME'] = os.getenv('BOT_NAME', 'aetheris')

from src.characters.cdl.simple_cdl_manager import get_simple_cdl_manager

def extract_personal_knowledge(character, message_content):
    """Extract personal knowledge based on query keywords"""
    personal_sections = []
    message_lower = message_content.lower()
    
    # Relationship extraction
    if any(keyword in message_lower for keyword in ['relationship', 'partner', 'dating', 'married']):
        if hasattr(character, 'relationships') and character.relationships:
            rel_info = character.relationships
            if hasattr(rel_info, 'status') and rel_info.status:
                personal_sections.append(f'Relationship Status: {rel_info.status}')
            if hasattr(rel_info, 'important_relationships') and rel_info.important_relationships:
                personal_sections.append(f'Key Relationships: {", ".join(rel_info.important_relationships[:3])}')
    
    # Career/work extraction
    if any(keyword in message_lower for keyword in ['work', 'job', 'career', 'education', 'professional']):
        if hasattr(character, 'skills_and_expertise') and character.skills_and_expertise:
            skills = character.skills_and_expertise
            if hasattr(skills, 'professional_skills') and skills.professional_skills:
                personal_sections.append(f'Professional Skills: {skills.professional_skills}')
        if hasattr(character, 'backstory') and character.backstory:
            backstory = character.backstory
            if hasattr(backstory, 'career_background') and backstory.career_background:
                # Truncate to 200 chars for display
                career = backstory.career_background[:200]
                personal_sections.append(f'Career Background: {career}...')
    
    return '\n'.join(personal_sections) if personal_sections else ''

print('='*80)
print('Personal Knowledge Extraction Test with Real Database')
print('='*80)

cdl_manager = get_simple_cdl_manager()
character = cdl_manager.get_character_object()

print(f'\nCharacter: {character.identity.name}')
print(f'Occupation: {character.identity.occupation}')

# Test queries
queries = [
    'Tell me about your relationship status',
    'Do you have a partner?',
    'What is your career background?',
    'Tell me about your professional work'
]

success_count = 0
for query in queries:
    print(f'\n{"─"*80}')
    print(f'Query: "{query}"')
    extraction = extract_personal_knowledge(character, query)
    
    if extraction:
        print(f'✅ EXTRACTED ({len(extraction)} chars):')
        for line in extraction.split('\n'):
            print(f'   {line}')
        success_count += 1
    else:
        print('⚠️  NO DATA EXTRACTED')

print(f'\n{"="*80}')
print(f'Success Rate: {success_count}/{len(queries)} queries returned data')
print('='*80)
