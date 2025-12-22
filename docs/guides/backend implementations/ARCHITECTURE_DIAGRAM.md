# AI Assistant Architecture - Phase 2

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER REQUEST                              │
│  "What did the pastor say about faith and grace?"                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ASSISTANT SERVICE                             │
│                    (Phase 3 - Next)                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: TOKENIZE & VALIDATE QUERY                               │
│                                                                   │
│  TokenizerService.count_tokens("What did...")                    │
│  → 12 tokens ✓ (within 150 token limit)                         │
│                                                                   │
│  PromptEngine.detect_prompt_injection(query)                     │
│  → No injection detected ✓                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: EMBED QUERY                                              │
│                                                                   │
│  EmbeddingService.embed("What did...")                           │
│  → [0.123, -0.456, ...] (384-dim vector)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: RETRIEVE CHUNKS (USER-SCOPED)                           │
│                                                                   │
│  RetrievalService.retrieve_top_chunks(                           │
│      query_vec, user_id=123, top_k=50                            │
│  )                                                                │
│                                                                   │
│  SQL: SELECT * FROM note_chunks nc                               │
│       JOIN notes n ON nc.note_id = n.id                          │
│       WHERE n.user_id = 123                                      │
│       ORDER BY embedding <=> query_vec                           │
│       LIMIT 50                                                    │
│                                                                   │
│  Returns:                                                         │
│  ┌──────────────────────────────────────────────┐                │
│  │ HIGH RELEVANCE (score >= 0.6)                │                │
│  ├──────────────────────────────────────────────┤                │
│  │ • Chunk 1: "Faith is trust..." (0.92)        │                │
│  │ • Chunk 2: "Grace is favor..." (0.88)        │                │
│  │ • Chunk 3: "Biblical faith..." (0.75)        │                │
│  │ ... (8 more chunks)                          │                │
│  └──────────────────────────────────────────────┘                │
│                                                                   │
│  ┌──────────────────────────────────────────────┐                │
│  │ LOW RELEVANCE (score < 0.6)                  │                │
│  ├──────────────────────────────────────────────┤                │
│  │ • Chunk 12: "Church picnic..." (0.45)        │                │
│  │ • Chunk 13: "Prayer meeting..." (0.38)       │                │
│  │ ... (37 more chunks)                         │                │
│  │ ⚠️  STORED BUT NOT USED IN CONTEXT           │                │
│  └──────────────────────────────────────────────┘                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: BUILD CONTEXT (TOKEN-AWARE)                             │
│                                                                   │
│  ContextBuilder.build_context(                                   │
│      high_relevance=[11 chunks],                                 │
│      low_relevance=[39 chunks],                                  │
│      token_budget=1800                                           │
│  )                                                                │
│                                                                   │
│  Process:                                                         │
│  ┌────────────────────────────────────────┐                      │
│  │ Chunk 1 (0.92): 245 tokens → ADD      │ Total: 245           │
│  │ Chunk 2 (0.88): 312 tokens → ADD      │ Total: 557           │
│  │ Chunk 3 (0.75): 198 tokens → ADD      │ Total: 755           │
│  │ Chunk 4 (0.72): 289 tokens → ADD      │ Total: 1044          │
│  │ Chunk 5 (0.68): 401 tokens → ADD      │ Total: 1445          │
│  │ Chunk 6 (0.65): 356 tokens → SKIP     │ Would exceed 1800!   │
│  └────────────────────────────────────────┘                      │
│                                                                   │
│  Output:                                                          │
│  • context_text: Formatted string with 5 chunks                  │
│  • chunks_used: [5 chunk dicts]                                  │
│  • low_relevance_stored: [39 chunk dicts] ✅ SAVED              │
│  • metadata: {chunks_used: 5, tokens: 1445, truncated: true}    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: ASSEMBLE PROMPT (PASTORAL TONE)                         │
│                                                                   │
│  PromptEngine.build_prompt(                                      │
│      user_query="What did...",                                   │
│      context_text="[Source: Sermon on Faith]..."                 │
│  )                                                                │
│                                                                   │
│  Assembled Prompt:                                               │
│  ┌────────────────────────────────────────────────┐              │
│  │ You are a compassionate pastoral assistant     │ 150 tokens   │
│  │ helping someone reflect on their sermon        │              │
│  │ notes...                                       │              │
│  ├────────────────────────────────────────────────┤              │
│  │ CONTEXT FROM YOUR SERMON NOTES:                │              │
│  │ ---                                            │ 1445 tokens  │
│  │ [Source: Sermon on Faith by Pastor John]      │              │
│  │ Faith is trust in God...                       │              │
│  │                                                │              │
│  │ [Source: Understanding Grace by Pastor Sarah]  │              │
│  │ Grace is God's unmerited favor...              │              │
│  │ ---                                            │              │
│  ├────────────────────────────────────────────────┤              │
│  │ QUESTION: What did the pastor say about        │ 12 tokens    │
│  │ faith and grace?                               │              │
│  │                                                │              │
│  │ ANSWER:                                        │              │
│  └────────────────────────────────────────────────┘              │
│                                                                   │
│  Token Breakdown:                                                │
│  • System: 150                                                   │
│  • Context: 1445                                                 │
│  • Query: 12                                                     │
│  • Reserved for output: 400                                      │
│  • Total: 2007 / 2048 ✓ Within budget!                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: GENERATE ANSWER (HUGGINGFACE API)                       │
│                                                                   │
│  HFTextGenService.generate(                                      │
│      prompt="You are a compassionate...",                        │
│      max_new_tokens=400,                                         │
│      temperature=0.3                                             │
│  )                                                                │
│                                                                   │
│  ┌────────────────────────────────────────────────┐              │
│  │ 🌐 HUGGINGFACE INFERENCE API                   │              │
│  │                                                │              │
│  │ POST https://api-inference.huggingface.co      │              │
│  │ Model: meta-llama/Llama-3.2-3B-Instruct        │              │
│  │ Headers: Authorization: Bearer hf_xxx          │              │
│  │                                                │              │
│  │ Response (1.2 seconds):                        │              │
│  │ "Based on your notes, the relationship        │              │
│  │ between faith and grace is beautifully        │              │
│  │ complementary. Pastor John teaches that       │              │
│  │ faith is our trust in God even when we        │              │
│  │ cannot see [Sermon on Faith]. Pastor Sarah    │              │
│  │ reminds us that this faith is not earned -    │              │
│  │ it rests on grace, God's unmerited favor      │              │
│  │ [Understanding Grace]. Together, they show    │              │
│  │ us that we walk in faith because God first    │              │
│  │ extended grace to us. Our faith is the        │              │
│  │ response to God's gracious invitation."       │              │
│  └────────────────────────────────────────────────┘              │
│                                                                   │
│  Metrics:                                                         │
│  • Generated: ~247 tokens                                        │
│  • Latency: 1,200ms                                              │
│  • Truncated: No                                                 │
│  • Cost: ~$0.0014 (2400 tokens × $0.0006/1K)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: POST-PROCESS & FORMAT RESPONSE                          │
│                                                                   │
│  AssistantResponse {                                             │
│    answer: "Based on your notes...",                             │
│    sources: [                                                     │
│      {note_id: 101, title: "Sermon on Faith", score: 0.92},     │
│      {note_id: 102, title: "Understanding Grace", score: 0.88}   │
│    ],                                                             │
│    context_metadata: {                                           │
│      chunks_retrieved_high: 11,                                  │
│      chunks_retrieved_low: 39,  ✅ STORED                       │
│      chunks_used: 5,                                             │
│      total_tokens_used: 1445,                                    │
│      truncated: true                                             │
│    },                                                             │
│    query_tokens: 12,                                             │
│    answer_tokens: 247,                                           │
│    latency_ms: 1850                                              │
│  }                                                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      RETURN TO USER                              │
│                                                                   │
│  {                                                                │
│    "answer": "Based on your notes, the relationship between      │
│               faith and grace is beautifully complementary...",  │
│    "sources": [                                                   │
│      {"note_id": 101, "title": "Sermon on Faith"},              │
│      {"note_id": 102, "title": "Understanding Grace"}            │
│    ]                                                              │
│  }                                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions Explained

### 1. Why Separate High/Low Relevance?

**High Relevance (>= 0.6 score):**
- ✅ Used in context
- ✅ Direct answer to question
- ✅ Maximizes quality

**Low Relevance (< 0.6 score):**
- ✅ Stored in response metadata
- ✅ Available for UI to show "Related but not used"
- ✅ Can be used for follow-up queries
- ✅ Useful for query refinement
- ✅ Future: "Did you also want to know about..."

**Benefits:**
- Higher quality answers (only relevant context)
- Better token efficiency
- Transparency (user sees what wasn't used)
- Expansion possibilities (progressive disclosure)

---

### 2. Why Pastoral Tone?

**System Prompt Characteristics:**
```
"You are a compassionate pastoral assistant..."
"Walk alongside the person in their faith journey..."
"Speak with warmth and encouragement..."
"Use 'we' language..."
```

**Impact on Generation:**
- Warm, supportive responses
- Spiritually sensitive language
- Encourages reflection
- Builds trust
- Appropriate for sermon notes context

**Example Comparison:**

❌ **Generic AI tone:**
> "According to note 101, faith is defined as trust in God. Note 102 states that grace is unmerited favor."

✅ **Pastoral tone:**
> "Based on your notes, we see a beautiful relationship between faith and grace. Pastor John reminds us that faith is our trust in God even when we cannot see the path ahead [Sermon on Faith]. This faith, Pastor Sarah teaches, rests not on our merit but on God's gracious favor toward us [Understanding Grace]."

---

### 3. Why HuggingFace API?

**No GPU Available → API is Best Choice**

**Alternatives Considered:**
| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **Local CPU** | Free, private | Very slow (30s+), poor quality | ❌ |
| **Local GPU** | Fast, free after setup | Requires 16GB+ VRAM | ❌ No GPU |
| **OpenAI API** | Best quality | $0.03/1K tokens (50× cost) | ❌ Too expensive |
| **HF API** | Good quality, $0.0006/1K | Slight latency | ✅ **BEST** |

**Cost Analysis (1000 queries/month):**
- Average: 2.4K tokens per query
- Total: 2.4M tokens/month
- Cost: 2,400 × $0.0006 = **$1.44/month**

**Extremely affordable!**

---

### 4. Token Budget Allocation

**Total Context Window: 2048 tokens**

```
┌──────────────────────────────────────────┐
│ System Prompt          150 tokens   7%  │
├──────────────────────────────────────────┤
│ Context (High-Rel)   ~1445 tokens  70%  │  ← Main payload
├──────────────────────────────────────────┤
│ User Query             ~12 tokens   1%  │
├──────────────────────────────────────────┤
│ Reserved Output        400 tokens  20%  │  ← Generation space
├──────────────────────────────────────────┤
│ Buffer                  41 tokens   2%  │  ← Safety margin
└──────────────────────────────────────────┘
Total: 2048 tokens
```

**Why these ratios?**
- Context gets 70% (most important)
- Output gets 20% (allows detailed answers)
- System + query minimal (fixed overhead)
- Buffer prevents edge-case overflows

---

### 5. Security: User Isolation

**Critical SQL Pattern:**
```sql
WHERE n.user_id = :user_id
```

**What this prevents:**
- ❌ User A accessing User B's notes
- ❌ SQL injection (parameterized query)
- ❌ Privilege escalation
- ❌ Data leakage via vector search

**Additional Security:**
- Input validation (user_id > 0)
- Token limits (prevents DoS)
- Prompt injection detection
- API key security (env variable)

---

## Performance Expectations

**Latency Breakdown:**
```
Query Embedding:        ~100-200ms  (sentence-transformers)
Vector Search:          ~50-100ms   (pgvector HNSW index)
Context Building:       ~10-20ms    (token counting)
Prompt Assembly:        ~5-10ms     (string formatting)
HF API Generation:      ~800-2000ms (network + inference)
Post-processing:        ~10-20ms    (response formatting)
─────────────────────────────────────────────
TOTAL:                  ~1-2.5 seconds
```

**Optimization Opportunities (Phase 5):**
- Cache embeddings (save ~150ms per query)
- Cache responses (save entire request)
- Use smaller model for simple queries
- Batch processing for multiple queries

---

## What Happens to Low-Relevance Chunks?

**Stored in response:**
```json
{
  "answer": "...",
  "sources": [...],
  "context_metadata": {
    "chunks_retrieved_low": 39,
    "low_relevance_stored": [
      {
        "chunk_id": 12,
        "note_id": 5,
        "chunk_text": "Church picnic on Saturday",
        "relevance_score": 0.45,
        "note_title": "Announcements"
      },
      // ... 38 more
    ]
  }
}
```

**Future Use Cases:**
1. **UI Display:** "Also found (less relevant): ..."
2. **Refinement:** "Would you like me to also consider...?"
3. **Expansion:** "Show me more context from that sermon"
4. **Analytics:** Track what's frequently stored but not used
5. **Learning:** Improve relevance threshold over time

---

## Architecture Diagram (System View)

```
┌───────────┐
│  Flutter  │
│    App    │
└─────┬─────┘
      │ POST /assistant/query
      │ {"query": "What is faith?"}
      ▼
┌─────────────────────────────────────┐
│         FastAPI Backend             │
│  ┌───────────────────────────────┐  │
│  │   assistant_routes.py         │  │
│  │   POST /assistant/query       │  │
│  └────────────┬──────────────────┘  │
│               ▼                      │
│  ┌───────────────────────────────┐  │
│  │   assistant_service.py        │  │ Phase 3
│  │   (Orchestration)             │  │ (Next)
│  └────────────┬──────────────────┘  │
│               ▼                      │
│  ┌───────────────────────────────┐  │
│  │  1. tokenizer_service.py      │  │ Phase 1 ✅
│  │  2. embedding_service.py      │  │ Existing ✅
│  │  3. retrieval_service.py      │  │ Phase 2 🔄
│  │  4. context_builder.py        │  │ Phase 2 🔄
│  │  5. prompt_engine.py          │  │ Phase 2 🔄
│  │  6. hf_textgen_service.py     │  │ Phase 2 🔄
│  └────────────┬──────────────────┘  │
└───────────────┼──────────────────────┘
                │
      ┌─────────┼─────────┐
      ▼         ▼         ▼
┌──────────┐ ┌────┐ ┌──────────────┐
│PostgreSQL│ │Redis│ │ HuggingFace  │
│ +pgvector│ │Cache│ │ Inference API│
└──────────┘ └────┘ └──────────────┘
```

---

**Next:** Implement Phase 2 services, then move to Phase 3 (orchestration)!

