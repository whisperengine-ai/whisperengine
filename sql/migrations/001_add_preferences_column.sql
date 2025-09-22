-- Migration: 001_add_preferences_column.sql
-- Date: September 22, 2025
-- Purpose: Add preferences column to user_profiles table with proper defaults and constraints

BEGIN;

-- Add preferences column if it doesn't exist
DO $$
BEGIN
    -- Check if column exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_profiles' 
        AND column_name = 'preferences'
    ) THEN
        -- Add the column
        ALTER TABLE user_profiles ADD COLUMN preferences JSONB DEFAULT '{}'::jsonb;
        RAISE NOTICE 'Added preferences column to user_profiles table';
    ELSE
        RAISE NOTICE 'Column preferences already exists in user_profiles table';
    END IF;
END $$;

-- Ensure the GIN index exists for preferences column
CREATE INDEX IF NOT EXISTS idx_user_profiles_preferences_gin
    ON user_profiles USING GIN (preferences);

-- Update any NULL preferences to empty JSON object
UPDATE user_profiles 
SET preferences = '{}'::jsonb 
WHERE preferences IS NULL;

-- Set NOT NULL constraint and default
ALTER TABLE user_profiles 
ALTER COLUMN preferences SET DEFAULT '{}'::jsonb;

-- Only add NOT NULL constraint if column doesn't already have it
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_profiles' 
        AND column_name = 'preferences' 
        AND is_nullable = 'YES'
    ) THEN
        ALTER TABLE user_profiles ALTER COLUMN preferences SET NOT NULL;
        RAISE NOTICE 'Set preferences column to NOT NULL';
    END IF;
END $$;

COMMIT;

-- Verify the changes
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'user_profiles' 
AND column_name = 'preferences';