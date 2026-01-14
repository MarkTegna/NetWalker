# Clear Python Bytecode Cache
# This script removes all __pycache__ directories and .pyc files

Write-Host "Clearing Python bytecode cache..." -ForegroundColor Cyan
Write-Host ""

# Count before cleanup
$pycacheDirs = Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
$pycFiles = Get-ChildItem -Path . -Recurse -File -Filter "*.pyc" -ErrorAction SilentlyContinue

Write-Host "Found:" -ForegroundColor Yellow
Write-Host "  $($pycacheDirs.Count) __pycache__ directories"
Write-Host "  $($pycFiles.Count) .pyc files"
Write-Host ""

# Remove __pycache__ directories
Write-Host "Removing __pycache__ directories..." -ForegroundColor Cyan
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Write-Host "  [OK] Removed __pycache__ directories" -ForegroundColor Green

# Remove .pyc files
Write-Host "Removing .pyc files..." -ForegroundColor Cyan
Get-ChildItem -Path . -Recurse -File -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force
Write-Host "  [OK] Removed .pyc files" -ForegroundColor Green

Write-Host ""
Write-Host "Verifying cleanup..." -ForegroundColor Cyan
$remainingCache = Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
$remainingPyc = Get-ChildItem -Path . -Recurse -File -Filter "*.pyc" -ErrorAction SilentlyContinue

if ($remainingCache.Count -eq 0 -and $remainingPyc.Count -eq 0) {
    Write-Host "  [OK] All cache files removed successfully!" -ForegroundColor Green
} else {
    Write-Host "  [WARNING] Some cache files remain:" -ForegroundColor Yellow
    Write-Host "    $($remainingCache.Count) __pycache__ directories"
    Write-Host "    $($remainingPyc.Count) .pyc files"
}

Write-Host ""
Write-Host "Cache cleanup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Run NetWalker again to test with fresh code"
Write-Host "  2. Check log for: 'DiscoveryEngine initialized with max_depth=99'"
Write-Host "  3. Verify devices at depth 2+ are being walked"
