# save-ftp-creds.ps1
# Run ONCE, yourself, in a normal PowerShell window. Prompts for the NFO FTP login and saves it
# encrypted for your Windows account only (DPAPI), outside Dropbox and the repo.
# Never paste this password into a chat.
$dir = Join-Path $env:USERPROFILE 'weight-tracker-secrets'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$cred = Get-Credential -UserName 'titan7' -Message 'NFO FTP login for hosted10.nfoservers.com'
if (-not $cred) { throw 'Cancelled' }
$cred | Export-Clixml -Path (Join-Path $dir 'nfo-ftp-creds.xml')
Write-Host "Saved to $dir\nfo-ftp-creds.xml (readable only by your Windows account on this PC)"
