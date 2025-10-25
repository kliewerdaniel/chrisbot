# 🤝 Contributing to AI Chatbot with Graph RAG & TTS

Thank you for your interest in contributing to this AI chatbot project! We welcome contributions from developers of all skill levels and backgrounds.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Contributing Guidelines](#contributing-guidelines)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Feature Development](#feature-development)
- [Issue Reporting](#issue-reporting)

## 🚀 Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Node.js** 18.18.0 or later
- **npm** or **yarn** package manager
- **Git** for version control
- **Python** 3.8+ (for Graph RAG and TTS features)
- **Ollama** (optional, for Graph RAG testing)

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/chrisbot06.git
   cd chrisbot06
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```

5. **Verify setup**
   ```bash
   npm run type-check  # TypeScript checks
   npm run lint        # Code linting
   npm run build       # Production build
   npm test           # Run tests
   ```

## 🏗️ Project Structure

```
├── src/
│   ├── app/                    # Next.js app router
│   │   ├── api/               # API endpoints
│   │   │   ├── chat/          # Chat functionality
│   │   │   ├── graph-rag/     # Graph RAG endpoints
│   │   │   ├── tts/           # Text-to-speech
│   │   │   └── system-prompts/ # AI personality management
│   │   ├── blog/              # Blog pages
│   │   └── dashboard/         # Admin dashboard
│   ├── components/            # React components
│   │   ├── Chat.tsx           # Main chat interface
│   │   ├── ChatInput.tsx      # Message input component
│   │   ├── MessageList.tsx    # Message display
│   │   └── MessageBubble.tsx  # Individual message bubbles
│   ├── lib/                   # Business logic
│   │   ├── stores/            # Zustand state management
│   │   └── tts-service.ts     # TTS integration service
│   └── utils/                 # Utility functions
├── scripts/                   # Python scripts for data processing
├── public/                    # Static assets
├── data/                      # Knowledge graph data
└── tests/                     # Test files
```

## 📝 Contributing Guidelines

### Types of Contributions

We welcome various types of contributions:

- **🐛 Bug Fixes**: Fix existing issues or bugs
- **✨ Features**: Add new functionality
- **📚 Documentation**: Improve documentation and examples
- **🎨 UI/UX**: Enhance user interface and experience
- **🧪 Tests**: Add or improve test coverage
- **🔧 Tooling**: Improve development tools and scripts

### Branching Strategy

Follow [GitHub Flow](https://guides.github.com/introductions/flow/):

- **`main`**: Production-ready code (protected branch)
- **Feature branches**: `feature/feature-name`
- **Bug fixes**: `fix/issue-description`
- **Documentation**: `docs/update-description`
- **Hotfixes**: `hotfix/critical-issue`

### Commit Conventions

Use [Conventional Commits](https://conventionalcommits.org/):

```bash
feat: add Graph RAG toggle in chat interface
fix: resolve TTS audio generation timeout
docs: update API documentation with examples
style: format components with consistent spacing
refactor: extract chat logic into custom hooks
test: add unit tests for message sanitization
chore: update dependencies and security patches
```

## 📋 Code Standards

### TypeScript Guidelines

- **Strict Typing**: Use explicit types, avoid `any`
- **Interface Preference**: Use interfaces over type aliases for object shapes
- **Generic Constraints**: Use generics for reusable components
- **Error Handling**: Implement proper error boundaries and fallbacks

### React Best Practices

- **Functional Components**: Use hooks over class components
- **Custom Hooks**: Extract reusable logic into custom hooks
- **Component Composition**: Prefer composition over inheritance
- **Performance**: Use `React.memo()` for expensive components

### API Development

- **RESTful Design**: Follow REST conventions for endpoints
- **Error Responses**: Provide meaningful error messages
- **Input Validation**: Validate all user inputs
- **Rate Limiting**: Consider implementing rate limits for public APIs

### State Management

- **Zustand Stores**: Use Zustand for global state management
- **Local State**: Keep local state in components when possible
- **Immutability**: Avoid mutating state directly
- **Selectors**: Use selectors for computed state

## 🧪 Testing

### Testing Strategy

- **Unit Tests**: Test individual functions and components
- **Integration Tests**: Test API endpoints and data flow
- **E2E Tests**: Test complete user journeys (using Playwright)
- **Performance Tests**: Monitor bundle size and runtime performance

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run with coverage report
npm run test:coverage

# Run specific test file
npm test -- chat-store.test.ts

# Run Playwright E2E tests
npx playwright test
```

### Writing Tests

```typescript
// Example: Component test
import { render, screen } from '@testing-library/react'
import ChatInput from '@/components/ChatInput'

describe('ChatInput', () => {
  it('renders input field', () => {
    render(<ChatInput onSend={() => {}} />)
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('calls onSend when message is submitted', async () => {
    const mockOnSend = jest.fn()
    const { user } = render(<ChatInput onSend={mockOnSend} />)

    await user.type(screen.getByRole('textbox'), 'Hello world')
    await user.click(screen.getByRole('button'))

    expect(mockOnSend).toHaveBeenCalledWith('Hello world')
  })
})
```

## 🔄 Pull Request Process

### Before Submitting

1. **Test your changes**:
   ```bash
   npm run type-check
   npm run lint
   npm run test
   npm run build
   ```

2. **Update documentation** if needed

3. **Add tests** for new features

4. **Ensure CI passes** (GitHub Actions will run automatically)

### PR Template

```markdown
## Description
Brief description of the changes and why they're needed.

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature)
- [ ] Documentation update
- [ ] Code refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] All tests pass locally

## Screenshots
Add screenshots if the changes affect the UI.

## Related Issues
Closes #123, relates to #456

## Additional Notes
Any additional context or information reviewers should know.
```

### Review Process

1. **Automated checks** run on all PRs
2. **Maintainers review** code and provide feedback
3. **Address feedback** and update PR as needed
4. **Merge** when approved and all checks pass

## ✨ Feature Development

### Adding New Features

1. **Create an issue** first to discuss the feature
2. **Design the implementation** with consideration for:
   - User experience
   - Performance impact
   - Maintainability
   - Testing requirements

3. **Implement incrementally** with small, testable changes
4. **Add comprehensive tests** covering edge cases
5. **Update documentation** with usage examples

### API Development

When adding new API endpoints:

1. **Follow REST conventions** for endpoint design
2. **Implement proper error handling** with meaningful messages
3. **Add input validation** and sanitization
4. **Document the API** with examples in README
5. **Add integration tests** for the endpoint

## 🐛 Issue Reporting

### Bug Reports

When reporting bugs, please include:

1. **Clear title** describing the issue
2. **Steps to reproduce** with exact commands/inputs
3. **Expected behavior** vs **actual behavior**
4. **Environment details** (Node version, OS, browser)
5. **Error logs** or screenshots if applicable
6. **Minimal reproduction** case if possible

### Feature Requests

For new features:

1. **Describe the feature** and its use case
2. **Explain why it's valuable** for users
3. **Consider alternatives** you've explored
4. **Provide examples** of how it would work
5. **Be open to discussion** about implementation details

## 📚 Documentation

### Documentation Standards

- **Clear and concise** language
- **Code examples** for all public APIs
- **Step-by-step instructions** for setup processes
- **Troubleshooting section** for common issues
- **Regular updates** when features change

### Updating Documentation

When making changes:

1. **Update README.md** for user-facing changes
2. **Add inline comments** for complex logic
3. **Update API documentation** with examples
4. **Add migration guides** for breaking changes

## 🙏 Recognition

Contributors are recognized through:

- **GitHub contributor list**
- **Release notes** mentioning contributions
- **Code authorship** in commit history
- **Community shoutouts** in discussions

## 📞 Getting Help

- **Check existing issues** for similar problems
- **Search documentation** and README first
- **Ask questions** in GitHub Discussions
- **Join our community** for real-time help

---

**Thank you for contributing to the AI Chatbot project!** 🎉

Your contributions help make this a better tool for developers and users worldwide.
