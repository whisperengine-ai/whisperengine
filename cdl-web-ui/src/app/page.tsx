import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            CDL Authoring Tool
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Character Definition Language (CDL) Web UI for creating, editing, and managing 
            character personalities, traits, communication styles, and knowledge bases.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
          <Link href="/characters" className="block">
            <div className="bg-white rounded-lg shadow-lg hover:shadow-xl transition-shadow p-8">
              <div className="text-3xl mb-4">👥</div>
              <h3 className="text-xl font-semibold mb-2">Characters</h3>
              <p className="text-gray-600">
                View, create, and edit character definitions including personality traits and communication styles.
              </p>
            </div>
          </Link>

          <Link href="/traits" className="block">
            <div className="bg-white rounded-lg shadow-lg hover:shadow-xl transition-shadow p-8">
              <div className="text-3xl mb-4">🎭</div>
              <h3 className="text-xl font-semibold mb-2">Personality Traits</h3>
              <p className="text-gray-600">
                Manage personality traits, behavioral patterns, and character archetypes.
              </p>
            </div>
          </Link>

          <Link href="/communication" className="block">
            <div className="bg-white rounded-lg shadow-lg hover:shadow-xl transition-shadow p-8">
              <div className="text-3xl mb-4">💬</div>
              <h3 className="text-xl font-semibold mb-2">Communication Styles</h3>
              <p className="text-gray-600">
                Define communication patterns, response styles, and conversational behaviors.
              </p>
            </div>
          </Link>

          <Link href="/values" className="block">
            <div className="bg-white rounded-lg shadow-lg hover:shadow-xl transition-shadow p-8">
              <div className="text-3xl mb-4">⭐</div>
              <h3 className="text-xl font-semibold mb-2">Values & Beliefs</h3>
              <p className="text-gray-600">
                Configure core values, beliefs, and ethical frameworks for characters.
              </p>
            </div>
          </Link>

          <Link href="/knowledge" className="block">
            <div className="bg-white rounded-lg shadow-lg hover:shadow-xl transition-shadow p-8">
              <div className="text-3xl mb-4">📚</div>
              <h3 className="text-xl font-semibold mb-2">Knowledge Base</h3>
              <p className="text-gray-600">
                Manage character-specific knowledge, experiences, and contextual information.
              </p>
            </div>
          </Link>

          <Link href="/evolution" className="block">
            <div className="bg-white rounded-lg shadow-lg hover:shadow-xl transition-shadow p-8">
              <div className="text-3xl mb-4">📈</div>
              <h3 className="text-xl font-semibold mb-2">Evolution History</h3>
              <p className="text-gray-600">
                Track character development, adaptation patterns, and learning progression.
              </p>
            </div>
          </Link>
        </div>

        <div className="text-center mt-16">
          <div className="bg-white rounded-lg shadow-lg p-8 max-w-2xl mx-auto">
            <h3 className="text-2xl font-semibold mb-4">Database Status</h3>
            <div className="flex items-center justify-center space-x-4">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-gray-700">Connected to PostgreSQL CDL Database</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
