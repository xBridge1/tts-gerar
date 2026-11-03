param(
    [string]$Nome = "GeradorTTS"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Ambiente Python não encontrado. Execute setup.ps1 antes de gerar o executável."
}

$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($null -eq $ffmpeg) {
    throw "FFmpeg não foi encontrado. Execute setup.ps1 e abra um novo PowerShell."
}

$ffmpegFolder = Split-Path -Parent $ffmpeg.Source
$ffmpegFiles = Get-ChildItem -Path (Join-Path $ffmpegFolder "*") -File -Include "ffmpeg.exe", "*.dll"
$pyInstallerArgs = @("-m", "PyInstaller", "--noconfirm", "--windowed", "--onefile", "--name", $Nome)
foreach ($file in $ffmpegFiles) {
    $pyInstallerArgs += "--add-binary"
    $pyInstallerArgs += "$($file.FullName);."
}
$pyInstallerArgs += (Join-Path $projectRoot "app.py")
& $venvPython @pyInstallerArgs
if ($LASTEXITCODE -ne 0) {
    throw "Não foi possível criar o executável. Execute setup.ps1 para instalar as dependências e tente novamente."
}

Write-Host ""
Write-Host "Executável criado em: $(Join-Path $projectRoot ("dist\$Nome.exe"))"
