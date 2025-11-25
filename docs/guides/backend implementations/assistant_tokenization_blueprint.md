# SCRIBES AI ASSISTANT — Tokenization-Aware Blueprint & Implementation Skeleton

**Owner:** Joshua

This document is the final, implementation-ready blueprint that integrates **tokenization, chunking, context management, retrieval, and Hugging Face generation** into Scribes' Assistant (Phase 6). It includes an actionable skeleton (files + minimal code) so you can start implementing immediately.

> Reference SRS / SDS: /mnt/data/Scribes — Final Sds (compact + Glossary) V1.pdf

---

## 1 — Goals (short)
- Make RAG robust against long notes by enforcing token budgets.  
- Ensure chunks, embeddings, and DB vector dims align (you confirmed 384).  
- Provide safe, repeatable prompt construction and generation caps.  
- Keep implementation modular and testable.

---

## 2 — High-level pipeline (token-aware)

```
Client → assistant_router → assistant_service
         ├→ tokenizer_service (count/truncate/chunk)
         ├→ retrieval_service (pgvector; returns chunks)
         ├→ context_builder (select/top-k + compression)
         ├→ prompt_engine (templates + token budget enforcement)
         └→ hf_textgen_service (generate with caps)
Response ← format + sources
```

---

## 3 — Key Config (app/core/config.py additions)
```python
ASSISTANT = {
  "MODEL_CONTEXT_WINDOW": 2048,
  "ASSISTANT_TOP_K": 12,
  "CONTEXT_TOKEN_CAP": 1800,   # tokens reserved for retrieved context
  "SYSTEM_TOKENS": 150,
  "USER_QUERY_TOKENS": 150,
  "MAX_OUTPUT_TOKENS": 400,
  "EMBEDDING_DIM": 384,
}
HF = {
  "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
  "GEN_MODEL": "meta-llama/Llama-2-7b-chat-hf",  # example
}
```

---

## 4 — Tokenizer Service (app/services/tokenizer_service.py)
Responsibilities:
- Load HF tokenizer matching generation model
- Expose: `count_tokens(text)`, `encode(text)`, `decode(tokens)`, `truncate_to_tokens(text, max_tokens)`, `chunk_text(text, chunk_size, overlap)`

Skeleton:
```python
from transformers import AutoTokenizer

class TokenizerService:
    def __init__(self, model_name):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    def count_tokens(self, text: str) -> int:
        return len(self.tokenizer(text)['input_ids'])

    def truncate(self, text: str, max_tokens: int) -> str:
        ids = self.tokenizer(text, truncation=True, max_length=max_tokens)['input_ids']
        return self.tokenizer.decode(ids)

    def chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 64):
        ids = self.tokenizer(text)['input_ids']
        chunks = []
        for i in range(0, len(ids), chunk_size - overlap):
            chunk_ids = ids[i:i+chunk_size]
            chunks.append(self.tokenizer.decode(chunk_ids))
        return chunks
```

Notes:
- Use the same tokenizer for both embedding chunking and generation to keep token accounting consistent.

---

## 5 — Chunking & Storage
When creating/updating a note:
1. Use `TokenizerService.chunk_text(note.content, chunk_size=384, overlap=64)` → produces chunks (~384 tokens)  
2. For each chunk: generate embedding (embedding dim 384) and store in `note_chunks` table with `note_id, chunk_idx, chunk_text, embedding`.

DB schema (new table `note_chunks`):
```sql
CREATE TABLE note_chunks (
  id SERIAL PRIMARY KEY,
  note_id INTEGER REFERENCES notes(id) ON DELETE CASCADE,
  chunk_idx INTEGER NOT NULL,
  chunk_text TEXT NOT NULL,
  embedding VECTOR(384),
  created_at timestamptz DEFAULT now()
);
CREATE INDEX ON note_chunks USING ivfflat (embedding vector_cosine_ops);
```

Rationale:
- More accurate retrieval; avoids whole-note noise.  
- Works with your existing pgvector setup.

---

## 6 — Retrieval Service (app/services/retrieval_service.py)
Responsibilities:
- Embed query
- Run vector similarity search on `note_chunks` (user-scoped)
- Return ranked list of chunks with score and metadata

Skeleton:
```python
def retrieve_top_chunks(db, query_vec, user_id, top_k=50):
    sql = '''
      SELECT id, note_id, chunk_text, embedding, (embedding <=> :q) as score
      FROM note_chunks
      WHERE note_id IN (SELECT id FROM notes WHERE user_id=:uid)
      ORDER BY embedding <=> :q
      LIMIT :k
    '''
    return db.execute(sql, {"q": query_vec, "uid": user_id, "k": top_k}).fetchall()
```

Notes:
- Use a large `top_k` (e.g., 50–100) then rerank/trim by token budget.

---

## 7 — Context Builder (app/services/context_builder.py)
Goal: Build the final context that fits `CONTEXT_TOKEN_CAP` while maximizing relevance.

Algorithm:
1. Accept `retrieved_chunks` sorted by score.
2. Initialize `tokens_used = 0` (system + user reserved)
3. For each chunk:
   - `chunk_tokens = tokenizer.count_tokens(chunk_text)
   - If tokens_used + chunk_tokens > CONTEXT_TOKEN_CAP -> skip or summarize chunk
   - Else append chunk and increment tokens_used
4. If not enough context or too many tokens, run an extractive summarization on lower-ranked chunks to compress (see compression).

Compression:
- Use short extractive summarization: select top N sentences (by TF-IDF) from chunk or call a small local HF summarization model with low cost.

Return: ordered list of `{note_id, chunk_idx, text, score, tokens}` and `context_token_count`.

---

## 8 — Prompt Engine (app/core/prompt_engine.py)
Responsibilities:
- Assemble final prompt: system instruction + context blocks + user question
- Ensure total tokens (system + context + query + expected output) ≤ MODEL_CONTEXT_WINDOW
- If over budget: trigger context compression policy

Prompt template (short):
```
SYSTEM: You are Scribes Assistant. Use only the context provided. Cite sources by note id.

CONTEXT:
-- BEGIN CONTEXT --
{context_blocks}
-- END CONTEXT --

QUESTION: {user_query}

Answer concisely. Provide sources as [note_id].
```

---

## 9 — HF Text Generation Service (app/services/hf_textgen_service.py)
Responsibilities:
- Load HF model (local or remote) with generation configs
- Provide `generate(prompt, max_new_tokens, temperature)` with timeout and retry

Skeleton (local):
```python
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained(GEN_MODEL)
model = AutoModelForCausalLM.from_pretrained(GEN_MODEL, device_map='auto')

def generate(prompt, max_new_tokens=256, temperature=0.2):
    inputs = tokenizer(prompt, return_tensors='pt').to(model.device)
    out = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=True, temperature=temperature)
    return tokenizer.decode(out[0], skip_special_tokens=True)
```

Operational controls:
- enforce `max_new_tokens` per operation
- set generation timeout (wrap call in async with timeout)
- fallback model (smaller) if OOM

---

## 10 — Assistant Service Orchestration (app/services/assistant_service.py)
Flow (compact):
1. `count_tokens(query)` and truncate if > USER_QUERY_TOKENS
2. `query_vec = embedding_service.embed(query)`
3. `retrieved = retrieval_service.retrieve_top_chunks(query_vec, user_id, top_k=100)`
4. `context = context_builder.build(retrieved, token_budget)`
5. `prompt = prompt_engine.build(context, query)`
6. `answer = hf_textgen_service.generate(prompt, max_new_tokens=MAX_OUTPUT_TOKENS)`
7. `post_process(answer)` — sanitize and extract source citations
8. Return `{answer, sources, meta}`

Include metrics and logging at each step.

---

## 11 — Caching, Rate-limiting, and Idempotency
- Cache assembled prompts and answers by `(user_id, query_hash)` for TTL 24h
- Store assistant interactions in `assistant_history` table for auditing
- Rate limit per-user through Redis (e.g., 60/min) and return 429 on exceed

---

## 12 — Tests to write
- Unit: tokenizer functions, chunker, context builder, prompt engine
- Integration: end-to-end with small HF gen model (use tiny model in CI)
- Stress: multiple concurrent assistant queries to observe latencies
- Security: ensure notes not leaked in logs

---

## 13 — Files to scaffold (implementation skeleton)

```
app/
 ├── services/
 │    ├── tokenizer_service.py
 │    ├── chunking_service.py
 │    ├── retrieval_service.py
 │    ├── context_builder.py
 │    ├── embedding_service.py   # existing
 │    ├── hf_textgen_service.py
 │    └── assistant_service.py
 ├── core/
 │    ├── config.py
 │    └── prompt_engine.py
 ├── routes/
 │    └── assistant_routes.py
 ├── models/
 │    └── note_chunks.py
 ├── db/
 │    └── migrations/  # add note_chunks + indices
 └── tests/
      └── test_assistant_*.py
```

I can scaffold each of these files with starter code now.

---

## 14 — Implementation Plan (sprint-ready)
**Sprint 1 (2–3 days)**
- scaffold files, tokenizer, chunking, DB migration
- unit tests for tokenizer + chunking

**Sprint 2 (3–4 days)**
- implement retrieval + context builder + prompt engine
- integration test with tiny HF model

**Sprint 3 (2–3 days)**
- implement HF gen service + assistant orchestration
- caching, rate limiting, history

**Sprint 4 (2 days)**
- reranker (optional), compression improvements, load tests

---

## 15 — Ready to generate scaffold
Say **"scaffold now"** and I will generate the starter code files for:
- tokenizer_service.py
- chunking_service.py
- note_chunks model + migration snippet
- retrieval_service.py
- context_builder.py
- prompt_engine.py
- hf_textgen_service.py
- assistant_service.py
- assistant_routes.py

I'll include minimal working code and test stubs so you can run an initial end-to-end locally (using a small HF model).

