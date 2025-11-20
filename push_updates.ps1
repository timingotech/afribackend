# Push backend updates to Railway
Write-Host "Pushing backend updates to Railway..." -ForegroundColor Green

# Check current branch
$branch = git branch --show-current
Write-Host "Current branch: $branch" -ForegroundColor Cyan

# Show pending commits
Write-Host "`nPending commits:" -ForegroundColor Yellow
git log origin/$branch..$branch --oneline

# Push to origin
Write-Host "`nPushing to origin..." -ForegroundColor Green
git push origin $branch

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Successfully pushed to Railway!" -ForegroundColor Green
    Write-Host "Railway will automatically deploy the changes." -ForegroundColor Cyan
    Write-Host "`nCheck deployment at: https://railway.app" -ForegroundColor Yellow
} else {
    Write-Host "`n❌ Push failed. Please check your git credentials." -ForegroundColor Red
    Write-Host "You may need to:" -ForegroundColor Yellow
    Write-Host "  1. Configure git credentials" -ForegroundColor White
    Write-Host "  2. Use SSH key authentication" -ForegroundColor White
    Write-Host "  3. Or push manually through GitHub Desktop/VS Code" -ForegroundColor White
}
