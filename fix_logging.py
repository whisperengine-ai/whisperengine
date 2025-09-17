#!/usr/bin/env python3
"""
Batch fix for logging format issues in WhisperEngine codebase
Converts f-string logging to lazy % formatting
"""

import re
import os
from pathlib import Path

def fix_logging_format(file_path):
    """Fix logging format in a single file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern to match f-string logging calls
    patterns = [
        # logging.error(f"message {var}")
        (r'logging\.(error|warning|info|debug)\(f"([^"]*)".*?\)', r'logging.\1("\2", '),
        # logging.error(f'message {var}')  
        (r"logging\.(error|warning|info|debug)\(f'([^']*)'.*?\)", r"logging.\1('\2', "),
    ]
    
    changes_made = 0
    
    for pattern, replacement in patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            # Extract the message and convert {var} to %s
            full_match = match.group(0)
            log_level = match.group(1)
            message = match.group(2)
            
            # Convert {var} to %s in the message
            converted_message = re.sub(r'\{([^}]+)\}', '%s', message)
            
            # Extract variables from the original f-string
            vars_in_braces = re.findall(r'\{([^}]+)\}', message)
            
            if vars_in_braces:
                # Build the new logging call
                var_list = ', '.join(vars_in_braces)
                if message.startswith('"'):
                    new_call = f'logging.{log_level}("{converted_message}", {var_list})'
                else:
                    new_call = f"logging.{log_level}('{converted_message}', {var_list})"
                
                content = content.replace(full_match, new_call)
                changes_made += 1
    
    # Write back if changes were made
    if changes_made > 0 and content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fixed {changes_made} logging issues in {file_path}")
        return changes_made
    
    return 0

def main():
    """Fix logging format issues across the codebase"""
    print("🔧 Fixing logging format issues...")
    
    # Files to fix
    files_to_fix = [
        "src/platforms/universal_chat.py",
        "src/examples/graph_bot_integration.py",
        "verify_logs_system.py"
    ]
    
    total_fixes = 0
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            fixes = fix_logging_format(file_path)
            total_fixes += fixes
        else:
            print(f"⚠️ File not found: {file_path}")
    
    print(f"\n🎉 Total fixes applied: {total_fixes}")

if __name__ == "__main__":
    main()