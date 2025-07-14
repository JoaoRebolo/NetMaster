import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import RPi.GPIO as GPIO
import random
from Store_v2 import StoreWindow

IMG_DIR = os.path.join(os.path.dirname(__file__), "img")
COIN_IMG = os.path.join(IMG_DIR, "picoin.png")
USER_ICONS = [
    os.path.join(IMG_DIR, "red_user_icon.png"),
    os.path.join(IMG_DIR, "green_user_icon.png"),
    os.path.join(IMG_DIR, "blue_user_icon.png"),
    os.path.join(IMG_DIR, "yellow_user_icon.png"),
]

CARD_IMG = os.path.join(IMG_DIR, "cartas", "back_card.png")

# GPIO setup para botão KEY1
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
    ("activities", "red"),      # 5
    ("events", "neutral"),     # 6 (cinzento)
    ("services", "red"),       # 7

    # Right column (top to bottom)
    ("start", "neutral"),      # 8 canto vermelho
    ("users", "red"),          # 9
    ("actions", "neutral"),     # 10 (cinzento)
    ("equipment", "red"),      # 11
    ("challenges", "neutral"), # 12 (cinzento)
    ("activities", "yellow"),   # 13
    ("events", "neutral"),     # 14 (cinzento)
    ("services", "yellow"),    # 15

    # Bottom row (right to left)
    ("start", "neutral"),      # 16 canto amarelo
    ("users", "yellow"),       # 17
    ("actions", "neutral"),     # 18 (cinzento)
    ("equipment", "yellow"),   # 19
    ("challenges", "neutral"), # 20 (cinzento)
    ("activities", "green"),    # 21
    ("events", "neutral"),     # 22 (cinzento)
    ("services", "green"),     # 23

    # Left column (bottom to top)
    ("start", "neutral"),      # 24 canto verde
    ("users", "green"),        # 25
    ("actions", "neutral"),     # 26 (cinzento)
    ("equipment", "green"),    # 27
    ("challenges", "neutral"), # 28 (cinzento)
    ("activities", "blue"),     # 29
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

def check_gpio_key(root):
    if GPIO.input(KEY1_PIN) == GPIO.LOW:
        GPIO.cleanup()
        root.destroy()
    root.after(100, lambda: check_gpio_key(root))
    
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
    pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    carta_img = ImageTk.PhotoImage(pil_img)
    carta_real_lbl = tk.Label(root, image=carta_img, bg="black")
    carta_real_lbl.image = carta_img  # type: ignore[attr-defined]
    carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center")

    # Botão de fechar (X)
    x_img_path = os.path.join(os.path.dirname(__file__), "img", "X_button.png")
    x_img = ImageTk.PhotoImage(Image.open(x_img_path).resize((48, 48)))
    x_btn = tk.Label(root, image=x_img, cursor="hand2", bg="black")
    x_btn.image = x_img  # type: ignore[attr-defined]
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
            # lbl.selected = False  # Removido para linter
        # Destaca a carta clicada
        clicked_label = event.widget
        clicked_label.config(highlightbackground="#8000FF", highlightcolor="#8000FF", highlightthickness=4)
        # clicked_label.selected = True  # Removido para linter
        parent.selected_label = clicked_label # Adicionado para armazenar a referência
        parent.selected_card_idx = idx
        parent.update_progress_bars_for_card(idx)
    return callback

class PlayerDashboard(tk.Toplevel):
    def __init__(self, root, player_color, saldo, other_players, player_name="Player", selected_card_idx=0):
        super().__init__(root)
        self.player_color = player_color 
        self.player_pos = START_POSITIONS.get(self.player_color.lower(), 0)
        self.selected_card_idx = selected_card_idx
        self.progress_bars = {}
        self.title("")
        self.configure(bg="black")
        self.player_name = player_name
        self.saldo = saldo
        self.other_players = other_players
        self.card_idx = 0
        self.cards = [
        # Carrossel inicial: cartas viradas para baixo, cor do jogador
        os.path.join(IMG_DIR, "cartas", f"back_card_{self.player_color.lower()}.png"),
        os.path.join(IMG_DIR, "cartas", f"back_card_{self.player_color.lower()}.png"),
        os.path.join(IMG_DIR, "cartas", f"back_card_{self.player_color.lower()}.png"),
        os.path.join(IMG_DIR, "cartas", f"back_card_{self.player_color.lower()}.png"),
        ]
        self.card_stats = [
            {"To send": 0, "Rxd": 0, "Lost": 0},
            {"To send": 0, "Rxd": 0, "Lost": 0},
            {"To send": 0, "Rxd": 0, "Lost": 0},
            {"To send": 0, "Rxd": 0, "Lost": 0},
        ]
        
        self.inventario = {
            "users": [],
            "equipments": [],
            "services": [],
            "action": [],
            "events": [],
            "challenges": [],
            "activities": [],
        }

        # ADICIONA ISTO:
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.geometry(f"{screen_width}x{screen_height}+0+0")
        self.overrideredirect(True)
        self.attributes("-fullscreen", True)

        # Definir bar_color para botões e barra inferior
        color_map = {
            "green": "#70AD47",
            "yellow": "#F2BA0D",
            "red": "#EE6F68",
            "blue": "#43BEF2"
        }
        self.bar_color = color_map.get(self.player_color.lower(), "#AAAAAA")
        
        self.selected_card_idx = selected_card_idx
        self.store_window = None
        # Cartas de teste para o inventário
        test_img_dir = os.path.join(os.path.dirname(__file__), "img", "cartas")
        # Adiciona 4 cartas normais + 2 cartas extra de Activities e Challenges para testar as setas
        for tipo in ["users", "equipments", "services", "action", "events", "challenges", "activities"]:
            pasta = os.path.join(test_img_dir, tipo)
            if os.path.exists(pasta):
                imgs = [os.path.join(pasta, f) for f in os.listdir(pasta) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if tipo in ["activities", "challenges"]:
                    # Adiciona 4 primeiras cartas normalmente
                    for img in imgs[:4]:
                        self.inventario[tipo].append(img)
                    # Adiciona mais 2 cartas extra se existirem
                    # for img in imgs[4:6]:
                    #     self.inventario[tipo].append(/home/joao_rebolo/netmaster_menu/img/cartas/activities/Activity_1.png)
                    #     self.inventario[tipo].append(/home/joao_rebolo/netmaster_menu/img/cartas/activities/Activity_5.png)
                    
                    self.inventario[tipo].append('/home/joao_rebolo/netmaster_menu/img/cartas/activities/Activity_1.png')
                    self.inventario[tipo].append('/home/joao_rebolo/netmaster_menu/img/cartas/activities/Activity_5.png')    
                else:
                    for img in imgs[:2]:
                        self.inventario[tipo].append(img)

        # --- BARRA SUPERIOR COM IMAGEM ---
        topbar_img_path = os.path.join(IMG_DIR, f"TopBar_{self.player_color.lower()}.png")
        img = Image.open(topbar_img_path).convert("RGBA")
        img = img.resize((screen_width, 60), Image.Resampling.LANCZOS)
        topbar_img = ImageTk.PhotoImage(img)
        self.topbar_label = tk.Label(self, image=topbar_img, bg="black", borderwidth=0, highlightthickness=0)
        self.topbar_label.image = topbar_img  # type: ignore[attr-defined]
        self.topbar_label.pack(side="top", fill="x")

        # Chama a tela de lançamento de dado
        self.show_dice_roll_screen(player_name, saldo, other_players, screen_width, screen_height)

    def animate_typing(self, label, text, delay=50, callback=None):
        def _type(i=0):
            if i <= len(text):
                label.config(text=text[:i])
                label.after(delay, _type, i + 1)
            elif callback:
                callback()
        _type()

    def show_dice_roll_screen(self, player_name, saldo, other_players, screen_width, screen_height):
        # Limpa widgets abaixo da barra superior
        for widget in self.winfo_children():
            if widget != self.topbar_label:
                widget.destroy()

        # Nome do jogador (centro)
        name_lbl = tk.Label(self, text=player_name, font=("Helvetica", 18, "bold"), fg="black", bg=self.bar_color)
        name_lbl.place(relx=0.5, y=25, anchor="n")

        # Saldo (direita)
        coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24,24)))
        coin_lbl = tk.Label(self, image=coin_img, bg=self.bar_color, borderwidth=0)
        coin_lbl.image = coin_img
        coin_lbl.place(x=screen_width-100, y=30)
        saldo_lbl = tk.Label(self, text=f"{saldo}", font=("Helvetica", 16, "bold"), fg="black", bg=self.bar_color)
        saldo_lbl.place(x=screen_width-70, y=30)

        # Ícones dos outros jogadores (esquerda)
        for idx, p in enumerate(other_players):
            if idx < len(USER_ICONS):
                icon_img = ImageTk.PhotoImage(Image.open(USER_ICONS[idx]).resize((30,30)))
                lbl = tk.Label(self, image=icon_img, bg=self.bar_color)
                lbl.image = icon_img  # type: ignore[attr-defined]
                lbl.place(x=5+idx*40, y=20)

        # Frame central para o dado e frases
        center_frame = tk.Frame(self, bg="black")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        lbl1 = tk.Label(center_frame, text="", font=("Helvetica", 22, "bold"), bg="black", fg="white", wraplength=int(screen_width*0.8), justify="center")
        lbl1.pack(pady=(0, 10))
        lbl2 = tk.Label(center_frame, text="", font=("Helvetica", 18), bg="black", fg="white", wraplength=int(screen_width*0.8), justify="center")
        lbl2.pack(pady=(0, 30))

        dice_btn = None
        go_btn = None


        if not hasattr(self, "player_pos"):
            self.player_pos = START_POSITIONS.get(self.player_color.lower(), 0)
        player_pos = self.player_pos

        def after_texts():
            nonlocal dice_btn, go_btn
            blank_img_path = os.path.join(IMG_DIR, "dice", "Dice_blank.png")
            dice_img = ImageTk.PhotoImage(Image.open(blank_img_path).resize((100,100)))
            dice_btn = tk.Label(center_frame, image=dice_img, bg="black")
            dice_btn.image = dice_img  # type: ignore[attr-defined]
            dice_btn.pack(pady=20)

            go_btn = tk.Button(center_frame, text="Go!", font=("Helvetica", 16, "bold"), bg="#005c75", fg="white")

            def roll_animation():
                go_btn.pack_forget()
                frames = 25
                results = [random.randint(1,6) for _ in range(frames)]
                final = random.randint(1,6)
                results.append(final)

                def animate(i=0,player_color=self.player_color):
                    
                    color_map = {
                    "green": "#70AD47",
                    "yellow": "#F2BA0D",
                    "red": "#EE6F68",
                    "blue": "#43BEF2"
                    }
                    
                    self.bar_color = color_map.get(player_color.lower(), "#AAAAAA")
                    
                    if i < len(results):
                        n = results[i]
                        img_path = os.path.join(IMG_DIR, "dice", f"Dice_{n}.png")
                        img = ImageTk.PhotoImage(Image.open(img_path).resize((100,100)))
                        dice_btn.config(image=img)
                        dice_btn.image = img  # type: ignore[attr-defined]
                        center_frame.after(100, animate, i+1)
                    else:
                        img_path = os.path.join(IMG_DIR, "dice", f"Dice_{final}.png")
                        img = ImageTk.PhotoImage(Image.open(img_path).resize((100,100)))
                        dice_btn.config(image=img)
                        dice_btn.image = img  # type: ignore[attr-defined]

                        # Esconde as frases imediatamente
                        lbl1.pack_forget()
                        lbl2.pack_forget()

                        steps = final
                        old = self.player_pos
                        new_pos = (old + steps) % NUM_CASAS
                        tipo, casa_cor = BOARD[new_pos]
                        self.player_pos = new_pos

                        def mostrar_nome_casa(tipo, casa_cor):
                            # Esconde o dado só agora
                            dice_btn.pack_forget()
                            cor_map = {
                                "green": "#70AD47",
                                "yellow": "#F2BA0D",
                                "red": "#EE6F68",
                                "blue": "#43BEF2",
                                "neutral": "#AAAAAA"
                            }
                            cor = cor_map.get(casa_cor, "#FFFFFF")
                            # Corrigir nome 'equipment' para 'EQUIPMENTS'
                            nome_tipo = tipo.upper()
                            if nome_tipo == "EQUIPMENT":
                                nome_tipo = "EQUIPMENTS"
                            nome_lbl = tk.Label(center_frame, text=nome_tipo, font=("Helvetica", 22, "bold"), fg=cor, bg="black")
                            nome_lbl.pack(pady=10)

                            def depois_nome():
                                nome_lbl.pack_forget()
                                if casa_cor == self.player_color.lower() or casa_cor == "neutral":
                                    # Casa própria ou neutra - Store normal
                                    self.store_window = StoreWindow(self, self.player_color, player_name, saldo, casa_tipo=tipo, casa_cor=casa_cor, inventario=self.inventario, dashboard=self)
                                else:
                                    # Casa de outro jogador - mostra mensagem e depois Store apenas para venda
                                    other_player_lbl = tk.Label(center_frame, text="Square of other player", font=("Helvetica", 18, "bold"), fg="white", bg="black")
                                    other_player_lbl.pack(pady=10)
                                    
                                    def abrir_store_outro_jogador():
                                        other_player_lbl.pack_forget()
                                        # Para casa de outro jogador, sempre abre a Store mas com restrições
                                        self.store_window = StoreWindow(self, self.player_color, player_name, saldo, casa_tipo=tipo, casa_cor=casa_cor, inventario=self.inventario, dashboard=self, other_player_house=True)
                                        center_frame.destroy()
                                    
                                    # Espera 2 segundos e depois abre a Store
                                    center_frame.after(2000, abrir_store_outro_jogador)
                            
                            # Espera 2 segundos DEPOIS de mostrar o nome da casa
                            center_frame.after(2000, depois_nome)

                        # Espera 2 segundos ANTES de esconder o dado e mostrar o nome da casa
                        center_frame.after(2000, lambda: mostrar_nome_casa(tipo, casa_cor))

                animate()

            go_btn.config(command=roll_animation)
            go_btn.pack(pady=(0, 5))

        self.animate_typing(lbl1, "It's your turn!", delay=60,
            callback=lambda: self.animate_typing(lbl2, "Roll the dice to start your adventure.", delay=60, callback=after_texts)
        )
        
    def atualizar_carrossel(self):
        # Junta todas as cartas de Activities e Challenges do inventário, sem duplicar
        novas_cartas = []
        for tipo in ["activities", "challenges"]:
            novas_cartas += self.inventario.get(tipo, [])
        # Se não houver cartas, mostra backs
        if not novas_cartas:
            novas_cartas = [CARD_IMG] * 4
        self.cards = novas_cartas
        self.card_idx = 0
        self.selected_card_idx = 0

    def playerdashboard_interface(self, player_name, saldo, other_players):
        self.atualizar_carrossel()
        # Limpar todos os widgets existentes (exceto a barra superior se existir)
        for widget in self.winfo_children():
            if hasattr(self, 'topbar_label') and widget == self.topbar_label:
                continue  # Manter a barra superior
            widget.destroy()
        
        # Barra superior com imagem
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}+0+0")
        self.overrideredirect(True)  # Remove barra de título
        self.attributes("-fullscreen", True)  # Garante fullscreen (opcional)
        
        # Ícones dos outros jogadores (esquerda)
        for idx, p in enumerate(other_players):
            if idx < len(USER_ICONS):
                icon_img = ImageTk.PhotoImage(Image.open(USER_ICONS[idx]).resize((30,30)))
                lbl = tk.Label(self, image=icon_img, bg=self.bar_color)
                lbl.image = icon_img  # type: ignore[attr-defined]
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
            ("Users", self.bar_color, "users"),
            ("Equip.", self.bar_color, "equipments"),
            ("Services", self.bar_color, "services"),
            ("Actions/\nEvents", self.bar_color, "actions_events")
        ]

        self.action_buttons = []
        for text, color, inv_key in btn_info:
            btn_font = ("Helvetica", 13, "bold")
            if text.startswith("Services"):
                btn_font = ("Helvetica", 12, "bold")  # Fonte menor só para "Services"
            btn = tk.Button(
                btns_frame, text=text, font=btn_font,
                wraplength=70,
                bg=color, fg="black", activebackground="white", activeforeground="black",
                bd=0, highlightthickness=0
            )
            btn.pack(side=tk.LEFT, padx=2, ipady=22, expand=True, fill="both")
            self.action_buttons.append(btn)
            # Associar inventário correto
            if inv_key == "actions_events":
                btn.config(command=lambda: self.show_inventory_matrix(["action", "events"]))
            else:
                btn.config(command=lambda k=inv_key: self.show_inventory_matrix([k]))

        # 2. Carrossel de cartas (agora abaixo dos botões)
        carousel_frame = tk.Frame(self, bg="black")
        carousel_frame.pack(pady=2)
        cards_container = tk.Frame(carousel_frame, bg="black")
        cards_container.pack()

        card_width, card_height = 85, 120  # Certifique-se que está definido antes

        self.card_labels = []
        for i, carta_path in enumerate(self.cards):
            img = ImageTk.PhotoImage(Image.open(carta_path).resize((card_width, card_height)))
            lbl = tk.Label(cards_container, image=img, bg="black", cursor="hand2")
            lbl.image = img  # type: ignore[attr-defined]
            lbl.grid(row=0, column=i, padx=2, pady=0)
            # Se for carta virada para baixo, abre inventário de Activities/Challenges
            if os.path.basename(carta_path).startswith("back_card_"):
                lbl.bind("<Button-1>", lambda e, idx=i: self.abrir_inventario_para_carrossel(idx))
            else:
                lbl.bind("<Button-1>", lambda e, p=carta_path: self.show_card_fullscreen_carrossel(p))
            # lbl.selected = True  # Removido para linter
            # lbl.selected = False  # Removido para linter
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

        # Botão End Turn centralizado na parte inferior, menor
        end_turn_btn = tk.Button(self, text="End Turn", font=("Helvetica", 13, "bold"), bg="#8000FF", fg="white", command=self.end_turn, width=8, height=1)
        end_turn_btn.place(relx=0.5, rely=1, anchor="s")

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
            lbl.bind("<Button-1>", make_card_callback(self, self.cards[idx]))

    def prev_card(self):
        self.card_idx = (self.card_idx - 1) % len(self.cards)
        self.update_card_image()

    def next_card(self):
        self.card_idx = (self.card_idx + 1) % len(self.cards)
        self.update_card_image()

    def add_progress_bar(self, parent, label, value):
        fr = tk.Frame(parent, bg="black")
        fr.pack(pady=2, anchor="w", fill="x", expand=True)
        tk.Label(fr, text=label, font=("Helvetica", 14), bg="black", fg="white", width=8, anchor="w").pack(side=tk.LEFT)
        pb = ttk.Progressbar(fr, length=160, maximum=10, value=value)
        pb.pack(side=tk.LEFT, padx=8, fill="x", expand=True)
        value_lbl = tk.Label(fr, text=str(value), font=("Helvetica", 14), bg="black", fg="white", width=2)
        value_lbl.pack(side=tk.LEFT)
        self.progress_bars[label] = pb  # Guarda referência
        if not hasattr(self, "progress_labels"):
            self.progress_labels = {}
        self.progress_labels[label] = value_lbl  # Guarda referência à label do valor

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

    def adicionar_carta_inventario(self, carta_path, carta_tipo):
        if carta_tipo in self.inventario:
            self.inventario[carta_tipo].append(carta_path)

    def show_inventory_page(self, carta_tipo):
        # Limpa widgets (menos barra superior)
        for widget in self.winfo_children():
            if widget == self.topbar_label:
                continue
            widget.destroy()

        screen_width = self.winfo_screenwidth()
        # Título
        title = tk.Label(self, text=carta_tipo.capitalize(), font=("Helvetica", 22, "bold"),
                         fg="black", bg=self.bar_color)
        title.place(relx=0.5, y=65, anchor="n")

        # Mostra as cartas desse tipo
        cartas = self.inventario.get(carta_tipo, [])
        if cartas:
            carta_path = cartas[-1]  # Mostra a última carta tirada
            img = ImageTk.PhotoImage(Image.open(carta_path).resize((180, 260)))
            carta_lbl = tk.Label(self, image=img, bg="black", cursor="hand2")
            carta_lbl.image = img  # type: ignore[attr-defined]
            carta_lbl.place(relx=0.5, rely=0.4, anchor="center")

            def abrir_fullscreen(event=None):
                self.show_card_fullscreen(carta_path, carta_tipo)
            carta_lbl.bind("<Button-1>", abrir_fullscreen)
        else:
            tk.Label(self, text="Sem cartas!", font=("Helvetica", 16), bg="black", fg="white").place(relx=0.5, rely=0.5, anchor="center")

        # Botão seta para voltar
        seta_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "arrow_left.png")).resize((48, 48)))
        seta_btn = tk.Button(
            self,
            image=seta_img,
            bg="black",
            borderwidth=0,
            command=lambda: self.show_dice_roll_screen(
                self.player_name,
                self.saldo,
                self.other_players,
                self.screen_width,
                self.screen_height
            )
        )
        seta_btn.image = seta_img  # type: ignore[attr-defined]
        seta_btn.place(x=10, rely=0.9*self.winfo_screenheight(), anchor="sw")

    def show_card_fullscreen(self, carta_path, carta_tipo):
        print("DEBUG: PlayerDashboard.show_card_fullscreen chamado")
        # Limpa widgets (menos barra superior)
        for widget in self.winfo_children():
            if widget == self.topbar_label:
                continue
            widget.destroy()

        pil_img = Image.open(carta_path)
        img_w, img_h = pil_img.size
        max_w, max_h = self.winfo_screenwidth(), self.winfo_screenheight()
        ratio = min(max_w/img_w, max_h/img_h)
        new_w, new_h = int(img_w*ratio), int(img_h*ratio)
        pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        carta_img = ImageTk.PhotoImage(pil_img)
        carta_real_lbl = tk.Label(self, image=carta_img, bg="black")
        carta_real_lbl.image = carta_img  # type: ignore[attr-defined]
        carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Botão X para fechar
        x_img_path = os.path.join(IMG_DIR, "X_button.png")
        x_img = ImageTk.PhotoImage(Image.open(x_img_path).resize((48, 48)))
        x_btn = tk.Label(self, image=x_img, bg="black", cursor="hand2")
        x_btn.image = x_img  # type: ignore[attr-defined]
        x_btn.place(relx=0.98, rely=0.02, anchor="ne")

        def fechar():
            # Limpa tudo menos a barra superior
            for widget in self.winfo_children():
                if widget == self.topbar_label:
                    continue
                widget.destroy()
            # Redesenha a interface principal
            self.playerdashboard_interface(self.player_name, self.saldo, self.other_players)

        x_btn.bind("<Button-1>", lambda e: fechar())

    def end_turn(self):
        # Placeholder: lógica para terminar o turno e passar ao próximo jogador
        # Aqui pode-se implementar a lógica de alternância de jogador
        import tkinter.messagebox
        tkinter.messagebox.showinfo("End Turn", "Turno terminado! Próximo jogador...")
        # Exemplo: pode-se limpar a interface ou chamar uma função para o próximo jogador

    def show_inventory_matrix(self, tipos, page=0):
        # Limpa widgets (menos barra superior)
        for widget in self.winfo_children():
            if widget == self.topbar_label:
                continue
            widget.destroy()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        # --- Nome do jogador, saldo e picoin ---
        name_lbl = tk.Label(self, text=self.player_name, font=("Helvetica", 18, "bold"), bg=self.bar_color, fg="black", borderwidth=0)
        name_lbl.place(relx=0.5, y=25, anchor="n")
        coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24,24)))
        coin_lbl = tk.Label(self, image=coin_img, bg=self.bar_color, borderwidth=0)
        coin_lbl.image = coin_img  # type: ignore[attr-defined]
        coin_lbl.place(x=screen_width-100, y=30)
        saldo_lbl = tk.Label(self, text=f"{self.saldo}", font=("Helvetica", 16, "bold"), bg=self.bar_color, fg="black", borderwidth=0)
        saldo_lbl.place(x=screen_width-70, y=30)
        # Título
        if len(tipos) == 1:
            title_str = tipos[0].capitalize()
        else:
            title_str = "Actions / Events"
        title = tk.Label(self, text=title_str, font=("Helvetica", 22, "bold"), fg="white", bg="black")
        title.place(relx=0.5, y=65, anchor="n")
        # Junta todas as cartas dos tipos
        cartas = []
        for t in tipos:
            cartas += self.inventario.get(t, [])
        # Paginação igual ao Activities/Challenges
        cards_per_page = 4
        total_pages = max(1, (len(cartas) + cards_per_page - 1) // cards_per_page)
        page = max(0, min(page, total_pages - 1))
        start_idx = page * cards_per_page
        end_idx = start_idx + cards_per_page
        cartas_page = cartas[start_idx:end_idx]
        matriz_frame = tk.Frame(self, bg="black")
        matriz_frame.place(relx=0.5, rely=0.5, anchor="center")
        n_col = 2
        card_w, card_h = 85, 120  # Igual ao Activities/Challenges
        for idx, carta_path in enumerate(cartas_page):
            row = idx // n_col
            col = idx % n_col
            try:
                img = ImageTk.PhotoImage(Image.open(carta_path).resize((card_w, card_h)))
            except Exception:
                continue
            carta_lbl = tk.Label(matriz_frame, image=img, bg="black", cursor="hand2")
            carta_lbl.image = img  # type: ignore[attr-defined]
            carta_lbl.grid(row=row, column=col, padx=8, pady=8)
            carta_lbl.bind("<Button-1>", lambda e, p=carta_path, t=tipos: self.show_card_fullscreen_inventory(p, t))
        # Setas de navegação à direita
        if total_pages > 1:
            seta_x = 0.90
            if page > 0:
                seta_cima = tk.Button(self, text="▲", font=("Helvetica", 18, "bold"), bg="#222", fg="white", width=2, command=lambda: self.show_inventory_matrix(tipos, page-1))
                seta_cima.place(relx=seta_x, rely=0.38, anchor="center")
            if page < total_pages - 1:
                seta_baixo = tk.Button(self, text="▼", font=("Helvetica", 18, "bold"), bg="#222", fg="white", width=2, command=lambda: self.show_inventory_matrix(tipos, page+1))
                seta_baixo.place(relx=seta_x, rely=0.62, anchor="center")
        # Botão Back centrado na parte inferior
        back_btn = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), bg="#005c75", fg="white", width=10, command=lambda: self.playerdashboard_interface(self.player_name, self.saldo, self.other_players))
        back_btn.place(relx=0.5, rely=0.98, anchor="s")

    def show_card_fullscreen_inventory(self, carta_path, tipos, page=0):
        # Limpa widgets (menos barra superior)
        for widget in self.winfo_children():
            if widget == self.topbar_label:
                continue
            widget.destroy()
        pil_img = Image.open(carta_path)
        img_w, img_h = pil_img.size
        max_w, max_h = self.winfo_screenwidth(), self.winfo_screenheight()
        ratio = min(max_w/img_w, max_h/img_h)
        new_w, new_h = int(img_w*ratio), int(img_h*ratio)
        pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        carta_img = ImageTk.PhotoImage(pil_img)
        carta_real_lbl = tk.Label(self, image=carta_img, bg="black", borderwidth=0, highlightthickness=0)
        carta_real_lbl.image = carta_img  # type: ignore[attr-defined]
        carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)
        # Botão X para fechar
        def voltar_inventario():
            # Se for inventário de Activities/Challenges, volta para show_inventory_matrix_carrossel
            if set(tipos) == set(["activities", "challenges"]):
                self.show_inventory_matrix_carrossel(tipos, page)
            else:
                self.show_inventory_matrix(tipos, page)
        x_btn = tk.Button(self, text="✖", font=("Helvetica", 24, "bold"), bg="#AAAAAA", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=voltar_inventario, cursor="hand2", activebackground="#CCCCCC")
        x_btn.place(relx=0.98, rely=0, anchor="ne")
        # Se for Users, Equipments ou Services, mostrar botão piccoin para vender
        if len(tipos) == 1 and tipos[0] in ["users", "equipments", "services"]:
            picoin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((48,48)))
            def abrir_confirm():
                self.show_sell_confirmation(carta_path, tipos[0], store_window=None)
            btn_picoin = tk.Button(self, image=picoin_img, bg="#4CAF50", borderwidth=0, command=abrir_confirm, cursor="hand2")
            btn_picoin.image = picoin_img  # type: ignore[attr-defined]
            btn_picoin.place(relx=1, rely=1, anchor="se")

    def show_inventory_for_sell(self, carta_tipo, store_window=None):
        print(f"DEBUG: show_inventory_for_sell chamado - carta_tipo: {carta_tipo}")
        
        # Garantir que a janela está visível e no estado correto
        self.deiconify()
        self.state('normal')  # Garantir que não está minimizada
        self.lift()
        self.focus_force()
        
        # Garantir que a Store está escondida
        if store_window and hasattr(store_window, 'withdraw'):
            store_window.withdraw()
        
        # Limpa widgets (menos barra superior)
        for widget in self.winfo_children():
            if widget == self.topbar_label:
                continue
            widget.destroy()
        
        # Força update para garantir que a limpeza foi feita
        self.update_idletasks()
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # --- Nome do jogador, saldo e picoin ---
        name_lbl = tk.Label(self, text=self.player_name, font=("Helvetica", 18, "bold"), bg=self.bar_color, fg="black", borderwidth=0)
        name_lbl.place(relx=0.5, y=25, anchor="n")
        coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24,24)))
        coin_lbl = tk.Label(self, image=coin_img, bg=self.bar_color, borderwidth=0)
        coin_lbl.image = coin_img
        coin_lbl.place(x=screen_width-100, y=30)
        saldo_lbl = tk.Label(self, text=f"{self.saldo}", font=("Helvetica", 16, "bold"), bg=self.bar_color, fg="black", borderwidth=0)
        saldo_lbl.place(x=screen_width-70, y=30)
        
        # Título
        title = tk.Label(self, text=carta_tipo.capitalize(), font=("Helvetica", 22, "bold"), fg="white", bg="black")
        title.place(relx=0.5, y=65, anchor="n")
        
        # Cartas do tipo
        cartas = self.inventario.get(carta_tipo, [])
        print(f"DEBUG: Cartas encontradas no inventário: {len(cartas)}")
        
        # Recria o frame para as cartas
        matriz_frame = tk.Frame(self, bg="black")
        matriz_frame.place(relx=0.5, rely=0.5, anchor="center")
        n_col = 4
        card_w, card_h = 110, 160
        self._sell_imgs = []
        
        def make_fullscreen_callback(carta_path):
            def callback(event=None):
                print(f"DEBUG: Carta clicada para venda: {carta_path}")
                # Verificar se a Store está disponível
                if store_window and hasattr(store_window, 'iniciar_venda_carta'):
                    print("DEBUG: Delegando para Store.iniciar_venda_carta")
                    # Garantir que a Store está no estado correto
                    if hasattr(store_window, 'winfo_exists') and store_window.winfo_exists():
                        store_window.deiconify()
                        store_window.state('normal')
                        store_window.lift()
                        store_window.focus_force()
                        # Esconder o PlayerDashboard temporariamente
                        self.withdraw()
                        # Aguardar um pouco para garantir que a Store está pronta
                        self.after(100, lambda: store_window.iniciar_venda_carta(carta_path, carta_tipo, self))
                    else:
                        print("DEBUG: Store window não existe mais")
                        self.show_card_fullscreen_sell(carta_path, carta_tipo, store_window)
                else:
                    print("DEBUG: Store window não disponível, usando método local")
                    # Usar método local como fallback
                    self.show_card_fullscreen_sell(carta_path, carta_tipo, store_window)
            return callback
        
        for idx, carta_path in enumerate(cartas):
            try:
                img = ImageTk.PhotoImage(Image.open(carta_path).resize((card_w, card_h)))
                self._sell_imgs.append(img)
            except Exception as e:
                print(f"DEBUG: Erro ao carregar carta {carta_path}: {e}")
                continue
            carta_lbl = tk.Label(matriz_frame, image=img, bg="black", cursor="hand2")
            carta_lbl.image = img  # type: ignore[attr-defined]
            carta_lbl.grid(row=idx//n_col, column=idx%n_col, padx=8, pady=8)
            carta_lbl.bind("<Button-1>", make_fullscreen_callback(carta_path))
        
        if not cartas:
            no_cards_lbl = tk.Label(matriz_frame, text="Sem cartas disponíveis!", font=("Helvetica", 16), bg="black", fg="white")
            no_cards_lbl.pack(pady=20)
        
        # Força update final para garantir que tudo é exibido
        self.update_idletasks()
        self.update()
        
        # Botão voltar
        if store_window:
            def voltar_para_store():
                print("DEBUG: PlayerDashboard voltar_para_store chamado")
                try:
                    # Primeiro, esconde o PlayerDashboard
                    print("DEBUG: Escondendo PlayerDashboard...")
                    self.withdraw()
                    
                    # Aguarda um pouco para garantir que foi escondido
                    print("DEBUG: Aguardando para processar volta à Store...")
                    self.after(100, lambda: self._process_back_to_store(store_window))
                    
                except Exception as e:
                    print(f"DEBUG: Erro ao iniciar volta para store: {e}")
                    import traceback
                    traceback.print_exc()
                    
            def _process_back_to_store(store_window):
                print("DEBUG: Processando volta à Store...")
                try:
                    # Verificar se a Store ainda existe
                    if hasattr(store_window, 'winfo_exists') and store_window.winfo_exists():
                        print("DEBUG: Store existe, forçando exibição...")
                        # Força a Store a aparecer
                        store_window.deiconify()
                        store_window.state('normal')
                        store_window.lift()
                        store_window.focus_force()
                        
                        # Aguarda um pouco e depois reconstrói
                        print("DEBUG: Chamando voltar_para_store da Store...")
                        store_window.after(50, lambda: store_window.voltar_para_store())
                        
                    else:
                        print("DEBUG: Store não existe mais, voltando ao PlayerDashboard")
                        self.deiconify()
                        self.lift()
                        self.focus_force()
                        self.playerdashboard_interface(self.player_name, self.saldo, self.other_players)
                        
                except Exception as e:
                    print(f"DEBUG: Erro ao processar volta à Store: {e}")
                    import traceback
                    traceback.print_exc()
                    # Em caso de erro, volta ao PlayerDashboard
                    try:
                        self.deiconify()
                        self.lift()
                        self.focus_force()
                        self.playerdashboard_interface(self.player_name, self.saldo, self.other_players)
                    except Exception as fallback_e:
                        print(f"DEBUG: Erro crítico no fallback: {fallback_e}")
            
            # Adiciona o método auxiliar à instância
            self._process_back_to_store = _process_back_to_store
            btn_voltar = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), bg="#005c75", fg="white", width=10, command=voltar_para_store)
            btn_voltar.place(relx=0.5, rely=0.98, anchor="s")
        else:
            btn_voltar = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), bg="#005c75", fg="white", width=10, command=lambda: self.playerdashboard_interface(self.player_name, self.saldo, self.other_players))
            btn_voltar.place(relx=0.5, rely=0.98, anchor="s")
        
        print("DEBUG: show_inventory_for_sell terminado com sucesso")

    def show_card_fullscreen_sell(self, carta_path, carta_tipo, store_window=None):
        # Limpa widgets (menos barra superior)
        for widget in self.winfo_children():
            if widget == self.topbar_label:
                continue
            widget.destroy()
        pil_img = Image.open(carta_path)
        img_w, img_h = pil_img.size
        max_w, max_h = self.winfo_screenwidth(), self.winfo_screenheight()
        ratio = min(max_w/img_w, max_h/img_h)
        new_w, new_h = int(img_w*ratio), int(img_h*ratio)
        pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        carta_img = ImageTk.PhotoImage(pil_img)
        carta_real_lbl = tk.Label(self, image=carta_img, bg="black", borderwidth=0, highlightthickness=0)
        carta_real_lbl.image = carta_img  # type: ignore[attr-defined]
        carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)
        # Botão piccoin canto inferior direito
        picoin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((48,48)))
        def abrir_confirm():
            self.show_sell_confirmation(carta_path, carta_tipo, store_window)
        btn_picoin = tk.Button(self, image=picoin_img, bg="#4CAF50", borderwidth=0, command=abrir_confirm, cursor="hand2")
        btn_picoin.image = picoin_img  # type: ignore[attr-defined]
        btn_picoin.place(relx=1, rely=1, anchor="se")
        # Botão X para fechar
        x_img_path = os.path.join(IMG_DIR, "X_button.png")
        x_img = ImageTk.PhotoImage(Image.open(x_img_path).resize((48, 48)))
        x_btn = tk.Label(self, image=x_img, bg="black", cursor="hand2")
        x_btn.image = x_img  # type: ignore[attr-defined]
        x_btn.place(relx=0.98, rely=0.02, anchor="ne")
        def fechar():
            self.show_inventory_for_sell(carta_tipo, store_window)
        x_btn.bind("<Button-1>", lambda e: fechar())

    def show_sell_confirmation(self, carta_path, carta_tipo, store_window=None):
        import os
        import tkinter.messagebox
        # Limpa widgets (menos barra superior)
        for widget in self.winfo_children():
            if widget == self.topbar_label:
                continue
            widget.destroy()
        screen_width = self.winfo_screenwidth()
        # Barra superior do jogador
        name_lbl = tk.Label(self, text=self.player_name, font=("Helvetica", 18, "bold"), bg=self.bar_color, fg="black", borderwidth=0)
        name_lbl.place(relx=0.5, y=25, anchor="n")
        coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24,24)))
        coin_lbl = tk.Label(self, image=coin_img, bg=self.bar_color, borderwidth=0)
        coin_lbl.image = coin_img
        coin_lbl.place(x=screen_width-100, y=30)
        saldo_lbl = tk.Label(self, text=f"{self.saldo}", font=("Helvetica", 16, "bold"), bg=self.bar_color, fg="black", borderwidth=0)
        saldo_lbl.place(x=screen_width-70, y=30)
        # Frame central para frase e botões
        confirm_frame = tk.Frame(self, bg="black")
        confirm_frame.pack(expand=True)
        tk.Label(confirm_frame, text="Are you sure you want to sell?", font=("Helvetica", 16, "bold"), fg="white", bg="black").pack(pady=(40, 20))
        tk.Label(confirm_frame, text=f"Your balance: {self.saldo}", font=("Helvetica", 16), fg="yellow", bg="black").pack(pady=(0, 10))
        # Valor da carta
        valor = self._extrair_valor_carta(carta_path) if hasattr(self, '_extrair_valor_carta') else None
        if valor is None:
            try:
                import re
                nome = os.path.basename(carta_path)
                match = re.search(r'_(\d+)\.', nome)
                if match:
                    valor = int(match.group(1))
            except Exception:
                valor = 0
        value_frame = tk.Frame(confirm_frame, bg="black")
        value_frame.pack(pady=(0, 30))
        tk.Label(value_frame, text="Card value: ", font=("Helvetica", 16), fg="white", bg="black").pack(side="left")
        tk.Label(value_frame, text=str(valor), font=("Helvetica", 16, "bold"), fg="yellow", bg="black").pack(side="left")
        picoin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24,24)))
        picoin_lbl = tk.Label(value_frame, image=picoin_img, bg="black")
        picoin_lbl.image = picoin_img
        picoin_lbl.pack(side="left", padx=(4,0))
        btns_frame = tk.Frame(confirm_frame, bg="black")
        btns_frame.pack()
        def confirmar():
            print("DEBUG: Confirmar venda - início")
            try:
                # Atualiza saldos
                if valor is not None:
                    self.saldo += valor
                    if store_window:
                        store_window.saldo -= valor
                        if hasattr(store_window, 'inventario') and carta_tipo in store_window.inventario:
                            store_window.inventario[carta_tipo].append(carta_path)
                if carta_tipo in self.inventario and carta_path in self.inventario[carta_tipo]:
                    self.inventario[carta_tipo].remove(carta_path)
                print(f"DEBUG: Venda confirmada - Player saldo: {self.saldo}")
                
                # REPLICAR EXATAMENTE A LÓGICA DA COMPRA: voltar ao PlayerDashboard e destruir Store
                # Volta imediatamente ao PlayerDashboard
                self.playerdashboard_interface(
                    self.player_name,
                    self.saldo,
                    self.other_players
                )
                
                # Em vez de destruir a Store, apenas a mostra e reconstrói
                if store_window:
                    try:
                        store_window.deiconify()
                        store_window.rebuild_store_interface()
                        store_window.lift()
                        store_window.focus_force()
                    except Exception as e:
                        print(f"DEBUG: ERRO ao reabrir Store: {e}")
                
            except Exception as e:
                print(f"DEBUG: ERRO na confirmação: {e}")
                import traceback
                traceback.print_exc()
        def cancelar():
            self.show_inventory_for_sell(carta_tipo, store_window)
        btn_yes = tk.Button(btns_frame, text="Yes", font=("Helvetica", 14, "bold"), bg="#4CAF50", fg="white", width=8, command=confirmar)
        btn_no = tk.Button(btns_frame, text="No", font=("Helvetica", 14, "bold"), bg="#F44336", fg="white", width=8, command=cancelar)
        btn_yes.pack(side="left", padx=20, pady=10)
        btn_no.pack(side="left", padx=20, pady=10)

    # Corrigir aceitação de carta Challenge/Activity para adicionar ao carrossel
    def aceitar_carta_challenge_activity(self, carta_path, carta_tipo):
        # Chamar isto ao aceitar uma carta Challenge/Activity
        self.adicionar_carta_carrossel(carta_path, carta_tipo)
        # ... resto do fluxo de aceitação ...
        self.playerdashboard_interface(self.player_name, self.saldo, self.other_players)

    # Corrigir fullscreen do carrossel: botão X volta sempre à interface principal
    def show_card_fullscreen_carrossel(self, carta_path):
        # Limpa widgets (menos barra superior)
        for widget in self.winfo_children():
            if widget == self.topbar_label:
                continue
            widget.destroy()
        pil_img = Image.open(carta_path)
        img_w, img_h = pil_img.size
        max_w, max_h = self.winfo_screenwidth(), self.winfo_screenheight()
        ratio = min(max_w/img_w, max_h/img_h)
        new_w, new_h = int(img_w*ratio), int(img_h*ratio)
        pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        carta_img = ImageTk.PhotoImage(pil_img)
        carta_real_lbl = tk.Label(self, image=carta_img, bg="black", borderwidth=0, highlightthickness=0)
        carta_real_lbl.image = carta_img  # type: ignore[attr-defined]
        carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)
        
        # Botão X para fechar
        def voltar_dashboard():
            self.playerdashboard_interface(self.player_name, self.saldo, self.other_players)
        x_btn = tk.Button(self, text="✖", font=("Helvetica", 24, "bold"), bg="#AAAAAA", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=voltar_dashboard, cursor="hand2", activebackground="#CCCCCC")
        x_btn.place(relx=0.98, rely=0, anchor="ne")
        
        # Botão de troca de carta no canto inferior direito
        try:
            switch_img_path = os.path.join(IMG_DIR, "switch_card.png")
            if os.path.exists(switch_img_path):
                switch_img = ImageTk.PhotoImage(Image.open(switch_img_path).resize((48, 48)))
                switch_btn = tk.Label(self, image=switch_img, bg="orange", cursor="hand2")
                switch_btn.image = switch_img  # type: ignore[attr-defined]
                switch_btn.place(relx=1, rely=1, anchor="se")
                
                def abrir_inventario_troca():
                    # Verificar se a carta atual não é uma carta virada para baixo
                    import os
                    if "back_card" in os.path.basename(carta_path).lower():
                        print("DEBUG: Não é possível trocar uma carta virada para baixo")
                        return
                    
                    # Guardar a carta atual do carrossel para troca
                    self.carta_carrossel_para_troca = carta_path
                    # Encontrar o índice da carta no carrossel
                    try:
                        self.carrossel_idx_selecao = self.cards.index(carta_path)
                    except ValueError:
                        self.carrossel_idx_selecao = 0
                    self.show_inventory_matrix_carrossel(["activities", "challenges"])
                switch_btn.bind("<Button-1>", lambda e: abrir_inventario_troca())
            else:
                # Se a imagem não existir, usar um botão de texto
                switch_btn = tk.Button(self, text="⇄", font=("Helvetica", 18, "bold"), bg="#F9B407", fg="white", width=3, height=1, borderwidth=0, highlightthickness=0, cursor="hand2", activebackground="#66BB6A")
                switch_btn.place(relx=1, rely=1, anchor="se")
                
                def abrir_inventario_troca():
                    # Verificar se a carta atual não é uma carta virada para baixo
                    import os
                    if "back_card" in os.path.basename(carta_path).lower():
                        print("DEBUG: Não é possível trocar uma carta virada para baixo")
                        return
                    
                    # Guardar a carta atual do carrossel para troca
                    self.carta_carrossel_para_troca = carta_path
                    # Encontrar o índice da carta no carrossel
                    try:
                        self.carrossel_idx_selecao = self.cards.index(carta_path)
                    except ValueError:
                        self.carrossel_idx_selecao = 0
                    self.show_inventory_matrix_carrossel(["activities", "challenges"])
                switch_btn.config(command=abrir_inventario_troca)
        except Exception as e:
            print(f"DEBUG: Erro ao criar botão de troca: {e}")
            # Fallback para botão de texto simples
            switch_btn = tk.Button(self, text="⇄", font=("Helvetica", 18, "bold"), bg="#F9B407", fg="white", width=3, height=1, borderwidth=0, highlightthickness=0, cursor="hand2", activebackground="#66BB6A")
            switch_btn.place(relx=1, rely=1, anchor="se")
            
            def abrir_inventario_troca():
                # Verificar se a carta atual não é uma carta virada para baixo
                import os
                if "back_card" in os.path.basename(carta_path).lower():
                    print("DEBUG: Não é possível trocar uma carta virada para baixo")
                    return
                
                # Guardar a carta atual do carrossel para troca
                self.carta_carrossel_para_troca = carta_path
                # Encontrar o índice da carta no carrossel
                try:
                    self.carrossel_idx_selecao = self.cards.index(carta_path)
                except ValueError:
                    self.carrossel_idx_selecao = 0
                self.show_inventory_matrix_carrossel(["activities", "challenges"])
            switch_btn.config(command=abrir_inventario_troca)

    # --- Carrossel: começa vazio e só adiciona Activities/Challenges aceites ---
    def adicionar_carta_carrossel(self, carta_path, carta_tipo):
        if carta_tipo in ["activities", "challenges"] and carta_path not in self.carrossel:
            self.carrossel.append(carta_path)
            self.atualizar_carrossel()

    def atualizar_carrossel(self):
        # Atualiza o carrossel para mostrar apenas as cartas em self.carrossel
        # (Implementação depende do teu método atual, mas deve usar self.carrossel)
        pass

    # No método onde o jogador aceita uma carta de Activities ou Challenges:
    # Chamar self.adicionar_carta_carrossel(carta_path, carta_tipo)

    def abrir_inventario_para_carrossel(self, carrossel_idx):
        # Abre o inventário de Activities/Challenges para escolher carta para o carrossel
        self.carrossel_idx_selecao = carrossel_idx
        self.show_inventory_matrix_carrossel(["activities", "challenges"])

    def show_inventory_matrix_carrossel(self, tipos, page=0):
        # Inventário em grelha 2x2 com navegação por páginas
        for widget in self.winfo_children():
            if widget == self.topbar_label:
                continue
            widget.destroy()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        name_lbl = tk.Label(self, text=self.player_name, font=("Helvetica", 18, "bold"), bg=self.bar_color, fg="black", borderwidth=0)
        name_lbl.place(relx=0.5, y=25, anchor="n")
        coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24,24)))
        coin_lbl = tk.Label(self, image=coin_img, bg=self.bar_color, borderwidth=0)
        coin_lbl.image = coin_img  # type: ignore[attr-defined]
        coin_lbl.place(x=screen_width-100, y=30)
        saldo_lbl = tk.Label(self, text=f"{self.saldo}", font=("Helvetica", 16, "bold"), bg=self.bar_color, fg="black", borderwidth=0)
        saldo_lbl.place(x=screen_width-70, y=30)
        if len(tipos) == 1:
            title_str = tipos[0].capitalize()
        else:
            title_str = "Activities / Challenges"
        title = tk.Label(self, text=title_str, font=("Helvetica", 22, "bold"), fg="white", bg="black")
        title.place(relx=0.5, y=65, anchor="n")
        cartas = []
        for t in tipos:
            cartas += self.inventario.get(t, [])
        # Paginação
        cards_per_page = 4
        total_pages = max(1, (len(cartas) + cards_per_page - 1) // cards_per_page)
        page = max(0, min(page, total_pages - 1))
        start_idx = page * cards_per_page
        end_idx = start_idx + cards_per_page
        cartas_page = cartas[start_idx:end_idx]
        matriz_frame = tk.Frame(self, bg="black")
        matriz_frame.place(relx=0.5, rely=0.5, anchor="center")
        n_col = 2
        card_w, card_h = 85, 120  # Reduzido para não tapar o título
        for idx, carta_path in enumerate(cartas_page):
            row = idx // n_col
            col = idx % n_col
            try:
                img = ImageTk.PhotoImage(Image.open(carta_path).resize((card_w, card_h)))
            except Exception:
                continue
            carta_lbl = tk.Label(matriz_frame, image=img, bg="black", cursor="hand2")
            carta_lbl.image = img  # type: ignore[attr-defined]
            carta_lbl.grid(row=row, column=col, padx=8, pady=8)
            carta_lbl.bind("<Button-1>", lambda e, p=carta_path, t=tipos, pg=page: self.show_card_fullscreen_carrossel_selecao(p, t, pg))
        # Setas de navegação
        if total_pages > 1:
            # Coordenadas para alinhar as setas à direita da grelha de cartas
            # Assume que a grelha está centrada em relx=0.5, então relx=0.85 fica à direita
            seta_x = 0.90
            # Seta para cima (▲) - parte superior direita da grelha
            if page > 0:
                seta_cima = tk.Button(self, text="▲", font=("Helvetica", 18, "bold"), bg="#222", fg="white", width=2, command=lambda: self.show_inventory_matrix_carrossel(tipos, page-1))
                seta_cima.place(relx=seta_x, rely=0.38, anchor="center")
            # Seta para baixo (▼) - parte inferior direita da grelha
            if page < total_pages - 1:
                seta_baixo = tk.Button(self, text="▼", font=("Helvetica", 18, "bold"), bg="#222", fg="white", width=2, command=lambda: self.show_inventory_matrix_carrossel(tipos, page+1))
                seta_baixo.place(relx=seta_x, rely=0.62, anchor="center")
        back_btn = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), bg="#005c75", fg="white", width=10, command=lambda: self.playerdashboard_interface(self.player_name, self.saldo, self.other_players))
        back_btn.place(relx=0.5, rely=0.98, anchor="s")

    def show_card_fullscreen_carrossel_selecao(self, carta_path, tipos, page=0):
        # Mostra carta em fullscreen com botões ✔ (aceitar) e ✖ (cancelar)
        for widget in self.winfo_children():
            if widget == self.topbar_label:
                continue
            widget.destroy()
        pil_img = Image.open(carta_path)
        img_w, img_h = pil_img.size
        max_w, max_h = self.winfo_screenwidth(), self.winfo_screenheight()
        ratio = min(max_w/img_w, max_h/img_h)
        new_w, new_h = int(img_w*ratio), int(img_h*ratio)
        pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        carta_img = ImageTk.PhotoImage(pil_img)
        carta_real_lbl = tk.Label(self, image=carta_img, bg="black", borderwidth=0, highlightthickness=0)
        carta_real_lbl.image = carta_img  # type: ignore[attr-defined]
        carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)
        # Botão ✔ canto superior esquerdo
        btn_certo = tk.Button(self, text="✔", font=("Helvetica", 24, "bold"), bg="#4CAF50", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=lambda: self.aceitar_carta_carrossel(carta_path, tipos, page), cursor="hand2", activebackground="#43d17a")
        btn_certo.place(relx=0., rely=0, anchor="nw")
        # Botão ✖ canto superior direito - volta para página de inventário
        def voltar_inventario():
            self.show_inventory_matrix_carrossel(tipos, page)
        btn_x = tk.Button(self, text="✖", font=("Helvetica", 24, "bold"), bg="#F44336", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=voltar_inventario, cursor="hand2", activebackground="#e57373")
        btn_x.place(relx=0.98, rely=0, anchor="ne")

    def aceitar_carta_carrossel(self, carta_path, tipos, page=0):
        # Fazer a troca entre a carta do carrossel e a carta selecionada do inventário
        idx = getattr(self, 'carrossel_idx_selecao', 0)
        carta_carrossel_atual = getattr(self, 'carta_carrossel_para_troca', None)
        
        if carta_carrossel_atual:
            print(f"DEBUG: Fazendo troca - Carta do carrossel: {carta_carrossel_atual}")
            print(f"DEBUG: Carta do inventário: {carta_path}")
            print(f"DEBUG: Índice do carrossel: {idx}")
            
            # 1. Colocar a carta do inventário no lugar da carta do carrossel
            self.cards[idx] = carta_path
            self.selected_card_idx = idx
            
            # 2. Remover a carta do inventário
            for t in tipos:
                if carta_path in self.inventario.get(t, []):
                    self.inventario[t].remove(carta_path)
                    print(f"DEBUG: Removida carta {carta_path} do inventário {t}")
                    break
            
            # 3. Adicionar a carta que estava no carrossel ao inventário
            # Determinar o tipo da carta que estava no carrossel
            carta_tipo_carrossel = None
            
            # Primeiro, verificar se a carta já estava no inventário
            for t in tipos:
                if carta_carrossel_atual in self.inventario.get(t, []):
                    carta_tipo_carrossel = t
                    break
            
            # Se não encontrou, tentar determinar pelo caminho da carta
            if not carta_tipo_carrossel:
                import os
                carta_basename = os.path.basename(carta_carrossel_atual).lower()
                carta_dirname = os.path.dirname(carta_carrossel_atual).lower()
                
                # Verificar se o nome do arquivo ou pasta contém o tipo
                for t in tipos:
                    if t in carta_basename or t in carta_dirname:
                        carta_tipo_carrossel = t
                        break
                
                # Se ainda não encontrou, verificar se é uma carta "back_card" (carta virada para baixo)
                if not carta_tipo_carrossel and "back_card" in carta_basename:
                    # Cartas viradas para baixo podem ir para qualquer tipo, usar o primeiro disponível
                    carta_tipo_carrossel = tipos[0]
                
                # Último recurso: usar o primeiro tipo disponível
                if not carta_tipo_carrossel:
                    carta_tipo_carrossel = tipos[0]
            
            # Adicionar a carta do carrossel ao inventário
            if carta_tipo_carrossel in self.inventario:
                self.inventario[carta_tipo_carrossel].append(carta_carrossel_atual)
                print(f"DEBUG: Adicionada carta {carta_carrossel_atual} ao inventário {carta_tipo_carrossel}")
            else:
                print(f"DEBUG: ERRO - Tipo {carta_tipo_carrossel} não encontrado no inventário")
            
            # 4. Limpar variáveis temporárias
            self.carta_carrossel_para_troca = None
            
            print("DEBUG: Troca concluída com sucesso!")
        else:
            print("DEBUG: Nenhuma carta do carrossel definida para troca, fazendo substituição normal")
            # Comportamento original - apenas substitui a carta virada para baixo
            self.cards[idx] = carta_path
            self.selected_card_idx = idx
            # Remover carta do inventário activities/challenges
            for t in tipos:
                if carta_path in self.inventario.get(t, []):
                    self.inventario[t].remove(carta_path)
        
        # Voltar à interface principal
        self.playerdashboard_interface(self.player_name, self.saldo, self.other_players)

# Exemplo de uso isolado:
if __name__ == "__main__":
    root = tk.Tk()
    root.attributes("-fullscreen", True)  
    PlayerDashboard(root, player_color="red", saldo=1000, other_players=["red", "blue", "yellow"])
    check_gpio_key(root)
    root.mainloop()