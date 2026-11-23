$ErrorActionPreference = 'Stop'
$msysBash = 'C:\msys64\usr\bin\bash.exe'
if (-not (Test-Path $msysBash)) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw 'MSYS2 is missing and winget is unavailable. Install MSYS2 from https://www.msys2.org/ then run this script again.'
    }
    Write-Host 'Installing MSYS2…'
    winget install --id MSYS2.MSYS2 --exact --silent --accept-package-agreements --accept-source-agreements
}
if (-not (Test-Path $msysBash)) {
    throw 'MSYS2 was not found at C:\msys64. Install it to the default location and retry.'
}
$scriptPath = (Join-Path $PSScriptRoot 'build-vickey.sh') -replace '\\','/'
if ($scriptPath -match '^([A-Za-z]):/(.*)$') {
    $scriptPath = '/' + $Matches[1].ToLower() + '/' + $Matches[2]
}
Write-Host 'Building ViceKey from the pinned Chiaki-ng source. The first build downloads the toolchain and can take a while.'
$env:MSYSTEM = 'MINGW64'
$env:CHERE_INVOKING = '1'
$command = "bash '$scriptPath'"
& $msysBash -lc $command
if ($LASTEXITCODE -ne 0) {
    throw "ViceKey build failed with exit code $LASTEXITCODE. Read the error above and send it back for fixing."
}
Write-Host "`nViceKey is ready: $(Join-Path $PSScriptRoot 'out\ViceKey-Windows.zip')" -ForegroundColor Green
