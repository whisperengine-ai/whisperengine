#!/usr/bin/env python3
"""
CDL Validation Demo - Demonstrate the validation system with current CDL files.

This script shows how to use the CDL validation system and runs validation
on the current character files to demonstrate functionality.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from validation import CDLValidator, CDLContentAuditor, CDLPatternTester


def demo_single_character_validation():
    """Demonstrate validation of a single character file."""
    print("🎯 CDL VALIDATION SYSTEM DEMO")
    print("=" * 80)
    
    # Try to find Elena's character file as an example
    possible_paths = [
        "characters/examples/elena-rodriguez.json",
        "characters/elena-rodriguez.json", 
        "../characters/examples/elena-rodriguez.json",
        "../../characters/examples/elena-rodriguez.json"
    ]
    
    elena_path = None
    for path in possible_paths:
        if Path(path).exists():
            elena_path = path
            break
    
    if not elena_path:
        print("⚠️  Could not find Elena's character file for demo")
        print("Creating a synthetic demo instead...")
        demo_with_synthetic_data()
        return
    
    print(f"📋 Using character file: {elena_path}")
    print()
    
    # Initialize validators
    validator = CDLValidator()
    auditor = CDLContentAuditor()
    tester = CDLPatternTester()
    
    print("🔍 1. STRUCTURE VALIDATION")
    print("-" * 40)
    validation_result = validator.validate_file(elena_path)
    validator.print_validation_report(validation_result, verbose=False)
    
    print("\n📝 2. CONTENT AUDIT")
    print("-" * 40)
    audit_result = auditor.audit_file(elena_path)
    auditor.print_detailed_report(audit_result)
    
    print("\n🎯 3. PATTERN TESTING")
    print("-" * 40)
    pattern_result = tester.test_character_patterns(elena_path)
    tester.print_pattern_report(pattern_result, verbose=True)
    
    # Final summary
    print("\n🏆 DEMO SUMMARY")
    print("=" * 50)
    print(f"✅ Structure Validation: {validation_result.overall_status.value}")
    print(f"📊 Content Completeness: {audit_result.completeness_score:.1f}%")
    print(f"🎯 Pattern Success Rate: {pattern_result.overall_success_rate:.1%}")
    
    print("\n💡 The CDL validation system provides:")
    print("   • Comprehensive structure and parsing validation")
    print("   • Detailed content completeness analysis")
    print("   • Conversation pattern detection testing")
    print("   • Actionable recommendations for improvement")
    print("   • Batch processing capabilities for multiple files")


def demo_with_synthetic_data():
    """Demo with synthetic character data if no files are found."""
    print("🧪 SYNTHETIC VALIDATION DEMO")
    print("-" * 40)
    
    # Create minimal synthetic CDL data
    synthetic_cdl = {
        "character": {
            "identity": {
                "name": "Demo Character",
                "age": 25,
                "occupation": "AI Assistant"
            },
            "personality": {
                "traits": ["helpful", "curious", "analytical"]
            },
            "communication": {
                "typical_responses": {
                    "greeting": "Hello! How can I help you today?"
                },
                "message_pattern_triggers": {
                    "help_request": ["help", "assist", "support"]
                },
                "conversation_flow_guidance": {
                    "help_request": "Offer specific assistance and ask clarifying questions"
                }
            }
        }
    }
    
    # Save to temporary file
    import json
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(synthetic_cdl, f, indent=2)
        temp_path = f.name
    
    try:
        print(f"📋 Using synthetic character data")
        
        # Run basic validation
        validator = CDLValidator()
        result = validator.validate_file(temp_path)
        
        print(f"✅ Parsing Success: {result.parsing_success}")
        print(f"📊 Standardization: {result.standardization_compliant}")
        print(f"🎯 Pattern Detection: {result.pattern_detection_working}")
        
        if result.issues:
            print(f"\n⚠️  Issues found: {len(result.issues)}")
            for issue in result.issues[:3]:  # Show first 3 issues
                print(f"   • {issue.message}")
        
        print("\n💡 This demonstrates the validation system can:")
        print("   • Parse and validate CDL structure")
        print("   • Check for standardized organization")
        print("   • Test conversation pattern detection")
        print("   • Provide detailed feedback and recommendations")
        
    finally:
        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)


def demo_batch_validation():
    """Demonstrate batch validation capabilities."""
    print("\n🔄 BATCH VALIDATION DEMO")
    print("-" * 40)
    
    # Try to find characters directory
    possible_dirs = [
        "characters/examples",
        "characters",
        "../characters/examples", 
        "../../characters/examples"
    ]
    
    chars_dir = None
    for directory in possible_dirs:
        if Path(directory).exists() and list(Path(directory).glob("*.json")):
            chars_dir = directory
            break
    
    if not chars_dir:
        print("⚠️  No character files found for batch demo")
        return
    
    print(f"📂 Using character directory: {chars_dir}")
    
    # Count files
    json_files = list(Path(chars_dir).glob("*.json"))
    print(f"📊 Found {len(json_files)} character files")
    
    if len(json_files) > 0:
        validator = CDLValidator()
        results = validator.validate_directory(chars_dir)
        
        print(f"\n📋 Batch Validation Results:")
        successful = sum(1 for r in results if r.parsing_success)
        standardized = sum(1 for r in results if r.standardization_compliant)
        
        print(f"   • Parsing Success: {successful}/{len(results)}")
        print(f"   • Standardized: {standardized}/{len(results)}")
        
        # Show top performers
        sorted_results = sorted(results, key=lambda r: r.completeness_score, reverse=True)
        print(f"\n🏆 Top Character (by completeness):")
        if sorted_results:
            top = sorted_results[0]
            print(f"   {top.character_name} - {top.completeness_score:.1f}% complete")
    
    print("\n💡 Batch validation enables:")
    print("   • Processing entire character collections")
    print("   • Comparative quality analysis")
    print("   • Identifying patterns across characters")
    print("   • Bulk quality assurance")


def show_usage_examples():
    """Show practical usage examples."""
    print("\n📖 USAGE EXAMPLES")
    print("=" * 50)
    
    print("🔹 Python API Usage:")
    print("""
from src.validation import CDLValidator, CDLContentAuditor, CDLPatternTester

# Validate structure and parsing
validator = CDLValidator()
result = validator.validate_file('path/to/character.json')
validator.print_validation_report(result)

# Audit content completeness
auditor = CDLContentAuditor()
audit = auditor.audit_file('path/to/character.json')
auditor.print_detailed_report(audit)

# Test conversation patterns
tester = CDLPatternTester()
patterns = tester.test_character_patterns('path/to/character.json')
tester.print_pattern_report(patterns)
""")
    
    print("🔹 Command Line Usage:")
    print("""
# Comprehensive validation of single file
python src/validation/validate_cdl.py single characters/elena.json

# Batch validation of directory
python src/validation/validate_cdl.py batch characters/examples/

# Content audit only
python src/validation/validate_cdl.py audit characters/marcus.json

# Pattern testing only
python src/validation/validate_cdl.py patterns characters/jake.json --verbose
""")
    
    print("🔹 Integration in Development Workflow:")
    print("""
# Pre-commit validation
python src/validation/validate_cdl.py single new_character.json

# Quality assurance check
python src/validation/validate_cdl.py batch characters/ --pattern "*.json"

# Debug conversation issues
python src/validation/validate_cdl.py patterns problematic_character.json -v
""")


def main():
    """Run the complete demo."""
    try:
        demo_single_character_validation()
        demo_batch_validation()
        show_usage_examples()
        
        print("\n🎉 CDL VALIDATION DEMO COMPLETE")
        print("=" * 50)
        print("The validation system is ready for use by developers!")
        print("Use 'python src/validation/validate_cdl.py --help' for CLI usage.")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n💥 Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()