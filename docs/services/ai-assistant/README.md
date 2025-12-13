# AI Assistant Service - Complete Documentation

Comprehensive documentation for the Scribes AI Assistant RAG (Retrieval-Augmented Generation) pipeline.

## 📚 Table of Contents

1. [Quick Start](#-quick-start)
2. [Architecture Overview](#-architecture-overview)
3. [Implementation Guides](#-implementation-guides)
4. [Testing Documentation](#-testing-documentation)
5. [Service Documentation](#-service-documentation)
6. [Development Guides](#-development-guides)

---

## 🚀 Quick Start

**New to the AI Assistant?** Start here:

### 📖 [`QUICK_START_ASSISTANT.md`](./QUICK_START_ASSISTANT.md)
Your first stop for understanding and using the AI Assistant.

**What you'll learn:**
- What the AI Assistant does
- How to make your first query
- Basic configuration
- Common use cases

**Quick example:**
```python
from app.services.assistant_service import AssistantService

service = AssistantService()
response = await service.query(
    user_query="What is grace?",
    user_id=1,
    db=db_session
)
print(response["answer"])
```

---

## 🏗️ Architecture Overview

### 📖 [`AI_Assistant_infrastructure.md`](./AI_Assistant_infrastructure.md)
Complete infrastructure overview and system architecture.

**Contents:**
- System architecture diagram
- All AI service components
- Data flow through RAG pipeline
- Token budget allocations
- Service dependencies

**Key Services:**
1. **TokenizerService** - Text chunking with token awareness
2. **EmbeddingService** - 384-dim semantic vectors
3. **RetrievalService** - Similarity search with pgvector
4. **ContextBuilder** - Smart context assembly
5. **PromptEngine** - Template-based prompt generation
6. **HFTextGenService** - Hugging Face API integration
7. **AssistantService** - Complete RAG orchestrator

---

### 📖 [`ARCHITECTURE_DIAGRAM.md`](./ARCHITECTURE_DIAGRAM.md)
Visual diagrams and flowcharts.

**Includes:**
- System component diagram
- RAG pipeline flow
- Data transformation stages
- Error handling paths

---

## 📋 Implementation Guides

### Phase 1: Core Integration

#### 📖 [`ASSISTANT_INTEGRATION_PLAN.md`](./ASSISTANT_INTEGRATION_PLAN.md)
Complete planning document for Phase 1 integration.

**Contents:**
- Infrastructure audit results
- Token flow mapping (2048 token budget)
- Implementation roadmap
- Edge case handling
- Testing strategy

**Token Budget Breakdown:**
- System Prompt: 150 tokens
- User Query: 150 tokens
- Context: 1200 tokens
- Output: 400 tokens
- Buffer: 148 tokens

---

#### 📖 [`ASSISTANT_SERVICE_IMPLEMENTATION_COMPLETE.md`](./ASSISTANT_SERVICE_IMPLEMENTATION_COMPLETE.md)
Detailed implementation documentation for AssistantService.

**The 7-Step RAG Pipeline:**

1. **Validate Query** - Check input requirements
2. **Embed Query** - Convert to 384-dim vector
3. **Retrieve Context** - Semantic search (top 5 chunks)
4. **Build Context** - Assemble within token budget
5. **Assemble Prompt** - Format system + user messages
6. **Generate Response** - Call Hugging Face API
7. **Format Response** - Structure output with metadata

**Error Handling:**
- `ValueError` - Invalid inputs
- `GenerationError` - API failures
- `Exception` - Unexpected errors

**Edge Cases:**
- Empty queries
- No context found
- Token budget exceeded
- API timeouts

---

#### 📖 [`PHASE_1_COMPLETE.md`](./PHASE_1_COMPLETE.md)
Phase 1 completion summary and sign-off.

**Deliverables:**
- ✅ AssistantService.query() implemented
- ✅ All 7 pipeline steps functional
- ✅ Error handling complete
- ✅ Logging comprehensive
- ✅ Unit tests passing

---

### Phase 2: Advanced Features

#### 📖 [`PHASE_2_CHECKLIST.md`](./PHASE_2_CHECKLIST.md)
Roadmap for Phase 2 enhancements.

**Planned Features:**
- Conversation history
- Multi-turn dialogue
- Context caching
- Response streaming
- Advanced prompt templates

---

#### 📖 [`PHASE_2_IMPLEMENTATION_GUIDE.md`](./PHASE_2_IMPLEMENTATION_GUIDE.md)
Detailed guide for Phase 2 development.

---

#### 📖 [`PHASE_2_SERVICE_IMPLEMENTATION_COMPLETE.md`](./PHASE_2_SERVICE_IMPLEMENTATION_COMPLETE.md)
Phase 2 completion documentation.

---

## 🧪 Testing Documentation

### Unit Tests

#### 📖 [`ASSISTANT_UNIT_TESTS_COMPLETE.md`](./ASSISTANT_UNIT_TESTS_COMPLETE.md)
Complete unit test documentation.

**Test Coverage:** 13 comprehensive tests

**Test Scenarios:**
1. ✅ Valid context query
2. ✅ No context handling
3. ✅ Generation error handling
4. ✅ Empty query validation
5. ✅ Token budget enforcement
6. ✅ User with no notes
7. ✅ Metadata optional
8. ✅ Max sources limit
9. ✅ Unexpected errors
10. ✅ Logging verification
11. ✅ Singleton pattern
12. ✅ Dependency initialization
13. ✅ Edge case handling

**Run tests:**
```bash
pytest tests/unit/test_assistant_service.py -v
```

---

#### 📖 [`UNIT_TESTS_COMPLETE.md`](./UNIT_TESTS_COMPLETE.md)
Legacy unit test documentation (pre-consolidation).

---

### Manual Testing

#### 📖 [`ASSISTANT_MANUAL_TESTING_GUIDE.md`](./ASSISTANT_MANUAL_TESTING_GUIDE.md)
**⭐ ESSENTIAL** - Comprehensive manual testing guide (700+ lines).

**Contents:**
1. **Environment Setup**
   - API key configuration
   - Database setup
   - Verification steps

2. **Test Data Preparation**
   - Using `scripts/testing/create_test_data.py`
   - Generating 5 theological notes
   - Creating embeddings

3. **5 Test Scenarios**
   - Valid context query
   - No context query
   - Prompt injection attempts
   - Long query handling
   - Response quality validation

4. **Quality Metrics**
   - Relevance scoring
   - Accuracy assessment
   - Response time benchmarks

5. **Troubleshooting Guide**
   - Common issues
   - Debug procedures
   - Log analysis

**Quick test:**
```python
# See manual testing guide for complete scripts
response = await service.query(
    user_query="What is grace?",
    user_id=7,  # Test user
    db=db
)
```

---

## 🔧 Service Documentation

### HF TextGen Service

#### 📖 [`HF_TEXTGEN_SERVICE_BLUEPRINT.md`](./HF_TEXTGEN_SERVICE_BLUEPRINT.md)
Design blueprint for Hugging Face text generation integration.

**Design Decisions:**
- Model: Llama-2-7b-chat-hf
- Max tokens: 400
- Temperature: 0.7
- Streaming: Not implemented (Phase 1)

---

#### 📖 [`HF_TEXTGEN_IMPLEMENTATION_COMPLETE.md`](./HF_TEXTGEN_IMPLEMENTATION_COMPLETE.md)
Implementation documentation for HFTextGenService.

**Features:**
- API key authentication
- Retry logic (3 attempts)
- Error handling
- Response parsing
- Token counting

**Usage:**
```python
from app.services.hf_textgen_service import HFTextGenService

service = HFTextGenService()
response = service.generate(
    prompt="Your prompt here",
    max_tokens=400
)
```

---

### Tokenizer Service

#### 📖 [`TOKENIZER_ASYNC_ANALYSIS.md`](./TOKENIZER_ASYNC_ANALYSIS.md)
Analysis of async vs sync tokenizer implementation.

**Decision:** Sync implementation chosen
- Faster for small texts
- No I/O operations
- Simpler error handling

---

#### 📖 [`TOKENIZER_OBSERVABILITY_METRICS.md`](./TOKENIZER_OBSERVABILITY_METRICS.md)
Metrics and monitoring for tokenizer performance.

**Metrics:**
- Chunking time
- Token count accuracy
- Overlap efficiency
- Memory usage

---

## 👨‍💻 Development Guides

### Getting Started

#### 📖 [`GETTING_STARTED.md`](./GETTING_STARTED.md)
Developer onboarding guide for AI Assistant development.

**Setup Steps:**
1. Install dependencies
2. Configure environment variables
3. Set up HF_API_KEY
4. Run database migrations
5. Generate test data
6. Run tests

---

## 📊 Document Index

| Document | Purpose | Audience |
|----------|---------|----------|
| **QUICK_START_ASSISTANT.md** | Getting started guide | All users |
| **AI_Assistant_infrastructure.md** | System architecture | Developers |
| **ASSISTANT_INTEGRATION_PLAN.md** | Implementation plan | Developers |
| **ASSISTANT_SERVICE_IMPLEMENTATION_COMPLETE.md** | Implementation details | Developers |
| **ASSISTANT_UNIT_TESTS_COMPLETE.md** | Unit test documentation | QA/Developers |
| **ASSISTANT_MANUAL_TESTING_GUIDE.md** | Manual test procedures | QA |
| **HF_TEXTGEN_SERVICE_BLUEPRINT.md** | Service design | Architects |
| **HF_TEXTGEN_IMPLEMENTATION_COMPLETE.md** | Service implementation | Developers |
| **PHASE_1_COMPLETE.md** | Phase 1 summary | All |
| **PHASE_2_CHECKLIST.md** | Future roadmap | Product/Developers |

---

## 🔗 Related Documentation

### Other Services
- **Cross-Reference Service:** `docs/guides/backend implementations/CrossRef_feature.md`
- **Embedding Service:** `docs/guides/backend implementations/Embedding_implementations.md`
- **Note Service:** `docs/guides/backend implementations/Notefeature_guide.md`

### Deployment
- **Production Checklist:** `docs/TESTING_DEPLOYMENT_CHECKLIST.md`
- **Background Workers:** `docs/BACKGROUND_WORKER_SETUP.md`

### Scripts
- **Test Data Generation:** `scripts/testing/create_test_data.py`
- **Script Documentation:** `scripts/README.md`

---

## 🎯 Common Tasks

### 1. Make Your First Query
```python
from app.services.assistant_service import AssistantService
from app.core.database import get_db

service = AssistantService()
async with get_db() as db:
    response = await service.query(
        user_query="What is faith?",
        user_id=1,
        db=db
    )
    print(response["answer"])
```

### 2. Run Unit Tests
```bash
pytest tests/unit/test_assistant_service.py -v
```

### 3. Create Test Data
```bash
python scripts/testing/create_test_data.py
```

### 4. Manual Testing
See: [`ASSISTANT_MANUAL_TESTING_GUIDE.md`](./ASSISTANT_MANUAL_TESTING_GUIDE.md)

### 5. Check Token Budget
```python
from app.core.prompt_engine import PromptEngine

engine = PromptEngine()
tokens = engine.count_tokens("Your text here")
print(f"Tokens: {tokens}")
```

---

## ⚙️ Configuration

### Required Environment Variables
```bash
# Hugging Face API
HF_API_KEY=hf_xxxxxxxxxxxxx

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/scribes

# Redis (for background jobs)
REDIS_URL=redis://localhost:6379/0

# Token Limits
MAX_CONTEXT_TOKENS=1200
MAX_OUTPUT_TOKENS=400
```

---

## 🐛 Troubleshooting

### Common Issues

**1. "HF_API_KEY not configured"**
```bash
# Add to .env file
HF_API_KEY=your_key_here
```

**2. "No context found for query"**
- Verify user has notes in database
- Check embeddings are generated
- Run: `python scripts/testing/create_test_data.py`

**3. "Token budget exceeded"**
- Query is too long (>150 tokens)
- Too much context retrieved
- Adjust MAX_CONTEXT_TOKENS in settings

See detailed troubleshooting: [`ASSISTANT_MANUAL_TESTING_GUIDE.md`](./ASSISTANT_MANUAL_TESTING_GUIDE.md)

---

## 📈 Performance Benchmarks

| Operation | Target | Actual |
|-----------|--------|--------|
| Query embedding | <100ms | ~80ms |
| Context retrieval | <200ms | ~150ms |
| Prompt assembly | <50ms | ~30ms |
| Text generation | <3s | ~2.5s |
| **Total pipeline** | <5s | ~4s |

---

## 🔐 Security Notes

- **API Keys:** Never commit HF_API_KEY to version control
- **User Data:** All queries are user-scoped (user_id required)
- **Input Validation:** All inputs sanitized before processing
- **Rate Limiting:** Implement in production (not in Phase 1)

---

## 📞 Support

- **Issues:** Check troubleshooting sections in docs
- **Testing:** See manual testing guide
- **Development:** See GETTING_STARTED.md

---

**Last Updated:** December 12, 2025
**Phase:** Phase 1 Complete ✅
