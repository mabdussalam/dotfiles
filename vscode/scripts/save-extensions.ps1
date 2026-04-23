<#
.SYNOPSIS
Saves currently installed VS Code extensions to a list.

.DESCRIPTION
Saves the list of currently installed extensions alphabetically and with UTF-8 encoding. By default, merges with the existing extensions.txt.

.PARAMETER Editor
The editor executable to use (code or antigravity). Default is code.

.PARAMETER Overwrite
If specified, overwrites extensions.txt instead of merging.

.EXAMPLE
.\save-extensions.ps1
Merges current extensions using 'code'.

.EXAMPLE
.\save-extensions.ps1 -Editor antigravity -Overwrite
Overwrites extensions.txt using 'antigravity'.
#>
param (
    [ValidateSet("code", "antigravity")]
    [string]$Editor = "code",
    [switch]$Overwrite
)

# Saves the list of currently installed extensions alphabetically and with UTF-8 encoding
$extFile = Join-Path $PSScriptRoot "..\extensions.txt"

$currentExts = & $Editor --list-extensions

if (-not $Overwrite -and (Test-Path $extFile)) {
    $existingExts = Get-Content $extFile
    $allExts = $existingExts + $currentExts | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique | Sort-Object
} else {
    $allExts = $currentExts | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Sort-Object
}

$allExts | Out-File -FilePath $extFile -Encoding utf8
Write-Host "Extensions successfully saved to extensions.txt!"
