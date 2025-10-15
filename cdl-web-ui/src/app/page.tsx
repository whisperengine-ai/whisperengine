import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-100 mb-4">
            WhisperEngine Platform
          </h1>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Zero-Configuration AI Character Platform. Create, configure, and deploy 
            AI characters with personalities, memory, and intelligence - all via Web UI.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <Link href="/characters" className="block">
            <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-lg hover:shadow-xl transition-shadow p-8">
              <div className="text-3xl mb-4">👥</div>
              <h3 className="text-xl font-semibold text-gray-100 mb-2">Characters</h3>
              <p className="text-gray-300">
                Create, edit, and manage AI characters with personalities, LLM configs, Discord settings, and deployment - all in one place.
              </p>
            </div>
          </Link>

          <Link href="/chat" className="block">
            <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-lg hover:shadow-xl transition-shadow p-8">
              <div className="text-3xl mb-4">💬</div>
              <h3 className="text-xl font-semibold text-gray-100 mb-2">Test Chat</h3>
              <p className="text-gray-300">
                Chat with your AI characters in real-time to test personality and responses.
              </p>
            </div>
          </Link>
        </div>

        <div className="text-center mt-16">
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 shadow max-w-md mx-auto">
            <h3 className="text-lg font-medium text-gray-100 mb-2">🚀 Character Authoring Platform</h3>
          </div>
        </div>
      </div>
    </div>
  )
}
