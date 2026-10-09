param([string]$Destination = $PSScriptRoot)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Add-Type -AssemblyName System.IO.Compression.FileSystem
$installRoot = [IO.Path]::GetFullPath($Destination)
New-Item -ItemType Directory -Force -Path $installRoot | Out-Null
$downloadRoot = Join-Path $installRoot '.downloads'
$receiptRoot = Join-Path $installRoot '.installed-parts'
New-Item -ItemType Directory -Force -Path $downloadRoot,$receiptRoot | Out-Null
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'download-manifest.json') -Raw | ConvertFrom-Json
$inventory = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'file-inventory.json') -Raw | ConvertFrom-Json
$installPrefix = $installRoot.TrimEnd('\') + '\'
$remaining = ($inventory.files | Where-Object { -not (Test-Path -LiteralPath (Join-Path $installRoot $_.path)) } | Measure-Object bytes -Sum).Sum
$drive = [IO.DriveInfo]::new([IO.Path]::GetPathRoot($installRoot))
if ($drive.AvailableFreeSpace -lt ($remaining + 2GB)) { throw 'Not enough free space. Use a drive with at least 25 GB available for a new installation.' }
Write-Host 'Downloading the complete local browser game. All archives are required.'
Write-Host ('Destination: ' + $installRoot)
foreach ($part in $manifest.parts) {
    $receipt = Join-Path $receiptRoot ($part.name + '.sha256')
    $entries = @($inventory.files | Where-Object part -eq $part.name)
    $entryMap = @{}
    foreach ($record in $entries) { $entryMap[$record.path] = $record }
    $complete = (Test-Path -LiteralPath $receipt) -and ((Get-Content -LiteralPath $receipt -Raw).Trim() -eq $part.sha256)
    if ($complete) {
        foreach ($entry in $entries) {
            $installed = Join-Path $installRoot $entry.path
            if (-not (Test-Path -LiteralPath $installed) -or (Get-Item -LiteralPath $installed).Length -ne $entry.bytes) { $complete=$false; break }
        }
    }
    if ($complete) { Write-Host ('Already installed: ' + $part.name); continue }
    $archive = Join-Path $downloadRoot $part.name
    $partial = $archive + '.partial'
    if (-not (Test-Path -LiteralPath $archive)) {
        Write-Host ('Downloading ' + $part.name)
        & curl.exe --fail --location --retry 4 --continue-at - --output $partial $part.url
        if ($LASTEXITCODE -ne 0) { throw ('Download failed: ' + $part.name + '. Run this script again to resume.') }
        if ((Get-FileHash -LiteralPath $partial -Algorithm SHA256).Hash.ToLowerInvariant() -ne $part.sha256) { throw ('Checksum mismatch: ' + $partial + '. Delete only this incomplete download and retry.') }
        Move-Item -LiteralPath $partial -Destination $archive
    }
    if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $part.sha256) { throw ('Checksum mismatch: ' + $archive) }
    Write-Host ('Extracting ' + $part.name)
    $zip = [IO.Compression.ZipFile]::OpenRead($archive)
    try {
        foreach ($entry in $zip.Entries) {
            $target = [IO.Path]::GetFullPath((Join-Path $installRoot $entry.FullName))
            if (-not $target.StartsWith($installPrefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe archive path rejected.' }
            $record = $entryMap[$entry.FullName]
            if (-not $record) { throw ('Unlisted archive entry: ' + $entry.FullName) }
            if (Test-Path -LiteralPath $target) {
                if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -eq $record.sha256) { continue }
                throw ('Existing file differs; nothing was overwritten: ' + $target + '. Choose a new empty destination.')
            }
            New-Item -ItemType Directory -Force -Path ([IO.Path]::GetDirectoryName($target)) | Out-Null
            $temporary = $target + '.installing'
            $inputStream = $entry.Open()
            $outputStream = [IO.File]::Create($temporary)
            try { $inputStream.CopyTo($outputStream) } finally { $inputStream.Dispose(); $outputStream.Dispose() }
            if ((Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash.ToLowerInvariant() -ne $record.sha256) { throw ('Extraction verification failed: ' + $target) }
            Move-Item -LiteralPath $temporary -Destination $target
        }
    } finally { $zip.Dispose() }
    [IO.File]::WriteAllText($receipt,$part.sha256)
    # Only the exact verified installer cache file is removed; installed game files remain.
    Remove-Item -LiteralPath $archive
}
$sourceInventory = Join-Path $PSScriptRoot 'file-inventory.json'
$targetInventory = Join-Path $installRoot 'file-inventory.json'
if ([IO.Path]::GetFullPath($sourceInventory) -ne [IO.Path]::GetFullPath($targetInventory)) {
    if (Test-Path -LiteralPath $targetInventory) {
        if ((Get-FileHash -LiteralPath $sourceInventory).Hash -ne (Get-FileHash -LiteralPath $targetInventory).Hash) { throw 'Existing file-inventory.json differs; no file was overwritten.' }
    } else { Copy-Item -LiteralPath $sourceInventory -Destination $targetInventory }
}
Write-Host 'Download complete. Double-click Launch-Local.cmd to play.' -ForegroundColor Green
