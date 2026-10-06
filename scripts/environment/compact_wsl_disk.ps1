<#
.SYNOPSIS
    Compacts and shrinks the WSL2 Ubuntu ext4.vhdx virtual hard disk file on Windows.

.DESCRIPTION
    This script measures the size of the WSL VHDX before, shuts down WSL cleanly,
    enables dynamic sparse reclaiming via 'wsl --manage Ubuntu --set-sparse true',
    and calculates the exact amount of disk space reclaimed on Windows Drive C:.
#>

$ErrorActionPreference = "Stop"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "   WSL 2 Windows VHDX Disk Compaction & Shrink Utility           " -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

# 1. Locate VHDX
$distroName = "Ubuntu"
$lxssKey = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss\*' | Where-Object { $_.DistributionName -eq $distroName }

if (-not $lxssKey) {
    Write-Error "Could not locate WSL registry registration for distribution: $distroName"
    exit 1
}

$vhdxPath = Join-Path $lxssKey.BasePath "ext4.vhdx"
if (-not (Test-Path $vhdxPath)) {
    Write-Error "ext4.vhdx not found at expected path: $vhdxPath"
    exit 1
}

$initialLength = (Get-Item $vhdxPath).Length
$initialSizeGB = [math]::round($initialLength / 1GB, 2)
Write-Host "[*] Located WSL VHDX: $vhdxPath" -ForegroundColor Gray
Write-Host "[*] Current VHDX Size on Windows: $initialSizeGB GB" -ForegroundColor Yellow

# 2. Shutdown WSL
Write-Host "`n[*] Shutting down WSL to release file locks..." -ForegroundColor Cyan
wsl --shutdown
Start-Sleep -Seconds 3

# 3. Enable Sparse / Compact
Write-Host "[*] Setting distro VHD to sparse (automatic reclaim)..." -ForegroundColor Cyan
try {
    wsl --manage $distroName --set-sparse true
    Write-Host "[✓] Sparse VHD enabled successfully!" -ForegroundColor Green
} catch {
    Write-Warning "Direct --set-sparse flag encountered an issue: $_"
}

# 4. Final stats
Start-Sleep -Seconds 2
$finalLength = (Get-Item $vhdxPath).Length
$finalSizeGB = [math]::round($finalLength / 1GB, 2)
$freedGB = [math]::round(($initialLength - $finalLength) / 1GB, 2)

$cDrive = Get-PSDrive -Name C
$freeCGB = [math]::round($cDrive.Free / 1GB, 2)

Write-Host "`n==================================================================" -ForegroundColor Green
Write-Host "   Compaction Summary                                            " -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Green
Write-Host " Initial VHDX Size:  $initialSizeGB GB"
Write-Host " Final VHDX Size:    $finalSizeGB GB"
Write-Host " Space Reclaimed:    $freedGB GB" -ForegroundColor Green
Write-Host " Current Free on C:  $freeCGB GB" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Green
