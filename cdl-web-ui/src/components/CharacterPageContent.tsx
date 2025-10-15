'use client'

import { Character } from '@/types/cdl'
import CharacterView from './CharacterView'
import UnifiedCharacterInterface from './UnifiedCharacterInterface'

interface CharacterPageContentProps {
  character: Character
  mode: 'view' | 'edit'
}

export default function CharacterPageContent({ character, mode }: CharacterPageContentProps) {
  if (mode === 'edit') {
    return (
      <div>
        <UnifiedCharacterInterface character={character} />
      </div>
    )
  }

  return (
    <div className="bg-gray-800 rounded-lg shadow">
      <CharacterView character={character} />
    </div>
  )
}