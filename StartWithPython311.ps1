#!/usr/bin/env powershell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Gear Measurement Software with Python 3.11" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set Python 3.11 path
$Python311Path = "C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe"

Write-Host "Checking Python 3.11..." -ForegroundColor Green
if (Test-Path $Python311Path) {
    Write-Host "✓ Found Python 3.11 at $Python311Path" -ForegroundColor Green
    Write-Host ""
    Write-Host "Starting program..." -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    
    # Run the program with Python 3.11
    & $Python311Path "齿轮波纹度软件2_修改版_simplified.py"
    
    Write-Host ""
    Write-Host "Program exited. Press any key to continue..." -ForegroundColor Cyan
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
} else {
    Write-Host "✗ Python 3.11 not found at $Python311Path" -ForegroundColor Red
    Write-Host "Please check your Python installation." -ForegroundColor Yellow
    
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Cyan
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
