import { Pool } from 'pg';
import { Character, CharacterLLMConfig, CharacterDiscordConfig, CharacterDeploymentConfig, CharacterWithConfigs } from '@/types/cdl';

// Re-export Character type for convenience
export type { Character, CharacterLLMConfig, CharacterDiscordConfig, CharacterDeploymentConfig, CharacterWithConfigs } from '@/types/cdl';

// Helper function to get database config from environment variables
// Supports both POSTGRES_* and PG* prefixes for backward compatibility
export function getDatabaseConfig() {
  // Determine the appropriate database host based on environment
  const isDocker = process.env.NODE_ENV === 'production' || process.env.DOCKER_ENV === 'true';
  const defaultHost = isDocker ? 'host.docker.internal' : 'localhost';
  
  return {
    host: process.env.POSTGRES_HOST || process.env.PGHOST || defaultHost,
    port: parseInt(
      process.env.POSTGRES_PORT || 
      process.env.PGPORT || 
      '5432'
    ),
    database: process.env.POSTGRES_DB || 
             process.env.POSTGRES_DATABASE || 
             process.env.PGDATABASE || 
             'whisperengine',
    user: process.env.POSTGRES_USER || process.env.PGUSER || 'whisperengine',
    password: process.env.POSTGRES_PASSWORD || process.env.PGPASSWORD || 'whisperengine_password',
    ssl: false,
  };
}

class DatabaseAdapter {
  private pool: Pool;

  constructor() {
    this.pool = new Pool(getDatabaseConfig());
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

  // Helper methods for normalized schema
  async getCharacterIdentityDetails(characterId: number): Promise<any> {
    const client = await this.pool.connect();
    try {
      const result = await client.query(
        'SELECT * FROM character_identity_details WHERE character_id = $1',
        [characterId]
      );
      return result.rows[0] || null;
    } finally {
      client.release();
    }
  }

  async getCharacterPersonalityTraits(characterId: number): Promise<any> {
    const client = await this.pool.connect();
    try {
      const result = await client.query(
        'SELECT trait_name, trait_value FROM personality_traits WHERE character_id = $1',
        [characterId]
      );
      
      const traits: any = {
        openness: 0.5,
        conscientiousness: 0.5,
        extraversion: 0.5,
        agreeableness: 0.5,
        neuroticism: 0.5
      };

      result.rows.forEach(row => {
        if (traits.hasOwnProperty(row.trait_name)) {
          traits[row.trait_name] = parseFloat(row.trait_value);
        }
      });

      return traits;
    } finally {
      client.release();
    }
  }

  async getCharacterValues(characterId: number): Promise<string[]> {
    const client = await this.pool.connect();
    try {
      const result = await client.query(
        'SELECT value_key FROM character_values WHERE character_id = $1 ORDER BY importance_level DESC, value_key',
        [characterId]
      );
      return result.rows.map(row => row.value_key);
    } finally {
      client.release();
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
        archetype: row.archetype || 'real-world',
        allow_full_roleplay: row.allow_full_roleplay || false,
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
      
      // Load related data from normalized tables
      const [identityDetails, personalityTraits, characterValues] = await Promise.all([
        this.getCharacterIdentityDetails(id),
        this.getCharacterPersonalityTraits(id),
        this.getCharacterValues(id)
      ]);

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
        location: identityDetails?.location || null,
        age_range: null,
        background: null,
        description: row.description || null,
        archetype: row.archetype || 'real-world',
        allow_full_roleplay: row.allow_full_roleplay || false,
        cdl_data: {
          identity: {
            name: row.name,
            occupation: row.occupation || '',
            description: row.description || '',
            location: identityDetails?.location || ''
          },
          personality: {
            big_five: personalityTraits,
            values: characterValues
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

  // Helper methods to save to normalized tables
  async saveCharacterIdentityDetails(characterId: number, identityData: any, client?: any): Promise<void> {
    const dbClient = client || await this.pool.connect();
    try {
      await dbClient.query(`
        INSERT INTO character_identity_details (character_id, full_name, location)
        VALUES ($1, $2, $3)
        ON CONFLICT (character_id) 
        DO UPDATE SET
          full_name = EXCLUDED.full_name,
          location = EXCLUDED.location
      `, [characterId, identityData.name, identityData.location]);
    } finally {
      if (!client) {
        dbClient.release();
      }
    }
  }

  async saveCharacterPersonalityTraits(characterId: number, traits: any, client?: any): Promise<void> {
    const dbClient = client || await this.pool.connect();
    try {
      // Delete existing traits and insert new ones
      await dbClient.query('DELETE FROM personality_traits WHERE character_id = $1', [characterId]);
      
      for (const [traitName, traitValue] of Object.entries(traits)) {
        await dbClient.query(`
          INSERT INTO personality_traits (character_id, trait_name, trait_value)
          VALUES ($1, $2, $3)
        `, [characterId, traitName, traitValue]);
      }
    } finally {
      if (!client) {
        dbClient.release();
      }
    }
  }

  async saveCharacterValues(characterId: number, values: string[], client?: any): Promise<void> {
    const dbClient = client || await this.pool.connect();
    try {
      // Delete existing values and insert new ones
      await dbClient.query('DELETE FROM character_values WHERE character_id = $1', [characterId]);
      
      for (const value of values) {
        await dbClient.query(`
          INSERT INTO character_values (character_id, value_key, value_description)
          VALUES ($1, $2, $3)
        `, [characterId, value, value]);
      }
    } finally {
      if (!client) {
        dbClient.release();
      }
    }
  }

  async updateCharacter(id: number, characterData: Partial<Character>): Promise<Character | null> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');

      // Update main character table
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
          characterData.archetype,
          characterData.allow_full_roleplay
        ]
      );

      if (result.rows.length === 0) {
        await client.query('ROLLBACK');
        return null;
      }

      // Save CDL data to normalized tables if provided
      if (characterData.cdl_data) {
        const cdl = characterData.cdl_data as any;
        
        // Save identity details
        if (cdl.identity) {
          await this.saveCharacterIdentityDetails(id, cdl.identity);
        }
        
        // Save personality data
        if (cdl.personality) {
          if (cdl.personality.big_five) {
            await this.saveCharacterPersonalityTraits(id, cdl.personality.big_five);
          }
          if (cdl.personality.values) {
            await this.saveCharacterValues(id, cdl.personality.values);
          }
        }
      }

      await client.query('COMMIT');

      // Return the updated character with all related data
      return await this.getCharacterById(id);
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }

  async deleteCharacter(id: number): Promise<boolean> {
    const client = await this.pool.connect();
    try {
      // First check if character exists
      const checkResult = await client.query(
        'SELECT id FROM characters WHERE id = $1',
        [id]
      );

      if (checkResult.rows.length === 0) {
        return false; // Character doesn't exist
      }

      // Delete character (cascading deletes will handle configs)
      const deleteResult = await client.query(
        'DELETE FROM characters WHERE id = $1',
        [id]
      );

      return deleteResult.rowCount !== null && deleteResult.rowCount > 0;
    } finally {
      client.release();
    }
  }

  async cloneCharacter(characterData: Partial<Character>): Promise<Character> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');

      // Generate a unique normalized name
      let baseNormalizedName = characterData.name?.toLowerCase().replace(/[^a-z0-9]/g, '_') || '';
      let normalizedName = baseNormalizedName;
      let counter = 1;
      
      // Check for existing normalized names and add a counter if needed
      while (true) {
        const existingResult = await client.query(
          'SELECT id FROM characters WHERE normalized_name = $1',
          [normalizedName]
        );
        
        if (existingResult.rows.length === 0) {
          break; // Name is unique
        }
        
        normalizedName = `${baseNormalizedName}_${counter}`;
        counter++;
      }
      
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
          characterData.archetype || 'real_world',
          characterData.allow_full_roleplay || false,
          true
        ]
      );

      const characterId = parseInt(characterResult.rows[0].id);
      const row = characterResult.rows[0];

      // Save CDL data to normalized tables if provided
      if (characterData.cdl_data) {
        const cdl = characterData.cdl_data as any;
        
        // Save identity details
        if (cdl.identity) {
          await this.saveCharacterIdentityDetails(characterId, cdl.identity, client);
        }
        
        // Save personality data
        if (cdl.personality) {
          if (cdl.personality.big_five) {
            await this.saveCharacterPersonalityTraits(characterId, cdl.personality.big_five, client);
          }
          if (cdl.personality.values && cdl.personality.values.length > 0) {
            await this.saveCharacterValues(characterId, cdl.personality.values, client);
          }
        }
      }

      await client.query('COMMIT');

      // Return the created character with all related data
      return await this.getCharacterById(characterId) || {
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
        archetype: row.archetype,
        allow_full_roleplay: row.allow_full_roleplay,
        cdl_data: characterData.cdl_data || {},
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
      // Use UPSERT to handle existing records
      const result = await client.query(`
        WITH existing AS (
          SELECT id FROM character_llm_config 
          WHERE character_id = $1 AND is_active = true
        ),
        updated AS (
          UPDATE character_llm_config 
          SET llm_client_type = $2,
              llm_chat_api_url = $3,
              llm_chat_model = $4,
              llm_chat_api_key = $5,
              llm_temperature = $6,
              llm_max_tokens = $7,
              llm_top_p = $8,
              llm_frequency_penalty = $9,
              llm_presence_penalty = $10,
              updated_at = CURRENT_TIMESTAMP
          WHERE character_id = $1 AND is_active = true
          RETURNING *
        ),
        inserted AS (
          INSERT INTO character_llm_config (
            character_id, llm_client_type, llm_chat_api_url, llm_chat_model, 
            llm_chat_api_key, llm_temperature, llm_max_tokens, llm_top_p,
            llm_frequency_penalty, llm_presence_penalty, is_active
          )
          SELECT $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, true
          WHERE NOT EXISTS (SELECT 1 FROM existing)
          RETURNING *
        )
        SELECT * FROM updated
        UNION ALL
        SELECT * FROM inserted
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

  async deleteCharacterLLMConfig(characterId: number): Promise<boolean> {
    const client = await this.pool.connect();
    try {
      const result = await client.query(
        'DELETE FROM character_llm_config WHERE character_id = $1',
        [characterId]
      );
      return result.rowCount !== null && result.rowCount > 0;
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

      // Insert new config using actual schema columns
      const result = await client.query(`
        INSERT INTO character_discord_config (
          character_id, discord_bot_token, discord_application_id, discord_guild_id,
          discord_status_message, discord_activity_type, max_message_length,
          typing_delay_seconds, enable_reactions, enable_typing_indicator, is_active
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, true)
        RETURNING *
      `, [
        characterId,
        config.discord_bot_token || null,
        config.discord_application_id || null,
        config.discord_guild_id || null,
        config.discord_status || 'online',
        config.discord_activity_type || 'playing',
        config.max_message_length || 2000,
        config.typing_delay_seconds || 2.0,
        config.enable_reactions || true,
        config.enable_typing_indicator || true
      ]);

      const row = result.rows[0];
      return {
        id: parseInt(row.id),
        character_id: parseInt(row.character_id),
        discord_bot_token: row.discord_bot_token,
        discord_application_id: row.discord_application_id,
        discord_guild_id: row.discord_guild_id,
        enable_discord: true, // Assume enabled if config exists
        discord_guild_restrictions: [], // Map from guild_id if needed
        discord_channel_restrictions: [], // Not in schema
        discord_status: row.discord_status_message,
        discord_activity_type: row.discord_activity_type,
        max_message_length: parseInt(row.max_message_length),
        typing_delay_seconds: parseFloat(row.typing_delay_seconds),
        enable_reactions: row.enable_reactions,
        enable_typing_indicator: row.enable_typing_indicator,
        is_active: row.is_active,
        created_at: row.created_at,
        updated_at: row.updated_at
      };
    } finally {
      client.release();
    }
  }

  async deleteCharacterDiscordConfig(characterId: number): Promise<boolean> {
    const client = await this.pool.connect();
    try {
      const result = await client.query(
        'DELETE FROM character_discord_config WHERE character_id = $1',
        [characterId]
      );
      return result.rowCount !== null && result.rowCount > 0;
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

  async deleteCharacterDeploymentConfig(characterId: number): Promise<boolean> {
    const client = await this.pool.connect();
    try {
      const result = await client.query(
        'DELETE FROM character_deployment_config WHERE character_id = $1',
        [characterId]
      );
      return result.rowCount !== null && result.rowCount > 0;
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

export async function deleteCharacter(id: number): Promise<boolean> {
  const db = new DatabaseAdapter();
  return await db.deleteCharacter(id);
}

export async function deleteCharacterLLMConfig(characterId: number): Promise<boolean> {
  const db = new DatabaseAdapter();
  return await db.deleteCharacterLLMConfig(characterId);
}

export async function deleteCharacterDiscordConfig(characterId: number): Promise<boolean> {
  const db = new DatabaseAdapter();
  return await db.deleteCharacterDiscordConfig(characterId);
}

export async function deleteCharacterDeploymentConfig(characterId: number): Promise<boolean> {
  const db = new DatabaseAdapter();
  return await db.deleteCharacterDeploymentConfig(characterId);
}

const db = new DatabaseAdapter();
export default db;
