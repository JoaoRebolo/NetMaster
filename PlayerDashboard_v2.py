import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import RPi.GPIO as GPIO

IMG_DIR = os.path.join(os.path.dirname(__file__), "img")
LOGO_IMG = os.path.join(IMG_DIR, "logo_netmaster_icon_v3.png")
COIN_IMG = os.path.join(IMG_DIR, "picoin.png")
USER_ICONS = [
    os.path.join(IMG_DIR, "red_user_button_icon.png"),
    os.path.join(IMG_DIR, "green_user_button_icon.png"),
    os.path.join(IMG_DIR, "blue_user_button_icon.png"),
    os.path.join(IMG_DIR, "yellow_user_button_icon.png"),
]

CARD_IMG = os.path.join(IMG_DIR, "cartas", "back_card.png")  # Exemplo

# GPIO setup para botão KEY1
KEY1_PIN = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(KEY1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

 # Verificar botão KEY1 para sair
def check_gpio_key():
    if GPIO.input(KEY1_PIN) == GPIO.LOW:
        GPIO.cleanup()
        root.destroy()
    root.after(100, check_gpio_key)

def mostrar_carta_fullscreen_root(root, carta_path, selected_card_idx=0):
    # Limpa tudo do root
    for widget in root.winfo_children():
        widget.destroy()
    root.configure(bg="black")

    pil_img = Image.open(carta_path)
    img_w, img_h = pil_img.size
    max_w, max_h = root.winfo_screenwidth(), root.winfo_screenheight()
    ratio = min(max_w/img_w, max_h/img_h)
    new_w, new_h = int(img_w*ratio), int(img_h*ratio)
    pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)

    carta_img = ImageTk.PhotoImage(pil_img)
    carta_real_lbl = tk.Label(root, image=carta_img, bg="black")
    carta_real_lbl.image = carta_img
    carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center")

    # Botão de fechar (X)
    x_img_path = os.path.join(os.path.dirname(__file__), "img", "X_button.png")
    x_img = ImageTk.PhotoImage(Image.open(x_img_path).resize((48, 48)))
    x_btn = tk.Label(root, image=x_img, cursor="hand2", bg="black")
    x_btn.image = x_img
    x_btn.place(relx=0.98, rely=0.02, anchor="ne")

    def fechar():
        carta_real_lbl.destroy()
        x_btn.destroy()
        # Restaura o dashboard mantendo a carta selecionada
        PlayerDashboard(root, player_color="green", saldo=1000, other_players=["red", "blue", "yellow"], selected_card_idx=selected_card_idx)
    x_btn.bind("<Button-1>", lambda e: fechar())

def make_card_callback(parent, path):
    def callback(event):
        # Descobre qual label foi clicado
        clicked_label = event.widget
        # Se já está selecionada (borda roxa), mostra em fullscreen
        if getattr(clicked_label, "selected", False):
            parent.try_mostrar_carta(path)
            return
        # Remove borda de todas as cartas
        for lbl in parent.card_labels:
            lbl.config(highlightthickness=0)
            lbl.selected = False
        # Adiciona borda roxa à carta clicada
        clicked_label.config(highlightbackground="#8000FF", highlightcolor="#8000FF", highlightthickness=4)
        clicked_label.selected = True
        # Atualiza barras de progresso conforme a carta
        parent.update_progress_bars_for_card(path)
    return callback

class PlayerDashboard(tk.Toplevel):
    def __init__(self, root, player_color, saldo, other_players, player_name="Player", selected_card_idx=0):
        super().__init__(root)
        # Inicialize as cartas e o índice do carrossel ANTES de qualquer uso!
        self.cards = [
            CARD_IMG, CARD_IMG, CARD_IMG, CARD_IMG  # Substitua pelos caminhos reais das cartas
        ]
        self.card_idx = 0
        self.card_stats = [
            {"To send": 2, "Rxd": 3, "Lost": 0},
            {"To send": 5, "Rxd": 1, "Lost": 1},
            {"To send": 1, "Rxd": 0, "Lost": 0},
            {"To send": 4, "Rxd": 2, "Lost": 2},
        ]

        self.title("")  # Sem título
        self.configure(bg="black")
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}+0+0")
        self.overrideredirect(True)  # Remove barra de título
        self.attributes("-fullscreen", True)  # Garante fullscreen (opcional)

        color_map = {
            "green": "#00FF00",
            "yellow": "#FFD600",
            "red": "#FF0000",
            "blue": "#0070FF"
        }
        
        self.progress_bars = {}  # Guarda referências às barras
        self.selected_card_idx = selected_card_idx

        bar_color = color_map.get(player_color.lower(), "#AAAAAA")
        top_bar = tk.Frame(self, bg=bar_color, height=60)
        top_bar.pack(fill="x", side="top", padx=0)
        top_bar.pack_propagate(False)

        # Ícones dos outros jogadores (esquerda)
        icons_frame = tk.Frame(top_bar, bg=bar_color)
        icons_frame.pack(side="left", padx=(0,0))  # Valor negativo aproxima da borda esquerda
        for idx, p in enumerate(other_players):
            if idx < len(USER_ICONS):
                icon_img = ImageTk.PhotoImage(Image.open(USER_ICONS[idx]).resize((40,40)))
                lbl = tk.Label(icons_frame, image=icon_img, bg=bar_color)
                lbl.image = icon_img
                lbl.pack(side="left", padx=0)

        # Nome do jogador (centro)
        name_lbl = tk.Label(top_bar, text=player_name, font=("Helvetica", 18, "bold"), bg=bar_color, fg="black")
        name_lbl.pack(side="left", expand=True, padx=10)

        # Saldo (direita)
        saldo_frame = tk.Frame(top_bar, bg=bar_color)
        saldo_frame.pack(side="right", padx=10)
        coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24,24)))
        coin_lbl = tk.Label(saldo_frame, image=coin_img, bg=bar_color)
        coin_lbl.image = coin_img
        coin_lbl.pack(side="left")
        saldo_lbl = tk.Label(saldo_frame, text=f"{saldo}", font=("Helvetica", 16, "bold"), bg=bar_color, fg="black")
        saldo_lbl.pack(side="left", padx=4)

        # --- NOVO LAYOUT ---

        # Espaço extra antes dos botões
        self.after(0, lambda: self.update())  # Garante update do layout antes de calcular altura
        tk.Frame(self, height=20, bg="black").pack()  # Adiciona espaço vertical

        # 1. Botões grandes (layout igual ao carrossel)
        btns_frame = tk.Frame(self, bg="black")
        btns_frame.pack(pady=18)  # Aumenta o espaço acima e abaixo dos botões
        card_width, card_height = 85, 120  # Igual ao carrossel

        btn_info = [
            ("Users", bar_color),
            ("Equip.", bar_color),
            ("Services", bar_color),
            ("Actions/\nEvents", bar_color)
        ]
        self.action_buttons = []
        for text, color in btn_info:
            btn_font = ("Helvetica", 13, "bold")
            if text.startswith("Services"):
                btn_font = ("Helvetica", 12, "bold")  # Fonte menor só para "Services"
            btn = tk.Button(
                btns_frame, text=text, font=btn_font,
                wraplength=70,
                bg=color, fg="black", activebackground="white", activeforeground="black",
                bd=0, highlightthickness=0
            )
            # Aumenta a altura vertical dos botões
            btn.pack(side=tk.LEFT, padx=2, ipady=22, expand=True, fill="both")
            self.action_buttons.append(btn)

        # 2. Carrossel de cartas (agora abaixo dos botões)
        carousel_frame = tk.Frame(self, bg="black")
        carousel_frame.pack(pady=2)
        cards_container = tk.Frame(carousel_frame, bg="black")
        cards_container.pack()

        card_width, card_height = 85, 120  # Certifique-se que está definido antes

        self.card_labels = []
        for i in range(4):
            idx = (self.card_idx + i) % len(self.cards)
            img = ImageTk.PhotoImage(Image.open(self.cards[idx]).resize((card_width, card_height)))
            lbl = tk.Label(cards_container, image=img, bg="black")
            lbl.image = img
            lbl.grid(row=0, column=i, padx=2, pady=0)  # <-- Use grid para alinhamento
            lbl.bind("<Button-1>", make_card_callback(self, self.cards[idx]))
            if idx == self.selected_card_idx:
                lbl.config(highlightbackground="#8000FF", highlightcolor="#8000FF", highlightthickness=4)
                lbl.selected = True
            else:
                lbl.config(highlightthickness=0)
                lbl.selected = False
            self.card_labels.append(lbl)

        # --- Tabela de valores por baixo das cartas ---
        stats_frame = tk.Frame(self, bg="black")
        stats_frame.pack(pady=(4, 0))

        stats_labels = ["To send", "Rxd", "Lost"]
        self.stats_value_labels = []

        for row, stat in enumerate(stats_labels):
            legend = tk.Label(stats_frame, text=stat, font=("Helvetica", 12, "bold"), bg="black", fg="white", width=8, anchor="e")
            legend.grid(row=row, column=0, padx=(0, 4), pady=0)
            row_labels = []
            for col in range(4):
                value = self.card_stats[col][stat]
                val_lbl = tk.Label(stats_frame, text=str(value), font=("Helvetica", 12), bg="black", fg="white", width=card_width//10, anchor="center")
                val_lbl.grid(row=row, column=col+1, padx=2, pady=0, sticky="nsew")
                row_labels.append(val_lbl)
            self.stats_value_labels.append(row_labels)

        # Ajuste o grid para expandir igualmente
        for col in range(1, 5):
            stats_frame.grid_columnconfigure(col, weight=1)
            cards_container.grid_columnconfigure(col-1, weight=1)

        # Barra fina da cor do jogador no fundo
        bottom_bar = tk.Frame(self, bg=bar_color, height=10)
        bottom_bar.pack(side="bottom", fill="x")

        # Estado inicial
        self.active_challenge = None  # Só pode haver 1 challenge ativo
        self.active_users = []        # Lista de users ativos (máx 4)
        self.max_users = 4


    def update_card_image(self):
        for i, lbl in enumerate(self.card_labels):
            idx = (self.card_idx + i) % len(self.cards)
            img = ImageTk.PhotoImage(Image.open(self.cards[idx]).resize((85,120)))
            lbl.config(image=img)
            lbl.image = img
            lbl.bind("<Button-1>", make_card_callback(self, self.cards[idx]))

    def prev_card(self):
        self.card_idx = (self.card_idx - 1) % len(self.cards)
        self.update_card_image()

    def next_card(self):
        self.card_idx = (self.card_idx + 1) % len(self.cards)
        self.update_card_image()

    def try_mostrar_carta(self, path):
        try:
            print("CLICOU!", path)
            idx = self.cards.index(path)
            mostrar_carta_fullscreen_root(self.master, path, selected_card_idx=idx)
        except Exception as ex:
            print("ERRO AO ABRIR FULLSCREEN:", ex)

    def activate_card(self, card_type, card_path):
        if card_type == "challenge":
            # Só pode haver 1 challenge ativo
            if self.active_challenge:
                self.discard_card(self.active_challenge)
            self.active_challenge = card_path
            self.show_card_active(card_path)
        elif card_type == "user":
            # Máximo de 4 users ativos
            if card_path not in self.active_users:
                if len(self.active_users) < self.max_users:
                    self.active_users.append(card_path)
                    self.show_card_active(card_path)
                else:
                    # Opcional: feedback ao jogador que já tem 4 users
                    print("Já tens 4 users ativos!")

    def discard_card(self, card_path):
        # Remove visualmente/desativa o challenge anterior
        pass

    def show_card_active(self, card_path):
        # Atualiza visualmente a carta como ativa
        pass

# Exemplo de uso isolado:
if __name__ == "__main__":
    root = tk.Tk()
    root.attributes("-fullscreen", True)  
    PlayerDashboard(root, player_color="green", saldo=1000, other_players=["red", "blue", "yellow"])
    check_gpio_key()
    root.mainloop()