import Link from 'next/link'

export default function TraitsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-8">
            <Link href="/" className="text-xl font-bold text-blue-600">CDL Authoring Tool</Link>
            <div className="flex space-x-6">
              <Link href="/characters" className="text-gray-600 hover:text-blue-600">Characters</Link>
              <Link href="/traits" className="text-blue-600 font-medium">Traits</Link>
              <Link href="/communication" className="text-gray-600 hover:text-blue-600">Communication</Link>
              <Link href="/values" className="text-gray-600 hover:text-blue-600">Values</Link>
              <Link href="/knowledge" className="text-gray-600 hover:text-blue-600">Knowledge</Link>
              <Link href="/evolution" className="text-gray-600 hover:text-blue-600">Evolution</Link>
            </div>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Personality Traits</h1>
          <p className="text-gray-600">Define and manage personality traits, behavioral patterns, and character archetypes.</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">Trait Library</h2>
            <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
              + New Trait
            </button>
          </div>

          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-4">🎭</div>
            <h3 className="text-lg font-medium mb-2">No traits defined</h3>
            <p>Create personality traits to build rich character profiles.</p>
          </div>
        </div>
      </div>
    </div>
  )
}