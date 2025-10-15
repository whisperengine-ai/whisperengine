-- Bot Deployments Table
-- Tracks deployed bot containers for characters

CREATE TABLE IF NOT EXISTS bot_deployments (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    container_name VARCHAR(255) NOT NULL UNIQUE,
    port INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'deploying', -- deploying, running, stopped, failed
    config JSONB, -- Full deployment configuration
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deployed_at TIMESTAMP WITH TIME ZONE,
    stopped_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes for performance
    CONSTRAINT unique_character_deployment UNIQUE (character_id),
    CONSTRAINT unique_port UNIQUE (port)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_bot_deployments_character_id ON bot_deployments(character_id);
CREATE INDEX IF NOT EXISTS idx_bot_deployments_status ON bot_deployments(status);
CREATE INDEX IF NOT EXISTS idx_bot_deployments_port ON bot_deployments(port);

-- Comments
COMMENT ON TABLE bot_deployments IS 'Tracks deployed bot containers for characters';
COMMENT ON COLUMN bot_deployments.character_id IS 'Reference to the character this bot represents';
COMMENT ON COLUMN bot_deployments.container_name IS 'Docker container name (must be unique)';
COMMENT ON COLUMN bot_deployments.port IS 'Port the bot is running on';
COMMENT ON COLUMN bot_deployments.status IS 'Current deployment status: deploying, running, stopped, failed';
COMMENT ON COLUMN bot_deployments.config IS 'Full deployment configuration including environment variables';
COMMENT ON COLUMN bot_deployments.error_message IS 'Error message if deployment failed';