'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'

interface Message {
  id: string
  content: string
  sender: 'user' | 'assistant'
  timestamp: Date
  metadata?: Record<string, unknown>
}

interface ChatConfig {
  characterName: string
  apiEndpoint: string
  userId: string
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [config, setConfig] = useState<ChatConfig>({
    characterName: 'Assistant',
    apiEndpoint: 'http://localhost:9090/api/chat',
    userId: `user_${Math.random().toString(36).substr(2, 9)}`
  })
  const [showConfig, setShowConfig] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking')
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    // Check for URL parameters
    const urlParams = new URLSearchParams(window.location.search)
    const endpoint = urlParams.get('endpoint')
    const character = urlParams.get('character')
    
    if (endpoint || character) {
      setConfig(prev => ({
        ...prev,
        ...(endpoint && { apiEndpoint: endpoint }),
        ...(character && { characterName: character })
      }))
    }
    
    const initializeConnection = async () => {
      await checkConnection()
      scrollToBottom()
    }
    
    initializeConnection()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const checkConnection = async () => {
    try {
      // Try the configured endpoint first, then fallback to default
      const endpointToTest = config.apiEndpoint.replace('/api/chat', '/health')
      const response = await fetch(endpointToTest)
      if (response.ok) {
        setConnectionStatus('connected')
        // Add welcome message
        if (messages.length === 0) {
          const currentTime = new Date().getHours()
          let greeting = 'Hello'
          if (currentTime < 12) greeting = 'Good morning'
          else if (currentTime < 18) greeting = 'Good afternoon'
          else greeting = 'Good evening'
          
          setMessages([{
            id: 'welcome',
            content: `${greeting}! I'm ${config.characterName}. I'm connected and ready to chat. What would you like to talk about?`,
            sender: 'assistant',
            timestamp: new Date()
          }])
        }
      } else {
        setConnectionStatus('disconnected')
      }
    } catch {
      setConnectionStatus('disconnected')
    }
  }

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage: Message = {
      id: `user_${Date.now()}`,
      content: inputValue,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      const response = await fetch(config.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: config.userId,
          message: inputValue,
          context: {
            channel_type: 'web_ui',
            platform: 'web',
            metadata: {}
          }
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      
      const assistantMessage: Message = {
        id: `assistant_${Date.now()}`,
        content: data.response || data.message || 'Sorry, I didn\'t understand that.',
        sender: 'assistant',
        timestamp: new Date(),
        metadata: data.metadata
      }

      setMessages(prev => [...prev, assistantMessage])
      setConnectionStatus('connected')
    } catch (error) {
      console.error('Error sending message:', error)
      
      const errorMessage: Message = {
        id: `error_${Date.now()}`,
        content: `Sorry, I'm having trouble connecting to the AI service. Please check that WhisperEngine is running and try again. Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        sender: 'assistant',
        timestamp: new Date()
      }

      setMessages(prev => [...prev, errorMessage])
      setConnectionStatus('disconnected')
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearChat = () => {
    setMessages([{
      id: 'welcome',
      content: `Hello! I'm your AI character assistant. How can I help you today?`,
      sender: 'assistant',
      timestamp: new Date()
    }])
  }

  const getStatusIndicator = () => {
    switch (connectionStatus) {
      case 'connected':
        return <span className="inline-block w-2 h-2 bg-green-500 rounded-full mr-2"></span>
      case 'disconnected':
        return <span className="inline-block w-2 h-2 bg-red-500 rounded-full mr-2"></span>
      case 'checking':
        return <span className="inline-block w-2 h-2 bg-yellow-500 rounded-full mr-2 animate-pulse"></span>
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-8">
              <Link href="/" className="text-xl font-bold text-blue-600">
                CDL Authoring Tool
              </Link>
              <div className="flex space-x-6">
                <Link href="/characters" className="text-gray-600 hover:text-blue-600">
                  Characters
                </Link>
                <Link href="/config" className="text-gray-600 hover:text-blue-600">
                  Configuration
                </Link>
                <Link href="/chat" className="text-blue-600 font-medium">
                  Chat
                </Link>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center text-sm text-gray-600">
                {getStatusIndicator()}
                {connectionStatus === 'connected' && `Connected to ${config.characterName}`}
                {connectionStatus === 'disconnected' && 'Disconnected'}
                {connectionStatus === 'checking' && 'Checking connection...'}
              </div>
              
              {connectionStatus === 'disconnected' && (
                <button
                  onClick={checkConnection}
                  className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
                >
                  Retry
                </button>
              )}
              
              {connectionStatus === 'connected' && (
                <button
                  onClick={checkConnection}
                  className="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700"
                  title="Test connection"
                >
                  ✓
                </button>
              )}
              
              <button
                onClick={() => setShowConfig(!showConfig)}
                className="text-gray-600 hover:text-gray-800"
              >
                ⚙️
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Configuration Panel */}
      {showConfig && (
        <div className="bg-blue-50 border-b border-blue-200 p-4">
          <div className="container mx-auto max-w-4xl">
            <h3 className="text-lg font-medium mb-3">Chat Configuration</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Character Name
                </label>
                <input
                  type="text"
                  value={config.characterName}
                  onChange={(e) => setConfig({...config, characterName: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Endpoint
                </label>
                <input
                  type="url"
                  value={config.apiEndpoint}
                  onChange={(e) => setConfig({...config, apiEndpoint: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  User ID
                </label>
                <input
                  type="text"
                  value={config.userId}
                  onChange={(e) => setConfig({...config, userId: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
            <div className="mt-3 flex space-x-2">
              <button
                onClick={checkConnection}
                className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
              >
                Test Connection
              </button>
              <button
                onClick={clearChat}
                className="bg-gray-600 text-white px-3 py-1 rounded text-sm hover:bg-gray-700"
              >
                Clear Chat
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Chat Interface */}
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="bg-white rounded-lg shadow-lg h-[600px] flex flex-col">
          {/* Chat Header */}
          <div className="border-b border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-xl font-semibold text-gray-900">
                  Chat with {config.characterName}
                </h1>
                <p className="text-sm text-gray-600">
                  Test your AI character in real-time
                </p>
              </div>
              <div className="flex items-center text-sm">
                {getStatusIndicator()}
                <span className={`${
                  connectionStatus === 'connected' ? 'text-green-600' : 
                  connectionStatus === 'disconnected' ? 'text-red-600' : 'text-yellow-600'
                }`}>
                  {connectionStatus === 'connected' && 'Ready to Chat'}
                  {connectionStatus === 'disconnected' && 'Not Connected'}
                  {connectionStatus === 'checking' && 'Connecting...'}
                </span>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.sender === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <p className="text-sm">{message.content}</p>
                  <p className={`text-xs mt-1 ${
                    message.sender === 'user' ? 'text-blue-100' : 'text-gray-500'
                  }`}>
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 text-gray-900 max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                    <span className="text-sm">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex space-x-2">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                className="flex-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                disabled={isLoading || connectionStatus === 'disconnected'}
              />
              <button
                onClick={sendMessage}
                disabled={!inputValue.trim() || isLoading || connectionStatus === 'disconnected'}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                Send
              </button>
            </div>
            
            {connectionStatus === 'connected' && messages.length <= 1 && (
              <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded text-sm text-green-800">
                <div className="font-medium mb-1">✅ Connected to {config.characterName}</div>
                <div className="text-green-700">
                  Your character is ready to chat! Type a message above to start the conversation.
                </div>
              </div>
            )}
            
            {connectionStatus === 'disconnected' && (
              <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded text-sm text-blue-800">
                <div className="font-medium mb-1">💡 Character Testing Requires WhisperEngine</div>
                <div className="text-blue-700">
                  To chat with deployed characters, start WhisperEngine with: <code className="bg-blue-100 px-1 rounded">./multi-bot.sh start all</code>
                </div>
                <div className="text-blue-600 text-xs mt-1">
                  Note: This is optional for character creation and management.
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}