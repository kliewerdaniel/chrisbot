<div align="center">

# 🤖 ChrisBot

*An advanced AI chatbot platform with Graph RAG and Text-to-Speech capabilities*

[![Next.js](https://img.shields.io/badge/Next.js-16.0-black.svg)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4.0-38B2AC.svg)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Jest](https://img.shields.io/badge/Jest-testing-green.svg)](https://jestjs.io/)
[![Playwright](https://img.shields.io/badge/Playwright-e2e-blue.svg)](https://playwright.dev/)

*Run AI conversations locally with enhanced context and speech synthesis*

</div>

---

## 📋 Table of Contents

- [✨ Features](#-features)
- [🚀 Quick Start](#-quick-start)
- [🛠️ Tech Stack](#️-tech-stack)
- [📁 Project Structure](#-project-structure)
- [🔧 Configuration](#-configuration)
- [🧪 Testing](#-testing)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [🆘 Troubleshooting](#-troubleshooting)

## ✨ Features

### 💬 **Advanced AI Chat**
- **Local LLM Integration**: Powered by Ollama for privacy-first AI conversations
- **Graph RAG**: Enhanced context through knowledge graphs and vector search
- **Multiple Models**: Support for various Ollama models (Mistral, Llama, etc.)
- **Real-time Streaming**: Live response generation with instant feedback
- **Session Management**: Save, load, and manage chat conversations

### 🎵 **Text-to-Speech (TTS)**
- **Coqui TTS Engine**: Professional-grade speech synthesis
- **50+ Voice Models**: Multiple languages and voice styles
- **Dual Playback**: Coqui TTS + browser fallback for reliability
- **Voice Enhancement**: Audio processing for improved clarity
- **Auto-play**: Automatic speech generation for responses

### 🎨 **Modern Interface**
- **Responsive Design**: Optimized for desktop and mobile devices
- **Dark/Light Theme**: Customizable appearance with system preference detection
- **Message Threading**: Conversation history with context preservation
- **Code Highlighting**: Syntax highlighting for code snippets
- **Copy/Share**: Easy message copying and clipboard integration

### 🔧 **System Prompts**
- **Customizable AI Behavior**: Define different AI personalities and expertise
- **JSON-Based Prompts**: Easy to create and modify prompt templates
- **Prompt Switching**: Change AI behavior mid-conversation

### 🗂️ **Data Ingestion**
- **Reddit Integration**: Import and process Reddit data for RAG
- **Chat History Analysis**: Process existing conversation data
- **Automatic Knowledge Graph**: Build contextual relationships
- **Vector Embeddings**: ChromaDB integration for semantic search

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18.18.0 or later ([Download here](https://nodejs.org/))
- **Python** 3.8+ ([Download here](https://python.org/))
- **Ollama** ([Install here](https://ollama.ai/))
- **Git** ([Download here](https://git-scm.com/))

### 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/kliewerdaniel/chrisbot.gi
   cd chrisbot
   ```

2. **Install Node.js dependencies**
   ```bash
   npm install
   ```

3. **Start Ollama service**
   ```bash
   ollama serve
   ```

4. **Download an AI model** (in another terminal)
   ```bash
   ollama pull mistral
   ```

5. **Initialize knowledge graph** (optional, for enhanced context)
   ```bash
   bash scripts/init-knowledge-graph.sh
   ```

6. **Start the development server**
   ```bash
   npm run dev
   ```

7. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

### 🎯 Basic Usage

1. **Select a System Prompt**: Choose from available AI personalities
2. **Choose an AI Model**: Pick your preferred Ollama model
3. **Start Chatting**: Type messages and get AI responses
4. **Enable TTS**: Toggle voice playback for responses
5. **Save Sessions**: Your conversations are automatically stored

## 🛠️ Tech Stack

### Frontend
- **[Next.js 16](https://nextjs.org/)** - React framework with App Router
- **[React 19](https://react.dev/)** - UI library with concurrent features
- **[TypeScript 5](https://www.typescriptlang.org/)** - Type-safe JavaScript
- **[Tailwind CSS 4](https://tailwindcss.com/)** - Utility-first CSS framework
- **[shadcn/ui](https://ui.shadcn.com/)** - Accessible component library
- **[Zustand](https://zustand-demo.pmnd.rs/)** - Lightweight state management

### Backend & AI/ML
- **[Ollama](https://ollama.ai/)** - Local LLM inference engine
- **[Coqui TTS](https://github.com/coqui-ai/TTS)** - Text-to-speech synthesis
- **[ChromaDB](https://www.trychroma.com/)** - Vector database for embeddings
- **[NetworkX](https://networkx.org/)** - Graph analysis and manipulation
- **[SQLite](https://sqlite.org/)** - Local database for chat history

### Development & Testing
- **[ESLint](https://eslint.org/)** - JavaScript/TypeScript linting
- **[Prettier](https://prettier.io/)** - Code formatting
- **[Jest](https://jestjs.io/)** - Unit and integration testing
- **[Playwright](https://playwright.dev/)** - End-to-end testing
- **[Husky](https://typicode.github.io/husky/)** - Git hooks

## 📁 Project Structure

```
chrisbot/
├── src/
│   ├── app/                 # Next.js App Router
│   │   ├── api/            # API routes (chat, TTS)
│   │   ├── globals.css     # Global styles
│   │   └── layout.tsx      # Root layout
│   ├── components/         # React components
│   │   ├── Chat.tsx        # Main chat interface
│   │   └── ui/             # shadcn/ui components
│   ├── lib/                # Utility libraries
│   │   ├── stores/         # Zustand state management
│   │   └── tts-service.ts  # TTS service integration
│   └── utils/              # Helper functions
├── scripts/                # Python scripts
│   ├── graph_rag_query.py # Graph RAG queries
│   ├── ingest_reddit_data_ollama.py # Data ingestion
│   └── init-knowledge-graph.sh # Setup script
├── data/                   # Knowledge graph data
├── public/                 # Static assets
├── tests/                  # Test suites
├── TTS/                    # Coqui TTS submodule
└── package.json
```

## 🔧 Configuration

### Environment Variables

Create a `.env.local` file in the root directory:

```bash
# Ollama Configuration (optional - defaults provided)
OLLAMA_HOST=http://localhost:8374

# TTS Configuration (optional)
TTS_PYTHON_PATH=./TTS/venv/bin/python
TTS_MODEL=tts_models/en/ljspeech/tacotron2-DDC
```

### System Prompts

Edit `data/system-prompts.json` to customize AI behavior:

```json
[
  {
    "id": "default",
    "name": "General Assistant",
    "prompt": "You are a helpful AI assistant..."
  }
]
```

### Knowledge Graph Setup

For enhanced context with Graph RAG:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Initialize knowledge graph with sample data
bash scripts/init-knowledge-graph.sh

# Or ingest custom Reddit data
python3 scripts/ingest_reddit_data_ollama.py --subreddit your_subreddit
```

## 🧪 Testing

### Running Tests

```bash
# Unit tests
npm test

# E2E tests
npm run test:e2e

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage
```

### Manual Testing

```bash
# Lint code
npm run lint

# Type checking
npm run type-check

# Format code
npm run format
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature`
3. **Make** your changes and add tests
4. **Run** tests: `npm test`
5. **Commit** changes: `git commit -m 'Add your feature'`
6. **Push** to branch: `git push origin feature/your-feature`
7. **Open** a Pull Request

### Development Guidelines

- **Code Style**: Follow ESLint and Prettier configurations
- **Type Safety**: Use TypeScript strictly with proper typing
- **Testing**: Add tests for new features and bug fixes
- **Documentation**: Update README for significant changes
- **Commits**: Use conventional commit format

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

**❌ Ollama connection failed**
```
Error: Failed to connect to Ollama
```
- Ensure Ollama is running: `ollama serve`
- Check if a model is downloaded: `ollama pull mistral`
- Verify OLLAMA_HOST in environment variables

**❌ TTS not working**
```
Error: TTS generation failed
```
- Check Python path in TTS service configuration
- Ensure TTS submodule is properly initialized
- Install Coqui TTS dependencies: `pip install -r TTS/requirements.txt`

**❌ Build fails**
```bash
npm run build
```
- Clear node_modules: `rm -rf node_modules && npm install`
- Check TypeScript errors: `npm run type-check`
- Ensure all dependencies are compatible

**❌ Tests failing**
- Update dependencies: `npm update`
- Clear test cache: `npm test -- --clearCache`
- Check Node.js version compatibility

### Performance Optimization

- **Large conversations**: Clear old messages periodically
- **TTS caching**: Generated audio files are cached in `public/audio/`
- **Database**: SQLite automatically optimizes with frequent usage

### Getting Help

1. **Check existing issues** on GitHub
2. **Review documentation** in the `docs/` directory
3. **Create a bug report** with reproduction steps
4. **Join our discussions** for community support

---

<div align="center">

**Built with ❤️ using modern web technologies and local AI**

[🚀 Get Started](#-quick-start) • [📖 Learn More](CONTRIBUTING.md) • [🐛 Report Issues](https://github.com/kliewerdaniel/chrisbot/issues)

</div>
