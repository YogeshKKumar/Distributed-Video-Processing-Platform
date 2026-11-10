# Run automated pytest test suite for Distributed Video Processing Platform
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Running Automated Test Suite (Unit, Integration, E2E) ... " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

python -m pytest -v --tb=short

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nAll tests passed successfully!" -ForegroundColor Green
} else {
    Write-Host "`nSome tests failed. See output above for details." -ForegroundColor Red
}
