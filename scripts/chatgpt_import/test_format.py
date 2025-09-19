#!/usr/bin/env python3
"""
Quick ChatGPT Import Test Script

This script provides a simple way to test ChatGPT import parsing
without needing the full WhisperEngine environment.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_chatgpt_format(file_path: str):
    """Test parsing of ChatGPT export format"""
    
    print(f"🧪 Testing ChatGPT export format: {file_path}")
    print("=" * 60)
    
    try:
        # Load the file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"✅ File loaded successfully")
        print(f"📊 Data type: {type(data)}")
        
        if isinstance(data, list):
            print(f"📋 Found {len(data)} conversations")
            
            # Analyze first few conversations
            for i, conv in enumerate(data[:3]):
                print(f"\n📝 Conversation {i+1}:")
                print(f"  Title: {conv.get('title', 'No title')}")
                print(f"  ID: {conv.get('id', 'No ID')}")
                
                # Check timestamps
                create_time = conv.get('create_time')
                if create_time:
                    dt = datetime.fromtimestamp(create_time)
                    print(f"  Created: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Analyze mapping structure
                mapping = conv.get('mapping', {})
                print(f"  Mapping nodes: {len(mapping)}")
                
                # Count message types
                user_msgs = 0
                assistant_msgs = 0
                system_msgs = 0
                
                for node_id, node_data in mapping.items():
                    message = node_data.get('message')
                    if message:
                        author = message.get('author', {})
                        role = author.get('role') if isinstance(author, dict) else None
                        
                        if role == 'user':
                            user_msgs += 1
                        elif role == 'assistant':
                            assistant_msgs += 1
                        elif role == 'system':
                            system_msgs += 1
                            
                print(f"  Messages: {user_msgs} user, {assistant_msgs} assistant, {system_msgs} system")
                
                # Show sample message content
                for node_id, node_data in mapping.items():
                    message = node_data.get('message')
                    if message and message.get('author', {}).get('role') == 'user':
                        content = message.get('content', {})
                        parts = content.get('parts', [])
                        if parts and parts[0]:
                            sample_text = str(parts[0])[:100]
                            print(f"  Sample user message: '{sample_text}{'...' if len(str(parts[0])) > 100 else ''}'")
                        break
                        
            if len(data) > 3:
                print(f"\n... and {len(data) - 3} more conversations")
                
        else:
            print(f"❓ Unexpected data structure - not a list of conversations")
            print(f"🔍 Top-level keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
        print(f"\n✅ Format analysis complete")
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing file: {e}")
        return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/chatgpt_import/test_format.py <conversations.json>")
        print("Example: python scripts/chatgpt_import/test_format.py ~/Downloads/conversations.json")
        return 1
        
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return 1
        
    success = test_chatgpt_format(file_path)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())