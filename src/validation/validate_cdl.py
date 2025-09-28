#!/usr/bin/env python3
"""
CDL Validation CLI - Command-line interface for CDL validation tools.

This script provides easy access to all CDL validation functionality for developers.

Usage:
    python src/validation/validate_cdl.py --help
    python src/validation/validate_cdl.py single path/to/character.json
    python src/validation/validate_cdl.py batch characters/examples/
    python src/validation/validate_cdl.py audit path/to/character.json
    python src/validation/validate_cdl.py patterns path/to/character.json
"""

import argparse
import sys
from pathlib import Path
from typing import List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from validation.cdl_validator import CDLValidator
from validation.content_auditor import CDLContentAuditor
from validation.pattern_tester import CDLPatternTester


def validate_single_file(file_path: str, verbose: bool = False):
    """Validate a single CDL file with all validation types."""
    print(f"🔍 Comprehensive CDL Validation")
    print("=" * 80)
    
    validator = CDLValidator()
    auditor = CDLContentAuditor()
    tester = CDLPatternTester()
    
    # Run all validations
    print(f"📋 Validating: {file_path}")
    
    # 1. Structure and parsing validation
    validation_result = validator.validate_file(file_path)
    validator.print_validation_report(validation_result, verbose=verbose)
    
    # 2. Content audit
    audit_result = auditor.audit_file(file_path)
    auditor.print_detailed_report(audit_result)
    
    # 3. Pattern testing
    pattern_result = tester.test_character_patterns(file_path)
    tester.print_pattern_report(pattern_result, verbose=verbose)
    
    # Summary
    print(f"\n📊 VALIDATION SUMMARY for {validation_result.character_name}")
    print("=" * 60)
    print(f"✅ Structure: {validation_result.summary}")
    print(f"📝 Content: {audit_result.overall_rating} ({audit_result.completeness_score:.1f}% complete, {audit_result.quality_score:.1f}% quality)")
    print(f"🔍 Patterns: {pattern_result.overall_success_rate:.1%} success rate, {pattern_result.working_tests} working tests")
    
    overall_health = "HEALTHY" if (
        validation_result.parsing_success and 
        validation_result.standardization_compliant and
        audit_result.completeness_score > 70 and
        pattern_result.overall_success_rate > 0.5
    ) else "NEEDS_ATTENTION"
    
    health_emoji = "✅" if overall_health == "HEALTHY" else "⚠️"
    print(f"\n{health_emoji} Overall Health: {overall_health}")


def validate_batch_files(directory_path: str, pattern: str = "*.json"):
    """Validate all CDL files in a directory."""
    print(f"🔍 Batch CDL Validation")
    print("=" * 80)
    
    validator = CDLValidator()
    auditor = CDLContentAuditor()
    tester = CDLPatternTester()
    
    directory = Path(directory_path)
    if not directory.exists():
        print(f"❌ Directory not found: {directory_path}")
        return
    
    # Get all files matching pattern
    files = list(directory.glob(pattern))
    if not files:
        print(f"❌ No files found matching pattern '{pattern}' in {directory_path}")
        return
    
    print(f"📋 Found {len(files)} files to validate")
    
    # Run batch validations
    validation_results = validator.validate_directory(directory_path, pattern)
    audit_results = []
    pattern_results = []
    
    for file_path in files:
        audit_results.append(auditor.audit_file(file_path))
        pattern_results.append(tester.test_character_patterns(file_path))
    
    # Print summary reports
    validator.print_summary_report(validation_results)
    auditor.print_summary_report(audit_results)
    tester.print_batch_summary(pattern_results)
    
    # Overall batch health assessment
    healthy_count = 0
    for i, validation_result in enumerate(validation_results):
        audit_result = audit_results[i] if i < len(audit_results) else None
        pattern_result = pattern_results[i] if i < len(pattern_results) else None
        
        if (validation_result.parsing_success and 
            validation_result.standardization_compliant and
            audit_result and audit_result.completeness_score > 70 and
            pattern_result and pattern_result.overall_success_rate > 0.5):
            healthy_count += 1
    
    print(f"\n🏥 BATCH HEALTH SUMMARY")
    print("=" * 40)
    print(f"Healthy Characters: {healthy_count}/{len(files)} ({healthy_count/len(files)*100:.1f}%)")
    
    if healthy_count == len(files):
        print("🎉 All characters are healthy!")
    elif healthy_count >= len(files) * 0.8:
        print("✅ Most characters are healthy - minor fixes needed")
    elif healthy_count >= len(files) * 0.5:
        print("⚠️  Some characters need attention")
    else:
        print("🚨 Many characters need significant work")


def audit_content_only(file_path: str):
    """Run only content audit on a file."""
    print(f"📝 CDL Content Audit")
    print("=" * 60)
    
    auditor = CDLContentAuditor()
    result = auditor.audit_file(file_path)
    auditor.print_detailed_report(result)


def test_patterns_only(file_path: str, verbose: bool = False):
    """Run only pattern testing on a file."""
    print(f"🔍 CDL Pattern Testing")
    print("=" * 60)
    
    tester = CDLPatternTester()
    result = tester.test_character_patterns(file_path)
    tester.print_pattern_report(result, verbose=verbose)


def structure_validation_only(file_path: str, verbose: bool = False):
    """Run only structure validation on a file."""
    print(f"🏗️  CDL Structure Validation")
    print("=" * 60)
    
    validator = CDLValidator()
    result = validator.validate_file(file_path)
    validator.print_validation_report(result, verbose=verbose)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CDL Validation Tools - Comprehensive validation for Character Definition Language files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s single characters/examples/elena-rodriguez.json
  %(prog)s batch characters/examples/ --pattern "*.json"
  %(prog)s audit characters/examples/gabriel.json  
  %(prog)s patterns characters/examples/marcus-thompson.json --verbose
  %(prog)s structure characters/examples/jake-sterling.json --verbose
        """
    )
    
    parser.add_argument(
        'command',
        choices=['single', 'batch', 'audit', 'patterns', 'structure'],
        help='Validation command to run'
    )
    
    parser.add_argument(
        'path',
        help='Path to CDL file or directory'
    )
    
    parser.add_argument(
        '--pattern',
        default='*.json',
        help='File pattern for batch operations (default: *.json)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output with detailed information'
    )
    
    args = parser.parse_args()
    
    # Validate path exists
    path = Path(args.path)
    if not path.exists():
        print(f"❌ Path not found: {args.path}")
        sys.exit(1)
    
    # Route to appropriate validation function
    try:
        if args.command == 'single':
            if path.is_file():
                validate_single_file(str(path), args.verbose)
            else:
                print(f"❌ Single validation requires a file path, got directory: {args.path}")
                sys.exit(1)
        
        elif args.command == 'batch':
            if path.is_dir():
                validate_batch_files(str(path), args.pattern)
            else:
                print(f"❌ Batch validation requires a directory path, got file: {args.path}")
                sys.exit(1)
        
        elif args.command == 'audit':
            if path.is_file():
                audit_content_only(str(path))
            else:
                print(f"❌ Content audit requires a file path, got directory: {args.path}")
                sys.exit(1)
        
        elif args.command == 'patterns':
            if path.is_file():
                test_patterns_only(str(path), args.verbose)
            else:
                print(f"❌ Pattern testing requires a file path, got directory: {args.path}")
                sys.exit(1)
        
        elif args.command == 'structure':
            if path.is_file():
                structure_validation_only(str(path), args.verbose)
            else:
                print(f"❌ Structure validation requires a file path, got directory: {args.path}")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print(f"\n⏹️  Validation interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        print(f"\n💥 Validation failed with error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()