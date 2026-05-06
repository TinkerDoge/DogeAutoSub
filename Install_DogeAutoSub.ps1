# DogeAutoSub fresh installer (PowerShell)
# Downloads the full release from the LAN update server and extracts it.
# No Python or admin required — just PowerShell (built into Windows 7+).
#
# Defaults:
#   Server       http://dogeautosub.local:8100  (mDNS)
#   InstallDir   $env:USERPROFILE\DogeAutoSub
#
# Usage:
#   .\Install_DogeAutoSub.ps1                                       # use defaults
#   .\Install_DogeAutoSub.ps1 -Server http://192.168.1.50:8100      # custom server
#   .\Install_DogeAutoSub.ps1 -InstallDir D:\Apps\DogeAutoSub       # custom dir
#   .\Install_DogeAutoSub.ps1 -NoPrompt                             # non-interactive

[CmdletBinding()]
param(
    [string]$Server = "http://dogeautosub.local:8100",
    [string]$InstallDir = (Join-Path $env:USERPROFILE "DogeAutoSub"),
    [switch]$NoPrompt
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "Continue"

function Write-Heading($text) {
    Write-Host ""
    Write-Host "  ===================================================" -ForegroundColor DarkCyan
    Write-Host "    $text" -ForegroundColor White
    Write-Host "  ===================================================" -ForegroundColor DarkCyan
}

function Write-Step($n, $text) {
    Write-Host ""
    Write-Host "  [$n] $text" -ForegroundColor Cyan
}

function Write-Ok($text)   { Write-Host "      OK: $text" -ForegroundColor Green }
function Write-Warn($text) { Write-Host "      WARN: $text" -ForegroundColor Yellow }
function Write-Err($text)  { Write-Host "      FAIL: $text" -ForegroundColor Red }

function Pause-Exit($code) {
    if (-not $NoPrompt) {
        Write-Host ""
        Read-Host "Press Enter to close" | Out-Null
    }
    exit $code
}

Write-Heading "DogeAutoSub Installer"
Write-Host "    Server      : $Server"
Write-Host "    Install to  : $InstallDir"

# ── 1. Probe the server ──────────────────────────────────────────────
Write-Step "1/4" "Probing update server..."
try {
    $manifest = Invoke-WebRequest -Uri "$Server/version.json" -UseBasicParsing -TimeoutSec 10 |
                Select-Object -ExpandProperty Content |
                ConvertFrom-Json
    Write-Ok "server reachable. Latest version: $($manifest.version)"
} catch {
    Write-Err "cannot reach $Server/version.json"
    Write-Host "      $($_.Exception.Message)" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  Make sure the update server is running on the host machine:" -ForegroundColor Yellow
    Write-Host "      python serve_updates.py" -ForegroundColor Yellow
    Pause-Exit 1
}

$version = $manifest.version
$fullZip = "DogeAutoSub_v${version}_full.zip"
$srcZip  = $manifest.filename

# ── 2. Confirm with user ─────────────────────────────────────────────
if (-not $NoPrompt) {
    Write-Host ""
    Write-Host "  Will download : $fullZip  (or $srcZip if full bundle missing)" -ForegroundColor White
    Write-Host "  Will extract  : $InstallDir" -ForegroundColor White
    if (Test-Path $InstallDir) {
        Write-Host "  WARNING       : $InstallDir already exists and will be wiped" -ForegroundColor Yellow
    }
    Write-Host ""
    $confirm = Read-Host "Proceed? [Y/n]"
    if ($confirm -eq "n" -or $confirm -eq "N") {
        Write-Host "  Cancelled." -ForegroundColor Yellow
        Pause-Exit 0
    }
}

# ── 3. Wipe existing install ─────────────────────────────────────────
if (Test-Path $InstallDir) {
    Write-Step "2/4" "Removing previous install..."
    try {
        Remove-Item -LiteralPath $InstallDir -Recurse -Force
        Write-Ok "removed $InstallDir"
    } catch {
        Write-Err "could not remove $InstallDir"
        Write-Host "      $($_.Exception.Message)" -ForegroundColor DarkGray
        Write-Host "      Close DogeAutoSub if it is currently running." -ForegroundColor Yellow
        Pause-Exit 1
    }
} else {
    Write-Step "2/4" "No previous install detected."
}

# ── 4. Download ──────────────────────────────────────────────────────
$tmpZip = Join-Path $env:TEMP $fullZip
if (Test-Path $tmpZip) { Remove-Item $tmpZip -Force }

Write-Step "3/4" "Downloading $fullZip ..."
Write-Host "      (this can be several GB; please be patient)" -ForegroundColor DarkGray

$downloadOk = $false
try {
    Invoke-WebRequest -Uri "$Server/$fullZip" -OutFile $tmpZip -UseBasicParsing
    Write-Ok "downloaded $([Math]::Round((Get-Item $tmpZip).Length / 1MB, 1)) MB"
    $downloadOk = $true
} catch {
    Write-Warn "full bundle not available, trying source zip..."
    try {
        Invoke-WebRequest -Uri "$Server/$srcZip" -OutFile $tmpZip -UseBasicParsing
        Write-Ok "downloaded source zip ($([Math]::Round((Get-Item $tmpZip).Length / 1MB, 1)) MB)"
        $downloadOk = $true
    } catch {
        Write-Err "download failed"
        Write-Host "      $($_.Exception.Message)" -ForegroundColor DarkGray
    }
}

if (-not $downloadOk) { Pause-Exit 1 }

# ── 5. Extract ───────────────────────────────────────────────────────
Write-Step "4/4" "Extracting to $InstallDir ..."
$extractParent = Split-Path -Parent $InstallDir
if (-not (Test-Path $extractParent)) { New-Item -ItemType Directory -Path $extractParent -Force | Out-Null }

try {
    # The PyInstaller zip wraps everything in a "DogeAutoSub" folder, so
    # extracting to the parent gives us $extractParent\DogeAutoSub already.
    # If the user requested a different dir name we'll rename below.
    Expand-Archive -LiteralPath $tmpZip -DestinationPath $extractParent -Force
    Write-Ok "extracted"
} catch {
    Write-Err "extract failed"
    Write-Host "      $($_.Exception.Message)" -ForegroundColor DarkGray
    Pause-Exit 1
}

# Locate the actual exe — the zip may produce DogeAutoSub\DogeAutoSub.exe
# under the extraction parent.
$exePath = $null
$candidates = @(
    (Join-Path $InstallDir "DogeAutoSub.exe"),
    (Join-Path $extractParent "DogeAutoSub\DogeAutoSub.exe")
)
foreach ($c in $candidates) {
    if (Test-Path $c) { $exePath = $c; break }
}

# If extraction landed at $extractParent\DogeAutoSub but user asked for a
# different name, move it.
$defaultExtract = Join-Path $extractParent "DogeAutoSub"
if ($exePath -and (Test-Path $defaultExtract) -and ($defaultExtract -ne $InstallDir)) {
    if (Test-Path $InstallDir) { Remove-Item $InstallDir -Recurse -Force }
    Move-Item -LiteralPath $defaultExtract -Destination $InstallDir
    $exePath = Join-Path $InstallDir "DogeAutoSub.exe"
}

# Clean up temp zip
Remove-Item $tmpZip -Force -ErrorAction SilentlyContinue

if (-not $exePath -or -not (Test-Path $exePath)) {
    Write-Err "DogeAutoSub.exe not found after extract"
    Write-Host "      Look manually inside: $extractParent" -ForegroundColor Yellow
    Pause-Exit 1
}

Write-Heading "Install complete"
Write-Host "    Path : $exePath" -ForegroundColor White

# ── 6. Optional desktop shortcut ─────────────────────────────────────
$makeShortcut = $true
if (-not $NoPrompt) {
    $r = Read-Host "  Create desktop shortcut? [Y/n]"
    if ($r -eq "n" -or $r -eq "N") { $makeShortcut = $false }
}
if ($makeShortcut) {
    try {
        $shell = New-Object -ComObject WScript.Shell
        $linkPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "DogeAutoSub.lnk"
        $sc = $shell.CreateShortcut($linkPath)
        $sc.TargetPath = $exePath
        $sc.WorkingDirectory = Split-Path $exePath -Parent
        $sc.IconLocation = "$exePath,0"
        $sc.Save()
        Write-Ok "shortcut placed on desktop"
    } catch {
        Write-Warn "could not create shortcut: $($_.Exception.Message)"
    }
}

# ── 7. Optional launch ───────────────────────────────────────────────
if (-not $NoPrompt) {
    $r = Read-Host "  Launch DogeAutoSub now? [Y/n]"
    if ($r -ne "n" -and $r -ne "N") {
        Start-Process -FilePath $exePath
    }
}

Pause-Exit 0
