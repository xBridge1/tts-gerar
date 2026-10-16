$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $projectRoot ".venv"
$tempPath = Join-Path $projectRoot ".tmp"
$python = Get-Command py -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Force -Path $tempPath | Out-Null
$env:TEMP = $tempPath
$env:TMP = $tempPath

if ($null -eq $python) {
    throw "Python não foi encontrado. Instale Python 3.10 ou mais recente e tente novamente."
}

if (-not (Test-Path (Join-Path $venvPath "Scripts\python.exe"))) {
    Write-Host "Criando ambiente virtual em $venvPath..."
    & $python.Source -3 -m venv $venvPath
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path (Join-Path $venvPath "Lib\site-packages\pip"))) {
    Write-Host "Instalando o pip no ambiente virtual..."
    & $venvPython -m ensurepip --upgrade --default-pip
}

Write-Host "Instalando dependências Python..."
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $projectRoot "requirements.txt")

if ($null -eq (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($null -eq $winget) {
        throw "FFmpeg não foi encontrado e o winget também não está disponível. Instale o FFmpeg e adicione-o ao PATH."
    }

    Write-Host "FFmpeg não encontrado. Instalando com winget..."
    & $winget.Source install --id Gyan.FFmpeg.Shared --exact --source winget --accept-source-agreements --accept-package-agreements
    if ($LASTEXITCODE -ne 0) {
        throw "Não foi possível instalar o FFmpeg pelo winget."
    }
}

Write-Host ""
Write-Host "Configuração concluída. Para gerar um áudio:"
Write-Host "  .\.venv\Scripts\python.exe .\gerar_tts.py --texto 'Olá, este é um teste.' --saida .\audios\teste.wav"
Write-Host ""
Write-Host "Se o FFmpeg foi instalado agora, abra um novo terminal antes de executar o comando."
