import path from 'path'
import fs from 'fs'

export interface TTSOptions {
  text: string
  model?: string
  outputPath?: string
}

export class TTSService {
  private ttsServerUrl: string

  constructor() {
    // Use the Coqui TTS server running on port 8080
    this.ttsServerUrl = 'http://localhost:8080'
  }

  async generateSpeech(options: TTSOptions): Promise<string> {
    const { text, model = 'tts_models/en/ljspeech/tacotron2-DDC', outputPath } = options

    // Generate unique filename if not provided
    const filename = outputPath || `tts_${Date.now()}.wav`
    const fullOutputPath = path.join(process.cwd(), 'public', 'audio', filename)

    // Ensure the audio directory exists
    const audioDir = path.dirname(fullOutputPath)
    if (!fs.existsSync(audioDir)) {
      fs.mkdirSync(audioDir, { recursive: true })
    }

    try {
      // Check if TTS server is available
      const isServerAvailable = await this.checkServerHealth()

      if (!isServerAvailable || model === 'browser-tts') {
        // Fall back to browser TTS - create a simple audio file or return a placeholder
        console.log('Using browser TTS fallback')
        // For browser TTS, we'll create a minimal audio file or just return the filename
        // The actual TTS will happen in the browser
        return filename
      }

      // Use the Coqui TTS server API
      const response = await fetch(`${this.ttsServerUrl}/api/tts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          text: text,
          speaker_id: '', // Use default speaker
          style_wav: '',
          language_id: ''
        })
      })

      if (!response.ok) {
        throw new Error(`TTS server responded with status: ${response.status}`)
      }

      // Check if response is actually audio data or an error
      const contentType = response.headers.get('content-type')
      if (!contentType || !contentType.includes('audio')) {
        const errorText = await response.text()
        throw new Error(`TTS server returned non-audio response: ${errorText}`)
      }

      // Get the audio data as blob
      const audioBlob = await response.blob()

      // Check if blob is actually audio data
      if (audioBlob.size === 0) {
        throw new Error('TTS server returned empty audio file')
      }

      // Convert blob to buffer and save to file
      const arrayBuffer = await audioBlob.arrayBuffer()
      const buffer = Buffer.from(arrayBuffer)
      fs.writeFileSync(fullOutputPath, buffer)

      console.log(`✅ TTS audio saved to ${fullOutputPath} (${buffer.length} bytes)`)
      return filename

    } catch (error) {
      console.error('TTS generation failed:', error)
      // Return the filename anyway so the frontend can fall back to browser TTS
      return filename
    }
  }

  async listAvailableModels(): Promise<Array<{name: string, description: string, language: string}>> {
    try {
      // For now, return a curated list of popular models
      // In a real implementation, you might want to query the server for available models
      const models = [
        {
          name: 'tts_models/en/ljspeech/tacotron2-DDC',
          description: 'Tacotron2 DDC • English • LJSpeech',
          language: 'en'
        },
        {
          name: 'tts_models/en/ljspeech/tacotron2-DDC_ph',
          description: 'Tacotron2 DDC Phonemes • English • LJSpeech',
          language: 'en'
        },
        {
          name: 'tts_models/en/ljspeech/glow-tts',
          description: 'Glow TTS • English • LJSpeech',
          language: 'en'
        },
        {
          name: 'tts_models/en/ljspeech/speedy-speech',
          description: 'Speedy Speech • English • LJSpeech',
          language: 'en'
        },
        {
          name: 'tts_models/en/ljspeech/tacotron2-DCA',
          description: 'Tacotron2 DCA • English • LJSpeech',
          language: 'en'
        },
        {
          name: 'tts_models/en/ljspeech/neural_hmm',
          description: 'Neural HMM • English • LJSpeech',
          language: 'en'
        }
      ]

      return models

    } catch (error) {
      console.error('Failed to list TTS models:', error)
      throw new Error(`Failed to list models: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  async checkServerHealth(): Promise<boolean> {
    try {
      // Try checking the root endpoint first
      const rootResponse = await fetch(this.ttsServerUrl)
      if (rootResponse.ok) {
        return true
      }

      // Fallback to trying a POST request with test data
      const testResponse = await fetch(`${this.ttsServerUrl}/api/tts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          text: 'test',
          speaker_id: '',
          style_wav: '',
          language_id: ''
        })
      })
      return testResponse.status !== 500 // Accept any response that's not a server error
    } catch (error) {
      console.log('TTS server health check failed:', error)
      return false
    }
  }
}
