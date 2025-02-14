# Changelog

All notable changes to the HyperA project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-02-14

### Added
- Initial project setup with Poetry for dependency management
- Modular metadata extraction system with language-specific support
- Python AST parsing implementation with extensibility for other languages
- Comprehensive test suite for metadata extraction
- Language support module for multi-language code analysis
- Rich metadata integration with AST snippets, function signatures, and dependency graphs
- Context linking system for repository and documentation references

### Changed
- Migrated from basic setuptools to Poetry for better dependency management
- Restructured project to follow modular architecture
- Enhanced metadata manager to use language-specific parsers
- Updated dependency versions to resolve conflicts:
  - Switched to langchain-core for better compatibility
  - Adjusted qdrant-client version for numpy compatibility

### Fixed
- Dependency conflicts between langchain and qdrant-client
- Python path issues in test suite
- AST parsing error handling
- Path handling in metadata context generation

### Infrastructure
- Set up project structure according to .windsurfrules guidelines
- Configured Poetry within Conda environment 'hypera'
- Established testing infrastructure with pytest
- Added proper logging configuration

### Documentation
- Added initial changelog
- Implemented comprehensive docstrings
- Created type hints for better code understanding
- Added function and class documentation

### Technical Debt
- [ ] Implement Tree-sitter integration for robust multi-language support
- [ ] Add support for additional programming languages
- [ ] Implement caching for parsed ASTs
- [ ] Add performance metrics for metadata extraction
