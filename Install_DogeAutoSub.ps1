# DogeAutoSub fresh installer (PowerShell)
# Downloads the full release from the LAN update server and extracts it.
# No Python or admin required — just PowerShell (built into Windows 7+).
#
# Defaults:
#   Server       http://dogeautosub.local:8100  (mDNS)
#   InstallDir   <folder containing this script>\DogeAutoSub
#
# So if you drop Install_DogeAutoSub.bat into D:\Tools\ and run it,
# the app installs at D:\Tools\DogeAutoSub\DogeAutoSub.exe.
#
# Usage:
#   .\Install_DogeAutoSub.ps1                                       # use defaults
#   .\Install_DogeAutoSub.ps1 -Server http://192.168.1.50:8100      # custom server
#   .\Install_DogeAutoSub.ps1 -InstallDir D:\Apps\DogeAutoSub       # custom dir
#   .\Install_DogeAutoSub.ps1 -NoPrompt                             # non-interactive

[CmdletBinding()]
param(
    [string]$Server = "http://dogeautosub.local:8100",
    [string[]]$FallbackServers = @("http://10.76.171.113:8100"),
    [string]$InstallDir = "",
    [switch]$NoPrompt
)

# Resolve default install dir relative to the script's own folder. We do
# this after the param block so $PSScriptRoot is reliable across PS hosts.
if ([string]::IsNullOrWhiteSpace($InstallDir)) {
    $base = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
    $InstallDir = Join-Path $base "DogeAutoSub"
}

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
Write-Host "    Primary     : $Server"
if ($FallbackServers -and $FallbackServers.Count -gt 0) {
    foreach ($fb in $FallbackServers) {
        Write-Host "    Fallback    : $fb"
    }
}
Write-Host "    Install to  : $InstallDir"

# ── 1. Probe the server (primary first, then any fallbacks) ──────────
Write-Step "1/3" "Probing update server..."

$candidates = @($Server) + @($FallbackServers | Where-Object { $_ -and $_ -ne $Server })
$manifest = $null
$reachableServer = $null
$lastError = $null

foreach ($candidate in $candidates) {
    Write-Host "      try $candidate ..." -ForegroundColor DarkGray
    try {
        $manifest = Invoke-WebRequest -Uri "$candidate/version.json" -UseBasicParsing -TimeoutSec 6 |
                    Select-Object -ExpandProperty Content |
                    ConvertFrom-Json
        $reachableServer = $candidate
        Write-Ok "server reachable at $candidate (version $($manifest.version))"
        break
    } catch {
        $lastError = $_.Exception.Message
        Write-Host "        unreachable ($lastError)" -ForegroundColor DarkYellow
    }
}

if (-not $manifest) {
    Write-Err "no server reachable on any candidate URL"
    Write-Host ""
    Write-Host "  Last error: $lastError" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  Make sure the update server is running on the host machine:" -ForegroundColor Yellow
    Write-Host "      python serve_updates.py" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  If your network blocks mDNS (.local), pass an explicit IP:" -ForegroundColor Yellow
    Write-Host "      Install_DogeAutoSub.bat -Server http://<host-ip>:8100" -ForegroundColor Yellow
    Pause-Exit 1
}

# All subsequent requests use whichever URL actually answered.
$Server = $reachableServer

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

# ── 3. Try the streaming-file installer first; fall back to zip ──────
# Streaming mode pulls one file at a time from /dist/<rel>. If a file
# already exists locally with the right size, it is skipped — so a
# re-run of the installer resumes a partial download for free.
$distManifest = $null
try {
    $distManifest = Invoke-WebRequest -Uri "$Server/dist_manifest.json" -UseBasicParsing -TimeoutSec 5 |
                    Select-Object -ExpandProperty Content |
                    ConvertFrom-Json
} catch {
    $distManifest = $null
}

function Install-FromStreamingFiles {
    param($manifest, $InstallDir, $Server)

    # Detect existing install. If DogeAutoSub.exe is already at the target,
    # this is a repair/upgrade pass — switch from "trust file size" to full
    # SHA-256 verification so outdated files (DLLs, .exe, .pyd) get caught
    # and replaced. Files in delta-update territory (.py/.css/.gif tracked
    # by the in-app updater) get the same treatment here — when the
    # installer's dist is the source of truth, it's correct to bring them
    # in line too.
    $repairMode = Test-Path (Join-Path $InstallDir "DogeAutoSub.exe")

    if ($repairMode) {
        Write-Step "2/3" "Repair mode: verifying every file by SHA-256..."
        Write-Host "      (existing install detected at $InstallDir)" -ForegroundColor DarkGray
    } else {
        Write-Step "2/3" "Streaming files (resumable; safe to re-run)..."
    }
    Write-Host ("      {0:N0} files, {1:N2} GB total" -f $manifest.total_files, ($manifest.total_bytes / 1GB)) -ForegroundColor DarkGray

    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    }

    # Hashing huge files (multi-GB model.bin, big DLLs) on a slow drive can
    # take minutes per file. Different builds of the same large binary
    # virtually always differ in size too, so trust size on anything above
    # this threshold and only hash smaller files.
    $hashThreshold = 50MB

    $i = 0
    $bytesDone = 0
    $bytesSkip = 0
    $skipped = 0
    $downloaded = 0
    $replaced = 0
    $files = $manifest.files
    $names = $files.PSObject.Properties.Name
    $total = $names.Count

    foreach ($rel in $names) {
        $i++
        $entry = $files.$rel
        $expected = [int64]$entry.size
        $expectedHash = $null
        if ($entry.PSObject.Properties.Name -contains "sha256") {
            $expectedHash = $entry.sha256
        }
        $localPath = Join-Path $InstallDir ($rel -replace "/", "\")
        $localDir = Split-Path -Parent $localPath
        if (-not (Test-Path $localDir)) {
            New-Item -ItemType Directory -Path $localDir -Force | Out-Null
        }

        $needsDownload = $true
        $wasReplacement = $false

        if (Test-Path $localPath) {
            $localSize = (Get-Item $localPath).Length

            if ($localSize -ne $expected) {
                # Size mismatch: always re-download.
                $wasReplacement = $true
            } elseif ($repairMode -and $expectedHash -and $expected -le $hashThreshold) {
                # In repair mode, verify by hash for files under the threshold.
                $localHash = (Get-FileHash -Path $localPath -Algorithm SHA256).Hash.ToLower()
                if ($localHash -eq $expectedHash.ToLower()) {
                    $needsDownload = $false
                } else {
                    $wasReplacement = $true
                    Write-Host ("        outdated -> $rel") -ForegroundColor DarkYellow
                }
            } else {
                # Fresh install, or file too large to hash: trust size.
                $needsDownload = $false
            }
        }

        if (-not $needsDownload) {
            $skipped++
            $bytesSkip += $expected
            continue
        }

        $url = "$Server/dist/$rel"
        $attempts = 0
        $maxAttempts = 3
        while ($true) {
            $attempts++
            try {
                Invoke-WebRequest -Uri $url -OutFile $localPath -UseBasicParsing -TimeoutSec 60
                break
            } catch {
                if ($attempts -ge $maxAttempts) { throw }
                Write-Host ("        retry $attempts/$maxAttempts : $rel") -ForegroundColor DarkYellow
                Start-Sleep -Seconds (2 * $attempts)
            }
        }

        $downloaded++
        if ($wasReplacement) { $replaced++ }
        $bytesDone += $expected

        # Cheap progress: every 1% of total file count, print a status line.
        if (($i % [Math]::Max(1, [int]($total / 100))) -eq 0) {
            $pct = [Math]::Round(100 * $i / $total, 1)
            $mb = [Math]::Round(($bytesDone + $bytesSkip) / 1MB, 0)
            Write-Host ("      [$pct%] $i / $total  ($mb MB)  -> $rel") -ForegroundColor DarkGray
        }
    }

    if ($repairMode) {
        Write-Ok ("downloaded $downloaded ($replaced replacements), verified $skipped intact, {0:N2} GB" -f (($bytesDone + $bytesSkip) / 1GB))
    } else {
        Write-Ok ("downloaded $downloaded, skipped $skipped (already correct), {0:N2} GB" -f (($bytesDone + $bytesSkip) / 1GB))
    }
}

if ($distManifest -and $distManifest.files) {
    try {
        Install-FromStreamingFiles -manifest $distManifest -InstallDir $InstallDir -Server $Server
        $streamingOk = $true
    } catch {
        Write-Err "streaming install failed: $($_.Exception.Message)"
        Write-Warn "falling back to zip download..."
        $streamingOk = $false
    }
} else {
    Write-Warn "server has no dist_manifest.json - using zip download"
    $streamingOk = $false
}

if ($streamingOk) {
    # Streaming mode: locate exe and skip the zip path entirely.
    $exePath = Join-Path $InstallDir "DogeAutoSub.exe"
    if (-not (Test-Path $exePath)) {
        $alt = Join-Path $InstallDir "DogeAutoSub\DogeAutoSub.exe"
        if (Test-Path $alt) { $exePath = $alt }
    }
} else {
    # ── Zip fallback path: wipe existing, download, extract ─────────────
    if (Test-Path $InstallDir) {
        Write-Step "2/3" "Removing previous install..."
        try {
            Remove-Item -LiteralPath $InstallDir -Recurse -Force
            Write-Ok "removed $InstallDir"
        } catch {
            Write-Err "could not remove $InstallDir"
            Write-Host "      $($_.Exception.Message)" -ForegroundColor DarkGray
            Write-Host "      Close DogeAutoSub if it is currently running." -ForegroundColor Yellow
            Pause-Exit 1
        }
    }

    $tmpZip = Join-Path $env:TEMP $fullZip
    if (Test-Path $tmpZip) { Remove-Item $tmpZip -Force }

    Write-Step "3/3" "Downloading $fullZip ..."
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

    $extractParent = Split-Path -Parent $InstallDir
    if (-not (Test-Path $extractParent)) {
        New-Item -ItemType Directory -Path $extractParent -Force | Out-Null
    }
    try {
        Expand-Archive -LiteralPath $tmpZip -DestinationPath $extractParent -Force
        Write-Ok "extracted"
    } catch {
        Write-Err "extract failed"
        Write-Host "      $($_.Exception.Message)" -ForegroundColor DarkGray
        Pause-Exit 1
    }
    Remove-Item $tmpZip -Force -ErrorAction SilentlyContinue

    $exePath = $null
    $candidates = @(
        (Join-Path $InstallDir "DogeAutoSub.exe"),
        (Join-Path $extractParent "DogeAutoSub\DogeAutoSub.exe")
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { $exePath = $c; break }
    }
}

# Zip-fallback branch may have landed extracted files at <parent>\DogeAutoSub
# even though the user requested a different folder name — relocate if so.
if (-not $streamingOk -and $extractParent) {
    $defaultExtract = Join-Path $extractParent "DogeAutoSub"
    if ($exePath -and (Test-Path $defaultExtract) -and ($defaultExtract -ne $InstallDir)) {
        if (Test-Path $InstallDir) { Remove-Item $InstallDir -Recurse -Force }
        Move-Item -LiteralPath $defaultExtract -Destination $InstallDir
        $exePath = Join-Path $InstallDir "DogeAutoSub.exe"
    }
}

if (-not $exePath -or -not (Test-Path $exePath)) {
    Write-Err "DogeAutoSub.exe not found after install"
    Write-Host "      Look manually inside: $InstallDir" -ForegroundColor Yellow
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
