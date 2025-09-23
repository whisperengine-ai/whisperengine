-- Universal Identity System Database Tables
-- Creates tables for cross-platform user identity management

-- Universal Users Table
CREATE TABLE IF NOT EXISTS universal_users (
    universal_id VARCHAR(255) PRIMARY KEY,
    primary_username VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    email VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    preferences TEXT DEFAULT '{}',
    privacy_settings TEXT DEFAULT '{}'
);

-- Platform Identities Table
CREATE TABLE IF NOT EXISTS platform_identities (
    id SERIAL PRIMARY KEY,
    universal_id VARCHAR(255) NOT NULL REFERENCES universal_users(universal_id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    platform_user_id VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    email VARCHAR(255),
    verified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, platform_user_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_platform_identities_universal_id ON platform_identities(universal_id);
CREATE INDEX IF NOT EXISTS idx_platform_identities_platform_user ON platform_identities(platform, platform_user_id);
CREATE INDEX IF NOT EXISTS idx_universal_users_username ON universal_users(primary_username);
CREATE INDEX IF NOT EXISTS idx_universal_users_email ON universal_users(email);

-- Comments for documentation
COMMENT ON TABLE universal_users IS 'Universal user identities across all platforms';
COMMENT ON TABLE platform_identities IS 'Platform-specific identity mappings to universal users';
COMMENT ON COLUMN universal_users.universal_id IS 'Universal unique identifier (weu_* format)';
COMMENT ON COLUMN platform_identities.platform IS 'Platform name (discord, web_ui, etc.)';
COMMENT ON COLUMN platform_identities.platform_user_id IS 'Platform-specific user ID';