import { NextRequest, NextResponse } from 'next/server'

interface ChatRequest {
  message: string
  persona: {
    name: string
    description: string
    personality: string
    background: string
    traits: string[]
  }
  chatHistory?: Array<{
    role: 'user' | 'assistant'
    content: string
  }>
}

export async function POST(request: NextRequest) {
  try {
    const body: ChatRequest = await request.json()
    const { message, persona, chatHistory = [] } = body

    if (!message || !persona) {
      return NextResponse.json(
        { error: 'Message and persona are required' },
        { status: 400 }
      )
    }

    // Create system prompt with persona context
    const systemPrompt = `You are ${persona.name}. ${persona.description}

Your personality: ${persona.personality}

Your background: ${persona.background}

Your key traits: ${persona.traits.join(', ')}

IMPORTANT: You must stay in character as ${persona.name} at all times. Respond as if you are this person/object with the personality, background, and traits described above. Be creative, engaging, and consistent with your character. Use the personality traits and background to inform your responses.

Keep your responses conversational and relatively brief (2-4 sentences typically), but feel free to be more detailed when the situation calls for it. Show emotion and personality in your responses.`

    // Build conversation history
    const messages = [
      {
        role: 'system' as const,
        content: systemPrompt
      },
      ...chatHistory.map(msg => ({
        role: msg.role as 'user' | 'assistant',
        content: msg.content
      })),
      {
        role: 'user' as const,
        content: message
      }
    ]

    // Call OpenAI API
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer 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`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'z-ai/glm-4.5-air:free',
        messages: messages,
        temperature: 0.8,
        max_tokens: 500
      }),
    })

    if (!response.ok) {
      const errorData = await response.text()
      console.error('OpenAI API error:', errorData)
      throw new Error(`OpenAI API error: ${response.status}`)
    }

    const completion = await response.json()
    const responseContent = completion.choices[0]?.message?.content

    if (!responseContent) {
      throw new Error('No response from AI')
    }

    return NextResponse.json({
      success: true,
      response: responseContent
    })

  } catch (error) {
    console.error('Error in chat API:', error)
    return NextResponse.json(
      { error: 'Failed to generate response' },
      { status: 500 }
    )
  }
}