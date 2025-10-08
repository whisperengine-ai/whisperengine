import { NextRequest, NextResponse } from 'next/server'
import { characterTemplates, CharacterTemplate } from '@/data/characterTemplates'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const template = characterTemplates.find(t => t.id === id)
    
    if (!template) {
      return NextResponse.json({
        success: false,
        error: 'Template not found'
      }, { status: 404 })
    }

    return NextResponse.json({
      success: true,
      template
    })
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const template = characterTemplates.find(t => t.id === id)
    
    if (!template) {
      return NextResponse.json({
        success: false,
        error: 'Template not found'
      }, { status: 404 })
    }

    const { action } = await request.json()

    if (action === 'convert_to_character') {
      // Convert template to character format
      const characterData = {
        name: template.name,
        normalized_name: template.name.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, ''),
        bot_name: template.name.toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 20),
        character_archetype: template.cdlData.communication.ai_identity_handling.allow_full_roleplay_immersion ? 'fantasy' : 'real-world',
        allow_full_roleplay_immersion: template.cdlData.communication.ai_identity_handling.allow_full_roleplay_immersion,
        cdl_data: {
          ...template.cdlData,
          // Add template metadata
          template_source: {
            template_id: template.id,
            template_name: template.name,
            template_category: template.category,
            converted_at: new Date().toISOString()
          }
        },
        // Preserve learning profile in metadata
        learning_metadata: {
          source_template: template.id,
          learning_profile: template.learningProfile,
          original_category: template.category
        }
      }

      return NextResponse.json({
        success: true,
        action: 'convert_to_character',
        character_data: characterData,
        template_source: {
          id: template.id,
          name: template.name,
          category: template.category
        }
      })
    }

    if (action === 'clone_template') {
      // Create a copy of the template with new ID
      const clonedTemplate: CharacterTemplate = {
        ...template,
        id: `${template.id}_clone_${Date.now()}`,
        name: `${template.name} (Copy)`,
        description: `${template.description} (Cloned from ${template.name})`
      }

      return NextResponse.json({
        success: true,
        action: 'clone_template',
        cloned_template: clonedTemplate,
        original_template: template.id
      })
    }

    return NextResponse.json({
      success: false,
      error: 'Invalid action. Supported actions: convert_to_character, clone_template'
    }, { status: 400 })

  } catch (error) {
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}