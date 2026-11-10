# Gerador de TTS

Ferramenta simples para converter texto em áudio WAV usando as vozes neurais do Microsoft Edge TTS.

## Instalação no Windows

Abra o PowerShell na pasta do projeto e execute:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

O instalador cria o ambiente virtual `.venv`, instala o pacote `edge-tts` e instala o FFmpeg pelo `winget` quando ele ainda não estiver disponível.

## Gerar um áudio

```powershell
.\.venv\Scripts\python.exe .\gerar_tts.py `
  --texto "Olá! Este é um teste de voz." `
  --saida .\audios\teste.wav
```

Também é possível ler o texto de um arquivo UTF-8:

```powershell
.\.venv\Scripts\python.exe .\gerar_tts.py `
  --arquivo .\texto.txt `
  --voz pt-BR-FranciscaNeural `
  --velocidade +0% `
  --saida .\audios\narracao.wav
```

O áudio é salvo em WAV mono, 8 kHz, 16-bit, adequado para fluxos de voz que exigem esse formato.

## Interface gráfica

Depois da instalação, abra a interface com:

```powershell
.\.venv\Scripts\python.exe .\app.py
```

Ela permite escrever o texto, escolher uma voz, ajustar a velocidade e definir o arquivo WAV de destino.

## Instalador do Windows

A forma mais simples de usar é baixar o `GeradorTTS-Setup-x.y.z.exe` na página de [Releases](https://github.com/xBridge1/tts-gerar/releases) e executá-lo. O instalador não exige administrador, cria atalho no Menu Iniciar (e, opcionalmente, na Área de Trabalho) e já inclui o FFmpeg. Os áudios são salvos por padrão em `Documentos\Gerador TTS`. O aplicativo precisa de conexão com a internet para usar as vozes neurais do Edge.

### Gerar o instalador

Requer o FFmpeg no PATH (instalado pelo `setup.ps1`) e o [Inno Setup 6](https://jrsoftware.org/isinfo.php):

```powershell
winget install --id JRSoftware.InnoSetup --exact
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Versao 1.0.0
```

O instalador será criado em `dist\GeradorTTS-Setup-1.0.0.exe`. Para gerar apenas um `.exe` portátil, sem instalador, use `.\build.ps1 -Portatil` (resultado em `dist\GeradorTTS.exe`).

O ícone do aplicativo fica em `iconpp.ico`.

## Escolher uma voz

Para consultar as vozes disponíveis:

```powershell
.\.venv\Scripts\python.exe .\gerar_tts.py --listar-vozes
```

Algumas vozes em português incluem `pt-BR-FranciscaNeural`, `pt-BR-AntonioNeural` e `pt-PT-RaquelNeural`.

## Desenvolvimento

Para instalar as dependências manualmente:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

O FFmpeg precisa estar instalado e disponível no `PATH` para converter o MP3 temporário em WAV.
