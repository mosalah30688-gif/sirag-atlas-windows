# ==============================================================================
# Build Both Official Windows Editions (Pure Native Qt 6 GUI — Zero Browser!):
# 1) dist\Sirag-Atlas-Seerah-Portable-x64.exe      (Single-file Portable .exe)
# 2) dist\Sirag-Atlas-Seerah-Win11-Store-x64.msix  (Windows 11 Store MSIX Package)
# ==============================================================================
$ErrorActionPreference = "Stop"

Write-Host "=== [1/4] Building Standalone Single-File Portable .EXE ===" -ForegroundColor Cyan
pyinstaller `
  --noconfirm `
  --clean `
  --windowed `
  --onefile `
  --name "Sirag-Atlas-Seerah-Portable-x64" `
  --icon "windows\sirag-atlas.ico" `
  --version-file "windows\version_info.txt" `
  --add-data "assets;assets" `
  --add-data "windows\sirag-atlas.ico;windows" `
  --add-data "version.json;." `
  --collect-submodules PySide6.QtMultimedia `
  main.py

Write-Host "=== [2/4] Running End-to-End Native GUI Smoke Test on Portable .EXE ===" -ForegroundColor Cyan
$proc = Start-Process -FilePath "dist\Sirag-Atlas-Seerah-Portable-x64.exe" -ArgumentList "--self-test" -Wait -PassThru
if ($proc.ExitCode -ne 0) {
    throw "Self-test failed with exit code $($proc.ExitCode)"
}
Write-Host "Portable .EXE passed native Qt6 GUI smoke test!" -ForegroundColor Green

Write-Host "=== [3/4] Building Fast-Launch App Bundle for Windows 11 Store MSIX ===" -ForegroundColor Cyan
pyinstaller `
  --noconfirm `
  --clean `
  --windowed `
  --onedir `
  --name "SiragAtlasSeerah" `
  --icon "windows\sirag-atlas.ico" `
  --version-file "windows\version_info.txt" `
  --add-data "assets;assets" `
  --add-data "windows\sirag-atlas.ico;windows" `
  --add-data "version.json;." `
  --collect-submodules PySide6.QtMultimedia `
  main.py

$msixStage = "build\msix_stage"
if (Test-Path $msixStage) { Remove-Item -Recurse -Force $msixStage }
New-Item -ItemType Directory -Force -Path "$msixStage\Assets" | Out-Null

Copy-Item -Path "dist\SiragAtlasSeerah\*" -Destination $msixStage -Recurse -Force
Copy-Item -Path "windows\AppxManifest.xml" -Destination "$msixStage\AppxManifest.xml" -Force
Copy-Item -Path "windows\msix_assets\*.png" -Destination "$msixStage\Assets\" -Force

Write-Host "=== [4/4] Packaging & Signing Windows 11 Store MSIX via Windows SDK ===" -ForegroundColor Cyan
$sdkBin = Get-ChildItem "C:\Program Files (x86)\Windows Kits\10\bin\10.*\x64\makeappx.exe" |
          Sort-Object FullName -Descending |
          Select-Object -First 1

if (-not $sdkBin) {
    throw "Windows 10/11 SDK makeappx.exe not found!"
}
$makeappx = $sdkBin.FullName
$signtool = Join-Path $sdkBin.DirectoryName "signtool.exe"

$msixOut = "dist\Sirag-Atlas-Seerah-Win11-Store-x64.msix"
if (Test-Path $msixOut) { Remove-Item -Force $msixOut }

& $makeappx pack /d $msixStage /p $msixOut /o
if ($LASTEXITCODE -ne 0) { throw "makeappx failed!" }

# Create SHA-256 Code Signing Certificate matching AppxManifest Publisher for instant Win11 sideloading
$cert = New-SelfSignedCertificate `
  -Type Custom `
  -Subject "CN=Mohamed Salah Abdelkhalek" `
  -KeyUsage DigitalSignature `
  -FriendlyName "Sirag Atlas Seerah Win11 Package Certificate" `
  -CertStoreLocation "Cert:\CurrentUser\My" `
  -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")

$pfxPass = ConvertTo-SecureString -String "SiragAtlas2026" -Force -AsPlainText
$pfxPath = "build\sirag-win11.pfx"
$cerPath = "dist\Sirag-Atlas-Win11-Store.cer"

Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $pfxPass | Out-Null
Export-Certificate -Cert $cert -FilePath $cerPath | Out-Null

& $signtool sign /fd SHA256 /a /f $pfxPath /p "SiragAtlas2026" $msixOut
if ($LASTEXITCODE -ne 0) { throw "signtool failed!" }

Remove-Item -Force $pfxPath -ErrorAction SilentlyContinue

Get-ChildItem "dist\Sirag-Atlas-Seerah-*" | Format-Table Name, @{Name="Size(MB)";Expression={[math]::Round($_.Length / 1MB, 2)}}
Write-Host "ALL WINDOWS 11 ARTIFACTS BUILT & VERIFIED SUCCESSFULLY!" -ForegroundColor Green
