#!/usr/bin/env python3
"""
Vector Episodic Data Analysis for Character Learning
Analyzes existing Qdrant vector data to understand episodic memory potential
"""

import asyncio
import os
import json
import statistics
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Set required environment variables for analysis
os.environ.setdefault('FASTEMBED_CACHE_PATH', '/tmp/fastembed_cache')
os.environ.setdefault('QDRANT_HOST', 'localhost')
os.environ.setdefault('QDRANT_PORT', '6334')
os.environ.setdefault('LLM_CHAT_MODEL', 'openrouter/anthropic/claude-3.5-sonnet')
os.environ.setdefault('OPENROUTER_API_KEY', 'dummy_key_for_analysis')

# Force localhost settings for local analysis
os.environ['QDRANT_HOST'] = 'localhost'
os.environ['QDRANT_PORT'] = '6334'

# Import WhisperEngine components
from src.memory.memory_protocol import create_memory_manager
from qdrant_client import QdrantClient
from qdrant_client.http import models

class VectorEpisodicDataAnalyzer:
    """Analyze existing vector data for episodic memory potential"""
    
    def __init__(self):
        self.qdrant_client = QdrantClient(
            host=os.getenv('QDRANT_HOST', 'localhost'),
            port=int(os.getenv('QDRANT_PORT', '6334')),
            timeout=30
        )
        self.analysis_results = {}
    
    async def get_all_collections(self):
        """Get all available Qdrant collections"""
        try:
            print(f"Connecting to Qdrant at {os.getenv('QDRANT_HOST', 'localhost')}:{os.getenv('QDRANT_PORT', '6334')}")
            collections = self.qdrant_client.get_collections()
            print(f"Successfully connected! Found {len(collections.collections)} collections")
            return [col.name for col in collections.collections]
        except Exception as e:
            print(f"Error getting collections: {e}")
            print(f"Connection details: host={os.getenv('QDRANT_HOST', 'localhost')}, port={os.getenv('QDRANT_PORT', '6334')}")
            return []
    
    async def analyze_collection_metadata(self, collection_name: str):
        """Analyze metadata structure and RoBERTa data in a collection"""
        print(f"\n🔍 Analyzing Collection: {collection_name}")
        print("=" * 60)
        
        try:
            # Get collection info
            collection_info = self.qdrant_client.get_collection(collection_name)
            point_count = collection_info.points_count or 0
            print(f"📊 Total Points: {point_count:,}")
            
            if point_count == 0:
                print("❌ Collection is empty")
                return {}
            
            # Sample points to analyze metadata structure
            sample_size = min(100, point_count)
            scroll_result = self.qdrant_client.scroll(
                collection_name=collection_name,
                limit=sample_size,
                with_payload=True,
                with_vectors=False
            )
            
            points = scroll_result[0]
            
            if not points:
                print("❌ No points retrieved")
                return {}
            
            # Analyze metadata patterns
            metadata_analysis = self._analyze_metadata_patterns(points)
            
            # Analyze RoBERTa emotional data
            roberta_analysis = self._analyze_roberta_patterns(points)
            
            # Analyze conversation patterns
            conversation_analysis = self._analyze_conversation_patterns(points)
            
            # Analyze memorable moment potential
            memorable_analysis = self._analyze_memorable_moments(points)
            
            collection_analysis = {
                'collection_name': collection_name,
                'total_points': point_count,
                'sample_size': len(points),
                'metadata_patterns': metadata_analysis,
                'roberta_patterns': roberta_analysis,
                'conversation_patterns': conversation_analysis,
                'memorable_moments': memorable_analysis
            }
            
            self._print_collection_summary(collection_analysis)
            return collection_analysis
            
        except Exception as e:
            print(f"❌ Error analyzing collection {collection_name}: {e}")
            return {}
    
    def _analyze_metadata_patterns(self, points):
        """Analyze metadata field patterns"""
        field_counts = defaultdict(int)
        field_types = defaultdict(set)
        
        for point in points:
            if point.payload:
                for field, value in point.payload.items():
                    field_counts[field] += 1
                    field_types[field].add(type(value).__name__)
        
        return {
            'total_fields': len(field_counts),
            'field_coverage': {field: (count / len(points)) * 100 
                             for field, count in field_counts.items()},
            'field_types': {field: list(types) for field, types in field_types.items()}
        }
    
    def _analyze_roberta_patterns(self, points):
        """Analyze RoBERTa emotional intelligence data patterns"""
        roberta_fields = [
            'roberta_confidence', 'emotion_variance', 'emotion_dominance',
            'emotional_intensity', 'is_multi_emotion', 'mixed_emotions',
            'all_emotions', 'secondary_emotion_1', 'secondary_emotion_2',
            'emotion_count', 'primary_emotion'
        ]
        
        roberta_data = defaultdict(list)
        roberta_coverage = {}
        emotion_distribution = defaultdict(int)
        
        for point in points:
            if point.payload:
                for field in roberta_fields:
                    if field in point.payload:
                        value = point.payload[field]
                        roberta_data[field].append(value)
                        
                        # Track emotion distribution
                        if field == 'primary_emotion' and value:
                            emotion_distribution[value] += 1
        
        # Calculate coverage and statistics
        for field in roberta_fields:
            roberta_coverage[field] = (len(roberta_data[field]) / len(points)) * 100
        
        # Statistical analysis of numeric fields
        numeric_stats = {}
        for field in ['roberta_confidence', 'emotion_variance', 'emotion_dominance', 'emotional_intensity']:
            if roberta_data[field]:
                values = [v for v in roberta_data[field] if isinstance(v, (int, float))]
                if values:
                    numeric_stats[field] = {
                        'mean': statistics.mean(values),
                        'median': statistics.median(values),
                        'min': min(values),
                        'max': max(values),
                        'std': statistics.stdev(values) if len(values) > 1 else 0
                    }
        
        return {
            'field_coverage': roberta_coverage,
            'numeric_statistics': numeric_stats,
            'emotion_distribution': dict(emotion_distribution),
            'high_confidence_ratio': len([v for v in roberta_data['roberta_confidence'] 
                                        if isinstance(v, (int, float)) and v > 0.8]) / max(len(roberta_data['roberta_confidence']), 1) * 100
        }
    
    def _analyze_conversation_patterns(self, points):
        """Analyze conversation flow and context patterns"""
        bot_names = defaultdict(int)
        user_counts = defaultdict(int)
        memory_types = defaultdict(int)
        recent_conversations = 0
        
        # Time analysis (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        for point in points:
            if point.payload:
                # Bot distribution
                if 'bot_name' in point.payload:
                    bot_names[point.payload['bot_name']] += 1
                
                # User distribution
                if 'user_id' in point.payload:
                    user_counts[point.payload['user_id']] += 1
                
                # Memory type distribution
                if 'memory_type' in point.payload:
                    memory_types[point.payload['memory_type']] += 1
                
                # Recent conversation analysis
                if 'timestamp' in point.payload:
                    try:
                        timestamp = datetime.fromisoformat(point.payload['timestamp'].replace('Z', '+00:00'))
                        if timestamp > thirty_days_ago:
                            recent_conversations += 1
                    except:
                        pass
        
        return {
            'bot_distribution': dict(bot_names),
            'unique_users': len(user_counts),
            'user_conversation_counts': dict(user_counts),
            'memory_type_distribution': dict(memory_types),
            'recent_conversations_30d': recent_conversations,
            'recent_ratio': (recent_conversations / len(points)) * 100
        }
    
    def _analyze_memorable_moments(self, points):
        """Analyze potential for memorable moments based on existing criteria"""
        memorable_candidates = []
        high_emotion_moments = 0
        multi_emotion_moments = 0
        high_confidence_moments = 0
        
        for point in points:
            if point.payload:
                score = 0
                criteria_met = []
                
                # High RoBERTa confidence (>0.8)
                roberta_conf = point.payload.get('roberta_confidence', 0)
                if isinstance(roberta_conf, (int, float)) and roberta_conf > 0.8:
                    score += 2
                    criteria_met.append('high_confidence')
                    high_confidence_moments += 1
                
                # High emotional intensity (>0.7)
                emotion_intensity = point.payload.get('emotional_intensity', 0)
                if isinstance(emotion_intensity, (int, float)) and emotion_intensity > 0.7:
                    score += 2
                    criteria_met.append('high_intensity')
                    high_emotion_moments += 1
                
                # Multi-emotion complexity
                is_multi = point.payload.get('is_multi_emotion', False)
                if is_multi:
                    score += 1
                    criteria_met.append('multi_emotion')
                    multi_emotion_moments += 1
                
                # Longer conversations (content length)
                content = point.payload.get('content', '')
                if len(str(content)) > 200:
                    score += 1
                    criteria_met.append('rich_content')
                
                # Personal information sharing
                content_lower = str(content).lower()
                personal_keywords = ['feel', 'think', 'remember', 'love', 'hate', 'excited', 'worried', 'hope']
                if any(keyword in content_lower for keyword in personal_keywords):
                    score += 1
                    criteria_met.append('personal_sharing')
                
                if score >= 3:  # Threshold for memorable moment
                    memorable_candidates.append({
                        'score': score,
                        'criteria': criteria_met,
                        'content_preview': str(content)[:100] + '...' if len(str(content)) > 100 else str(content),
                        'primary_emotion': point.payload.get('primary_emotion'),
                        'roberta_confidence': roberta_conf,
                        'emotional_intensity': emotion_intensity
                    })
        
        # Sort by score
        memorable_candidates.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'total_memorable_candidates': len(memorable_candidates),
            'memorable_ratio': (len(memorable_candidates) / len(points)) * 100,
            'high_confidence_moments': high_confidence_moments,
            'high_emotion_moments': high_emotion_moments,
            'multi_emotion_moments': multi_emotion_moments,
            'top_memorable_examples': memorable_candidates[:5]  # Top 5 examples
        }
    
    def _print_collection_summary(self, analysis):
        """Print formatted analysis summary"""
        print(f"\n📈 ANALYSIS SUMMARY for {analysis['collection_name']}")
        print("-" * 40)
        
        # Basic stats
        print(f"Total memories: {analysis['total_points']:,}")
        print(f"Sample analyzed: {analysis['sample_size']}")
        
        # RoBERTa coverage
        roberta = analysis['roberta_patterns']
        print(f"\n🧠 RoBERTa Emotional Intelligence:")
        print(f"  • High confidence memories (>0.8): {roberta.get('high_confidence_ratio', 0):.1f}%")
        print(f"  • Primary emotion coverage: {roberta['field_coverage'].get('primary_emotion', 0):.1f}%")
        print(f"  • Emotional intensity coverage: {roberta['field_coverage'].get('emotional_intensity', 0):.1f}%")
        
        # Top emotions
        emotions = roberta.get('emotion_distribution', {})
        if emotions:
            top_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"  • Top emotions: {', '.join([f'{emotion} ({count})' for emotion, count in top_emotions])}")
        
        # Conversation patterns
        conv = analysis['conversation_patterns']
        print(f"\n💬 Conversation Patterns:")
        print(f"  • Unique users: {conv['unique_users']}")
        print(f"  • Recent conversations (30d): {conv['recent_conversations_30d']} ({conv['recent_ratio']:.1f}%)")
        
        # Bot distribution
        bots = conv.get('bot_distribution', {})
        if bots:
            print(f"  • Bot distribution: {', '.join([f'{bot}: {count}' for bot, count in bots.items()])}")
        
        # Memorable moments
        memorable = analysis['memorable_moments']
        print(f"\n⭐ Memorable Moment Potential:")
        print(f"  • Memorable candidates: {memorable['total_memorable_candidates']} ({memorable['memorable_ratio']:.1f}%)")
        print(f"  • High confidence moments: {memorable['high_confidence_moments']}")
        print(f"  • High emotion moments: {memorable['high_emotion_moments']}")
        print(f"  • Multi-emotion moments: {memorable['multi_emotion_moments']}")
        
        # Top memorable examples
        if memorable['top_memorable_examples']:
            print(f"\n🎯 Top Memorable Examples:")
            for i, example in enumerate(memorable['top_memorable_examples'][:3], 1):
                print(f"  {i}. Score: {example['score']}, Emotion: {example['primary_emotion']}")
                print(f"     Criteria: {', '.join(example['criteria'])}")
                print(f"     Preview: {example['content_preview']}")
    
    async def run_full_analysis(self):
        """Run complete analysis across all collections"""
        print("🚀 WhisperEngine Vector Episodic Data Analysis")
        print("=" * 60)
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get all collections
        collections = await self.get_all_collections()
        
        if not collections:
            print("❌ No collections found in Qdrant")
            return
        
        print(f"\n📚 Found {len(collections)} collections:")
        for collection in collections:
            print(f"  • {collection}")
        
        # Analyze each collection
        self.analysis_results = {}
        for collection in collections:
            try:
                analysis = await self.analyze_collection_metadata(collection)
                if analysis:
                    self.analysis_results[collection] = analysis
            except Exception as e:
                print(f"❌ Failed to analyze {collection}: {e}")
        
        # Generate summary report
        await self.generate_summary_report()
    
    async def generate_summary_report(self):
        """Generate comprehensive summary across all collections"""
        print(f"\n\n🎯 EPISODIC MEMORY ANALYSIS SUMMARY")
        print("=" * 60)
        
        total_memories = sum(analysis['total_points'] for analysis in self.analysis_results.values())
        total_memorable = sum(analysis['memorable_moments']['total_memorable_candidates'] 
                            for analysis in self.analysis_results.values())
        
        print(f"Total memories across all characters: {total_memories:,}")
        print(f"Total memorable moment candidates: {total_memorable:,}")
        print(f"Overall memorable ratio: {(total_memorable / total_memories * 100) if total_memories > 0 else 0:.1f}%")
        
        # Character-specific insights
        print(f"\n🎭 Character-Specific Insights:")
        for collection_name, analysis in self.analysis_results.items():
            char_name = collection_name.replace('whisperengine_memory_', '').replace('chat_memories_', '').title()
            memorable_count = analysis['memorable_moments']['total_memorable_candidates']
            total_count = analysis['total_points']
            ratio = (memorable_count / total_count * 100) if total_count > 0 else 0
            
            print(f"  • {char_name}: {memorable_count} memorable moments from {total_count:,} total ({ratio:.1f}%)")
            
            # Top emotion for this character
            emotions = analysis['roberta_patterns'].get('emotion_distribution', {})
            if emotions:
                top_emotion = max(emotions.items(), key=lambda x: x[1])
                print(f"    Primary emotion: {top_emotion[0]} ({top_emotion[1]} occurrences)")
        
        # Recommendations
        print(f"\n💡 IMPLEMENTATION RECOMMENDATIONS:")
        print("1. 🎯 High-potential characters for episodic memory:")
        
        # Sort by memorable moment potential
        char_potential = []
        for collection_name, analysis in self.analysis_results.items():
            char_name = collection_name.replace('whisperengine_memory_', '').replace('chat_memories_', '').title()
            memorable_ratio = analysis['memorable_moments']['memorable_ratio']
            total_memorable = analysis['memorable_moments']['total_memorable_candidates']
            char_potential.append((char_name, memorable_ratio, total_memorable))
        
        char_potential.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        for i, (char_name, ratio, count) in enumerate(char_potential[:3], 1):
            print(f"   {i}. {char_name}: {ratio:.1f}% memorable ({count} candidates)")
        
        print("\n2. 🔧 Implementation priorities:")
        print("   • Start with characters having >15% memorable ratio")
        print("   • Focus on roberta_confidence > 0.8 memories first")
        print("   • Use emotional_intensity > 0.7 for moment selection")
        print("   • Multi-emotion moments provide richer context")
        
        print("\n3. 📊 Data quality observations:")
        
        # Average RoBERTa coverage
        avg_roberta_coverage = statistics.mean([
            analysis['roberta_patterns']['field_coverage'].get('primary_emotion', 0)
            for analysis in self.analysis_results.values()
        ])
        print(f"   • Average RoBERTa emotion coverage: {avg_roberta_coverage:.1f}%")
        
        # Average high confidence ratio
        avg_high_conf = statistics.mean([
            analysis['roberta_patterns'].get('high_confidence_ratio', 0)
            for analysis in self.analysis_results.values()
        ])
        print(f"   • Average high-confidence ratio: {avg_high_conf:.1f}%")
        
        print(f"\n✅ Analysis complete! Ready for PHASE 1A implementation.")

async def main():
    """Main analysis execution"""
    analyzer = VectorEpisodicDataAnalyzer()
    await analyzer.run_full_analysis()

if __name__ == "__main__":
    asyncio.run(main())