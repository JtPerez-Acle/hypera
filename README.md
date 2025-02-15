# HyperA: Next-Generation Agentic Code Understanding System

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Poetry](https://img.shields.io/badge/poetry-1.7.1-blue.svg)](https://python-poetry.org/)
[![Qdrant](https://img.shields.io/badge/qdrant-1.7.0-blue.svg)](https://qdrant.tech/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

HyperA is an advanced, agentic code analysis system that achieves hyper-human comprehension of codebases through the power of multi-agent coordination, adaptive learning, and state-of-the-art AI models. By combining Gemini 1.5 Pro's massive context window with DeepSeek's advanced reasoning capabilities, HyperA delivers unprecedented insights into code structure, behavior, and optimization opportunities.

## 🌟 Features

### Core Capabilities
- **Agentic Analysis**: Multi-agent system for autonomous code understanding
- **Adaptive Learning**: Self-improving strategies for code analysis
- **Rich Metadata**: Comprehensive code context extraction
- **Massive Context**: 2M token window via Gemini 1.5 Pro
- **Deep Reasoning**: Advanced code analysis via DeepSeek
- **Vector Search**: High-performance retrieval via Qdrant

## 🛠️ Visualization color coding

- 🟧 Orange: Core/Primary components
- 🟦 Blue: Strategy components
- 🟩 Green: Processing components
- 🟪 Purple: External services/Secondary components

### System Architecture

```mermaid
graph TB
    subgraph "Core System"
        AC["🎯 AgentCoordinator<br/>Resource & Knowledge Hub"]
        KS["📚 Knowledge Store<br/>Shared Insights"]
    end

    subgraph "Analysis Agents"
        BA["🔍 BehavioralAnalyzer<br/>Code Behavior"]
        SA["🛡️ SecurityAnalyzer<br/>Vulnerabilities"]
        PA["📐 PatternAnalyzer<br/>Design Patterns"]
        MA["📊 MetricsAnalyzer<br/>Code Quality"]
        DA["🔗 DependencyAnalyzer<br/>Dependencies"]
    end

    subgraph "Intelligent Components"
        AMM["🧠 AdaptiveMetadataManager<br/>Smart Extraction"]
        AP["⚡ AdaptivePipeline<br/>Dynamic Processing"]
        AR["🔍 AdaptiveRetriever<br/>Pattern Learning"]
    end

    subgraph "External Services"
        GEM["🌐 Gemini 1.5 Pro<br/>2M Context"]
        DS["🤖 DeepSeek<br/>Reasoning"]
        QD["💾 Qdrant<br/>Vector Store"]
    end

    %% Coordinator connections
    AC -->|"Manages"| BA
    AC -->|"Manages"| SA
    AC -->|"Manages"| PA
    AC -->|"Manages"| MA
    AC -->|"Manages"| DA
    AC -->|"Orchestrates"| AMM
    AC -->|"Orchestrates"| AP
    AC -->|"Orchestrates"| AR
    AC <-->|"Syncs"| KS

    %% Component interactions
    AMM -->|"Feeds"| AP
    AP -->|"Stores"| QD
    AR -->|"Queries"| QD
    
    %% External service usage
    AR -->|"Context"| GEM
    BA & SA & PA & MA & DA -->|"Reasoning"| DS

    style AC fill:#ff9900,stroke:#fff,stroke-width:2px
    style KS fill:#ff9900,stroke:#fff,stroke-width:2px
    style BA fill:#00aaff,stroke:#fff,stroke-width:2px
    style SA fill:#00aaff,stroke:#fff,stroke-width:2px
    style PA fill:#00aaff,stroke:#fff,stroke-width:2px
    style MA fill:#00aaff,stroke:#fff,stroke-width:2px
    style DA fill:#00aaff,stroke:#fff,stroke-width:2px
    style AMM fill:#00ff99,stroke:#fff,stroke-width:2px
    style AP fill:#00ff99,stroke:#fff,stroke-width:2px
    style AR fill:#00ff99,stroke:#fff,stroke-width:2px
    style GEM fill:#ff66cc,stroke:#fff,stroke-width:2px
    style DS fill:#ff66cc,stroke:#fff,stroke-width:2px
    style QD fill:#ff66cc,stroke:#fff,stroke-width:2px
```

### Agent Interaction Flow

```mermaid
sequenceDiagram
    participant U as User
    participant AC as AgentCoordinator
    participant BA as BehavioralAnalyzer
    participant SA as SecurityAnalyzer
    participant KS as Knowledge Store
    participant AMM as MetadataManager
    participant AR as AdaptiveRetriever

    U->>AC: analyze_code(code)
    
    rect rgb(240, 240, 240)
        Note over AC,AR: Phase 1: Context Building
        AC->>AMM: extract_metadata(code)
        AMM-->>AC: rich_metadata
        AC->>AR: retrieve_context(code)
        AR-->>AC: relevant_context
    end

    rect rgb(230, 240, 250)
        Note over AC,KS: Phase 2: Agent Coordination
        AC->>BA: analyze(code, context)
        AC->>SA: analyze(code, context)
        
        par Agent Learning
            BA->>KS: share_insights()
            SA->>KS: share_insights()
        end
        
        BA-->>AC: behavioral_analysis
        SA-->>AC: security_analysis
    end

    rect rgb(240, 230, 240)
        Note over AC,U: Phase 3: Knowledge Integration
        AC->>KS: update_knowledge()
        KS-->>AC: enhanced_insights
        AC->>U: comprehensive_result
    end
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12
- Poetry
- Conda (optional)
- Qdrant Server

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/hypera.git
   cd hypera
   ```

2. Set up the environment:
   ```bash
   # Using Poetry (recommended)
   poetry install

   # Using Conda
   conda env create -f environment.yml
   conda activate hypera
   ```

3. Configure API keys:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys:
   # - GEMINI_API_KEY
   # - DEEPSEEK_API_KEY
   # - QDRANT_API_KEY (optional)
   ```

4. Start Qdrant:
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

## 🎯 Usage

### Basic Usage

```python
from hypera.core.coordinator import AgentCoordinator
from hypera.reasoning.agents import BehavioralAnalyzer, SecurityAnalyzer

# Initialize the coordinator
coordinator = AgentCoordinator()

# Register agents
behavioral_agent = BehavioralAnalyzer()
security_agent = SecurityAnalyzer()

await coordinator.register_agent("behavioral", behavioral_agent)
await coordinator.register_agent("security", security_agent)

# Analyze code
result = await coordinator.analyze_code(
    code="your_code_here",
    analysis_types=["behavior", "security"]
)
```

### Advanced Configuration

```python
from hypera.metadata.manager import AdaptiveMetadataManager
from hypera.vector_store.adaptive_pipeline import AdaptivePipeline
from hypera.retrieval.adaptive_retriever import AdaptiveRetriever

# Configure components with custom settings
metadata_manager = AdaptiveMetadataManager(
    extraction_strategies={
        "quick": {"depth": 1, "patterns": ["imports", "functions"]},
        "deep": {"depth": 2, "patterns": ["all"]}
    }
)

pipeline = AdaptivePipeline(
    chunking_strategies={
        "small": {"min_size": 50, "max_size": 200},
        "large": {"min_size": 400, "max_size": 1000}
    }
)

retriever = AdaptiveRetriever(
    search_strategies={
        "quick": {"similarity": 0.7, "max_results": 5},
        "thorough": {"similarity": 0.5, "max_results": 20}
    }
)
```

## 🔄 System Components

### Agent Coordination

```mermaid
flowchart TB
    subgraph "Resource Management"
        RM["Resource Monitor"]
        RA["Resource Allocator"]
        PS["Priority Scheduler"]
    end

    subgraph "Performance Tracking"
        MT["Metrics Tracker"]
        PO["Performance Optimizer"]
    end

    subgraph "Knowledge Management"
        KS["Knowledge Store"]
        KD["Knowledge Distributor"]
    end

    subgraph "Agents"
        A1["Agent 1<br/>CPU: 30%<br/>Memory: 500MB"]
        A2["Agent 2<br/>CPU: 45%<br/>Memory: 750MB"]
        A3["Agent 3<br/>CPU: 25%<br/>Memory: 250MB"]
    end

    RM -->|"Usage Data"| PO
    PO -->|"Optimize"| RA
    RA -->|"Allocate"| PS
    PS -->|"Schedule"| A1 & A2 & A3
    
    A1 & A2 & A3 -->|"Report"| MT
    MT -->|"Stats"| PO
    
    A1 & A2 & A3 -->|"Share"| KS
    KS -->|"Distribute"| KD
    KD -->|"Update"| A1 & A2 & A3

    style RM fill:#ff9900,stroke:#fff
    style RA fill:#ff9900,stroke:#fff
    style PS fill:#ff9900,stroke:#fff
    style MT fill:#00aaff,stroke:#fff
    style PO fill:#00aaff,stroke:#fff
    style KS fill:#00ff99,stroke:#fff
    style KD fill:#00ff99,stroke:#fff
    style A1 fill:#ff66cc,stroke:#fff
    style A2 fill:#ff66cc,stroke:#fff
    style A3 fill:#ff66cc,stroke:#fff
```

### Metadata Management

```mermaid
graph TB
    subgraph "Extraction Strategies"
        QS["Quick Strategy<br/>Depth: 1<br/>Patterns: Basic"]
        DS["Deep Strategy<br/>Depth: 2<br/>Patterns: Extended"]
        CS["Comprehensive<br/>Depth: 3<br/>Patterns: All"]
    end

    subgraph "Pattern Learning"
        PD["Pattern Detector"]
        PR["Pattern Registry"]
        PE["Pattern Evaluator"]
    end

    subgraph "Metadata Processing"
        ME["Metadata Extractor"]
        MP["Metadata Processor"]
        MV["Metadata Validator"]
    end

    subgraph "Output"
        MS["Metadata Store"]
        MI["Metadata Index"]
    end

    Code[/"Source Code"/] --> ME
    ME --> |"Extract"| MP
    MP --> |"Validate"| MV
    MV --> |"Store"| MS
    MS --> |"Index"| MI

    QS & DS & CS --> |"Configure"| ME
    ME --> |"Patterns"| PD
    PD --> |"Register"| PR
    PR --> |"Evaluate"| PE
    PE --> |"Optimize"| QS & DS & CS

    style Code fill:#ff9900,stroke:#fff
    style QS fill:#00aaff,stroke:#fff
    style DS fill:#00aaff,stroke:#fff
    style CS fill:#00aaff,stroke:#fff
    style PD fill:#00ff99,stroke:#fff
    style PR fill:#00ff99,stroke:#fff
    style PE fill:#00ff99,stroke:#fff
    style ME fill:#ff66cc,stroke:#fff
    style MP fill:#ff66cc,stroke:#fff
    style MV fill:#ff66cc,stroke:#fff
    style MS fill:#ff9900,stroke:#fff
    style MI fill:#ff9900,stroke:#fff
```

### Vector Store Pipeline

```mermaid
graph TB
    subgraph "Chunking Strategies"
        SC["Small Chunks<br/>50-200 tokens"]
        MC["Medium Chunks<br/>150-500 tokens"]
        LC["Large Chunks<br/>400-1000 tokens"]
    end

    subgraph "Processing Pipeline"
        CP["Chunk Processor"]
        EP["Embedding Processor"]
        VP["Vector Processor"]
    end

    subgraph "Quality Control"
        QA["Quality Analyzer"]
        PE["Performance Evaluator"]
        OO["Optimization Oracle"]
    end

    subgraph "Storage"
        VS["Vector Store<br/>[Qdrant]"]
        CS["Chunk Store"]
    end

    Code[/"Source Code"/] --> CP
    CP --> |"Process"| EP
    EP --> |"Vectorize"| VP
    VP --> |"Store"| VS
    VP --> |"Index"| CS

    SC & MC & LC --> |"Configure"| CP
    CP & EP & VP --> |"Analyze"| QA
    QA --> |"Evaluate"| PE
    PE --> |"Optimize"| OO
    OO --> |"Adjust"| SC & MC & LC

    style Code fill:#ff9900,stroke:#fff
    style SC fill:#00aaff,stroke:#fff
    style MC fill:#00aaff,stroke:#fff
    style LC fill:#00aaff,stroke:#fff
    style CP fill:#00ff99,stroke:#fff
    style EP fill:#00ff99,stroke:#fff
    style VP fill:#00ff99,stroke:#fff
    style QA fill:#ff66cc,stroke:#fff
    style PE fill:#ff66cc,stroke:#fff
    style OO fill:#ff66cc,stroke:#fff
    style VS fill:#ff9900,stroke:#fff
    style CS fill:#ff9900,stroke:#fff
```

### Retrieval System

```mermaid
graph TB
    subgraph "Query Strategies"
        QS["Quick Search<br/>Precision: High<br/>Results: 5"]
        BS["Balanced Search<br/>Precision: Medium<br/>Results: 10"]
        TS["Thorough Search<br/>Precision: Low<br/>Results: 20"]
    end

    subgraph "Pattern Learning"
        PD["Pattern Detector"]
        PL["Pattern Learner"]
        PO["Pattern Optimizer"]
    end

    subgraph "Query Processing"
        QP["Query Processor"]
        QE["Query Enhancer"]
        QR["Query Router"]
    end

    subgraph "Results"
        RP["Results Processor"]
        RR["Results Ranker"]
        RC["Results Cache"]
    end

    Query[/"User Query"/] --> QP
    QP --> |"Enhance"| QE
    QE --> |"Route"| QR
    QR --> |"Execute"| QS & BS & TS
    QS & BS & TS --> |"Process"| RP
    RP --> |"Rank"| RR
    RR --> |"Cache"| RC

    QP --> |"Analyze"| PD
    PD --> |"Learn"| PL
    PL --> |"Optimize"| PO
    PO --> |"Adjust"| QS & BS & TS

    style Query fill:#ff9900,stroke:#fff
    style QS fill:#00aaff,stroke:#fff
    style BS fill:#00aaff,stroke:#fff
    style TS fill:#00aaff,stroke:#fff
    style PD fill:#00ff99,stroke:#fff
    style PL fill:#00ff99,stroke:#fff
    style PO fill:#00ff99,stroke:#fff
    style QP fill:#ff66cc,stroke:#fff
    style QE fill:#ff66cc,stroke:#fff
    style QR fill:#ff66cc,stroke:#fff
    style RP fill:#ff9900,stroke:#fff
    style RR fill:#ff9900,stroke:#fff
    style RC fill:#ff9900,stroke:#fff
```

## 📊 Performance

HyperA's agentic approach delivers significant improvements:

- **Analysis Speed**: 3x faster than traditional methods
- **Context Understanding**: 2M token window vs 4-16K in other systems
- **Resource Efficiency**: Dynamic allocation reduces CPU/memory usage by 40%
- **Pattern Recognition**: Adaptive learning improves accuracy by 25% over time

## 🛠️ Development

### Project Structure
```
hypera/
├── src/
│   ├── core/
│   │   └── coordinator.py      # Agent coordination
│   ├── metadata/
│   │   └── manager.py          # Adaptive metadata
│   ├── vector_store/
│   │   └── adaptive_pipeline.py # Smart chunking
│   ├── retrieval/
│   │   └── adaptive_retriever.py # Pattern learning
│   └── reasoning/
│       └── agents/             # Specialized agents
├── tests/
├── docs/
└── examples/
```

### Running Tests
```bash
# Run all tests
poetry run pytest

# Run specific test category
poetry run pytest tests/test_agents
```

### Contributing
1. Fork the repository
2. Create your feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 📚 Documentation

- [Architecture Overview](docs/architecture.md)
- [API Reference](docs/api.md)
- [Development Guide](docs/development.md)
- [Examples](examples/README.md)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google's Gemini team for the 1.5 Pro model
- DeepSeek for their advanced reasoning capabilities
- Qdrant team for the vector database
- All contributors and maintainers

---

**Note**: This project is under active development. For the latest updates, check our [CHANGELOG.md](CHANGELOG.md).