import { notFound } from 'next/navigation'
import Link from 'next/link'
import { getCharacterById } from '@/lib/db'
import CharacterEditForm from '@/components/CharacterEditForm'

interface PageProps {
  params: Promise<{
    id: string
  }>
}

export default async function CharacterEditPage({ params }: PageProps) {
  const resolvedParams = await params
  const characterId = parseInt(resolvedParams.id)
  
  if (isNaN(characterId)) {
    notFound()
  }

  const character = await getCharacterById(characterId)
  
  if (!character) {
    notFound()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-8">
            <Link href="/" className="text-xl font-bold text-blue-600">
              CDL Authoring Tool
            </Link>
            <div className="flex space-x-6">
              <Link href="/characters" className="text-blue-600 font-medium">
                Characters
              </Link>
              <Link href="/traits" className="text-gray-600 hover:text-blue-600">
                Traits
              </Link>
              <Link href="/communication" className="text-gray-600 hover:text-blue-600">
                Communication
              </Link>
              <Link href="/values" className="text-gray-600 hover:text-blue-600">
                Values
              </Link>
              <Link href="/knowledge" className="text-gray-600 hover:text-blue-600">
                Knowledge
              </Link>
              <Link href="/evolution" className="text-gray-600 hover:text-blue-600">
                Evolution
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Edit Character: {character.name}
              </h1>
              <p className="text-gray-600">
                Modify character personality, traits, and behavioral patterns using enhanced JSONB CDL data.
              </p>
            </div>
            <Link 
              href="/characters" 
              className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600"
            >
              ← Back to Characters
            </Link>
          </div>
        </div>

        {/* Character Edit Form */}
        <div className="bg-white rounded-lg shadow p-6">
          <CharacterEditForm character={character} />
        </div>
      </div>
    </div>
  )
}