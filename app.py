"""Interface gráfica para o Gerador de TTS."""

import asyncio
import ctypes
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from gerar_tts import FORMATO_PADRAO, FORMATOS, gerar_audio_arquivo


VOZES = {
    "Francisca (Brasil)": "pt-BR-FranciscaNeural",
    "Antonio (Brasil)": "pt-BR-AntonioNeural",
    "Thalita (Brasil)": "pt-BR-ThalitaMultilingualNeural",
    "Raquel (Portugal)": "pt-PT-RaquelNeural",
    "Duarte (Portugal)": "pt-PT-DuarteNeural",
}
VELOCIDADES = ["-25%", "-15%", "-10%", "-5%", "+0%", "+10%", "+20%", "+30%"]
ROTULO_FORMATO = {rotulo: chave for chave, (rotulo, _, _) in FORMATOS.items()}

# Paleta compartilhada com o SIPPER (ciper/gui/theme.py, tema "dark").
COR = {
    "bg": "#050505",
    "panel": "#101010",
    "panel_alt": "#161616",
    "surface": "#0C0C0C",
    "border": "#3A1217",
    "text": "#F5EDEE",
    "muted": "#B08F94",
    "accent": "#C1121F",
    "accent_alt": "#8F0D18",
    "success": "#22A06B",
    "selection": "#3D1218",
}
FONTE = "Segoe UI"
PLACEHOLDER = "Digite ou cole aqui o texto que será narrado…"

PASTA_RECURSOS = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
ICONE = PASTA_RECURSOS / "icon" / "app.ico"


class GeradorTTSApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Gerador de TTS")
        if ICONE.is_file():
            self.iconbitmap(default=str(ICONE))
        self.geometry("820x640")
        self.configure(background=COR["border"])
        self.resizable(False, False)
        self.overrideredirect(True)
        self.after(10, self._centralizar_e_arredondar)

        self.voz = tk.StringVar(value="Francisca (Brasil)")
        self.velocidade = tk.StringVar(value="+0%")
        self.formato = tk.StringVar(value=FORMATOS[FORMATO_PADRAO][0])
        self.saida = tk.StringVar(value=self._saida_padrao())
        self.status = tk.StringVar(value="Pronto para gerar.")
        self.contador = tk.StringVar(value="0 caracteres")
        self._ultimo_arquivo: Path | None = None
        self._gerando = False

        self._configurar_estilos()
        self._montar_tela()
        self.formato.trace_add("write", lambda *_: self._ajustar_extensao())

    # ------------------------------------------------------------------ janela

    def _centralizar_e_arredondar(self) -> None:
        """Centraliza a janela e aplica cantos arredondados no Windows."""
        self.update_idletasks()
        largura, altura = self.winfo_width(), self.winfo_height()
        posicao_x = (self.winfo_screenwidth() - largura) // 2
        posicao_y = (self.winfo_screenheight() - altura) // 2
        self.geometry(f"{largura}x{altura}+{posicao_x}+{posicao_y}")

        if self.tk.call("tk", "windowingsystem") == "win32":
            regiao = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, largura + 1, altura + 1, 18, 18)
            ctypes.windll.user32.SetWindowRgn(self.winfo_id(), regiao, True)
            self._mostrar_na_barra_de_tarefas()

    def _janela_windows(self) -> int:
        """Devolve o handle da janela de nível superior criada pelo Tk."""
        return ctypes.windll.user32.GetParent(self.winfo_id())

    def _mostrar_na_barra_de_tarefas(self) -> None:
        """Janelas sem borda (overrideredirect) somem da barra; isto as traz de volta."""
        gwl_exstyle, ws_ex_appwindow, ws_ex_toolwindow = -20, 0x00040000, 0x00000080
        user32 = ctypes.windll.user32
        hwnd = self._janela_windows()
        estilo = user32.GetWindowLongW(hwnd, gwl_exstyle)
        user32.SetWindowLongW(hwnd, gwl_exstyle, (estilo & ~ws_ex_toolwindow) | ws_ex_appwindow)
        # O Windows só aplica a mudança quando a janela é exibida novamente.
        self.withdraw()
        self.after(10, self.deiconify)

    def _minimizar(self) -> None:
        if self.tk.call("tk", "windowingsystem") == "win32":
            sw_minimize = 6
            ctypes.windll.user32.ShowWindow(self._janela_windows(), sw_minimize)
        else:
            self.iconify()

    def _iniciar_arrasto(self, evento: tk.Event) -> None:
        self._arrasto_x = evento.x_root
        self._arrasto_y = evento.y_root

    def _arrastar_janela(self, evento: tk.Event) -> None:
        deslocamento_x = evento.x_root - self._arrasto_x
        deslocamento_y = evento.y_root - self._arrasto_y
        self.geometry(f"+{self.winfo_x() + deslocamento_x}+{self.winfo_y() + deslocamento_y}")
        self._arrasto_x = evento.x_root
        self._arrasto_y = evento.y_root

    # ------------------------------------------------------------------ estilo

    def _configurar_estilos(self) -> None:
        estilo = ttk.Style(self)
        estilo.theme_use("clam")

        self.option_add("*TCombobox*Listbox.background", COR["panel_alt"])
        self.option_add("*TCombobox*Listbox.foreground", COR["text"])
        self.option_add("*TCombobox*Listbox.selectBackground", COR["selection"])
        self.option_add("*TCombobox*Listbox.selectForeground", COR["text"])
        self.option_add("*TCombobox*Listbox.font", (FONTE, 10))
        self.option_add("*TCombobox*Listbox.borderWidth", 0)
        self.option_add("*TCombobox*Listbox.highlightThickness", 0)

        campo = {
            "fieldbackground": COR["surface"],
            "background": COR["surface"],
            "foreground": COR["text"],
            "bordercolor": COR["border"],
            "lightcolor": COR["surface"],
            "darkcolor": COR["surface"],
            "insertcolor": COR["text"],
            "padding": (10, 7),
        }
        estilo.configure("App.TCombobox", arrowcolor=COR["muted"], arrowsize=14, **campo)
        estilo.map(
            "App.TCombobox",
            fieldbackground=[("readonly", COR["surface"])],
            background=[("active", COR["panel_alt"]), ("readonly", COR["surface"])],
            foreground=[("readonly", COR["text"])],
            arrowcolor=[("active", COR["accent"]), ("pressed", COR["accent"])],
            bordercolor=[("focus", COR["accent"]), ("active", COR["accent"])],
            lightcolor=[("focus", COR["surface"])],
            darkcolor=[("focus", COR["surface"])],
            selectbackground=[("readonly", COR["surface"])],
            selectforeground=[("readonly", COR["text"])],
        )
        estilo.configure("App.TEntry", selectbackground=COR["selection"], selectforeground=COR["text"], **campo)
        estilo.map("App.TEntry", bordercolor=[("focus", COR["accent"])], lightcolor=[("focus", COR["surface"])])

        estilo.configure(
            "App.Horizontal.TProgressbar",
            troughcolor=COR["surface"],
            background=COR["accent"],
            bordercolor=COR["border"],
            lightcolor=COR["accent"],
            darkcolor=COR["accent"],
            thickness=4,
        )

    @staticmethod
    def _hover(widget: tk.Widget, normal: dict, sobre: dict) -> None:
        def entrar(_evento: tk.Event) -> None:
            if str(widget.cget("state")) != "disabled":
                widget.configure(**sobre)

        widget.bind("<Enter>", entrar)
        widget.bind("<Leave>", lambda _evento: widget.configure(**normal))

    def _cartao(self, pai: tk.Widget, titulo: str) -> tk.Frame:
        """Cria um painel com borda e título no estilo dos cards do SIPPER."""
        borda = tk.Frame(pai, background=COR["panel"], highlightthickness=1, highlightbackground=COR["border"])
        tk.Label(
            borda, text=titulo.upper(), background=COR["panel"], foreground=COR["muted"],
            font=(FONTE, 8, "bold"), anchor="w",
        ).pack(fill="x", padx=16, pady=(12, 6))
        corpo = tk.Frame(borda, background=COR["panel"])
        corpo.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        borda.corpo = corpo  # type: ignore[attr-defined]
        return borda

    def _rotulo(self, pai: tk.Widget, texto: str) -> tk.Label:
        return tk.Label(pai, text=texto, background=COR["panel"], foreground=COR["text"], font=(FONTE, 9), anchor="w")

    # ------------------------------------------------------------------ tela

    def _montar_tela(self) -> None:
        # Moldura de 1px na cor da borda, como o contorno das janelas do SIPPER.
        janela = tk.Frame(self, background=COR["bg"])
        janela.pack(fill="both", expand=True, padx=1, pady=1)

        self._montar_barra_titulo(janela)

        conteudo = tk.Frame(janela, background=COR["bg"])
        conteudo.pack(fill="both", expand=True, padx=20, pady=(4, 20))

        tk.Label(
            conteudo, text="Texto para fala", background=COR["bg"], foreground=COR["text"],
            font=(FONTE, 18, "bold"), anchor="w",
        ).pack(fill="x")
        tk.Label(
            conteudo, text="Escreva o texto, escolha voz e formato, e gere o áudio.",
            background=COR["bg"], foreground=COR["muted"], font=(FONTE, 10), anchor="w",
        ).pack(fill="x", pady=(0, 14))

        self._montar_cartao_texto(conteudo)
        self._montar_cartao_opcoes(conteudo)
        self._montar_rodape(conteudo)

    def _montar_barra_titulo(self, pai: tk.Widget) -> None:
        barra = tk.Frame(pai, background=COR["bg"], height=42)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        marca = tk.Frame(barra, background=COR["bg"])
        marca.pack(side="left", padx=(18, 0))
        ponto = tk.Canvas(marca, width=10, height=10, background=COR["bg"], highlightthickness=0)
        ponto.create_oval(1, 1, 9, 9, fill=COR["accent"], outline="")
        ponto.pack(side="left", pady=(2, 0))
        titulo = tk.Label(
            marca, text="GERADOR DE TTS", background=COR["bg"], foreground=COR["text"],
            font=(FONTE, 9, "bold"), padx=8,
        )
        titulo.pack(side="left")
        for item in (barra, marca, ponto, titulo):
            item.bind("<ButtonPress-1>", self._iniciar_arrasto)
            item.bind("<B1-Motion>", self._arrastar_janela)

        base = {
            "background": COR["bg"], "foreground": COR["muted"], "activeforeground": COR["text"],
            "borderwidth": 0, "relief": "flat", "width": 5, "takefocus": 0, "cursor": "hand2",
        }
        fechar = tk.Button(barra, text="✕", command=self.destroy, activebackground=COR["accent"], font=(FONTE, 10), **base)
        fechar.pack(side="right", fill="y")
        self._hover(fechar, {"background": COR["bg"], "foreground": COR["muted"]}, {"background": COR["accent"], "foreground": COR["text"]})
        minimizar = tk.Button(barra, text="—", command=self._minimizar, activebackground=COR["panel_alt"], font=(FONTE, 9), **base)
        minimizar.pack(side="right", fill="y")
        self._hover(minimizar, {"background": COR["bg"], "foreground": COR["muted"]}, {"background": COR["panel_alt"], "foreground": COR["text"]})

    def _montar_cartao_texto(self, pai: tk.Widget) -> None:
        cartao = self._cartao(pai, "Texto")
        cartao.pack(fill="both", expand=True)

        moldura = tk.Frame(cartao.corpo, background=COR["surface"], highlightthickness=1, highlightbackground=COR["border"], highlightcolor=COR["accent"])
        moldura.pack(fill="both", expand=True)
        self.texto = tk.Text(
            moldura, wrap="word", font=(FONTE, 11), height=7, undo=True,
            background=COR["surface"], foreground=COR["muted"], insertbackground=COR["text"],
            selectbackground=COR["selection"], selectforeground=COR["text"],
            relief="flat", borderwidth=0, highlightthickness=0, padx=12, pady=10,
        )
        self.texto.pack(side="left", fill="both", expand=True)
        self.texto.insert("1.0", PLACEHOLDER)
        self.texto.bind("<FocusIn>", self._limpar_placeholder)
        self.texto.bind("<FocusOut>", self._restaurar_placeholder)
        self.texto.bind("<<Modified>>", self._texto_alterado)
        self.texto.bind("<FocusIn>", lambda _e: moldura.configure(highlightbackground=COR["accent"]), add="+")
        self.texto.bind("<FocusOut>", lambda _e: moldura.configure(highlightbackground=COR["border"]), add="+")
        self.texto.bind("<Control-Return>", lambda _e: (self.gerar(), "break")[1])

        info = tk.Frame(cartao.corpo, background=COR["panel"])
        info.pack(fill="x", pady=(6, 0))
        tk.Label(info, textvariable=self.contador, background=COR["panel"], foreground=COR["muted"], font=(FONTE, 8)).pack(side="left")
        tk.Label(info, text="Ctrl+Enter para gerar", background=COR["panel"], foreground=COR["muted"], font=(FONTE, 8)).pack(side="right")

    def _montar_cartao_opcoes(self, pai: tk.Widget) -> None:
        cartao = self._cartao(pai, "Configurações")
        cartao.pack(fill="x", pady=(14, 0))
        corpo = cartao.corpo
        for coluna, peso in enumerate((3, 2, 4)):
            corpo.columnconfigure(coluna, weight=peso, uniform="opcoes")

        campos = (
            ("Voz", self.voz, list(VOZES)),
            ("Velocidade", self.velocidade, VELOCIDADES),
            ("Formato do áudio", self.formato, list(ROTULO_FORMATO)),
        )
        for coluna, (rotulo, variavel, valores) in enumerate(campos):
            margem = (0, 0) if coluna == 2 else (0, 12)
            self._rotulo(corpo, rotulo).grid(row=0, column=coluna, sticky="w", padx=margem)
            combo = ttk.Combobox(corpo, textvariable=variavel, values=valores, state="readonly", style="App.TCombobox", font=(FONTE, 10))
            combo.grid(row=1, column=coluna, sticky="ew", padx=margem, pady=(4, 12))
            combo.bind("<<ComboboxSelected>>", lambda _e, c=combo: c.selection_clear())

        self._rotulo(corpo, "Salvar como").grid(row=2, column=0, columnspan=3, sticky="w")
        destino = tk.Frame(corpo, background=COR["panel"])
        destino.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(4, 0))
        destino.columnconfigure(0, weight=1)
        ttk.Entry(destino, textvariable=self.saida, style="App.TEntry", font=(FONTE, 10)).grid(row=0, column=0, sticky="ew")
        procurar = tk.Button(
            destino, text="Procurar…", command=self.escolher_saida, cursor="hand2",
            background=COR["panel_alt"], foreground=COR["text"], activebackground=COR["selection"],
            activeforeground=COR["text"], relief="flat", borderwidth=0, font=(FONTE, 10),
            padx=16, pady=6, highlightthickness=1, highlightbackground=COR["border"], takefocus=0,
        )
        procurar.grid(row=0, column=1, sticky="ns", padx=(8, 0))
        self._hover(
            procurar,
            {"background": COR["panel_alt"], "highlightbackground": COR["border"]},
            {"background": COR["selection"], "highlightbackground": COR["accent"]},
        )

    def _montar_rodape(self, pai: tk.Widget) -> None:
        self.progresso = ttk.Progressbar(pai, mode="indeterminate", style="App.Horizontal.TProgressbar")

        rodape = tk.Frame(pai, background=COR["bg"])
        rodape.pack(fill="x", side="bottom", pady=(14, 0))
        self._rodape = rodape

        esquerda = tk.Frame(rodape, background=COR["bg"])
        esquerda.pack(side="left", fill="x", expand=True)
        self.rotulo_status = tk.Label(
            esquerda, textvariable=self.status, background=COR["bg"], foreground=COR["muted"],
            font=(FONTE, 9), anchor="w", justify="left", wraplength=520,
        )
        self.rotulo_status.pack(side="left")
        self.botao_abrir = tk.Label(
            esquerda, text="Abrir pasta", background=COR["bg"], foreground=COR["accent"],
            font=(FONTE, 9, "underline"), cursor="hand2",
        )
        self.botao_abrir.bind("<Button-1>", lambda _e: self._abrir_pasta())

        self.botao = tk.Button(
            rodape, text="▶  Gerar áudio", command=self.gerar, cursor="hand2",
            background=COR["accent"], foreground=COR["text"], activebackground=COR["accent_alt"],
            activeforeground=COR["text"], disabledforeground=COR["muted"],
            relief="flat", borderwidth=0, font=(FONTE, 10, "bold"), padx=22, pady=9, takefocus=0,
        )
        self.botao.pack(side="right")
        self._hover(self.botao, {"background": COR["accent"]}, {"background": COR["accent_alt"]})

    # ------------------------------------------------------------------ texto

    def _limpar_placeholder(self, _evento: tk.Event) -> None:
        if self.texto.get("1.0", "end-1c") == PLACEHOLDER:
            self.texto.delete("1.0", "end")
            self.texto.configure(foreground=COR["text"])

    def _restaurar_placeholder(self, _evento: tk.Event) -> None:
        if not self.texto.get("1.0", "end-1c").strip():
            self.texto.delete("1.0", "end")
            self.texto.insert("1.0", PLACEHOLDER)
            self.texto.configure(foreground=COR["muted"])

    def _texto_atual(self) -> str:
        texto = self.texto.get("1.0", "end-1c")
        return "" if texto == PLACEHOLDER else texto.strip()

    def _texto_alterado(self, _evento: tk.Event) -> None:
        total = len(self._texto_atual())
        self.contador.set(f"{total} caractere" + ("" if total == 1 else "s"))
        self.texto.edit_modified(False)

    # ------------------------------------------------------------------ saída

    def _formato_atual(self) -> str:
        return ROTULO_FORMATO[self.formato.get()]

    def _extensao_atual(self) -> str:
        return FORMATOS[self._formato_atual()][1]

    @staticmethod
    def _saida_padrao() -> str:
        nome = f"audio_{datetime.now():%Y%m%d_%H%M%S}{FORMATOS[FORMATO_PADRAO][1]}"
        # Instalado em Arquivos de Programas, a pasta atual não é gravável.
        base = Path.home() / "Documents" / "Gerador TTS" if getattr(sys, "frozen", False) else Path.cwd() / "audios"
        return str(base / nome)

    def _ajustar_extensao(self) -> None:
        caminho = self.saida.get().strip()
        if caminho:
            self.saida.set(str(Path(caminho).with_suffix(self._extensao_atual())))

    def escolher_saida(self) -> None:
        extensao = self._extensao_atual()
        atual = Path(self.saida.get())
        arquivo = filedialog.asksaveasfilename(
            title="Salvar áudio", defaultextension=extensao,
            filetypes=[(self.formato.get(), f"*{extensao}"), ("Todos os arquivos", "*.*")],
            initialdir=str(atual.parent) if atual.parent.is_dir() else None,
            initialfile=atual.with_suffix(extensao).name,
        )
        if arquivo:
            self.saida.set(str(Path(arquivo).with_suffix(extensao)))

    def _abrir_pasta(self) -> None:
        if self._ultimo_arquivo is None:
            return
        if sys.platform == "win32":
            subprocess.Popen(["explorer", "/select,", str(self._ultimo_arquivo)])

    # ------------------------------------------------------------------ geração

    def _definir_status(self, mensagem: str, cor: str = COR["muted"], mostrar_abrir: bool = False) -> None:
        self.status.set(mensagem)
        self.rotulo_status.configure(foreground=cor)
        if mostrar_abrir:
            self.botao_abrir.pack(side="left", padx=(10, 0))
        else:
            self.botao_abrir.pack_forget()

    def _alternar_gerando(self, gerando: bool) -> None:
        self._gerando = gerando
        if gerando:
            self.botao.configure(state="disabled", text="Gerando…", background=COR["selection"], cursor="watch")
            self.progresso.pack(fill="x", side="bottom", before=self._rodape, pady=(12, 0))
            self.progresso.start(12)
        else:
            self.botao.configure(state="normal", text="▶  Gerar áudio", background=COR["accent"], cursor="hand2")
            self.progresso.stop()
            self.progresso.pack_forget()

    def gerar(self) -> None:
        if self._gerando:
            return
        texto = self._texto_atual()
        if not texto:
            messagebox.showwarning("Texto necessário", "Digite o texto que será narrado.")
            return
        if not self.saida.get().strip():
            messagebox.showwarning("Destino necessário", "Escolha onde salvar o áudio.")
            return
        self._alternar_gerando(True)
        self._definir_status("Gerando áudio, aguarde…")
        parametros = (texto, Path(self.saida.get()), VOZES[self.voz.get()], self.velocidade.get(), self._formato_atual())
        threading.Thread(target=self._gerar_em_segundo_plano, args=parametros, daemon=True).start()

    def _gerar_em_segundo_plano(self, texto: str, saida: Path, voz: str, velocidade: str, formato: str) -> None:
        try:
            destino = asyncio.run(gerar_audio_arquivo(texto, saida, voz, velocidade, formato))
            self.after(0, self._concluido, destino)
        except Exception as erro:
            self.after(0, self._falhou, str(erro))

    def _concluido(self, destino: Path) -> None:
        self._alternar_gerando(False)
        self._ultimo_arquivo = destino
        self._definir_status(f"✓ Salvo em {destino}", COR["success"], mostrar_abrir=True)
        # Prepara um novo nome para não sobrescrever o áudio recém-gerado.
        novo = Path(self._saida_padrao()).with_suffix(self._extensao_atual()).name
        self.saida.set(str(destino.parent / novo))

    def _falhou(self, mensagem: str) -> None:
        self._alternar_gerando(False)
        self._definir_status("Falha ao gerar o áudio.", COR["accent"])
        messagebox.showerror("Erro ao gerar áudio", mensagem)


if __name__ == "__main__":
    if sys.platform == "win32":
        # Faz a barra de tarefas usar o ícone do app em vez do ícone do Python.
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("GeradorTTS.App")
    GeradorTTSApp().mainloop()
