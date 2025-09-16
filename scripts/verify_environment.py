"""
Environment Verification Script for AI Memory Enhancement

This script verifies that all required dependencies and models are properly installed
and functional for the AI memory enhancement project.

Usage: python scripts/verify_environment.py
"""

import asyncio
import logging
import sys
import traceback
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def verify_spacy() -> dict[str, Any]:
    """Verify spaCy installation and model availability."""
    try:
        import spacy

        # Check which models are available
        models_available = []
        models_tested = []

        # Try large model first
        try:
            nlp = spacy.load("en_core_web_lg")
            doc = nlp("This is a test sentence about technology and artificial intelligence.")
            entities = [ent.text for ent in doc.ents]
            models_available.append("en_core_web_lg")
            models_tested.append(
                {"model": "en_core_web_lg", "entities": entities, "status": "working"}
            )
        except OSError:
            models_tested.append({"model": "en_core_web_lg", "status": "not_found"})

        # Try small model as fallback
        try:
            nlp_sm = spacy.load("en_core_web_sm")
            doc_sm = nlp_sm("This is a test sentence about technology and artificial intelligence.")
            entities_sm = [ent.text for ent in doc_sm.ents]
            models_available.append("en_core_web_sm")
            models_tested.append(
                {"model": "en_core_web_sm", "entities": entities_sm, "status": "working"}
            )
        except OSError:
            models_tested.append({"model": "en_core_web_sm", "status": "not_found"})

        if models_available:
            return {
                "status": "success",
                "version": spacy.__version__,
                "models_available": models_available,
                "models_tested": models_tested,
                "recommended_model": models_available[0],  # First available (lg preferred)
                "functional": True,
            }
        else:
            return {
                "status": "error",
                "version": spacy.__version__,
                "models_available": [],
                "error": "No spaCy models found. Run: python -m spacy download en_core_web_sm",
                "functional": False,
            }

    except ImportError as e:
        return {"status": "error", "error": f"spaCy not installed: {e}", "functional": False}


async def verify_transformers() -> dict[str, Any]:
    """Verify transformers installation."""
    try:
        import transformers

        # Test basic import
        from transformers import AutoTokenizer

        return {"status": "success", "version": transformers.__version__, "functional": True}

    except ImportError as e:
        return {"status": "error", "error": f"Transformers not installed: {e}", "functional": False}


async def verify_sentence_transformers() -> dict[str, Any]:
    """Verify sentence-transformers installation."""
    try:
        from sentence_transformers import SentenceTransformer

        # Test model loading (this might take a moment on first run)
        try:
            model = SentenceTransformer("all-Mpnet-BASE-v2")

            # Test encoding
            test_sentence = "This is a test sentence."
            embedding = model.encode([test_sentence])

            return {
                "status": "success",
                "model": "all-Mpnet-BASE-v2",
                "embedding_dim": len(embedding[0]),
                "functional": True,
            }

        except Exception as e:
            return {"status": "warning", "error": f"Model loading failed: {e}", "functional": False}

    except ImportError as e:
        return {
            "status": "error",
            "error": f"Sentence-transformers not installed: {e}",
            "functional": False,
        }


async def verify_existing_systems() -> dict[str, Any]:
    """Verify existing bot systems are still functional."""
    try:
        # Test graph database connectivity
        try:
            from src.graph_database.neo4j_connector import Neo4jConnector

            connector = Neo4jConnector()
            await connector.verify_connection()
            graph_status = {"status": "success", "functional": True}
        except Exception as e:
            graph_status = {"status": "warning", "error": str(e), "functional": False}

        # Test memory system
        try:
            from src.memory.user_memory_manager import UserMemoryManager

            UserMemoryManager()
            # Basic initialization test
            memory_status = {"status": "success", "functional": True}
        except Exception as e:
            memory_status = {"status": "warning", "error": str(e), "functional": False}

        return {"graph_database": graph_status, "memory_system": memory_status}

    except Exception as e:
        return {"error": f"Failed to verify existing systems: {e}", "functional": False}


async def verify_advanced_topic_extractor() -> dict[str, Any]:
    """Verify the new Advanced Topic Extractor."""
    try:
        from src.analysis.advanced_topic_extractor import AdvancedTopicExtractor

        extractor = AdvancedTopicExtractor()
        await extractor.initialize()

        # Test extraction
        test_message = "I'm excited about working on AI projects with Python and machine learning!"
        result = await extractor.extract_topics_enhanced(test_message)

        return {
            "status": "success",
            "initialized": True,
            "test_entities": len(result["entities"]),
            "test_phrases": len(result["key_phrases"]),
            "processing_time": result["metadata"]["processing_time_seconds"],
            "functional": True,
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "functional": False,
        }


async def main():
    """Run all environment verification tests."""

    all_functional = True

    # Test 1: spaCy
    spacy_result = await verify_spacy()
    if spacy_result["functional"]:
        pass
    else:
        all_functional = False

    # Test 2: Transformers
    transformers_result = await verify_transformers()
    if transformers_result["functional"]:
        pass
    else:
        all_functional = False

    # Test 3: Sentence Transformers
    sentence_transformers_result = await verify_sentence_transformers()
    if sentence_transformers_result["functional"]:
        pass
    else:
        all_functional = False

    # Test 4: Existing Systems
    existing_result = await verify_existing_systems()
    if "graph_database" in existing_result:
        if existing_result["graph_database"]["functional"]:
            pass
        else:
            pass

        if existing_result["memory_system"]["functional"]:
            pass
        else:
            pass

    # Test 5: Advanced Topic Extractor
    extractor_result = await verify_advanced_topic_extractor()
    if extractor_result["functional"]:
        pass
    else:
        if "traceback" in extractor_result:
            pass
        all_functional = False

    # Summary
    if all_functional:
        pass
    else:
        pass

    return all_functional


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception:
        sys.exit(1)
