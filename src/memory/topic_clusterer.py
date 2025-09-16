"""
Advanced Topic Clustering System for Memory Organization
Groups conversations and memories by semantic topics for better retrieval
"""

import json
import logging
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any

import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


@dataclass
class TopicCluster:
    """Represents a topic cluster with associated memories"""

    cluster_id: str
    name: str
    description: str
    keywords: list[str]
    centroid_embedding: list[float]
    memory_ids: list[str]
    conversation_count: int
    last_updated: str
    confidence_score: float
    related_clusters: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TopicCluster":
        return cls(**data)


@dataclass
class MemoryTopicInfo:
    """Topic information for a specific memory"""

    memory_id: str
    primary_topic: str
    secondary_topics: list[str]
    topic_confidence: float
    keywords_extracted: list[str]
    embedding_vector: list[float]
    classification_timestamp: str


class AdvancedTopicClusterer:
    """
    Sophisticated topic clustering system that organizes memories by semantic topics
    for improved organization and retrieval
    """

    def __init__(self, embedding_manager=None, llm_client=None):
        self.embedding_manager = embedding_manager
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)

        # Topic storage
        self.topic_clusters: dict[str, TopicCluster] = {}
        self.memory_topic_info: dict[str, MemoryTopicInfo] = {}
        self.topic_embeddings: dict[str, np.ndarray] = {}

        # Configuration
        self.min_cluster_size = 3
        self.max_clusters = 50
        self.similarity_threshold = 0.75
        self.reclustering_interval = timedelta(days=7)
        self.keyword_extraction_limit = 10

        # Clustering algorithms
        self.clustering_method = "adaptive"  # "kmeans", "dbscan", "adaptive"
        self.auto_cluster_threshold = 0.3

        # Performance tracking
        self.stats = {
            "clusters_created": 0,
            "memories_clustered": 0,
            "reclusterings_performed": 0,
            "last_clustering": None,
        }

        # Topic keyword cache
        self.topic_keywords_cache = {}
        self.cache_ttl = timedelta(hours=6)

    async def classify_memory_topic(
        self, memory_id: str, content: str, existing_topics: list[str] | None = None
    ) -> MemoryTopicInfo:
        """
        Classify a memory into topic clusters and return topic information
        """
        self.logger.debug("Classifying topic for memory %s", memory_id)

        # Generate embedding for the content
        embedding = await self._get_content_embedding(content)
        if embedding is None:
            return self._create_default_topic_info(memory_id, content)

        # Extract keywords from content
        keywords = await self._extract_content_keywords(content)

        # Find best matching cluster
        best_cluster, confidence = await self._find_best_cluster_match(
            embedding, keywords, existing_topics
        )

        # Get secondary topic matches
        secondary_topics = await self._find_secondary_topics(
            embedding, best_cluster, existing_topics
        )

        # Create topic info
        topic_info = MemoryTopicInfo(
            memory_id=memory_id,
            primary_topic=best_cluster,
            secondary_topics=secondary_topics,
            topic_confidence=confidence,
            keywords_extracted=keywords,
            embedding_vector=embedding.tolist() if embedding is not None else [],
            classification_timestamp=datetime.now().isoformat(),
        )

        # Store the topic information
        self.memory_topic_info[memory_id] = topic_info

        # Update cluster membership
        await self._update_cluster_membership(memory_id, best_cluster, embedding, keywords)

        return topic_info

    async def get_topic_recommendations(
        self, content: str, limit: int = 5
    ) -> list[tuple[str, float]]:
        """
        Get topic recommendations for given content without storing
        """
        embedding = await self._get_content_embedding(content)
        if embedding is None:
            return []

        recommendations = []

        for cluster_id, cluster in self.topic_clusters.items():
            if cluster.centroid_embedding:
                centroid = np.array(cluster.centroid_embedding)
                similarity = self._compute_embedding_similarity(embedding, centroid)
                recommendations.append((cluster_id, similarity))

        # Sort by similarity and return top recommendations
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:limit]

    async def create_new_topic_cluster(
        self, name: str, initial_memories: list[str], description: str | None = None
    ) -> TopicCluster:
        """
        Create a new topic cluster with initial memories
        """
        cluster_id = f"topic_{len(self.topic_clusters)}_{name.lower().replace(' ', '_')}"

        # Collect embeddings and keywords from initial memories
        embeddings = []
        all_keywords = []

        for memory_id in initial_memories:
            if memory_id in self.memory_topic_info:
                topic_info = self.memory_topic_info[memory_id]
                if topic_info.embedding_vector:
                    embeddings.append(np.array(topic_info.embedding_vector))
                all_keywords.extend(topic_info.keywords_extracted)

        # Calculate centroid
        centroid_embedding = []
        if embeddings:
            centroid_embedding = np.mean(embeddings, axis=0).tolist()

        # Extract most common keywords
        keyword_counts = Counter(all_keywords)
        top_keywords = [
            kw for kw, count in keyword_counts.most_common(self.keyword_extraction_limit)
        ]

        # Generate description if not provided
        if not description:
            description = await self._generate_cluster_description(
                name, top_keywords, initial_memories
            )

        # Create cluster
        cluster = TopicCluster(
            cluster_id=cluster_id,
            name=name,
            description=description,
            keywords=top_keywords,
            centroid_embedding=centroid_embedding,
            memory_ids=initial_memories.copy(),
            conversation_count=len(initial_memories),
            last_updated=datetime.now().isoformat(),
            confidence_score=0.8,  # Start with high confidence for manually created clusters
            related_clusters=[],
        )

        self.topic_clusters[cluster_id] = cluster
        self.stats["clusters_created"] += 1

        # Update memory topic info to point to this cluster
        for memory_id in initial_memories:
            if memory_id in self.memory_topic_info:
                self.memory_topic_info[memory_id].primary_topic = cluster_id

        self.logger.info(
            "Created new topic cluster: %s with %d memories", name, len(initial_memories)
        )
        return cluster

    async def recluster_all_topics(self, force: bool = False) -> dict[str, Any]:
        """
        Perform complete reclustering of all topics using advanced algorithms
        """
        if not force and self.stats["last_clustering"]:
            last_clustering = datetime.fromisoformat(self.stats["last_clustering"])
            if datetime.now() - last_clustering < self.reclustering_interval:
                return {"status": "skipped", "reason": "too_recent"}

        self.logger.info("Starting complete topic reclustering")

        # Collect all embeddings and memory IDs
        embeddings = []
        memory_ids = []

        for memory_id, topic_info in self.memory_topic_info.items():
            if topic_info.embedding_vector:
                embeddings.append(np.array(topic_info.embedding_vector))
                memory_ids.append(memory_id)

        if len(embeddings) < self.min_cluster_size:
            return {"status": "insufficient_data", "memories": len(embeddings)}

        # Convert to numpy array
        embedding_matrix = np.array(embeddings)

        # Perform clustering based on selected method
        cluster_labels = await self._perform_clustering(embedding_matrix)

        # Create new clusters from results
        new_clusters = await self._create_clusters_from_labels(
            memory_ids, embeddings, cluster_labels
        )

        # Update storage
        old_cluster_count = len(self.topic_clusters)
        self.topic_clusters.clear()
        self.topic_clusters.update(new_clusters)

        # Update memory topic info
        await self._update_memory_cluster_assignments(memory_ids, cluster_labels)

        # Find related clusters
        await self._compute_cluster_relationships()

        # Update stats
        self.stats["reclusterings_performed"] += 1
        self.stats["last_clustering"] = datetime.now().isoformat()

        result = {
            "status": "completed",
            "old_clusters": old_cluster_count,
            "new_clusters": len(self.topic_clusters),
            "memories_processed": len(memory_ids),
            "clustering_method": self.clustering_method,
        }

        self.logger.info("Reclustering completed: %s", result)
        return result

    async def get_cluster_summary(self, cluster_id: str) -> dict[str, Any] | None:
        """
        Get comprehensive summary of a topic cluster
        """
        if cluster_id not in self.topic_clusters:
            return None

        cluster = self.topic_clusters[cluster_id]

        # Get recent memories from cluster
        recent_memories = []
        for memory_id in cluster.memory_ids[-10:]:  # Last 10 memories
            if memory_id in self.memory_topic_info:
                recent_memories.append(
                    {
                        "memory_id": memory_id,
                        "keywords": self.memory_topic_info[memory_id].keywords_extracted,
                        "confidence": self.memory_topic_info[memory_id].topic_confidence,
                    }
                )

        # Calculate cluster statistics
        total_keywords = []
        confidence_scores = []
        for memory_id in cluster.memory_ids:
            if memory_id in self.memory_topic_info:
                topic_info = self.memory_topic_info[memory_id]
                total_keywords.extend(topic_info.keywords_extracted)
                confidence_scores.append(topic_info.topic_confidence)

        keyword_frequency = Counter(total_keywords)
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        )

        return {
            "cluster_info": cluster.to_dict(),
            "statistics": {
                "total_memories": len(cluster.memory_ids),
                "average_confidence": avg_confidence,
                "top_keywords": dict(keyword_frequency.most_common(15)),
                "related_cluster_count": len(cluster.related_clusters),
            },
            "recent_memories": recent_memories,
            "last_updated": cluster.last_updated,
        }

    async def find_similar_clusters(
        self, cluster_id: str, limit: int = 5
    ) -> list[tuple[str, float]]:
        """
        Find clusters similar to the given cluster
        """
        if cluster_id not in self.topic_clusters:
            return []

        target_cluster = self.topic_clusters[cluster_id]
        if not target_cluster.centroid_embedding:
            return []

        target_embedding = np.array(target_cluster.centroid_embedding)
        similarities = []

        for other_id, other_cluster in self.topic_clusters.items():
            if other_id == cluster_id or not other_cluster.centroid_embedding:
                continue

            other_embedding = np.array(other_cluster.centroid_embedding)
            similarity = self._compute_embedding_similarity(target_embedding, other_embedding)
            similarities.append((other_id, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]

    async def merge_clusters(
        self, cluster_id1: str, cluster_id2: str, new_name: str | None = None
    ) -> str | None:
        """
        Merge two clusters into one
        """
        if cluster_id1 not in self.topic_clusters or cluster_id2 not in self.topic_clusters:
            return None

        cluster1 = self.topic_clusters[cluster_id1]
        cluster2 = self.topic_clusters[cluster_id2]

        # Create merged cluster
        merged_name = new_name or f"{cluster1.name} + {cluster2.name}"
        merged_id = f"merged_{len(self.topic_clusters)}_{merged_name.lower().replace(' ', '_')}"

        # Combine embeddings for new centroid
        embeddings1 = [
            np.array(self.memory_topic_info[mid].embedding_vector)
            for mid in cluster1.memory_ids
            if mid in self.memory_topic_info and self.memory_topic_info[mid].embedding_vector
        ]
        embeddings2 = [
            np.array(self.memory_topic_info[mid].embedding_vector)
            for mid in cluster2.memory_ids
            if mid in self.memory_topic_info and self.memory_topic_info[mid].embedding_vector
        ]

        all_embeddings = embeddings1 + embeddings2
        new_centroid = np.mean(all_embeddings, axis=0).tolist() if all_embeddings else []

        # Combine keywords
        all_keywords = cluster1.keywords + cluster2.keywords
        keyword_counts = Counter(all_keywords)
        merged_keywords = [
            kw for kw, count in keyword_counts.most_common(self.keyword_extraction_limit)
        ]

        # Create merged cluster
        merged_cluster = TopicCluster(
            cluster_id=merged_id,
            name=merged_name,
            description=f"Merged cluster: {cluster1.description} + {cluster2.description}",
            keywords=merged_keywords,
            centroid_embedding=new_centroid,
            memory_ids=cluster1.memory_ids + cluster2.memory_ids,
            conversation_count=cluster1.conversation_count + cluster2.conversation_count,
            last_updated=datetime.now().isoformat(),
            confidence_score=(cluster1.confidence_score + cluster2.confidence_score) / 2,
            related_clusters=list(set(cluster1.related_clusters + cluster2.related_clusters)),
        )

        # Update storage
        self.topic_clusters[merged_id] = merged_cluster
        del self.topic_clusters[cluster_id1]
        del self.topic_clusters[cluster_id2]

        # Update memory assignments
        for memory_id in merged_cluster.memory_ids:
            if memory_id in self.memory_topic_info:
                self.memory_topic_info[memory_id].primary_topic = merged_id

        self.logger.info("Merged clusters %s and %s into %s", cluster_id1, cluster_id2, merged_id)
        return merged_id

    # Private methods

    async def _get_content_embedding(self, content: str) -> np.ndarray | None:
        """Get embedding for content"""
        if not self.embedding_manager:
            return None

        try:
            embedding = self.embedding_manager.generate_embedding(content)
            return embedding if embedding is not None else None
        except Exception as e:
            self.logger.debug("Failed to generate embedding: %s", str(e))
            return None

    async def _extract_content_keywords(self, content: str) -> list[str]:
        """Extract keywords from content using multiple methods"""
        keywords = []

        # Method 1: LLM-based keyword extraction
        if self.llm_client:
            try:
                llm_keywords = await self._llm_extract_keywords(content)
                keywords.extend(llm_keywords)
            except Exception as e:
                self.logger.debug("LLM keyword extraction failed: %s", str(e))

        # Method 2: Statistical keyword extraction
        statistical_keywords = self._statistical_keyword_extraction(content)
        keywords.extend(statistical_keywords)

        # Deduplicate and limit
        unique_keywords = list(dict.fromkeys(keywords))  # Preserve order while deduplicating
        return unique_keywords[: self.keyword_extraction_limit]

    async def _llm_extract_keywords(self, content: str) -> list[str]:
        """Extract keywords using LLM"""
        prompt = f"""Extract the most important keywords and key phrases from this text.
        Focus on concrete topics, entities, and concepts.

        Text: {content[:1000]}

        Return only a JSON list of 5-10 keywords:
        ["keyword1", "keyword2", "keyword3"]"""

        messages = [
            {
                "role": "system",
                "content": "You are a keyword extraction expert. Return only valid JSON.",
            },
            {"role": "user", "content": prompt},
        ]

        response = self.llm_client.generate_facts_chat_completion(
            messages=messages, max_tokens=150, temperature=0.1
        )

        if isinstance(response, dict) and "choices" in response:
            response_text = response["choices"][0]["message"]["content"].strip()

            # Clean JSON response
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()

            keywords = json.loads(response_text)
            if isinstance(keywords, list):
                return [str(kw) for kw in keywords]

        return []

    def _statistical_keyword_extraction(self, content: str) -> list[str]:
        """Extract keywords using statistical methods"""
        import re
        from collections import Counter

        # Clean and tokenize
        content_clean = re.sub(r"[^\w\s]", " ", content.lower())
        words = content_clean.split()

        # Filter words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "me",
            "him",
            "us",
            "them",
            "my",
            "your",
            "his",
            "its",
            "our",
            "their",
            "this",
            "that",
            "these",
            "those",
            "am",
            "can",
            "may",
            "might",
            "must",
        }

        filtered_words = [word for word in words if len(word) > 3 and word not in stop_words]

        # Get most frequent words
        word_counts = Counter(filtered_words)
        return [word for word, count in word_counts.most_common(8)]

    async def _find_best_cluster_match(
        self,
        embedding: np.ndarray,
        keywords: list[str],
        existing_topics: list[str] | None = None,
    ) -> tuple[str, float]:
        """Find the best matching cluster for the given embedding and keywords"""
        if not self.topic_clusters:
            # Create first cluster
            return await self._create_initial_cluster(embedding, keywords), 1.0

        best_cluster = None
        best_score = 0.0

        for cluster_id, cluster in self.topic_clusters.items():
            if existing_topics and cluster_id not in existing_topics:
                continue

            score = await self._calculate_cluster_match_score(embedding, keywords, cluster)

            if score > best_score:
                best_score = score
                best_cluster = cluster_id

        # If no good match found, create new cluster
        if best_score < self.auto_cluster_threshold:
            new_cluster_id = await self._create_new_cluster_from_content(embedding, keywords)
            return new_cluster_id, 1.0

        return best_cluster, best_score

    async def _calculate_cluster_match_score(
        self, embedding: np.ndarray, keywords: list[str], cluster: TopicCluster
    ) -> float:
        """Calculate how well content matches a cluster"""
        scores = []

        # Embedding similarity
        if cluster.centroid_embedding:
            centroid = np.array(cluster.centroid_embedding)
            embedding_sim = self._compute_embedding_similarity(embedding, centroid)
            scores.append(embedding_sim * 0.7)  # Weight embedding similarity highly

        # Keyword overlap
        if keywords and cluster.keywords:
            keyword_overlap = len(set(keywords).intersection(set(cluster.keywords)))
            keyword_sim = keyword_overlap / max(len(keywords), len(cluster.keywords))
            scores.append(keyword_sim * 0.3)  # Weight keyword similarity lower

        return sum(scores) / len(scores) if scores else 0.0

    def _compute_embedding_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Compute cosine similarity between embeddings"""
        try:
            emb1_2d = emb1.reshape(1, -1)
            emb2_2d = emb2.reshape(1, -1)
            similarity = cosine_similarity(emb1_2d, emb2_2d)[0][0]
            return float(similarity)
        except Exception:
            return 0.0

    async def _find_secondary_topics(
        self,
        embedding: np.ndarray,
        primary_cluster: str,
        existing_topics: list[str] | None = None,
    ) -> list[str]:
        """Find secondary topic matches"""
        secondary = []

        for cluster_id, cluster in self.topic_clusters.items():
            if cluster_id == primary_cluster:
                continue
            if existing_topics and cluster_id not in existing_topics:
                continue

            if cluster.centroid_embedding:
                centroid = np.array(cluster.centroid_embedding)
                similarity = self._compute_embedding_similarity(embedding, centroid)

                if similarity > 0.5:  # Lower threshold for secondary topics
                    secondary.append(cluster_id)

        return secondary[:3]  # Limit to 3 secondary topics

    async def _create_initial_cluster(self, embedding: np.ndarray, keywords: list[str]) -> str:
        """Create the first cluster"""
        cluster_id = "topic_0_general"

        cluster = TopicCluster(
            cluster_id=cluster_id,
            name="General Discussion",
            description="General conversation topics",
            keywords=keywords,
            centroid_embedding=embedding.tolist(),
            memory_ids=[],
            conversation_count=0,
            last_updated=datetime.now().isoformat(),
            confidence_score=0.8,
            related_clusters=[],
        )

        self.topic_clusters[cluster_id] = cluster
        self.stats["clusters_created"] += 1
        return cluster_id

    async def _create_new_cluster_from_content(
        self, embedding: np.ndarray, keywords: list[str]
    ) -> str:
        """Create a new cluster from content that doesn't match existing clusters"""
        cluster_count = len(self.topic_clusters)
        cluster_name = keywords[0].title() if keywords else f"Topic {cluster_count}"
        cluster_id = f"topic_{cluster_count}_{cluster_name.lower().replace(' ', '_')}"

        description = (
            f"Cluster focused on {', '.join(keywords[:3])}" if keywords else "New topic cluster"
        )

        cluster = TopicCluster(
            cluster_id=cluster_id,
            name=cluster_name,
            description=description,
            keywords=keywords,
            centroid_embedding=embedding.tolist(),
            memory_ids=[],
            conversation_count=0,
            last_updated=datetime.now().isoformat(),
            confidence_score=0.6,  # Lower confidence for auto-created clusters
            related_clusters=[],
        )

        self.topic_clusters[cluster_id] = cluster
        self.stats["clusters_created"] += 1
        return cluster_id

    async def _update_cluster_membership(
        self, memory_id: str, cluster_id: str, embedding: np.ndarray, keywords: list[str]
    ):
        """Update cluster membership and centroid"""
        if cluster_id not in self.topic_clusters:
            return

        cluster = self.topic_clusters[cluster_id]

        # Add memory to cluster
        if memory_id not in cluster.memory_ids:
            cluster.memory_ids.append(memory_id)
            cluster.conversation_count += 1

        # Update cluster keywords
        all_keywords = cluster.keywords + keywords
        keyword_counts = Counter(all_keywords)
        cluster.keywords = [
            kw for kw, count in keyword_counts.most_common(self.keyword_extraction_limit)
        ]

        # Update centroid (running average)
        if cluster.centroid_embedding:
            current_centroid = np.array(cluster.centroid_embedding)
            # Simple running average (could be improved with more sophisticated updating)
            weight = 0.1  # Weight for new embedding
            new_centroid = (1 - weight) * current_centroid + weight * embedding
            cluster.centroid_embedding = new_centroid.tolist()
        else:
            cluster.centroid_embedding = embedding.tolist()

        cluster.last_updated = datetime.now().isoformat()
        self.stats["memories_clustered"] += 1

    def _create_default_topic_info(self, memory_id: str, content: str) -> MemoryTopicInfo:
        """Create default topic info when clustering fails"""
        return MemoryTopicInfo(
            memory_id=memory_id,
            primary_topic="uncategorized",
            secondary_topics=[],
            topic_confidence=0.5,
            keywords_extracted=self._statistical_keyword_extraction(content),
            embedding_vector=[],
            classification_timestamp=datetime.now().isoformat(),
        )

    async def _perform_clustering(self, embedding_matrix: np.ndarray) -> np.ndarray:
        """Perform clustering using the selected algorithm"""
        if self.clustering_method == "kmeans":
            return await self._kmeans_clustering(embedding_matrix)
        elif self.clustering_method == "dbscan":
            return await self._dbscan_clustering(embedding_matrix)
        else:  # adaptive
            return await self._adaptive_clustering(embedding_matrix)

    async def _kmeans_clustering(self, embedding_matrix: np.ndarray) -> np.ndarray:
        """Perform K-means clustering"""
        n_samples = embedding_matrix.shape[0]
        n_clusters = min(self.max_clusters, max(2, n_samples // 10))  # Adaptive cluster count

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embedding_matrix)

        return cluster_labels

    async def _dbscan_clustering(self, embedding_matrix: np.ndarray) -> np.ndarray:
        """Perform DBSCAN clustering"""
        # Automatically determine eps using distance analysis
        from sklearn.neighbors import NearestNeighbors

        neighbors = NearestNeighbors(n_neighbors=5)
        neighbors.fit(embedding_matrix)
        distances, indices = neighbors.kneighbors(embedding_matrix)
        distances = np.sort(distances, axis=0)
        distances = distances[:, 1]  # k-distance

        # Use knee point as eps
        eps = np.percentile(distances, 75)  # 75th percentile as heuristic

        dbscan = DBSCAN(eps=eps, min_samples=self.min_cluster_size)
        cluster_labels = dbscan.fit_predict(embedding_matrix)

        return cluster_labels

    async def _adaptive_clustering(self, embedding_matrix: np.ndarray) -> np.ndarray:
        """Perform adaptive clustering that chooses the best method"""
        # Try both methods and choose the one with better silhouette score
        try:
            from sklearn.metrics import silhouette_score

            kmeans_labels = await self._kmeans_clustering(embedding_matrix)
            dbscan_labels = await self._dbscan_clustering(embedding_matrix)

            kmeans_score = (
                silhouette_score(embedding_matrix, kmeans_labels)
                if len(set(kmeans_labels)) > 1
                else -1
            )
            dbscan_score = (
                silhouette_score(embedding_matrix, dbscan_labels)
                if len(set(dbscan_labels)) > 1
                else -1
            )

            if kmeans_score > dbscan_score:
                self.logger.debug("Selected K-means clustering (score: %.3f)", kmeans_score)
                return kmeans_labels
            else:
                self.logger.debug("Selected DBSCAN clustering (score: %.3f)", dbscan_score)
                return dbscan_labels

        except Exception as e:
            self.logger.debug("Adaptive clustering failed, using K-means: %s", str(e))
            return await self._kmeans_clustering(embedding_matrix)

    async def _create_clusters_from_labels(
        self, memory_ids: list[str], embeddings: list[np.ndarray], cluster_labels: np.ndarray
    ) -> dict[str, TopicCluster]:
        """Create TopicCluster objects from clustering results"""
        clusters = {}

        # Group memories by cluster label
        cluster_groups = defaultdict(list)
        cluster_embeddings = defaultdict(list)

        for i, label in enumerate(cluster_labels):
            if label != -1:  # Ignore noise points from DBSCAN
                cluster_groups[label].append(memory_ids[i])
                cluster_embeddings[label].append(embeddings[i])

        # Create cluster objects
        for label, memory_list in cluster_groups.items():
            if len(memory_list) < self.min_cluster_size:
                continue  # Skip small clusters

            cluster_id = f"auto_cluster_{label}"

            # Calculate centroid
            cluster_embs = cluster_embeddings[label]
            centroid = np.mean(cluster_embs, axis=0).tolist()

            # Collect keywords from all memories in cluster
            all_keywords = []
            for memory_id in memory_list:
                if memory_id in self.memory_topic_info:
                    all_keywords.extend(self.memory_topic_info[memory_id].keywords_extracted)

            keyword_counts = Counter(all_keywords)
            top_keywords = [
                kw for kw, count in keyword_counts.most_common(self.keyword_extraction_limit)
            ]

            # Generate cluster name from top keywords
            cluster_name = top_keywords[0].title() if top_keywords else f"Cluster {label}"

            # Generate description
            description = f"Auto-generated cluster with {len(memory_list)} memories"
            if top_keywords:
                description += f" focusing on {', '.join(top_keywords[:3])}"

            cluster = TopicCluster(
                cluster_id=cluster_id,
                name=cluster_name,
                description=description,
                keywords=top_keywords,
                centroid_embedding=centroid,
                memory_ids=memory_list,
                conversation_count=len(memory_list),
                last_updated=datetime.now().isoformat(),
                confidence_score=0.7,  # Medium confidence for auto-generated clusters
                related_clusters=[],
            )

            clusters[cluster_id] = cluster

        return clusters

    async def _update_memory_cluster_assignments(
        self, memory_ids: list[str], cluster_labels: np.ndarray
    ):
        """Update memory topic info with new cluster assignments"""
        for i, memory_id in enumerate(memory_ids):
            if memory_id in self.memory_topic_info:
                label = cluster_labels[i]
                if label != -1:  # Valid cluster
                    cluster_id = f"auto_cluster_{label}"
                    self.memory_topic_info[memory_id].primary_topic = cluster_id
                else:
                    self.memory_topic_info[memory_id].primary_topic = "uncategorized"

    async def _compute_cluster_relationships(self):
        """Compute relationships between clusters"""
        cluster_ids = list(self.topic_clusters.keys())

        for i, cluster_id1 in enumerate(cluster_ids):
            cluster1 = self.topic_clusters[cluster_id1]
            related = []

            for j, cluster_id2 in enumerate(cluster_ids):
                if i >= j:  # Avoid duplicates and self-comparison
                    continue

                cluster2 = self.topic_clusters[cluster_id2]

                if cluster1.centroid_embedding and cluster2.centroid_embedding:
                    emb1 = np.array(cluster1.centroid_embedding)
                    emb2 = np.array(cluster2.centroid_embedding)
                    similarity = self._compute_embedding_similarity(emb1, emb2)

                    if similarity > 0.6:  # Threshold for related clusters
                        related.append(cluster_id2)
                        # Also add reciprocal relationship
                        if cluster_id1 not in cluster2.related_clusters:
                            cluster2.related_clusters.append(cluster_id1)

            cluster1.related_clusters = related

    async def _generate_cluster_description(
        self, name: str, keywords: list[str], memory_ids: list[str]
    ) -> str:
        """Generate a description for a cluster using LLM"""
        if not self.llm_client:
            return f"Topic cluster focused on {name}"

        try:
            prompt = f"""Create a brief description for a conversation topic cluster.

            Cluster name: {name}
            Keywords: {', '.join(keywords[:5])}
            Number of conversations: {len(memory_ids)}

            Write a 1-2 sentence description that explains what this cluster is about."""

            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at creating concise, informative descriptions.",
                },
                {"role": "user", "content": prompt},
            ]

            response = self.llm_client.generate_facts_chat_completion(
                messages=messages, max_tokens=100, temperature=0.3
            )

            if isinstance(response, dict) and "choices" in response:
                description = response["choices"][0]["message"]["content"].strip()
                return description

        except Exception as e:
            self.logger.debug("LLM description generation failed: %s", str(e))

        return f"Topic cluster about {name} with {len(memory_ids)} conversations"

    def get_clustering_stats(self) -> dict[str, Any]:
        """Get comprehensive clustering statistics"""
        total_memories = len(self.memory_topic_info)
        clustered_memories = sum(
            1 for info in self.memory_topic_info.values() if info.primary_topic != "uncategorized"
        )

        cluster_sizes = [len(cluster.memory_ids) for cluster in self.topic_clusters.values()]
        avg_cluster_size = sum(cluster_sizes) / len(cluster_sizes) if cluster_sizes else 0

        confidence_scores = [info.topic_confidence for info in self.memory_topic_info.values()]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

        return {
            "total_clusters": len(self.topic_clusters),
            "total_memories": total_memories,
            "clustered_memories": clustered_memories,
            "clustering_rate": clustered_memories / total_memories if total_memories > 0 else 0,
            "average_cluster_size": avg_cluster_size,
            "largest_cluster_size": max(cluster_sizes) if cluster_sizes else 0,
            "smallest_cluster_size": min(cluster_sizes) if cluster_sizes else 0,
            "average_confidence": avg_confidence,
            "clusters_created": self.stats["clusters_created"],
            "reclusterings_performed": self.stats["reclusterings_performed"],
            "last_clustering": self.stats["last_clustering"],
            "clustering_method": self.clustering_method,
        }
