import asyncio
from src.characters.cdl.parser import load_character
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration

async def test_enhanced_context():
    character = load_character('characters/examples/sophia_v2.json')
    cdl_integration = CDLAIPromptIntegration()
    
    # Test enhanced career extraction
    career_msg = 'Tell me about your work and career background'
    career_sections = await cdl_integration._extract_cdl_personal_knowledge_sections(character, career_msg)
    print('=== ENHANCED CAREER EXTRACTION ===')
    print(f'Message: {career_msg}')
    print(f'Extracted: {career_sections}')
    
    # Test hobbies extraction
    hobby_msg = 'What do you like to do for fun in your free time?'
    hobby_sections = await cdl_integration._extract_cdl_personal_knowledge_sections(character, hobby_msg)
    print(f'\n=== HOBBIES EXTRACTION ===')
    print(f'Message: {hobby_msg}')
    print(f'Extracted: {hobby_sections}')
    
    # Test no match
    general_msg = 'Hello, how are you?'
    general_sections = await cdl_integration._extract_cdl_personal_knowledge_sections(character, general_msg)
    print(f'\n=== GENERAL CONVERSATION ===')
    print(f'Message: {general_msg}')
    extracted_text = general_sections if general_sections else "No personal context (efficient!)"
    print(f'Extracted: {extracted_text}')

asyncio.run(test_enhanced_context())