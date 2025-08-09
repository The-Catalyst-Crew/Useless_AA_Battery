import { NextRequest, NextResponse } from 'next/server'

interface PersonaResult {
  name: string
  description: string
  personality: string
  background: string
  traits: string[]
}

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const imageFile = formData.get('image') as File

    if (!imageFile) {
      return NextResponse.json(
        { error: 'No image file provided' },
        { status: 400 }
      )
    }

    // Convert image to base64 for analysis
    const bytes = await imageFile.arrayBuffer()
    const base64Image = Buffer.from(bytes).toString('base64')
    const imageDataUrl = `data:${imageFile.type};base64,${base64Image}`

    // Get API key from environment variables
    const apiKey = process.env.API_KEY
    if (!apiKey) {
      throw new Error('Missing API_KEY in environment variables')
    }

    // Use OpenAI API
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'qwen/qwen2.5-vl-72b-instruct:free',
        messages: [
          {
            role: 'system',
            content: `You are a creative AI persona generator. When given an image, you must:

1. First, carefully analyze and identify the main object or subject in the image
2. Then create a detailed, imaginative persona for it

Your response should be a JSON object with the following structure:
{
  "name": "A creative name for the object/person",
  "description": "A brief description of what the object is and its current state based on the image",
  "personality": "Detailed personality traits, quirks, and characteristics",
  "background": "An imaginative backstory explaining where it came from, its experiences, and how it got to where it is now",
  "traits": ["trait1", "trait2", "trait3", "trait4", "trait5"]
}

Be creative, whimsical, and engaging. Make the persona feel alive and unique. For inanimate objects, give them human-like qualities and emotions. For people or animals, create an imaginative backstory that goes beyond what's visible in the image.

IMPORTANT: You must respond with valid JSON only, no additional text.`
          },
          {
            role: 'user',
            content: [
              {
                type: 'text',
                text: 'Please analyze this image and create a detailed persona for the main object or subject in it.'
              },
              {
                type: 'image_url',
                image_url: {
                  url: imageDataUrl
                }
              }
            ]
          }
        ],
        temperature: 0.8,
        max_tokens: 1000
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

    const jsonMatch = responseContent.match(/\{[\s\S]*\}/)
    if (!jsonMatch) {
      throw new Error('Invalid response format from AI')
    }

    const persona: PersonaResult = JSON.parse(jsonMatch[0])

    return NextResponse.json({
      success: true,
      persona
    })

  } catch (error) {
    console.error('Error generating persona:', error)
    return NextResponse.json(
      { error: 'Failed to generate persona' },
      { status: 500 }
    )
  }
}