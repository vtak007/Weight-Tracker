# save-ftp-creds.ps1
# Run ONCE, yourself, in a normal PowerShell window (not inside Claude Code).
# Prompts for the NFO FTP password (hidden) and saves the login encrypted for your Windows account
# only (DPAPI), outside Dropbox and the repo. Never paste this password into a chat.
$dir = Join-Path $env:USERPROFILE 'weight-tracker-secrets'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$user = 'titan7'
$pw = Read-Host -AsSecureString -Prompt "NFO FTP password for $user@hosted10.nfoservers.com (typing is hidden)"
if ($pw.Length -eq 0) { throw 'No password entered' }
$cred = New-Object System.Management.Automation.PSCredential($user, $pw)
$cred | Export-Clixml -Path (Join-Path $dir 'nfo-ftp-creds.xml')
Write-Host "Saved to $dir\nfo-ftp-creds.xml (readable only by your Windows account on this PC)"
