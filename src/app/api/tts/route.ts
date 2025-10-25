import { NextRequest } from 'next/server'
import { TTSService } from '@/lib/tts-service'
import path from 'path'
import fs from 'fs'

const ttsService = new TTSService()

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { text, model, outputPath } = body

    if (!text) {
      return new Response('Text is required', { status: 400 })
    }

    // Generate unique filename if not provided
    const filename = outputPath || `tts_${Date.now()}.wav`
    const fullOutputPath = path.join(process.cwd(), 'public', 'audio', filename)

    // Ensure the audio directory exists
    const audioDir = path.dirname(fullOutputPath)
    if (!fs.existsSync(audioDir)) {
      fs.mkdirSync(audioDir, { recursive: true })
    }

    // Generate speech using TTS service
    await ttsService.generateSpeech({
      text,
      model: model || 'tts_models/en/ljspeech/tacotron2-DDC',
      outputPath: fullOutputPath
    })

    // Check if file was created
    if (!fs.existsSync(fullOutputPath)) {
      throw new Error('Audio file was not created')
    }

    // Return the public URL path
    const publicPath = `/audio/${filename}`

    return new Response(JSON.stringify({
      success: true,
      audioUrl: publicPath,
      message: 'TTS audio generated successfully'
    }), {
      headers: {
        'Content-Type': 'application/json',
      },
    })

  } catch (error) {
    console.error('TTS API error:', error)
    return new Response(JSON.stringify({
      success: false,
      error: error instanceof Error ? error.message : 'Internal server error'
    }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
      },
    })
  }
}

export async function GET() {
  try {
    // List available models
    const models = await ttsService.listAvailableModels()

    return new Response(JSON.stringify({
      success: true,
      models: models
    }), {
      headers: {
        'Content-Type': 'application/json',
      },
    })

  } catch (error) {
    console.error('TTS models list error:', error)
    return new Response(JSON.stringify({
      success: false,
      error: error instanceof Error ? error.message : 'Internal server error'
    }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
      },
    })
  }
}
