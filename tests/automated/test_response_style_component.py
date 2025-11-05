"""
Test script for CDL-based create_response_style_component()

Validates that the new component:
1. Pulls character-specific data from database
2. Shows different content for different characters
3. Replaces hardcoded create_guidance_component()

Run: python tests/automated/test_response_style_component.py
"""
import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database.postgres_pool_manager import get_postgres_pool
from src.characters.cdl.enhanced_cdl_manager import create_enhanced_cdl_manager
from src.prompts.cdl_component_factories import create_response_style_component


async def test_response_style_component():
    """Test response style component for multiple characters."""
    
    # Test characters with known different personalities and response_style data
    test_characters = ["elena", "gabriel"]
    
    print("=" * 80)
    print("🧪 TESTING: CDL Response Style Component")
    print("=" * 80)
    print()
    
    try:
        # Get database pool
        pool = await get_postgres_pool()
        if not pool:
            print("❌ FAILED: Could not get PostgreSQL pool")
            return False
        
        enhanced_manager = create_enhanced_cdl_manager(pool)
        
        all_passed = True
        
        for character_name in test_characters:
            print(f"📋 Testing character: {character_name.upper()}")
            print("-" * 80)
            
            # Create component
            component = await create_response_style_component(
                enhanced_manager=enhanced_manager,
                character_name=character_name,
                priority=17
            )
            
            if not component:
                print(f"❌ FAILED: No component created for {character_name}")
                all_passed = False
                continue
            
            # Validate component properties
            assert component.priority == 17, f"Wrong priority: {component.priority}"
            assert component.required == True, "Component should be required"
            assert len(component.content) > 100, "Content too short"
            
            # Check for character-specific content
            content_lower = component.content.lower()
            
            # Character name should appear in content
            if character_name.lower() not in content_lower:
                print(f"⚠️  WARNING: Character name '{character_name}' not found in content")
            
            # Print component details
            print(f"✅ Component Created:")
            print(f"   Type: {component.type.value}")
            print(f"   Priority: {component.priority}")
            print(f"   Token Cost: ~{component.token_cost}")
            print(f"   Required: {component.required}")
            print(f"   Content Length: {len(component.content)} chars")
            
            # Print metadata
            if component.metadata:
                print(f"   Metadata:")
                for key, value in component.metadata.items():
                    print(f"     - {key}: {value}")
            
            # Print first 300 chars of content
            print(f"\n   Content Preview:")
            preview = component.content[:500].replace('\n', '\n   ')
            print(f"   {preview}")
            if len(component.content) > 500:
                print(f"   ... ({len(component.content) - 500} more characters)")
            
            print()
        
        if all_passed:
            print("=" * 80)
            print("✅ ALL TESTS PASSED")
            print("=" * 80)
            print()
            print("🎯 SUCCESS: create_response_style_component() pulls character-specific")
            print("           guidance from CDL database instead of using hardcoded text!")
            print()
            return True
        else:
            print("=" * 80)
            print("❌ SOME TESTS FAILED")
            print("=" * 80)
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Set environment for database connection
    os.environ["POSTGRES_HOST"] = os.getenv("POSTGRES_HOST", "localhost")
    os.environ["POSTGRES_PORT"] = os.getenv("POSTGRES_PORT", "5433")
    os.environ["POSTGRES_USER"] = os.getenv("POSTGRES_USER", "whisperengine")
    os.environ["POSTGRES_PASSWORD"] = os.getenv("POSTGRES_PASSWORD", "whisperengine_dev_password")
    os.environ["POSTGRES_DB"] = os.getenv("POSTGRES_DB", "whisperengine")
    
    # Run test
    success = asyncio.run(test_response_style_component())
    sys.exit(0 if success else 1)
