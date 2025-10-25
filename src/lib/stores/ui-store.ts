import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { UISettingsState } from './types'

export const useUIStore = create<UISettingsState>()(
  persist(
    (set, get) => ({
      // Dialog states
      isEditorOpen: false,
      isHistoryOpen: false,
      editingSessionId: null,
      editingTitle: '',

      // TTS settings
      voices: [],
      selectedVoice: '',
      playingMessageId: null,
      voiceEnhancement: true,
      autoPlayEnabled: false,

      // Coqui TTS settings
      ttsModels: [],
      selectedTTSModel: 'tts_models/en/ljspeech/tacotron2-DDC',
      isTTSLoading: false,
      ttsLoadingMessages: new Set<number>(),

      // Dialog actions
      setIsEditorOpen: (isEditorOpen) => set({ isEditorOpen }),
      setIsHistoryOpen: (isHistoryOpen) => set({ isHistoryOpen }),
      setEditingSessionId: (editingSessionId) => set({ editingSessionId }),
      setEditingTitle: (editingTitle) => set({ editingTitle }),

      // TTS actions
      loadVoices: () => {
        const availableVoices = speechSynthesis.getVoices()
        set({ voices: availableVoices })
        const { selectedVoice } = get()
        if (availableVoices.length > 0 && !selectedVoice) {
          set({ selectedVoice: availableVoices[0].voiceURI })
        }
      },

      setSelectedVoice: (selectedVoice) => set({ selectedVoice }),
      setPlayingMessageId: (playingMessageId) => set({ playingMessageId }),
      setVoiceEnhancement: (voiceEnhancement) => set({ voiceEnhancement }),
      setAutoPlayEnabled: (autoPlayEnabled) => set({ autoPlayEnabled }),

      // Coqui TTS actions
      loadTTSModels: async () => {
        try {
          set({ isTTSLoading: true })
          const response = await fetch('/api/tts')
          if (response.ok) {
            const data = await response.json()
            if (data.success) {
              // Transform the models array to include descriptions
              const modelsWithDescriptions = data.models.map((modelName: string) => ({
                name: modelName,
                description: modelName.split('/').join(' • '),
                language: modelName.split('/')[1] || 'en'
              }))
              set({ ttsModels: modelsWithDescriptions })
            }
          }
        } catch (error) {
          console.error('Failed to load TTS models:', error)
        } finally {
          set({ isTTSLoading: false })
        }
      },

      setSelectedTTSModel: (selectedTTSModel) => set({ selectedTTSModel }),
      setTTSLoading: (isTTSLoading) => set({ isTTSLoading }),

      // TTS loading message actions
      addTTSLoadingMessage: (messageIndex: number) => set((state) => ({
        ttsLoadingMessages: new Set([...state.ttsLoadingMessages, messageIndex])
      })),
      removeTTSLoadingMessage: (messageIndex: number) => set((state) => {
        const newSet = new Set(state.ttsLoadingMessages)
        newSet.delete(messageIndex)
        return { ttsLoadingMessages: newSet }
      }),
      isMessageTTSLoading: (messageIndex: number) => {
        const { ttsLoadingMessages } = get()
        return ttsLoadingMessages.has(messageIndex)
      },
    }),
    {
      name: 'ui-store',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        selectedVoice: state.selectedVoice,
        voiceEnhancement: state.voiceEnhancement,
        autoPlayEnabled: state.autoPlayEnabled,
        selectedTTSModel: state.selectedTTSModel,
      }),
    }
  )
)
