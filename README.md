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

## Executável do Windows

Com o FFmpeg instalado e disponível no PATH, execute:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

O arquivo `dist\GeradorTTS.exe` será criado com o FFmpeg incluído, portanto não exige uma instalação separada do FFmpeg no computador de destino. O aplicativo ainda precisa de conexão com a internet para usar as vozes neurais do Edge.

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
