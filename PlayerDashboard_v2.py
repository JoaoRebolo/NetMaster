import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import RPi.GPIO as GPIO

IMG_DIR = os.path.join(os.path.dirname(__file__), "img")
LOGO_IMG = os.path.join(IMG_DIR, "logo_netmaster_icon_v3.png")
COIN_IMG = os.path.join(IMG_DIR, "picoin.png")
USER_ICONS = [
    os.path.join(IMG_DIR, "red_user_icon.png"),
    os.path.join(IMG_DIR, "green_user_icon.png"),
    os.path.join(IMG_DIR, "blue_user_icon.png"),
    os.path.join(IMG_DIR, "yellow_user_icon.png"),
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

def make_card_callback(parent, idx):
    def callback(event):
        # Remove destaque de todas as cartas
        for lbl in parent.card_labels:
            lbl.config(highlightthickness=0)
            lbl.selected = False
        # Destaca a carta clicada
        clicked_label = event.widget
        clicked_label.config(highlightbackground="#8000FF", highlightcolor="#8000FF", highlightthickness=4)
        clicked_label.selected = True
        parent.selected_card_idx = idx
        parent.update_progress_bars_for_card(idx)
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

        # Definir bar_color para botões e barra inferior
        color_map = {
            "green": "#70AD47",
            "yellow": "#F2BA0D",
            "red": "#EE6F68",
            "blue": "#43BEF2"
        }
        self.bar_color = color_map.get(player_color.lower(), "#AAAAAA")

        self.selected_card_idx = selected_card_idx

        bar_color = color_map.get(player_color.lower(), "#AAAAAA")

        # Barra superior com imagem
        topbar_img_path = os.path.join(IMG_DIR, f"TopBar_{player_color.lower()}.png")
        img = Image.open(topbar_img_path).convert("RGBA")
        img = img.resize((screen_width, 60), Image.LANCZOS)
        topbar_img = ImageTk.PhotoImage(img)
        self.topbar_label = tk.Label(self, image=topbar_img, bg="black", borderwidth=0, highlightthickness=0)
        self.topbar_label.image = topbar_img
        self.topbar_label.pack(side="top", fill="x")


        # Ícones dos outros jogadores (esquerda)
        for idx, p in enumerate(other_players):
            if idx < len(USER_ICONS):
                icon_img = ImageTk.PhotoImage(Image.open(USER_ICONS[idx]).resize((30,30)))
                lbl = tk.Label(self, image=icon_img, bg=self.bar_color)
                lbl.image = icon_img
                lbl.place(x=5+idx*40, y=20)

        # Nome do jogador (centro)
        name_lbl = tk.Label(self, text=player_name, font=("Helvetica", 18, "bold"), bg=self.bar_color, fg="black", borderwidth=0)
        name_lbl.place(relx=0.5, y=25, anchor="n")

        # Saldo (direita)
        coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24,24)))
        coin_lbl = tk.Label(self, image=coin_img, bg=self.bar_color, borderwidth=0)
        coin_lbl.image = coin_img
        coin_lbl.place(x=screen_width-100, y=30)
        saldo_lbl = tk.Label(self, text=f"{saldo}", font=("Helvetica", 16, "bold"), bg=self.bar_color, fg="black", borderwidth=0)
        saldo_lbl.place(x=screen_width-70, y=30)

        # --- NOVO LAYOUT ---

        # Espaço extra antes dos botões
        self.after(0, lambda: self.update())  # Garante update do layout antes de calcular altura
        tk.Frame(self, height=20, bg="black").pack()  # aumenta o height para mais espaço

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
            lbl.bind("<Button-1>", make_card_callback(self, idx))
            if idx == self.selected_card_idx:
                lbl.config(highlightbackground="#8000FF", highlightcolor="#8000FF", highlightthickness=4)
                lbl.selected = True
            else:
                lbl.config(highlightthickness=0)
                lbl.selected = False
            self.card_labels.append(lbl)
            
                # Frame para as barras de progresso
        self.progress_frame = tk.Frame(self, bg="black")
        self.progress_frame.pack(pady=(10, 0))

        self.progress_bars = {}
        self.progress_labels = {}

        stats = ["To send", "Rxd", "Lost"]
        for i, stat in enumerate(stats):
            row = tk.Frame(self.progress_frame, bg="black")
            row.pack(fill="x", pady=2)
            # Label do nome da stat à esquerda
            stat_lbl = tk.Label(row, text=stat, font=("Helvetica", 12, "bold"), bg="black", fg="white", width=8, anchor="w")
            stat_lbl.pack(side="left")
            # Barra de progresso
            bar = ttk.Progressbar(row, orient="horizontal", length=240, mode="determinate", maximum=10)
            bar.pack(side="left", fill="x", expand=True, padx=(4, 4))
            self.progress_bars[stat] = bar
            # Label do valor à direita da barra
            value_lbl = tk.Label(row, text="0", font=("Helvetica", 12, "bold"), bg="black", fg="white", width=2, anchor="e")
            value_lbl.pack(side="left", padx=(4, 0))
            self.progress_labels[stat] = value_lbl

        #Outra alternativa para mostrar os valores abaixo das cartas
        """ # --- Tabela de valores por baixo das cartas ---
        stats_frame = tk.Frame(self, bg="black")
        stats_frame.pack(pady=(4, 0))

        self.stats_value_labels = []  # <-- Adiciona esta linha ANTES do ciclo

        stats_labels = [("To send", "To\nsend"), ("Rxd", "Rxd"), ("Lost", "Lost")]

        for row, (stat_key, stat_label) in enumerate(stats_labels):
            legend = tk.Label(
                stats_frame,
                text=stat_label,
                font=("Helvetica", 12, "bold"),
                bg="black",
                fg="white",
                width=8,
                height=2 if "\n" in stat_label else 1,
                anchor="w"  # <-- Alinha o texto à esquerda dentro do label
            )
            # Espaçamento extra APÓS "To send"
            if stat_key == "To send":
                pady_val = (0, 6)
            elif stat_key == "Rxd":
                pady_val = (0, 6)
            else:
                pady_val = (0, 0)
            legend.grid(row=row, column=0, padx=(0,0), pady=pady_val, sticky="w")  # <-- Alinha o label à esquerda na célula
            row_labels = []
            for col in range(4):
                value = self.card_stats[col][stat_key]
                # Ajusta o deslocamento horizontal de cada coluna:
                if col == 0:
                    col_padx = (0, 4)   # Mais espaço à direita da primeira coluna
                elif col == 3:
                    col_padx = (6, 2)   # Mais espaço à esquerda da última coluna
                else:
                    col_padx = (4, 4)   # Espaço igual entre colunas intermédias

                val_lbl = tk.Label(
                    stats_frame,
                    text=str(value),
                    font=("Helvetica", 12),
                    bg="black",
                    fg="white",
                    width=card_width//10,
                    anchor="w"
                )
                val_lbl.grid(row=row, column=col+1, padx=col_padx, pady=pady_val, sticky="w")
                row_labels.append(val_lbl)
            self.stats_value_labels.append(row_labels)

        # Ajuste o grid para expandir igualmente
        for col in range(1, 5):
            stats_frame.grid_columnconfigure(col, weight=1)
            cards_container.grid_columnconfigure(col-1, weight=1) """

        # Barra fina da cor do jogador no fundo
        bottom_bar = tk.Frame(self, bg=bar_color, height=10)
        bottom_bar.pack(side="bottom", fill="x")

        # Estado inicial
        self.active_challenge = None  # Só pode haver 1 challenge ativo
        self.active_users = []        # Lista de users ativos (máx 4)
        self.max_users = 4

    def update_progress_bars_for_card(self, card_idx):
        stats = self.card_stats[card_idx]
        for stat in ["To send", "Rxd", "Lost"]:
            value = stats[stat]
            self.progress_bars[stat]["value"] = value
            self.progress_labels[stat]["text"] = str(value)

        # Chama isto sempre que muda a carta selecionada:
        self.update_progress_bars_for_card(self.selected_card_idx)

    def update_card_image(self):
        for i, lbl in enumerate(self.card_labels):
            idx = (self.card_idx + i) % len(self.cards)
            img = ImageTk.PhotoImage(Image.open(self.cards[idx]).resize((85,120)))
            lbl.config(image=img)
            lbl.image = img
            lbl.bind("<Button-1>", make_card_callback(self, idx))

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

    def update_progress_bars_for_card(self, card_idx):
        stats = self.card_stats[card_idx]
        for stat in ["To send", "Rxd", "Lost"]:
            value = stats[stat]
            self.progress_bars[stat]["value"] = value
            self.progress_labels[stat]["text"] = str(value)

# Exemplo de uso isolado:
if __name__ == "__main__":
    root = tk.Tk()
    root.attributes("-fullscreen", True)  
    PlayerDashboard(root, player_color="green", saldo=1000, other_players=["red", "blue", "yellow"])
    check_gpio_key()
    root.mainloop()