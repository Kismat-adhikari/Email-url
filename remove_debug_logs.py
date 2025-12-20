#!/usr/bin/env python3
"""
Remove all debug print statements from backend files for production
"""

import re
import os

def remove_debug_logs():
    """Remove debug logs from backend files"""
    
    # Files to clean
    files_to_clean = [
        'app_anon_history.py',
        'team_manager.py',
        'team_api.py'
    ]
    
    for filename in files_to_clean:
        if not os.path.exists(filename):
            continue
            
        print(f"🧹 Cleaning {filename}...")
        
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_lines = len(content.split('\n'))
        
        # Remove debug print statements
        patterns = [
            r'^\s*print\(f?"?DEBUG:.*?\)\s*$',
            r'^\s*print\(f?"DEBUG .*?\)\s*$',
            r'^\s*print\(f?"🔍.*?\)\s*$',
            r'^\s*print\(f?"🔄.*?\)\s*$',
            r'^\s*print\(f?"DEBUG.*?\)\s*$',
        ]
        
        for pattern in patterns:
            content = re.sub(pattern, '', content, flags=re.MULTILINE)
        
        # Remove empty lines that were left behind
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        new_lines = len(content.split('\n'))
        removed_lines = original_lines - new_lines
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   ✅ Removed {removed_lines} debug lines from {filename}")
    
    print("🎉 Debug log cleanup complete!")

if __name__ == "__main__":
    remove_debug_logs()