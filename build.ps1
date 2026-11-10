param(
    [string]$Nome = "GeradorTTS",
    [string]$Versao = "1.0.0",
    # Gera apenas um .exe único e portátil, sem instalador.
    [switch]$Portatil
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Ambiente Python não encontrado. Execute setup.ps1 antes de gerar o executável."
}

$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($null -eq $ffmpeg) {
    throw "FFmpeg não foi encontrado. Execute setup.ps1 e abra um novo PowerShell."
}

$icone = Join-Path $projectRoot "icon\app.ico"
if (-not (Test-Path $icone)) {
    throw "Ícone não encontrado em $icone."
}

$modo = if ($Portatil) { "--onefile" } else { "--onedir" }
$ffmpegFolder = Split-Path -Parent $ffmpeg.Source
$ffmpegFiles = Get-ChildItem -Path (Join-Path $ffmpegFolder "*") -File -Include "ffmpeg.exe", "*.dll"
$pyInstallerArgs = @(
    "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed", $modo,
    "--name", $Nome,
    "--icon", $icone,
    "--add-data", "$icone;icon"
)
foreach ($file in $ffmpegFiles) {
    $pyInstallerArgs += "--add-binary"
    $pyInstallerArgs += "$($file.FullName);."
}
$pyInstallerArgs += (Join-Path $projectRoot "app.py")
& $venvPython @pyInstallerArgs
if ($LASTEXITCODE -ne 0) {
    throw "Não foi possível criar o executável. Execute setup.ps1 para instalar as dependências e tente novamente."
}

if ($Portatil) {
    Write-Host ""
    Write-Host "Executável portátil criado em: $(Join-Path $projectRoot "dist\$Nome.exe")"
    return
}

$iscc = @(
    (Get-Command iscc -ErrorAction SilentlyContinue).Source,
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

if ($null -eq $iscc) {
    throw "Inno Setup não encontrado. Instale com: winget install --id JRSoftware.InnoSetup --exact"
}

& $iscc "/DAppVersion=$Versao" (Join-Path $projectRoot "installer.iss")
if ($LASTEXITCODE -ne 0) {
    throw "Não foi possível criar o instalador."
}

Write-Host ""
Write-Host "Instalador criado em: $(Join-Path $projectRoot "dist\$Nome-Setup-$Versao.exe")"
