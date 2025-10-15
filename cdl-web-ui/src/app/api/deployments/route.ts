import { NextResponse } from 'next/server'

interface DeployedBot {
  name: string
  container_name: string
  endpoint: string
  status: string
  health: 'healthy' | 'unhealthy' | 'unknown'
  uptime: string
}

export async function GET() {
  try {
    // In quickstart mode, we have one known assistant bot
    const assistantEndpoint = process.env.WHISPERENGINE_API_URL || 'http://whisperengine-assistant:9090'
    
    // Check if the assistant is responding
    let assistantHealth: 'healthy' | 'unhealthy' | 'unknown' = 'unknown'
    let assistantStatus = 'checking...'
    
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000)
      
      const healthResponse = await fetch(`${assistantEndpoint}/health`, {
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      if (healthResponse.ok) {
        assistantHealth = 'healthy'
        assistantStatus = 'running'
      } else {
        assistantHealth = 'unhealthy'
        assistantStatus = `error: ${healthResponse.status}`
      }
    } catch (error) {
      assistantHealth = 'unhealthy'
      assistantStatus = 'not responding'
    }
    
    const deployedBots: DeployedBot[] = [
      {
        name: 'assistant',
        container_name: 'whisperengine-assistant',
        endpoint: assistantEndpoint,
        status: assistantStatus,
        health: assistantHealth,
        uptime: 'unknown'
      }
    ]
    
    return NextResponse.json({
      deployed_bots: deployedBots,
      total_deployed: deployedBots.length,
      infrastructure_status: assistantHealth === 'healthy' ? 'running' : 'degraded'
    })
  } catch (error) {
    console.error('Error getting deployments:', error)
    return NextResponse.json(
      { error: 'Failed to get deployment information' },
      { status: 500 }
    )
  }
}

// Health check endpoint for a specific bot
export async function POST(request: Request) {
  try {
    const { bot_name } = await request.json()
    
    if (!bot_name) {
      return NextResponse.json(
        { error: 'Bot name is required' },
        { status: 400 }
      )
    }
    
    // In quickstart mode, we only have the assistant bot
    if (bot_name !== 'assistant') {
      return NextResponse.json({
        bot_name,
        container_status: 'not_found',
        health_check: 'not_deployed'
      })
    }
    
    const assistantEndpoint = process.env.WHISPERENGINE_API_URL || 'http://whisperengine-assistant:9090'
    
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000)
      
      const healthResponse = await fetch(`${assistantEndpoint}/health`, {
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      return NextResponse.json({
        bot_name,
        container_status: 'running',
        health_check: healthResponse.ok ? 'healthy' : 'unhealthy',
        health_status: healthResponse.status,
        endpoint: assistantEndpoint
      })
    } catch (healthError) {
      return NextResponse.json({
        bot_name,
        container_status: 'unknown',
        health_check: 'unhealthy',
        error: 'Health endpoint not responding',
        endpoint: assistantEndpoint
      })
    }
  } catch (error) {
    console.error('Error checking bot health:', error)
    return NextResponse.json(
      { error: 'Failed to check bot health' },
      { status: 500 }
    )
  }
}