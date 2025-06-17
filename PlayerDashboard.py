import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import RPi.GPIO as GPIO
import random
from Store import StoreWindow

IMG_DIR = os.path.join(os.path.dirname(__file__), "img")
COIN_IMG = os.path.join(IMG_DIR, "picoin.png")
USER_ICONS = [
    os.path.join(IMG_DIR, "red_user_icon.png"),
    os.path.join(IMG_DIR, "green_user_icon.png"),
    os.path.join(IMG_DIR, "blue_user_icon.png"),
    os.path.join(IMG_DIR, "yellow_user_icon.png"),
]

# GPIO setup para botão KEY1
KEY1_PIN = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(KEY1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

BOARD = [
    # Top row (left to right)
    ("start", "neutral"),      # 0 canto azul
    ("users", "blue"),         # 1
    ("action", "neutral"),     # 2 (cinzento)
    ("equipment", "blue"),     # 3
    ("challenges", "neutral"), # 4 (cinzento)
    ("data", "red"),           # 5
    ("events", "neutral"),     # 6 (cinzento)
    ("services", "red"),       # 7

    # Right column (top to bottom)
    ("start", "neutral"),      # 8 canto vermelho
    ("users", "red"),          # 9
    ("action", "neutral"),     # 10 (cinzento)
    ("equipment", "red"),      # 11
    ("challenges", "neutral"), # 12 (cinzento)
    ("data", "yellow"),        # 13
    ("events", "neutral"),     # 14 (cinzento)
    ("services", "yellow"),    # 15

    # Bottom row (right to left)
    ("start", "neutral"),      # 16 canto amarelo
    ("users", "yellow"),       # 17
    ("action", "neutral"),     # 18 (cinzento)
    ("equipment", "yellow"),   # 19
    ("challenges", "neutral"), # 20 (cinzento)
    ("data", "green"),         # 21
    ("events", "neutral"),     # 22 (cinzento)
    ("services", "green"),     # 23

    # Left column (bottom to top)
    ("start", "neutral"),      # 24 canto verde
    ("users", "green"),        # 25
    ("action", "neutral"),     # 26 (cinzento)
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

def check_gpio_key(root):
    if GPIO.input(KEY1_PIN) == GPIO.LOW:
        GPIO.cleanup()
        root.destroy()
    else:
        root.after(100, lambda: check_gpio_key(root))

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
        self.bar_color = color_map.get(player_color.lower(), "#AAAAAA")

        # --- BARRA SUPERIOR COM IMAGEM ---
        topbar_img_path = os.path.join(IMG_DIR, f"TopBar_{player_color.lower()}.png")
        img = Image.open(topbar_img_path).convert("RGBA")
        img = img.resize((screen_width, 60), Image.LANCZOS)
        topbar_img = ImageTk.PhotoImage(img)
        self.topbar_label = tk.Label(self, image=topbar_img, bg="black", borderwidth=0, highlightthickness=0)
        self.topbar_label.image = topbar_img
        self.topbar_label.pack(side="top", fill="x")

        # Chama a tela de lançamento de dado
        self.show_dice_roll_screen(player_name, saldo, other_players, screen_width, screen_height)

        self.inventory = {
            "users": [],
            "equipment": [],
            "services": [],
            "action": [],
            "events": [],
            "challenges": [],
            "data": [],
        }

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
        coin_lbl = tk.Label(self, image=coin_img, bg=self.bar_color)
        coin_lbl.image = coin_img
        coin_lbl.place(x=screen_width-100, y=30)
        saldo_lbl = tk.Label(self, text=f"{saldo}", font=("Helvetica", 16, "bold"), fg="black", bg=self.bar_color)
        saldo_lbl.place(x=screen_width-70, y=30)

        # Ícones dos outros jogadores (esquerda)
        for idx, p in enumerate(other_players):
            if idx < len(USER_ICONS):
                icon_img = ImageTk.PhotoImage(Image.open(USER_ICONS[idx]).resize((30,30)))
                lbl = tk.Label(self, image=icon_img, bg=self.bar_color)
                lbl.image = icon_img
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

        cor_map = {
            "green": "#70AD47",
            "yellow": "#F2BA0D",
            "red": "#EE6F68",
            "blue": "#43BEF2",
            "neutral": "#AAAAAA"
        }

        if not hasattr(self, "player_pos"):
            self.player_pos = START_POSITIONS.get(self.player_color.lower(), 0)
        player_pos = self.player_pos

        def after_texts():
            nonlocal dice_btn, go_btn
            blank_img_path = os.path.join(IMG_DIR, "dice", "Dice_blank.png")
            dice_img = ImageTk.PhotoImage(Image.open(blank_img_path).resize((100,100)))
            dice_btn = tk.Label(center_frame, image=dice_img, bg="black")
            dice_btn.image = dice_img
            dice_btn.pack(pady=20)

            go_btn = tk.Button(center_frame, text="Go!", font=("Helvetica", 16, "bold"), bg="#005c75", fg="white")

            def roll_animation():
                go_btn.pack_forget()
                frames = 25
                results = [random.randint(1,6) for _ in range(frames)]
                final = random.randint(1,6)
                results.append(final)

                def animate(i=0):
                    if i < len(results):
                        n = results[i]
                        img_path = os.path.join(IMG_DIR, "dice", f"Dice_{n}.png")
                        img = ImageTk.PhotoImage(Image.open(img_path).resize((100,100)))
                        dice_btn.config(image=img)
                        dice_btn.image = img
                        center_frame.after(100, animate, i+1)
                    else:
                        img_path = os.path.join(IMG_DIR, "dice", f"Dice_{final}.png")
                        img = ImageTk.PhotoImage(Image.open(img_path).resize((100,100)))
                        dice_btn.config(image=img)
                        dice_btn.image = img

                        # Esconde as frases
                        lbl1.pack_forget()
                        lbl2.pack_forget()
                        dice_btn.pack_forget()

                        # Mostra só o nome da casa, centrado e colorido
                        steps = final
                        old = self.player_pos
                        new_pos = (old + steps) % NUM_CASAS
                        tipo, casa_cor = BOARD[new_pos]
                        cor_hex = cor_map.get(casa_cor, "#FFFFFF")
                        nome_lbl = tk.Label(center_frame, text=tipo.upper(), font=("Helvetica", 22, "bold"), fg=cor_hex, bg="black", wraplength=int(screen_width*0.8), justify="center")
                        nome_lbl.pack(pady=10)
                        self.player_pos = new_pos

                        def abrir_store():
                            # Só abre a Store se for casa da cor do jogador ou neutra
                            if casa_cor == self.player_color.lower() or casa_cor == "neutral":
                                StoreWindow(self, self.player_color, player_name, saldo, casa_tipo=tipo, casa_cor=casa_cor)
                            center_frame.destroy()
                        center_frame.after(2000, abrir_store)

                animate()

            go_btn.config(command=roll_animation)
            go_btn.pack(pady=(0, 5))

        self.animate_typing(lbl1, "It's your turn!", delay=60,
            callback=lambda: self.animate_typing(lbl2, "Roll the dice to start your adventure.", delay=60, callback=after_texts)
        )

    def show_dashboard_main(self):
        # Aqui vai o layout principal do dashboard (carrossel, barras, etc)
        # ... já existente no teu __init__ ...
        pass

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

    def update_progress_bars_for_card(self, card_path):
        # Exemplo: valores fictícios para cada carta
        # Podes adaptar esta lógica conforme o teu jogo
        if "Data_1" in card_path:
            values = {"To send": 2, "Rxd": 1, "Lost": 0}
        elif "Data_5" in card_path:
            values = {"To send": 5, "Rxd": 3, "Lost": 1}
        elif "Challenge_1" in card_path:
            values = {"To send": 1, "Rxd": 0, "Lost": 0}
        elif "Challenge_8" in card_path:
            values = {"To send": 4, "Rxd": 2, "Lost": 2}
        else:
            values = {"To send": 0, "Rxd": 0, "Lost": 0}
        for label, pb in self.progress_bars.items():
            pb["value"] = values.get(label, 0)
            if hasattr(self, "progress_labels") and label in self.progress_labels:
                self.progress_labels[label].config(text=str(values.get(label, 0)))

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
        if carta_tipo in self.inventory:
            self.inventory[carta_tipo].append(carta_path)

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
        cartas = self.inventory.get(carta_tipo, [])
        if cartas:
            carta_path = cartas[-1]  # Mostra a última carta tirada
            img = ImageTk.PhotoImage(Image.open(carta_path).resize((180, 260)))
            carta_lbl = tk.Label(self, image=img, bg="black", cursor="hand2")
            carta_lbl.image = img
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
        seta_btn.image = seta_img
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
        pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)

        carta_img = ImageTk.PhotoImage(pil_img)
        carta_real_lbl = tk.Label(self, image=carta_img, bg="black")
        carta_real_lbl.image = carta_img
        carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Botão X para fechar
        x_img_path = os.path.join(IMG_DIR, "X_button.png")
        x_img = ImageTk.PhotoImage(Image.open(x_img_path).resize((48, 48)))
        x_btn = tk.Label(self, image=x_img, bg="black", cursor="hand2")
        x_btn.image = x_img
        x_btn.place(relx=0.98, rely=0.02, anchor="ne")
        x_btn.bind("<Button-1>", lambda e: self.show_inventory_page(carta_tipo))

# Exemplo de uso isolado:
if __name__ == "__main__":
    root = tk.Tk()
    root.attributes("-fullscreen", True)  
    PlayerDashboard(root, player_color="red", saldo=1000, other_players=["red", "blue", "yellow"])
    check_gpio_key(root)
    root.mainloop()