$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$releaseVersion = & $pythonPath -c "from wordsense import __version__; print(__version__)"
if ($LASTEXITCODE -ne 0) { throw 'Cannot read release version.' }
& $pythonPath -m tools.make_icon
if ($LASTEXITCODE -ne 0) { throw 'Icon conversion failed.' }
& $pythonPath -m tools.prepare_distribution
if ($LASTEXITCODE -ne 0) { throw 'License preparation failed.' }
& $pythonPath -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
& $pythonPath -m PyInstaller --noconfirm packaging\WordSense.spec
if ($LASTEXITCODE -ne 0) { throw 'Build failed.' }
$releaseDirectory = Join-Path $projectRoot ("dist\WordSense-v" + $releaseVersion)
Copy-Item -LiteralPath (Join-Path $projectRoot 'packaging\使用说明.txt') -Destination $releaseDirectory
Copy-Item -LiteralPath (Join-Path $projectRoot 'packaging\THIRD_PARTY_NOTICES.txt') -Destination $releaseDirectory
Copy-Item -LiteralPath (Join-Path $projectRoot 'LICENSE') -Destination $releaseDirectory
Copy-Item -LiteralPath (Join-Path $projectRoot 'packaging\licenses') -Destination $releaseDirectory -Recurse
$reportPath = Join-Path $projectRoot 'docs\packaged-smoke.json'
$smokeProcess = Start-Process -FilePath (Join-Path $releaseDirectory 'WordSense.exe') -ArgumentList @('--smoke-test', ('"' + $reportPath + '"')) -PassThru -WindowStyle Hidden
if (-not $smokeProcess.WaitForExit(60000)) { $smokeProcess.Kill(); throw 'Packaged smoke test timed out.' }
if ($smokeProcess.ExitCode -ne 0) { throw 'Packaged smoke test failed.' }
$report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
if ($report.status -ne 'passed' -or -not $report.frozen) { throw 'Invalid packaged smoke result.' }
$archivePath = Join-Path $projectRoot ("dist\WordSense-v" + $releaseVersion + '-Windows-x64.zip')
Compress-Archive -LiteralPath $releaseDirectory -DestinationPath $archivePath -Force
$archiveHash = Get-FileHash -LiteralPath $archivePath -Algorithm SHA256
($archiveHash.Hash.ToLower() + '  ' + (Split-Path -Leaf $archivePath)) | Set-Content -LiteralPath ($archivePath + '.sha256') -Encoding utf8
$archiveHash | Format-List
# Keep the intermediate EXE from being mistaken for the runnable release.
$intermediateExe = Join-Path $projectRoot 'build\WordSense\WordSense.exe'
if (Test-Path -LiteralPath $intermediateExe) {
    Move-Item -LiteralPath $intermediateExe -Destination ($intermediateExe + '.build-artifact') -Force
}
