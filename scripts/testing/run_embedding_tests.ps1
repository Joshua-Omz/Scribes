# Run Embedding Tests
# This script runs the embedding generation tests

Write-Host "🧪 Running Note Embedding Tests..." -ForegroundColor Cyan
Write-Host ""

# Run the specific test file
pytest app/tests/test_note_embeddings.py -v --tb=short

Write-Host ""
Write-Host "✅ Test run complete!" -ForegroundColor Green
