# Phase 2 Quick Action Checklist

**Your Decisions:**
- ✅ HuggingFace API (no GPU)
- ✅ Pastoral tone
- ✅ High/low relevance separation
- ✅ Store low-relevance for later

---

## Step-by-Step Implementation (30-60 minutes)

### Step 1: Environment Setup (5 min)

```powershell
# 1. Install HuggingFace Hub
pip install huggingface-hub

# 2. Get HF token
# Visit: https://huggingface.co/settings/tokens
# Create token → Copy it

# 3. Update .env file
```

Add to `.env`:
```env
HF_API_KEY=hf_your_token_here
HF_USE_API=True
HF_GENERATION_MODEL=meta-llama/Llama-3.2-3B-Instruct
HF_GENERATION_TEMPERATURE=0.3
```

### Step 2: Implement Services (20 min)

Open `PHASE_2_IMPLEMENTATION_GUIDE.md` and copy the code for each file:

**File 1: `app/services/retrieval_service.py`**
- [ ] Copy full implementation from guide
- [ ] Replace existing scaffold file
- [ ] Note: Implements user isolation + high/low relevance separation

**File 2: `app/services/context_builder.py`**
- [ ] Copy full implementation from guide
- [ ] Replace existing scaffold file
- [ ] Note: Uses high-relevance, stores low-relevance

**File 3: `app/core/prompt_engine.py`**
- [ ] Copy full implementation from guide
- [ ] Replace existing scaffold file
- [ ] Note: Pastoral tone + prompt injection defense

**File 4: `app/services/hf_textgen_service.py`**
- [ ] Copy full implementation from guide
- [ ] Replace existing scaffold file
- [ ] Note: Uses HF Inference API (no GPU needed)

### Step 3: Test Individual Services (15 min)

**Test 1: Prompt Engine**
```powershell
python -c "from app.core.prompt_engine import get_prompt_engine; engine = get_prompt_engine(); result = engine.build_prompt('What is faith?', 'Faith is...'); print('Pastoral tone:', 'pastoral' in result['prompt'].lower()); print('Tokens:', result['token_breakdown']['total_input_tokens'])"
```

**Test 2: Context Builder**
```powershell
python
```
```python
from app.services.context_builder import get_context_builder

builder = get_context_builder()
high = [{"chunk_id": 1, "note_id": 1, "chunk_text": "Faith is trust.", "relevance_score": 0.9, "note_title": "Faith"}]
low = [{"chunk_id": 2, "note_id": 2, "chunk_text": "Picnic Saturday.", "relevance_score": 0.3, "note_title": "News"}]

result = builder.build_context(high, low, 1800)
print(f"High-relevance used: {len(result['chunks_used'])}")
print(f"Low-relevance stored: {len(result['low_relevance_stored'])}")
print(f"Context preview: {result['context_text'][:100]}")
```

**Test 3: Generation Service** (requires HF API key)
```python
import asyncio
from app.services.hf_textgen_service import get_textgen_service

async def test():
    gen = get_textgen_service()
    result = await gen.generate("You are a pastoral assistant. What is grace?\nAnswer:", max_new_tokens=50)
    print(f"Generated: {result['generated_text'][:200]}")
    print(f"Latency: {result['latency_ms']}ms")

asyncio.run(test())
```

### Step 4: Run Integration Test (10 min)

Create and run the integration test:

```powershell
# Copy test code from guide to:
# app/tests/test_assistant_integration.py

# Run it
pytest app/tests/test_assistant_integration.py -v
```

Should see: `✅ Integration test passed!`

### Step 5: Verify Configuration (5 min)

```powershell
python -c "from app.core.config import settings; print('Model:', settings.hf_generation_model); print('API mode:', settings.hf_use_api); print('Temperature:', settings.hf_generation_temperature)"
```

Should show:
```
Model: meta-llama/Llama-3.2-3B-Instruct
API mode: True
Temperature: 0.3
```

---

## Verification Checklist

After implementation, verify:

- [ ] All 4 service files replaced (no more `NotImplementedError`)
- [ ] HF_API_KEY in .env
- [ ] `pip install huggingface-hub` completed
- [ ] Prompt engine has pastoral tone (test shows "pastoral" in system prompt)
- [ ] Context builder separates high/low relevance (test shows both lists)
- [ ] Generation service connects to HF API (test generates text)
- [ ] No import errors when loading services
- [ ] Integration test passes

---

## Common Issues & Fixes

**Error: "HF_API_KEY not found"**
```powershell
# Check .env file has:
HF_API_KEY=hf_...
# Restart Python/server to reload env
```

**Error: "Model not found"**
```env
# Try alternative model in .env:
HF_GENERATION_MODEL=mistralai/Mistral-7B-Instruct-v0.2
```

**Error: "Rate limit exceeded"**
- Wait 1 minute
- HF free tier has limits
- Consider Pro account ($9/month for higher limits)

**Error: Import errors**
```powershell
pip install --upgrade huggingface-hub transformers
```

---

## What You Get After Phase 2

✅ **Working Components:**
1. Retrieval service (user-isolated vector search)
2. Context builder (high/low relevance separation)
3. Prompt engine (pastoral tone)
4. Generation service (HF API integration)

✅ **Capabilities:**
- Retrieve relevant chunks from user's notes
- Build token-aware context
- Generate pastoral-toned responses
- Store low-relevance chunks for later use

🔴 **Still Need (Phase 3):**
- Assistant orchestration (wire services together)
- API routes (POST /assistant/query endpoint)
- Embedding generation (for query vectorization)

---

## Next Steps

When Phase 2 is complete:

1. **Mark todos 6-10 complete** ✅
2. **Read Phase 3 guide** (I can create it)
3. **Test with real sermon notes** (after migration)
4. **Review pastoral tone** in generated answers

---

## Quick Reference

**Service Locations:**
- `app/services/retrieval_service.py`
- `app/services/context_builder.py`
- `app/core/prompt_engine.py`
- `app/services/hf_textgen_service.py`

**Test Files:**
- `app/tests/test_assistant_integration.py`
- Unit tests (run individually to test each service)

**Documentation:**
- Full guide: `PHASE_2_IMPLEMENTATION_GUIDE.md`
- Phase 1 summary: `PHASE_1_COMPLETE.md`
- Quick start: `QUICK_START_ASSISTANT.md`

**Config:**
- Settings: `app/core/config.py`
- Environment: `.env`

---

**Estimated Time:** 30-60 minutes  
**Difficulty:** Medium (copy-paste + test)  
**Dependencies:** HuggingFace API token (free)

**Ready to start? Begin with Step 1!** 🚀

