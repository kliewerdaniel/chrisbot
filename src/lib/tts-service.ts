import { spawn } from 'child_process'
import path from 'path'

export interface TTSOptions {
  text: string
  model?: string
  outputPath?: string
}

export class TTSService {
  private pythonPath: string
  private ttsPath: string

  constructor() {
    // Use the Python virtual environment we set up
    this.pythonPath = path.join(process.cwd(), 'TTS', 'venv311', 'bin', 'python')
    this.ttsPath = path.join(process.cwd(), 'TTS')
  }

  async generateSpeech(options: TTSOptions): Promise<string> {
    const { text, model = 'tts_models/en/ljspeech/tacotron2-DDC', outputPath = 'output.wav' } = options

    return new Promise((resolve, reject) => {
      const escapedText = text.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\n/g, '\\n').replace(/\r/g, '\\r').replace(/\t/g, '\\t')

      const pythonProcess = spawn(this.pythonPath, [
        '-c',
        `
import sys
sys.path.insert(0, r'''${this.ttsPath}''')
from TTS.api import TTS
import os
import torch

# Fix for PyTorch 2.6+ security changes
torch.serialization.add_safe_globals(['TTS.utils.radam.RAdam'])

# Initialize TTS
tts = TTS(r'''${model}''')

# Generate speech
output_file = r'''${outputPath}'''
tts.tts_to_file(text=r'''${escapedText}''', file_path=output_file)
        `
      ])

      let stderr = ''

      pythonProcess.stdout.on('data', (data: Buffer) => {
        // Acknowledge stdout but don't use it
      })

      pythonProcess.stderr.on('data', (data: Buffer) => {
        stderr += data.toString()
      })

      pythonProcess.on('close', (code: number | null) => {
        if (code === 0) {
          resolve(outputPath)
        } else {
          reject(new Error(`TTS generation failed: ${stderr}`))
        }
      })

      pythonProcess.on('error', (error: Error) => {
        reject(error)
      })
    })
  }

  async listAvailableModels(): Promise<string[]> {
    return new Promise((resolve, reject) => {
      const pythonProcess = spawn(this.pythonPath, [
        '-c',
        `
import sys
sys.path.insert(0, '${this.ttsPath}')
from TTS.api import TTS

# Get available models
manager = TTS().list_models()
models = manager.list_tts_models()
for model in models:
    print(model)
        `
      ])

      let stdout = ''
      let stderr = ''

      pythonProcess.stdout.on('data', (data: Buffer) => {
        stdout += data.toString()
      })

      pythonProcess.stderr.on('data', (data: Buffer) => {
        stderr += data.toString()
      })

      pythonProcess.on('close', (code: number | null) => {
        if (code === 0) {
          const models = stdout.trim().split('\n').filter(model => model.length > 0)
          resolve(models)
        } else {
          reject(new Error(`Failed to list models: ${stderr}`))
        }
      })

      pythonProcess.on('error', (error: Error) => {
        reject(error)
      })
    })
  }
}
