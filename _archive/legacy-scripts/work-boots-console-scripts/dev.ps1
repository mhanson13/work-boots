param(
  [string]$ApiUrl = "http://localhost:4000"
)

Write-Host "Running backend in dev mode..." -ForegroundColor Cyan
Push-Location ..\backend
npm install
npm run dev
Pop-Location
