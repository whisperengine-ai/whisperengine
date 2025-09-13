#!/usr/bin/env python3
"""
Advanced name extraction from ChromaDB Discord facts
"""

import re
import json
import sqlite3
from typing import Dict, List, Optional, Tuple
from user_profile_db import UserProfileDatabase

class DiscordNameExtractor:
    """Extract Discord user names from stored facts"""
    
    def __init__(self, db_path: str = "user_profiles.db", chromadb_path: str = "chromadb_data/chroma.sqlite3"):
        self.db = UserProfileDatabase(db_path)
        self.chromadb_path = chromadb_path
    
    def extract_names_from_chromadb(self) -> Dict[str, str]:
        """Extract user ID to name mappings from ChromaDB"""
        mappings = {}
        
        try:
            with sqlite3.connect(self.chromadb_path) as conn:
                # Look for documents containing Discord user information
                cursor = conn.execute("""
                    SELECT string_value as document
                    FROM embedding_metadata 
                    WHERE key = 'chroma:document'
                    AND (string_value LIKE '%Discord user%' 
                         OR string_value LIKE '%display name%'
                         OR string_value LIKE '%ID:%')
                """)
                
                for (document,) in cursor.fetchall():
                    extracted = self._parse_discord_document(document)
                    if extracted:
                        user_id, name = extracted
                        mappings[user_id] = name
                        print(f"Found mapping: {user_id} -> {name}")
                
        except Exception as e:
            print(f"❌ Error accessing ChromaDB: {e}")
            
        return mappings
    
    def _parse_discord_document(self, document: str) -> Optional[Tuple[str, str]]:
        """Parse a ChromaDB document to extract user ID and name"""
        
        # Pattern: "Discord user markanthony.art has Discord ID 672814231002939413"
        match = re.search(r'Discord user (\S+) has Discord ID (\d+)', document)
        if match:
            username, user_id = match.groups()
            return user_id, username
            
        # Pattern: "Discord user markanthony.art (ID: 672814231002939413) uses display name 'MarkAnthony'"
        match = re.search(r'Discord user \S+ \(ID: (\d+)\) uses display name [\'"]([^\'"]+)[\'"]', document)
        if match:
            user_id, display_name = match.groups()
            return user_id, display_name
            
        # Pattern: "Global fact: Discord user ... ID: number"
        match = re.search(r'ID:\s*(\d+).*?(\w+)', document)
        if match and 'Discord' in document:
            user_id, potential_name = match.groups()
            # Only use if it looks like a name (not a number or short code)
            if len(potential_name) > 2 and not potential_name.isdigit():
                return user_id, potential_name
                
        return None
    
    def apply_name_mappings(self, mappings: Dict[str, str]) -> int:
        """Apply the extracted name mappings to user profiles"""
        updated_count = 0
        
        for user_id, name in mappings.items():
            if self.db.update_user_name(user_id, name):
                updated_count += 1
                
        return updated_count
    
    def auto_update_names(self) -> int:
        """Automatically extract and apply names from ChromaDB"""
        print("🔍 Extracting names from ChromaDB...")
        mappings = self.extract_names_from_chromadb()
        
        if mappings:
            print(f"\n📝 Found {len(mappings)} name mappings")
            for user_id, name in mappings.items():
                print(f"   • {user_id} -> {name}")
            
            print(f"\n🔄 Applying updates...")
            updated_count = self.apply_name_mappings(mappings)
            print(f"✅ Updated {updated_count} user profiles")
            
            return updated_count
        else:
            print("❌ No name mappings found in ChromaDB")
            return 0

def main():
    extractor = DiscordNameExtractor()
    updated = extractor.auto_update_names()
    
    if updated > 0:
        print(f"\n🎉 Successfully updated {updated} user names!")
        print("Run 'python query_profiles.py list' to see the results")
    else:
        print("\n💡 No names were updated. You may need to manually set names using:")
        print("   python update_names.py interactive")

if __name__ == "__main__":
    main()
