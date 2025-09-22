-- Migration: Add preferences column to user_profiles table
-- Date: September 22, 2025
-- Purpose: Fix "column 'preferences' does not exist" error in bot initialization

BEGIN;

-- Check if preferences column exists, if not add it
DO $$
BEGIN
    -- Try to add the preferences column
    BEGIN
        ALTER TABLE user_profiles ADD COLUMN preferences JSONB DEFAULT '{}'::jsonb;
        RAISE NOTICE 'Added preferences column to user_profiles table';
    EXCEPTION 
        WHEN duplicate_column THEN 
            RAISE NOTICE 'Column preferences already exists in user_profiles table';
    END;
END $$;

-- Ensure the GIN index exists for preferences column
CREATE INDEX IF NOT EXISTS idx_user_profiles_preferences_gin
    ON user_profiles USING GIN (preferences);

-- Update any NULL preferences to empty JSON object
UPDATE user_profiles 
SET preferences = '{}'::jsonb 
WHERE preferences IS NULL;

-- Add a constraint to ensure preferences is never NULL
ALTER TABLE user_profiles 
ALTER COLUMN preferences SET DEFAULT '{}'::jsonb,
ALTER COLUMN preferences SET NOT NULL;

COMMIT;

-- Verify the migration
\d user_profiles;