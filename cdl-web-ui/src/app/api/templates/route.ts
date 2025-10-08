import { NextRequest, NextResponse } from 'next/server'
import { characterTemplates, CharacterTemplate, getAllCategories } from '@/data/characterTemplates'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const category = searchParams.get('category')
    const search = searchParams.get('search')
    const limit = searchParams.get('limit')
    
    let filteredTemplates = characterTemplates

    // Filter by category
    if (category && category !== 'all') {
      filteredTemplates = filteredTemplates.filter(t => t.category === category)
    }

    // Filter by search term
    if (search) {
      const searchTerm = search.toLowerCase()
      filteredTemplates = filteredTemplates.filter(t => 
        t.name.toLowerCase().includes(searchTerm) ||
        t.description.toLowerCase().includes(searchTerm) ||
        t.category.toLowerCase().includes(searchTerm)
      )
    }

    // Apply limit
    if (limit) {
      const limitNum = parseInt(limit, 10)
      if (!isNaN(limitNum) && limitNum > 0) {
        filteredTemplates = filteredTemplates.slice(0, limitNum)
      }
    }

    return NextResponse.json({
      success: true,
      templates: filteredTemplates,
      meta: {
        total: filteredTemplates.length,
        categories: getAllCategories(),
        filters: {
          category: category || null,
          search: search || null,
          limit: limit ? parseInt(limit, 10) : null
        }
      }
    })
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const templateData: CharacterTemplate = await request.json()
    
    // Validate required fields
    if (!templateData.name || !templateData.category || !templateData.description) {
      return NextResponse.json({
        success: false,
        error: 'Missing required fields: name, category, description'
      }, { status: 400 })
    }

    if (!templateData.cdlData || !templateData.learningProfile) {
      return NextResponse.json({
        success: false,
        error: 'Missing required fields: cdlData, learningProfile'
      }, { status: 400 })
    }

    // Generate ID if not provided
    if (!templateData.id) {
      templateData.id = `custom_${templateData.name.toLowerCase().replace(/[^a-z0-9]/g, '_')}_${Date.now()}`
    }

    // Add default icon if not provided
    if (!templateData.icon) {
      templateData.icon = '🤖'
    }

    // Note: In a real implementation, you would save this to a database
    // For now, we'll just return the validated template
    return NextResponse.json({
      success: true,
      message: 'Template validated and ready for use',
      template: templateData,
      note: 'In production, this would be saved to a template database'
    }, { status: 201 })
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}