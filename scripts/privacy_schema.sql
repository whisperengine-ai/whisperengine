-- Privacy and Context Boundaries Database Schema
-- Add this to the existing PostgreSQL database

-- User Privacy Preferences Table
CREATE TABLE IF NOT EXISTS user_privacy_preferences (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    privacy_level TEXT NOT NULL DEFAULT 'moderate' CHECK (privacy_level IN ('strict', 'moderate', 'permissive')),
    allow_cross_server BOOLEAN DEFAULT FALSE,
    allow_dm_to_server BOOLEAN DEFAULT FALSE,
    allow_server_to_dm BOOLEAN DEFAULT FALSE,
    allow_private_to_public BOOLEAN DEFAULT FALSE,
    custom_rules JSONB DEFAULT '{}',
    consent_status TEXT NOT NULL DEFAULT 'not_asked' CHECK (consent_status IN ('not_asked', 'granted', 'denied', 'expired')),
    consent_timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key to users table if it exists
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Context Boundary Audit Log Table
CREATE TABLE IF NOT EXISTS context_boundary_audit (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    request_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source_context TEXT NOT NULL,
    target_context TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('allowed', 'blocked', 'consent_requested', 'allowed_once', 'denied_once', 'allowed_always', 'denied_always')),
    reason TEXT,
    privacy_level TEXT,
    
    -- Foreign key to users table if it exists
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_privacy_preferences_user_id ON user_privacy_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_privacy_preferences_privacy_level ON user_privacy_preferences(privacy_level);
CREATE INDEX IF NOT EXISTS idx_privacy_preferences_updated_at ON user_privacy_preferences(updated_at);

CREATE INDEX IF NOT EXISTS idx_audit_user_id ON context_boundary_audit(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON context_boundary_audit(request_timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_decision ON context_boundary_audit(decision);
CREATE INDEX IF NOT EXISTS idx_audit_source_target ON context_boundary_audit(source_context, target_context);

-- Auto-update timestamp trigger for privacy preferences
CREATE TRIGGER update_privacy_preferences_updated_at
    BEFORE UPDATE ON user_privacy_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create a view for recent audit activity
CREATE OR REPLACE VIEW recent_privacy_audit AS
SELECT 
    user_id,
    request_timestamp,
    source_context,
    target_context,
    decision,
    reason,
    privacy_level
FROM context_boundary_audit 
WHERE request_timestamp >= CURRENT_TIMESTAMP - INTERVAL '30 days'
ORDER BY request_timestamp DESC;

-- Create a view for privacy settings summary
CREATE OR REPLACE VIEW privacy_settings_summary AS
SELECT 
    upp.user_id,
    upp.privacy_level,
    upp.consent_status,
    upp.updated_at as preferences_updated,
    COUNT(cba.id) as audit_entries_count,
    MAX(cba.request_timestamp) as last_audit_entry
FROM user_privacy_preferences upp
LEFT JOIN context_boundary_audit cba ON upp.user_id = cba.user_id
GROUP BY upp.user_id, upp.privacy_level, upp.consent_status, upp.updated_at;

COMMENT ON TABLE user_privacy_preferences IS 'Stores user privacy preferences and consent status for context boundary enforcement';
COMMENT ON TABLE context_boundary_audit IS 'Audit log for all privacy decisions and context boundary enforcement actions';
