#!/usr/bin/env python3
"""
Validate that CDL prompt formatting is working correctly after fixes.
This script checks for raw dict dumps and validates proper formatting.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from characters.cdl.enhanced_cdl_manager import EnhancedCDLManager
from prompts.cdl_ai_integration import CDLAIPromptIntegration
from database.connection_pool import create_postgres_pool


async def validate_prompt_formatting(character_name: str = "elena"):
    """Validate that character prompt formatting is clean without raw dict dumps"""
    
    print(f"🔍 Validating prompt formatting for {character_name}...")
    
    # Setup database connection
    pool = await create_postgres_pool()
    
    try:
        # Load character data
        cdl_manager = EnhancedCDLManager(pool)
        character_data = await cdl_manager.load_character(character_name)
        
        if not character_data:
            print(f"❌ ERROR: Could not load character '{character_name}'")
            return False
        
        print(f"✅ Character data loaded successfully")
        
        # Create prompt integration
        cdl_integration = CDLAIPromptIntegration()
        
        # Build dynamic custom fields (this is where formatting happens)
        test_message = "What are your core values and beliefs about ocean conservation?"
        custom_fields = await cdl_integration._build_dynamic_custom_fields(
            character_data, 
            character_name,
            test_message
        )
        
        print(f"\n📊 Custom fields length: {len(custom_fields)} characters")
        
        # Check for problematic patterns
        issues_found = []
        
        # 1. Check for raw dict dumps with curly braces
        if "{'key':" in custom_fields or '{"key":' in custom_fields:
            issues_found.append("❌ FOUND: Raw dict dumps with 'key' field (values_and_beliefs issue)")
        
        if "{'period':" in custom_fields or '{"period":' in custom_fields:
            issues_found.append("❌ FOUND: Raw dict dumps with 'period' field (background issue)")
        
        if "{'category':" in custom_fields or '{"category":' in custom_fields:
            issues_found.append("❌ FOUND: Raw dict dumps with 'category' field (abilities/patterns issue)")
        
        # 2. Check for proper formatting patterns
        if "• " in custom_fields and "(Importance:" in custom_fields:
            print("✅ GOOD: Found properly formatted values with importance markers")
        
        if "📋" in custom_fields:
            print("✅ GOOD: Found section markers (📋)")
        
        # 3. Check for empty sections that should have been filtered
        if "VALUES AND BELIEFS:" in custom_fields:
            print("✅ GOOD: VALUES AND BELIEFS section included (contextual match)")
        
        if "BACKGROUND:" in custom_fields:
            # Check if it has actual content
            if "PhD in Marine Biology" in custom_fields or "Scripps Institution" in custom_fields:
                print("✅ GOOD: BACKGROUND section has actual content")
            else:
                issues_found.append("⚠️ WARNING: BACKGROUND section present but may be empty")
        
        # Display results
        print(f"\n{'='*60}")
        print(f"📋 VALIDATION RESULTS FOR {character_name.upper()}")
        print(f"{'='*60}")
        
        if issues_found:
            print(f"\n❌ ISSUES FOUND ({len(issues_found)}):")
            for issue in issues_found:
                print(f"  {issue}")
            print(f"\n🔧 Formatting fixes may not be applied correctly")
            return False
        else:
            print(f"\n✅ NO ISSUES FOUND - Prompt formatting is clean!")
            print(f"✅ All sections properly formatted")
            print(f"✅ No raw dict dumps detected")
            return True
        
    finally:
        await pool.close()


async def show_sample_sections(character_name: str = "elena"):
    """Show sample formatted sections for visual inspection"""
    
    print(f"\n{'='*60}")
    print(f"📝 SAMPLE FORMATTED SECTIONS")
    print(f"{'='*60}\n")
    
    pool = await create_postgres_pool()
    
    try:
        cdl_manager = EnhancedCDLManager(pool)
        character_data = await cdl_manager.load_character(character_name)
        
        if not character_data:
            return
        
        cdl_integration = CDLAIPromptIntegration()
        
        # Build custom fields with a message that triggers values section
        test_message = "What are your core values and beliefs?"
        custom_fields = await cdl_integration._build_dynamic_custom_fields(
            character_data, 
            character_name,
            test_message
        )
        
        # Extract and display first 1000 chars
        print("SAMPLE OUTPUT (first 1000 characters):")
        print("-" * 60)
        print(custom_fields[:1000])
        print("-" * 60)
        
        # Check for specific sections
        if "VALUES AND BELIEFS:" in custom_fields:
            start = custom_fields.find("VALUES AND BELIEFS:")
            end = start + 500
            print("\n📋 VALUES AND BELIEFS SECTION:")
            print("-" * 60)
            print(custom_fields[start:end])
            print("-" * 60)
        
        if "BACKGROUND:" in custom_fields:
            start = custom_fields.find("BACKGROUND:")
            end = start + 500
            print("\n📋 BACKGROUND SECTION:")
            print("-" * 60)
            print(custom_fields[start:end])
            print("-" * 60)
        
    finally:
        await pool.close()


async def main():
    """Main validation function"""
    
    character_name = sys.argv[1] if len(sys.argv) > 1 else "elena"
    
    print(f"\n{'='*60}")
    print(f"🧪 CDL PROMPT FORMATTING VALIDATION")
    print(f"{'='*60}\n")
    
    # Run validation
    success = await validate_prompt_formatting(character_name)
    
    # Show sample sections
    await show_sample_sections(character_name)
    
    # Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
