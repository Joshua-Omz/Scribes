# Scribes Backend - Quick Start Script
# Run this script to set up your development environment

Write-Host "🚀 Setting up Scribes Backend..." -ForegroundColor Cyan

# Check Python version
Write-Host "`n📋 Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host $pythonVersion -ForegroundColor Green

# Create virtual environment if it doesn't exist
if (!(Test-Path "venv")) {
    Write-Host "`n🔧 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "`n✅ Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`n🔌 Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "`n⬆️  Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "`n📦 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Create .env file if it doesn't exist
if (!(Test-Path ".env")) {
    Write-Host "`n📝 Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✅ .env file created - Please edit it with your configuration" -ForegroundColor Green
    Write-Host "   Important: Set DATABASE_URL and JWT_SECRET_KEY" -ForegroundColor Cyan
} else {
    Write-Host "`n✅ .env file already exists" -ForegroundColor Green
}

Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Cyan

Write-Host "`n📚 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Edit .env file with your database and SMTP credentials" -ForegroundColor White
Write-Host "   2. Create PostgreSQL database: CREATE DATABASE scribes_db;" -ForegroundColor White
Write-Host "   3. Run migrations: alembic upgrade head" -ForegroundColor White
Write-Host "   4. Start server: python -m app.main" -ForegroundColor White
Write-Host "   5. Visit: http://localhost:8000/docs" -ForegroundColor White

Write-Host "`n🎯 Quick Commands:" -ForegroundColor Yellow
Write-Host "   Start dev server:  python -m app.main" -ForegroundColor White
Write-Host "   Run tests:         pytest" -ForegroundColor White
Write-Host "   Create migration:  alembic revision --autogenerate -m 'message'" -ForegroundColor White
Write-Host "   Apply migrations:  alembic upgrade head" -ForegroundColor White

Write-Host "`n✨ Happy coding!" -ForegroundColor Cyan
