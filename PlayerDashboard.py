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

def mostrar_carta_fullscreen_root(root, carta_path):
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
        # Aqui podes restaurar o dashboard, por exemplo:
        PlayerDashboard(root, player_color="green", saldo=1000, other_players=["red", "blue", "yellow"])
    x_btn.bind("<Button-1>", lambda e: fechar())

def make_card_callback(parent, path):
    return lambda e: parent.try_mostrar_carta(path)

class PlayerDashboard(tk.Toplevel):
    def __init__(self, root, player_color, saldo, other_players, player_name="Player"):
        super().__init__(root)
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
        bar_color = color_map.get(player_color.lower(), "#AAAAAA")
        top_bar = tk.Frame(self, bg=bar_color, height=60)
        top_bar.pack(fill="x", side="top", padx=0)  # Garante sem espaço extra à esquerda
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

        # Carrossel de cartas (3 cartas visíveis)
        carousel_frame = tk.Frame(self, bg="black")
        carousel_frame.pack(pady=(10,15), fill="x")

        # Frame para o botão "<"
        prev_btn_frame = tk.Frame(carousel_frame, bg="black")
        prev_btn_frame.pack(side=tk.LEFT, fill="y")
        prev_btn = tk.Button(prev_btn_frame, text="<", font=("Helvetica", 18), command=self.prev_card, bg="black", fg="white", bd=0, highlightthickness=0)
        prev_btn.pack(expand=True)

        # Frame central para as cartas
        cards_container = tk.Frame(carousel_frame, bg="black")
        cards_container.pack(side=tk.LEFT, expand=True, fill="both")

        self.cards = [
            os.path.join(IMG_DIR, "cartas", "data", "Data_1.png"),
            os.path.join(IMG_DIR, "cartas", "data", "Data_5.png"),
            os.path.join(IMG_DIR, "cartas", "challenges", "Challenge_1.png"),
            os.path.join(IMG_DIR, "cartas", "challenges", "Challenge_8.png"),
            os.path.join(IMG_DIR, "cartas", "back_card.png"),
        ]
        self.card_idx = 0

        self.card_labels = []
        for i in range(3):
            idx = (self.card_idx + i) % len(self.cards)
            img = ImageTk.PhotoImage(Image.open(self.cards[idx]).resize((85,120)))
            lbl = tk.Label(cards_container, image=img, bg="black")
            lbl.image = img
            lbl.pack(side=tk.LEFT, padx=5)
            lbl.bind("<Button-1>", make_card_callback(self, self.cards[idx]))
            self.card_labels.append(lbl)

        # Frame para o botão ">"
        next_btn_frame = tk.Frame(carousel_frame, bg="black")
        next_btn_frame.pack(side=tk.LEFT, fill="y")
        next_btn = tk.Button(next_btn_frame, text=">", font=("Helvetica", 18), command=self.next_card, bg="black", fg="white", bd=0, highlightthickness=0)
        next_btn.pack(expand=True)

        # Barras de progresso (alinhadas à esquerda e esticadas)
        progress_frame = tk.Frame(self, bg="black")
        progress_frame.pack(pady=(0,5), anchor="w", fill="x", expand=True)
        self.add_progress_bar(progress_frame, "To send", 3)
        self.add_progress_bar(progress_frame, "Txd", 1)
        self.add_progress_bar(progress_frame, "Lost", 0)

        # Botões de ação (layout igual ao Store)
        btns_frame = tk.Frame(self, bg="black")
        btns_frame.pack(pady=0)
        btn_font = ("Helvetica", 18, "bold")
        btn_size = {"width": 6, "height": 3}  # Igual ao Store

        btn_users = tk.Button(
            btns_frame, text="Users", font=btn_font, bg=bar_color,
            activebackground="white", activeforeground="black", fg="black",
            **btn_size, highlightthickness=0, bd=0
        )
        btn_equip = tk.Button(
            btns_frame, text="Equip.", font=btn_font, bg=bar_color,
            activebackground="white", activeforeground="black", fg="black",
            **btn_size, highlightthickness=0, bd=0
        )
        btn_services = tk.Button(
            btns_frame, text="Services", font=btn_font, bg=bar_color,
            activebackground="white", activeforeground="black", fg="black",
            **btn_size, highlightthickness=0, bd=0
        )
        btn_actions = tk.Button(
            btns_frame, text="Actions/\nEvents", font=btn_font, bg=bar_color,
            activebackground="white", activeforeground="black", fg="black",
            **btn_size, highlightthickness=0, bd=0
        )

        btn_users.grid(row=0, column=0, padx=10, pady=5)
        btn_equip.grid(row=0, column=1, padx=10, pady=5)
        btn_services.grid(row=1, column=0, padx=10, pady=5)
        btn_actions.grid(row=1, column=1, padx=10, pady=5)


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
        pb = ttk.Progressbar(fr, length=160, maximum=10, value=value)  # Diminuído
        pb.pack(side=tk.LEFT, padx=8, fill="x", expand=True)
        tk.Label(fr, text=str(value), font=("Helvetica", 14), bg="black", fg="white", width=2).pack(side=tk.LEFT)

    def try_mostrar_carta(self, path):
        try:
            print("CLICOU!", path)
            mostrar_carta_fullscreen_root(self.master, path)
        except Exception as ex:
            print("ERRO AO ABRIR FULLSCREEN:", ex)

# Exemplo de uso isolado:
if __name__ == "__main__":
    root = tk.Tk()
    root.attributes("-fullscreen", True)  
    PlayerDashboard(root, player_color="green", saldo=1000, other_players=["red", "blue", "yellow"])
    check_gpio_key()
    root.mainloop()