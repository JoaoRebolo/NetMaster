from PIL import Image, ImageTk
import os
import RPi.GPIO as GPIO
import tkinter as tk  # Importação do tkinter
import threading
import socket
import random
import string
import itertools
import netifaces

LOCAL_PORT = 5050
DISCOVERY_PORT = 5001
TCP_PORT = LOCAL_PORT  # Usa a mesma porta TCP do teu servidor

# Caminho para imagens e onde guardar o nome
IMG_DIR = "/home/joao_rebolo/netmaster_menu/img"
USERNAME_FILE = "/home/joao_rebolo/netmaster_menu/username.txt"
CARTAS_DIR = os.path.join(IMG_DIR, "cartas")

# GPIO setup para botão KEY1
KEY1_PIN = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(KEY1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Variável global do estado do teclado (uppercase / lowercase)
keyboard_state = "uppercase"

clients = []  # Lista de clientes conectados

# Tipos de carta e cores
CARD_TYPES = ["users", "action", "equipment", "challenges", "data", "events", "service"]
COLORS = ["green", "yellow", "red", "blue", "neutral"]

# Baralhos: dict do tipo {'green': {'users': [lista de paths], ...}, ...}
baralhos = {}

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
            pasta = os.path.join(CARTAS_DIR, cor, tipo)
            if os.path.exists(pasta):
                cartas = [os.path.join(pasta, f) for f in os.listdir(pasta) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                random.shuffle(cartas)
                baralhos[cor][tipo] = cartas
            else:
                baralhos[cor][tipo] = []
preparar_baralhos()

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
        "green": "#00FF00",
        "yellow": "#FFD600",
        "red": "#FF0000",
        "blue": "#0070FF",
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
    global tf
    # Caminho para a imagem do verso da carta (usa o nome do ficheiro que colocaste, por exemplo "netmaster_card_back.png")
    verso_path = os.path.join(CARTAS_DIR, "back_card.png")  # ou "verso.png" se for esse o nome
    if not os.path.exists(verso_path):
        verso_path = os.path.join(CARTAS_DIR, "verso.png")  # fallback

    img = ImageTk.PhotoImage(Image.open(verso_path).resize((220, 320)))  # ajusta o tamanho se quiseres
    carta_lbl = tk.Label(tf, image=img, bg="black")
    carta_lbl.image = img
    carta_lbl.pack(pady=10)

    def revelar_carta():
        carta_lbl.destroy()
        go_btn.destroy()
        carta_path = tirar_carta(casa_cor, tipo)
        if carta_path and os.path.exists(carta_path):
            carta_img = ImageTk.PhotoImage(Image.open(carta_path).resize((220, 320)))
            carta_real_lbl = tk.Label(tf, image=carta_img, bg="black")
            carta_real_lbl.image = carta_img
            carta_real_lbl.pack(pady=10)
        else:
            tk.Label(tf, text="Sem cartas disponíveis!", font=("Helvetica", 14), bg="black", fg="white").pack(pady=10)

    go_btn = tk.Button(tf, text="Go!", font=("Helvetica", 16, "bold"), bg="#005c75", fg="white", command=revelar_carta)
    go_btn.pack(pady=5)

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

    if keyboard_state == "uppercase":
        rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
    else:
        rows = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]

    for row in rows:
        rf = tk.Frame(keyboard_frame, bg="white")  # fundo branco
        rf.pack()
        for ch in row:
            tk.Button(rf, text=ch, width=2, command=lambda c=ch: add_char(c), bg="white", fg="black", activebackground="white", activeforeground="black").pack(side=tk.LEFT, padx=1, pady=1)

    ctrl = tk.Frame(keyboard_frame, bg="white")  # fundo branco
    ctrl.pack(pady=5)
    tk.Button(ctrl, text="Space", width=5, command=space, bg="white", fg="black", activebackground="white", activeforeground="black").pack(side=tk.LEFT, padx=2)
    tk.Button(ctrl, text="Back", width=5, command=backspace, bg="white", fg="black", activebackground="white", activeforeground="black").pack(side=tk.LEFT, padx=2)
    tk.Button(ctrl, text="Enter", width=5, command=enter_key, bg="white", fg="black", activebackground="white", activeforeground="black").pack(side=tk.LEFT, padx=2)
    tk.Button(ctrl, text="ABC", width=5, command=toggle_keyboard_state, bg="white", fg="black", activebackground="white", activeforeground="black").pack(side=tk.LEFT, padx=2)

# Alternar uppercase/lowercase
def toggle_keyboard_state():
    global keyboard_state
    keyboard_state = "lowercase" if keyboard_state == "uppercase" else "uppercase"
    update_keyboard()

# Mostrar teclado flutuante ao focar na entry
def show_keyboard(event=None):
    update_keyboard()
    keyboard_frame.place(relx=0.5, rely=0.9, anchor="s")

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

# Carregar imagens dos logos e ícones
print("A carregar logo IST...")
ist_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "logo_ist_icon_v4.png")).resize((100,70)))
print("A carregar logo NetMaster...")
netmaster_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "logo_netmaster_icon_v3.png")).resize((80,40)))
print("A carregar logo INESC...")
inesc_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "logo_inesc_icon_v2.png")).resize((60,40)))
create_icon = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "create_game_icon_button.png")).resize((100,100)))
search_icon = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "search_game_icon_button.png")).resize((100,100)))

# Definição de open_name_input
def open_name_input():
    global user_window, name_entry, keyboard_frame
    user_window = tk.Toplevel(root, bg="black")  # fundo preto
    user_window.overrideredirect(True)
    user_window.geometry(f"{screen_width}x{screen_height}+0+0")

    # logos no topo
    tk.Label(user_window, image=ist_img, bg="black").place(x=0, y=10, anchor="nw")
    tk.Label(user_window, image=netmaster_img, bg="black").place(relx=0.5, y=10, anchor="n")
    tk.Label(user_window, image=inesc_img, bg="black").place(relx=1.0, x=-10, y=10, anchor="ne")

    # texto animado
    tf = tk.Frame(user_window, bg="black")
    tf.place(relx=0.5, rely=0.3, anchor="center")
    l1 = tk.Label(tf, text="", font=("Helvetica",18,"bold"), bg="black", fg="white")
    l2 = tk.Label(tf, text="", font=("Helvetica",16), bg="black", fg="white")
    l1.pack()
    l2.pack()

    # input
    input_fr = tk.Frame(user_window, bg="black")
    name_entry = tk.Entry(input_fr, font=("Helvetica",14), width=22, justify="center")
    name_entry.bind("<Button-1>", show_keyboard)
    submit_btn = tk.Button(input_fr, text="Submit", font=("Helvetica",12,"bold"),
                           command=submit_name, bg="#005c75", fg="white")

    def show_input():
        input_fr.place(relx=0.5, rely=0.4, anchor="n")
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

    tk.Label(up, image=ist_img, bg="black").place(x=0, y=10, anchor="nw")
    tk.Label(up, image=netmaster_img, bg="black").place(relx=0.5, y=10, anchor="n")
    tk.Label(up, image=inesc_img, bg="black").place(relx=1.0, x=-10, y=10, anchor="ne")

    # texto animado exibindo nome
    tf = tk.Frame(up, bg="black")
    tf.place(relx=0.5, rely=0.35, anchor="center")
    lbl1 = tk.Label(tf, text="", font=("Helvetica",18,"bold"), bg="black", fg="#6F0DB6")
    lbl2 = tk.Label(tf, text="", font=("Helvetica",14), bg="black", fg="white")
    lbl1.pack()
    lbl2.pack()

    def show_buttons():
        bf = tk.Frame(up, bg="black")
        bf.place(relx=0.5, rely=0.6, anchor="center")
        # ícones de cor
        for color, fname in [("Red","red_user_button_icon.png"),
                             ("Green","green_user_button_icon.png"),
                             ("Blue","blue_user_button_icon.png"),
                             ("Yellow","yellow_user_button_icon.png")]:
            icon = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, fname)).resize((65,65)))
            tk.Button(
                bf,
                image=icon,
                bd=0,
                bg="black",
                activebackground="black",
                highlightthickness=0,  # <-- remove moldura de foco
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
    # O nome já foi passado antes, guarda-o também
    try:
        with open(USERNAME_FILE, "r") as f:
            host_name = f.read().strip()
    except:
        host_name = "Host"
    # Cria o jogador aqui!
    jogador = Player(host_name, host_color.lower(), START_POSITIONS[host_color.lower()])
    cp = tk.Toplevel(root, bg="black")
    cp.overrideredirect(True)
    cp.geometry(f"{screen_width}x{screen_height}+0+0")

    # Barra superior colorida
    color_map = {
        "Red": "#FF0000",
        "Green": "#00FF00",
        "Blue": "#0070FF",
        "Yellow": "#FFD600"
    }
    bar_color = color_map.get(color, "white")
    top_bar = tk.Frame(cp, bg=bar_color, height=55, width=screen_width)
    top_bar.place(x=0, y=0, relwidth=1)

    # Frame central (texto)
    tf = tk.Frame(cp, bg="black")
    tf.place(relx=0.5, rely=0.4, anchor="center")  # igual à página inicial

    # Label "Great!" (igual à página inicial)
    great_lbl = tk.Label(tf, text="", font=("Helvetica", 18, "bold"), bg="black", fg="white")
    great_lbl.pack()

    # Label "How do you want to play?" (igual à página inicial)
    how_lbl = tk.Label(tf, text="", font=("Helvetica", 14), bg="black", fg="white")
    how_lbl.pack()

    # Função para mostrar os botões após a animação
    def show_play_buttons():
        btns_frame = tk.Frame(cp, bg="black")
        btns_frame.place(relx=0.5, rely=0.75, anchor="center")

        local_icon = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "local_game_icon_button.png")).resize((115, 130)))
        remote_icon = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "remote_game_icon_button.png")).resize((115, 130)))

        def launch_local():
            cp.destroy()  # Fecha a janela de escolha de cor/modo
            show_host_turn_page(bar_color)

        def launch_remote():
            cp.destroy()
            show_host_turn_page(bar_color)

        tk.Button(
            btns_frame,
            image=local_icon,
            bd=0,
            bg="black",
            activebackground="black",
            highlightthickness=0,
            command=launch_local
        ).pack(side=tk.LEFT, padx=20)
        cp.local_icon = local_icon  # manter referência

        tk.Button(
            btns_frame,
            image=remote_icon,
            bd=0,
            bg="black",
            activebackground="black",
            highlightthickness=0,
            command=launch_remote
        ).pack(side=tk.LEFT, padx=20)
        cp.remote_icon = remote_icon  # manter referência

    # Animação em cadeia
    animate_typing(great_lbl, "Great!", delay=60,
        callback=lambda: animate_typing(how_lbl, "How do you want to play?", delay=40, callback=show_play_buttons)
    )

def generate_session_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

#def register_mdns_service(name, port=LOCAL_PORT):
#    """Regista _netmaster._tcp.local. para descoberta mDNS/Avahi."""
#    zeroconf = Zeroconf()
#    ip_addr = socket.inet_aton(get_local_ip())
#    info = ServiceInfo(
#        "_netmaster._tcp.local.",
#        f"{name}._netmaster._tcp.local.",
#        addresses=[ip_addr],
#        port=port,
#        properties={}
#    )
#    zeroconf.register_service(info)
#    return zeroconf, info


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

    lbl1 = tk.Label(tf, text="Success!", font=("Helvetica", 28, "bold"), bg="black", fg="white")
    lbl1.pack(pady=(0, 30))
    lbl2 = tk.Label(tf, text=f"Players Joined: {players_joined}", font=("Helvetica", 20), bg="black", fg="white")
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

# def start_local_server(bar_color=None, host_color=None):
#     def server_thread():
#         global clients
#         clients = []  # limpa a lista de clientes!
#         chosen_colors = set()
#         if host_color:
#             chosen_colors.add(host_color)
#         # --- ANÚNCIO mDNS ---
#         host_name = "NetMasterHost"  # ou usa o nome do utilizador, se quiseres
#         #zeroconf, info = register_mdns_service(host_name, port=5050)
#         #print("DEBUG: Serviço mDNS registado!")
#         print("Servidor LOCAL pronto em 0.0.0.0:5050")
#         server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         server.bind(('0.0.0.0', 5050))
#         server.listen(4)
#         server.settimeout(1)
#         import time
#         t0 = time.time()
#         try:
#             while time.time() - t0 < 60 and len(clients) < 4:
#                 try:
#                     conn, addr = server.accept()
#                     conn.settimeout(10)
#                     print(f"DEBUG: Ligação aceite de {addr}")

#                     # Envia as cores já escolhidas
#                     cores_str = ",".join(list(chosen_colors))
#                     if not cores_str:
#                         cores_str = " "  # nunca vazio!
#                     print(f"DEBUG: A enviar cores para o cliente: '{cores_str}'")
#                     conn.sendall(cores_str.encode())
#                     print("DEBUG: cores enviadas para o cliente, à espera da cor do cliente...")
#                     try:
#                         color = conn.recv(1024).decode().strip()
#                     except socket.timeout:
#                         print(f"Timeout à espera da cor do jogador {addr}")
#                         conn.close()
#                         continue
#                     if not color:
#                         print(f"Cliente {addr} não enviou cor, fechando ligação.")
#                         conn.close()
#                         continue
#                     if color not in chosen_colors:
#                         chosen_colors.add(color)
#                         clients.append(conn)
#                         print(f"Jogador {addr} entrou com cor {color}. Total: {len(clients)}")
#                     else:
#                         conn.close()
#                 except socket.timeout:
#                     pass
#             print(f"Timer terminado ou capacidade máxima atingida. Jogadores: {len(clients)}")
#             if len(clients) > 0:
#                 root.after(0, lambda: show_success_page(bar_color, len(clients)))
#             else:
#                 print("Nenhum jogador válido entrou na sessão.")
#         finally:
#             pass  # Não é necessário fazer nada aqui, mas o bloco não pode estar vazio

#     threading.Thread(target=server_thread, daemon=True).start()

# def start_remote_server(show_code_callback=None, session_code=None, bar_color=None, host_color=None):
#     def server_thread():
#         global clients, chosen_colors
#         clients = []
#         chosen_colors = set()
#         if host_color:
#             chosen_colors.add(host_color)
#         if show_code_callback:
#             show_code_callback(session_code)
#         print(f"Código de sessão REMOTO: {session_code}")
#         server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         server.bind(('0.0.0.0', 6000))
#         server.listen(4)
#         server.settimeout(1)
#         import time
#         t0 = time.time()
#         while time.time() - t0 < 30 and len(clients) < 4:
#             try:
#                 conn, addr = server.accept()
#                 conn.settimeout(5)
#                 received_code = conn.recv(1024).decode().strip()
#                 if received_code != session_code:
#                     conn.sendall(b"INVALID_SESSION_CODE")
#                     conn.close()
#                     continue
#                 conn.sendall((','.join(chosen_colors)).encode())
#                 try:
#                     color = conn.recv(1024).decode().strip()
#                 except socket.timeout:
#                     print(f"Timeout à espera da cor do jogador {addr}")
#                     conn.close()
#                     continue
#                 if not color:
#                     print(f"Cliente {addr} não enviou cor, fechando ligação.")
#                     conn.close()
#                     continue
#                 if color not in chosen_colors:
#                     chosen_colors.add(color)
#                     clients.append(conn)
#                     print(f"Jogador {addr} entrou com cor {color}. Total: {len(clients)}")
#                 else:
#                     conn.close()
#             except socket.timeout:
#                 pass

#         # Após o timer, aceita rapidamente todas as ligações pendentes (máx 1s)
#         end_time = time.time() + 1
#         while time.time() < end_time:
#             try:
#                 conn, addr = server.accept()
#                 conn.settimeout(5)
#                 received_code = conn.recv(1024).decode().strip()
#                 if received_code != session_code:
#                     conn.sendall(b"INVALID_SESSION_CODE")
#                     conn.close()
#                     continue
#                 conn.sendall((','.join(chosen_colors)).encode())
#                 try:
#                     color = conn.recv(1024).decode().strip()
#                 except socket.timeout:
#                     print(f"Timeout à espera da cor do jogador {addr}")
#                     conn.close()
#                     continue
#                 if not color:
#                     print(f"Cliente {addr} não enviou cor, fechando ligação.")
#                     conn.close()
#                     continue
#                 if color not in chosen_colors:
#                     chosen_colors.add(color)
#                     clients.append(conn)
#                     print(f"Jogador {addr} entrou com cor {color}. Total: {len(clients)}")
#                 else:
#                     conn.close()
#             except socket.timeout:
#                 break

#         print(f"Timer terminado ou capacidade máxima atingida. Jogadores: {len(clients)}")
#         if len(clients) > 0:
#             root.after(0, lambda: show_success_page(bar_color, len(clients)))
#         else:
#             print("Nenhum jogador válido entrou na sessão.")
#     threading.Thread(target=server_thread, daemon=True).start()

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

    # Loading wheel (simples animação de texto)
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
    tf.place(relx=0.5, rely=0.6, anchor="center")

    lbl1 = tk.Label(tf, text="", font=("Helvetica", 22, "bold"), bg="black", fg="white", wraplength=600, justify="center")
    lbl1.pack(pady=(0, 10))
    lbl2 = tk.Label(tf, text="", font=("Helvetica", 18), bg="black", fg="white", wraplength=600, justify="center")
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
            nome_lbl = tk.Label(tf, text=tipo.upper(), font=("Helvetica", 22, "bold"), fg=cor_hex, bg="black")
            nome_lbl.pack(pady=10)

            def depois_nome():
                nome_lbl.pack_forget()
                if casa_cor == jogador.color or casa_cor == "neutral":
                    mostrar_carta(jogador, casa_cor, tipo)
                else:
                    info_lbl = tk.Label(tf, text="Square of other player.", font=("Helvetica", 14), bg="black", fg="white")
                    info_lbl.pack(pady=10)
            tf.after(5000, depois_nome)

        go_btn.config(command=roll_animation)
        go_btn.pack(pady=(0, 5))

    animate_typing(lbl1, "It's your turn!", delay=60,
        callback=lambda: animate_typing(lbl2, "Roll the dice to start your adventure.", delay=60, callback=after_texts)
    )
# --- CÓDIGO NOVO AQUI ---
def show_main_menu():
    main_win = tk.Toplevel(root, bg="black")
    main_win.overrideredirect(True)
    main_win.geometry(f"{screen_width}x{screen_height}+0+0")

    # Logos no topo
    tk.Label(main_win, image=ist_img, bg="black").place(x=0, y=10, anchor="nw")
    tk.Label(main_win, image=netmaster_img, bg="black").place(relx=0.5, y=10, anchor="n")
    tk.Label(main_win, image=inesc_img, bg="black").place(relx=1.0, x=-10, y=10, anchor="ne")

    # Texto inicial
    init_tf = tk.Frame(main_win, bg="black")
    init_tf.place(relx=0.5, rely=0.3, anchor="center")
    il1 = tk.Label(init_tf, text="", font=("Helvetica",18,"bold"), bg="black", fg="white")
    il2 = tk.Label(init_tf, text="", font=("Helvetica",14), bg="black", fg="white")
    il1.pack()
    il2.pack()

    # Botões iniciais
    btn_frame = tk.Frame(main_win, bg="black")
    def show_buttons():
        btn_frame.place(relx=0.5, rely=0.6, anchor="center")
        tk.Button(
            btn_frame,
            image=create_icon,
            bd=0,
            bg="black",
            activebackground="black",
            highlightthickness=0,
            command=lambda: [main_win.destroy(), open_name_input()]
        ).pack(side=tk.LEFT, padx=20)
        tk.Button(
            btn_frame,
            image=search_icon,
            bd=0,
            bg="black",
            activebackground="black",
            highlightthickness=0,
            command=lambda: [main_win.destroy(), open_name_input()]  # ou outra função para "Join Game"
        ).pack(side=tk.LEFT, padx=20)

    animate_typing(il1, "Hey there, NetMaster! 👋", delay=50,
                   callback=lambda: animate_typing(il2, "What would you like to do today?", delay=40, callback=show_buttons))

if __name__ == "__main__":
    print("A iniciar aplicação NetMaster...")
    check_gpio_key()
    show_main_menu()
    root.mainloop()

