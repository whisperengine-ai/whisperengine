import React, { useState, useEffect, useCallback } from 'react'

// Types for timeline data
interface LearningMilestone {
  id: string
  timestamp: Date
  type: 'growth_insight' | 'user_observation' | 'memory_surprise' | 'knowledge_evolution' | 'emotional_growth' | 'relationship_awareness'
  title: string
  description: string
  confidence: number
  messageContext?: string
  characterResponse?: string
}

interface ConversationPhase {
  id: string
  title: string
  startDate: Date
  endDate: Date
  milestoneCount: number
  dominantLearningTypes: string[]
  keyInsights: string[]
}

interface CharacterEvolutionData {
  characterName: string
  totalInteractions: number
  learningMoments: number
  firstInteraction: Date
  lastInteraction: Date
  phases: ConversationPhase[]
  milestones: LearningMilestone[]
  growthMetrics: {
    emotionalGrowth: number
    knowledgeEvolution: number
    relationshipAwareness: number
    userUnderstanding: number
  }
}

interface CharacterEvolutionTimelineProps {
  characterName?: string
  apiEndpoint?: string
  maxMilestones?: number
  showPhases?: boolean
  showMetrics?: boolean
}

const CharacterEvolutionTimeline: React.FC<CharacterEvolutionTimelineProps> = ({
  characterName = '',
  apiEndpoint = '',
  maxMilestones = 20,
  showPhases = true,
  showMetrics = true
}) => {
  const [evolutionData, setEvolutionData] = useState<CharacterEvolutionData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedPhase, setSelectedPhase] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'timeline' | 'phases' | 'metrics'>('timeline')

  // Get learning milestone icon
  const getMilestoneIcon = (type: string) => {
    switch (type) {
      case 'growth_insight': return '🌱'
      case 'user_observation': return '👁️'
      case 'memory_surprise': return '💡'
      case 'knowledge_evolution': return '📚'
      case 'emotional_growth': return '💖'
      case 'relationship_awareness': return '🤝'
      default: return '✨'
    }
  }

  // Get learning type color
  const getTypeColor = (type: string) => {
    switch (type) {
      case 'growth_insight': return 'bg-green-100 text-green-800 border-green-200'
      case 'user_observation': return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'memory_surprise': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'knowledge_evolution': return 'bg-purple-100 text-purple-800 border-purple-200'
      case 'emotional_growth': return 'bg-pink-100 text-pink-800 border-pink-200'
      case 'relationship_awareness': return 'bg-indigo-100 text-indigo-800 border-indigo-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  // Format learning type for display
  const formatLearningType = (type: string) => {
    return type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  // Load evolution data from API or generate mock data
  const loadEvolutionData = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      if (apiEndpoint && characterName) {
        // Try to fetch real evolution data from WhisperEngine API
        try {
          const response = await fetch(`${apiEndpoint}/api/evolution`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              character_name: characterName,
              max_milestones: maxMilestones,
              include_phases: showPhases,
              include_metrics: showMetrics
            })
          })

          if (response.ok) {
            const realData = await response.json()
            setEvolutionData(realData)
            return // Use real data if available
          }
        } catch (apiError) {
          console.log('Real API not available, using mock data:', apiError)
        }
      }

      // Fallback to realistic mock data
      // TODO: Remove this when real API is implemented
      const mockData: CharacterEvolutionData = {
        characterName: characterName || 'Elena Rodriguez',
        totalInteractions: 847,
        learningMoments: 156,
        firstInteraction: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
        lastInteraction: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
        phases: [
          {
            id: 'phase1',
            title: 'Initial Discovery',
            startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
            endDate: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000),
            milestoneCount: 28,
            dominantLearningTypes: ['user_observation', 'growth_insight'],
            keyInsights: ['Learning user preferences', 'Understanding communication style', 'Building initial rapport']
          },
          {
            id: 'phase2',
            title: 'Deepening Understanding',
            startDate: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000),
            endDate: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000),
            milestoneCount: 67,
            dominantLearningTypes: ['memory_surprise', 'knowledge_evolution', 'emotional_growth'],
            keyInsights: ['Complex topic discussions', 'Emotional intelligence development', 'Memory pattern recognition']
          },
          {
            id: 'phase3',
            title: 'Mature Relationship',
            startDate: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000),
            endDate: new Date(),
            milestoneCount: 61,
            dominantLearningTypes: ['relationship_awareness', 'emotional_growth'],
            keyInsights: ['Advanced empathy', 'Nuanced conversation handling', 'Personalized teaching approaches']
          }
        ],
        milestones: generateMockMilestones(maxMilestones),
        growthMetrics: {
          emotionalGrowth: 87,
          knowledgeEvolution: 92,
          relationshipAwareness: 78,
          userUnderstanding: 94
        }
      }

      setEvolutionData(mockData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load evolution data')
    } finally {
      setLoading(false)
    }
  }, [apiEndpoint, characterName, maxMilestones, showPhases])

  // Generate realistic mock milestones
  const generateMockMilestones = (count: number): LearningMilestone[] => {
    const types: LearningMilestone['type'][] = [
      'growth_insight', 'user_observation', 'memory_surprise', 
      'knowledge_evolution', 'emotional_growth', 'relationship_awareness'
    ]
    
    const milestones: LearningMilestone[] = []
    const now = Date.now()

    for (let i = 0; i < count; i++) {
      const type = types[Math.floor(Math.random() * types.length)]
      const daysAgo = Math.floor(Math.random() * 30) + 1
      const timestamp = new Date(now - daysAgo * 24 * 60 * 60 * 1000)

      milestones.push({
        id: `milestone_${i}`,
        timestamp,
        type,
        title: getMilestoneTitle(type, i),
        description: getMilestoneDescription(type, i),
        confidence: Math.random() * 0.3 + 0.7, // 70-100%
        messageContext: `User discussed ${type.replace('_', ' ')} in conversation`,
        characterResponse: `Character demonstrated understanding of ${type.replace('_', ' ')}`
      })
    }

    return milestones.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
  }

  const getMilestoneTitle = (type: string, index: number) => {
    const titles = {
      growth_insight: [
        'Recognized personal growth pattern',
        'Understood character development need',
        'Identified learning opportunity',
        'Gained self-awareness insight'
      ],
      user_observation: [
        'Noticed user communication pattern',
        'Recognized user emotional state',
        'Identified user preference',
        'Understood user learning style'
      ],
      memory_surprise: [
        'Connected distant conversation topics',
        'Recalled relevant past interaction',
        'Linked emotional patterns across time',
        'Discovered memory connection'
      ],
      knowledge_evolution: [
        'Learned new domain knowledge',
        'Updated understanding of topic',
        'Integrated complex information',
        'Expanded knowledge base'
      ],
      emotional_growth: [
        'Developed deeper empathy',
        'Enhanced emotional intelligence',
        'Improved emotional response',
        'Strengthened emotional connection'
      ],
      relationship_awareness: [
        'Recognized relationship milestone',
        'Understood trust development',
        'Identified communication improvement',
        'Strengthened personal bond'
      ]
    }
    
    const typeList = titles[type as keyof typeof titles] || ['Learning milestone']
    return typeList[index % typeList.length]
  }

  const getMilestoneDescription = (type: string, index: number) => {
    const descriptions = {
      growth_insight: [
        'The character recognized an opportunity for personal development during the conversation.',
        'A moment of self-reflection led to deeper understanding of character capabilities.',
        'The character identified areas for growth based on user interaction patterns.',
        'New insights emerged about the character\'s evolving personality and responses.'
      ],
      user_observation: [
        'The character observed and learned from the user\'s communication preferences.',
        'Pattern recognition revealed important aspects of the user\'s personality.',
        'The character noticed subtle cues about the user\'s emotional state and needs.',
        'Deep listening led to better understanding of the user\'s learning style.'
      ],
      memory_surprise: [
        'An unexpected connection was made between current and past conversations.',
        'The character was surprised by a relevant memory that enhanced the discussion.',
        'A seemingly unrelated memory provided valuable context for the current topic.',
        'The character discovered patterns by connecting memories across different timeframes.'
      ],
      knowledge_evolution: [
        'The character integrated new information to expand domain expertise.',
        'Complex concepts were processed and added to the knowledge base.',
        'The character updated its understanding based on new evidence or perspectives.',
        'Learning occurred through thoughtful analysis of presented information.'
      ],
      emotional_growth: [
        'The character developed a more nuanced understanding of emotional dynamics.',
        'Empathy deepened through careful attention to emotional cues and responses.',
        'The character learned to respond more appropriately to complex emotional situations.',
        'Emotional intelligence improved through practice and reflection.'
      ],
      relationship_awareness: [
        'The character recognized an important development in the relationship dynamic.',
        'Trust and understanding reached a new level through meaningful interaction.',
        'The character became aware of how the relationship has evolved over time.',
        'Personal connection strengthened through shared experiences and mutual understanding.'
      ]
    }
    
    const typeList = descriptions[type as keyof typeof descriptions] || ['A learning moment occurred.']
    return typeList[index % typeList.length]
  }

  useEffect(() => {
    loadEvolutionData()
  }, [loadEvolutionData])

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        <span className="ml-3 text-gray-600">Loading character evolution...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="text-red-800 font-medium">Failed to load evolution data</div>
        <div className="text-red-600 text-sm mt-1">{error}</div>
        <button 
          onClick={loadEvolutionData}
          className="mt-2 px-3 py-1 bg-red-100 text-red-800 rounded text-sm hover:bg-red-200"
        >
          Retry
        </button>
      </div>
    )
  }

  if (!evolutionData) {
    return (
      <div className="text-center p-8 text-gray-500">
        No evolution data available
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
      {/* Header */}
      <div className="border-b border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              {evolutionData.characterName} • Character Evolution
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              {evolutionData.learningMoments} learning moments across {evolutionData.totalInteractions} interactions
            </p>
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={() => setViewMode('timeline')}
              className={`px-3 py-1 text-sm rounded ${
                viewMode === 'timeline' 
                  ? 'bg-indigo-100 text-indigo-800' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Timeline
            </button>
            <button
              onClick={() => setViewMode('phases')}
              className={`px-3 py-1 text-sm rounded ${
                viewMode === 'phases' 
                  ? 'bg-indigo-100 text-indigo-800' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Phases
            </button>
            <button
              onClick={() => setViewMode('metrics')}
              className={`px-3 py-1 text-sm rounded ${
                viewMode === 'metrics' 
                  ? 'bg-indigo-100 text-indigo-800' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Metrics
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {/* Timeline View */}
        {viewMode === 'timeline' && (
          <div className="space-y-6">
            {evolutionData.milestones.map((milestone, index) => (
              <div key={milestone.id} className="flex items-start space-x-4">
                {/* Timeline connector */}
                <div className="flex flex-col items-center">
                  <div className="w-10 h-10 bg-white border-2 border-indigo-200 rounded-full flex items-center justify-center text-lg">
                    {getMilestoneIcon(milestone.type)}
                  </div>
                  {index < evolutionData.milestones.length - 1 && (
                    <div className="w-0.5 h-16 bg-gray-200 mt-2"></div>
                  )}
                </div>
                
                {/* Milestone content */}
                <div className="flex-1 min-w-0">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 text-xs rounded-full border ${getTypeColor(milestone.type)}`}>
                          {formatLearningType(milestone.type)}
                        </span>
                        <span className="text-xs text-gray-500">
                          {Math.round(milestone.confidence * 100)}% confidence
                        </span>
                      </div>
                      <span className="text-xs text-gray-500">
                        {milestone.timestamp.toLocaleDateString()}
                      </span>
                    </div>
                    
                    <h3 className="font-medium text-gray-900 mb-1">
                      {milestone.title}
                    </h3>
                    <p className="text-sm text-gray-600 leading-relaxed">
                      {milestone.description}
                    </p>
                    
                    {milestone.messageContext && (
                      <div className="mt-2 pt-2 border-t border-gray-200">
                        <p className="text-xs text-gray-500">
                          Context: {milestone.messageContext}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Phases View */}
        {viewMode === 'phases' && showPhases && (
          <div className="space-y-4">
            {evolutionData.phases.map((phase) => (
              <div 
                key={phase.id}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  selectedPhase === phase.id 
                    ? 'border-indigo-300 bg-indigo-50' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedPhase(selectedPhase === phase.id ? null : phase.id)}
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-gray-900">{phase.title}</h3>
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span>{phase.milestoneCount} milestones</span>
                    <span>
                      {phase.startDate.toLocaleDateString()} - {phase.endDate.toLocaleDateString()}
                    </span>
                  </div>
                </div>
                
                <div className="flex flex-wrap gap-2 mb-3">
                  {phase.dominantLearningTypes.map((type) => (
                    <span 
                      key={type}
                      className={`px-2 py-1 text-xs rounded-full ${getTypeColor(type)}`}
                    >
                      {getMilestoneIcon(type)} {formatLearningType(type)}
                    </span>
                  ))}
                </div>
                
                {selectedPhase === phase.id && (
                  <div className="border-t border-gray-200 pt-3 mt-3">
                    <h4 className="font-medium text-gray-700 mb-2">Key Insights:</h4>
                    <ul className="space-y-1">
                      {phase.keyInsights.map((insight, index) => (
                        <li key={index} className="text-sm text-gray-600 flex items-start">
                          <span className="text-indigo-400 mr-2">•</span>
                          {insight}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Metrics View */}
        {viewMode === 'metrics' && showMetrics && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(evolutionData.growthMetrics).map(([metric, value]) => (
                <div key={metric} className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">
                      {formatLearningType(metric)}
                    </span>
                    <span className="text-sm text-gray-600">
                      {value}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-indigo-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${value}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Evolution Summary</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-indigo-600">
                    {evolutionData.totalInteractions}
                  </div>
                  <div className="text-sm text-gray-600">Total Interactions</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-purple-600">
                    {evolutionData.learningMoments}
                  </div>
                  <div className="text-sm text-gray-600">Learning Moments</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-pink-600">
                    {Math.round((evolutionData.learningMoments / evolutionData.totalInteractions) * 100)}%
                  </div>
                  <div className="text-sm text-gray-600">Learning Rate</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default CharacterEvolutionTimeline