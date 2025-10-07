import { NextResponse } from 'next/server'
import { getCharacters } from '@/lib/db'

export async function GET() {
  try {
    const characters = await getCharacters()
    
    // Return both raw data and debug info
    return NextResponse.json({
      success: true,
      count: characters.length,
      characters: characters,
      debug: {
        first_character: characters[0] || null,
        bot_names: characters.map(c => ({ name: c.name, bot_name: c.bot_name, character_archetype: c.character_archetype }))
      }
    })
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    const errorStack = error instanceof Error ? error.stack : undefined
    
    return NextResponse.json({
      success: false,
      error: errorMessage,
      stack: errorStack
    }, { status: 500 })
  }
}