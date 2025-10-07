import Link from 'next/link'
import CharacterCreateForm from '@/components/CharacterCreateForm'

export default function NewCharacterPage() {
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
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-4">
            <Link 
              href="/characters" 
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              ← Back to Characters
            </Link>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Create New Character</h1>
          <p className="text-gray-600">
            Define a new AI character with comprehensive personality, communication style, and behavioral patterns.
          </p>
        </div>

        <CharacterCreateForm />
      </div>
    </div>
  )
}