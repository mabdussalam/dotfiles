<#
.SYNOPSIS
Installs VS Code extensions from a list.

.DESCRIPTION
Reads extensions.txt and installs each extension using the specified editor executable.

.PARAMETER Editor
The editor executable to use (code or antigravity). Default is code.

.EXAMPLE
.\install-extensions.ps1
Installs using 'code'.

.EXAMPLE
.\install-extensions.ps1 -Editor antigravity
Installs using 'antigravity'.
#>
param (
    [ValidateSet("code", "antigravity")]
    [string]$Editor = "code"
)

# Reads extensions.txt and installs each one
$extFile = Join-Path $PSScriptRoot "..\extensions.txt"
if (Test-Path $extFile) {
    Get-Content $extFile | ForEach-Object {
        if (![string]::IsNullOrWhiteSpace($_)) {
            Write-Host "Installing $_ with $Editor..."
            & $Editor --install-extension $_
        }
    }
    Write-Host "All extensions processed!"
} else {
    Write-Host "extensions.txt not found!"
}
