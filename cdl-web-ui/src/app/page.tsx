import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            CDL Authoring Tool
          </h1>
          <p className="text-xl text-gray-800 max-w-3xl mx-auto">
            Character Definition Language (CDL) Web UI for creating, editing, and managing 
            character personalities, traits, communication styles, and knowledge bases.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
          <Link href="/characters" className="block">
            <div className="bg-white rounded-lg shadow-lg hover:shadow-xl transition-shadow p-8">
              <div className="text-3xl mb-4">👥</div>
              <h3 className="text-xl font-semibold mb-2">Characters</h3>
              <p className="text-gray-800">
                View, create, and edit character definitions including personality traits and communication styles.
              </p>
            </div>
          </Link>

          <Link href="/traits" className="block">
            <div className="bg-white rounded-lg shadow-lg hover:shadow-xl transition-shadow p-8">
              <div className="text-3xl mb-4">🎭</div>
              <h3 className="text-xl font-semibold mb-2">Personality Traits</h3>
              <p className="text-gray-800">
                Manage personality traits, behavioral patterns, and character archetypes.
              </p>
            </div>
          </Link>

          <Link href="/communication" className="block">
            <div className="bg-white rounded-lg shadow-lg hover:shadow-xl transition-shadow p-8">
              <div className="text-3xl mb-4">💬</div>
              <h3 className="text-xl font-semibold mb-2">Communication Styles</h3>
              <p className="text-gray-800">
                Define communication patterns, response styles, and conversational behaviors.
              </p>
            </div>
          </Link>

          <Link href="/values" className="block">
            <div className="bg-white rounded-lg shadow-lg hover:shadow-xl transition-shadow p-8">
              <div className="text-3xl mb-4">⭐</div>
              <h3 className="text-xl font-semibold mb-2">Values & Beliefs</h3>
              <p className="text-gray-800">
                Configure core values, beliefs, and ethical frameworks for characters.
              </p>
            </div>
          </Link>

          <Link href="/knowledge" className="block">
            <div className="bg-white rounded-lg shadow-lg hover:shadow-xl transition-shadow p-8">
              <div className="text-3xl mb-4">📚</div>
              <h3 className="text-xl font-semibold mb-2">Knowledge Base</h3>
              <p className="text-gray-800">
                Manage character-specific knowledge, experiences, and contextual information.
              </p>
            </div>
          </Link>

          <Link href="/evolution" className="block">
            <div className="bg-white rounded-lg shadow-lg hover:shadow-xl transition-shadow p-8">
              <div className="text-3xl mb-4">📈</div>
              <h3 className="text-xl font-semibold mb-2">Evolution History</h3>
              <p className="text-gray-800">
                Track character development, adaptation patterns, and learning progression.
              </p>
            </div>
          </Link>
        </div>

        <div className="text-center mt-16">
                      <div className="bg-white rounded-lg p-4 shadow">
              <h3 className="text-lg font-medium mb-2">Database Status</h3>
              <p className="text-gray-900">{status}</p>
            </div>
        </div>
      </div>
    </div>
  )
}
