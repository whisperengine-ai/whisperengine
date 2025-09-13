#!/usr/bin/env python3
"""
Show remaining facts for a user after cleanup
"""
import logging
from memory_manager import UserMemoryManager

logging.basicConfig(level=logging.INFO)

def show_user_facts(user_id: str):
    """Show all facts for a specific user"""
    try:
        memory_manager = UserMemoryManager()
        
        # Get all entries for this user
        results = memory_manager.collection.get(
            where={"user_id": user_id}
        )
        
        if not results['documents']:
            print(f"No entries found for user {user_id}")
            return
        
        print(f"Facts for user {user_id}:")
        print("=" * 50)
        
        fact_count = 0
        for i, doc in enumerate(results['documents']):
            metadata = results['metadatas'][i]
            
            # Only show user facts
            if metadata.get('type') == 'user_fact':
                fact_text = metadata.get('fact', doc)
                confidence = metadata.get('confidence', 'unknown')
                timestamp = metadata.get('timestamp', 'unknown')
                fact_count += 1
                print(f"{fact_count}. {fact_text}")
                print(f"   Confidence: {confidence}, Added: {timestamp}")
                print()
        
        if fact_count == 0:
            print("No user facts found.")
        else:
            print(f"Total facts: {fact_count}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    user_id = input("Enter user ID: ").strip()
    show_user_facts(user_id)
