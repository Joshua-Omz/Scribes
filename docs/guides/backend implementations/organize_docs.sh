#!/bin/bash

# Move Phase 4 Circuit Breaker docs
mv PHASE_4_CIRCUIT_BREAKERS_OVERVIEW.md "circuit breaker/"
mv PHASE_4_DOCUMENTATION_COMPLETE.md "circuit breaker/"
mv PHASE_4_IMPLEMENTATION_PLAN.md "circuit breaker/"
mv PHASE_4_PREREQUISITES.md "circuit breaker/"
mv PHASE_4_TESTING_STRATEGY.md "circuit breaker/"

# Move Assistant-related docs
mv ASSISTANT_INTEGRATION_PLAN.md "assistant features/"
mv ASSISTANT_MANUAL_TESTING_GUIDE.md "assistant features/"
mv ASSISTANT_SERVICE_IMPLEMENTATION_COMPLETE.md "assistant features/"
mv ASSISTANT_UNIT_TESTS_COMPLETE.md "assistant features/"
mv HF_TEXTGEN_IMPLEMENTATION_COMPLETE.md "assistant features/"
mv HF_TEXTGEN_SERVICE_BLUEPRINT.md "assistant features/"
mv PHASE_1_COMPLETE.md "assistant features/"
mv PHASE_2_CHECKLIST.md "assistant features/"
mv PHASE_2_IMPLEMENTATION_GUIDE.md "assistant features/"
mv PHASE_2_SERVICE_IMPLEMENTATION_COMPLETE.md "assistant features/"

# Move Cross-Reference docs
mv CrossRef_Implementation.md "cross refs/"
mv CrossRef_feature.md "cross refs/"

# Move Embedding docs
mv Embedding_implementations.md "embeddings/"
mv TOKENIZER_ASYNC_ANALYSIS.md "embeddings/"
mv TOKENIZER_OBSERVABILITY_METRICS.md "embeddings/"

echo "Organization complete!"
