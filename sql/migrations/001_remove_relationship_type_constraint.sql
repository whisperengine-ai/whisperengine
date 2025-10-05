-- Migration: Remove overly strict relationship_type CHECK constraint
-- Date: 2025-10-05
-- Reason: Constraint was too rigid and error-prone, blocking natural language evolution

-- Drop the old constraint
ALTER TABLE user_fact_relationships 
DROP CONSTRAINT IF EXISTS user_fact_relationships_relationship_type_check;

-- Add flexible validation (just ensure non-empty and reasonable length)
ALTER TABLE user_fact_relationships 
ADD CONSTRAINT user_fact_relationships_relationship_type_check 
CHECK (LENGTH(relationship_type) > 0 AND LENGTH(relationship_type) <= 50);

-- Comment explaining the change
COMMENT ON COLUMN user_fact_relationships.relationship_type IS 
'Flexible relationship type field (e.g., likes, dislikes, enjoys, knows, visited, wants, owns, prefers, interested_in, loves, etc.)';
