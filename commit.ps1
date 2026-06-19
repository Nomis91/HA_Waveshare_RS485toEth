<#
.SYNOPSIS
    Prepares a commit and opens TortoiseGit with an auto-generated message.
.DESCRIPTION
    Stages all changes, analyzes what changed, builds a descriptive commit
    message, then launches the TortoiseGit commit dialog with it pre-filled.
#>

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repo

# Stage everything
git add -A

# Collect changed files (cached / staged)
$staged   = @(git diff --cached --name-only 2>$null)
$newFiles = @(git ls-files --others --exclude-standard 2>$null)
$deleted  = @(git diff --cached --diff-filter=D --name-only 2>$null)
$renamed  = @(git diff --cached --name-status 2>$null | Where-Object { $_ -match '^R' })

# Nothing to commit?
if ($staged.Count -eq 0 -and $newFiles.Count -eq 0) {
    Write-Host ""
    Write-Host "Nothing to commit - working tree clean." -ForegroundColor Yellow
    exit 0
}

# Count by extension
$py    = @($staged | Where-Object { $_ -match '\.py$'   }).Count
$json  = @($staged | Where-Object { $_ -match '\.json$' }).Count
$md    = @($staged | Where-Object { $_ -match '\.md$'   }).Count
$other = @($staged | Where-Object { $_ -notmatch '\.(py|json|md)$' }).Count
$newN  = $newFiles.Count
$delN  = $deleted.Count
$renN  = $renamed.Count
$total = $staged.Count + $newN

# --- Build the commit message ---
$lines = [System.Collections.Generic.List[string]]::new()

$lines.Add("Update waveshare_eth2x integration")
$lines.Add("")

# Summary
$parts = @()
if ($py    -gt 0) { $parts += "$py Python file(s)" }
if ($json  -gt 0) { $parts += "$json JSON file(s)" }
if ($md    -gt 0) { $parts += "$md documentation file(s)" }
if ($other -gt 0) { $parts += "$other other file(s)" }
if ($newN  -gt 0) { $parts += "$newN new file(s) added" }
if ($delN  -gt 0) { $parts += "$delN file(s) deleted" }
if ($renN  -gt 0) { $parts += "$renN file(s) renamed" }

if ($parts.Count -gt 0) {
    $lines.Add("Changed: " + ($parts -join ", "))
    $lines.Add("")
}

# Detailed breakdown by area
$details = @()

$allText = ($staged -join "`n")

if ($allText -match "hacs\.json")            { $details += "  + Added HACS integration support" }
if ($allText -match "manifest\.json")        { $details += "  + Updated integration manifest" }
if ($allText -match "strings\.json")         { $details += "  + Updated UI translations" }
if ($allText -match "const\.py")             { $details += "  + Updated integration constants / naming" }
if ($allText -match "config_flow")           { $details += "  + Updated configuration flow" }
if ($allText -match "gateway\.py")           { $details += "  + Updated TCP gateway layer" }
if ($allText -match "protocol\.py")          { $details += "  + Updated Modbus RTU protocol" }
if ($allText -match "devices[/\\]")          { $details += "  + Updated device drivers" }
if ($allText -match "platforms[/\\]")        { $details += "  + Updated Home Assistant entity platforms" }
if ($allText -match "coordinators[/\\]")     { $details += "  + Updated integration coordinators" }
if ($allText -match "health[/\\]")           { $details += "  + Updated health monitoring" }
if ($allText -match "errors[/\\]")           { $details += "  + Updated error tracking" }

if ($details.Count -gt 0) {
    $lines.Add("Details:")
    $lines.AddRange($details)
    $lines.Add("")
}

# List every changed file
$lines.Add("Files:")
foreach ($f in $staged) {
    $clean = $f.Replace('\','/')
    $lines.Add("  - $clean")
}
foreach ($f in $newFiles) {
    $clean = $f.Replace('\','/')
    $lines.Add("  + $clean")
}

# Total
$lines.Add("")
$lines.Add("Total: $total file(s)")

# Final message
$message = $lines -join "`n"

# Display
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Generated commit message:" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
Write-Host $message
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Write to temp file for TortoiseGit /logmsgfile
$msgFile = Join-Path $env:TEMP "tgit_commit_msg.txt"
[System.IO.File]::WriteAllText($msgFile, $message, [System.Text.UTF8Encoding]::new($false))

# Launch TortoiseGit commit dialog
$proc = "TortoiseGitProc.exe"
$args = "/command:commit", "/path:`"$repo`"", "/logmsgfile:`"$msgFile`""

Write-Host "Opening TortoiseGit commit dialog..." -ForegroundColor Green
Start-Process $proc -ArgumentList $args
