import { NextRequest, NextResponse } from 'next/server'
import { getCharacterById } from '@/lib/db'
import * as yaml from 'js-yaml'

interface PageProps {
  params: Promise<{
    id: string
  }>
}

export async function GET(request: NextRequest, { params }: PageProps) {
  try {
    const resolvedParams = await params
    const characterId = parseInt(resolvedParams.id)
    
    if (isNaN(characterId)) {
      return NextResponse.json({
        success: false,
        error: 'Invalid character ID'
      }, { status: 400 })
    }

    const character = await getCharacterById(characterId)
    
    if (!character) {
      return NextResponse.json({
        success: false,
        error: 'Character not found'
      }, { status: 404 })
    }

    // Convert character to clean YAML structure
    const yamlStructure: {
      name: string
      identity: {
        name: string
        occupation: string | null
        description: string | null
        archetype: string
        allow_full_roleplay_immersion: boolean
      }
      metadata: Record<string, unknown>
      personality?: unknown
      communication?: unknown
      values?: unknown
      interests?: unknown
    } = {
      name: character.name,
      identity: {
        name: character.name,
        occupation: character.occupation,
        description: character.description,
        archetype: character.character_archetype || 'real-world',
        allow_full_roleplay_immersion: character.allow_full_roleplay_immersion || false
      },
      metadata: {
        database_id: character.id,
        normalized_name: character.normalized_name,
        export_date: new Date().toISOString(),
        created_at: character.created_at,
        updated_at: character.updated_at,
        is_active: character.is_active,
        schema_version: '1.0',
        source: 'whisperengine_cdl_web_ui'
      }
    }

    // Add CDL data if available
    if (character.cdl_data) {
      // Merge CDL data into the structure
      if (character.cdl_data.personality) {
        yamlStructure.personality = character.cdl_data.personality
      }
      if (character.cdl_data.communication) {
        yamlStructure.communication = character.cdl_data.communication
      }
      if (character.cdl_data.values) {
        yamlStructure.values = character.cdl_data.values
      }
      if (character.cdl_data.interests) {
        yamlStructure.interests = character.cdl_data.interests
      }
    }

    // Remove null/undefined values
    const cleanStructure = JSON.parse(JSON.stringify(yamlStructure, (key, value) => 
      value === null || value === undefined ? undefined : value
    ))

    // Convert to YAML
    const yamlContent = yaml.dump(cleanStructure, {
      indent: 2,
      lineWidth: 120,
      noRefs: true,
      sortKeys: false
    })

    // Return YAML file as download
    const filename = `${character.normalized_name || character.name.toLowerCase().replace(/[^a-z0-9]/g, '_')}.yaml`
    
    return new NextResponse(yamlContent, {
      status: 200,
      headers: {
        'Content-Type': 'application/x-yaml',
        'Content-Disposition': `attachment; filename="${filename}"`,
        'Cache-Control': 'no-cache'
      }
    })

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    const errorStack = error instanceof Error ? error.stack : undefined
    
    console.error('Character YAML export error:', error)
    
    return NextResponse.json({
      success: false,
      error: errorMessage,
      stack: errorStack
    }, { status: 500 })
  }
}