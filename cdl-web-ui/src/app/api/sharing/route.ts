import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const { character_data, sharing_options } = await request.json()
    
    if (!character_data || !character_data.name) {
      return NextResponse.json({
        success: false,
        error: 'Missing character data'
      }, { status: 400 })
    }

    // Generate sharing link and metadata
    const sharing_id = `share_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const expires_at = sharing_options?.expires_hours 
      ? new Date(Date.now() + (sharing_options.expires_hours * 60 * 60 * 1000))
      : new Date(Date.now() + (7 * 24 * 60 * 60 * 1000)) // Default 7 days

    // Create shareable data (filter sensitive information)
    const shareable_data = {
      ...character_data,
      // Remove sensitive fields
      bot_token: undefined,
      private_keys: undefined,
      personal_knowledge: sharing_options?.include_personal_data ? character_data.personal_knowledge : undefined,
      
      // Add sharing metadata
      sharing_metadata: {
        shared_by: sharing_options?.shared_by || 'anonymous',
        shared_at: new Date().toISOString(),
        expires_at: expires_at.toISOString(),
        sharing_id,
        access_level: sharing_options?.access_level || 'read_only',
        allow_modifications: sharing_options?.allow_modifications || false
      }
    }

    // In production, save to database with sharing_id
    // For now, return the sharing information
    return NextResponse.json({
      success: true,
      sharing_id,
      sharing_url: `${process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000'}/shared/${sharing_id}`,
      expires_at: expires_at.toISOString(),
      shareable_data,
      sharing_options: {
        access_level: sharing_options?.access_level || 'read_only',
        include_personal_data: sharing_options?.include_personal_data || false,
        allow_modifications: sharing_options?.allow_modifications || false,
        expires_hours: sharing_options?.expires_hours || 168 // 7 days default
      }
    }, { status: 201 })
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const sharing_id = searchParams.get('sharing_id')
    
    if (!sharing_id) {
      return NextResponse.json({
        success: false,
        error: 'Missing sharing_id parameter'
      }, { status: 400 })
    }

    // In production, fetch from database by sharing_id
    // For now, return mock data
    return NextResponse.json({
      success: true,
      message: 'In production, this would fetch shared character by sharing_id',
      sharing_id,
      note: 'This endpoint would validate expiration and access permissions'
    })
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}