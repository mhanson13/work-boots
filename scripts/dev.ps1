param(
  [ValidateSet("run", "test")]
  [string]$Command = "run",
  [switch]$Postgres,
  [switch]$UpgradePip,
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$PytestArgs
)

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if ($Command -eq "run") {
  $argsList = @()
  if ($Postgres) { $argsList += "postgres" }
  if ($UpgradePip) { $argsList += "--upgrade-pip" }
  & ".\scripts\run_api.bat" @argsList
  exit $LASTEXITCODE
}

& ".\scripts\test_api.bat" @PytestArgs
exit $LASTEXITCODE
