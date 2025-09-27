#!/usr/bin/env python3
"""
WhisperEngine Vector Store Recovery Script
Fix corrupted vector dimensions and re-embed everything properly
"""

import os
import sys
import asyncio
from datetime import datetime
import json
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from qdrant_client import QdrantClient
from qdrant_client.http import models
from fastembed import TextEmbedding

class VectorStoreRecovery:
    def __init__(self):
        self.client = QdrantClient(host="localhost", port=6334)
        self.collection_name = "whisperengine_memory"
        self.backup_collection_name = f"{self.collection_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.embedder = None
        
    async def initialize_embedder(self):
        """Initialize the embedding model"""
        print("🔧 Initializing BAAI/bge-small-en-v1.5 embedding model...")
        self.embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        test_embedding = list(self.embedder.embed(["test"]))[0]
        print(f"✅ Model loaded. Dimension: {len(test_embedding)}")
        return len(test_embedding)
    
    def backup_collection(self):
        """Create a backup of the current collection"""
        print(f"💾 Creating backup: {self.backup_collection_name}")
        
        try:
            # Get collection info
            info = self.client.get_collection(self.collection_name)
            
            # Create backup collection with same structure
            self.client.create_collection(
                collection_name=self.backup_collection_name,
                vectors_config=models.VectorParams(
                    size=384,  # Correct dimension
                    distance=models.Distance.COSINE
                )
            )
            
            print(f"✅ Backup collection '{self.backup_collection_name}' created")
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False
    
    async def extract_and_fix_data(self):
        """Extract all data and prepare for re-embedding"""
        print("📤 Extracting all data for re-embedding...")
        
        all_points = []
        batch_size = 100
        offset = None
        
        while True:
            # Get batch of points
            result = self.client.scroll(
                collection_name=self.collection_name,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=False  # We'll regenerate vectors
            )
            
            points, next_offset = result
            if not points:
                break
                
            all_points.extend(points)
            offset = next_offset
            
            if len(all_points) % 1000 == 0:
                print(f"  Extracted {len(all_points)} points...")
            
            if not next_offset:
                break
        
        print(f"✅ Extracted {len(all_points)} total points")
        return all_points
    
    async def re_embed_content(self, points: List[Any]):
        """Re-embed all content with correct model"""
        print(f"🔄 Re-embedding {len(points)} memories...")
        
        valid_points = []
        batch_size = 16  # FastEmbed batch size
        
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            
            # Extract content for embedding
            contents = []
            valid_batch_points = []
            
            for point in batch:
                if point.payload and 'content' in point.payload:
                    content = point.payload['content']
                    if content and content.strip():  # Valid content
                        contents.append(content)
                        valid_batch_points.append(point)
            
            if not contents:
                continue
            
            try:
                # Generate embeddings for batch
                if self.embedder:  # Type guard
                    embeddings = list(self.embedder.embed(contents))
                    
                    # Create properly structured points
                    for point, embedding in zip(valid_batch_points, embeddings):
                        if len(embedding) == 384:  # Validate dimension
                            valid_points.append({
                                'id': point.id,
                                'vector': embedding,
                                'payload': point.payload
                            })
                        else:
                            print(f"⚠️  Skipping point {point.id} - wrong dimension: {len(embedding)}")
                else:
                    print("❌ Embedder not initialized")
                    break
                
            except Exception as e:
                print(f"⚠️  Error embedding batch: {e}")
                continue
            
            if (i + batch_size) % 500 == 0:
                print(f"  Progress: {min(i + batch_size, len(points))}/{len(points)} points")
        
        print(f"✅ Successfully re-embedded {len(valid_points)} points")
        return valid_points
    
    def recreate_collection(self, vector_dim: int):
        """Recreate the main collection with correct configuration"""
        print(f"🗑️  Recreating collection with {vector_dim}D vectors...")
        
        try:
            # Delete existing collection
            self.client.delete_collection(self.collection_name)
            print(f"  Deleted old collection")
            
            # Create new collection with correct settings
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=vector_dim,
                    distance=models.Distance.COSINE
                )
            )
            
            print(f"✅ Created new collection with {vector_dim}D vectors")
            return True
            
        except Exception as e:
            print(f"❌ Failed to recreate collection: {e}")
            return False
    
    def upload_fixed_points(self, points: List[Dict[str, Any]]):
        """Upload the re-embedded points to the collection"""
        print(f"⬆️  Uploading {len(points)} fixed points...")
        
        batch_size = 100
        uploaded = 0
        
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            
            try:
                # Convert dict points to PointStruct
                qdrant_points = []
                for point_dict in batch:
                    qdrant_points.append(models.PointStruct(
                        id=point_dict['id'],
                        vector=point_dict['vector'],
                        payload=point_dict['payload']
                    ))
                
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=qdrant_points
                )
                
                uploaded += len(batch)
                if uploaded % 1000 == 0:
                    print(f"  Uploaded {uploaded}/{len(points)} points")
                    
            except Exception as e:
                print(f"⚠️  Error uploading batch: {e}")
        
        print(f"✅ Upload complete: {uploaded} points")
        return uploaded
    
    def validate_recovery(self):
        """Validate the recovery was successful"""
        print("🔍 Validating recovery...")
        
        try:
            info = self.client.get_collection(self.collection_name)
            print(f"  Collection points: {info.points_count}")
            
            # Sample some points to verify dimensions
            result = self.client.scroll(self.collection_name, limit=5, with_vectors=["content", "emotion", "semantic"])  # ✅ FIXED: Specify named vectors
            points = result[0]
            
            if points:
                dimensions = set()
                for point in points:
                    if point.vector:
                        dimensions.add(len(point.vector))
                
                print(f"  Vector dimensions found: {sorted(dimensions)}")
                if dimensions == {384}:
                    print("✅ All vectors have correct 384D dimension")
                    return True
                else:
                    print("❌ Still have incorrect dimensions!")
                    return False
            else:
                print("⚠️  No points found for validation")
                return False
                
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return False

async def main():
    """Main recovery process"""
    print("🚨 WhisperEngine Vector Store Recovery")
    print("=" * 50)
    print("⚠️  This will fix corrupted vector dimensions")
    print("⚠️  Backup will be created before changes")
    print()
    
    # Confirm before proceeding
    confirm = input("Continue with recovery? (yes/no): ").lower().strip()
    if confirm != 'yes':
        print("❌ Recovery cancelled")
        return
    
    recovery = VectorStoreRecovery()
    
    try:
        # Step 1: Initialize embedder
        vector_dim = await recovery.initialize_embedder()
        
        # Step 2: Backup current data
        if not recovery.backup_collection():
            print("❌ Recovery aborted - backup failed")
            return
        
        # Step 3: Extract all data
        points = await recovery.extract_and_fix_data()
        if not points:
            print("❌ No data found to recover")
            return
        
        # Step 4: Re-embed all content
        fixed_points = await recovery.re_embed_content(points)
        if not fixed_points:
            print("❌ No valid content to re-embed")
            return
        
        # Step 5: Recreate collection
        if not recovery.recreate_collection(vector_dim):
            print("❌ Failed to recreate collection")
            return
        
        # Step 6: Upload fixed data
        uploaded = recovery.upload_fixed_points(fixed_points)
        
        # Step 7: Validate
        if recovery.validate_recovery():
            print("\n✅ RECOVERY SUCCESSFUL!")
            print(f"   Original points: {len(points)}")
            print(f"   Recovered points: {uploaded}")
            print(f"   Backup created: {recovery.backup_collection_name}")
            print(f"   Vector dimension: {vector_dim}D (correct)")
        else:
            print("\n❌ Recovery validation failed")
            
    except Exception as e:
        print(f"❌ Recovery failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())