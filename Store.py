import tkinter as tk
from PIL import Image, ImageTk
import os
import RPi.GPIO as GPIO
import random

IMG_DIR = "/home/joao_rebolo/netmaster_menu/img"
CARTAS_DIR = os.path.join(IMG_DIR, "cartas")
COIN_IMG = os.path.join(IMG_DIR, "picoin.png")
AWNING_IMG = os.path.join(IMG_DIR, "Store_awning_v2.png")

KEY1_PIN = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(KEY1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

BOARD = [
    # Top row (left to right)
    ("start", "neutral"),      # 0 canto azul
    ("users", "blue"),         # 1
    ("actions", "neutral"),     # 2 (cinzento)
    ("equipment", "blue"),     # 3
    ("challenges", "neutral"), # 4 (cinzento)
    ("data", "red"),           # 5
    ("events", "neutral"),     # 6 (cinzento)
    ("services", "red"),       # 7

    # Right column (top to bottom)
    ("start", "neutral"),      # 8 canto vermelho
    ("users", "red"),          # 9
    ("actions", "neutral"),     # 10 (cinzento)
    ("equipment", "red"),      # 11
    ("challenges", "neutral"), # 12 (cinzento)
    ("data", "yellow"),        # 13
    ("events", "neutral"),     # 14 (cinzento)
    ("services", "yellow"),    # 15

    # Bottom row (right to left)
    ("start", "neutral"),      # 16 canto amarelo
    ("users", "yellow"),       # 17
    ("actions", "neutral"),     # 18 (cinzento)
    ("equipment", "yellow"),   # 19
    ("challenges", "neutral"), # 20 (cinzento)
    ("data", "green"),         # 21
    ("events", "neutral"),     # 22 (cinzento)
    ("services", "green"),     # 23

    # Left column (bottom to top)
    ("start", "neutral"),      # 24 canto verde
    ("users", "green"),        # 25
    ("actions", "neutral"),     # 26 (cinzento)
    ("equipment", "green"),    # 27
    ("challenges", "neutral"), # 28 (cinzento)
    ("data", "blue"),          # 29
    ("events", "neutral"),     # 30 (cinzento)
    ("services", "blue"),      # 31
]
NUM_CASAS = len(BOARD)

START_POSITIONS = {
    "blue": 0,
    "red": 8,
    "yellow": 16,
    "green": 24
}

CARD_TYPES = ["users", "action", "equipment", "challenges", "data", "events", "services"]
COLORS = ["green", "yellow", "red", "blue", "neutral"]

# Carregar baralhos como no Menu.py
def preparar_baralhos():
    baralhos = {}
    for cor in COLORS:
        baralhos[cor] = {}
        for tipo in CARD_TYPES:
            pasta = os.path.join(CARTAS_DIR, tipo)
            if os.path.exists(pasta):
                cartas = [os.path.join(pasta, f) for f in os.listdir(pasta) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                random.shuffle(cartas)
                baralhos[cor][tipo] = cartas.copy()
            else:
                baralhos[cor][tipo] = []
    return baralhos

baralhos = preparar_baralhos()

def tirar_carta(cor, tipo):
    """Tira a carta do topo do baralho da cor e tipo dados."""
    cartas = baralhos.get(cor, {}).get(tipo, [])
    if cartas:
        return cartas.pop(0)
    # Se não houver cartas dessa cor/tipo, tenta neutral
    cartas_neutral = baralhos.get("neutral", {}).get(tipo, [])
    if cartas_neutral:
        return cartas_neutral.pop(0)
    return None  # Não há cartas

class StoreWindow(tk.Toplevel):
    def __init__(self, root, player_color, player_name, saldo=1000, casa_tipo=None, casa_cor=None):
        super().__init__(root)
        self.title("Store")
        self.configure(bg="black")
        self.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
        self.overrideredirect(True)
        self.player_color = player_color.lower()
        self.player_name = player_name

        # Barra superior com imagem Store_awning.png
        awning_img = ImageTk.PhotoImage(Image.open(AWNING_IMG).resize((root.winfo_screenwidth(), 50)))
        awning_label = tk.Label(self, image=awning_img, bg="black")
        awning_label.image = awning_img
        awning_label.pack(pady=(0, 10), fill="x")

        # Frame principal para os botões
        main_frame = tk.Frame(self, bg="black")
        main_frame.pack(anchor="center", pady=(0, 20))

        btn_font = ("Helvetica", 18, "bold")
        btn_size = {"width": 6, "height": 3}

        # Primeira linha: Actions, Events, Challenges (neutras) com imagens GRANDES
        img_size = (90, 90)
        actions_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "Actions_button.png")).resize(img_size))
        events_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "Events_button.png")).resize(img_size))
        challenges_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "Challenges_button.png")).resize(img_size))

        btn_a = tk.Button(main_frame, image=actions_img, bg="#000000", activebackground="#000000", width=75, height=100, highlightthickness=0, bd=0)
        btn_e = tk.Button(main_frame, image=events_img, bg="#000000", activebackground="#000000", width=75, height=100, highlightthickness=0, bd=0)
        btn_d = tk.Button(main_frame, image=challenges_img, bg="#000000", activebackground="#000000", width=75, height=100, highlightthickness=0, bd=0)
        btn_a.image = actions_img
        btn_e.image = events_img
        btn_d.image = challenges_img

        btn_a.grid(row=0, column=0, padx=10, pady=(5, 2), sticky="n")
        btn_e.grid(row=0, column=1, padx=10, pady=(5, 2), sticky="n")
        btn_d.grid(row=0, column=2, padx=10, pady=(5, 2), sticky="n")

        # Botão para lançar o dado
        # roll_btn = tk.Button(self, text="Lançar Dado", font=("Helvetica", 18, "bold"),
        #                      bg="#A020F0", fg="white", command=self.roll_and_highlight)
        # roll_btn.pack(pady=20)

        self.btn_a = btn_a
        self.btn_e = btn_e
        self.btn_d = btn_d
        self.store_buttons = [btn_a, btn_e, btn_d]

        # Frame para centralizar os botões dos jogadores
        players_frame = tk.Frame(self, bg="black")
        players_frame.pack(pady=0)  # Espaço menor acima dos jogadores

        color_map = {
            "green": "#70AD47",
            "yellow": "#F2BA0D",
            "red": "#EE6F68",
            "blue": "#43BEF2"
        }

        # Segunda linha: J1, J2
        btn_j1 = tk.Button(players_frame, text="J1", font=btn_font, bg=color_map["blue"], fg="black", **btn_size)
        btn_j2 = tk.Button(players_frame, text="J2", font=btn_font, bg=color_map["red"], fg="black", **btn_size)
        btn_j3 = tk.Button(players_frame, text="J3", font=btn_font, bg=color_map["green"], fg="black", **btn_size)
        btn_j4 = tk.Button(players_frame, text="J4", font=btn_font, bg=color_map["yellow"], fg="black", **btn_size)
        btn_j1.grid(row=0, column=0, padx=10, pady=5)
        btn_j2.grid(row=0, column=1, padx=10, pady=5)
        btn_j3.grid(row=1, column=0, padx=10, pady=5)
        btn_j4.grid(row=1, column=1, padx=10, pady=5)

        self.jogador_buttons = {
            "blue": btn_j1,
            "red": btn_j2,
            "green": btn_j3,
            "yellow": btn_j4
        }

        # Bank com saldo e moeda, centralizado em baixo
        bank_frame = tk.Frame(self, bg="black")
        bank_frame.pack(side=tk.BOTTOM, pady=20)
        coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((40, 40)))
        tk.Label(bank_frame, text="Bank:", font=("Helvetica", 18, "bold"), bg="black", fg="white").pack(side=tk.LEFT)
        tk.Label(bank_frame, image=coin_img, bg="black").pack(side=tk.LEFT, padx=10)
        tk.Label(bank_frame, text=f"{saldo} piccoins", font=("Helvetica", 18, "bold"), bg="black", fg="#FFD600").pack(side=tk.LEFT)
        self.coin_img = coin_img  # manter referência

        # Inicia verificação do botão físico KEY1
        self.check_gpio_key()

        # Se receber casa_tipo e casa_cor, destaca o botão e mostra o label
        if casa_tipo and casa_cor:
            self.highlight_casa(casa_tipo, casa_cor)

    def check_gpio_key(self):
        if GPIO.input(KEY1_PIN) == GPIO.LOW:
            print()  # Salta uma linha no terminal
            GPIO.cleanup()
            self.destroy()
            os._exit(0)  # Termina imediatamente o processo
        else:
            self.after(100, self.check_gpio_key)

    def get_color(self, color):
        return {
            "green": "#00FF00",
            "yellow": "#FFD600",
            "red": "#FF0000",
            "blue": "#0070FF",
            "neutral": "#AAAAAA"
        }.get(color.lower(), "#AAAAAA")

    def roll_and_highlight(self):
        # Simula lançamento do dado
        steps = random.randint(1, 6)
        old_pos = getattr(self, "player_pos", START_POSITIONS.get(self.player_color.lower(), 0))
        new_pos = (old_pos + steps) % NUM_CASAS
        tipo, casa_cor = BOARD[new_pos]
        self.player_pos = new_pos

        # Remove destaque anterior
        for btn in getattr(self, "store_buttons", []):
            btn.config(highlightbackground="black", highlightthickness=0)

        # Mapeia tipo para botão
        tipo_to_btn = {
            "action": self.btn_a,
            "events": self.btn_e,
            "challenges": self.btn_d,
            # Adiciona outros tipos se necessário
        }
        btn = tipo_to_btn.get(tipo)
        if btn:
            btn.config(highlightbackground="#A020F0", highlightcolor="#A020F0", highlightthickness=6)
            # Mostra label com nome da casa
            if hasattr(self, "result_lbl") and self.result_lbl:
                self.result_lbl.destroy()
            self.result_lbl = tk.Label(self, text=tipo.upper(), font=("Helvetica", 22, "bold"),
                                      fg=self.get_color(casa_cor), bg="black")
            self.result_lbl.pack(pady=10)
            # Só permite clicar no botão destacado
            btn.config(command=lambda: self.tirar_carta(tipo, casa_cor))
        else:
            # Se não for um tipo com botão, só mostra o nome
            if hasattr(self, "result_lbl") and self.result_lbl:
                self.result_lbl.destroy()
            self.result_lbl = tk.Label(self, text=tipo.upper(), font=("Helvetica", 22, "bold"),
                                      fg=self.get_color(casa_cor), bg="black")
            self.result_lbl.pack(pady=10)

    def highlight_casa(self, casa_tipo, casa_cor):
        # Remove destaque anterior
        for btn in getattr(self, "store_buttons", []):
            btn.config(highlightbackground="black", highlightthickness=0)

        tipo_to_btn = {
            "action": self.btn_a,
            "events": self.btn_e,
            "challenges": self.btn_d,
        }
        btn = tipo_to_btn.get(casa_tipo)
        if btn:
            btn.config(highlightbackground="#A020F0", highlightcolor="#A020F0", highlightthickness=6)
            # Mostra label com nome da casa
            if hasattr(self, "result_lbl") and self.result_lbl:
                self.result_lbl.destroy()
            self.result_lbl = tk.Label(self, text=casa_tipo.upper(), font=("Helvetica", 22, "bold"),
                                      fg=self.get_color(casa_cor), bg="black")
            self.result_lbl.pack(pady=10)
            # Só permite clicar no botão destacado
            btn.config(command=lambda: self.tirar_carta(casa_tipo, casa_cor))
        else:
            if hasattr(self, "result_lbl") and self.result_lbl:
                self.result_lbl.destroy()
            self.result_lbl = tk.Label(self, text=casa_tipo.upper(), font=("Helvetica", 22, "bold"),
                                      fg=self.get_color(casa_cor), bg="black")
            self.result_lbl.pack(pady=10)

        # Destaca o botão do jogador se calhar na sua cor
        if casa_cor in self.jogador_buttons and casa_cor == self.player_color:
            btn_jogador = self.jogador_buttons[casa_cor]
            btn_jogador.config(highlightbackground="#A020F0", highlightcolor="#A020F0", highlightthickness=6)
            btn_jogador.config(command=lambda: self.tirar_carta_jogador(casa_tipo, casa_cor))
        else:
            # Remove destaque dos botões dos jogadores
            for btn in self.jogador_buttons.values():
                btn.config(highlightbackground="black", highlightthickness=0)
                btn.config(command=lambda: None)

    def tirar_carta(self, casa_tipo, casa_cor):
        # Aqui podes implementar a lógica de mostrar a carta, igual ao Menu.py
        # Exemplo: mostra só um popup
        from tkinter import messagebox
        messagebox.showinfo("Tirar Carta", f"Tiraste uma carta de {casa_tipo.upper()} ({casa_cor.upper()})!")
        # Remove destaque
        for btn in getattr(self, "store_buttons", []):
            btn.config(highlightbackground="black", highlightthickness=0)
        if hasattr(self, "result_lbl") and self.result_lbl:
            self.result_lbl.destroy()

    def tirar_carta_jogador(self, casa_tipo, casa_cor):
        self.mostrar_carta(casa_cor, casa_tipo)

    def mostrar_carta(self, casa_cor, tipo):
        # Limpa tudo da janela Store, mas mantém a barra superior
        for widget in self.winfo_children():
            if hasattr(self, "awning_label") and widget == self.awning_label:
                continue
            widget.destroy()
        self.configure(bg="black")

        # Frame central para centrar carta e botão
        center_frame = tk.Frame(self, bg="black")
        center_frame.pack(expand=True)

        verso_path = os.path.join(CARTAS_DIR, "back_card.png")
        if not os.path.exists(verso_path):
            verso_path = os.path.join(CARTAS_DIR, "verso.png")

        img = ImageTk.PhotoImage(Image.open(verso_path).resize((220, 320)))
        carta_lbl = tk.Label(center_frame, image=img, bg="black")
        carta_lbl.image = img
        carta_lbl.pack(pady=(0, 12))

        def revelar_carta():
            carta_lbl.destroy()
            go_btn.destroy()
            carta_path = tirar_carta(casa_cor, tipo)
            if carta_path and os.path.exists(carta_path):
                self.mostrar_carta_fullscreen(carta_path, tipo)
            else:
                tk.Label(center_frame, text="Sem cartas disponíveis!", font=("Helvetica", 14), bg="black", fg="white").pack(pady=10)

        go_btn = tk.Button(center_frame, text="Go!", font=("Helvetica", 16, "bold"), bg="#005c75", fg="white", command=revelar_carta)
        go_btn.pack(pady=(5, 0))

    def mostrar_carta_fullscreen(self, carta_path, casa_tipo):
        print("DEBUG: Store.mostrar_carta_fullscreen chamado")
        # Limpa tudo da janela Store
        for widget in self.winfo_children():
            widget.destroy()
        self.configure(bg="black")

        pil_img = Image.open(carta_path)
        img_w, img_h = pil_img.size
        # Usa todo o ecrã (sem margem)
        max_w, max_h = self.winfo_screenwidth(), self.winfo_screenheight()
        ratio = min(max_w/img_w, max_h/img_h)
        new_w, new_h = int(img_w*ratio), int(img_h*ratio)
        pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)

        carta_img = ImageTk.PhotoImage(pil_img)
        carta_real_lbl = tk.Label(self, image=carta_img, bg="black")
        carta_real_lbl.image = carta_img
        carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Botão X no canto superior direito
        x_img_path = os.path.join(IMG_DIR, "X_button.png")
        x_img = ImageTk.PhotoImage(Image.open(x_img_path).resize((48, 48)))

        def fechar():
            carta_real_lbl.destroy()
            x_btn.destroy()
            # Guarda a carta no dashboard
            if casa_tipo in ["data", "challenges"]:
                if hasattr(self.master, "adicionar_carta_carrossel"):
                    self.master.adicionar_carta_carrossel(carta_path)
            elif casa_tipo in ["users", "equipment", "services", "action", "events"]:
                if hasattr(self.master, "adicionar_carta_inventario"):
                    self.master.adicionar_carta_inventario(carta_path, casa_tipo)
            self.destroy()
            # Volta ao dashboard e mostra a interface principal
            if hasattr(self.master, "playerdashboard_interface"):
                self.master.playerdashboard_interface(
                    self.master.player_name,
                    self.master.saldo,
                    self.master.other_players
                )

        x_btn = tk.Label(self, image=x_img, bg="black", cursor="hand2")
        x_btn.image = x_img
        x_btn.place(relx=0.98, rely=0.02, anchor="ne")
        x_btn.bind("<Button-1>", lambda e: fechar())