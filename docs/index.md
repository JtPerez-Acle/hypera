# Welcome to HyperA

HyperA is a hyper-human codebase understanding system that leverages advanced retrieval and deep reasoning to capture every nuance of code. Our system combines the power of Gemini 1.5 Pro for retrieval and DeepSeek R1 for enhanced reasoning, along with rich metadata and scalable vector storage using Qdrant.

## Key Features

- **Advanced Code Understanding**: Utilizes Gemini 1.5 Pro's 2-million token context window for comprehensive code analysis
- **Deep Reasoning**: Powered by DeepSeek R1 for sophisticated code comprehension
- **Rich Metadata Integration**: Captures AST fragments, function signatures, and dependency graphs
- **Multi-Language Support**: Designed to handle Python, Rust, and TypeScript codebases
- **Scalable Vector Storage**: Uses Qdrant for efficient code and metadata retrieval
- **Comprehensive Documentation**: Auto-generated API documentation with examples and guides

## Project Documentation

### Development Resources
- [Development Plan](DEVELOPMENT_PLAN.md): Our roadmap and milestone tracking
- [Changelog](CHANGELOG.md): Detailed version history and updates
- [Test Coverage](TEST_COVERAGE.md): Comprehensive test suite documentation

### Getting Started
```bash
# Clone the repository
git clone https://github.com/JtPerez-Acle/hypera.git
cd hypera

# Set up the environment using Poetry
poetry install

# Install documentation dependencies
poetry install --with docs

# Start the documentation server
poetry run mkdocs serve
```

### Project Status

#### Current Version: 0.1.5 (2025-02-14)
- Full Pydantic V2 migration completed
- Enhanced metadata validation
- Improved test coverage
- See [Changelog](CHANGELOG.md) for details

#### Development Progress
- Foundation and Infrastructure (7/8 complete)
- Vector Storage and Retrieval (8/8 complete)
- Multi-Language Support (2/8 complete)
- Advanced Code Analysis (1/8 complete)
- Retrieval System (8/8 complete)
- Reasoning Engine (0/8 started)
- User Interface (0/8 started)
- Deployment and Scaling (0/8 started)

See our [Development Plan](DEVELOPMENT_PLAN.md) for detailed progress tracking.

## Contributing

We welcome contributions! Please check our [Contributing Guide](CONTRIBUTING.md) for guidelines.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install dependencies with `poetry install`
4. Run tests with `poetry run pytest`
5. Submit a pull request

### Key Resources
- [API Reference](api/): Detailed API documentation
- [Test Coverage](TEST_COVERAGE.md): Current test coverage and guidelines
- [Development Plan](DEVELOPMENT_PLAN.md): Project roadmap and progress
