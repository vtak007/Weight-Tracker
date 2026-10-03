# nfo-ftp.ps1
# Shared helper (dot-source it) for the Weight Tracker NFO uploads.
# Opens an explicit-FTPS session to the NFO web host, pinned to the host's self-signed certificate,
# using the WinSCP .NET assembly and a DPAPI-encrypted credential file (created once by save-ftp-creds.ps1).

$NfoHost        = 'hosted10.nfoservers.com'
# SHA-256 fingerprint of the host's FTP TLS certificate (self-signed, expires 2028-11-05).
# If NFO rotates the certificate, uploads fail with a certificate error: update this value.
$NfoFingerprint = '18:2D:FF:A7:2B:45:67:54:26:F4:1E:76:BB:5F:9D:9B:80:5A:EE:9A:87:3E:4F:A3:A0:F6:27:97:BE:74:D1:1C'
$NfoCredFile    = Join-Path $env:USERPROFILE 'weight-tracker-secrets\nfo-ftp-creds.xml'
$WinScpDir      = 'C:\Program Files (x86)\WinSCP'

function New-NfoSession {
    if (-not (Test-Path $NfoCredFile)) {
        throw "Missing $NfoCredFile - run deploy\save-ftp-creds.ps1 once to create it"
    }
    $cred = Import-Clixml -Path $NfoCredFile
    Add-Type -Path (Join-Path $WinScpDir 'WinSCPnet.dll')

    $opt = New-Object WinSCP.SessionOptions
    $opt.Protocol       = [WinSCP.Protocol]::Ftp
    $opt.FtpSecure      = [WinSCP.FtpSecure]::Explicit
    $opt.HostName       = $NfoHost
    $opt.UserName       = $cred.UserName
    $opt.SecurePassword = $cred.Password
    $opt.TlsHostCertificateFingerprint = $NfoFingerprint

    $session = New-Object WinSCP.Session
    try { $session.Open($opt) } catch { $session.Dispose(); throw }
    return $session
}

function New-BinaryTransferOptions {
    $o = New-Object WinSCP.TransferOptions
    $o.TransferMode = [WinSCP.TransferMode]::Binary
    return $o
}
