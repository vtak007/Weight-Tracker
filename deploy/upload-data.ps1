# upload-data.ps1
# Uploads the newest weight-tracker-data_YYYY.json to NFO /weight-private/ over explicit FTPS.
# Uploads to a .part name then renames, so the phone page never sees a half-written file.
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\nfo-ftp.ps1"

$logPath = 'C:\Users\Perdi\Documents\upload-weighttracker.log'
$dataDir = Split-Path $PSScriptRoot -Parent

function Write-Log([string]$m) {
    Add-Content -Path $logPath -Value ("{0} {1}" -f (Get-Date -Format 's'), $m)
}

$session = $null
try {
    $src = Get-ChildItem -Path $dataDir -File |
        Where-Object { $_.Name -match '^weight-tracker-data_\d{4}\.json$' } |
        Sort-Object Name -Descending | Select-Object -First 1
    if (-not $src) { throw "No weight-tracker-data_YYYY.json found in $dataDir" }
    try { Get-Content -LiteralPath $src.FullName -Raw | ConvertFrom-Json | Out-Null }
    catch { throw "$($src.Name) is not valid JSON; not uploading" }

    $session = New-NfoSession
    $remote  = "/weight-private/$($src.Name)"
    $opts    = New-BinaryTransferOptions

    $session.PutFiles($src.FullName, "$remote.part", $false, $opts).Check()
    try {
        $session.MoveFile("$remote.part", $remote)
    } catch {
        # Server refused to rename over an existing file: remove it, then move.
        if ($session.FileExists($remote)) { $session.RemoveFiles($remote).Check() }
        $session.MoveFile("$remote.part", $remote)
    }

    Write-Log ("OK uploaded {0} ({1} bytes) to {2}" -f $src.Name, $src.Length, $remote)
} catch {
    Write-Log ("ERROR {0}" -f $_)
    Write-Host "ERROR: $_"
    exit 1
} finally {
    if ($session) { $session.Dispose() }
}
