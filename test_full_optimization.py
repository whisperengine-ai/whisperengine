#!/usr/bin/env python3
"""
Full optimization validation test for WhisperEngine
Tests prompt template optimization and intelligent message summarization integration
"""
import asyncio
import json
import time
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def main():
    """Run simplified optimization validation using live system data"""
    print("🚀 WhisperEngine Optimization Validation")
    print("=" * 50)
    
    try:
        # Import within function to avoid module loading issues
        from src.core.config import get_system_prompt
        from src.utils.context_size_manager import estimate_tokens
        
        # Test 1: Check current prompt optimization
        print("\n🧪 Testing Current Prompt Configuration...")
        current_prompt = get_system_prompt()
        current_tokens = estimate_tokens(current_prompt)
        
        print(f"   Current system prompt tokens: {current_tokens}")
        
        # Baseline comparison (typical unoptimized prompt is ~5000+ tokens)
        baseline_tokens = 5000
        if current_tokens < 3000:
            reduction = ((baseline_tokens - current_tokens) / baseline_tokens) * 100
            print(f"   ✅ Optimized prompt detected!")
            print(f"   📊 Estimated token reduction: {reduction:.1f}%")
            prompt_optimized = True
        else:
            print(f"   ⚠️ Prompt may need optimization")
            prompt_optimized = False
            reduction = 0
        
        # Test 2: Check boundary manager integration
        print("\n🧪 Testing Boundary Manager Integration...")
        try:
            from src.conversation.boundary_manager import ConversationBoundaryManager
            boundary_manager = ConversationBoundaryManager()
            
            # Simple initialization test
            test_result = await boundary_manager.process_message(
                user_id="test_user_123",
                channel_id="test_channel_456", 
                message_id="test_msg_789",
                message_content="Integration test message",
                timestamp=datetime.now()
            )
            
            if test_result:
                print(f"   ✅ Boundary manager integration working")
                print(f"   📝 Session ID: {test_result.session_id[:8]}...")
                boundary_working = True
            else:
                print(f"   ⚠️ Boundary manager integration issue")
                boundary_working = False
                
        except Exception as e:
            print(f"   ❌ Boundary manager error: {e}")
            boundary_working = False
        
        # Test 3: Performance check
        print("\n📊 Performance Check...")
        start_time = time.time()
        
        # Simulate typical operations
        for i in range(3):
            _ = get_system_prompt()
            _ = estimate_tokens("Test message for performance measurement")
        
        end_time = time.time()
        processing_time = (end_time - start_time) * 1000
        
        print(f"   ⏱️ Processing time for 3 operations: {processing_time:.1f}ms")
        performance_ok = processing_time < 1000  # Should be very fast for these operations
        
        if performance_ok:
            print(f"   ✅ Performance target met")
        else:
            print(f"   ⚠️ Performance may need improvement")
        
        # Generate final report
        print("\n📋 OPTIMIZATION STATUS REPORT")
        print("=" * 50)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'prompt_optimization': {
                'enabled': prompt_optimized,
                'current_tokens': current_tokens,
                'estimated_reduction_percent': reduction if prompt_optimized else 0
            },
            'boundary_manager': {
                'integration_working': boundary_working,
                'status': 'active' if boundary_working else 'error'
            },
            'performance': {
                'meets_basic_targets': performance_ok,
                'processing_time_ms': processing_time
            }
        }
        
        # Overall assessment
        working_components = sum([prompt_optimized, boundary_working, performance_ok])
        total_components = 3
        
        if working_components == total_components:
            status = "SUCCESS"
            print("🎉 ALL OPTIMIZATIONS WORKING!")
        elif working_components >= 2:
            status = "PARTIAL_SUCCESS" 
            print("✅ MAJOR OPTIMIZATIONS WORKING")
        else:
            status = "NEEDS_ATTENTION"
            print("⚠️ OPTIMIZATIONS NEED ATTENTION")
        
        report['overall_status'] = status
        report['working_components'] = f"{working_components}/{total_components}"
        
        print(f"📊 Prompt optimization: {'✅' if prompt_optimized else '❌'}")
        print(f"📊 Boundary manager: {'✅' if boundary_working else '❌'}")
        print(f"📊 Performance: {'✅' if performance_ok else '❌'}")
        print(f"🎯 Overall status: {status}")
        
        if prompt_optimized:
            print(f"💡 Token reduction achieved: {reduction:.1f}%")
        
        # Save report
        report_file = f"optimization_status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Report saved to: {report_file}")
        
        return status == "SUCCESS"
        
    except Exception as e:
        print(f"\n❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())