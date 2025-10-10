#!/usr/bin/env python3
"""
Synthetic Conversation Data Consolidator

This script consolidates individual conversation JSON files in the synthetic_conversations/
directory into a single batch_test_results.json file that the character intelligence 
validator expects.

Usage:
    python consolidate_synthetic_data.py

The script will:
1. Find all conversation_*.json files in synthetic_conversations/
2. Load and validate each conversation file
3. Create a consolidated batch_test_results.json file
4. Provide statistics on the consolidation process
"""

import json
import os
import glob
from datetime import datetime
from typing import List, Dict, Any


def consolidate_synthetic_conversations() -> None:
    """Consolidate individual conversation files into batch_test_results.json"""
    
    print('🔧 Consolidating synthetic conversation data')
    print('=' * 50)
    
    # Find all conversation JSON files
    conversation_files = glob.glob('./synthetic_conversations/conversation_*.json')
    print(f'📁 Found {len(conversation_files)} conversation files')
    
    if not conversation_files:
        print('❌ No conversation files found in ./synthetic_conversations/')
        return
    
    conversations = []
    skipped_files = []
    
    # Load each conversation file
    for file_path in sorted(conversation_files):
        try:
            with open(file_path, 'r') as f:
                conversation_data = json.load(f)
                
            # Validate basic structure
            required_fields = ['conversation_id', 'bot_name', 'exchanges']
            missing_fields = [field for field in required_fields if field not in conversation_data]
            
            if missing_fields:
                print(f'⚠️  Warning: {file_path} missing fields: {missing_fields}')
                skipped_files.append(file_path)
                continue
                
            conversations.append(conversation_data)
            
        except json.JSONDecodeError as e:
            print(f'❌ Error parsing {file_path}: {e}')
            skipped_files.append(file_path)
        except Exception as e:
            print(f'⚠️  Warning: Could not read {file_path}: {e}')
            skipped_files.append(file_path)
    
    # Create consolidated structure
    batch_data = {
        'conversations': conversations,
        'total_conversations': len(conversations),
        'generated_timestamp': datetime.now().isoformat(),
        'metadata': {
            'source': 'individual_conversation_files',
            'consolidation_script': 'consolidate_synthetic_data.py',
            'total_files_found': len(conversation_files),
            'files_processed': len(conversations),
            'files_skipped': len(skipped_files),
            'skipped_files': skipped_files
        }
    }
    
    # Write consolidated file
    output_path = './synthetic_conversations/batch_test_results.json'
    try:
        with open(output_path, 'w') as f:
            json.dump(batch_data, f, indent=2)
        
        file_size_mb = os.path.getsize(output_path) / (1024*1024)
        print(f'✅ Created {output_path}')
        print(f'📊 Statistics:')
        print(f'   • Total conversations: {len(conversations)}')
        print(f'   • File size: {file_size_mb:.2f} MB')
        print(f'   • Files skipped: {len(skipped_files)}')
        
        if skipped_files:
            print(f'⚠️  Skipped files: {skipped_files}')
            
        print('\n🎯 Ready for character intelligence validation!')
        
    except Exception as e:
        print(f'❌ Error writing {output_path}: {e}')


def main():
    """Main function"""
    try:
        consolidate_synthetic_conversations()
    except KeyboardInterrupt:
        print('\n🛑 Consolidation interrupted by user')
    except Exception as e:
        print(f'❌ Unexpected error: {e}')
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()