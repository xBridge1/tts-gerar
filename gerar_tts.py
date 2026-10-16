"""Converte texto em áudio WAV usando o Microsoft Edge TTS."""

import argparse
import asyncio
import shutil
import subprocess
import tempfile
from pathlib import Path

import edge_tts


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gera arquivos WAV a partir de texto usando o Edge TTS."
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
        help="Arquivo WAV de saída (padrão: audio.wav).",
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


async def gerar_audio(texto: str, args: argparse.Namespace) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError(
            "FFmpeg não foi encontrado no PATH. Execute setup.ps1 para instalar as dependências."
        )

    saida = args.saida.with_suffix(".wav")
    saida.parent.mkdir(parents=True, exist_ok=True)

    comunicacao = edge_tts.Communicate(
        text=texto,
        voice=args.voz,
        rate=args.velocidade,
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
                "-ac",
                "1",
                "-ar",
                "8000",
                "-sample_fmt",
                "s16",
                str(saida),
            ],
            check=True,
        )
    finally:
        mp3.unlink(missing_ok=True)

    print(f"Áudio gerado: {saida.resolve()}")


async def main() -> None:
    parser = criar_parser()
    args = parser.parse_args()

    if args.listar_vozes:
        await listar_vozes()
        return

    try:
        texto = obter_texto(args)
        if not texto.strip():
            raise ValueError("O texto informado está vazio.")
        await gerar_audio(texto, args)
    except (FileNotFoundError, RuntimeError, ValueError) as erro:
        parser.error(str(erro))


if __name__ == "__main__":
    asyncio.run(main())
