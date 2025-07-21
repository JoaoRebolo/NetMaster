from PIL import Image, ImageTk, UnidentifiedImageError
import os
import RPi.GPIO as GPIO
import tkinter as tk  # Importação do tkinter
import threading
import socket
import random
import string
import itertools
import netifaces
from PlayerDashboard import PlayerDashboard, check_gpio_key
from Store import StoreWindow

LOCAL_PORT = 5050
DISCOVERY_PORT = 5001
TCP_PORT = LOCAL_PORT  # Usa a mesma porta TCP do teu servidor

# Caminho para imagens e onde guardar o nome
IMG_DIR = os.path.join(os.path.dirname(__file__), "img")
USERNAME_FILE = os.path.join(os.path.dirname(__file__), "username.txt")
CARTAS_DIR = os.path.join(IMG_DIR, "cartas")

# GPIO setup para botão KEY1
KEY1_PIN = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(KEY1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Variável global do estado do teclado (uppercase / lowercase)
keyboard_state = "uppercase"

clients = []  # Lista de clientes conectados

# Tipos de carta e cores
CARD_TYPES = ["users", "actions", "equipments", "challenges", "activities", "events", "services"]
COLORS = ["green", "yellow", "red", "blue", "neutral"]

# Baralhos: dict do tipo {'green': {'users': [lista de paths], ...}, ...}
baralhos = {}

BOARD = [
    # Top row (left to right)
    ("start", "neutral"),      # 0 canto azul
    ("users", "blue"),         # 1
    ("actions", "neutral"),     # 2 (cinzento)
    ("equipments", "blue"),     # 3
    ("challenges", "neutral"), # 4 (cinzento)
    ("activities", "red"),      # 5
    ("events", "neutral"),     # 6 (cinzento)
    ("services", "red"),       # 7

    # Right column (top to bottom)
    ("start", "neutral"),      # 8 canto vermelho
    ("users", "red"),          # 9
    ("actions", "neutral"),     # 10 (cinzento)
    ("equipments", "red"),      # 11
    ("challenges", "neutral"), # 12 (cinzento)
    ("activities", "yellow"),   # 13
    ("events", "neutral"),     # 14 (cinzento)
    ("services", "yellow"),    # 15

    # Bottom row (right to left)
    ("start", "neutral"),      # 16 canto amarelo
    ("users", "yellow"),       # 17
    ("actions", "neutral"),     # 18 (cinzento)
    ("equipments", "yellow"),   # 19
    ("challenges", "neutral"), # 20 (cinzento)
    ("activities", "green"),    # 21
    ("events", "neutral"),     # 22 (cinzento)
    ("services", "green"),     # 23

    # Left column (bottom to top)
    ("start", "neutral"),      # 24 canto verde
    ("users", "green"),        # 25
    ("actions", "neutral"),     # 26 (cinzento)
    ("equipments", "green"),    # 27
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

# === CLASSE SIMPLES PARA JOGADOR ===
class Player:
    def __init__(self, name: str, color: str, start_pos: int):
        self.name = name
        self.color = color
        self.pos = start_pos

    def __repr__(self):
        return f"<Player {self.name!r} pos={self.pos} color={self.color!r}>"

def preparar_baralhos():
    global baralhos
    baralhos = {}
    for cor in COLORS:
        baralhos[cor] = {}
        for tipo in CARD_TYPES:
            cartas = []
            
            # Mapear nomes de tipos para pastas (ajustar inconsistências)
            folder_name = tipo
            if tipo == "actions":
                folder_name = "actions"  # Se existir pasta actions
            elif tipo == "services":
                folder_name = "services"
            
            # Estrutura: cartas/[tipo]/Residential-level/
            base_path = os.path.join(CARTAS_DIR, folder_name, "Residential-level")
            
            # Para tipos que têm cores (equipments, services, users)
            if folder_name in ["equipments", "services", "users"]:
                # Mapear cores do jogo para nomes de pastas
                color_folder = cor.capitalize()  # blue -> Blue, etc.
                if cor == "neutral":
                    # Para neutral, tentar todas as cores disponíveis
                    for test_color in ["Blue", "Green", "Red", "Yellow"]:
                        color_path = os.path.join(base_path, test_color)
                        if os.path.exists(color_path):
                            card_files = [os.path.join(color_path, f) for f in os.listdir(color_path) 
                                        if f.lower().endswith((".png", ".jpg", ".jpeg"))]
                            cartas.extend(card_files)
                else:
                    color_path = os.path.join(base_path, color_folder)
                    if os.path.exists(color_path):
                        cartas = [os.path.join(color_path, f) for f in os.listdir(color_path) 
                                if f.lower().endswith((".png", ".jpg", ".jpeg"))]
            else:
                # Para tipos sem cores (challenges, events, activities, actions)
                if os.path.exists(base_path):
                    cartas = [os.path.join(base_path, f) for f in os.listdir(base_path) 
                            if f.lower().endswith((".png", ".jpg", ".jpeg"))]
            
            if cartas:
                random.shuffle(cartas)
                baralhos[cor][tipo] = cartas.copy()
            else:
                baralhos[cor][tipo] = []
preparar_baralhos()
print("DEBUG: Baralhos carregados:")
for cor in baralhos:
    for tipo in baralhos[cor]:
        print(f"{cor}/{tipo}: {len(baralhos[cor][tipo])} cartas")

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

def move_player(player, steps):
    global tf
    old = player.pos
    player.pos = (player.pos + steps) % NUM_CASAS
    tipo, casa_cor = BOARD[player.pos]

    # Mostra nome da casa na cor certa
    cor_map = {
        "green": "#70AD47",
        "yellow": "#F2BA0D",
        "red": "#EE6F68",
        "blue": "#43BEF2",
        "neutral": "#AAAAAA"
    }
    cor_hex = cor_map.get(casa_cor, "#FFFFFF")

    resultado = f"{player.name} lançou {steps}: {old} → {player.pos}\n"
    resultado += f"Casa: {tipo.upper()}"

    # Mostra label com nome da casa na cor
    resultado_lbl = tk.Label(tf, text=tipo.upper(), font=("Helvetica", 22, "bold"), fg=cor_hex, bg="black")
    resultado_lbl.pack(pady=10)

    # Se for da mesma cor ou neutra, mostra carta
    if casa_cor == player.color or casa_cor == "neutral":
        mostrar_carta(player, casa_cor, tipo)
    else:
        # Casa normal, não tira carta
        info_lbl = tk.Label(tf, text="Casa normal ou de outra cor.", font=("Helvetica", 14), bg="black", fg="white")
        info_lbl.pack(pady=10)
        
def mostrar_carta(player, casa_cor, tipo):
    global tf, screen_height
    print(f"DEBUG: mostrar_carta({casa_cor=}, {tipo=})")
    verso_path = os.path.join(CARTAS_DIR, "back_card.png")
    if not os.path.exists(verso_path):
        verso_path = os.path.join(CARTAS_DIR, "verso.png")

    img = ImageTk.PhotoImage(Image.open(verso_path).resize((220, 320)))
    carta_lbl = tk.Label(tf, image=img, bg="black")
    carta_lbl.image = img
    carta_lbl.pack(pady=(0, 2))

    go_btn = None

    def revelar_carta():
        nonlocal go_btn
        carta_lbl.destroy()
        if go_btn:
            go_btn.destroy()
        carta_path = tirar_carta(casa_cor, tipo)
        print(f"DEBUG: tirar_carta devolveu {carta_path}")
        if carta_path and os.path.exists(carta_path):
            mostrar_carta_fullscreen(carta_path)
        else:
            print("DEBUG: Carta não existe no path")
            tk.Label(tf, text="Sem cartas disponíveis!", font=("Helvetica", 14), bg="black", fg="white").pack(pady=10)

    go_btn = tk.Button(tf, text="Go!", font=("Helvetica", 16, "bold"), bg="#005c75", fg="white", command=revelar_carta)
    go_btn.pack(pady=(5, 2))

def mostrar_carta_fullscreen(carta_path):
    # Limpa tudo do root
    for widget in root.winfo_children():
        widget.destroy()
    root.configure(bg="black")

    pil_img = Image.open(carta_path)
    img_w, img_h = pil_img.size
    max_w, max_h = screen_width, screen_height
    ratio = min(max_w/img_w, max_h/img_h)
    new_w, new_h = int(img_w*ratio), int(img_h*ratio)
    pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)

    carta_img = ImageTk.PhotoImage(pil_img)
    carta_real_lbl = tk.Label(root, image=carta_img, bg="black")
    carta_real_lbl.image = carta_img
    carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center")

    # Carregar imagem do X
    x_img_path = os.path.join(IMG_DIR, "X_button.png")
    x_img = ImageTk.PhotoImage(Image.open(x_img_path).resize((48, 48)))
    
    def fechar():
        carta_real_lbl.destroy()
        x_btn.destroy()
        # Aqui podes restaurar o conteúdo anterior ou chamar a próxima função do jogo

    # Botão de fechar com imagem
    x_btn = tk.Label(root, image=x_img, bg="", cursor="hand2")
    x_btn.image = x_img  # manter referência
    x_btn.place(relx=0.95, rely=0.02, anchor="ne")
    x_btn.bind("<Button-1>", lambda e: fechar())

# Função para animação de escrita
def animate_typing(label, text, delay=50, callback=None):
    def _type(i=0):
        if i <= len(text):
            label.config(text=text[:i])
            label.after(delay, _type, i + 1)
        elif callback:
            callback()
    _type()

# Atualizar layout do teclado conforme estado
def update_keyboard():
    for widget in keyboard_frame.winfo_children():
        widget.destroy()

    key_font = ("Helvetica", 10)
    key_width = 1  # Achata as teclas na horizontal
    key_height = 1

    if keyboard_state == "uppercase":
        rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
    else:
        rows = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]

    for row in rows:
        rf = tk.Frame(keyboard_frame, bg="white")
        rf.pack(pady=6)
        for ch in row:
            tk.Button(
                rf, text=ch, width=key_width, height=key_height,
                font=key_font,
                command=lambda c=ch: add_char(c),
                bg="white", fg="black",
                activebackground="white", activeforeground="black"
            ).pack(side=tk.LEFT, padx=0, pady=0)  # Sem espaço lateral

    ctrl = tk.Frame(keyboard_frame, bg="white")
    ctrl.pack(pady=8)
    tk.Button(ctrl, text="Space", width=4, font=key_font, command=space, bg="white", fg="black", activebackground="white", activeforeground="black").pack(side=tk.LEFT, padx=1)
    tk.Button(ctrl, text="Back", width=4, font=key_font, command=backspace, bg="white", fg="black", activebackground="white", activeforeground="black").pack(side=tk.LEFT, padx=1)
    tk.Button(ctrl, text="Enter", width=4, font=key_font, command=enter_key, bg="white", fg="black", activebackground="white", activeforeground="black").pack(side=tk.LEFT, padx=1)
    tk.Button(ctrl, text="ABC", width=4, font=key_font, command=toggle_keyboard_state, bg="white", fg="black", activebackground="white", activeforeground="black").pack(side=tk.LEFT, padx=1)

# Alternar uppercase/lowercase
def toggle_keyboard_state():
    global keyboard_state
    keyboard_state = "lowercase" if keyboard_state == "uppercase" else "uppercase"
    update_keyboard()

# Mostrar teclado flutuante ao focar na entry
def show_keyboard(event=None):
    update_keyboard()
    # Coloca o teclado mais em baixo, mas ainda visível
    keyboard_frame.place(relx=0.5, rely=0.65, anchor="n")

# Funções do teclado virtual
def add_char(char):
    global keyboard_state
    name_entry.insert(tk.END, char)
    if keyboard_state == "uppercase":
        keyboard_state = "lowercase"
        update_keyboard()

def backspace():
    current = name_entry.get()
    name_entry.delete(0, tk.END)
    name_entry.insert(0, current[:-1])

def space():
    name_entry.insert(tk.END, " ")

def enter_key():
    if keyboard_frame.winfo_ismapped():
        keyboard_frame.place_forget()

# Salvar nome e avançar para página do usuário
def submit_name():
    name = name_entry.get().strip().capitalize()
    if name:
        with open(USERNAME_FILE, "w") as f:
            f.write(name)
        if keyboard_frame.winfo_ismapped():
            keyboard_frame.place_forget()
        user_window.destroy()
        show_user_page(name)

# Verificar botão KEY1 para sair
def check_gpio_key():
    if GPIO.input(KEY1_PIN) == GPIO.LOW:
        GPIO.cleanup()
        root.destroy()
    root.after(100, check_gpio_key)

# Janela principal
root = tk.Tk()
#root.overrideredirect(True)
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(f"{screen_width}x{screen_height}+0+0")
root.configure(bg="black")  # fundo preto
root.attributes("-fullscreen", True)

# Carregar imagens dos logos e ícones
print("A carregar logo NetMaster...")
netmaster_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "logo_netmaster_icon_v3.png")).resize((100,40)))
create_icon = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "create_game_icon_button.png")).resize((100,100)))
search_icon = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "search_game_icon_button.png")).resize((100,100)))

# Definição de open_name_input
def open_name_input():
    global user_window, name_entry, keyboard_frame
    user_window = tk.Toplevel(root, bg="black")  # fundo preto
    user_window.overrideredirect(True)
    user_window.geometry(f"{screen_width}x{screen_height}+0+0")

    # Só o logo NetMaster ao centro
    tk.Label(user_window, image=netmaster_img, bg="black").place(relx=0.5, y=10, anchor="n")

    tf = tk.Frame(user_window, bg="black")
    tf.place(relx=0.5, rely=0.32, anchor="center")
    l1 = tk.Label(tf, text="", font=("Helvetica",18,"bold"), bg="black", fg="white", wraplength=int(screen_width*0.8), justify="center")
    l2 = tk.Label(tf, text="", font=("Helvetica",16), bg="black", fg="white", wraplength=int(screen_width*0.8), justify="center")
    l1.pack(pady=(0,8))
    l2.pack(pady=(0,12))

    # input
    input_fr = tk.Frame(user_window, bg="black")
    name_entry = tk.Entry(input_fr, font=("Helvetica",14), width=22, justify="center")
    name_entry.bind("<Button-1>", show_keyboard)
    submit_btn = tk.Button(input_fr, text="Submit", font=("Helvetica",12,"bold"),
                           command=submit_name, bg="#005c75", fg="white")

    def show_input():
        input_fr.place(relx=0.5, rely=0.44, anchor="n")
        name_entry.pack(pady=10)
        submit_btn.pack()

    animate_typing(l1, "Initializing user profile...", delay=50,
                   callback=lambda: animate_typing(l2, "What should we call you?", delay=40, callback=show_input))

    # frame do teclado
    keyboard_frame = tk.Frame(user_window, bg="white")
    update_keyboard()

# Exibir página do usuário após nome inserido
def show_user_page(name):
    up = tk.Toplevel(root, bg="black")  # fundo preto
    up.overrideredirect(True)
    up.geometry(f"{screen_width}x{screen_height}+0+0")

    tk.Label(up, image=netmaster_img, bg="black").place(relx=0.5, y=10, anchor="n")

    tf = tk.Frame(up, bg="black")
    tf.place(relx=0.5, rely=0.36, anchor="center")
    lbl1 = tk.Label(tf, text="", font=("Helvetica",18,"bold"), bg="black", fg="#6F0DB6", wraplength=int(screen_width*0.8), justify="center")
    lbl2 = tk.Label(tf, text="", font=("Helvetica",14), bg="black", fg="white", wraplength=int(screen_width*0.8), justify="center")
    lbl1.pack(pady=(0,8))
    lbl2.pack(pady=(0,12))

    def show_buttons():
        bf = tk.Frame(up, bg="black")
        bf.place(relx=0.5, rely=0.6, anchor="center")
        # ícones de cor
        for color, fname in [("Red","red_user_icon.png"),
                             ("Green","green_user_icon.png"),
                             ("Blue","blue_user_icon.png"),
                             ("Yellow","yellow_user_icon.png")]:
            icon = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, fname)).resize((65,65)))
            tk.Button(
                bf,
                image=icon,
                bd=0,
                bg="black",
                activebackground="black",
                highlightthickness=0,
                command=lambda c=color: open_color_page(c)
            ).pack(side=tk.LEFT, padx=10)
            # manter referência
            setattr(up, f"{color.lower()}_icon", icon)

    animate_typing(lbl1, name, delay=50,
                   callback=lambda: animate_typing(lbl2,
                       "pick a color that feels like you!\nThis will represent your network.",
                       delay=50, callback=show_buttons))

# Ao selecionar cor, abrir nova página
def open_color_page(color):
    global host_name, host_color, jogador
    host_color = color
    color_map = {
    "green": "#70AD47",
    "yellow": "#F2BA0D",
    "red": "#EE6F68",
    "blue": "#43BEF2"
    }
    bar_color = color_map.get(host_color.lower(), "#AAAAAA")
    
    try:
        with open(USERNAME_FILE, "r") as f:
            host_name = f.read().strip()
    except:
        host_name = "Host"
    jogador = Player(host_name, host_color.lower(), START_POSITIONS[host_color.lower()])
    cp = tk.Toplevel(root, bg="black")
    cp.overrideredirect(True)
    cp.geometry(f"{screen_width}x{screen_height}+0+0")

    # Barra superior
    topbar_img_path = os.path.join(IMG_DIR, f"TopBar_{host_color.lower()}.png")
    img = Image.open(topbar_img_path).convert("RGBA")
    img = img.resize((screen_width, 60), Image.LANCZOS)
    topbar_img = ImageTk.PhotoImage(img)
    cp.topbar_img = topbar_img
    topbar_label = tk.Label(cp, image=topbar_img, bg="black", borderwidth=0, highlightthickness=0)
    topbar_label.place(x=0, y=0, width=screen_width, height=60)

    name_lbl = tk.Label(cp, text=host_name, font=("Helvetica", 18, "bold"), fg="black", bg=bar_color, bd=0)
    name_lbl.place(relx=0.5, y=25, anchor="n")

    COIN_IMG = os.path.join(IMG_DIR, "picoin.png")
    coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24,24)))
    cp.coin_img = coin_img
    coin_lbl = tk.Label(cp, image=coin_img, bg=bar_color, bd=0)
    coin_lbl.place(x=screen_width-100, y=30)
    saldo_lbl = tk.Label(cp, text="1000", font=("Helvetica", 16, "bold"), fg="black", bg=bar_color, bd=0)
    saldo_lbl.place(x=screen_width-70, y=30)

    # Frame central (texto) - LOCAL!
    tf = tk.Frame(cp, bg="black")
    tf.place(relx=0.5, rely=0.28, anchor="center")

    great_lbl = tk.Label(tf, text="", font=("Helvetica", 18, "bold"), bg="black", fg="white", wraplength=int(screen_width*0.8), justify="center")
    great_lbl.pack(pady=(0,8))
    how_lbl = tk.Label(tf, text="", font=("Helvetica", 14), bg="black", fg="white", wraplength=int(screen_width*0.8), justify="center")
    how_lbl.pack(pady=(0,12))

    local_icon = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "local_game_icon_button.png")).resize((115, 130)))
    remote_icon = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "remote_game_icon_button.png")).resize((115, 130)))
    cp.local_icon = local_icon
    cp.remote_icon = remote_icon

    def show_play_buttons():
        btns_frame = tk.Frame(cp, bg="black")
        btns_frame.place(relx=0.5, rely=0.7, anchor="center")
        def launch_local():
            cp.destroy()
            PlayerDashboard(
                root,
                player_color=host_color.lower(),
                saldo=1000,
                other_players=[c for c in ["red", "green", "blue", "yellow"] if c != host_color.lower()],
                player_name=host_name
            )
            check_gpio_key(root)
        def launch_remote():
            cp.destroy()
            PlayerDashboard(
                root,
                player_color=host_color.lower(),
                saldo=1000,
                other_players=[c for c in ["red", "green", "blue", "yellow"] if c != host_color.lower()],
                player_name=host_name
            )
            check_gpio_key(root)
        tk.Button(
            btns_frame,
            image=cp.local_icon,
            bd=0,
            bg="black",
            activebackground="black",
            highlightthickness=0,
            command=launch_local
        ).pack(side=tk.TOP, pady=10)
        tk.Button(
            btns_frame,
            image=cp.remote_icon,
            bd=0,
            bg="black",
            activebackground="black",
            highlightthickness=0,
            command=launch_remote
        ).pack(side=tk.TOP, pady=10)

    animate_typing(great_lbl, "Great!", delay=60,
        callback=lambda: animate_typing(how_lbl, "How do you want to play?", delay=40, callback=show_play_buttons)
    )

def generate_session_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def show_success_page(bar_color, players_joined):
    global clients
    success_win = tk.Toplevel(root, bg="black")
    success_win.overrideredirect(True)
    success_win.geometry(f"{screen_width}x{screen_height}+0+0")

    # Barra superior colorida
    top_bar = tk.Frame(success_win, bg=bar_color, height=55, width=screen_width)
    top_bar.place(x=0, y=0, relwidth=1)

    tf = tk.Frame(success_win, bg="black")
    tf.place(relx=0.5, rely=0.4, anchor="center")

    lbl1 = tk.Label(tf, text="Success!", font=("Helvetica", 28, "bold"), bg="black", fg="white", wraplength=int(screen_width*0.8), justify="center")
    lbl1.pack(pady=(0, 30))
    lbl2 = tk.Label(tf, text=f"Players Joined: {players_joined}", font=("Helvetica", 20), bg="black", fg="white", wraplength=int(screen_width*0.8), justify="center")
    lbl2.pack()

    def advance():
        print(f"DEBUG: Enviando START_TURN|{host_name}|{host_color} para {len(clients)} clientes")
        for conn in clients:
            try:
                conn.sendall(f"START_TURN|{host_name}|{host_color}".encode())
            except Exception as e:
                print(f"Erro ao enviar para cliente: {e}")
        success_win.destroy()
        show_host_turn_page(bar_color)

    # Após 5 segundos, avança para a página do turno do host
    success_win.after(5050, advance)

def show_session_code(session_code):
    win = tk.Toplevel(root, bg="black")
    win.geometry("400x200")
    win.title("Session Code")
    tk.Label(win, text="Session code", bg="black", fg="white", font=("Helvetica", 16, "bold")).pack(pady=(20, 0))
    tk.Label(win, text=session_code, bg="black", fg="yellow", font=("Helvetica", 32, "bold")).pack(pady=10)
    tk.Button(win, text="OK", command=win.destroy, font=("Helvetica", 12)).pack(pady=20)

def show_loading_page(bar_color, session_code=None):
    loading_win = tk.Toplevel(root, bg="black")
    loading_win.overrideredirect(True)
    loading_win.geometry(f"{screen_width}x{screen_height}+0+0")

    # Barra superior colorida
    top_bar = tk.Frame(loading_win, bg=bar_color, height=55, width=screen_width)
    top_bar.place(x=0, y=0, relwidth=1)

    tf = tk.Frame(loading_win, bg="black")
    tf.place(relx=0.5, rely=0.5, anchor="center")

    loading_lbl = tk.Label(tf, text="", font=("Helvetica", 40), bg="black", fg="white")
    loading_lbl.pack(pady=(0, 20))

    waiting_lbl = tk.Label(tf, text="Waiting...", font=("Helvetica", 18), bg="black", fg="white")
    waiting_lbl.pack()

    # Código de sessão (se existir)
    if session_code:
        code_lbl = tk.Label(tf, text=session_code, font=("Helvetica", 24, "bold"), bg="black", fg="yellow")
        code_lbl.pack(pady=(20, 0))

    # Animação da "loading wheel"
    def animate_wheel():
        for c in itertools.cycle(["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]):
            loading_lbl.config(text=c)
            loading_lbl.update()
            if not getattr(loading_win, "running", True):
                break
            loading_lbl.after(100)
    loading_win.running = True
    threading.Thread(target=animate_wheel, daemon=True).start()

    # Para fechar a janela depois (quando o jogo começar), faz: loading_win.running = False; loading_win.destroy()

def show_host_turn_page(bar_color):
    global tf
    turn_win = tk.Toplevel(root, bg="black")
    turn_win.overrideredirect(True)
    turn_win.geometry(f"{screen_width}x{screen_height}+0+0")

    # Barra superior colorida
    top_bar = tk.Frame(turn_win, bg=bar_color, height=55, width=screen_width)
    top_bar.place(x=0, y=0, relwidth=1)

    tf = tk.Frame(turn_win, bg="black")
    tf.place(relx=0.5, rely=0.62, anchor="center")  # Mais espaço em cima

    lbl1 = tk.Label(tf, text="", font=("Helvetica", 22, "bold"), bg="black", fg="white", wraplength=int(screen_width*0.8), justify="center")
    lbl1.pack(pady=(0, 10))
    lbl2 = tk.Label(tf, text="", font=("Helvetica", 18), bg="black", fg="white", wraplength=int(screen_width*0.8), justify="center")
    lbl2.pack(pady=(0, 30))

    dice_btn = None
    go_btn = None

    def after_texts():
        nonlocal dice_btn, go_btn
        # Mostra o dado em branco
        blank_img_path = os.path.join(IMG_DIR, "dice", "Dice_blank.png")
        dice_img = ImageTk.PhotoImage(Image.open(blank_img_path).resize((100,100)))
        dice_btn = tk.Label(tf, image=dice_img, bg="black")
        dice_btn.image = dice_img
        dice_btn.pack(pady=20)

        go_btn = tk.Button(tf, text="Go!", font=("Helvetica", 16, "bold"), bg="#005c75", fg="white")

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
                    tf.after(100, animate, i+1)
                else:
                    img_path = os.path.join(IMG_DIR, "dice", f"Dice_{final}.png")
                    img = ImageTk.PhotoImage(Image.open(img_path).resize((100,100)))
                    dice_btn.config(image=img)
                    dice_btn.image = img
                    tf.after(5000, lambda: mostrar_nome_casa(final))
            animate()

        def mostrar_nome_casa(steps):
            dice_btn.pack_forget()
            # Esconde as frases do topo
            lbl1.pack_forget()
            lbl2.pack_forget()
            old = jogador.pos
            jogador.pos = (jogador.pos + steps) % NUM_CASAS
            tipo, casa_cor = BOARD[jogador.pos]
            cor_map = {
                "green": "#00FF00",
                "yellow": "#FFD600",
                "red": "#FF0000",
                "blue": "#0070FF",
                "neutral": "#AAAAAA"
            }
            cor_hex = cor_map.get(casa_cor, "#FFFFFF")
            nome_lbl = tk.Label(tf, text=tipo.upper(), font=("Helvetica", 22, "bold"), fg=cor_hex, bg="black", wraplength=int(screen_width*0.8), justify="center")
            nome_lbl.pack(pady=10)

            def depois_nome():
                nome_lbl.pack_forget()
                if casa_cor == jogador.color or casa_cor == "neutral":
                    mostrar_carta(jogador, casa_cor, tipo)
                else:
                    info_lbl = tk.Label(tf, text="Square of other player.", font=("Helvetica", 14), bg="black", fg="white", wraplength=int(screen_width*0.8), justify="center")
                    info_lbl.pack(pady=10)
            tf.after(5000, depois_nome)

        go_btn.config(command=roll_animation)
        go_btn.pack(pady=(0, 5))

    animate_typing(lbl1, "It's your turn!", delay=60,
        callback=lambda: animate_typing(lbl2, "Roll the dice to start your adventure.", delay=60, callback=after_texts)
    )

def show_main_menu():
    main_win = tk.Toplevel(root, bg="black")
    main_win.overrideredirect(True)
    main_win.geometry(f"{screen_width}x{screen_height}+0+0")

    # Barra superior com logo NetMaster ao centro
    top_bar = tk.Frame(main_win, bg="black", height=60, width=screen_width)
    top_bar.place(x=0, y=0, relwidth=1)
    tk.Label(top_bar, image=netmaster_img, bg="black").place(relx=0.5, y=10, anchor="n")

    # Texto inicial
    init_tf = tk.Frame(main_win, bg="black")
    init_tf.place(relx=0.5, rely=0.32, anchor="center")
    il1 = tk.Label(init_tf, text="", font=("Helvetica", 18, "bold"), bg="black", fg="white", wraplength=int(screen_width*0.8), justify="center")  # AUMENTADO
    il2 = tk.Label(init_tf, text="", font=("Helvetica", 12), bg="black", fg="white", wraplength=int(screen_width*0.8), justify="center")        # AUMENTADO
    il1.pack(pady=(0,8))
    il2.pack(pady=(0,12))

    # Botões iniciais
    btn_frame = tk.Frame(main_win, bg="black")
    def show_buttons():
        # Botões mais baixos (rely=0.65)
        btn_frame.place(relx=0.5, rely=0.68, anchor="center")
        tk.Button(
            btn_frame,
            image=create_icon,
            bd=0,
            bg="black",
            activebackground="black",
            highlightthickness=0,
            command=lambda: [main_win.destroy(), open_name_input()]
        ).pack(side=tk.TOP, pady=10)
        tk.Button(
            btn_frame,
            image=search_icon,
            bd=0,
            bg="black",
            activebackground="black",
            highlightthickness=0,
            command=lambda: [main_win.destroy(), open_name_input()]  # ou outra função para "Join Game"
        ).pack(side=tk.TOP, pady=10)

    animate_typing(il1, "Welcome to NetMaster! 👋", delay=50,
                   callback=lambda: animate_typing(il2, "What would you like to do today?", delay=40, callback=show_buttons))

if __name__ == "__main__":
    print("A iniciar aplicação NetMaster...")
    root.attributes("-fullscreen", True)  
    show_main_menu()  
    check_gpio_key()
    root.mainloop()

