# deploy-web.ps1
# Uploads the phone site (PHP files + app.html) to NFO /public/FMJfiles/weight/ over explicit FTPS.
# Refuses to deploy anything that is not committed (deploy-discipline).
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\nfo-ftp.ps1"

$repo = Split-Path $PSScriptRoot -Parent
Push-Location $repo
try {
    $dirty = git status --porcelain -- server weight-tracker.html
    if ($dirty) { throw "Uncommitted changes in deployable files:`n$dirty`nCommit first, then deploy." }
    $sha = git rev-parse --short HEAD
} finally { Pop-Location }

$remote = '/public/FMJfiles/weight'
$files = @(
    @('server\index.php',    'index.php'),
    @('server\data.php',     'data.php'),
    @('server\lib.php',      'lib.php'),
    @('server\.htaccess',    '.htaccess'),
    @('server\robots.txt',   'robots.txt'),
    @('weight-tracker.html', 'app.html')
)

$session = New-NfoSession
try {
    $opts = New-BinaryTransferOptions
    if (-not $session.FileExists($remote)) { $session.CreateDirectory($remote) }
    foreach ($f in $files) {
        $session.PutFiles((Join-Path $repo $f[0]), "$remote/$($f[1])", $false, $opts).Check()
        Write-Host ("uploaded {0} -> {1}/{2}" -f $f[0], $remote, $f[1])
    }
} finally { $session.Dispose() }
Write-Host "Deployed commit $sha to $remote"
