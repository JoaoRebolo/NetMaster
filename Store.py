import tkinter as tk
from PIL import Image, ImageTk
import os
import RPi.GPIO as GPIO

IMG_DIR = "/home/joao_rebolo/netmaster_menu/img"
COIN_IMG = os.path.join(IMG_DIR, "picoin.png")
AWNING_IMG = os.path.join(IMG_DIR, "Store_awning.png")

KEY1_PIN = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(KEY1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

class StoreWindow(tk.Toplevel):
    def __init__(self, root, player_color, player_name, saldo=1000):
        super().__init__(root)
        self.title("Store")
        self.configure(bg="black")
        self.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
        self.overrideredirect(True)

        # Barra superior com imagem Store_awning.png
        awning_img = ImageTk.PhotoImage(Image.open(AWNING_IMG).resize((root.winfo_screenwidth(), 50)))
        awning_label = tk.Label(self, image=awning_img, bg="black")
        awning_label.image = awning_img  # manter referência
        awning_label.pack(pady=(0, 10), fill="x")

        # Frame principal para os botões
        main_frame = tk.Frame(self, bg="black")
        main_frame.pack(anchor="center", pady=(0, 20))  # Reduz o espaço entre as linhas

        btn_font = ("Helvetica", 18, "bold")
        btn_size = {"width": 6, "height": 3}  # Botões maiores

        # Primeira linha: Actions, Events, Challenges (neutras) com imagens GRANDES
        img_size = (90, 90)  # Tamanho maior
        actions_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "Actions_button.png")).resize(img_size))
        events_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "Events_button.png")).resize(img_size))
        challenges_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "Challenges_button.png")).resize(img_size))

        btn_a = tk.Button(main_frame, image=actions_img, bg="#000000", activebackground="#000000",width=75, height=100, highlightthickness=0, bd=0)
        btn_e = tk.Button(main_frame, image=events_img,bg= "#000000", activebackground="#000000",width=75, height=100, highlightthickness=0, bd=0)
        btn_d = tk.Button(main_frame, image=challenges_img, bg="#000000", activebackground="#000000",width=75, height=100, highlightthickness=0, bd=0)
        btn_a.image = actions_img
        btn_e.image = events_img
        btn_d.image = challenges_img

        btn_a.grid(row=0, column=0, padx=10, pady=(5, 2), sticky="n")
        btn_e.grid(row=0, column=1, padx=10, pady=(5, 2), sticky="n")
        btn_d.grid(row=0, column=2, padx=10, pady=(5, 2), sticky="n")

        # Frame para centralizar os botões dos jogadores
        players_frame = tk.Frame(self, bg="black")
        players_frame.pack(pady=0)  # Espaço menor acima dos jogadores

        # Segunda linha: J1, J2
        btn_j1 = tk.Button(players_frame, text="J1", font=btn_font, bg=self.get_color(player_color), fg="white", **btn_size)
        btn_j2 = tk.Button(players_frame, text="J2", font=btn_font, bg=self.get_color(player_color), fg="white", **btn_size)
        btn_j1.grid(row=0, column=0, padx=10, pady=5)
        btn_j2.grid(row=0, column=1, padx=10, pady=5)

        # Terceira linha: J3, J4
        btn_j3 = tk.Button(players_frame, text="J3", font=btn_font, bg=self.get_color(player_color), fg="white", **btn_size)
        btn_j4 = tk.Button(players_frame, text="J4", font=btn_font, bg=self.get_color(player_color), fg="white", **btn_size)
        btn_j3.grid(row=1, column=0, padx=10, pady=5)
        btn_j4.grid(row=1, column=1, padx=10, pady=5)

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
            "blue": "#0070FF"
        }.get(color.lower(), "#AAAAAA")

# Exemplo de uso isolado:
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    StoreWindow(root, player_color="green", player_name="Jogador1")
    root.mainloop()