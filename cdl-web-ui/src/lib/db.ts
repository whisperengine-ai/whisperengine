import { Pool } from 'pg';
import { Character, CharacterLLMConfig, CharacterDiscordConfig, CharacterDeploymentConfig, CharacterWithConfigs } from '@/types/cdl';

// Re-export Character type for convenience
export type { Character, CharacterLLMConfig, CharacterDiscordConfig, CharacterDeploymentConfig, CharacterWithConfigs } from '@/types/cdl';

class DatabaseAdapter {
  private pool: Pool;

  constructor() {
    this.pool = new Pool({
      host: process.env.PGHOST || 'host.docker.internal',
      port: parseInt(process.env.PGPORT || '5433'),
      database: process.env.PGDATABASE || 'whisperengine',
      user: process.env.PGUSER || 'whisperengine',
      password: process.env.PGPASSWORD || 'whisperengine_password',
      ssl: false,
    });
  }

  async testConnection(): Promise<boolean> {
    try {
      const client = await this.pool.connect();
      await client.query('SELECT 1');
      client.release();
      return true;
    } catch (error) {
      console.error('Database connection test failed:', error);
      return false;
    }
  }

  async getCharacters(): Promise<Character[]> {
    const client = await this.pool.connect();
    try {
      const result = await client.query(
        'SELECT id, name, normalized_name, occupation, description, archetype, allow_full_roleplay, is_active, created_at, updated_at FROM characters WHERE is_active = true ORDER BY name'
      );
      
      return result.rows.map(row => ({
        id: parseInt(row.id),
        name: row.name,
        normalized_name: row.normalized_name || row.name.toLowerCase().replace(/[^a-z0-9]/g, '_'),
        bot_name: row.normalized_name || row.name.toLowerCase().replace(/[^a-z0-9]/g, '_'),
        created_at: row.created_at || new Date().toISOString(),
        updated_at: row.updated_at || new Date().toISOString(),
        is_active: row.is_active,
        version: 1,
        occupation: row.occupation || null,
        location: null,
        age_range: null,
        background: null,
        description: row.description || null,
        character_archetype: row.archetype || 'real-world',
        allow_full_roleplay_immersion: row.allow_full_roleplay || false,
        cdl_data: {
          identity: {
            name: row.name,
            occupation: row.occupation || '',
            description: row.description || ''
          },
          allow_full_roleplay_immersion: row.allow_full_roleplay || false
        },
        created_by: null,
        notes: null,
      }));
    } finally {
      client.release();
    }
  }

  async getCharacterById(id: number): Promise<Character | null> {
    const client = await this.pool.connect();
    try {
      const result = await client.query(
        'SELECT id, name, normalized_name, occupation, description, archetype, allow_full_roleplay, is_active, created_at, updated_at FROM characters WHERE id = $1 AND is_active = true',
        [id]
      );
      
      if (result.rows.length === 0) {
        return null;
      }

      const row = result.rows[0];
      return {
        id: parseInt(row.id),
        name: row.name,
        normalized_name: row.normalized_name || row.name.toLowerCase().replace(/[^a-z0-9]/g, '_'),
        bot_name: row.normalized_name || row.name.toLowerCase().replace(/[^a-z0-9]/g, '_'),
        created_at: row.created_at || new Date().toISOString(),
        updated_at: row.updated_at || new Date().toISOString(),
        is_active: row.is_active,
        version: 1,
        occupation: row.occupation || null,
        location: null,
        age_range: null,
        background: null,
        description: row.description || null,
        character_archetype: row.archetype || 'real-world',
        allow_full_roleplay_immersion: row.allow_full_roleplay || false,
        cdl_data: {
          identity: {
            name: row.name,
            occupation: row.occupation || '',
            description: row.description || ''
          },
          allow_full_roleplay_immersion: row.allow_full_roleplay || false
        },
        created_by: null,
        notes: null,
      };
    } finally {
      client.release();
    }
  }

  async updateCharacter(id: number, characterData: Partial<Character>): Promise<Character | null> {
    const client = await this.pool.connect();
    try {
      const result = await client.query(
        `UPDATE characters 
         SET name = COALESCE($2, name),
             normalized_name = COALESCE($3, normalized_name),
             occupation = COALESCE($4, occupation),
             description = COALESCE($5, description),
             archetype = COALESCE($6, archetype),
             allow_full_roleplay = COALESCE($7, allow_full_roleplay),
             updated_at = CURRENT_TIMESTAMP
         WHERE id = $1 AND is_active = true
         RETURNING id, name, normalized_name, occupation, description, archetype, allow_full_roleplay, is_active, created_at, updated_at`,
        [
          id,
          characterData.name,
          characterData.normalized_name,
          characterData.occupation,
          characterData.description,
          characterData.character_archetype,
          characterData.allow_full_roleplay_immersion
        ]
      );

      if (result.rows.length === 0) {
        return null;
      }

      const row = result.rows[0];
      return {
        id: parseInt(row.id),
        name: row.name,
        normalized_name: row.normalized_name,
        bot_name: row.normalized_name,
        created_at: row.created_at,
        updated_at: row.updated_at,
        is_active: row.is_active,
        version: 1,
        occupation: row.occupation,
        location: null,
        age_range: null,
        background: null,
        description: row.description,
        character_archetype: row.archetype,
        allow_full_roleplay_immersion: row.allow_full_roleplay,
        cdl_data: characterData.cdl_data || {},
        created_by: null,
        notes: null,
      };
    } finally {
      client.release();
    }
  }

  async cloneCharacter(characterData: Partial<Character>): Promise<Character> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');

      const normalizedName = characterData.name?.toLowerCase().replace(/[^a-z0-9]/g, '_') || '';
      
      // Insert main character record
      const characterResult = await client.query(
        `INSERT INTO characters (name, normalized_name, occupation, description, archetype, allow_full_roleplay, is_active, created_at, updated_at) 
         VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) 
         RETURNING id, name, normalized_name, occupation, description, archetype, allow_full_roleplay, is_active, created_at, updated_at`,
        [
          characterData.name,
          normalizedName,
          characterData.occupation || null,
          characterData.description || null,
          characterData.character_archetype || 'real-world',
          characterData.allow_full_roleplay_immersion || false,
          true
        ]
      );

      const characterId = parseInt(characterResult.rows[0].id);
      const row = characterResult.rows[0];

      await client.query('COMMIT');

      // Merge Discord configuration into cdl_data for the response
      const enhancedCdlData = {
        ...characterData.cdl_data,
        discord_config: (characterData as Record<string, unknown>).discord_config || {}
      };

      return {
        id: characterId,
        name: row.name,
        normalized_name: row.normalized_name,
        bot_name: row.normalized_name,
        created_at: row.created_at,
        updated_at: row.updated_at,
        is_active: row.is_active,
        version: 1,
        occupation: row.occupation,
        location: null,
        age_range: null,
        background: null,
        description: row.description,
        character_archetype: row.archetype,
        allow_full_roleplay_immersion: row.allow_full_roleplay,
        cdl_data: enhancedCdlData,
        created_by: null,
        notes: null,
      };
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }

  async createCharacter(characterData: Partial<Character>): Promise<Character> {
    // For now, createCharacter is the same as cloneCharacter
    return this.cloneCharacter(characterData);
  }

  async updateCharacterActiveStatus(id: number, isActive: boolean): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query(
        'UPDATE characters SET is_active = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2',
        [isActive, id]
      );
    } finally {
      client.release();
    }
  }

  // Character LLM Configuration Methods
  async getCharacterLLMConfig(characterId: number): Promise<CharacterLLMConfig | null> {
    const client = await this.pool.connect();
    try {
      const result = await client.query(
        'SELECT * FROM character_llm_config WHERE character_id = $1 AND is_active = true',
        [characterId]
      );
      
      if (result.rows.length === 0) {
        return null;
      }

      const row = result.rows[0];
      return {
        id: parseInt(row.id),
        character_id: parseInt(row.character_id),
        llm_client_type: row.llm_client_type,
        llm_chat_api_url: row.llm_chat_api_url,
        llm_chat_model: row.llm_chat_model,
        llm_chat_api_key: row.llm_chat_api_key,
        llm_temperature: parseFloat(row.llm_temperature),
        llm_max_tokens: parseInt(row.llm_max_tokens),
        llm_top_p: parseFloat(row.llm_top_p),
        llm_frequency_penalty: parseFloat(row.llm_frequency_penalty),
        llm_presence_penalty: parseFloat(row.llm_presence_penalty),
        is_active: row.is_active,
        created_at: row.created_at,
        updated_at: row.updated_at
      };
    } finally {
      client.release();
    }
  }

  async createOrUpdateCharacterLLMConfig(characterId: number, config: Partial<CharacterLLMConfig>): Promise<CharacterLLMConfig> {
    const client = await this.pool.connect();
    try {
      // First, deactivate any existing active config
      await client.query(
        'UPDATE character_llm_config SET is_active = false WHERE character_id = $1 AND is_active = true',
        [characterId]
      );

      // Insert new config
      const result = await client.query(`
        INSERT INTO character_llm_config (
          character_id, llm_client_type, llm_chat_api_url, llm_chat_model, 
          llm_chat_api_key, llm_temperature, llm_max_tokens, llm_top_p,
          llm_frequency_penalty, llm_presence_penalty, is_active
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, true)
        RETURNING *
      `, [
        characterId,
        config.llm_client_type || 'openrouter',
        config.llm_chat_api_url || 'https://openrouter.ai/api/v1',
        config.llm_chat_model || 'anthropic/claude-3-haiku',
        config.llm_chat_api_key || null,
        config.llm_temperature || 0.7,
        config.llm_max_tokens || 4000,
        config.llm_top_p || 0.9,
        config.llm_frequency_penalty || 0.0,
        config.llm_presence_penalty || 0.0
      ]);

      const row = result.rows[0];
      return {
        id: parseInt(row.id),
        character_id: parseInt(row.character_id),
        llm_client_type: row.llm_client_type,
        llm_chat_api_url: row.llm_chat_api_url,
        llm_chat_model: row.llm_chat_model,
        llm_chat_api_key: row.llm_chat_api_key,
        llm_temperature: parseFloat(row.llm_temperature),
        llm_max_tokens: parseInt(row.llm_max_tokens),
        llm_top_p: parseFloat(row.llm_top_p),
        llm_frequency_penalty: parseFloat(row.llm_frequency_penalty),
        llm_presence_penalty: parseFloat(row.llm_presence_penalty),
        is_active: row.is_active,
        created_at: row.created_at,
        updated_at: row.updated_at
      };
    } finally {
      client.release();
    }
  }

  // Character Discord Configuration Methods
  async getCharacterDiscordConfig(characterId: number): Promise<CharacterDiscordConfig | null> {
    const client = await this.pool.connect();
    try {
      const result = await client.query(
        'SELECT * FROM character_discord_config WHERE character_id = $1 AND is_active = true',
        [characterId]
      );
      
      if (result.rows.length === 0) {
        return null;
      }

      const row = result.rows[0];
      return {
        id: parseInt(row.id),
        character_id: parseInt(row.character_id),
        discord_bot_token: row.discord_bot_token,
        discord_application_id: row.discord_application_id,
        discord_public_key: row.discord_public_key,
        enable_discord: row.enable_discord,
        discord_guild_restrictions: row.discord_guild_restrictions || [],
        discord_channel_restrictions: row.discord_channel_restrictions || [],
        discord_status: row.discord_status,
        discord_activity_type: row.discord_activity_type,
        discord_activity_name: row.discord_activity_name,
        response_delay_min: parseInt(row.response_delay_min),
        response_delay_max: parseInt(row.response_delay_max),
        typing_indicator: row.typing_indicator,
        is_active: row.is_active,
        created_at: row.created_at,
        updated_at: row.updated_at
      };
    } finally {
      client.release();
    }
  }

  async createOrUpdateCharacterDiscordConfig(characterId: number, config: Partial<CharacterDiscordConfig>): Promise<CharacterDiscordConfig> {
    const client = await this.pool.connect();
    try {
      // First, deactivate any existing active config
      await client.query(
        'UPDATE character_discord_config SET is_active = false WHERE character_id = $1 AND is_active = true',
        [characterId]
      );

      // Insert new config
      const result = await client.query(`
        INSERT INTO character_discord_config (
          character_id, discord_bot_token, discord_application_id, discord_public_key,
          enable_discord, discord_guild_restrictions, discord_channel_restrictions,
          discord_status, discord_activity_type, discord_activity_name,
          response_delay_min, response_delay_max, typing_indicator, is_active
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, true)
        RETURNING *
      `, [
        characterId,
        config.discord_bot_token || null,
        config.discord_application_id || null,
        config.discord_public_key || null,
        config.enable_discord || false,
        config.discord_guild_restrictions || [],
        config.discord_channel_restrictions || [],
        config.discord_status || 'online',
        config.discord_activity_type || 'watching',
        config.discord_activity_name || 'conversations',
        config.response_delay_min || 1000,
        config.response_delay_max || 3000,
        config.typing_indicator || true
      ]);

      const row = result.rows[0];
      return {
        id: parseInt(row.id),
        character_id: parseInt(row.character_id),
        discord_bot_token: row.discord_bot_token,
        discord_application_id: row.discord_application_id,
        discord_public_key: row.discord_public_key,
        enable_discord: row.enable_discord,
        discord_guild_restrictions: row.discord_guild_restrictions || [],
        discord_channel_restrictions: row.discord_channel_restrictions || [],
        discord_status: row.discord_status,
        discord_activity_type: row.discord_activity_type,
        discord_activity_name: row.discord_activity_name,
        response_delay_min: parseInt(row.response_delay_min),
        response_delay_max: parseInt(row.response_delay_max),
        typing_indicator: row.typing_indicator,
        is_active: row.is_active,
        created_at: row.created_at,
        updated_at: row.updated_at
      };
    } finally {
      client.release();
    }
  }

  // Character Deployment Configuration Methods
  async getCharacterDeploymentConfig(characterId: number): Promise<CharacterDeploymentConfig | null> {
    const client = await this.pool.connect();
    try {
      const result = await client.query(
        'SELECT * FROM character_deployment_config WHERE character_id = $1 AND is_active = true',
        [characterId]
      );
      
      if (result.rows.length === 0) {
        return null;
      }

      const row = result.rows[0];
      return {
        id: parseInt(row.id),
        character_id: parseInt(row.character_id),
        health_check_port: row.health_check_port ? parseInt(row.health_check_port) : null,
        container_name: row.container_name,
        docker_image: row.docker_image,
        env_overrides: row.env_overrides || {},
        memory_limit: row.memory_limit,
        cpu_limit: row.cpu_limit,
        deployment_status: row.deployment_status,
        last_deployed_at: row.last_deployed_at,
        deployment_logs: row.deployment_logs,
        is_active: row.is_active,
        created_at: row.created_at,
        updated_at: row.updated_at
      };
    } finally {
      client.release();
    }
  }

  async createOrUpdateCharacterDeploymentConfig(characterId: number, config: Partial<CharacterDeploymentConfig>): Promise<CharacterDeploymentConfig> {
    const client = await this.pool.connect();
    try {
      // First, deactivate any existing active config
      await client.query(
        'UPDATE character_deployment_config SET is_active = false WHERE character_id = $1 AND is_active = true',
        [characterId]
      );

      // Auto-assign health check port if not provided
      let healthCheckPort = config.health_check_port;
      if (!healthCheckPort) {
        const portResult = await client.query(
          'SELECT COALESCE(MAX(health_check_port), 9089) + 1 as next_port FROM character_deployment_config'
        );
        healthCheckPort = parseInt(portResult.rows[0].next_port);
      }

      // Insert new config
      const result = await client.query(`
        INSERT INTO character_deployment_config (
          character_id, health_check_port, container_name, docker_image,
          env_overrides, memory_limit, cpu_limit, deployment_status, is_active
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, true)
        RETURNING *
      `, [
        characterId,
        healthCheckPort,
        config.container_name || null,
        config.docker_image || 'whisperengine-bot:latest',
        JSON.stringify(config.env_overrides || {}),
        config.memory_limit || '512m',
        config.cpu_limit || '0.5',
        config.deployment_status || 'inactive'
      ]);

      const row = result.rows[0];
      return {
        id: parseInt(row.id),
        character_id: parseInt(row.character_id),
        health_check_port: row.health_check_port ? parseInt(row.health_check_port) : null,
        container_name: row.container_name,
        docker_image: row.docker_image,
        env_overrides: row.env_overrides || {},
        memory_limit: row.memory_limit,
        cpu_limit: row.cpu_limit,
        deployment_status: row.deployment_status,
        last_deployed_at: row.last_deployed_at,
        deployment_logs: row.deployment_logs,
        is_active: row.is_active,
        created_at: row.created_at,
        updated_at: row.updated_at
      };
    } finally {
      client.release();
    }
  }

  // Get character with all configurations
  async getCharacterWithConfigs(id: number): Promise<CharacterWithConfigs | null> {
    const character = await this.getCharacterById(id);
    if (!character) {
      return null;
    }

    const [llmConfig, discordConfig, deploymentConfig] = await Promise.all([
      this.getCharacterLLMConfig(id),
      this.getCharacterDiscordConfig(id),
      this.getCharacterDeploymentConfig(id)
    ]);

    return {
      ...character,
      llm_config: llmConfig || undefined,
      discord_config: discordConfig || undefined,
      deployment_config: deploymentConfig || undefined
    };
  }
}

export async function getCharacters(): Promise<Character[]> {
  const db = new DatabaseAdapter();
  return await db.getCharacters();
}

export async function getCharacterById(id: number): Promise<Character | null> {
  const db = new DatabaseAdapter();
  return await db.getCharacterById(id);
}

export async function createCharacter(characterData: Partial<Character>): Promise<Character> {
  const db = new DatabaseAdapter();
  return await db.createCharacter(characterData);
}

export async function updateCharacter(id: number, characterData: Partial<Character>): Promise<Character | null> {
  const db = new DatabaseAdapter();
  return await db.updateCharacter(id, characterData);
}

export async function updateCharacterActiveStatus(id: number, isActive: boolean): Promise<void> {
  const db = new DatabaseAdapter();
  return await db.updateCharacterActiveStatus(id, isActive);
}

// Character Configuration Functions
export async function getCharacterLLMConfig(characterId: number): Promise<CharacterLLMConfig | null> {
  const db = new DatabaseAdapter();
  return await db.getCharacterLLMConfig(characterId);
}

export async function createOrUpdateCharacterLLMConfig(characterId: number, config: Partial<CharacterLLMConfig>): Promise<CharacterLLMConfig> {
  const db = new DatabaseAdapter();
  return await db.createOrUpdateCharacterLLMConfig(characterId, config);
}

export async function getCharacterDiscordConfig(characterId: number): Promise<CharacterDiscordConfig | null> {
  const db = new DatabaseAdapter();
  return await db.getCharacterDiscordConfig(characterId);
}

export async function createOrUpdateCharacterDiscordConfig(characterId: number, config: Partial<CharacterDiscordConfig>): Promise<CharacterDiscordConfig> {
  const db = new DatabaseAdapter();
  return await db.createOrUpdateCharacterDiscordConfig(characterId, config);
}

export async function getCharacterDeploymentConfig(characterId: number): Promise<CharacterDeploymentConfig | null> {
  const db = new DatabaseAdapter();
  return await db.getCharacterDeploymentConfig(characterId);
}

export async function createOrUpdateCharacterDeploymentConfig(characterId: number, config: Partial<CharacterDeploymentConfig>): Promise<CharacterDeploymentConfig> {
  const db = new DatabaseAdapter();
  return await db.createOrUpdateCharacterDeploymentConfig(characterId, config);
}

export async function getCharacterWithConfigs(id: number): Promise<CharacterWithConfigs | null> {
  const db = new DatabaseAdapter();
  return await db.getCharacterWithConfigs(id);
}

const db = new DatabaseAdapter();
export default db;
