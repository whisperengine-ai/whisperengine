#!/usr/bin/env python3
"""
Global Facts Dump and Import Tool

This script provides functionality to:
1. Export all global facts from the memory system to a JSON file
2. Import global facts from a JSON file back into the memory system

Usage:
    Export: python dump_global_facts.py export [--output filename.json]
    Import: python dump_global_facts.py import --input filename.json [--confirm]
    
The export format includes:
- Fact content
- Context
- Timestamp
- Added by information
- Extraction method
"""

import argparse
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.memory.memory_manager import UserMemoryManager
from src.utils.exceptions import MemoryStorageError, ValidationError


def export_global_facts(memory_manager: UserMemoryManager, output_file: Optional[str] = None) -> Optional[str]:
    """
    Export all global facts to a JSON file.
    
    Args:
        memory_manager: The memory manager instance
        output_file: Optional output filename. If not provided, generates timestamp-based name.
        
    Returns:
        The filename that was written to
    """
    try:
        # Get all global facts
        print("Retrieving global facts...")
        global_facts = memory_manager.get_all_global_facts()
        
        if not global_facts:
            print("No global facts found in the database.")
            return None
            
        print(f"Found {len(global_facts)} global facts")
        
        # Generate output filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"global_facts_export_{timestamp}.json"
        
        # Prepare export data
        export_data = {
            "export_info": {
                "export_date": datetime.now().isoformat(),
                "total_facts": len(global_facts),
                "export_version": "1.0"
            },
            "global_facts": []
        }
        
        # Process each fact
        for fact_data in global_facts:
            metadata = fact_data.get("metadata", {})
            fact_entry = {
                "fact": metadata.get("fact", ""),
                "context": metadata.get("context", ""),
                "timestamp": metadata.get("timestamp", ""),
                "added_by": metadata.get("added_by", "unknown"),
                "extraction_method": metadata.get("extraction_method", "unknown")
            }
            export_data["global_facts"].append(fact_entry)
        
        # Write to file
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nGlobal facts exported successfully!")
        print(f"File: {output_path.absolute()}")
        print(f"Total facts exported: {len(global_facts)}")
        
        return str(output_path)
        
    except Exception as e:
        print(f"Error exporting global facts: {e}")
        raise


def import_global_facts(memory_manager: UserMemoryManager, input_file: str, confirm: bool = False) -> int:
    """
    Import global facts from a JSON file.
    
    Args:
        memory_manager: The memory manager instance
        input_file: Path to the JSON file to import
        confirm: If True, skip confirmation prompt
        
    Returns:
        Number of facts imported
    """
    try:
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Load the export file
        print(f"Loading global facts from: {input_path.absolute()}")
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate file format
        if "global_facts" not in data:
            raise ValueError("Invalid file format: missing 'global_facts' key")
        
        facts_to_import = data["global_facts"]
        if not facts_to_import:
            print("No global facts found in the file.")
            return 0
        
        export_info = data.get("export_info", {})
        print(f"\nFile information:")
        print(f"  Export date: {export_info.get('export_date', 'Unknown')}")
        print(f"  Total facts in file: {len(facts_to_import)}")
        print(f"  Export version: {export_info.get('export_version', 'Unknown')}")
        
        # Show sample facts
        print(f"\nSample facts to import:")
        for i, fact in enumerate(facts_to_import[:3]):
            print(f"  {i+1}. {fact.get('fact', '')[:80]}...")
        
        if len(facts_to_import) > 3:
            print(f"  ... and {len(facts_to_import) - 3} more facts")
        
        # Confirmation
        if not confirm:
            response = input(f"\nDo you want to import {len(facts_to_import)} global facts? [y/N]: ")
            if response.lower() not in ['y', 'yes']:
                print("Import cancelled.")
                return 0
        
        # Import facts
        print("\nImporting global facts...")
        imported_count = 0
        errors = []
        
        for i, fact_data in enumerate(facts_to_import):
            try:
                fact = fact_data.get("fact", "")
                context = fact_data.get("context", "")
                added_by = fact_data.get("added_by", "import")
                
                if not fact.strip():
                    errors.append(f"Fact {i+1}: Empty fact content")
                    continue
                
                # Store the fact
                memory_manager.store_global_fact(
                    fact=fact,
                    context=context,
                    added_by=f"{added_by}_import"
                )
                
                imported_count += 1
                
                # Progress indicator
                if (i + 1) % 10 == 0:
                    print(f"  Imported {i + 1}/{len(facts_to_import)} facts...")
                    
            except (ValidationError, MemoryStorageError) as e:
                errors.append(f"Fact {i+1}: {str(e)}")
            except Exception as e:
                errors.append(f"Fact {i+1}: Unexpected error - {str(e)}")
        
        # Summary
        print(f"\nImport completed!")
        print(f"Successfully imported: {imported_count} facts")
        
        if errors:
            print(f"Errors encountered: {len(errors)}")
            print("First few errors:")
            for error in errors[:5]:
                print(f"  - {error}")
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more errors")
        
        return imported_count
        
    except Exception as e:
        print(f"Error importing global facts: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Export and import global facts from the memory system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Export all global facts:
    python dump_global_facts.py export
    
  Export to specific file:
    python dump_global_facts.py export --output my_facts.json
    
  Import global facts:
    python dump_global_facts.py import --input my_facts.json
    
  Import without confirmation prompt:
    python dump_global_facts.py import --input my_facts.json --confirm
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export global facts to JSON file')
    export_parser.add_argument(
        '--output', '-o',
        help='Output file name (default: auto-generated with timestamp)'
    )
    export_parser.add_argument(
        '--db-path',
        default='./chromadb_data',
        help='Path to ChromaDB database (default: ./chromadb_data)'
    )
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import global facts from JSON file')
    import_parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input JSON file to import from'
    )
    import_parser.add_argument(
        '--confirm', '-y',
        action='store_true',
        help='Skip confirmation prompt'
    )
    import_parser.add_argument(
        '--db-path',
        default='./chromadb_data',
        help='Path to ChromaDB database (default: ./chromadb_data)'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        # Initialize memory manager
        print("Initializing memory manager...")
        try:
            db_path = getattr(args, 'db_path', './chromadb_data')
            memory_manager = UserMemoryManager(persist_directory=db_path)
        except Exception as init_error:
            print(f"❌ Failed to initialize memory system: {init_error}")
            print("\nPossible solutions:")
            print("1. Make sure the ChromaDB database is properly initialized")
            print("2. Try running the Discord bot first to initialize the database")
            print("3. Check if the chromadb_data directory exists and has proper permissions")
            return 1
        
        if args.command == 'export':
            output_file = export_global_facts(memory_manager, args.output)
            if output_file:
                return 0
            else:
                return 1
                
        elif args.command == 'import':
            imported_count = import_global_facts(memory_manager, args.input, args.confirm)
            if imported_count > 0:
                print(f"\nImport successful: {imported_count} facts imported")
                return 0
            else:
                return 1
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
