"""
Semantic Deduplication System for Memory Optimization
Prevents storage of redundant memories and improves retrieval quality
"""
import logging
import numpy as np
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

@dataclass
class MemoryFingerprint:
    """Compact representation of memory content for deduplication"""
    content_hash: str
    semantic_hash: str
    embedding_preview: List[float]  # First 10 dimensions for quick comparison
    content_length: int
    key_phrases: List[str]
    timestamp: str
    memory_type: str
    
class SemanticDeduplicator:
    """
    Advanced semantic deduplication system that prevents redundant memory storage
    while preserving meaningful variations and updates
    """
    
    def __init__(self, embedding_manager=None, similarity_threshold: float = 0.92):
        self.embedding_manager = embedding_manager
        self.similarity_threshold = similarity_threshold
        self.logger = logging.getLogger(__name__)
        
        # Deduplication cache and fingerprint storage
        self.memory_fingerprints: Dict[str, MemoryFingerprint] = {}
        self.content_clusters: Dict[str, List[str]] = {}  # cluster_id -> memory_ids
        self.similarity_cache: Dict[str, float] = {}  # (id1, id2) -> similarity
        
        # Configuration
        self.max_fingerprints = 10000
        self.fingerprint_ttl = timedelta(days=30)
        self.cluster_merge_threshold = 0.85
        self.min_content_length = 20
        
        # Performance tracking
        self.stats = {
            'duplicates_prevented': 0,
            'similarities_computed': 0,
            'cache_hits': 0,
            'clusters_created': 0
        }
    
    def should_store_memory(self, content: str, memory_type: str = "conversation", 
                          user_id: Optional[str] = None) -> Tuple[bool, Optional[str], float]:
        """
        Determine if a memory should be stored based on semantic similarity to existing memories
        
        Returns:
            (should_store, similar_memory_id, similarity_score)
        """
        _ = user_id  # Reserved for future user-specific deduplication rules
        if len(content.strip()) < self.min_content_length:
            return False, None, 0.0
        
        # Generate fingerprint for the new content
        fingerprint = self._generate_fingerprint(content, memory_type)
        
        # Check for exact content duplicates first (fast)
        exact_duplicate = self._find_exact_duplicate(fingerprint)
        if exact_duplicate:
            self.stats['duplicates_prevented'] += 1
            return False, exact_duplicate, 1.0
        
        # Check for semantic duplicates (slower but more thorough)
        similar_memory, similarity = self._find_semantic_duplicate(fingerprint)
        
        if similar_memory and similarity > self.similarity_threshold:
            self.stats['duplicates_prevented'] += 1
            self.logger.debug("Prevented duplicate memory storage: %.3f similarity", similarity)
            return False, similar_memory, similarity
        
        # Memory is unique enough to store
        return True, similar_memory, similarity
    
    def register_memory(self, memory_id: str, content: str, memory_type: str = "conversation") -> MemoryFingerprint:
        """
        Register a new memory and its fingerprint for future deduplication
        """
        fingerprint = self._generate_fingerprint(content, memory_type, memory_id)
        self.memory_fingerprints[memory_id] = fingerprint
        
        # Add to cluster or create new cluster
        self._update_clusters(memory_id, fingerprint)
        
        # Clean old fingerprints if needed
        self._cleanup_old_fingerprints()
        
        self.logger.debug("Registered memory fingerprint for %s", memory_id)
        return fingerprint
    
    def find_similar_memories(self, content: str, limit: int = 5, 
                            min_similarity: float = 0.7) -> List[Tuple[str, float]]:
        """
        Find memories that are semantically similar to the given content
        
        Returns:
            List of (memory_id, similarity_score) tuples
        """
        if not self.embedding_manager:
            return []
        
        try:
            # Generate embedding for input content
            query_embedding = self.embedding_manager.generate_embedding(content)
            if query_embedding is None:
                return []
            
            similar_memories = []
            
            # Compare with all stored fingerprints
            for memory_id, fingerprint in self.memory_fingerprints.items():
                try:
                    # Quick filter using embedding preview
                    preview_similarity = self._quick_similarity_check(query_embedding, fingerprint)
                    if preview_similarity < min_similarity - 0.1:  # Allow some margin for full comparison
                        continue
                    
                    # Full semantic comparison
                    memory_embedding = self.embedding_manager.generate_embedding(
                        self._reconstruct_content_from_fingerprint(fingerprint)
                    )
                    if memory_embedding is None:
                        continue
                    
                    similarity = self._compute_similarity(query_embedding, memory_embedding)
                    
                    if similarity >= min_similarity:
                        similar_memories.append((memory_id, similarity))
                        
                except (AttributeError, TypeError, ValueError) as e:
                    self.logger.debug("Error computing similarity for memory %s: %s", memory_id, str(e))
                    continue
            
            # Sort by similarity and return top results
            similar_memories.sort(key=lambda x: x[1], reverse=True)
            return similar_memories[:limit]
            
        except (AttributeError, TypeError) as e:
            self.logger.error("Error finding similar memories: %s", str(e))
            return []
    
    def get_cluster_memories(self, memory_id: str) -> List[str]:
        """Get all memories in the same cluster as the given memory"""
        for memory_ids in self.content_clusters.values():
            if memory_id in memory_ids:
                return memory_ids.copy()
        return [memory_id]
    
    def optimize_memory_storage(self, memory_ids: List[str]) -> Dict[str, Any]:
        """
        Analyze a set of memories and suggest optimizations
        """
        optimization_report = {
            'total_memories': len(memory_ids),
            'duplicate_groups': [],
            'suggested_merges': [],
            'space_savings_estimate': 0,
            'optimization_opportunities': []
        }
        
        if not memory_ids:
            return optimization_report
        
        # Find duplicate groups
        processed = set()
        for memory_id in memory_ids:
            if memory_id in processed or memory_id not in self.memory_fingerprints:
                continue
            
            similar_group = [memory_id]
            fingerprint = self.memory_fingerprints[memory_id]
            
            # Find all similar memories
            for other_id in memory_ids:
                if other_id == memory_id or other_id in processed:
                    continue
                
                if other_id in self.memory_fingerprints:
                    similarity = self._compute_fingerprint_similarity(
                        fingerprint, self.memory_fingerprints[other_id]
                    )
                    if similarity > 0.8:  # Lower threshold for optimization suggestions
                        similar_group.append(other_id)
            
            if len(similar_group) > 1:
                optimization_report['duplicate_groups'].append({
                    'memories': similar_group,
                    'estimated_similarity': self._estimate_group_similarity(similar_group)
                })
                processed.update(similar_group)
        
        # Calculate space savings
        total_groups = len(optimization_report['duplicate_groups'])
        if total_groups > 0:
            avg_group_size = sum(len(group['memories']) for group in optimization_report['duplicate_groups']) / total_groups
            optimization_report['space_savings_estimate'] = int((avg_group_size - 1) * total_groups)
        
        # Add optimization suggestions
        if optimization_report['space_savings_estimate'] > 10:
            optimization_report['optimization_opportunities'].append({
                'type': 'deduplication',
                'description': f"Remove {optimization_report['space_savings_estimate']} duplicate memories",
                'priority': 'high'
            })
        
        return optimization_report
    
    def _generate_fingerprint(self, content: str, memory_type: str, 
                            memory_id: Optional[str] = None) -> MemoryFingerprint:
        """Generate a compact fingerprint for memory content"""
        _ = memory_id  # Reserved for future memory-specific fingerprinting
        
        # Content hash for exact duplicate detection
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        # Semantic hash based on key phrases
        key_phrases = self._extract_key_phrases(content)
        semantic_content = ' '.join(sorted(key_phrases))
        semantic_hash = hashlib.md5(semantic_content.encode('utf-8')).hexdigest()
        
        # Embedding preview (first 10 dimensions for quick comparison)
        embedding_preview = []
        if self.embedding_manager:
            try:
                full_embedding = self.embedding_manager.generate_embedding(content)
                if full_embedding is not None:
                    embedding_preview = full_embedding[:10].tolist()
            except (AttributeError, TypeError, ValueError) as e:
                self.logger.debug("Failed to generate embedding preview: %s", str(e))
        
        return MemoryFingerprint(
            content_hash=content_hash,
            semantic_hash=semantic_hash,
            embedding_preview=embedding_preview,
            content_length=len(content),
            key_phrases=key_phrases,
            timestamp=datetime.now().isoformat(),
            memory_type=memory_type
        )
    
    def _extract_key_phrases(self, content: str) -> List[str]:
        """Extract key phrases for semantic hashing"""
        import re
        
        # Clean content
        content = re.sub(r'[^\w\s]', ' ', content.lower())
        words = content.split()
        
        # Filter out common words and short words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'us',
            'them', 'my', 'your', 'his', 'its', 'our', 'their', 'this',
            'that', 'these', 'those', 'am', 'can', 'may', 'might', 'must'
        }
        
        key_words = [word for word in words 
                    if len(word) > 3 and word not in stop_words]
        
        # Create phrases from consecutive key words
        phrases = []
        for i in range(len(key_words)):
            # Single words
            phrases.append(key_words[i])
            
            # Two-word phrases
            if i < len(key_words) - 1:
                phrases.append(f"{key_words[i]} {key_words[i+1]}")
        
        # Return most significant phrases
        from collections import Counter
        phrase_counts = Counter(phrases)
        return [phrase for phrase, count in phrase_counts.most_common(10)]
    
    def _find_exact_duplicate(self, fingerprint: MemoryFingerprint) -> Optional[str]:
        """Find exact content duplicates using content hash"""
        for memory_id, stored_fingerprint in self.memory_fingerprints.items():
            if stored_fingerprint.content_hash == fingerprint.content_hash:
                return memory_id
        return None
    
    def _find_semantic_duplicate(self, fingerprint: MemoryFingerprint) -> Tuple[Optional[str], float]:
        """Find semantic duplicates using embedding similarity"""
        if not self.embedding_manager or not fingerprint.embedding_preview:
            return None, 0.0
        
        best_similarity = 0.0
        best_match = None
        
        for memory_id, stored_fingerprint in self.memory_fingerprints.items():
            if not stored_fingerprint.embedding_preview:
                continue
            
            # Quick similarity check using preview
            preview_similarity = self._quick_similarity_check_previews(
                fingerprint.embedding_preview, stored_fingerprint.embedding_preview
            )
            
            if preview_similarity > self.similarity_threshold - 0.1:  # Allow margin for full check
                # More detailed similarity computation would go here
                # For now, use the preview similarity as approximation
                if preview_similarity > best_similarity:
                    best_similarity = preview_similarity
                    best_match = memory_id
        
        return best_match, best_similarity
    
    def _quick_similarity_check(self, query_embedding: np.ndarray, 
                              fingerprint: MemoryFingerprint) -> float:
        """Quick similarity check using embedding preview"""
        if not fingerprint.embedding_preview:
            return 0.0
        
        query_preview = query_embedding[:10] if len(query_embedding) >= 10 else query_embedding
        return self._quick_similarity_check_previews(query_preview.tolist(), fingerprint.embedding_preview)
    
    def _quick_similarity_check_previews(self, preview1: List[float], preview2: List[float]) -> float:
        """Compute cosine similarity between two embedding previews"""
        if not preview1 or not preview2:
            return 0.0
        
        try:
            # Ensure same length
            min_len = min(len(preview1), len(preview2))
            p1 = np.array(preview1[:min_len])
            p2 = np.array(preview2[:min_len])
            
            # Compute cosine similarity
            norm1 = np.linalg.norm(p1)
            norm2 = np.linalg.norm(p2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(np.dot(p1, p2) / (norm1 * norm2))
            
        except (ValueError, TypeError, ZeroDivisionError):
            return 0.0
    
    def _compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two full embeddings"""
        try:
            # Reshape to 2D arrays for cosine_similarity
            emb1_2d = embedding1.reshape(1, -1)
            emb2_2d = embedding2.reshape(1, -1)
            similarity_matrix = cosine_similarity(emb1_2d, emb2_2d)
            return float(similarity_matrix[0][0])
        except (ValueError, TypeError, AttributeError):
            return 0.0
    
    def _compute_fingerprint_similarity(self, fp1: MemoryFingerprint, fp2: MemoryFingerprint) -> float:
        """Compute similarity between two fingerprints"""
        
        # Exact match
        if fp1.content_hash == fp2.content_hash:
            return 1.0
        
        # Semantic similarity based on key phrases
        phrases1 = set(fp1.key_phrases)
        phrases2 = set(fp2.key_phrases)
        
        if not phrases1 or not phrases2:
            return 0.0
        
        intersection = len(phrases1.intersection(phrases2))
        union = len(phrases1.union(phrases2))
        jaccard_similarity = intersection / union if union > 0 else 0.0
        
        # Embedding preview similarity
        embedding_similarity = self._quick_similarity_check_previews(
            fp1.embedding_preview, fp2.embedding_preview
        )
        
        # Combined similarity (weighted average)
        return 0.4 * jaccard_similarity + 0.6 * embedding_similarity
    
    def _update_clusters(self, memory_id: str, fingerprint: MemoryFingerprint):
        """Update memory clusters with new memory"""
        best_cluster = None
        best_similarity = 0.0
        
        # Find the best matching cluster
        for cluster_id, cluster_memory_ids in self.content_clusters.items():
            if not cluster_memory_ids:
                continue
            
            # Check similarity with cluster representative (first memory)
            rep_id = cluster_memory_ids[0]
            if rep_id in self.memory_fingerprints:
                similarity = self._compute_fingerprint_similarity(
                    fingerprint, self.memory_fingerprints[rep_id]
                )
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_cluster = cluster_id
        
        # Add to best cluster or create new one
        if best_cluster and best_similarity > self.cluster_merge_threshold:
            self.content_clusters[best_cluster].append(memory_id)
        else:
            # Create new cluster
            cluster_id = f"cluster_{len(self.content_clusters)}"
            self.content_clusters[cluster_id] = [memory_id]
            self.stats['clusters_created'] += 1
    
    def _cleanup_old_fingerprints(self):
        """Remove old fingerprints to prevent memory bloat"""
        if len(self.memory_fingerprints) <= self.max_fingerprints:
            return
        
        # Remove oldest fingerprints
        cutoff_time = datetime.now() - self.fingerprint_ttl
        to_remove = []
        
        for memory_id, fingerprint in self.memory_fingerprints.items():
            try:
                timestamp = datetime.fromisoformat(fingerprint.timestamp)
                if timestamp < cutoff_time:
                    to_remove.append(memory_id)
            except (ValueError, TypeError):
                # Remove invalid timestamps
                to_remove.append(memory_id)
        
        # Remove from fingerprints and clusters
        for memory_id in to_remove:
            del self.memory_fingerprints[memory_id]
            
            # Remove from clusters
            for cluster_id, cluster_memories in self.content_clusters.items():
                if memory_id in cluster_memories:
                    cluster_memories.remove(memory_id)
                    if not cluster_memories:  # Empty cluster
                        del self.content_clusters[cluster_id]
                    break
        
        if to_remove:
            self.logger.debug("Cleaned up %d old memory fingerprints", len(to_remove))
    
    def _reconstruct_content_from_fingerprint(self, fingerprint: MemoryFingerprint) -> str:
        """Reconstruct approximate content from fingerprint (for similarity comparison)"""
        # This is a simplified reconstruction - in practice, you might store more content
        return ' '.join(fingerprint.key_phrases)
    
    def _estimate_group_similarity(self, memory_ids: List[str]) -> float:
        """Estimate average similarity within a group of memories"""
        if len(memory_ids) < 2:
            return 1.0
        
        similarities = []
        for i in range(len(memory_ids)):
            for j in range(i + 1, len(memory_ids)):
                id1, id2 = memory_ids[i], memory_ids[j]
                if id1 in self.memory_fingerprints and id2 in self.memory_fingerprints:
                    similarity = self._compute_fingerprint_similarity(
                        self.memory_fingerprints[id1], self.memory_fingerprints[id2]
                    )
                    similarities.append(similarity)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def get_deduplication_stats(self) -> Dict[str, Any]:
        """Get statistics about deduplication performance"""
        return {
            'total_fingerprints': len(self.memory_fingerprints),
            'total_clusters': len(self.content_clusters),
            'duplicates_prevented': self.stats['duplicates_prevented'],
            'similarities_computed': self.stats['similarities_computed'],
            'cache_hits': self.stats['cache_hits'],
            'clusters_created': self.stats['clusters_created'],
            'average_cluster_size': (
                sum(len(cluster) for cluster in self.content_clusters.values()) / 
                len(self.content_clusters)
            ) if self.content_clusters else 0,
            'similarity_threshold': self.similarity_threshold
        }