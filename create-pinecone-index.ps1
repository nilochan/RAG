# PowerShell script to create HuggingFace Pinecone index

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host "=" * 59 -ForegroundColor Cyan
Write-Host "🤗 HuggingFace Embeddings Pinecone Index Setup" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host "=" * 59 -ForegroundColor Cyan
Write-Host ""

# Change to backend directory
Set-Location -Path "educational-rag-platform"

Write-Host "📦 Installing required Python packages..." -ForegroundColor Yellow
pip install pinecone-client python-dotenv

Write-Host ""
Write-Host "🚀 Running setup script..." -ForegroundColor Yellow
python setup_huggingface_index.py

Write-Host ""
Write-Host "✅ Setup complete! Check the output above for success status." -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Copy the PINECONE_HOST from Pinecone dashboard" -ForegroundColor White
Write-Host "2. Add PINECONE_HOST to Railway environment variables" -ForegroundColor White
Write-Host "3. Railway will auto-deploy with FREE embeddings!" -ForegroundColor White
Write-Host ""

# Return to original directory
Set-Location -Path ".."
