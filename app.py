"""Interface gráfica para o Gerador de TTS."""

import asyncio
import ctypes
import sys
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from gerar_tts import gerar_audio_wav


VOZES = {
    "Francisca (Brasil)": "pt-BR-FranciscaNeural",
    "Antonio (Brasil)": "pt-BR-AntonioNeural",
    "Thalita (Brasil)": "pt-BR-ThalitaMultilingualNeural",
    "Raquel (Portugal)": "pt-PT-RaquelNeural",
    "Duarte (Portugal)": "pt-PT-DuarteNeural",
}

FUNDO = "#2C353E"
FUNDO_HOVER = "#3A4650"
DESTAQUE = "#CDFF00"
DESTAQUE_HOVER = "#D6FF33"
TEXTO = "#FFFFFF"

PASTA_RECURSOS = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
ICONE = PASTA_RECURSOS / "icon" / "app.ico"


class GeradorTTSApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Gerador de TTS")
        if ICONE.is_file():
            self.iconbitmap(default=str(ICONE))
        self.geometry("760x440")
        self.configure(background=FUNDO)
        self.resizable(False, False)
        self.overrideredirect(True)
        self.after(10, self._centralizar_e_arredondar)

        self.voz = tk.StringVar(value="Francisca (Brasil)")
        self.velocidade = tk.StringVar(value="+0%")
        self.saida = tk.StringVar(value=self._saida_padrao())
        self._montar_tela()

    def _centralizar_e_arredondar(self) -> None:
        """Centraliza a janela e aplica cantos arredondados no Windows."""
        self.update_idletasks()
        largura, altura = self.winfo_width(), self.winfo_height()
        posicao_x = (self.winfo_screenwidth() - largura) // 2
        posicao_y = (self.winfo_screenheight() - altura) // 2
        self.geometry(f"{largura}x{altura}+{posicao_x}+{posicao_y}")

        if self.tk.call("tk", "windowingsystem") == "win32":
            regiao = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, largura + 1, altura + 1, 16, 16)
            ctypes.windll.user32.SetWindowRgn(self.winfo_id(), regiao, True)

    @staticmethod
    def _saida_padrao() -> str:
        nome = f"audio_{datetime.now():%Y%m%d_%H%M%S}.wav"
        # Instalado em Arquivos de Programas, a pasta atual não é gravável.
        base = Path.home() / "Documents" / "Gerador TTS" if getattr(sys, "frozen", False) else Path.cwd() / "audios"
        return str(base / nome)

    def _montar_tela(self) -> None:
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        self.option_add("*TCombobox*Listbox.background", FUNDO)
        self.option_add("*TCombobox*Listbox.foreground", TEXTO)
        self.option_add("*TCombobox*Listbox.selectBackground", DESTAQUE)
        self.option_add("*TCombobox*Listbox.selectForeground", FUNDO)
        self.option_add("*TCombobox*Listbox.highlightThickness", 0)
        estilo.configure("App.TFrame", background=FUNDO)
        estilo.configure("App.TLabel", background=FUNDO, foreground=TEXTO)
        estilo.configure("Title.TLabel", background=FUNDO, foreground=TEXTO)
        estilo.configure("Accent.TButton", background=FUNDO, foreground=DESTAQUE, font=("Segoe UI Emoji", 15, "bold"), padding=(5, 1), borderwidth=0, relief="flat")
        estilo.map("Accent.TButton", background=[("active", FUNDO_HOVER), ("!active", FUNDO)], foreground=[("active", DESTAQUE), ("!active", DESTAQUE)])
        estilo.configure("Icon.TButton", background=FUNDO, foreground=DESTAQUE, font=("Segoe UI Emoji", 15, "bold"), padding=(3, 1), borderwidth=0, relief="flat")
        estilo.map("Icon.TButton", background=[("active", FUNDO_HOVER), ("!active", FUNDO)], foreground=[("active", DESTAQUE), ("!active", DESTAQUE)])
        estilo.configure("Select.TCombobox", fieldbackground=FUNDO, background=FUNDO, foreground=TEXTO, arrowcolor=TEXTO, bordercolor=TEXTO, lightcolor=FUNDO, darkcolor=FUNDO)
        estilo.map("Select.TCombobox", fieldbackground=[("readonly", "active", FUNDO), ("readonly", "pressed", FUNDO), ("readonly", FUNDO)], background=[("readonly", "active", FUNDO), ("readonly", "pressed", FUNDO), ("readonly", FUNDO)], foreground=[("readonly", TEXTO)], arrowcolor=[("active", DESTAQUE), ("pressed", DESTAQUE), ("!active", TEXTO)], bordercolor=[("active", DESTAQUE), ("pressed", DESTAQUE), ("!active", TEXTO)], selectbackground=[("readonly", FUNDO)], selectforeground=[("readonly", TEXTO)])
        estilo.configure("TEntry", fieldbackground=FUNDO, foreground=TEXTO)

        barra = tk.Frame(self, background=FUNDO, height=44)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        barra.columnconfigure(1, weight=1)
        titulo = tk.Label(barra, text="Gerador de TTS", background=FUNDO, foreground=TEXTO, font=("Segoe UI", 11, "bold"), padx=16)
        titulo.grid(row=0, column=0, sticky="w")
        for item in (barra, titulo):
            item.bind("<ButtonPress-1>", self._iniciar_arrasto)
            item.bind("<B1-Motion>", self._arrastar_janela)
        botao_base = {
            "background": DESTAQUE,
            "foreground": FUNDO,
            "activebackground": DESTAQUE_HOVER,
            "activeforeground": FUNDO,
            "font": ("Segoe UI", 15, "bold"),
            "borderwidth": 0,
            "relief": "flat",
            "width": 4,
            "anchor": "center",
            "justify": "center",
            "padx": 0,
            "pady": 0,
            "takefocus": 0,
        }
        minimizar = tk.Button(barra, text="—", command=self.iconify, cursor="hand2", **botao_base)
        minimizar.configure(font=("Segoe UI", 12, "bold"))
        minimizar.grid(row=0, column=2, sticky="nsew")
        self._adicionar_hover(minimizar, DESTAQUE, DESTAQUE_HOVER)
        fechar = tk.Button(barra, text="×", command=self.destroy, cursor="hand2", **botao_base)
        fechar.grid(row=0, column=3, sticky="nsew")
        self._adicionar_hover(fechar, DESTAQUE, DESTAQUE_HOVER)

        conteudo = ttk.Frame(self, padding=18, style="App.TFrame")
        conteudo.grid(row=1, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        conteudo.columnconfigure(0, weight=1)
        conteudo.rowconfigure(1, weight=1)

        ttk.Label(conteudo, text="Escreva o texto, escolha a voz e salve em WAV.", style="App.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 12)
        )

        self.texto = tk.Text(
            conteudo, wrap="word", font=("Segoe UI", 11), height=8,
            background=FUNDO, foreground=TEXTO, insertbackground=TEXTO,
            relief="solid", borderwidth=1, highlightthickness=1, highlightbackground=TEXTO,
            padx=10, pady=8,
        )
        self.texto.grid(row=1, column=0, sticky="nsew")
        self.texto.insert("1.0", "Digite ou cole o texto que será narrado aqui.")

        opcoes = ttk.Frame(conteudo, style="App.TFrame")
        opcoes.grid(row=2, column=0, sticky="ew", pady=(14, 8))
        opcoes.columnconfigure(1, weight=1)
        opcoes.columnconfigure(3, weight=1)
        ttk.Label(opcoes, text="Voz:", style="App.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Combobox(opcoes, textvariable=self.voz, values=list(VOZES), state="readonly", style="Select.TCombobox").grid(
            row=0, column=1, sticky="ew", padx=(6, 18)
        )
        ttk.Label(opcoes, text="Velocidade:", style="App.TLabel").grid(row=0, column=2, sticky="w")
        ttk.Combobox(opcoes, textvariable=self.velocidade, values=["-25%", "-15%", "-5%", "+0%", "+10%", "+20%"], width=8, style="Select.TCombobox").grid(
            row=0, column=3, sticky="w", padx=(6, 0)
        )

        destino = ttk.Frame(conteudo, style="App.TFrame")
        destino.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        destino.columnconfigure(0, weight=1)
        ttk.Label(destino, text="Salvar como:", style="App.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(destino, textvariable=self.saida).grid(row=1, column=0, sticky="ew", pady=(3, 0))
        ttk.Button(destino, text="📁", style="Icon.TButton", command=self.escolher_saida).grid(row=1, column=1, padx=(8, 0), pady=(3, 0))

        rodape = ttk.Frame(conteudo, style="App.TFrame")
        rodape.grid(row=4, column=0, sticky="ew")
        rodape.columnconfigure(0, weight=1)
        self.botao = ttk.Button(rodape, text="▶", style="Accent.TButton", command=self.gerar)
        self.botao.grid(row=0, column=0, pady=(2, 0))

    def _iniciar_arrasto(self, evento: tk.Event) -> None:
        self._arrasto_x = evento.x_root
        self._arrasto_y = evento.y_root

    @staticmethod
    def _adicionar_hover(botao: tk.Button, cor_normal: str, cor_hover: str) -> None:
        botao.bind("<Enter>", lambda _evento: botao.configure(background=cor_hover))
        botao.bind("<Leave>", lambda _evento: botao.configure(background=cor_normal))

    def _arrastar_janela(self, evento: tk.Event) -> None:
        deslocamento_x = evento.x_root - self._arrasto_x
        deslocamento_y = evento.y_root - self._arrasto_y
        self.geometry(f"+{self.winfo_x() + deslocamento_x}+{self.winfo_y() + deslocamento_y}")
        self._arrasto_x = evento.x_root
        self._arrasto_y = evento.y_root

    def escolher_saida(self) -> None:
        arquivo = filedialog.asksaveasfilename(
            title="Salvar áudio", defaultextension=".wav", filetypes=[("Áudio WAV", "*.wav")],
            initialfile=Path(self.saida.get()).name,
        )
        if arquivo:
            self.saida.set(arquivo)

    def gerar(self) -> None:
        texto = self.texto.get("1.0", "end-1c").strip()
        if not texto or texto == "Digite ou cole o texto que será narrado aqui.":
            messagebox.showwarning("Texto necessário", "Digite o texto que será narrado.")
            return
        if not self.saida.get().strip():
            messagebox.showwarning("Destino necessário", "Escolha onde salvar o áudio.")
            return
        self.botao.state(["disabled"])
        threading.Thread(target=self._gerar_em_segundo_plano, args=(texto,), daemon=True).start()

    def _gerar_em_segundo_plano(self, texto: str) -> None:
        try:
            destino = asyncio.run(gerar_audio_wav(texto, Path(self.saida.get()), VOZES[self.voz.get()], self.velocidade.get()))
            self.after(0, self._concluido, destino)
        except Exception as erro:
            self.after(0, self._falhou, str(erro))

    def _concluido(self, destino: Path) -> None:
        self.botao.state(["!disabled"])
        messagebox.showinfo("Concluído", f"Áudio gerado com sucesso.\n\n{destino}")

    def _falhou(self, mensagem: str) -> None:
        self.botao.state(["!disabled"])
        messagebox.showerror("Erro ao gerar áudio", mensagem)


if __name__ == "__main__":
    GeradorTTSApp().mainloop()
