# save-ftp-creds.ps1
# Run ONCE, yourself, in a normal PowerShell window (not inside Claude Code).
# Prompts for the NFO FTP password and saves the login encrypted for your Windows account only
# (DPAPI), outside Dropbox and the repo. Never paste this password into a chat.
#
#   -ShowTyping   show what you type/paste (use if a hidden paste gives the wrong length)
param([switch]$ShowTyping)

$dir = Join-Path $env:USERPROFILE 'weight-tracker-secrets'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$user = 'titan7'

if ($ShowTyping) {
    $plain = Read-Host -Prompt "NFO FTP password for $user@hosted10.nfoservers.com (VISIBLE)"
    $plain = $plain.Trim()
    $pw = ConvertTo-SecureString -String $plain -AsPlainText -Force
    $plain = $null
} else {
    $pw = Read-Host -AsSecureString -Prompt "NFO FTP password for $user@hosted10.nfoservers.com (typing is hidden)"
}
if ($pw.Length -eq 0) { throw 'No password entered' }

$cred = New-Object System.Management.Automation.PSCredential($user, $pw)
$cred | Export-Clixml -Path (Join-Path $dir 'nfo-ftp-creds.xml')
Write-Host "Saved to $dir\nfo-ftp-creds.xml (readable only by your Windows account on this PC)"
Write-Host "Password length saved: $($pw.Length) characters (your FTP password should be 10)"
