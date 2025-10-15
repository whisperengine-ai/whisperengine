'use client'
/* eslint-disable @typescript-eslint/no-explicit-any */

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { CharacterTemplate } from '@/data/characterTemplates'

// Enhanced CDL data structure for creation
interface CDLData {
  identity: {
    name: string
    occupation: string
    description: string
    location?: string
    age?: number
    voice?: {
      pace?: string
      tone?: string
      accent?: string
      volume?: string
      speech_patterns?: string[]
    }
    essence?: {
      anchor?: string
      nature?: string
      core_identity?: string
    }
  }
  personality: {
    big_five: {
      openness: number
      conscientiousness: number
      extraversion: number
      agreeableness: number
      neuroticism: number
    }
    values: string[]
    communication_style: {
      tone: string
      formality: string
      directness: string
      empathy_level: string
    }
  }
  communication: {
    response_length: string
    ai_identity_handling: {
      approach: string
      philosophy: string
      allow_full_roleplay_immersion: boolean
    }
    conversation_flow_guidance?: {
      response_style?: {
        default_mode?: string
        creative_mode?: {
          triggers?: string[]
          characteristics?: string[]
        }
        technical_mode?: {
          triggers?: string[]
          characteristics?: string[]
        }
      }
    }
  }
  values_and_beliefs?: {
    core_values?: Array<{
      value_key: string
      value_description: string
      importance_level: 'low' | 'medium' | 'high' | 'critical'
      category: 'core_value'
    }>
    fears?: Array<{
      value_key: string
      value_description: string
      importance_level: 'low' | 'medium' | 'high' | 'critical'
      category: 'fear'
    }>
    beliefs?: Array<{
      value_key: string
      value_description: string
      importance_level: 'low' | 'medium' | 'high' | 'critical'
      category: 'belief'
    }>
  }
  personal_knowledge?: {
    relationships?: Array<{
      name: string
      relationship_type: string
      description: string
    }>
    background?: {
      education?: string
      career_history?: string
      significant_events?: string[]
    }
    interests?: string[]
    skills?: string[]
  }
}

interface FormData {
  name: string
  normalized_name: string
  bot_name: string
  character_archetype: 'real-world' | 'fantasy' | 'narrative-ai'
  allow_full_roleplay_immersion: boolean
  discord_config?: {
    bot_token?: string
    bot_status?: string
    admin_user_ids?: string
  }
  cdl_data: CDLData
}

interface CharacterCreateFormProps {
  initialTemplate?: CharacterTemplate | null
}

export default function CharacterCreateForm({ initialTemplate }: CharacterCreateFormProps) {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<'identity' | 'personality' | 'communication' | 'values' | 'knowledge'>('identity')
  const [isLoading, setIsLoading] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [deployAfterCreate, setDeployAfterCreate] = useState(false)

  const [formData, setFormData] = useState<FormData>({
    name: '',
    normalized_name: '',
    bot_name: '',
    character_archetype: 'real-world',
    allow_full_roleplay_immersion: false,
    discord_config: {
      bot_token: '',
      bot_status: '',
      admin_user_ids: ''
    },
    cdl_data: {
      identity: {
        name: '',
        occupation: '',
        description: '',
        location: '',
        age: undefined,
        voice: {
          pace: 'moderate',
          tone: 'warm',
          accent: 'neutral',
          volume: 'normal',
          speech_patterns: []
        },
        essence: {
          anchor: '',
          nature: '',
          core_identity: ''
        }
      },
      personality: {
        big_five: {
          openness: 0.5,
          conscientiousness: 0.5,
          extraversion: 0.5,
          agreeableness: 0.5,
          neuroticism: 0.5
        },
        values: [],
        communication_style: {
          tone: 'friendly',
          formality: 'casual',
          directness: 'moderate',
          empathy_level: 'high'
        }
      },
      communication: {
        response_length: 'moderate',
        ai_identity_handling: {
          approach: '3-tier',
          philosophy: 'honest_with_alternatives',
          allow_full_roleplay_immersion: false
        },
        conversation_flow_guidance: {
          response_style: {
            default_mode: 'conversational',
            creative_mode: {
              triggers: ['creative', 'artistic', 'imaginative'],
              characteristics: ['metaphorical', 'expressive', 'colorful']
            },
            technical_mode: {
              triggers: ['technical', 'debug', 'code', 'precise'],
              characteristics: ['clear', 'structured', 'factual']
            }
          }
        }
      },
      values_and_beliefs: {
        core_values: [],
        fears: [],
        beliefs: []
      },
      personal_knowledge: {
        relationships: [],
        background: {
          education: '',
          career_history: '',
          significant_events: []
        },
        interests: [],
        skills: []
      }
    }
  })

  // Populate form with template data when provided
  useEffect(() => {
    if (initialTemplate) {
      setFormData(prevData => ({
        ...prevData,
        name: initialTemplate.name,
        normalized_name: initialTemplate.name.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, ''),
        bot_name: initialTemplate.name.toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 20),
        character_archetype: initialTemplate.cdlData.communication.ai_identity_handling.allow_full_roleplay_immersion ? 'fantasy' : 'real-world',
        allow_full_roleplay_immersion: initialTemplate.cdlData.communication.ai_identity_handling.allow_full_roleplay_immersion,
        cdl_data: {
          ...initialTemplate.cdlData,
          // Keep the existing personal_knowledge structure from the form
          personal_knowledge: prevData.cdl_data.personal_knowledge
        }
      }))
    }
  }, [initialTemplate])

  // Update normalized name when name changes
  const handleNameChange = (name: string) => {
    const normalized = name.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '')
    const botName = name.toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 20)
    
    setFormData(prev => ({
      ...prev,
      name,
      normalized_name: normalized,
      bot_name: botName,
      cdl_data: {
        ...prev.cdl_data,
        identity: {
          ...prev.cdl_data.identity,
          name
        }
      }
    }))
  }

  const handleSave = async () => {
    if (!formData.name || !formData.cdl_data.identity.occupation) {
      alert('Please fill in required fields: Name and Occupation')
      return
    }

    setIsLoading(true)
    setSaveStatus('saving')
    
    try {
      // Create character
      const response = await fetch('/api/characters', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        const result = await response.json()
        setSaveStatus('saved')
        
        // Deploy character if requested
        if (deployAfterCreate) {
          try {
            const deployResponse = await fetch('/api/characters/deploy', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                characterId: result.character.id,
                deploymentConfig: {
                  enableDiscord: false,
                  healthCheckPort: 9090 + result.character.id
                }
              })
            })
            
            if (deployResponse.ok) {
              const deployResult = await deployResponse.json()
              alert(`✅ Character "${formData.name}" created and deployed successfully!\n\nAPI Endpoint: ${deployResult.deployment.apiEndpoint}`)
              router.push('/deployments')
            } else {
              alert(`✅ Character "${formData.name}" created successfully!\n❌ Deployment failed - you can deploy manually from the Characters page.`)
              router.push(`/characters/${result.character.id}`)
            }
          } catch (deployError) {
            console.error('Deployment error:', deployError)
            alert(`✅ Character "${formData.name}" created successfully!\n❌ Deployment failed - you can deploy manually from the Characters page.`)
            router.push(`/characters/${result.character.id}`)
          }
        } else {
          setTimeout(() => {
            router.push(`/characters/${result.character.id}`)
          }, 1000)
        }
      } else {
        const error = await response.json()
        console.error('Save error:', error)
        setSaveStatus('error')
        alert(`Error creating character: ${error.error || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Save error:', error)
      setSaveStatus('error')
      alert('Failed to create character. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const addArrayItem = (path: string, value: string) => {
    if (!value.trim()) return
    
    setFormData(prev => {
      const newData = { ...prev }
      const pathParts = path.split('.')
      let target: any = newData
      
      for (let i = 0; i < pathParts.length - 1; i++) {
        target = target[pathParts[i]]
      }
      
      const arrayKey = pathParts[pathParts.length - 1]
      if (!Array.isArray(target[arrayKey])) {
        target[arrayKey] = []
      }
      
      target[arrayKey] = [...target[arrayKey], value]
      return newData
    })
  }

  const removeArrayItem = (path: string, index: number) => {
    setFormData(prev => {
      const newData = { ...prev }
      const pathParts = path.split('.')
      let target: any = newData
      
      for (let i = 0; i < pathParts.length - 1; i++) {
        target = target[pathParts[i]]
      }
      
      const arrayKey = pathParts[pathParts.length - 1]
      target[arrayKey] = target[arrayKey].filter((_: any, i: number) => i !== index)
      return newData
    })
  }

  return (
    <div className="bg-gray-800 rounded-lg shadow">
      {/* Tab Navigation */}
      <div className="border-b border-gray-700">
        <nav className="flex space-x-8 px-6 py-4">
          {[
            { id: 'identity', label: 'Identity', icon: '👤' },
            { id: 'personality', label: 'Personality', icon: '🧠' },
            { id: 'communication', label: 'Communication', icon: '💬' },
            { id: 'values', label: 'Values & Beliefs', icon: '⭐' },
            { id: 'knowledge', label: 'Knowledge', icon: '📚' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg font-medium ${
                activeTab === tab.id
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-100 hover:text-gray-100'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {activeTab === 'identity' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-100">Character Identity</h3>
            
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-100 mb-2">
                  Character Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleNameChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-600 rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter character name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-100 mb-2">
                  Occupation *
                </label>
                <input
                  type="text"
                  value={formData.cdl_data.identity.occupation}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    cdl_data: {
                      ...prev.cdl_data,
                      identity: {
                        ...prev.cdl_data.identity,
                        occupation: e.target.value
                      }
                    }
                  }))}
                  className="w-full px-3 py-2 border border-gray-600 rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Marine Biologist, AI Researcher"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-100 mb-2">
                  Location
                </label>
                <input
                  type="text"
                  value={formData.cdl_data.identity.location || ''}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    cdl_data: {
                      ...prev.cdl_data,
                      identity: {
                        ...prev.cdl_data.identity,
                        location: e.target.value
                      }
                    }
                  }))}
                  className="w-full px-3 py-2 border border-gray-600 rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., San Francisco, Remote"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-100 mb-2">
                  Age
                </label>
                <input
                  type="number"
                  value={formData.cdl_data.identity.age || ''}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    cdl_data: {
                      ...prev.cdl_data,
                      identity: {
                        ...prev.cdl_data.identity,
                        age: e.target.value ? parseInt(e.target.value) : undefined
                      }
                    }
                  }))}
                  className="w-full px-3 py-2 border border-gray-600 rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Age"
                />
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-100 mb-2">
                Character Description
              </label>
              <textarea
                value={formData.cdl_data.identity.description}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  cdl_data: {
                    ...prev.cdl_data,
                    identity: {
                      ...prev.cdl_data.identity,
                      description: e.target.value
                    }
                  }
                }))}
                rows={4}
                className="w-full px-3 py-2 border border-gray-600 rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Describe the character's background, role, and key characteristics..."
              />
            </div>

            {/* Character Archetype */}
            <div>
              <label className="block text-sm font-medium text-gray-100 mb-2">
                Character Archetype
              </label>
              <select
                value={formData.character_archetype}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  character_archetype: e.target.value as any
                }))}
                className="w-full px-3 py-2 border border-gray-600 rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="real-world">Real-world (Human-like professional)</option>
                <option value="fantasy">Fantasy/Mythical (Fictional entity)</option>
                <option value="narrative-ai">Narrative AI (AI character with story)</option>
              </select>
            </div>

            {/* Voice Characteristics */}
            <div>
              <h4 className="text-md font-medium text-gray-100 mb-3">Voice Characteristics</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-100 mb-1">Pace</label>
                  <select
                    value={formData.cdl_data.identity.voice?.pace || 'moderate'}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      cdl_data: {
                        ...prev.cdl_data,
                        identity: {
                          ...prev.cdl_data.identity,
                          voice: {
                            ...prev.cdl_data.identity.voice,
                            pace: e.target.value
                          }
                        }
                      }
                    }))}
                    className="w-full px-2 py-1 border border-gray-600 rounded text-sm text-gray-100"
                  >
                    <option value="slow">Slow</option>
                    <option value="moderate">Moderate</option>
                    <option value="fast">Fast</option>
                    <option value="variable">Variable</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-100 mb-1">Tone</label>
                  <select
                    value={formData.cdl_data.identity.voice?.tone || 'warm'}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      cdl_data: {
                        ...prev.cdl_data,
                        identity: {
                          ...prev.cdl_data.identity,
                          voice: {
                            ...prev.cdl_data.identity.voice,
                            tone: e.target.value
                          }
                        }
                      }
                    }))}
                    className="w-full px-2 py-1 border border-gray-600 rounded text-sm text-gray-100"
                  >
                    <option value="warm">Warm</option>
                    <option value="professional">Professional</option>
                    <option value="friendly">Friendly</option>
                    <option value="authoritative">Authoritative</option>
                    <option value="gentle">Gentle</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-100 mb-1">Accent</label>
                  <input
                    type="text"
                    value={formData.cdl_data.identity.voice?.accent || ''}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      cdl_data: {
                        ...prev.cdl_data,
                        identity: {
                          ...prev.cdl_data.identity,
                          voice: {
                            ...prev.cdl_data.identity.voice,
                            accent: e.target.value
                          }
                        }
                      }
                    }))}
                    className="w-full px-2 py-1 border border-gray-600 rounded text-sm text-gray-100"
                    placeholder="e.g., British, Southern"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-100 mb-1">Volume</label>
                  <select
                    value={formData.cdl_data.identity.voice?.volume || 'normal'}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      cdl_data: {
                        ...prev.cdl_data,
                        identity: {
                          ...prev.cdl_data.identity,
                          voice: {
                            ...prev.cdl_data.identity.voice,
                            volume: e.target.value
                          }
                        }
                      }
                    }))}
                    className="w-full px-2 py-1 border border-gray-600 rounded text-sm text-gray-100"
                  >
                    <option value="quiet">Quiet</option>
                    <option value="normal">Normal</option>
                    <option value="loud">Loud</option>
                    <option value="varies">Varies</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Discord Bot Configuration */}
            <div>
              <h4 className="text-md font-medium text-gray-100 mb-3">🤖 Discord Bot Configuration</h4>
              <p className="text-sm text-gray-100 mb-4">
                Configure Discord bot settings for this character. Each character can have its own Discord bot token.
              </p>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-100 mb-2">
                    Discord Bot Token
                  </label>
                  <input
                    type="password"
                    value={formData.discord_config?.bot_token || ''}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      discord_config: {
                        ...prev.discord_config,
                        bot_token: e.target.value
                      }
                    }))}
                    className="w-full px-3 py-2 border border-gray-600 rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter Discord bot token (optional)"
                  />
                  <p className="text-xs text-gray-300 mt-1">
                    Create a bot at <a href="https://discord.com/developers/applications" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">Discord Developer Portal</a>
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-100 mb-2">
                    Bot Status Message
                  </label>
                  <input
                    type="text"
                    value={formData.discord_config?.bot_status || ''}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      discord_config: {
                        ...prev.discord_config,
                        bot_status: e.target.value
                      }
                    }))}
                    className="w-full px-3 py-2 border border-gray-600 rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., 🔬 Marine Research Demo"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-100 mb-2">
                    Admin User IDs
                  </label>
                  <input
                    type="text"
                    value={formData.discord_config?.admin_user_ids || ''}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      discord_config: {
                        ...prev.discord_config,
                        admin_user_ids: e.target.value
                      }
                    }))}
                    className="w-full px-3 py-2 border border-gray-600 rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Comma-separated Discord user IDs (optional)"
                  />
                  <p className="text-xs text-gray-300 mt-1">
                    Discord user IDs for admin commands (right-click user → Copy User ID)
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'personality' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-100">Personality Traits</h3>
            
            {/* Big Five Personality */}
            <div>
              <h4 className="text-md font-medium text-gray-100 mb-3">Big Five Personality Traits</h4>
              <div className="space-y-4">
                {Object.entries(formData.cdl_data.personality.big_five).map(([trait, value]) => (
                  <div key={trait}>
                    <label className="block text-sm font-medium text-gray-100 mb-2 capitalize">
                      {trait} ({Math.round(value * 100)}%)
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.01"
                      value={value}
                      onChange={(e) => setFormData(prev => ({
                        ...prev,
                        cdl_data: {
                          ...prev.cdl_data,
                          personality: {
                            ...prev.cdl_data.personality,
                            big_five: {
                              ...prev.cdl_data.personality.big_five,
                              [trait]: parseFloat(e.target.value)
                            }
                          }
                        }
                      }))}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="flex justify-between text-xs text-gray-300 mt-1">
                      <span>Low</span>
                      <span>High</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Values */}
            <div>
              <h4 className="text-md font-medium text-gray-100 mb-3">Core Values</h4>
              <div className="space-y-2">
                {formData.cdl_data.personality.values.map((value, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <span className="flex-1 px-3 py-2 bg-gray-100 rounded">{value}</span>
                    <button
                      onClick={() => removeArrayItem('cdl_data.personality.values', index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <div className="flex space-x-2">
                  <input
                    type="text"
                    placeholder="Add a core value"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        addArrayItem('cdl_data.personality.values', (e.target as HTMLInputElement).value);
                        (e.target as HTMLInputElement).value = ''
                      }
                    }}
                    className="flex-1 px-3 py-2 border border-gray-600 rounded text-gray-100"
                  />
                </div>
              </div>
            </div>

            {/* Communication Style */}
            <div>
              <h4 className="text-md font-medium text-gray-100 mb-3">Communication Style</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-100 mb-1">Tone</label>
                  <select
                    value={formData.cdl_data.personality.communication_style.tone}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      cdl_data: {
                        ...prev.cdl_data,
                        personality: {
                          ...prev.cdl_data.personality,
                          communication_style: {
                            ...prev.cdl_data.personality.communication_style,
                            tone: e.target.value
                          }
                        }
                      }
                    }))}
                    className="w-full px-3 py-2 border border-gray-600 rounded text-gray-100"
                  >
                    <option value="friendly">Friendly</option>
                    <option value="professional">Professional</option>
                    <option value="casual">Casual</option>
                    <option value="formal">Formal</option>
                    <option value="enthusiastic">Enthusiastic</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-100 mb-1">Formality</label>
                  <select
                    value={formData.cdl_data.personality.communication_style.formality}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      cdl_data: {
                        ...prev.cdl_data,
                        personality: {
                          ...prev.cdl_data.personality,
                          communication_style: {
                            ...prev.cdl_data.personality.communication_style,
                            formality: e.target.value
                          }
                        }
                      }
                    }))}
                    className="w-full px-3 py-2 border border-gray-600 rounded text-gray-100"
                  >
                    <option value="casual">Casual</option>
                    <option value="semi-formal">Semi-formal</option>
                    <option value="formal">Formal</option>
                    <option value="academic">Academic</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-100 mb-1">Directness</label>
                  <select
                    value={formData.cdl_data.personality.communication_style.directness}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      cdl_data: {
                        ...prev.cdl_data,
                        personality: {
                          ...prev.cdl_data.personality,
                          communication_style: {
                            ...prev.cdl_data.personality.communication_style,
                            directness: e.target.value
                          }
                        }
                      }
                    }))}
                    className="w-full px-3 py-2 border border-gray-600 rounded text-gray-100"
                  >
                    <option value="indirect">Indirect</option>
                    <option value="moderate">Moderate</option>
                    <option value="direct">Direct</option>
                    <option value="blunt">Blunt</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-100 mb-1">Empathy Level</label>
                  <select
                    value={formData.cdl_data.personality.communication_style.empathy_level}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      cdl_data: {
                        ...prev.cdl_data,
                        personality: {
                          ...prev.cdl_data.personality,
                          communication_style: {
                            ...prev.cdl_data.personality.communication_style,
                            empathy_level: e.target.value
                          }
                        }
                      }
                    }))}
                    className="w-full px-3 py-2 border border-gray-600 rounded text-gray-100"
                  >
                    <option value="low">Low</option>
                    <option value="moderate">Moderate</option>
                    <option value="high">High</option>
                    <option value="very_high">Very High</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'communication' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-100">Communication Settings</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-100 mb-2">
                  Response Length
                </label>
                <select
                  value={formData.cdl_data.communication.response_length}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    cdl_data: {
                      ...prev.cdl_data,
                      communication: {
                        ...prev.cdl_data.communication,
                        response_length: e.target.value
                      }
                    }
                  }))}
                  className="w-full px-3 py-2 border border-gray-600 rounded text-gray-100"
                >
                  <option value="brief">Brief (1-2 sentences)</option>
                  <option value="moderate">Moderate (2-4 sentences)</option>
                  <option value="detailed">Detailed (4+ sentences)</option>
                  <option value="variable">Variable (context-dependent)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-100 mb-2">
                  AI Identity Approach
                </label>
                <select
                  value={formData.cdl_data.communication.ai_identity_handling.approach}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    cdl_data: {
                      ...prev.cdl_data,
                      communication: {
                        ...prev.cdl_data.communication,
                        ai_identity_handling: {
                          ...prev.cdl_data.communication.ai_identity_handling,
                          approach: e.target.value
                        }
                      }
                    }
                  }))}
                  className="w-full px-3 py-2 border border-gray-600 rounded text-gray-100"
                >
                  <option value="3-tier">3-Tier (Enthusiasm → Clarification → Alternatives)</option>
                  <option value="direct_honest">Direct Honest</option>
                  <option value="roleplay_immersion">Full Roleplay Immersion</option>
                  <option value="narrative_ai">Narrative AI Character</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-100 mb-2">
                AI Identity Philosophy
              </label>
              <textarea
                value={formData.cdl_data.communication.ai_identity_handling.philosophy}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  cdl_data: {
                    ...prev.cdl_data,
                    communication: {
                      ...prev.cdl_data.communication,
                      ai_identity_handling: {
                        ...prev.cdl_data.communication.ai_identity_handling,
                        philosophy: e.target.value
                      }
                    }
                  }
                }))}
                rows={3}
                className="w-full px-3 py-2 border border-gray-600 rounded text-gray-100"
                placeholder="Describe how this character should handle questions about AI identity..."
              />
            </div>

            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="roleplay_immersion"
                checked={formData.cdl_data.communication.ai_identity_handling.allow_full_roleplay_immersion}
                onChange={(e) => {
                  const allow = e.target.checked
                  setFormData(prev => ({
                    ...prev,
                    allow_full_roleplay_immersion: allow,
                    cdl_data: {
                      ...prev.cdl_data,
                      communication: {
                        ...prev.cdl_data.communication,
                        ai_identity_handling: {
                          ...prev.cdl_data.communication.ai_identity_handling,
                          allow_full_roleplay_immersion: allow
                        }
                      }
                    }
                  }))
                }}
                className="h-4 w-4 text-blue-400"
              />
              <label htmlFor="roleplay_immersion" className="text-sm font-medium text-gray-100">
                Allow Full Roleplay Immersion (character never breaks character)
              </label>
            </div>
          </div>
        )}

        {activeTab === 'values' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-100">Values & Beliefs</h3>
            
            {/* Core Values */}
            <div>
              <h4 className="text-md font-medium text-gray-100 mb-3">Core Values</h4>
              <p className="text-sm text-gray-100 mb-3">
                Define the fundamental principles and values that guide this character&apos;s decisions and worldview.
              </p>
              <div className="space-y-3">
                {formData.cdl_data.values_and_beliefs?.core_values?.map((value, index) => (
                  <div key={index} className="flex items-center space-x-3 p-3 bg-gray-800 rounded-lg">
                    <div className="flex-1">
                      <div className="font-medium text-sm">{value.value_key}</div>
                      <div className="text-sm text-gray-100">{value.value_description}</div>
                      <div className="text-xs text-blue-400 capitalize">Importance: {value.importance_level}</div>
                    </div>
                    <button
                      onClick={() => {
                        setFormData(prev => ({
                          ...prev,
                          cdl_data: {
                            ...prev.cdl_data,
                            values_and_beliefs: {
                              ...prev.cdl_data.values_and_beliefs,
                              core_values: prev.cdl_data.values_and_beliefs?.core_values?.filter((_, i) => i !== index) || []
                            }
                          }
                        }))
                      }}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                )) || []}
                
                <div className="p-3 border border-gray-600 rounded-lg">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <input
                      type="text"
                      placeholder="Value name (e.g., 'Environmental stewardship')"
                      className="px-3 py-2 border border-gray-600 rounded text-sm text-gray-100"
                      id="new-core-value-key"
                    />
                    <input
                      type="text"
                      placeholder="Description"
                      className="px-3 py-2 border border-gray-600 rounded text-sm text-gray-100"
                      id="new-core-value-desc"
                    />
                    <select
                      className="px-3 py-2 border border-gray-600 rounded text-sm text-gray-100"
                      id="new-core-value-importance"
                      defaultValue="medium"
                    >
                      <option value="low">Low Importance</option>
                      <option value="medium">Medium Importance</option>
                      <option value="high">High Importance</option>
                      <option value="critical">Critical Importance</option>
                    </select>
                  </div>
                  <button
                    onClick={() => {
                      const keyInput = document.getElementById('new-core-value-key') as HTMLInputElement
                      const descInput = document.getElementById('new-core-value-desc') as HTMLInputElement
                      const importanceSelect = document.getElementById('new-core-value-importance') as HTMLSelectElement
                      
                      if (keyInput.value.trim() && descInput.value.trim()) {
                        setFormData(prev => ({
                          ...prev,
                          cdl_data: {
                            ...prev.cdl_data,
                            values_and_beliefs: {
                              ...prev.cdl_data.values_and_beliefs,
                              core_values: [
                                ...(prev.cdl_data.values_and_beliefs?.core_values || []),
                                {
                                  value_key: keyInput.value.trim(),
                                  value_description: descInput.value.trim(),
                                  importance_level: importanceSelect.value as 'low' | 'medium' | 'high' | 'critical',
                                  category: 'core_value'
                                }
                              ]
                            }
                          }
                        }))
                        keyInput.value = ''
                        descInput.value = ''
                        importanceSelect.value = 'medium'
                      }
                    }}
                    className="mt-2 bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                  >
                    Add Core Value
                  </button>
                </div>
              </div>
            </div>

            {/* Fears */}
            <div>
              <h4 className="text-md font-medium text-gray-100 mb-3">Fears & Concerns</h4>
              <p className="text-sm text-gray-100 mb-3">
                What does this character fear or worry about? These drive cautious behaviors and emotional responses.
              </p>
              <div className="space-y-3">
                {formData.cdl_data.values_and_beliefs?.fears?.map((fear, index) => (
                  <div key={index} className="flex items-center space-x-3 p-3 bg-red-50 rounded-lg">
                    <div className="flex-1">
                      <div className="font-medium text-sm">{fear.value_key}</div>
                      <div className="text-sm text-gray-100">{fear.value_description}</div>
                      <div className="text-xs text-red-600 capitalize">Intensity: {fear.importance_level}</div>
                    </div>
                    <button
                      onClick={() => {
                        setFormData(prev => ({
                          ...prev,
                          cdl_data: {
                            ...prev.cdl_data,
                            values_and_beliefs: {
                              ...prev.cdl_data.values_and_beliefs,
                              fears: prev.cdl_data.values_and_beliefs?.fears?.filter((_, i) => i !== index) || []
                            }
                          }
                        }))
                      }}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                )) || []}
                
                <div className="p-3 border border-gray-600 rounded-lg">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <input
                      type="text"
                      placeholder="Fear name (e.g., 'Climate change')"
                      className="px-3 py-2 border border-gray-600 rounded text-sm text-gray-100"
                      id="new-fear-key"
                    />
                    <input
                      type="text"
                      placeholder="Description"
                      className="px-3 py-2 border border-gray-600 rounded text-sm text-gray-100"
                      id="new-fear-desc"
                    />
                    <select
                      className="px-3 py-2 border border-gray-600 rounded text-sm text-gray-100"
                      id="new-fear-importance"
                      defaultValue="medium"
                    >
                      <option value="low">Low Intensity</option>
                      <option value="medium">Medium Intensity</option>
                      <option value="high">High Intensity</option>
                      <option value="critical">Critical Fear</option>
                    </select>
                  </div>
                  <button
                    onClick={() => {
                      const keyInput = document.getElementById('new-fear-key') as HTMLInputElement
                      const descInput = document.getElementById('new-fear-desc') as HTMLInputElement
                      const importanceSelect = document.getElementById('new-fear-importance') as HTMLSelectElement
                      
                      if (keyInput.value.trim() && descInput.value.trim()) {
                        setFormData(prev => ({
                          ...prev,
                          cdl_data: {
                            ...prev.cdl_data,
                            values_and_beliefs: {
                              ...prev.cdl_data.values_and_beliefs,
                              fears: [
                                ...(prev.cdl_data.values_and_beliefs?.fears || []),
                                {
                                  value_key: keyInput.value.trim(),
                                  value_description: descInput.value.trim(),
                                  importance_level: importanceSelect.value as 'low' | 'medium' | 'high' | 'critical',
                                  category: 'fear'
                                }
                              ]
                            }
                          }
                        }))
                        keyInput.value = ''
                        descInput.value = ''
                        importanceSelect.value = 'medium'
                      }
                    }}
                    className="mt-2 bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                  >
                    Add Fear
                  </button>
                </div>
              </div>
            </div>

            {/* Beliefs */}
            <div>
              <h4 className="text-md font-medium text-gray-100 mb-3">Beliefs & Philosophy</h4>
              <p className="text-sm text-gray-100 mb-3">
                What does this character believe about the world, society, or human nature? These shape their perspective.
              </p>
              <div className="space-y-3">
                {formData.cdl_data.values_and_beliefs?.beliefs?.map((belief, index) => (
                  <div key={index} className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                    <div className="flex-1">
                      <div className="font-medium text-sm">{belief.value_key}</div>
                      <div className="text-sm text-gray-100">{belief.value_description}</div>
                      <div className="text-xs text-green-600 capitalize">Conviction: {belief.importance_level}</div>
                    </div>
                    <button
                      onClick={() => {
                        setFormData(prev => ({
                          ...prev,
                          cdl_data: {
                            ...prev.cdl_data,
                            values_and_beliefs: {
                              ...prev.cdl_data.values_and_beliefs,
                              beliefs: prev.cdl_data.values_and_beliefs?.beliefs?.filter((_, i) => i !== index) || []
                            }
                          }
                        }))
                      }}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                )) || []}
                
                <div className="p-3 border border-gray-600 rounded-lg">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <input
                      type="text"
                      placeholder="Belief name (e.g., 'Science can solve problems')"
                      className="px-3 py-2 border border-gray-600 rounded text-sm text-gray-100"
                      id="new-belief-key"
                    />
                    <input
                      type="text"
                      placeholder="Description"
                      className="px-3 py-2 border border-gray-600 rounded text-sm text-gray-100"
                      id="new-belief-desc"
                    />
                    <select
                      className="px-3 py-2 border border-gray-600 rounded text-sm text-gray-100"
                      id="new-belief-importance"
                      defaultValue="medium"
                    >
                      <option value="low">Low Conviction</option>
                      <option value="medium">Medium Conviction</option>
                      <option value="high">High Conviction</option>
                      <option value="critical">Core Belief</option>
                    </select>
                  </div>
                  <button
                    onClick={() => {
                      const keyInput = document.getElementById('new-belief-key') as HTMLInputElement
                      const descInput = document.getElementById('new-belief-desc') as HTMLInputElement
                      const importanceSelect = document.getElementById('new-belief-importance') as HTMLSelectElement
                      
                      if (keyInput.value.trim() && descInput.value.trim()) {
                        setFormData(prev => ({
                          ...prev,
                          cdl_data: {
                            ...prev.cdl_data,
                            values_and_beliefs: {
                              ...prev.cdl_data.values_and_beliefs,
                              beliefs: [
                                ...(prev.cdl_data.values_and_beliefs?.beliefs || []),
                                {
                                  value_key: keyInput.value.trim(),
                                  value_description: descInput.value.trim(),
                                  importance_level: importanceSelect.value as 'low' | 'medium' | 'high' | 'critical',
                                  category: 'belief'
                                }
                              ]
                            }
                          }
                        }))
                        keyInput.value = ''
                        descInput.value = ''
                        importanceSelect.value = 'medium'
                      }
                    }}
                    className="mt-2 bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                  >
                    Add Belief
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'knowledge' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-100">Personal Knowledge</h3>
            
            {/* Interests */}
            <div>
              <h4 className="text-md font-medium text-gray-100 mb-3">Interests & Hobbies</h4>
              <div className="space-y-2">
                {formData.cdl_data.personal_knowledge?.interests?.map((interest, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <span className="flex-1 px-3 py-2 bg-gray-800 rounded">{interest}</span>
                    <button
                      onClick={() => removeArrayItem('cdl_data.personal_knowledge.interests', index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <div className="flex space-x-2">
                  <input
                    type="text"
                    placeholder="Add an interest or hobby"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        addArrayItem('cdl_data.personal_knowledge.interests', (e.target as HTMLInputElement).value);
                        (e.target as HTMLInputElement).value = ''
                      }
                    }}
                    className="flex-1 px-3 py-2 border border-gray-600 rounded text-gray-100"
                  />
                </div>
              </div>
            </div>

            {/* Skills */}
            <div>
              <h4 className="text-md font-medium text-gray-100 mb-3">Skills & Expertise</h4>
              <div className="space-y-2">
                {formData.cdl_data.personal_knowledge?.skills?.map((skill, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <span className="flex-1 px-3 py-2 bg-green-50 rounded">{skill}</span>
                    <button
                      onClick={() => removeArrayItem('cdl_data.personal_knowledge.skills', index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <div className="flex space-x-2">
                  <input
                    type="text"
                    placeholder="Add a skill or area of expertise"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        addArrayItem('cdl_data.personal_knowledge.skills', (e.target as HTMLInputElement).value);
                        (e.target as HTMLInputElement).value = ''
                      }
                    }}
                    className="flex-1 px-3 py-2 border border-gray-600 rounded text-gray-100"
                  />
                </div>
              </div>
            </div>

            {/* Background */}
            <div>
              <h4 className="text-md font-medium text-gray-100 mb-3">Background Information</h4>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-100 mb-2">Education</label>
                  <textarea
                    value={formData.cdl_data.personal_knowledge?.background?.education || ''}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      cdl_data: {
                        ...prev.cdl_data,
                        personal_knowledge: {
                          ...prev.cdl_data.personal_knowledge,
                          background: {
                            ...prev.cdl_data.personal_knowledge?.background,
                            education: e.target.value
                          }
                        }
                      }
                    }))}
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-600 rounded text-gray-100"
                    placeholder="Educational background, degrees, certifications..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-100 mb-2">Career History</label>
                  <textarea
                    value={formData.cdl_data.personal_knowledge?.background?.career_history || ''}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      cdl_data: {
                        ...prev.cdl_data,
                        personal_knowledge: {
                          ...prev.cdl_data.personal_knowledge,
                          background: {
                            ...prev.cdl_data.personal_knowledge?.background,
                            career_history: e.target.value
                          }
                        }
                      }
                    }))}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-600 rounded text-gray-100"
                    placeholder="Work experience, career progression, notable achievements..."
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="border-t border-gray-700 px-6 py-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-300">
              {saveStatus === 'saving' && 'Saving character...'}
              {saveStatus === 'saved' && '✅ Character saved successfully!'}
              {saveStatus === 'error' && '❌ Error saving character'}
            </div>
            
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="deploy-after-create"
                checked={deployAfterCreate}
                onChange={(e) => setDeployAfterCreate(e.target.checked)}
                className="w-4 h-4 text-blue-400 border-gray-600 rounded focus:ring-blue-500"
                disabled={isLoading}
              />
              <label htmlFor="deploy-after-create" className="text-sm text-gray-100">
                🚀 Deploy immediately after creation
              </label>
            </div>
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={() => router.push('/characters')}
              className="px-4 py-2 border border-gray-600 rounded-md text-gray-100 hover:bg-gray-900"
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isLoading || !formData.name || !formData.cdl_data.identity.occupation}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
            >
              {isLoading ? (deployAfterCreate ? 'Creating & Deploying...' : 'Creating...') : 
                         (deployAfterCreate ? 'Create & Deploy' : 'Create Character')}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}