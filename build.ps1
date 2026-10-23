$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host "Membersihkan hasil build sebelumnya..."
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

Write-Host "Menjalankan PyInstaller..."
py -m PyInstaller autoedit.spec --noconfirm --clean

$exe = Join-Path $root "dist\autoedit\autoedit.exe"
if (-not (Test-Path $exe)) {
    throw "Build gagal: $exe tidak ditemukan"
}

$size = [math]::Round((Get-ChildItem (Join-Path $root "dist\autoedit") -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB, 1)
Write-Host ""
Write-Host "Selesai: $exe"
Write-Host "Ukuran folder: $size MB"
