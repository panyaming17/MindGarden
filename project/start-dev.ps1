# Quick Start Script for Development
# This script starts both backend and frontend services

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  Starting Development Services" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python environment..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python not found. Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

# Check Node.js
Write-Host "Checking Node.js environment..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  1. Starting Backend Service" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

# Setup backend virtual environment
if (!(Test-Path "backend/venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv backend/venv
}

Write-Host "Activating Python virtual environment..." -ForegroundColor Yellow
& ".\backend\venv\Scripts\Activate.ps1"

Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
Set-Location backend
pip install -r requirements.txt --quiet

# Check .env file
if (!(Test-Path "../.env")) {
    Write-Host "Warning: .env file not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item "..\.env.example" "..\.env"
}

Write-Host "Starting backend service (FastAPI)..." -ForegroundColor Green
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan

# Start backend in background
Start-Process -FilePath "uvicorn" -ArgumentList "main:app","--reload","--host","0.0.0.0","--port","8000" -WindowStyle Normal

Set-Location ..

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  2. Starting Frontend Service" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

# Setup frontend
if (!(Test-Path "frontend/node_modules")) {
    Write-Host "Installing frontend dependencies (this may take a few minutes)..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
}

# Check frontend .env
if (!(Test-Path "frontend/.env")) {
    Write-Host "Warning: frontend/.env file not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item "frontend\.env.example" "frontend\.env"
}

Write-Host "Starting frontend dev server (Vite + Vue3)..." -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Set-Location frontend

# Start frontend in background
Start-Process -FilePath "npm" -ArgumentList "run","dev" -WindowStyle Normal

Set-Location ..

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  All Services Started!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs:    http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Frontend:    http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C in each terminal to stop services" -ForegroundColor Yellow
Write-Host ""
