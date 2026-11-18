"""Converte texto em áudio (WAV, MP3, OGG, FLAC...) usando o Microsoft Edge TTS."""

import argparse
import asyncio
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import edge_tts


# chave -> (rótulo, extensão, argumentos do FFmpeg para a conversão)
FORMATOS: dict[str, tuple[str, str, list[str]]] = {
    "wav-telefonia": ("WAV · telefonia (8 kHz, mono)", ".wav", ["-ac", "1", "-ar", "8000", "-sample_fmt", "s16"]),
    "wav": ("WAV · alta qualidade (24 kHz, mono)", ".wav", ["-ac", "1", "-ar", "24000", "-sample_fmt", "s16"]),
    "ulaw": ("WAV · G.711 µ-law (8 kHz)", ".wav", ["-ac", "1", "-ar", "8000", "-c:a", "pcm_mulaw"]),
    "mp3": ("MP3", ".mp3", ["-c:a", "copy"]),
    "ogg": ("OGG Vorbis", ".ogg", ["-c:a", "libvorbis", "-q:a", "5"]),
    "flac": ("FLAC (sem perdas)", ".flac", ["-c:a", "flac"]),
}
FORMATO_PADRAO = "wav-telefonia"


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gera arquivos de áudio a partir de texto usando o Edge TTS."
    )
    entrada = parser.add_mutually_exclusive_group()
    entrada.add_argument("--texto", help="Texto que será convertido em áudio.")
    entrada.add_argument(
        "--arquivo",
        type=Path,
        help="Arquivo UTF-8 com o texto que será convertido.",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path("audio.wav"),
        help="Arquivo de saída; a extensão é ajustada ao formato (padrão: audio.wav).",
    )
    parser.add_argument(
        "--formato",
        choices=list(FORMATOS),
        default=FORMATO_PADRAO,
        help=f"Formato do áudio (padrão: {FORMATO_PADRAO}).",
    )
    parser.add_argument(
        "--voz",
        default="pt-BR-FranciscaNeural",
        help="Voz utilizada (padrão: pt-BR-FranciscaNeural).",
    )
    parser.add_argument(
        "--velocidade",
        default="-5%",
        help="Velocidade da fala, por exemplo -10%%, +0%% ou +20%%.",
    )
    parser.add_argument(
        "--listar-vozes",
        action="store_true",
        help="Lista as vozes disponíveis e encerra.",
    )
    return parser


async def listar_vozes() -> None:
    vozes = await edge_tts.list_voices()
    for voz in sorted(vozes, key=lambda item: (item["Locale"], item["ShortName"])):
        print(f'{voz["ShortName"]}\t{voz["Gender"]}\t{voz["Locale"]}\t{voz["FriendlyName"]}')


def obter_texto(args: argparse.Namespace) -> str:
    if args.texto is not None:
        return args.texto
    if args.arquivo is not None:
        if not args.arquivo.is_file():
            raise FileNotFoundError(f"Arquivo não encontrado: {args.arquivo}")
        return args.arquivo.read_text(encoding="utf-8")
    raise ValueError("Informe --texto, --arquivo ou use --listar-vozes.")


async def gerar_audio(texto: str, args: argparse.Namespace) -> Path:
    return await gerar_audio_arquivo(texto, args.saida, args.voz, args.velocidade, args.formato)


def localizar_ffmpeg() -> str | None:
    """Encontra o FFmpeg no Windows ou dentro do executável empacotado."""
    if getattr(sys, "frozen", False):
        ffmpeg_embutido = Path(sys._MEIPASS) / "ffmpeg.exe"
        if ffmpeg_embutido.is_file():
            return str(ffmpeg_embutido)
    return shutil.which("ffmpeg")


async def gerar_audio_wav(
    texto: str,
    saida: Path,
    voz: str = "pt-BR-FranciscaNeural",
    velocidade: str = "-5%",
) -> Path:
    """Gera um WAV mono, 8 kHz e 16-bit e devolve o caminho criado."""
    return await gerar_audio_arquivo(texto, saida, voz, velocidade, "wav-telefonia")


async def gerar_audio_arquivo(
    texto: str,
    saida: Path,
    voz: str = "pt-BR-FranciscaNeural",
    velocidade: str = "-5%",
    formato: str = FORMATO_PADRAO,
) -> Path:
    """Gera o áudio no formato escolhido e devolve o caminho criado."""
    if formato not in FORMATOS:
        raise ValueError(f"Formato desconhecido: {formato}")
    _, extensao, argumentos = FORMATOS[formato]

    ffmpeg = localizar_ffmpeg()
    if ffmpeg is None:
        raise RuntimeError(
            "FFmpeg não foi encontrado. Execute setup.ps1 ou gere o executável com build.ps1."
        )

    if not texto.strip():
        raise ValueError("O texto informado está vazio.")

    saida = Path(saida).with_suffix(extensao)
    saida.parent.mkdir(parents=True, exist_ok=True)

    comunicacao = edge_tts.Communicate(
        text=texto,
        voice=voz,
        rate=velocidade,
    )

    arquivo_temporario = tempfile.NamedTemporaryFile(
        prefix="edge-tts-", suffix=".mp3", delete=False
    )
    mp3 = Path(arquivo_temporario.name)
    arquivo_temporario.close()

    try:
        await comunicacao.save(str(mp3))
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(mp3),
                *argumentos,
                str(saida),
            ],
            check=True,
            # Evita abrir uma janela de console no executável sem terminal.
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    finally:
        mp3.unlink(missing_ok=True)

    return saida.resolve()


async def main() -> None:
    parser = criar_parser()
    args = parser.parse_args()

    if args.listar_vozes:
        await listar_vozes()
        return

    try:
        texto = obter_texto(args)
        destino = await gerar_audio(texto, args)
        print(f"Áudio gerado: {destino}")
    except (FileNotFoundError, RuntimeError, ValueError) as erro:
        parser.error(str(erro))


if __name__ == "__main__":
    asyncio.run(main())
