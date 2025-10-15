-- Migration: Character Configuration Tables
-- Description: Add per-character LLM and Discord configuration support
-- Date: 2025-10-14
-- Author: WhisperEngine Team

-- Character LLM Configuration Table
CREATE TABLE IF NOT EXISTS character_llm_config (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- LLM Provider Configuration
    llm_client_type VARCHAR(100) NOT NULL DEFAULT 'openrouter',
    llm_chat_api_url VARCHAR(500) NOT NULL DEFAULT 'https://openrouter.ai/api/v1',
    llm_chat_model VARCHAR(200) NOT NULL DEFAULT 'anthropic/claude-3-haiku',
    llm_chat_api_key TEXT, -- Encrypted storage recommended
    
    -- Advanced LLM Settings
    llm_temperature NUMERIC(3,2) DEFAULT 0.7,
    llm_max_tokens INTEGER DEFAULT 4000,
    llm_top_p NUMERIC(3,2) DEFAULT 0.9,
    llm_frequency_penalty NUMERIC(3,2) DEFAULT 0.0,
    llm_presence_penalty NUMERIC(3,2) DEFAULT 0.0,
    
    -- Configuration metadata
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure one active config per character
    UNIQUE(character_id, is_active) DEFERRABLE INITIALLY DEFERRED
);

-- Character Discord Configuration Table
CREATE TABLE IF NOT EXISTS character_discord_config (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- Discord Bot Configuration
    discord_bot_token TEXT, -- Encrypted storage recommended
    discord_application_id VARCHAR(200),
    discord_public_key TEXT,
    
    -- Discord Integration Settings
    enable_discord BOOLEAN DEFAULT false,
    discord_guild_restrictions TEXT[], -- Array of allowed guild IDs
    discord_channel_restrictions TEXT[], -- Array of allowed channel IDs
    
    -- Discord Behavior Settings
    discord_status VARCHAR(100) DEFAULT 'online', -- online, idle, dnd, invisible
    discord_activity_type VARCHAR(50) DEFAULT 'watching', -- playing, streaming, listening, watching
    discord_activity_name VARCHAR(200) DEFAULT 'conversations',
    
    -- Response Settings
    response_delay_min INTEGER DEFAULT 1000, -- milliseconds
    response_delay_max INTEGER DEFAULT 3000, -- milliseconds
    typing_indicator BOOLEAN DEFAULT true,
    
    -- Configuration metadata
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure one active config per character
    UNIQUE(character_id, is_active) DEFERRABLE INITIALLY DEFERRED
);

-- Character Deployment Configuration Table
CREATE TABLE IF NOT EXISTS character_deployment_config (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- Deployment Settings
    health_check_port INTEGER UNIQUE, -- Auto-assigned starting from 9090
    container_name VARCHAR(200),
    docker_image VARCHAR(200) DEFAULT 'whisperengine-bot:latest',
    
    -- Environment Overrides
    env_overrides JSONB DEFAULT '{}', -- Key-value pairs for environment variables
    
    -- Resource Limits
    memory_limit VARCHAR(20) DEFAULT '512m',
    cpu_limit VARCHAR(20) DEFAULT '0.5',
    
    -- Deployment Status
    deployment_status VARCHAR(50) DEFAULT 'inactive', -- inactive, pending, active, failed
    last_deployed_at TIMESTAMP WITH TIME ZONE,
    deployment_logs TEXT,
    
    -- Configuration metadata
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure one active config per character
    UNIQUE(character_id, is_active) DEFERRABLE INITIALLY DEFERRED
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_character_llm_config_character_id ON character_llm_config(character_id);
CREATE INDEX IF NOT EXISTS idx_character_discord_config_character_id ON character_discord_config(character_id);
CREATE INDEX IF NOT EXISTS idx_character_deployment_config_character_id ON character_deployment_config(character_id);

CREATE INDEX IF NOT EXISTS idx_character_llm_config_active ON character_llm_config(character_id, is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_character_discord_config_active ON character_discord_config(character_id, is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_character_deployment_config_active ON character_deployment_config(character_id, is_active) WHERE is_active = true;

-- Update trigger for updated_at timestamps
CREATE OR REPLACE FUNCTION update_character_config_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_character_llm_config_updated_at
    BEFORE UPDATE ON character_llm_config
    FOR EACH ROW
    EXECUTE FUNCTION update_character_config_updated_at();

CREATE TRIGGER update_character_discord_config_updated_at
    BEFORE UPDATE ON character_discord_config
    FOR EACH ROW
    EXECUTE FUNCTION update_character_config_updated_at();

CREATE TRIGGER update_character_deployment_config_updated_at
    BEFORE UPDATE ON character_deployment_config
    FOR EACH ROW
    EXECUTE FUNCTION update_character_config_updated_at();

-- Comments for documentation
COMMENT ON TABLE character_llm_config IS 'Per-character LLM provider and model configuration';
COMMENT ON TABLE character_discord_config IS 'Per-character Discord bot integration settings';
COMMENT ON TABLE character_deployment_config IS 'Per-character deployment and container configuration';

COMMENT ON COLUMN character_llm_config.llm_chat_api_key IS 'API key for LLM provider - should be encrypted at application level';
COMMENT ON COLUMN character_discord_config.discord_bot_token IS 'Discord bot token - should be encrypted at application level';
COMMENT ON COLUMN character_deployment_config.health_check_port IS 'Unique port for character health check endpoint';
COMMENT ON COLUMN character_deployment_config.env_overrides IS 'JSON object of environment variable overrides for this character';