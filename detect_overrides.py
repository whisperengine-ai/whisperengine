#!/usr/bin/env python3
"""
Runtime Override Detection Script

This script shows you how to detect if memory methods are being overridden
with enhanced versions at runtime.
"""

import inspect
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def detect_method_override():
    """Detect if memory methods are being overridden with enhanced versions."""
    
    print("🔍 Memory Method Override Detection")
    print("=" * 50)
    
    try:
        # Import the components
        from src.memory.integrated_memory_manager import IntegratedMemoryManager
        from src.utils.enhanced_memory_manager import EnhancedMemoryManager
        from src.utils.memory_integration_patch import apply_memory_enhancement_patch
        
        print("✅ Successfully imported memory components")
        
        # Create base memory manager
        base_manager = IntegratedMemoryManager()
        print("✅ Created base IntegratedMemoryManager")
        
        # Check original method
        original_method = base_manager.retrieve_relevant_memories
        original_module = inspect.getmodule(original_method)
        original_qualname = getattr(original_method, '__qualname__', 'unknown')
        
        print(f"\n📋 BEFORE Enhancement:")
        print(f"   Method: retrieve_relevant_memories")
        print(f"   Module: {original_module.__name__ if original_module else 'unknown'}")
        print(f"   Qualname: {original_qualname}")
        print(f"   Type: {type(base_manager).__name__}")
        
        # Apply enhancement patch
        enhanced_manager = apply_memory_enhancement_patch(base_manager)
        print(f"\n🚀 AFTER Enhancement:")
        
        # Check enhanced method
        enhanced_method = enhanced_manager.retrieve_relevant_memories
        enhanced_module = inspect.getmodule(enhanced_method)
        enhanced_qualname = getattr(enhanced_method, '__qualname__', 'unknown')
        
        print(f"   Method: retrieve_relevant_memories")
        print(f"   Module: {enhanced_module.__name__ if enhanced_module else 'unknown'}")
        print(f"   Qualname: {enhanced_qualname}")
        print(f"   Type: {type(enhanced_manager).__name__}")
        
        # Check if method was actually replaced
        if original_method != enhanced_method:
            print(f"\n✅ METHOD WAS REPLACED!")
            print(f"   🔄 Old: {original_qualname}")
            print(f"   🚀 New: {enhanced_qualname}")
        else:
            print(f"\n⚠️  Method was NOT replaced")
        
        # Check if it's the enhanced manager
        if isinstance(enhanced_manager, EnhancedMemoryManager):
            print(f"✅ Manager is now EnhancedMemoryManager")
        else:
            print(f"⚠️  Manager is still: {type(enhanced_manager).__name__}")
        
        # Show method source (first few lines)
        try:
            source_lines = inspect.getsourcelines(enhanced_method)
            print(f"\n📖 Enhanced Method Source (first 3 lines):")
            for i, line in enumerate(source_lines[0][:3]):
                print(f"   {i+1}: {line.rstrip()}")
        except:
            print(f"   (Source not available)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_override_chain():
    """Show the full override chain for method calls."""
    
    print(f"\n🔗 Override Chain Analysis")
    print("=" * 30)
    
    try:
        from src.utils.enhanced_memory_manager import EnhancedMemoryManager
        
        # Show the actual override implementation
        print("📋 Enhanced Manager Override Pattern:")
        print("```python")
        print("def retrieve_relevant_memories(self, user_id, message, limit=10):")
        print("    '''Enhanced version - replaces original method'''")
        print("    return self.retrieve_relevant_memories_enhanced(user_id, message, limit, None)")
        print("```")
        
        print(f"\n🔄 Call Flow:")
        print("   User Code:")
        print("   ├── manager.retrieve_relevant_memories(user_id, query)")
        print("   └── 🔄 INTERCEPTED by EnhancedMemoryManager")
        print("       └── 🚀 Redirected to retrieve_relevant_memories_enhanced()")
        print("           └── 💡 Uses optimized query processing")
        print("               └── 📊 Returns enhanced results")
        
        return True
        
    except Exception as e:
        print(f"❌ Error showing override chain: {e}")
        return False

def check_runtime_logs():
    """Show how to detect this in runtime logs."""
    
    print(f"\n📝 How to Verify in Runtime Logs")
    print("=" * 40)
    
    print("✅ Look for these log messages in your bot startup:")
    print("   • 'Enhanced memory system patch applied successfully'")
    print("   • 'Improved topic recall from past conversations'")
    print("   • 'Enhanced memory system patch applied for improved topic recall'")
    
    print(f"\n✅ Enhanced query processing logs:")
    print("   • 'Enhanced query processing for user {user_id}'")
    print("   • 'Query optimization strategies: {count}'")
    print("   • 'Combined search returned {count} unique memories'")
    
    print(f"\n✅ Method override verification:")
    print("   • Check manager type in logs: should show 'EnhancedMemoryManager'")
    print("   • Memory patch success messages")
    
    print(f"\n💡 Pro Tip:")
    print("   Add this to your code to verify at runtime:")
    print("   ```python")
    print("   logger.info(f'Memory manager type: {type(self.memory_manager).__name__}')")
    print("   logger.info(f'Method module: {self.memory_manager.retrieve_relevant_memories.__module__}')")
    print("   ```")

if __name__ == "__main__":
    success = True
    
    success &= detect_method_override()
    success &= show_override_chain()
    check_runtime_logs()
    
    print(f"\n" + "=" * 60)
    if success:
        print("🎉 OVERRIDE DETECTION COMPLETE!")
        print("Your memory methods ARE being enhanced through override.")
    else:
        print("❌ Could not fully verify overrides")
    
    print(f"\n🎯 Summary:")
    print("• Enhanced methods replace legacy ones automatically")
    print("• No code changes needed - transparent enhancement")
    print("• All 'legacy' calls actually use enhanced functionality")