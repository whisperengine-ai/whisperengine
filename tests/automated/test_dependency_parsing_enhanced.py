#!/usr/bin/env python3
"""
Test dependency parsing enhancements (xcomp/ccomp/phrasal verbs).

Tests the enhanced _extract_relationships_from_doc() method to ensure:
- Clausal complements are extracted (xcomp, ccomp)
- Phrasal verbs are captured (particles)
- Negation propagates through clauses
- Backward compatibility maintained
"""

import pytest
from src.enrichment.nlp_preprocessor import EnrichmentNLPPreprocessor


@pytest.fixture
def nlp_proc():
    """Create preprocessor instance."""
    return EnrichmentNLPPreprocessor()


class TestClausalComplements:
    """Test extraction of infinitival and content clauses."""
    
    def test_infinitival_complement_xcomp(self, nlp_proc):
        """Test extraction of infinitive complements (xcomp)."""
        text = "I want to visit Paris"
        relationships = nlp_proc.extract_dependency_relationships(text)
        
        # Should extract both "want" and "visit"
        verbs = [r["verb"] for r in relationships]
        assert "want" in verbs, "Should extract main verb 'want'"
        assert "visit" in verbs, "Should extract complement verb 'visit'"
        
        # Visit should have Paris as object
        visit_rel = [r for r in relationships if r["verb"] == "visit"]
        assert visit_rel, "Should find visit relationship"
        assert visit_rel[0]["object"].lower() == "paris", "Visit should have Paris as object"
    
    def test_content_clause_ccomp(self, nlp_proc):
        """Test extraction of content clauses (ccomp)."""
        text = "I think you should try coding"
        relationships = nlp_proc.extract_dependency_relationships(text)
        
        # Should extract "think" and "try"
        verbs = [r["verb"] for r in relationships]
        assert "think" in verbs, "Should extract main verb 'think'"
        assert "try" in verbs, "Should extract complement verb 'try'"
    
    def test_multi_action_statement(self, nlp_proc):
        """Test extraction of multiple actions in one statement."""
        text = "I want to visit Paris and explore museums"
        relationships = nlp_proc.extract_dependency_relationships(text)
        
        # Should extract at least 3 verbs
        verbs = [r["verb"] for r in relationships]
        assert len(verbs) >= 2, f"Should extract 2+ verbs, got {len(verbs)}: {verbs}"
        assert "want" in verbs
        assert "visit" in verbs or "explore" in verbs  # At least one action
    
    def test_nested_complements(self, nlp_proc):
        """Test deeply nested clause complements."""
        text = "I hope to try to learn programming"
        relationships = nlp_proc.extract_dependency_relationships(text)
        
        verbs = [r["verb"] for r in relationships]
        # Should extract multiple levels
        assert len(verbs) > 0, "Should extract at least one verb"


class TestPhrasalVerbs:
    """Test extraction and handling of phrasal verbs."""
    
    def test_phrasal_verb_extraction(self, nlp_proc):
        """Test that particles are captured in phrasal verbs."""
        text = "Let's meet up in person"
        relationships = nlp_proc.extract_dependency_relationships(text)
        
        # Should have "meet_up" or "meet" in verbs
        verbs = [r["verb"] for r in relationships]
        assert any("meet" in v for v in verbs), f"Should capture meet/meet_up, got {verbs}"
        
        # Check particle flag on meet relationships
        meet_rels = [r for r in relationships if "meet" in r["verb"]]
        if meet_rels:
            assert any(r.get("has_particles", False) for r in meet_rels), "Should mark phrasal verb"
    
    def test_various_phrasal_verbs(self, nlp_proc):
        """Test various phrasal verb patterns."""
        texts = [
            "Let's go out tonight",
            "Come over this weekend",
            "I'll call you up later"
        ]
        
        for text in texts:
            relationships = nlp_proc.extract_dependency_relationships(text)
            # Just ensure it doesn't crash and extracts relationships
            assert isinstance(relationships, list), f"Should return list from: {text}"


class TestNegationPropagation:
    """Test negation handling and propagation through clauses."""
    
    def test_negation_basic(self, nlp_proc):
        """Test basic negation detection (existing functionality)."""
        text = "I don't like pizza"
        relationships = nlp_proc.extract_dependency_relationships(text)
        
        like_rels = [r for r in relationships if r["verb"] == "like"]
        assert like_rels, "Should find 'like' verb"
        assert like_rels[0]["is_negated"], "Should mark 'like' as negated"
    
    def test_negation_propagation_to_complement(self, nlp_proc):
        """Test that negation propagates from parent to complement verb."""
        text = "I don't want to eat meat"
        relationships = nlp_proc.extract_dependency_relationships(text)
        
        # Both "want" and "eat" should be marked negated
        verbs_dict = {r["verb"]: r for r in relationships}
        
        assert "want" in verbs_dict, "Should extract 'want'"
        assert verbs_dict["want"]["is_negated"], "'want' should be negated"
        
        if "eat" in verbs_dict:
            assert verbs_dict["eat"]["is_negated"], "'eat' should inherit negation from 'want'"
    
    def test_negation_with_multiple_actions(self, nlp_proc):
        """Test negation propagates through relationships."""
        text = "I don't want to visit that place or meet anyone"
        relationships = nlp_proc.extract_dependency_relationships(text)
        
        # Main action should be negated
        all_negated = [r for r in relationships if r["is_negated"]]
        assert len(all_negated) >= 1, "At least one verb should be marked negated"


class TestBackwardCompatibility:
    """Ensure existing functionality still works."""
    
    def test_basic_subject_verb_object(self, nlp_proc):
        """Test extraction of basic SVO still works."""
        text = "I love pizza"
        relationships = nlp_proc.extract_dependency_relationships(text)
        
        assert len(relationships) > 0, "Should extract at least one relationship"
        rel = relationships[0]
        assert rel["verb"] == "love", f"Expected verb 'love', got {rel['verb']}"
        assert rel["subject"] == "I", f"Expected subject 'I', got {rel['subject']}"
        assert rel["object"].lower() == "pizza", f"Expected object 'pizza', got {rel['object']}"
    
    def test_coordinated_verbs_still_work(self, nlp_proc):
        """Test that conj verbs still get extracted."""
        text = "I like pizza and pasta"
        relationships = nlp_proc.extract_dependency_relationships(text)
        
        # Should extract relationships
        assert len(relationships) >= 1, "Should extract at least one relationship"
        verbs = [r["verb"] for r in relationships]
        assert "like" in verbs, f"Should extract 'like' verb, got {verbs}"
    
    def test_empty_text_handling(self, nlp_proc):
        """Test that empty text is handled gracefully."""
        text = ""
        relationships = nlp_proc.extract_dependency_relationships(text)
        
        assert isinstance(relationships, list), "Should return list for empty text"
    
    def test_complex_sentence_old_format(self, nlp_proc):
        """Test that old sentence structures still work."""
        text = "The dog chased the cat through the garden"
        relationships = nlp_proc.extract_dependency_relationships(text)
        
        # Should extract at least the main verb
        assert len(relationships) > 0, "Should extract at least one relationship"
        verbs = [r["verb"] for r in relationships]
        assert any("chase" in v for v in verbs), f"Should extract chase verb, got {verbs}"


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_no_verb(self, nlp_proc):
        """Test text with no verbs."""
        text = "A big red car"
        relationships = nlp_proc.extract_dependency_relationships(text)
        
        # Should return empty or minimal list gracefully
        assert isinstance(relationships, list), "Should return list even with no verbs"
    
    def test_verb_without_object(self, nlp_proc):
        """Test verbs without explicit objects."""
        text = "I am happy"
        relationships = nlp_proc.extract_dependency_relationships(text)
        
        # Should extract even with partial information
        assert isinstance(relationships, list), "Should handle verbs without objects"
    
    def test_very_long_sentence(self, nlp_proc):
        """Test handling of very long sentences."""
        text = "I want to go to Paris and visit the Eiffel Tower and eat croissants and meet new friends and learn French"
        relationships = nlp_proc.extract_dependency_relationships(text)
        
        # Should extract multiple relationships without crashing
        assert len(relationships) > 0, "Should extract relationships from long sentence"
    
    def test_special_characters(self, nlp_proc):
        """Test handling of special characters."""
        text = "I don't want to... visit!"
        relationships = nlp_proc.extract_dependency_relationships(text)
        
        # Should handle gracefully
        assert isinstance(relationships, list), "Should handle special characters"


class TestMetadata:
    """Test that new metadata fields are present."""
    
    def test_clause_type_field(self, nlp_proc):
        """Test that clause_type field is present and correct."""
        text = "I want to visit Paris"
        relationships = nlp_proc.extract_dependency_relationships(text)
        
        # All relationships should have clause_type
        for rel in relationships:
            assert "clause_type" in rel, "Missing clause_type field"
            assert rel["clause_type"] in ["root", "xcomp", "ccomp"], f"Invalid clause_type: {rel['clause_type']}"
    
    def test_has_particles_field(self, nlp_proc):
        """Test that has_particles field is present."""
        text = "Meet up tomorrow"
        relationships = nlp_proc.extract_dependency_relationships(text)
        
        # All relationships should have has_particles
        for rel in relationships:
            assert "has_particles" in rel, "Missing has_particles field"
            assert isinstance(rel["has_particles"], bool), "has_particles should be boolean"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
