import tkinter as tk
from PIL import Image, ImageTk
import os
try:
    import RPi.GPIO as GPIO
except ImportError:
    # Mock para ambiente de desenvolvimento sem GPIO
    class MockGPIO:
        BCM = "BCM"
        IN = "IN"
        PUD_UP = "PUD_UP"
        LOW = False
        @staticmethod
        def setmode(mode): pass
        @staticmethod  
        def setup(pin, mode, pull_up_down=None): pass
        @staticmethod
        def input(pin): return True
        @staticmethod
        def cleanup(): pass
    GPIO = MockGPIO()
import random
import glob

IMG_DIR = os.path.join(os.path.dirname(__file__), "img")

# Detectar automaticamente onde estão as cartas
def detect_cartas_base_dir():
    """Detecta automaticamente o diretório base das cartas"""
    possible_dirs = [
        # Raspberry Pi
        "/home/joao_rebolo/netmaster_menu/img/cartas",
        # Desenvolvimento local
        "/Users/joaop_27h1t5j/Desktop/IST/Bolsa/cartas_netmaster/Bin/Residential-Level",
        # Fallback local
        os.path.join(os.path.dirname(__file__), "img", "cartas")
    ]
    
    for dir_path in possible_dirs:
        if os.path.exists(dir_path):
            print(f"DEBUG: Usando diretório de cartas: {dir_path}")
            return dir_path
    
    print("DEBUG: Nenhum diretório de cartas encontrado!")
    return possible_dirs[0]  # fallback

CARTAS_BASE_DIR = detect_cartas_base_dir()
COIN_IMG = os.path.join(IMG_DIR, "picoin.png")
AWNING_IMG = os.path.join(IMG_DIR, "Store_awning_v2.png")
BELOWBAR_IMG = os.path.join(IMG_DIR, "BelowBar_store.png")

KEY1_PIN = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(KEY1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

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

CARD_TYPES = ["users", "actions", "equipments", "challenges", "activities", "events", "services"]
COLORS = ["green", "yellow", "red", "blue", "neutral"]

def check_gpio_key(root):
    if GPIO.input(KEY1_PIN) == GPIO.LOW:
        GPIO.cleanup()
        root.destroy()
    root.after(100, lambda: check_gpio_key(root))

# Carregar baralhos adaptado à nova estrutura: cartas/[tipo]/Residential-level/[cor]/
def preparar_baralhos():
    baralhos = {}
    for cor in COLORS:
        baralhos[cor] = {}
        for tipo in CARD_TYPES:
            cartas = []
            
            # Tentar múltiplas estruturas de pastas
            possible_paths = []
            
            # Para cartas que têm cores específicas (equipments, services, users, activities)
            if tipo in ["equipments", "services", "users", "activities"]:
                # Mapear cor do jogador para diferentes formatos de nome
                color_variants = []
                if cor == "blue":
                    color_variants = ["Blue", "blue", "BLUE"]
                elif cor == "green": 
                    color_variants = ["Green", "green", "GREEN"]
                elif cor == "red":
                    color_variants = ["Red", "red", "RED"]
                elif cor == "yellow":
                    color_variants = ["Yellow", "yellow", "YELLOW"]
                else:  # neutral - adicionar todas as cores
                    color_variants = ["Blue", "Green", "Red", "Yellow", "blue", "green", "red", "yellow"]
                
                if cor != "neutral":
                    # Estruturas possíveis para cores específicas:
                    for color_var in color_variants:
                        # 1. cartas/[tipo]/Residential-level/[cor]/
                        possible_paths.append(os.path.join(CARTAS_BASE_DIR, tipo, "Residential-level", color_var))
                        # 2. cartas/Residential-[tipo]-[cor]/
                        possible_paths.append(os.path.join(CARTAS_BASE_DIR, f"Residential-{tipo}-{color_var}"))
                        # 3. cartas/[tipo]/[cor]/
                        possible_paths.append(os.path.join(CARTAS_BASE_DIR, tipo, color_var))
                else:
                    # Para neutral, tentar todas as cores
                    for color_var in color_variants:
                        possible_paths.append(os.path.join(CARTAS_BASE_DIR, tipo, "Residential-level", color_var))
                        possible_paths.append(os.path.join(CARTAS_BASE_DIR, f"Residential-{tipo}-{color_var}"))
                        possible_paths.append(os.path.join(CARTAS_BASE_DIR, tipo, color_var))
            else:
                # Para cartas sem cor específica (challenges, events, actions)
                # Estruturas possíveis:
                possible_paths = [
                    # 1. cartas/[tipo]/Residential-level/
                    os.path.join(CARTAS_BASE_DIR, tipo, "Residential-level"),
                    # 2. cartas/Residential-[tipo]/
                    os.path.join(CARTAS_BASE_DIR, f"Residential-{tipo}"),
                    # 3. cartas/[tipo]/
                    os.path.join(CARTAS_BASE_DIR, tipo)
                ]
            
            # Tentar encontrar cartas em qualquer uma das estruturas possíveis
            for path in possible_paths:
                if os.path.exists(path):
                    try:
                        card_files = [os.path.join(path, f) for f in os.listdir(path) 
                                    if f.lower().endswith((".png", ".jpg", ".jpeg"))]
                        if card_files:
                            cartas.extend(card_files)
                            print(f"DEBUG: Found {len(card_files)} cards at {path}")
                    except Exception as e:
                        print(f"DEBUG: Error reading {path}: {e}")
                        continue
            
            # Remover duplicatas mantendo ordem
            seen = set()
            unique_cartas = []
            for carta in cartas:
                if carta not in seen:
                    seen.add(carta)
                    unique_cartas.append(carta)
            cartas = unique_cartas
            
            if cartas:
                random.shuffle(cartas)
                baralhos[cor][tipo] = cartas.copy()
                print(f"DEBUG: Total {len(cartas)} cards for '{tipo}' color '{cor}'")
            else:
                baralhos[cor][tipo] = []
                print(f"DEBUG: No cards found for type '{tipo}' color '{cor}'")
                print(f"DEBUG: Tried paths: {possible_paths}")
    
    print("Cartas neutral/actions:", len(baralhos.get("neutral", {}).get("actions", [])))
    return baralhos

baralhos = preparar_baralhos()

def tirar_carta(cor, tipo):
    """Tira a carta do topo do baralho da cor e tipo dados."""
    print(f"DEBUG: tirar_carta chamado com cor={cor!r}, tipo={tipo!r}")
    cartas = baralhos.get(cor, {}).get(tipo, [])
    print(f"DEBUG: cartas da cor {cor} e tipo {tipo}: {len(cartas)} cartas disponíveis")
    if cartas:
        carta = cartas.pop(0)
        print(f"DEBUG: Carta tirada: {carta}")
        return carta
    # Se não houver cartas dessa cor/tipo, tenta neutral
    cartas_neutral = baralhos.get("neutral", {}).get(tipo, [])
    print(f"DEBUG: cartas neutral do tipo {tipo}: {len(cartas_neutral)} cartas disponíveis")
    if cartas_neutral:
        carta = cartas_neutral.pop(0)
        print(f"DEBUG: Carta neutral tirada: {carta}")
        return carta
    print(f"DEBUG: Nenhuma carta disponível para cor={cor}, tipo={tipo}")
    return None  # Não há cartas

class StoreWindow(tk.Toplevel):
    def __init__(self, root, player_color, player_name, saldo=1000, casa_tipo=None, casa_cor=None, inventario=None, dashboard=None, other_player_house=False):
        super().__init__(root)
        self.title("Store")
        self.configure(bg="black")
        self.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
        self.overrideredirect(True)
        self.player_color = player_color.lower()  # Guarda o nome da cor
        self.player_name = player_name
        self.inventario = inventario # Inventário do jogador: {tipo: [lista_de_cartas]}
        self.dashboard = dashboard  # Referência direta ao PlayerDashboard
        self.other_player_house = other_player_house  # Se é uma casa de outro jogador
        self.saldo = saldo  # Guarda o saldo atual
        self.casa_tipo = casa_tipo
        self.casa_cor = casa_cor
        
        # Debug do inventário
        if inventario:
            for tipo, cartas in inventario.items():
                if cartas:  # Só mostra se houver cartas
                    print(f"DEBUG: Store init - {tipo}: {len(cartas)} cartas")
        else:
            print("DEBUG: Store init - inventário vazio ou None")

        # Barra superior com imagem Store_awning.png
        awning_img = ImageTk.PhotoImage(Image.open(AWNING_IMG).resize((root.winfo_screenwidth(), 50)))
        awning_label = tk.Label(self, image=awning_img, bg="black")
        awning_label.image = awning_img  # type: ignore[attr-defined]
        awning_label.pack(pady=(0, 10), fill="x")
        
        # Mapeamento de cor para código hexadecimal
        color_map = {
            "green": "#70AD47",
            "yellow": "#F2BA0D",
            "red": "#EE6F68",
            "blue": "#43BEF2"
        }
        self.player_color_hex = color_map.get(self.player_color, "#AAAAAA")  # Usar para bg dos botões

        # Frame principal para os botões
        main_frame = tk.Frame(self, bg="black")
        main_frame.pack(anchor="center", pady=(0, 10))

        btn_font = ("Helvetica", 18, "bold")
        btn_size = {"width": 8, "height": 5}

        # Primeira linha: Actions, Events, Challenges (neutras) com imagens GRANDES
        img_size = (90, 90)
        actions_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "Actions_button.png")).resize(img_size))
        events_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "Events_button.png")).resize(img_size))
        challenges_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "Challenges_button.png")).resize(img_size))

        btn_a = tk.Button(main_frame, image=actions_img, bg="#000000", activebackground="#000000", width=75, height=80, highlightthickness=0, bd=0)
        btn_e = tk.Button(main_frame, image=events_img, bg="#000000", activebackground="#000000", width=75, height=80, highlightthickness=0, bd=0)
        btn_d = tk.Button(main_frame, image=challenges_img, bg="#000000", activebackground="#000000", width=75, height=80, highlightthickness=0, bd=0)

        btn_a.grid(row=0, column=0, padx=10, pady=(5, 2), sticky="n")
        btn_e.grid(row=0, column=1, padx=10, pady=(5, 2), sticky="n")
        btn_d.grid(row=0, column=2, padx=10, pady=(5, 2), sticky="n")

        # Imagens devem ser mantidas como referências
        btn_a.image = actions_img
        btn_e.image = events_img
        btn_d.image = challenges_img

        # Comandos padrão vazios - serão ativados quando destacados
        btn_a.config(command="")
        btn_e.config(command="")
        btn_d.config(command="")

        # Botão para lançar o dado
        # roll_btn = tk.Button(self, text="Lançar Dado", font=("Helvetica", 18, "bold"),
        #                      bg="#A020F0", fg="white", command=self.roll_and_highlight)
        # roll_btn.pack(pady=20)

        self.btn_a = btn_a
        self.btn_e = btn_e
        self.btn_d = btn_d
        self.store_buttons = [btn_a, btn_e, btn_d]

        # Frame para centralizar os botões das cartas do jogador
        players_frame = tk.Frame(self, bg="black")
        players_frame.pack(pady=(0, 0))

        btn_font = ("Helvetica", 18, "bold")

        # Botões para Users, Equipments, Activities, Services (todos com a cor do jogador)
        btn_users = tk.Button(players_frame, text="Users", font=btn_font, bg=self.player_color_hex, fg="black", 
                             relief="flat", borderwidth=0, width=10, height=4)
        btn_equipments = tk.Button(players_frame, text="Equipments", font=btn_font, bg=self.player_color_hex, fg="black", 
                                 relief="flat", borderwidth=0, width=10, height=4)
        btn_activities = tk.Button(players_frame, text="Activities", font=btn_font, bg=self.player_color_hex, fg="black", 
                            relief="flat", borderwidth=0, width=10, height=4)
        btn_services = tk.Button(players_frame, text="Services", font=btn_font, bg=self.player_color_hex, fg="black", 
                                relief="flat", borderwidth=0, width=10, height=4)

        # Aplicar cantos arredondados usando configuração adicional
        for btn in [btn_users, btn_equipments, btn_activities, btn_services]:
            btn.config(relief="flat", borderwidth=0, highlightthickness=0)
            # Configurar cor de fundo ativa igual à cor normal
            btn.config(activebackground=self.player_color_hex, activeforeground="black")

        btn_users.grid(row=0, column=0, padx=10, pady=5)
        btn_equipments.grid(row=0, column=1, padx=10, pady=5)
        btn_activities.grid(row=1, column=0, padx=10, pady=5)
        btn_services.grid(row=1, column=1, padx=10, pady=5)

        self.card_buttons = {
            "users": btn_users,
            "equipments": btn_equipments,
            "activities": btn_activities,
            "services": btn_services
        }

        # Comandos padrão que serão sobrescritos pelos destaques
        # Configurados como vazios inicialmente para serem ativados quando destacados
        btn_users.config(command="")
        btn_equipments.config(command="")
        btn_activities.config(command="")
        btn_services.config(command="")

        # Frame para os botões de ação na parte inferior (inicialmente oculto)
        self.action_frame = tk.Frame(self, bg="black")
        # self.action_frame.pack_propagate(False)  # Removido para não forçar altura
        # self.action_frame.configure(height=60)   # Removido para não forçar altura

        # Sub-frame centralizado para os botões
        self.action_buttons_frame = tk.Frame(self.action_frame, bg="black")
        self.action_buttons_frame.pack(anchor="center", pady=2)  # Pequeno espaçamento inferior
        
        # Botões de ação: Buy, Sell, Skip dentro de frames de tamanho fixo
        action_font = ("Helvetica", 14, "bold")
        frame_width = 100
        frame_height = 50

        self.buy_frame = tk.Frame(self.action_buttons_frame, width=frame_width, height=frame_height, bg="black")
        self.sell_frame = tk.Frame(self.action_buttons_frame, width=frame_width, height=frame_height, bg="black")
        self.skip_frame = tk.Frame(self.action_buttons_frame, width=frame_width, height=frame_height, bg="black")
        self.buy_frame.pack_propagate(False)
        self.sell_frame.pack_propagate(False)
        self.skip_frame.pack_propagate(False)

        btn_buy = tk.Button(self.buy_frame, text="BUY", font=action_font, bg="#4CAF50", fg="white", 
                           relief="flat", borderwidth=0,
                           command=self.buy_action)
        btn_sell = tk.Button(self.sell_frame, text="SELL", font=action_font, bg="#F44336", fg="white", 
                            relief="flat", borderwidth=0,
                            command=self.sell_action)
        btn_skip = tk.Button(self.skip_frame, text="SKIP", font=action_font, bg="#FF9800", fg="white", 
                            relief="flat", borderwidth=0,
                            command=self.skip_action)
        # Destacar cor ativa igual à cor normal
        for btn in [btn_buy, btn_sell, btn_skip]:
            btn.config(activebackground=btn.cget("bg"), activeforeground=btn.cget("fg"))

        # Centralizar cada botão no seu frame
        btn_sell.place(relx=0.5, rely=0.5, anchor="center")
        btn_buy.place(relx=0.5, rely=0.5, anchor="center")
        btn_skip.place(relx=0.5, rely=0.5, anchor="center")

        # Pack frames lado a lado
        self.sell_frame.pack(side="left", padx=10, pady=0)
        self.buy_frame.pack(side="left", padx=10, pady=0)
        self.skip_frame.pack(side="left", padx=10, pady=0)

        self.btn_buy = btn_buy
        self.btn_sell = btn_sell
        self.btn_skip = btn_skip

        # Variáveis para controlar estado de navegação
        self.current_card_type = None  # Tipo de carta atual para compra
        self.current_sell_type = None  # Tipo de carta sendo vendida
        self.current_sell_page = 0     # Página atual de venda

        # Inicia verificação do botão físico KEY1
        self.check_gpio_key()

        # Se receber casa_tipo e casa_cor, destaca o botão
        if casa_tipo and casa_cor:
            self.highlight_casa(casa_tipo, casa_cor)
        else:
            # Se não houver destaque, desabilitar todos os botões
            self.disable_all_buttons()
        
        # Se for casa de outro jogador, sempre habilita os botões Users, Equipment, Activities, Services
        if self.other_player_house:
            # Configurar comandos para os botões permitidos em casa de outro jogador
            if self.card_buttons.get("users"):
                self.card_buttons["users"].config(command=lambda: self.tirar_carta("users", casa_cor if casa_cor else "neutral"))
            if self.card_buttons.get("equipments"):
                self.card_buttons["equipments"].config(command=lambda: self.tirar_carta("equipments", casa_cor if casa_cor else "neutral"))
            if self.card_buttons.get("activities"):
                self.card_buttons["activities"].config(command=lambda: self.tirar_carta("activities", casa_cor if casa_cor else "neutral"))
            if self.card_buttons.get("services"):
                self.card_buttons["services"].config(command=lambda: self.tirar_carta("services", casa_cor if casa_cor else "neutral"))

        # Barra inferior com imagem BelowBar_store.png
        belowbar_img = ImageTk.PhotoImage(Image.open(BELOWBAR_IMG).resize((root.winfo_screenwidth(), 50)))
        belowbar_label = tk.Label(self, image=belowbar_img, bg="black")
        belowbar_label.image = belowbar_img  # type: ignore[attr-defined]
        belowbar_label.pack(side="bottom", fill="x")

        # Mover saldo e piccoin para parte inferior direita (por cima do BelowBar)
        coin_img_bottom = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24, 24)))
        coin_lbl_bottom = tk.Label(self, image=coin_img_bottom, bg="#DC8392")
        coin_lbl_bottom.image = coin_img_bottom  # type: ignore[attr-defined]
        coin_lbl_bottom.place(x=root.winfo_screenwidth()-100, rely=1.0, y=-25, anchor="w")
        
        saldo_lbl_bottom = tk.Label(self, text=f"{self.saldo}", font=("Helvetica", 16, "bold"), fg="black", bg="#DC8392")
        saldo_lbl_bottom.place(x=root.winfo_screenwidth()-70, rely=1.0, y=-25, anchor="w")

        # Botão do Player no canto superior direito para ir ao PlayerDashboard
        def abrir_playerdashboard():
            """Abre a interface principal do PlayerDashboard (igual ao botão Player das cartas de Challenges)"""
            print("DEBUG: Botão Player pressionado - abrindo interface principal do PlayerDashboard")
            if self.dashboard and hasattr(self.dashboard, "playerdashboard_interface"):
                self.dashboard.playerdashboard_interface(
                    self.dashboard.player_name,
                    self.dashboard.saldo,
                    self.dashboard.other_players
                )
                print("DEBUG: Interface principal do PlayerDashboard aberta com sucesso")
            else:
                print("DEBUG: ERRO - PlayerDashboard não disponível ou método playerdashboard_interface não encontrado")

        try:
            # Carregar ícone do jogador
            user_icon_path = os.path.join(IMG_DIR, f"{self.player_color}_user_icon.png")
            user_icon_img = ImageTk.PhotoImage(Image.open(user_icon_path).resize((48, 48)))
            btn_player = tk.Button(self, image=user_icon_img, bg="black", relief="flat", borderwidth=0, 
                                  command=abrir_playerdashboard, cursor="hand2", activebackground="black",
                                  highlightthickness=0)
            btn_player.image = user_icon_img  # Manter referência para evitar garbage collection
            btn_player.place(x=root.winfo_screenwidth()-15, y=5, anchor="ne")  # Movido mais para a direita e para cima
            print(f"DEBUG: Botão Player criado com ícone {self.player_color}_user_icon.png")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar ícone do jogador {self.player_color}_user_icon.png: {e}")
            # Fallback para botão de texto se não conseguir carregar a imagem
            btn_player = tk.Button(self, text="👤", font=("Helvetica", 20), bg="black", fg="white", 
                                  relief="flat", borderwidth=0, command=abrir_playerdashboard, cursor="hand2",
                                  activebackground="black", activeforeground="white", highlightthickness=0)
            btn_player.place(x=root.winfo_screenwidth()-15, y=5, anchor="ne")  # Movido mais para a direita e para cima
            print("DEBUG: Botão Player criado com ícone de fallback")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar ícone do jogador {self.player_color}_user_icon.png: {e}")
            # Fallback para botão de texto se não conseguir carregar a imagem
            btn_player = tk.Button(self, text="👤", font=("Helvetica", 20), bg="black", fg="white", 
                                  relief="flat", borderwidth=0, command=abrir_playerdashboard, cursor="hand2",
                                  activebackground="black", activeforeground="white")
            btn_player.place(x=root.winfo_screenwidth()-30, y=10, anchor="ne")  # Movido o mais para a direita possível
            print("DEBUG: Botão Player criado com ícone de fallback")

    def __del__(self):
        print("DEBUG: StoreWindow __del__ chamado (janela destruída)")

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

        # Remove destaque anterior de todos os botões
        for btn in getattr(self, "store_buttons", []):
            btn.config(highlightbackground="black", highlightthickness=0)
        for btn in getattr(self, "card_buttons", {}).values():
            btn.config(highlightbackground="black", highlightthickness=0)

        # Mapeia tipo para botão (incluindo os botões de cartas)
        tipo_to_btn = {
            "action": self.btn_a,
            "events": self.btn_e,
            "challenges": self.btn_d,
            "users": self.card_buttons.get("users"),
            "equipment": self.card_buttons.get("equipments"),  # Mapeia 'equipment' para o botão de equipamentos
            "equipments": self.card_buttons.get("equipments"),
            "activities": self.card_buttons.get("activities"),
            "services": self.card_buttons.get("services"),
        }
        btn = tipo_to_btn.get(tipo)
        if btn:
            btn.config(highlightbackground="#A020F0", highlightcolor="#A020F0", highlightthickness=6)
            # Só permite clicar no botão destacado
            btn.config(command=lambda: self.tirar_carta(tipo, casa_cor))
        
        # Não mostra mais os botões de ação automaticamente
        # Os botões de compra/venda agora vão diretamente para a página de compra

    def disable_all_buttons(self):
        """Desabilita todos os botões para que não sejam clicáveis"""
        for btn in getattr(self, "store_buttons", []):
            btn.config(command="")
        
        # Se for casa de outro jogador, não desabilita Users, Equipment, Services
        if self.other_player_house:
            for btn_name, btn in getattr(self, "card_buttons", {}).items():
                if btn_name not in ["users", "equipments", "services"]:
                    btn.config(command="")
        else:
            # Para casas próprias ou neutras, desabilita todos
            for btn in getattr(self, "card_buttons", {}).values():
                btn.config(command="")

    def enable_only_highlighted_button(self, casa_tipo, casa_cor):
        """Habilita apenas o botão destacado e desativa todos os outros (neutros e inventário)."""
        # Desabilita todos os botões neutros
        for btn in getattr(self, "store_buttons", []):
            btn.config(command="")
        # Desabilita todos os botões do inventário
        for btn in getattr(self, "card_buttons", {}).values():
            btn.config(command="")
        # Ativa só o botão correto
        tipo_to_btn = {
            "action": self.btn_a,
            "actions": self.btn_a,
            "events": self.btn_e,
            "challenges": self.btn_d,
            "users": self.card_buttons.get("users"),
            "equipment": self.card_buttons.get("equipments"),
            "equipments": self.card_buttons.get("equipments"),
            "activities": self.card_buttons.get("activities"),
            "services": self.card_buttons.get("services"),
        }
        btn = tipo_to_btn.get(casa_tipo)
        if btn:
            btn.config(command=lambda: self.tirar_carta(casa_tipo, casa_cor))

    def highlight_casa(self, casa_tipo, casa_cor):
        # Remove destaque anterior de todos os botões
        for btn in getattr(self, "store_buttons", []):
            btn.config(highlightbackground="black", highlightthickness=0)
        for btn in getattr(self, "card_buttons", {}).values():
            btn.config(highlightbackground="black", highlightthickness=0)

        # Se for casa de outro jogador, destaca os botões permitidos (Users, Equipments, Activities, Services)
        if self.other_player_house:
            if casa_tipo in ["equipments", "services", "users", "equipment", "activities"]:
                # Destaca todos os botões permitidos para casa de outro jogador
                allowed_buttons = ["users", "equipments", "activities", "services"]
                for btn_name in allowed_buttons:
                    if self.card_buttons.get(btn_name):
                        self.card_buttons[btn_name].config(highlightbackground="#A020F0", highlightcolor="#A020F0", highlightthickness=6)
                        self.card_buttons[btn_name].config(command=lambda t=btn_name: self.tirar_carta(t, casa_cor))
                # Desabilita botões neutros
                self.disable_all_buttons()
                # Reabilita apenas os botões permitidos
                for btn_name in allowed_buttons:
                    if self.card_buttons.get(btn_name):
                        self.card_buttons[btn_name].config(state="normal")
            else:
                # Para casas de outro jogador não permitidas, não destaca nada e desabilita todos
                self.disable_all_buttons()
            return

        # Comportamento normal para casas próprias ou neutras
        tipo_to_btn = {
            "action": self.btn_a,
            "actions": self.btn_a,
            "events": self.btn_e,
            "challenges": self.btn_d,
            "users": self.card_buttons.get("users"),
            "equipment": self.card_buttons.get("equipments"),  # Mapeia 'equipment' para o botão de equipamentos
            "equipments": self.card_buttons.get("equipments"),
            "activities": self.card_buttons.get("activities"),
            "services": self.card_buttons.get("services"),
        }
        btn = tipo_to_btn.get(casa_tipo)
        if btn:
            btn.config(highlightbackground="#A020F0", highlightcolor="#A020F0", highlightthickness=6)
            # Só permite clicar no botão destacado
            # Se a casa for neutra, tira carta da cor neutral
            if casa_cor == "neutral":
                btn.config(command=lambda: self.tirar_carta(casa_tipo, "neutral"))
            else:
                btn.config(command=lambda: self.tirar_carta(casa_tipo, casa_cor))
            # Habilita apenas o botão destacado
            self.enable_only_highlighted_button(casa_tipo, casa_cor)

    def show_action_buttons(self):
        """Mostra os botões de ação na parte inferior do ecrã e destaca-os em roxo"""
        # Remover destaque roxo de todos os botões
        for btn in getattr(self, "store_buttons", []):
            btn.config(highlightbackground="black", highlightthickness=0)
        for btn in getattr(self, "card_buttons", {}).values():
            btn.config(highlightbackground="black", highlightthickness=0)
        # Desabilitar todos os botões quando os botões de ação aparecem
        self.disable_all_buttons()
        
        # Verificar se o jogador tem cartas do tipo correspondente para vender
        current_type = getattr(self, 'current_card_type', None)
        has_cards_to_sell = False
        
        # IMPORTANTE: Garantir que usamos o inventário mais recente do PlayerDashboard
        if hasattr(self, 'dashboard') and self.dashboard and hasattr(self.dashboard, 'inventario'):
            self.inventario = self.dashboard.inventario
            print(f"DEBUG: Inventário da Store sincronizado com o PlayerDashboard no show_action_buttons")
        
        if current_type and self.inventario:
            # Mapear tipos para chaves do inventário
            type_mapping = {
                "equipment": "equipments",
                "equipments": "equipments", 
                "users": "users",
                "services": "services",
                "activities": "activities"
            }
            inventory_key = type_mapping.get(current_type, current_type)
            
            if inventory_key in self.inventario:
                todas_cartas = self.inventario[inventory_key]
                
                # Se for Activities, considerar apenas cartas não ativas
                if inventory_key == "activities":
                    cartas_ativas = []
                    if hasattr(self, 'dashboard') and self.dashboard and hasattr(self.dashboard, 'cards'):
                        cartas_ativas = [carta for carta in self.dashboard.cards if carta in todas_cartas]
                        print(f"DEBUG: Cartas ativas no carrossel: {len(cartas_ativas)}")
                    
                    # Filtrar apenas cartas que não estão ativas
                    cartas_disponiveis = [carta for carta in todas_cartas if carta not in cartas_ativas]
                    cards_count = len(cartas_disponiveis)
                    print(f"DEBUG: Activities disponíveis para venda: {cards_count} de {len(todas_cartas)} totais")
                else:
                    # Para outros tipos, contar todas as cartas
                    cards_count = len(todas_cartas)
                    
                has_cards_to_sell = cards_count > 0
                print(f"DEBUG: Verificando inventário - tipo: {current_type}, chave: {inventory_key}, cartas: {cards_count}")
        
        print(f"DEBUG: show_action_buttons - current_type: {current_type}, has_cards: {has_cards_to_sell}")
        
        # Se for casa de outro jogador, sempre mostra Skip e Sell se tiver cartas
        if self.other_player_house:
            action_buttons = [self.btn_skip]
            if has_cards_to_sell:
                action_buttons.append(self.btn_sell)
                print("DEBUG: Casa outro jogador - adicionando botão Sell")
        else:
            # Casa própria ou neutra - mostra Buy, Sell (se tiver cartas) e Skip
            action_buttons = [self.btn_buy, self.btn_skip]
            if has_cards_to_sell:
                action_buttons.append(self.btn_sell)
                print("DEBUG: Casa própria - adicionando botão Sell")
        
        # Destacar os botões de ação em roxo
        for btn in action_buttons:
            btn.config(highlightbackground="#A020F0", highlightcolor="#A020F0", highlightthickness=6)
        
        # Esconder/mostrar botões conforme necessário
        if self.other_player_house:
            # Casa de outro jogador - esconde Buy, mostra apenas Sell (se tiver cartas) e Skip
            self.buy_frame.pack_forget()
            if has_cards_to_sell:
                self.sell_frame.pack(side="left", padx=10, pady=0)
            else:
                self.sell_frame.pack_forget()
            self.skip_frame.pack(side="left", padx=10, pady=0)
        else:
            # Casa própria ou neutra - comportamento normal
            if has_cards_to_sell:
                self.sell_frame.pack(side="left", padx=10, pady=0)
            else:
                self.sell_frame.pack_forget()
            self.buy_frame.pack(side="left", padx=10, pady=0)
            self.skip_frame.pack(side="left", padx=10, pady=0)
        
        self.action_frame.pack(side="bottom", fill="x", pady=0)

    def hide_action_buttons(self):
        """Esconde os botões de ação e remove o destaque roxo"""
        try:
            # Remove destaque dos botões de ação se existirem
            for btn_name in ['btn_buy', 'btn_sell', 'btn_skip']:
                if hasattr(self, btn_name):
                    btn = getattr(self, btn_name)
                    if btn and hasattr(btn, 'winfo_exists') and btn.winfo_exists():
                        btn.config(highlightbackground="black", highlightcolor="black", highlightthickness=0)
            # Esconde o frame de ação se existir
            if hasattr(self, 'action_frame') and self.action_frame and hasattr(self.action_frame, 'winfo_exists') and self.action_frame.winfo_exists():
                self.action_frame.pack_forget()
            print("DEBUG: hide_action_buttons executado com sucesso")
        except (AttributeError, tk.TclError) as e:
            print(f"DEBUG: Erro em hide_action_buttons (ignorado): {e}")
            # Ignora erros se os widgets não existirem ainda
            pass

    def buy_action(self):
        """Ação do botão Buy: mostra a página de compra de cartas do tipo atual"""
        self.show_buy_page()

    def show_buy_page(self):
        import glob
        from tkinter import messagebox
        # Limpa absolutamente todos os widgets da janela Store
        for widget in self.winfo_children():
            widget.destroy()
        self.update()
        self.configure(bg="black")

        # Barra superior (igual à Store)
        awning_img = ImageTk.PhotoImage(Image.open(AWNING_IMG).resize((self.winfo_screenwidth(), 50)))
        awning_label = tk.Label(self, image=awning_img, bg="black")
        awning_label.image = awning_img  # type: ignore[attr-defined]
        awning_label.pack(pady=(0, 10), fill="x")

        # Título
        tipo_atual = getattr(self, 'current_card_type', None)
        if not tipo_atual:
            messagebox.showinfo("Erro", "Tipo de carta não definido!")
            return
        titulo = tipo_atual.capitalize()
        title_lbl = tk.Label(self, text=f"{titulo}", font=("Helvetica", 22, "bold"), fg="white", bg="black")
        title_lbl.pack(pady=(20, 10))
        
        # Card value info abaixo do título
        value_info_frame = tk.Frame(self, bg="black")
        value_info_frame.pack(pady=(0, 20))
        
        value_text_lbl = tk.Label(value_info_frame, text="Card value: ", 
                                 font=("Helvetica", 16), fg="yellow", bg="black")
        value_text_lbl.pack(side="left")
        
        self._valor_lbl = tk.Label(value_info_frame, text="?", 
                                  font=("Helvetica", 16, "bold"), fg="yellow", bg="black")
        self._valor_lbl.pack(side="left", padx=(5, 5))
        
        # Ícone da moeda
        picoin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24,24)))
        self._picoin_lbl = tk.Label(value_info_frame, image=picoin_img, bg="black")
        self._picoin_lbl.image = picoin_img  # type: ignore[attr-defined]
        self._picoin_lbl.pack(side="left")

        # Obter cartas disponíveis para compra do baralho do jogador
        print(f"DEBUG: Buscando cartas para tipo '{tipo_atual}' e cor '{self.player_color}'")
        
        # Verificar se o tipo existe nos baralhos
        cartas_disp = []
        if self.player_color in baralhos and tipo_atual in baralhos[self.player_color]:
            cartas_disp = baralhos[self.player_color][tipo_atual].copy()
            print(f"DEBUG: Encontradas {len(cartas_disp)} cartas no baralho do jogador")
        
        # Se não houver cartas da cor do jogador, tentar neutral
        if not cartas_disp and "neutral" in baralhos and tipo_atual in baralhos["neutral"]:
            cartas_disp = baralhos["neutral"][tipo_atual].copy()
            print(f"DEBUG: Encontradas {len(cartas_disp)} cartas no baralho neutral")
        
        # Debug adicional
        print(f"DEBUG: Baralhos disponíveis para {self.player_color}:")
        if self.player_color in baralhos:
            for tipo, cartas in baralhos[self.player_color].items():
                print(f"  {tipo}: {len(cartas)} cartas")
        
        if not cartas_disp:
            print(f"DEBUG: Nenhuma carta encontrada para {tipo_atual}")
            tk.Label(self, text="Sem cartas disponíveis para compra!", font=("Helvetica", 16), bg="black", fg="white").pack(pady=20)
            return

        # Carrossel de cartas (duas cartas visíveis) - ajustado para compensar o card value
        self._buy_imgs = [None, None]
        self._buy_paths = cartas_disp
        self._buy_idx = 0  # índice da carta destacada
        self._fullscreen_open = False
        self._carrossel_frame = tk.Frame(self, bg="black")
        self._carrossel_frame.pack(fill="x", pady=(20, 10))  # Reduzido de (60, 10) para (20, 10)

        # Setas em texto Unicode (agora com place)
        seta_esq = tk.Button(self._carrossel_frame, text="\u25C0", font=("Helvetica", 24, "bold"), bg="black", fg="white", bd=0, highlightthickness=0, activebackground="black", activeforeground="#FFD600", cursor="hand2", command=self._carrossel_prev)
        seta_esq.place(relx=0.0, rely=0.5, anchor="w")
        seta_dir = tk.Button(self._carrossel_frame, text="\u25B6", font=("Helvetica", 24, "bold"), bg="black", fg="white", bd=0, highlightthickness=0, activebackground="black", activeforeground="#FFD600", cursor="hand2", command=self._carrossel_next)
        seta_dir.place(relx=1.0, rely=0.5, anchor="e")

        # Duas cartas lado a lado
        self._carta_lbls = []
        def make_card_callback(idx):
            def callback(event):
                n = len(self._buy_paths)
                carta_idx = (self._buy_idx + idx) % n
                print(f"DEBUG: Clique na carta do carrossel - idx relativo: {idx}, idx real: {carta_idx}, buy_idx: {self._buy_idx}")
                if carta_idx != self._buy_idx:
                    print("DEBUG: Mudar destaque para esta carta.")
                    self._buy_idx = carta_idx
                    self._carrossel_update()
                else:
                    print("DEBUG: Abrir carta em fullscreen!")
                    self._abrir_fullscreen_por_indice_real(carta_idx)
            return callback
        for i in range(2):
            lbl = tk.Label(self._carrossel_frame, bg="black", borderwidth=0, relief="flat")
            if i == 0:
                lbl.grid(row=0, column=1, padx=(0,3))
            else:
                lbl.grid(row=0, column=2, padx=(3,0))
            lbl.bind("<Button-1>", make_card_callback(i))
            self._carta_lbls.append(lbl)
        self._carrossel_frame.grid_columnconfigure(0, weight=1)
        self._carrossel_frame.grid_columnconfigure(3, weight=1)

        # Info e botões por baixo (estilo Store)
        frame_width = 100
        frame_height = 50
        self._info_frame = tk.Frame(self, bg="black")
        self._info_frame.pack(side="bottom", pady=0, fill="x")
        # Frames para cada elemento
        self.inventory_frame = tk.Frame(self._info_frame, width=frame_width, height=frame_height, bg="black")
        self.buy_frame = tk.Frame(self._info_frame, width=frame_width, height=frame_height, bg="black")
        self.picoin_frame = tk.Frame(self._info_frame, width=frame_width, height=frame_height, bg="black")
        self.voltar_frame = tk.Frame(self._info_frame, width=frame_width, height=frame_height, bg="black")
        self.inventory_frame.pack_propagate(False)
        self.buy_frame.pack_propagate(False)
        self.picoin_frame.pack_propagate(False)
        self.voltar_frame.pack_propagate(False)
        self.inventory_frame.pack(side="left", padx=(20,10), pady=0)
        self.buy_frame.pack(side="left", padx=10, pady=0)
        self.picoin_frame.pack(side="left", padx=10, pady=0, expand=True)
        self.voltar_frame.pack(side="left", padx=(10,40), pady=0)
        # Botão Inventory (onde estava o Buy)
        self._btn_inventory = tk.Button(self.inventory_frame, text="Inventory", font=("Helvetica", 14, "bold"), bg="#8A2BE2", fg="white", relief="flat", borderwidth=0, command=self._abrir_inventory)
        self._btn_inventory.place(relx=0.5, rely=0.5, anchor="center")
        # Botão Buy (alinhado com os outros botões)
        self._btn_buy = tk.Button(self.buy_frame, text="Buy", font=("Helvetica", 14, "bold"), bg="#4CAF50", fg="white", relief="flat", borderwidth=0, command=self._comprar_carta)
        self._btn_buy.place(relx=0.5, rely=0.5, anchor="center")  # Alinhado com Inventory e Back

        self._carrossel_update()

        # Barra inferior com imagem BelowBar_store.png
        belowbar_img = ImageTk.PhotoImage(Image.open(BELOWBAR_IMG).resize((self.winfo_screenwidth(), 50)))
        belowbar_label = tk.Label(self, image=belowbar_img, bg="black")
        belowbar_label.image = belowbar_img  # type: ignore[attr-defined]
        belowbar_label.pack(side="bottom", fill="x")

        # Mover saldo e piccoin para parte inferior direita (por cima do BelowBar)
        coin_img_bottom = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24, 24)))
        coin_lbl_bottom = tk.Label(self, image=coin_img_bottom, bg="#DC8392")
        coin_lbl_bottom.image = coin_img_bottom  # type: ignore[attr-defined]
        coin_lbl_bottom.place(x=self.winfo_screenwidth()-100, rely=1.0, y=-25, anchor="w")
        
        saldo_lbl_bottom = tk.Label(self, text=f"{self.saldo}", font=("Helvetica", 16, "bold"), fg="black", bg="#DC8392")
        saldo_lbl_bottom.place(x=self.winfo_screenwidth()-70, rely=1.0, y=-25, anchor="w")

        # Botão Back no canto inferior direito (depois da barra para ficar visível)
        self._btn_voltar = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), bg="#005c75", fg="white", relief="flat", borderwidth=0, command=self.voltar_para_store)
        self._btn_voltar.place(relx=0.98, rely=0.92, anchor="se")  # Movido para cima da barra inferior

    def _abrir_inventory(self):
        """Abre a página de inventário do tipo correspondente usando a função sincronizada"""
        tipo_atual = getattr(self, "current_card_type", None)
        if tipo_atual:
            print(f"DEBUG: Abrindo inventário sincronizado para compra - tipo: {tipo_atual}")
            # Usar a nova função sincronizada que volta para a página de compra
            self.show_inventory_matrix_buy([tipo_atual], 0, tipo_atual)
        else:
            print("DEBUG: Tipo de carta atual não definido")

    def _carrossel_prev(self):
        if not self._fullscreen_open:
            self._buy_idx = (self._buy_idx - 1) % len(self._buy_paths)
            self._carrossel_update()

    def _carrossel_next(self):
        if not self._fullscreen_open:
            self._buy_idx = (self._buy_idx + 1) % len(self._buy_paths)
            self._carrossel_update()

    def _carrossel_update(self):
        # Mostra duas cartas lado a lado, só uma destacada
        n = len(self._buy_paths)
        idxs = [self._buy_idx, (self._buy_idx+1)%n] if n > 1 else [self._buy_idx, self._buy_idx]
        for i, lbl in enumerate(self._carta_lbls):
            carta_path = self._buy_paths[idxs[i]]
            try:
                img = ImageTk.PhotoImage(Image.open(carta_path).resize((120, 180)))
            except Exception:
                img = None
            if img is not None:
                lbl.config(image=img)
                if not hasattr(self, '_carta_imgs'):
                    self._carta_imgs = []
                if len(self._carta_imgs) <= i:
                    self._carta_imgs.append(img)
                else:
                    self._carta_imgs[i] = img
            else:
                lbl.config(image="")
                if hasattr(self, '_carta_imgs'):
                    self._carta_imgs[i] = None
            # Destaca só a carta selecionada
            if i == 0:
                lbl.config(highlightbackground="yellow", highlightcolor="yellow", highlightthickness=4)
            else:
                lbl.config(highlightbackground="black", highlightcolor="black", highlightthickness=0)
        # Atualiza valor da carta destacada
        valor = self._extrair_valor_carta(self._buy_paths[self._buy_idx])
        self._valor_lbl.config(text=str(valor) if valor is not None else "?")

    def _abrir_fullscreen_por_indice_real(self, carta_idx):
        print(f"DEBUG: _abrir_fullscreen_por_indice_real chamado com carta_idx={carta_idx}")
        self._fullscreen_open = True
        carta_path = self._buy_paths[carta_idx]
        print(f"DEBUG: Caminho da carta a abrir em fullscreen: {carta_path}")
        # Esconde todos os widgets atuais
        self._fullscreen_hidden_widgets = []
        for widget in self.winfo_children():
            if widget.winfo_ismapped():
                self._fullscreen_hidden_widgets.append(widget)
                widget.place_forget() if hasattr(widget, 'place_info') and widget.place_info() else widget.pack_forget()
        self.configure(bg="black")
        try:
            pil_img = Image.open(carta_path)
            img_w, img_h = pil_img.size
            max_w, max_h = self.winfo_screenwidth(), self.winfo_screenheight()
            ratio = min(max_w/img_w, max_h/img_h)
            new_w, new_h = int(img_w*ratio), int(img_h*ratio)
            pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            carta_img = ImageTk.PhotoImage(pil_img)
            print("DEBUG: Imagem carregada e redimensionada com sucesso.")
        except Exception as e:
            print(f"ERRO ao carregar imagem em fullscreen: {e}")
            return
        carta_real_lbl = tk.Label(self, image=carta_img, bg="black")
        if not hasattr(self, '_img_refs'):
            self._img_refs = []
        self._img_refs.append(carta_img)
        carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center")
        # Botão circular cinza (✖) no canto superior direito
        def fechar():
            carta_real_lbl.destroy()
            btn_x.destroy()
            self._fullscreen_open = False
            self._buy_idx = carta_idx
            # Limpa todos os widgets antes de voltar à página de compra
            for widget in self.winfo_children():
                widget.destroy()
            self.show_buy_page()
        btn_x = tk.Button(self, text="✖", font=("Helvetica", 24, "bold"), bg="#AAAAAA", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=fechar, cursor="hand2", activebackground="#CCCCCC")
        btn_x.place(relx=0.98, rely=0, anchor="ne")

    def _extrair_valor_carta(self, carta_path):
        import re
        # Extrai valor do nome do ficheiro: ..._100.png → 100
        nome = os.path.basename(carta_path)
        match = re.search(r'_(\d+)\.', nome)
        if match:
            return int(match.group(1))
        return None

    def _comprar_carta(self):
        # Se houver carta destacada, mostra página de confirmação
        carta_path = self._buy_paths[self._buy_idx]
        valor = self._extrair_valor_carta(carta_path)
        # Esconde todos os widgets exceto barra superior
        for widget in self.winfo_children():
            if isinstance(widget, tk.Label) and hasattr(widget, 'image') and widget.winfo_y() == 0:
                continue  # Mantém a barra superior
            widget.destroy()
        self.configure(bg="black")
        # Frase de confirmação
        # Picoin + saldo na parte superior direita
        coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24, 24)))
        coin_lbl = tk.Label(self, image=coin_img, bg="#DC8392")
        coin_lbl.image = coin_img  # type: ignore[attr-defined]
        coin_lbl.place(x=self.winfo_screenwidth()-100, y=12)
        
        # Usar o saldo do Player em vez do saldo da Store também na barra superior
        player_saldo = self.dashboard.saldo if self.dashboard else self.saldo
        saldo_lbl = tk.Label(self, text=f"{player_saldo}", font=("Helvetica", 16, "bold"), fg="black", bg="#DC8392")
        saldo_lbl.place(x=self.winfo_screenwidth()-70, y=12)
        confirm_frame = tk.Frame(self, bg="black")
        confirm_frame.pack(expand=True)
        tk.Label(confirm_frame, text="Are you sure you want to buy?", font=("Helvetica", 16, "bold"), fg="white", bg="black").pack(pady=(40, 20))
        
        # Usar o saldo do Player em vez do saldo da Store
        player_saldo = self.dashboard.saldo if self.dashboard else self.saldo
        tk.Label(confirm_frame, text=f"Your balance: {player_saldo}", font=("Helvetica", 16), fg="yellow", bg="black").pack(pady=(0, 10))
        
        # Valor da carta
        value_frame = tk.Frame(confirm_frame, bg="black")
        value_frame.pack(pady=(0, 30))
        
        value_text_lbl = tk.Label(value_frame, text="Card value: ", 
                                 font=("Helvetica", 16), fg="white", bg="black")
        value_text_lbl.pack(side="left")
        
        value_amount_lbl = tk.Label(value_frame, text=str(valor) if valor is not None else "?", 
                                   font=("Helvetica", 16, "bold"), fg="yellow", bg="black")
        value_amount_lbl.pack(side="left", padx=(5, 5))
        
        # Ícone da moeda
        try:
            picoin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24,24)))
            picoin_lbl = tk.Label(value_frame, image=picoin_img, bg="black")
            picoin_lbl.image = picoin_img  # type: ignore[attr-defined]
            picoin_lbl.pack(side="left")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar ícone da moeda: {e}")
        
        btns_frame = tk.Frame(confirm_frame, bg="black")
        btns_frame.pack()
        def confirmar():
            # Executa a compra
            if valor is not None and self.dashboard and self.dashboard.saldo >= valor:
                print(f"DEBUG: Antes da compra - Store: {self.saldo}, Player: {self.dashboard.saldo}, Valor: {valor}")
                # IMPORTANTE: O Player paga pela carta e a Store recebe o pagamento
                # O saldo do Player DIMINUI (paga pela carta)
                self.dashboard.saldo -= valor
                # A Store recebe o pagamento
                self.saldo += valor
                print(f"DEBUG: Depois da compra - Store: {self.saldo}, Player: {self.dashboard.saldo}")
                # Garantir tipo correto para inventário
                tipo_inv = self.current_card_type
                if tipo_inv == "equipment":
                    tipo_inv = "equipments"
                elif tipo_inv == "actions":
                    tipo_inv = "action"  # PlayerDashboard usa "action" (singular)
                elif tipo_inv == "activity":
                    tipo_inv = "activities"  # PlayerDashboard usa "activities" (plural)
                print(f"DEBUG: Purchase - mapping card type '{self.current_card_type}' to inventory key '{tipo_inv}'")
                if self.dashboard and hasattr(self.dashboard, 'adicionar_carta_inventario'):
                    self.dashboard.adicionar_carta_inventario(carta_path, tipo_inv)
                print(f"DEBUG: Carta guardada no inventario do PlayerDashboard: {tipo_inv} -> {carta_path}")
                # ALTERAÇÃO: Voltar à página de compra em vez da dashboard
                self.show_buy_page()
                print("DEBUG: Voltando à página de compra após confirmação")
                # NÃO destruir a StoreWindow aqui!
                # self.destroy()
            else:
                from tkinter import messagebox
                messagebox.showwarning("Saldo insuficiente", "Não tens saldo suficiente para comprar esta carta!")
                self.show_buy_page()
        def cancelar():
            self.show_buy_page()
        btn_yes = tk.Button(btns_frame, text="Yes", font=("Helvetica", 14, "bold"), bg="#4CAF50", fg="white", width=8, command=confirmar)
        btn_no = tk.Button(btns_frame, text="No", font=("Helvetica", 14, "bold"), bg="#F44336", fg="white", width=8, command=cancelar)
        btn_yes.pack(side="left", padx=20, pady=10)
        btn_no.pack(side="left", padx=20, pady=10)

    def voltar_para_store(self):
        print("DEBUG: voltar_para_store chamado")
        try:
            # Se a janela já foi destruída, não faz nada
            if not self.winfo_exists():
                print("DEBUG: StoreWindow já foi destruída, não é possível reconstruir.")
                return
            # Reset do current_card_type (usado para Buy/Sell), mas MANTÉM casa_tipo e casa_cor originais
            self.current_card_type = None
            # Reset de outros estados que possam interferir
            if hasattr(self, '_fullscreen_open'):
                self._fullscreen_open = False
            if hasattr(self, '_buy_idx'):
                self._buy_idx = 0
            # Garante que a janela está no estado correto
            self.deiconify()
            self.configure(bg="black")
            self.state('normal')  # Garante que não está minimizada
            # Limpa todos os widgets da janela
            for widget in self.winfo_children():
                widget.destroy()
            # Force update para garantir que a limpeza foi feita
            self.update_idletasks()
            print("DEBUG: Estado limpo, reconstruindo interface...")
            print(f"DEBUG: Mantendo estado original - casa_tipo: {self.casa_tipo}, casa_cor: {self.casa_cor}")
            # Reconstrói a interface da Store
            self.rebuild_store_interface()
            # Force final update e foco
            self.update()
            self.lift()
            self.focus_force()
            print("DEBUG: voltar_para_store terminado com sucesso")
        except Exception as e:
            print(f"DEBUG: ERRO em voltar_para_store: {e}")
            import traceback
            traceback.print_exc()
            # Tenta uma reconstrução simples em caso de erro
            try:
                if self.winfo_exists():
                    self.deiconify()
                    self.rebuild_store_interface()
            except:
                pass

    def sell_action(self):
        """Ação do botão Sell: mostra o inventário do tipo correspondente para seleção de carta a vender (sempre usa Store local)."""
        current_type = getattr(self, 'current_card_type', None)
        if current_type:
            type_mapping = {
                "equipment": "equipments",
                "equipments": "equipments", 
                "users": "users",
                "services": "services",
                "activities": "activities"
            }
            inventory_key = type_mapping.get(current_type, current_type)
            print(f"DEBUG: sell_action - current_type: {current_type}, inventory_key: {inventory_key}")
        else:
            inventory_key = current_type
        
        # Usa SEMPRE o método local da Store
        print("DEBUG: Usando método local show_sell_inventory")
        self.show_sell_inventory(inventory_key)

    def show_sell_inventory(self, carta_tipo):
        """Mostra o inventário do tipo selecionado para venda usando o mesmo layout do PlayerDashboard"""
        print(f"DEBUG: show_sell_inventory chamado com carta_tipo={carta_tipo}")
        
        # Guardar estado atual da venda
        self.current_sell_type = carta_tipo
        self.current_sell_page = 0
        
        # Limpa todos os widgets da janela Store
        for widget in self.winfo_children():
            widget.destroy()
        self.configure(bg="black")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Barra superior com imagem TopBar da cor do jogador
        try:
            topbar_img_path = os.path.join(IMG_DIR, f"TopBar_{self.player_color}.png")
            topbar_img = ImageTk.PhotoImage(Image.open(topbar_img_path).resize((screen_width, 60)))
            topbar_label = tk.Label(self, image=topbar_img, bg="black", borderwidth=0, highlightthickness=0)
            topbar_label.image = topbar_img  # type: ignore[attr-defined]
            topbar_label.pack(side="top", fill="x")
            
            # Nome do jogador centralizado sobre a imagem
            name_lbl = tk.Label(self, text=self.player_name, 
                               font=("Helvetica", 18, "bold"), bg=self.player_color_hex, fg="black")
            name_lbl.place(relx=0.5, y=25, anchor="n")
            
            # Saldo e piccoin na barra superior, à direita
            coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24, 24)))
            coin_lbl = tk.Label(self, image=coin_img, bg=self.player_color_hex)
            coin_lbl.image = coin_img  # type: ignore[attr-defined]
            coin_lbl.place(x=screen_width-100, y=30)
            
            # Usar o saldo do jogador em vez do saldo da Store
            saldo_jogador = self.dashboard.saldo if self.dashboard else self.saldo
            saldo_lbl = tk.Label(self, text=f"{saldo_jogador}", 
                               font=("Helvetica", 16, "bold"), fg="black", bg=self.player_color_hex)
            saldo_lbl.place(x=screen_width-70, y=30)
            
        except Exception as e:
            print(f"DEBUG: Erro ao carregar TopBar, usando header simples: {e}")
            # Fallback para header simples se não conseguir carregar a imagem
            header_frame = tk.Frame(self, bg=self.player_color_hex, height=60)
            header_frame.pack(fill="x", pady=0)
            header_frame.pack_propagate(False)
            
            name_lbl = tk.Label(header_frame, text=self.player_name, 
                               font=("Helvetica", 18, "bold"), bg=self.player_color_hex, fg="black")
            name_lbl.place(relx=0.5, rely=0.5, anchor="center")
            
            coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24, 24)))
            coin_lbl = tk.Label(header_frame, image=coin_img, bg=self.player_color_hex)
            coin_lbl.image = coin_img  # type: ignore[attr-defined]
            coin_lbl.place(x=screen_width-100, rely=0.5, anchor="w")
            
            # Usar o saldo do jogador em vez do saldo da Store
            saldo_jogador = self.dashboard.saldo if self.dashboard else self.saldo
            saldo_lbl = tk.Label(header_frame, text=f"{saldo_jogador}", 
                               font=("Helvetica", 16, "bold"), bg=self.player_color_hex, fg="black")
            saldo_lbl.place(x=screen_width-70, rely=0.5, anchor="w")
        
        # Título - igual ao PlayerDashboard
        titulo = carta_tipo.capitalize() if carta_tipo else "Inventory"
        title = tk.Label(self, text=f"Sell {titulo}", font=("Helvetica", 22, "bold"), fg="white", bg="black")
        title.place(relx=0.5, y=65, anchor="n")  # Mesma posição do PlayerDashboard
        
        # Obter cartas do inventário
        # IMPORTANTE: Garantir que usamos o inventário mais recente do PlayerDashboard
        if hasattr(self, 'dashboard') and self.dashboard and hasattr(self.dashboard, 'inventario'):
            self.inventario = self.dashboard.inventario
            print(f"DEBUG: Inventário da Store sincronizado com o PlayerDashboard no show_sell_inventory")
        
        cartas = []
        if self.inventario and carta_tipo in self.inventario:
            todas_cartas = self.inventario[carta_tipo]
            
            # Se for Activities, filtrar cartas que não estão ativas no carrossel
            if carta_tipo == "activities":
                cartas_ativas = []
                if hasattr(self, 'dashboard') and self.dashboard and hasattr(self.dashboard, 'cards'):
                    cartas_ativas = [carta for carta in self.dashboard.cards if carta in todas_cartas]
                    print(f"DEBUG: Cartas ativas no carrossel: {len(cartas_ativas)}")
                    for carta in cartas_ativas:
                        print(f"DEBUG: Carta ativa: {carta}")
                
                # Filtrar apenas cartas que não estão ativas
                cartas = [carta for carta in todas_cartas if carta not in cartas_ativas]
                print(f"DEBUG: Cartas Activities disponíveis para venda: {len(cartas)} de {len(todas_cartas)} totais")
            else:
                # Para outros tipos, mostrar todas as cartas
                cartas = todas_cartas
                
            print(f"DEBUG: Encontradas {len(cartas)} cartas do tipo {carta_tipo}")
        else:
            print(f"DEBUG: Nenhuma carta encontrada para tipo {carta_tipo}")
            print(f"DEBUG: Inventário disponível: {list(self.inventario.keys()) if self.inventario else 'None'}")
        
        if cartas:
            # Paginação igual ao PlayerDashboard
            cards_per_page = 4
            total_pages = max(1, (len(cartas) + cards_per_page - 1) // cards_per_page)
            page = 0  # Sempre começar na primeira página
            start_idx = page * cards_per_page
            end_idx = start_idx + cards_per_page
            cartas_page = cartas[start_idx:end_idx]
            
            # Matriz de cartas igual ao PlayerDashboard
            matriz_frame = tk.Frame(self, bg="black")
            matriz_frame.place(relx=0.5, rely=0.5, anchor="center")  # Centralizada igual ao PlayerDashboard
            
            n_col = 2  # 2 colunas igual ao PlayerDashboard
            card_w, card_h = 85, 120  # Tamanho igual ao PlayerDashboard
            self._sell_imgs = []
            
            def make_fullscreen_callback(carta_path):
                def callback(event=None):
                    print(f"DEBUG: Carta clicada para venda: {carta_path}")
                    self.iniciar_venda_carta(carta_path, carta_tipo, self.dashboard)
                return callback
            
            for idx, carta_path in enumerate(cartas_page):
                row = idx // n_col
                col = idx % n_col
                try:
                    img = ImageTk.PhotoImage(Image.open(carta_path).resize((card_w, card_h)))
                    self._sell_imgs.append(img)
                    
                    carta_lbl = tk.Label(matriz_frame, image=img, bg="black", cursor="hand2")
                    carta_lbl.image = img  # type: ignore[attr-defined]
                    carta_lbl.grid(row=row, column=col, padx=8, pady=8)  # Padding igual ao PlayerDashboard
                    carta_lbl.bind("<Button-1>", make_fullscreen_callback(carta_path))
                    
                    print(f"DEBUG: Carta adicionada à grid: {os.path.basename(carta_path)}")
                except Exception as e:
                    print(f"DEBUG: Erro ao carregar carta {carta_path}: {e}")
                    continue
            
            # Setas de navegação iguais ao PlayerDashboard
            if total_pages > 1:
                seta_x = 0.90  # Posição igual ao PlayerDashboard
                if page > 0:
                    seta_cima = tk.Button(self, text="▲", font=("Helvetica", 18, "bold"), bg="#222", fg="white", width=2, 
                                         command=lambda: self.show_sell_inventory_paginated(carta_tipo, page-1))
                    seta_cima.place(relx=seta_x, rely=0.38, anchor="center")  # Posição igual ao PlayerDashboard
                if page < total_pages - 1:
                    seta_baixo = tk.Button(self, text="▼", font=("Helvetica", 18, "bold"), bg="#222", fg="white", width=2, 
                                          command=lambda: self.show_sell_inventory_paginated(carta_tipo, page+1))
                    seta_baixo.place(relx=seta_x, rely=0.62, anchor="center")  # Posição igual ao PlayerDashboard
        else:
            # Mensagem se não houver cartas
            no_cards_lbl = tk.Label(self, text="No cards available to sell!", 
                                   font=("Helvetica", 16), bg="black", fg="white")
            no_cards_lbl.place(relx=0.5, rely=0.5, anchor="center")
        
        # Botão Back igual ao PlayerDashboard
        btn_voltar = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), 
                              bg="#005c75", fg="white", width=10, 
                              command=self.voltar_para_store)
        btn_voltar.place(relx=0.5, rely=0.98, anchor="s")  # Posição igual ao PlayerDashboard
        
        print("DEBUG: show_sell_inventory concluído")

    def show_sell_inventory_paginated(self, carta_tipo, page=0):
        """Versão paginada do show_sell_inventory usando o mesmo layout do PlayerDashboard"""
        print(f"DEBUG: show_sell_inventory_paginated chamado com carta_tipo={carta_tipo}, page={page}")
        
        # Guardar estado atual da venda
        self.current_sell_type = carta_tipo
        self.current_sell_page = page
        
        # Limpa todos os widgets da janela Store
        for widget in self.winfo_children():
            widget.destroy()
        self.configure(bg="black")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Barra superior com imagem TopBar da cor do jogador
        try:
            topbar_img_path = os.path.join(IMG_DIR, f"TopBar_{self.player_color}.png")
            topbar_img = ImageTk.PhotoImage(Image.open(topbar_img_path).resize((screen_width, 60)))
            topbar_label = tk.Label(self, image=topbar_img, bg="black", borderwidth=0, highlightthickness=0)
            topbar_label.image = topbar_img  # type: ignore[attr-defined]
            topbar_label.pack(side="top", fill="x")
            
            # Nome do jogador centralizado sobre a imagem
            name_lbl = tk.Label(self, text=self.player_name, 
                               font=("Helvetica", 18, "bold"), bg=self.player_color_hex, fg="black")
            name_lbl.place(relx=0.5, y=25, anchor="n")
            
            # Saldo e piccoin na barra superior, à direita
            coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24, 24)))
            coin_lbl = tk.Label(self, image=coin_img, bg=self.player_color_hex)
            coin_lbl.image = coin_img  # type: ignore[attr-defined]
            coin_lbl.place(x=screen_width-100, y=30)
            
            # Usar o saldo do jogador em vez do saldo da Store
            saldo_jogador = self.dashboard.saldo if self.dashboard else self.saldo
            saldo_lbl = tk.Label(self, text=f"{saldo_jogador}", 
                               font=("Helvetica", 16, "bold"), fg="black", bg=self.player_color_hex)
            saldo_lbl.place(x=screen_width-70, y=30)
            
        except Exception as e:
            print(f"DEBUG: Erro ao carregar TopBar, usando header simples: {e}")
            # Fallback para header simples se não conseguir carregar a imagem
            header_frame = tk.Frame(self, bg=self.player_color_hex, height=60)
            header_frame.pack(fill="x", pady=0)
            header_frame.pack_propagate(False)
            
            name_lbl = tk.Label(header_frame, text=self.player_name, 
                               font=("Helvetica", 18, "bold"), bg=self.player_color_hex, fg="black")
            name_lbl.place(relx=0.5, rely=0.5, anchor="center")
            
            coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24, 24)))
            coin_lbl = tk.Label(header_frame, image=coin_img, bg=self.player_color_hex)
            coin_lbl.image = coin_img  # type: ignore[attr-defined]
            coin_lbl.place(x=screen_width-100, rely=0.5, anchor="w")
            
            # Usar o saldo do jogador em vez do saldo da Store
            saldo_jogador = self.dashboard.saldo if self.dashboard else self.saldo
            saldo_lbl = tk.Label(header_frame, text=f"{saldo_jogador}", 
                               font=("Helvetica", 16, "bold"), bg=self.player_color_hex, fg="black")
            saldo_lbl.place(x=screen_width-70, rely=0.5, anchor="w")
        
        # Título - igual ao PlayerDashboard
        titulo = carta_tipo.capitalize() if carta_tipo else "Inventory"
        title = tk.Label(self, text=f"Sell {titulo}", font=("Helvetica", 22, "bold"), fg="white", bg="black")
        title.place(relx=0.5, y=65, anchor="n")  # Mesma posição do PlayerDashboard
        
        # Obter cartas do inventário
        # IMPORTANTE: Garantir que usamos o inventário mais recente do PlayerDashboard
        if hasattr(self, 'dashboard') and self.dashboard and hasattr(self.dashboard, 'inventario'):
            self.inventario = self.dashboard.inventario
            print(f"DEBUG: Inventário da Store sincronizado com o PlayerDashboard no show_sell_inventory_paginated")
        
        cartas = []
        if self.inventario and carta_tipo in self.inventario:
            todas_cartas = self.inventario[carta_tipo]
            
            # Se for Activities, filtrar cartas que não estão ativas no carrossel
            if carta_tipo == "activities":
                cartas_ativas = []
                if hasattr(self, 'dashboard') and self.dashboard and hasattr(self.dashboard, 'cards'):
                    cartas_ativas = [carta for carta in self.dashboard.cards if carta in todas_cartas]
                    print(f"DEBUG: Cartas ativas no carrossel: {len(cartas_ativas)}")
                    for carta in cartas_ativas:
                        print(f"DEBUG: Carta ativa: {carta}")
                
                # Filtrar apenas cartas que não estão ativas
                cartas = [carta for carta in todas_cartas if carta not in cartas_ativas]
                print(f"DEBUG: Cartas Activities disponíveis para venda: {len(cartas)} de {len(todas_cartas)} totais")
            else:
                # Para outros tipos, mostrar todas as cartas
                cartas = todas_cartas
                
            print(f"DEBUG: Encontradas {len(cartas)} cartas do tipo {carta_tipo}")
        else:
            print(f"DEBUG: Nenhuma carta encontrada para tipo {carta_tipo}")
            print(f"DEBUG: Inventário disponível: {list(self.inventario.keys()) if self.inventario else 'None'}")
        
        if cartas:
            # Paginação igual ao PlayerDashboard
            cards_per_page = 4
            total_pages = max(1, (len(cartas) + cards_per_page - 1) // cards_per_page)
            page = max(0, min(page, total_pages - 1))
            start_idx = page * cards_per_page
            end_idx = start_idx + cards_per_page
            cartas_page = cartas[start_idx:end_idx]
            
            # Matriz de cartas igual ao PlayerDashboard
            matriz_frame = tk.Frame(self, bg="black")
            matriz_frame.place(relx=0.5, rely=0.5, anchor="center")  # Centralizada igual ao PlayerDashboard
            
            n_col = 2  # 2 colunas igual ao PlayerDashboard
            card_w, card_h = 85, 120  # Tamanho igual ao PlayerDashboard
            self._sell_imgs = []
            
            def make_fullscreen_callback(carta_path):
                def callback(event=None):
                    print(f"DEBUG: Carta clicada para venda: {carta_path}")
                    self.iniciar_venda_carta(carta_path, carta_tipo, self.dashboard)
                return callback
            
            for idx, carta_path in enumerate(cartas_page):
                row = idx // n_col
                col = idx % n_col
                try:
                    img = ImageTk.PhotoImage(Image.open(carta_path).resize((card_w, card_h)))
                    self._sell_imgs.append(img)
                    
                    carta_lbl = tk.Label(matriz_frame, image=img, bg="black", cursor="hand2")
                    carta_lbl.image = img  # type: ignore[attr-defined]
                    carta_lbl.grid(row=row, column=col, padx=8, pady=8)  # Padding igual ao PlayerDashboard
                    carta_lbl.bind("<Button-1>", make_fullscreen_callback(carta_path))
                    
                    print(f"DEBUG: Carta adicionada à grid: {os.path.basename(carta_path)}")
                except Exception as e:
                    print(f"DEBUG: Erro ao carregar carta {carta_path}: {e}")
                    continue
            
            # Setas de navegação iguais ao PlayerDashboard
            if total_pages > 1:
                seta_x = 0.90  # Posição igual ao PlayerDashboard
                if page > 0:
                    seta_cima = tk.Button(self, text="▲", font=("Helvetica", 18, "bold"), bg="#222", fg="white", width=2, 
                                         command=lambda: self.show_sell_inventory_paginated(carta_tipo, page-1))
                    seta_cima.place(relx=seta_x, rely=0.38, anchor="center")  # Posição igual ao PlayerDashboard
                if page < total_pages - 1:
                    seta_baixo = tk.Button(self, text="▼", font=("Helvetica", 18, "bold"), bg="#222", fg="white", width=2, 
                                          command=lambda: self.show_sell_inventory_paginated(carta_tipo, page+1))
                    seta_baixo.place(relx=seta_x, rely=0.62, anchor="center")  # Posição igual ao PlayerDashboard
        else:
            # Mensagem se não houver cartas
            no_cards_lbl = tk.Label(self, text="No cards available to sell!", 
                                   font=("Helvetica", 16), bg="black", fg="white")
            no_cards_lbl.place(relx=0.5, rely=0.5, anchor="center")
        
        # Botão Back igual ao PlayerDashboard
        btn_voltar = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), 
                              bg="#005c75", fg="white", width=10, 
                              command=self.voltar_para_store)
        btn_voltar.place(relx=0.5, rely=0.98, anchor="s")  # Posição igual ao PlayerDashboard
        
        print("DEBUG: show_sell_inventory_paginated concluído")

    def skip_action(self):
        """Ação do botão Skip - sai da loja"""
        
        print("DEBUG: skip_action chamado") # Esconde os botões de ação
        
        try:
            self.hide_action_buttons()
        except AttributeError:
            pass
        
        # Fecha a Store
        self.destroy()
        
        # Se houver um dashboard, recria a interface principal e traz para a frente
        if self.dashboard:
            self.dashboard.playerdashboard_interface(
                self.dashboard.player_name,
                self.dashboard.saldo,  # Usar o saldo atualizado do PlayerDashboard (já foi decrementado)
                self.dashboard.other_players
            )
            try:
                self.dashboard.lift()
            except Exception:
                pass

    def tirar_carta(self, casa_tipo, casa_cor):
        print(f"DEBUG: tirar_carta chamado com casa_tipo={casa_tipo!r}, casa_cor={casa_cor!r}")
        
        # Normalizar o tipo para consistent naming
        if casa_tipo == "equipment":
            casa_tipo = "equipments"
        
        # Se for casa de outro jogador, sempre vai diretamente para a página de compra para Users, Equipment, Services, Activities
        if self.other_player_house and casa_tipo in ["equipments", "services", "users", "activities"]:
            # Armazenar o tipo de carta atual para verificar o inventário
            self.current_card_type = casa_tipo
            print(f"DEBUG: Casa outro jogador - definindo current_card_type = {casa_tipo}")
            self.show_buy_page()
            return
        
        # Se for casa de outro jogador mas não for tipo permitido, não faz nada
        if self.other_player_house:
            print(f"DEBUG: Casa de outro jogador - tipo {casa_tipo} não permitido")
            return
        
        # Comportamento normal para casas próprias ou neutras - vai diretamente para página de compra
        if casa_tipo in ["equipments", "services", "users", "activities"]:
            # Armazenar o tipo de carta atual para verificar o inventário
            self.current_card_type = casa_tipo
            print(f"DEBUG: Casa própria - definindo current_card_type = {casa_tipo}")
            self.show_buy_page()
        elif casa_tipo in ["actions", "action", "events", "challenges"]:
            # Para actions, events, challenges mostra a carta
            self.mostrar_carta(casa_cor, casa_tipo)
        else:
            # Para outros tipos, não faz nada
            pass

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

        verso_path = os.path.join(IMG_DIR, "cartas", "back_card.png")
        if not os.path.exists(verso_path):
            verso_path = os.path.join(IMG_DIR, "verso.png")

        # Verificar se o arquivo existe antes de tentar carregar
        if os.path.exists(verso_path):
            try:
                img = ImageTk.PhotoImage(Image.open(verso_path).resize((220, 320)))
                carta_lbl = tk.Label(center_frame, image=img, bg="black")
                carta_lbl.image = img  # Manter referência para evitar garbage collection
                carta_lbl.pack(pady=(0, 12))
                print(f"DEBUG: Imagem da carta verso carregada: {verso_path}")
            except Exception as e:
                print(f"DEBUG: Erro ao carregar imagem da carta verso: {e}")
                # Criar um placeholder se não conseguir carregar a imagem
                carta_lbl = tk.Label(center_frame, text="🂠", font=("Helvetica", 60), fg="white", bg="black")
                carta_lbl.pack(pady=(0, 12))
        else:
            print(f"DEBUG: Arquivo de carta verso não encontrado: {verso_path}")
            # Criar um placeholder se o arquivo não existir
            carta_lbl = tk.Label(center_frame, text="🂠", font=("Helvetica", 60), fg="white", bg="black")
            carta_lbl.pack(pady=(0, 12))

        def revelar_carta():
            carta_lbl.destroy()
            go_btn.destroy()
            carta_path = None
            
            # Corrigir a lógica de tirar cartas
            if tipo == "actions":
                print(f"DEBUG: Tentar tirar carta do tipo 'actions'")
                carta_path = tirar_carta(casa_cor, "actions")
            elif tipo == "events":
                print(f"DEBUG: Tentar tirar carta do tipo 'events'")
                carta_path = tirar_carta(casa_cor, "events")
            elif tipo == "challenges":
                print(f"DEBUG: Tentar tirar carta do tipo 'challenges'")
                carta_path = tirar_carta(casa_cor, "challenges")
                if not carta_path:
                    # Tentar também 'challenge' no singular
                    carta_path = tirar_carta(casa_cor, "challenge")
            elif tipo == "activities":
                print(f"DEBUG: Tentar tirar carta do tipo 'activities'")
                carta_path = tirar_carta(casa_cor, "activities")
            else:
                print(f"DEBUG: Tentar tirar carta do tipo '{tipo}'")
                carta_path = tirar_carta(casa_cor, tipo)
                
            print(f"DEBUG: carta_path={carta_path}")
            
            if carta_path and os.path.exists(carta_path):
                print(f"DEBUG: Carta encontrada e existe: {carta_path}")
                # --- LÓGICA DE ATRIBUIÇÃO/ESCOLHA ---
                if (tipo in ["actions", "events"] and casa_cor == "neutral"):
                    # Apenas mostrar fullscreen, adicionar ao inventário só no fechar do fullscreen
                    self.mostrar_carta_fullscreen(carta_path, tipo)
                elif (tipo == "challenges" and casa_cor == "neutral") or (tipo == "activities" and casa_cor == self.player_color):
                    # Perguntar ao jogador se quer ficar com a carta
                    self.mostrar_carta_fullscreen_escolha(carta_path, tipo)
                else:
                    self.mostrar_carta_fullscreen(carta_path, tipo)
            else:
                print(f"DEBUG: Nenhuma carta disponível para tipo={tipo}, casa_cor={casa_cor}")
                # Criar novo frame para a mensagem
                no_cards_frame = tk.Frame(self, bg="black")
                no_cards_frame.pack(expand=True)
                tk.Label(no_cards_frame, text="Sem cartas disponíveis!", font=("Helvetica", 14), bg="black", fg="white").pack(pady=10)
                # Botão para voltar
                tk.Button(no_cards_frame, text="Back", font=("Helvetica", 14, "bold"), bg="#005c75", fg="white", command=self.voltar_para_store).pack(pady=10)

        go_btn = tk.Button(center_frame, text="Go!", font=("Helvetica", 16, "bold"), bg="#005c75", fg="white", command=revelar_carta)
        go_btn.pack(pady=(5, 0))

    def mostrar_carta_fullscreen(self, carta_path, casa_tipo):
        print(f"DEBUG: Store.mostrar_carta_fullscreen chamado com carta_path={carta_path}, casa_tipo={casa_tipo}")
        
        # Verificar se o arquivo existe
        if not os.path.exists(carta_path):
            print(f"DEBUG: ERRO - Arquivo de carta não existe: {carta_path}")
            # Voltar à Store se a carta não existir
            self.voltar_para_store()
            return
            
        # Limpa tudo da janela Store
        for widget in self.winfo_children():
            widget.destroy()
        self.configure(bg="black")

        try:
            pil_img = Image.open(carta_path)
            img_w, img_h = pil_img.size
            # Usa todo o ecrã (sem margem)
            max_w, max_h = self.winfo_screenwidth(), self.winfo_screenheight()
            ratio = min(max_w/img_w, max_h/img_h)
            new_w, new_h = int(img_w*ratio), int(img_h*ratio)
            pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            carta_img = ImageTk.PhotoImage(pil_img)
            carta_real_lbl = tk.Label(self, image=carta_img, bg="black")
            carta_real_lbl.image = carta_img  # Manter referência
            carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center")
            
            print("DEBUG: Carta mostrada em fullscreen com sucesso")
        except Exception as e:
            print(f"DEBUG: ERRO ao carregar carta em fullscreen: {e}")
            # Mostrar mensagem de erro e voltar
            error_frame = tk.Frame(self, bg="black")
            error_frame.pack(expand=True)
            tk.Label(error_frame, text="Erro ao carregar carta!", font=("Helvetica", 16), bg="black", fg="red").pack(pady=20)
            tk.Button(error_frame, text="Back", font=("Helvetica", 14, "bold"), bg="#005c75", fg="white", command=self.voltar_para_store).pack(pady=10)
            return

        # Botão circular cinza (✖) no canto superior direito
        def fechar():
            carta_real_lbl.destroy()
            btn_x.destroy()
            # Guarda a carta no inventário do dashboard, se aplicável
            tipo_inv = casa_tipo
            if tipo_inv == "equipment":
                tipo_inv = "equipments"
            elif tipo_inv == "actions":
                tipo_inv = "action"  # PlayerDashboard usa "action" (singular)
            print(f"DEBUG: Mapping card type '{casa_tipo}' to inventory key '{tipo_inv}'")
            if self.dashboard and hasattr(self.dashboard, 'adicionar_carta_inventario'):
                self.dashboard.adicionar_carta_inventario(carta_path, tipo_inv)
                print(f"DEBUG: Card added to inventory: {tipo_inv} -> {carta_path}")
            # NÃO destruir a StoreWindow aqui!
            # self.destroy()
            # Volta ao dashboard e mostra a interface principal SEM botão Store
            if self.dashboard and hasattr(self.dashboard, "playerdashboard_interface"):
                try:
                    # Esconder a Store primeiro
                    self.withdraw()
                    print("DEBUG: Store escondida ao aceitar carta do baralho")
                    
                    # Mostrar o PlayerDashboard
                    self.dashboard.deiconify()
                    self.dashboard.state('normal')
                    self.dashboard.lift()
                    self.dashboard.focus_force()
                    print("DEBUG: PlayerDashboard mostrado ao aceitar carta do baralho")
                    
                    # Chamar a interface principal do PlayerDashboard SEM botão Store
                    self.dashboard.playerdashboard_interface(
                        self.dashboard.player_name,
                        self.dashboard.saldo,
                        self.dashboard.other_players,
                        show_store_button=False
                    )
                    print("DEBUG: Interface principal do PlayerDashboard aberta SEM botão Store")
                except Exception as e:
                    print(f"DEBUG: Erro ao voltar ao PlayerDashboard após aceitar carta do baralho: {e}")
        btn_x = tk.Button(self, text="✖", font=("Helvetica", 24, "bold"), bg="#AAAAAA", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=fechar, cursor="hand2", activebackground="#CCCCCC")
        btn_x.place(relx=0.98, rely=0, anchor="ne")

        # Se for Challenge, adicionar botão Inventory centrado em cima
        if casa_tipo in ["challenges", "challenge"]:
            def abrir_playerdashboard():
                print("DEBUG: Abrindo interface principal do PlayerDashboard")
                # Vai para a interface principal do PlayerDashboard SEM botão Store
                if self.dashboard and hasattr(self.dashboard, "playerdashboard_interface"):
                    try:
                        # Esconder a Store primeiro
                        self.withdraw()
                        print("DEBUG: Store escondida ao abrir PlayerDashboard via botão Challenge")
                        
                        # Mostrar o PlayerDashboard
                        self.dashboard.deiconify()
                        self.dashboard.state('normal')
                        self.dashboard.lift()
                        self.dashboard.focus_force()
                        print("DEBUG: PlayerDashboard mostrado via botão Challenge")
                        
                        # Chamar a interface principal do PlayerDashboard SEM botão Store
                        self.dashboard.playerdashboard_interface(
                            self.dashboard.player_name,
                            self.dashboard.saldo,
                            self.dashboard.other_players,
                            show_store_button=False
                        )
                        print("DEBUG: Interface principal do PlayerDashboard aberta SEM botão Store via Challenge")
                    except Exception as e:
                        print(f"DEBUG: Erro ao abrir PlayerDashboard via botão Challenge: {e}")
            
            # Carregamento do ícone do jogador
            try:
                user_icon_path = os.path.join(IMG_DIR, f"{self.player_color}_user_icon.png")
                user_icon_img = ImageTk.PhotoImage(Image.open(user_icon_path).resize((48, 48)))
                btn_inventory = tk.Button(self, image=user_icon_img, bg="#8A2BE2", relief="flat", borderwidth=0, command=abrir_playerdashboard, cursor="hand2")
                btn_inventory.image = user_icon_img  # Manter referência para evitar garbage collection
            except Exception as e:
                print(f"DEBUG: Erro ao carregar ícone do jogador {self.player_color}_user_icon.png: {e}")
                # Fallback para texto se não conseguir carregar a imagem
                btn_inventory = tk.Button(self, text="Player", font=("Helvetica", 16, "bold"), bg="#8A2BE2", fg="white", relief="flat", borderwidth=0, command=abrir_playerdashboard)
            
            btn_inventory.place(relx=0.5, rely=0, anchor="n")

    def mostrar_carta_fullscreen_escolha(self, carta_path, carta_tipo):
        # Mostra a carta em fullscreen e pergunta se quer ficar com ela
        for widget in self.winfo_children():
            widget.destroy()
        self.configure(bg="black")
        pil_img = Image.open(carta_path)
        img_w, img_h = pil_img.size
        max_w, max_h = self.winfo_screenwidth(), self.winfo_screenheight()
        ratio = min(max_w/img_w, max_h/img_h)
        new_w, new_h = int(img_w*ratio), int(img_h*ratio)
        pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        carta_img = ImageTk.PhotoImage(pil_img)
        carta_real_lbl = tk.Label(self, image=carta_img, bg="black")
        carta_real_lbl.image = carta_img  # Manter referência para evitar garbage collection
        carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center")
        # Botão Inventory centrado no topo se for Challenge
        if carta_tipo in ["challenges", "challenge"]:
            def abrir_playerdashboard():
                print("DEBUG: Abrindo interface principal do PlayerDashboard")
                # Vai para a interface principal do PlayerDashboard
                if self.dashboard and hasattr(self.dashboard, "playerdashboard_interface"):
                    self.dashboard.playerdashboard_interface(
                        self.dashboard.player_name,
                        self.dashboard.saldo,
                        self.dashboard.other_players
                    )
            
            # Carregamento do ícone do jogador
            try:
                user_icon_path = os.path.join(IMG_DIR, f"{self.player_color}_user_icon.png")
                user_icon_img = ImageTk.PhotoImage(Image.open(user_icon_path).resize((48, 48)))
                btn_inventory = tk.Button(self, image=user_icon_img, bg="#8A2BE2", relief="flat", borderwidth=0, command=abrir_playerdashboard, cursor="hand2")
                btn_inventory.image = user_icon_img  # Manter referência para evitar garbage collection
            except Exception as e:
                print(f"DEBUG: Erro ao carregar ícone do jogador {self.player_color}_user_icon.png: {e}")
                # Fallback para texto se não conseguir carregar a imagem
                btn_inventory = tk.Button(self, text="Player", font=("Helvetica", 16, "bold"), bg="#8A2BE2", fg="white", relief="flat", borderwidth=0, command=abrir_playerdashboard)
            
            btn_inventory.place(relx=0.5, rely=0, anchor="n")
        # Botões Sim/Não
        def aceitar():
            tipo_inv = carta_tipo
            if tipo_inv == "equipment":
                tipo_inv = "equipments"
            elif tipo_inv == "actions":
                tipo_inv = "action"  # PlayerDashboard usa "action" (singular)
            print(f"DEBUG: Choice - mapping card type '{carta_tipo}' to inventory key '{tipo_inv}'")
            if self.dashboard:
                if hasattr(self.dashboard, 'inventario') and tipo_inv in self.dashboard.inventario:
                    self.dashboard.inventario[tipo_inv].append(carta_path)
                    print(f"DEBUG: Card added to inventory via choice: {tipo_inv} -> {carta_path}")
                # NÃO destruir a StoreWindow aqui!
                # self.destroy()
                if hasattr(self.dashboard, "playerdashboard_interface"):
                    try:
                        # Esconder a Store primeiro
                        self.withdraw()
                        print("DEBUG: Store escondida ao aceitar escolha")
                        
                        # Mostrar o PlayerDashboard
                        self.dashboard.deiconify()
                        self.dashboard.state('normal')
                        self.dashboard.lift()
                        self.dashboard.focus_force()
                        print("DEBUG: PlayerDashboard mostrado ao aceitar escolha")
                        
                        # Chamar a interface principal do PlayerDashboard SEM botão Store
                        self.dashboard.playerdashboard_interface(
                            self.dashboard.player_name,
                            self.dashboard.saldo,
                            self.dashboard.other_players,
                            show_store_button=False
                        )
                        print("DEBUG: Interface principal do PlayerDashboard aberta SEM botão Store")
                    except Exception as e:
                        print(f"DEBUG: Erro ao voltar ao PlayerDashboard após aceitar escolha: {e}")
        def recusar():
            # NÃO destruir a StoreWindow aqui!
            # self.destroy()
            if self.dashboard and hasattr(self.dashboard, "playerdashboard_interface"):
                try:
                    # Esconder a Store primeiro
                    self.withdraw()
                    print("DEBUG: Store escondida ao recusar escolha")
                    
                    # Mostrar o PlayerDashboard
                    self.dashboard.deiconify()
                    self.dashboard.state('normal')
                    self.dashboard.lift()
                    self.dashboard.focus_force()
                    print("DEBUG: PlayerDashboard mostrado ao recusar escolha")
                    
                    # Chamar a interface principal do PlayerDashboard SEM botão Store
                    self.dashboard.playerdashboard_interface(
                        self.dashboard.player_name,
                        self.dashboard.saldo,
                        self.dashboard.other_players,
                        show_store_button=False
                    )
                    print("DEBUG: Interface principal do PlayerDashboard aberta SEM botão Store")
                except Exception as e:
                    print(f"DEBUG: Erro ao voltar ao PlayerDashboard após recusar escolha: {e}")
        # Botão verde (✔) canto superior direito
        btn_certo = tk.Button(self, text="✔", font=("Helvetica", 24, "bold"), bg="#4CAF50", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=aceitar, cursor="hand2", activebackground="#43d17a")
        btn_certo.place(relx=0.98, rely=0, anchor="ne")
        # Botão vermelho (✖) canto superior esquerdo
        btn_x = tk.Button(self, text="✖", font=("Helvetica", 24, "bold"), bg="#F44336", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=recusar, cursor="hand2", activebackground="#e57373")
        btn_x.place(relx=0., rely=0, anchor="nw")

    def iniciar_venda_carta(self, carta_path, carta_tipo, player_dashboard):
        """Mostra a carta em fullscreen para venda, com botão piccoin e confirmação, tudo na StoreWindow."""
        print(f"DEBUG: iniciar_venda_carta chamado - carta_path: {carta_path}")
        
        # Verificar se o arquivo existe
        if not os.path.exists(carta_path):
            print(f"DEBUG: ERRO - Arquivo de carta não existe: {carta_path}")
            return
        
        # Garantir que a Store está visível e no estado correto
        self.deiconify()
        self.state('normal')
        self.lift()
        self.focus_force()
        
        # Limpa todos os widgets da Store
        for widget in self.winfo_children():
            widget.destroy()
        self.configure(bg="black")
        
        # Força update para garantir que a limpeza foi feita
        self.update_idletasks()
        
        # Mostra a carta em fullscreen ocupando toda a tela
        try:
            pil_img = Image.open(carta_path)
            img_w, img_h = pil_img.size
            
            # Área disponível: toda a tela
            available_width = self.winfo_screenwidth()
            available_height = self.winfo_screenheight()
            
            # Calcular o ratio para ocupar o máximo possível da tela
            ratio = min(available_width/img_w, available_height/img_h)
            new_w, new_h = int(img_w*ratio), int(img_h*ratio)
            pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            carta_img = ImageTk.PhotoImage(pil_img)
            
            # Centralizar a carta na tela
            carta_real_lbl = tk.Label(self, image=carta_img, bg="black", borderwidth=0, highlightthickness=0)
            carta_real_lbl.image = carta_img  # Manter referência para evitar garbage collection
            carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center")
            print("DEBUG: Carta carregada e mostrada em fullscreen com sucesso")
            
        except Exception as e:
            print(f"DEBUG: ERRO ao carregar carta para venda: {e}")
            # Mostrar um placeholder em caso de erro
            carta_real_lbl = tk.Label(self, text="Erro ao carregar carta", font=("Helvetica", 20), fg="red", bg="black")
            carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center")
        
        # Botão X para voltar ao inventário de venda (no canto superior direito)
        def fechar():
            print("DEBUG: Botão X pressionado - voltando ao inventário de venda")
            try:
                # Volta ao inventário de venda na Store
                self.show_sell_inventory(carta_tipo)
            except Exception as e:
                print(f"DEBUG: Erro ao fechar venda: {e}")
                # Em caso de erro, tenta voltar à Store
                self.voltar_para_store()
                
        x_btn = tk.Button(self, text="✖", font=("Helvetica", 24, "bold"), bg="#AAAAAA", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=fechar, cursor="hand2", activebackground="#CCCCCC")
        x_btn.place(relx=1, rely=0, anchor="ne")  # Volta ao canto superior direito
        
        # Botão piccoin para vender
        picoin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((48,48)))
        def abrir_confirm():
            self.confirmar_venda_carta(carta_path, carta_tipo, player_dashboard)
        btn_picoin = tk.Button(self, image=picoin_img, bg="#4CAF50", borderwidth=0, command=abrir_confirm, cursor="hand2")
        btn_picoin.image = picoin_img  # Manter referência para evitar garbage collection
        btn_picoin.place(relx=0, rely=1, anchor="sw")
        
        # Força update final
        self.update_idletasks()
        self.update()

    def confirmar_venda_carta(self, carta_path, carta_tipo, player_dashboard):
        """Mostra a página de confirmação de venda e trata a lógica de saldo e inventário."""
        print(f"DEBUG: confirmar_venda_carta chamado - carta_path: {carta_path}")
        
        # Limpa widgets
        for widget in self.winfo_children():
            widget.destroy()
        self.configure(bg="black")
        
        screen_width = self.winfo_screenwidth()
        
        # Barra superior com imagem TopBar da cor do jogador
        try:
            topbar_img_path = os.path.join(IMG_DIR, f"TopBar_{self.player_color}.png")
            topbar_img = ImageTk.PhotoImage(Image.open(topbar_img_path).resize((screen_width, 60)))
            header_label = tk.Label(self, image=topbar_img, bg="black", borderwidth=0, highlightthickness=0)
            header_label.image = topbar_img  # type: ignore[attr-defined]
            header_label.pack(side="top", fill="x")
            
            # Nome do jogador centralizado sobre a imagem
            name_lbl = tk.Label(self, text=player_dashboard.player_name, 
                               font=("Helvetica", 18, "bold"), bg=self.player_color_hex, fg="black")
            name_lbl.place(relx=0.5, y=25, anchor="n")
            
            # Saldo e moeda no canto direito sobre a imagem
            coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24,24)))
            coin_lbl = tk.Label(self, image=coin_img, bg=self.player_color_hex)
            coin_lbl.image = coin_img  # type: ignore[attr-defined]
            coin_lbl.place(x=screen_width-100, y=30)
            
            saldo_lbl = tk.Label(self, text=f"{player_dashboard.saldo}", 
                               font=("Helvetica", 16, "bold"), bg=self.player_color_hex, fg="black")
            saldo_lbl.place(x=screen_width-70, y=30)
            
        except Exception as e:
            print(f"DEBUG: Erro ao carregar TopBar, usando header simples: {e}")
            # Fallback para header simples se não conseguir carregar a imagem
            header_frame = tk.Frame(self, bg=self.player_color_hex, height=60)
            header_frame.pack(fill="x", pady=0)
            header_frame.pack_propagate(False)
            
            name_lbl = tk.Label(header_frame, text=player_dashboard.player_name, 
                               font=("Helvetica", 18, "bold"), bg=self.player_color_hex, fg="black")
            name_lbl.place(relx=0.5, rely=0.5, anchor="center")
            
            coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24,24)))
            coin_lbl = tk.Label(header_frame, image=coin_img, bg=self.player_color_hex)
            coin_lbl.image = coin_img  # type: ignore[attr-defined]
            coin_lbl.place(x=screen_width-100, rely=0.5, anchor="w")
            
            saldo_lbl = tk.Label(header_frame, text=f"{player_dashboard.saldo}", 
                               font=("Helvetica", 16, "bold"), bg=self.player_color_hex, fg="black")
            saldo_lbl.place(x=screen_width-70, rely=0.5, anchor="w")
        
        # Frame central para conteúdo
        confirm_frame = tk.Frame(self, bg="black")
        confirm_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Pergunta principal
        question_lbl = tk.Label(confirm_frame, text="Are you sure you want to sell?", 
                               font=("Helvetica", 16, "bold"), fg="white", bg="black")
        question_lbl.pack(pady=(60, 30))
        
        # Saldo atual
        balance_lbl = tk.Label(confirm_frame, text=f"Your balance: {player_dashboard.saldo}", 
                              font=("Helvetica", 16), fg="yellow", bg="black")
        balance_lbl.pack(pady=(0, 20))
        
        # Valor da carta
        valor = None
        try:
            import re
            nome = os.path.basename(carta_path)
            print(f"DEBUG: Extraindo valor do arquivo: {nome}")
            
            # Tentar diferentes padrões de extração
            match = re.search(r'_(\d+)\.', nome)
            if match:
                valor = int(match.group(1))
                print(f"DEBUG: Valor extraído: {valor}")
            else:
                # Tentar outros padrões
                match = re.search(r'(\d+)', nome)
                if match:
                    valor = int(match.group(1))
                    print(f"DEBUG: Valor extraído (padrão alternativo): {valor}")
                else:
                    print(f"DEBUG: Nenhum valor encontrado no nome do arquivo")
                    valor = 50  # valor padrão
        except Exception as e:
            print(f"DEBUG: Erro ao extrair valor: {e}")
            valor = 50  # valor padrão
        
        # Frame para mostrar valor da carta
        value_frame = tk.Frame(confirm_frame, bg="black")
        value_frame.pack(pady=(0, 40))
        
        value_text_lbl = tk.Label(value_frame, text="Card value: ", 
                                 font=("Helvetica", 16), fg="white", bg="black")
        value_text_lbl.pack(side="left")
        
        value_amount_lbl = tk.Label(value_frame, text=str(valor), 
                                   font=("Helvetica", 16, "bold"), fg="yellow", bg="black")
        value_amount_lbl.pack(side="left", padx=(5, 5))
        
        # Ícone da moeda
        try:
            picoin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24,24)))
            picoin_lbl = tk.Label(value_frame, image=picoin_img, bg="black")
            picoin_lbl.image = picoin_img  # type: ignore[attr-defined]
            picoin_lbl.pack(side="left")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar ícone da moeda: {e}")
        
        # Frame para botões
        btns_frame = tk.Frame(confirm_frame, bg="black")
        btns_frame.pack(pady=20)
        
        def confirmar():
            print("DEBUG: Confirmar venda - início (StoreWindow)")
            print(f"DEBUG: Valor da carta: {valor}")
            
            # Atualiza saldos
            if valor is not None and valor > 0:
                # Player recebe o dinheiro
                player_dashboard.saldo += valor
                # Store paga (perde dinheiro)
                self.saldo -= valor
                
                print(f"DEBUG: Saldos atualizados - Player: {player_dashboard.saldo}, Store: {self.saldo}")
                
                # Remove carta do inventário do player
                if (hasattr(player_dashboard, 'inventario') and 
                    player_dashboard.inventario and 
                    carta_tipo in player_dashboard.inventario and 
                    carta_path in player_dashboard.inventario[carta_tipo]):
                    
                    player_dashboard.inventario[carta_tipo].remove(carta_path)
                    print(f"DEBUG: Carta removida do inventário do player: {carta_path}")
                
                # IMPORTANTE: Sincronizar o inventário da Store com o do PlayerDashboard
                # A Store mantém uma referência ao inventário do PlayerDashboard
                if hasattr(self, 'inventario') and self.inventario is not None:
                    # Atualizar o inventário da Store para refletir as mudanças
                    self.inventario = player_dashboard.inventario
                    print(f"DEBUG: Inventário da Store sincronizado com o PlayerDashboard")
                
                # CORREÇÃO: NÃO adicionar a carta ao inventário da Store
                # porque a Store usa a referência do inventário do PlayerDashboard
                # Adicionar a carta vendida ao inventário da Store causaria que ela aparecesse novamente
                print(f"DEBUG: Carta vendida não será adicionada ao inventário da Store para evitar duplicação")
            
            print(f"DEBUG: Venda confirmada - Player saldo: {player_dashboard.saldo}, Store saldo: {self.saldo}")
            
            # ALTERAÇÃO: Volta à página de venda em vez da página inicial da Store
            if hasattr(self, 'current_sell_type') and self.current_sell_type:
                # Volta à página de venda do mesmo tipo
                self.show_sell_inventory_paginated(self.current_sell_type, getattr(self, 'current_sell_page', 0))
                print(f"DEBUG: Voltando à página de venda de {self.current_sell_type}")
            else:
                # Fallback para a página inicial da Store se não houver tipo guardado
                self.voltar_para_store()
                print("DEBUG: Voltando à página inicial da Store (fallback)")
        
        def cancelar():
            print("DEBUG: Venda cancelada - voltando à visualização da carta")
            self.iniciar_venda_carta(carta_path, carta_tipo, player_dashboard)
        
        # Botões Yes e No
        btn_yes = tk.Button(btns_frame, text="Yes", font=("Helvetica", 14, "bold"), 
                           bg="#4CAF50", fg="white", width=8, 
                           command=confirmar, cursor="hand2")
        btn_yes.pack(side="left", padx=20, pady=10)
        
        btn_no = tk.Button(btns_frame, text="No", font=("Helvetica", 14, "bold"), 
                          bg="#F44336", fg="white", width=8, 
                          command=cancelar, cursor="hand2")
        btn_no.pack(side="left", padx=20, pady=10)
        
        print("DEBUG: confirmar_venda_carta interface criada com sucesso")

    def rebuild_store_interface(self):
        """Reconstrói a interface da Store após voltar da página de compra"""
        print("DEBUG: rebuild_store_interface chamado")
        
        try:
            # IMPORTANTE: Sincronizar inventário com o PlayerDashboard antes de reconstruir
            if hasattr(self, 'dashboard') and self.dashboard and hasattr(self.dashboard, 'inventario'):
                self.inventario = self.dashboard.inventario
                print("DEBUG: Inventário sincronizado com PlayerDashboard no rebuild_store_interface")
            
            # Garante que a janela está visível e no estado correto
            self.deiconify()
            self.configure(bg="black")
            self.update_idletasks()
            print("DEBUG: Janela preparada para reconstrução")
            
            # Barra superior com imagem Store_awning.png
            try:
                screen_width = self.winfo_screenwidth()
                if screen_width <= 1:  # Se retornar um valor inválido
                    screen_width = 800  # valor padrão
                    print("DEBUG: Usando largura padrão")
            except:
                screen_width = 800  # valor padrão em caso de erro
                print("DEBUG: Erro ao obter largura da tela, usando padrão")
            
            awning_img = ImageTk.PhotoImage(Image.open(AWNING_IMG).resize((screen_width, 50)))
            awning_label = tk.Label(self, image=awning_img, bg="black")
            awning_label.image = awning_img  # type: ignore[attr-defined]
            awning_label.pack(pady=(0, 10), fill="x")
            print(f"DEBUG: Barra superior criada com largura {screen_width}")
            
            # Frame principal para os botões
            main_frame = tk.Frame(self, bg="black")
            main_frame.pack(anchor="center", pady=(0, 10))
            print("DEBUG: Frame principal criado")

            btn_font = ("Helvetica", 18, "bold")
            btn_size = {"width": 8, "height": 5}

            # Primeira linha: Actions, Events, Challenges (neutras) com imagens GRANDES
            img_size = (90, 90)
            actions_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "Actions_button.png")).resize(img_size))
            events_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "Events_button.png")).resize(img_size))
            challenges_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "Challenges_button.png")).resize(img_size))
            print("DEBUG: Imagens dos botões carregadas")

            btn_a = tk.Button(main_frame, image=actions_img, bg="#000000", activebackground="#000000", width=75, height=80, highlightthickness=0, bd=0)
            btn_e = tk.Button(main_frame, image=events_img, bg="#000000", activebackground="#000000", width=75, height=80, highlightthickness=0, bd=0)
            btn_d = tk.Button(main_frame, image=challenges_img, bg="#000000", activebackground="#000000", width=75, height=80, highlightthickness=0, bd=0)

            btn_a.grid(row=0, column=0, padx=10, pady=(5, 2), sticky="n")
            btn_e.grid(row=0, column=1, padx=10, pady=(5, 2), sticky="n")
            btn_d.grid(row=0, column=2, padx=10, pady=(5, 2), sticky="n")
            print("DEBUG: Botões Actions, Events, Challenges criados e posicionados")

            # Imagens devem ser mantidas como referências
            btn_a.image = actions_img
            btn_e.image = events_img
            btn_d.image = challenges_img

            # Comandos padrão vazios - serão ativados quando destacados
            btn_a.config(command="")
            btn_e.config(command="")
            btn_d.config(command="")

            self.btn_a = btn_a
            self.btn_e = btn_e
            self.btn_d = btn_d
            self.store_buttons = [btn_a, btn_e, btn_d]

            # Frame para centralizar os botões das cartas do jogador
            players_frame = tk.Frame(self, bg="black")
            players_frame.pack(pady=(0, 0))
            print("DEBUG: Frame dos jogadores criado")

            btn_font = ("Helvetica", 18, "bold")

            # Botões para Users, Equipments, Activities, Services (todos com a cor do jogador)
            btn_users = tk.Button(players_frame, text="Users", font=btn_font, bg=self.player_color_hex, fg="black", 
                                 relief="flat", borderwidth=0, width=10, height=4)
            btn_equipments = tk.Button(players_frame, text="Equipments", font=btn_font, bg=self.player_color_hex, fg="black", 
                                     relief="flat", borderwidth=0, width=10, height=4)
            btn_activities = tk.Button(players_frame, text="Activities", font=btn_font, bg=self.player_color_hex, fg="black", 
                                    relief="flat", borderwidth=0, width=10, height=4)
            btn_services = tk.Button(players_frame, text="Services", font=btn_font, bg=self.player_color_hex, fg="black", 
                                    relief="flat", borderwidth=0, width=10, height=4)

            # Aplicar cantos arredondados usando configuração adicional
            for btn in [btn_users, btn_equipments, btn_activities, btn_services]:
                btn.config(relief="flat", borderwidth=0, highlightthickness=0)
                # Configurar cor de fundo ativa igual à cor normal
                btn.config(activebackground=self.player_color_hex, activeforeground="black")

            btn_users.grid(row=0, column=0, padx=10, pady=5)
            btn_equipments.grid(row=0, column=1, padx=10, pady=5)
            btn_activities.grid(row=1, column=0, padx=10, pady=5)
            btn_services.grid(row=1, column=1, padx=10, pady=5)

            self.card_buttons = {
                "users": btn_users,
                "equipments": btn_equipments,
                "activities": btn_activities,
                "services": btn_services
            }

            # Comandos padrão vazios - serão ativados quando destacados
            btn_users.config(command="")
            btn_equipments.config(command="")
            btn_activities.config(command="")
            btn_services.config(command="")

            # Frame para os botões de ação na parte inferior (inicialmente oculto)
            self.action_frame = tk.Frame(self, bg="black")

            # Sub-frame centralizado para os botões
            self.action_buttons_frame = tk.Frame(self.action_frame, bg="black")
            self.action_buttons_frame.pack(anchor="center", pady=2)
            
            # Botões de ação: Buy, Sell, Skip dentro de frames de tamanho fixo
            action_font = ("Helvetica", 14, "bold")
            frame_width = 100
            frame_height = 50

            self.buy_frame = tk.Frame(self.action_buttons_frame, width=frame_width, height=frame_height, bg="black")
            self.sell_frame = tk.Frame(self.action_buttons_frame, width=frame_width, height=frame_height, bg="black")
            self.skip_frame = tk.Frame(self.action_buttons_frame, width=frame_width, height=frame_height, bg="black")
            self.buy_frame.pack_propagate(False)
            self.sell_frame.pack_propagate(False)
            self.skip_frame.pack_propagate(False)

            btn_buy = tk.Button(self.buy_frame, text="BUY", font=action_font, bg="#4CAF50", fg="white", 
                               relief="flat", borderwidth=0,
                               command=self.buy_action)
            btn_sell = tk.Button(self.sell_frame, text="SELL", font=action_font, bg="#F44336", fg="white", 
                                relief="flat", borderwidth=0,
                                command=self.sell_action)
            btn_skip = tk.Button(self.skip_frame, text="SKIP", font=action_font, bg="#FF9800", fg="white", 
                                relief="flat", borderwidth=0,
                                command=self.skip_action)
            # Destacar cor ativa igual à cor normal
            for btn in [btn_buy, btn_sell, btn_skip]:
                btn.config(activebackground=btn.cget("bg"), activeforeground=btn.cget("fg"))

            # Centralizar cada botão no seu frame
            btn_sell.place(relx=0.5, rely=0.5, anchor="center")
            btn_buy.place(relx=0.5, rely=0.5, anchor="center")
            btn_skip.place(relx=0.5, rely=0.5, anchor="center")

            # Pack frames lado a lado
            self.sell_frame.pack(side="left", padx=10, pady=0)
            self.buy_frame.pack(side="left", padx=10, pady=0)
            self.skip_frame.pack(side="left", padx=10, pady=0)

            self.btn_buy = btn_buy
            self.btn_sell = btn_sell
            self.btn_skip = btn_skip

            # Garantir que os botões de ação estão escondidos inicialmente
            self.hide_action_buttons()
            print("DEBUG: Botões de ação escondidos")

            # --- CORREÇÃO: Aplicar destaque e comandos corretos para casas neutras e normais ---
            if hasattr(self, 'casa_tipo') and hasattr(self, 'casa_cor') and self.casa_tipo and self.casa_cor:
                print(f"DEBUG: Aplicando destaque para {self.casa_tipo} {self.casa_cor}")
                # Para casas neutras, garantir que o tipo é plural (actions, events, challenges)
                tipo_map = {"action": "actions", "event": "events", "challenge": "challenges"}
                casa_tipo = self.casa_tipo
                if self.casa_cor == "neutral":
                    casa_tipo = tipo_map.get(self.casa_tipo, self.casa_tipo)
                self.highlight_casa(casa_tipo, self.casa_cor)
            else:
                print("DEBUG: Desabilitando todos os botões - sem destaque")
                self.disable_all_buttons()
            
            # Se for casa de outro jogador, sempre habilita os botões Users, Equipment, Activities, Services
            if getattr(self, 'other_player_house', False):
                casa_cor_atual = getattr(self, 'casa_cor', 'neutral')
                # Configurar comandos para os botões permitidos em casa de outro jogador
                if self.card_buttons.get("users"):
                    self.card_buttons["users"].config(command=lambda: self.tirar_carta("users", casa_cor_atual))
                if self.card_buttons.get("equipments"):
                    self.card_buttons["equipments"].config(command=lambda: self.tirar_carta("equipments", casa_cor_atual))
                if self.card_buttons.get("activities"):
                    self.card_buttons["activities"].config(command=lambda: self.tirar_carta("activities", casa_cor_atual))
                if self.card_buttons.get("services"):
                    self.card_buttons["services"].config(command=lambda: self.tirar_carta("services", casa_cor_atual))
                print("DEBUG: Configuração para casa de outro jogador aplicada (incluindo Activities)")
            
            # Força update final para garantir que tudo é exibido
            self.update_idletasks()
            self.update()
            
            # Barra inferior com imagem BelowBar_store.png
            belowbar_img = ImageTk.PhotoImage(Image.open(BELOWBAR_IMG).resize((screen_width, 50)))
            belowbar_label = tk.Label(self, image=belowbar_img, bg="black")
            belowbar_label.image = belowbar_img  # type: ignore[attr-defined]
            belowbar_label.pack(side="bottom", fill="x")

            # Mover saldo e piccoin para parte inferior direita (por cima do BelowBar)
            coin_img_bottom = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24, 24)))
            coin_lbl_bottom = tk.Label(self, image=coin_img_bottom, bg="#DC8392")
            coin_lbl_bottom.image = coin_img_bottom  # type: ignore[attr-defined]
            coin_lbl_bottom.place(x=screen_width-100, rely=1.0, y=-25, anchor="w")
            
            saldo_lbl_bottom = tk.Label(self, text=f"{self.saldo}", font=("Helvetica", 16, "bold"), fg="black", bg="#DC8392")
            saldo_lbl_bottom.place(x=screen_width-70, rely=1.0, y=-25, anchor="w")
            self.coin_img = coin_img_bottom  # manter referência
            print(f"DEBUG: Saldo exibido: {self.saldo}")
            
            # Botão do Player no canto superior direito para ir ao PlayerDashboard
            def abrir_playerdashboard():
                """Abre a interface principal do PlayerDashboard (igual ao botão Player das cartas de Challenges)"""
                print("DEBUG: Botão Player pressionado - abrindo interface principal do PlayerDashboard")
                if self.dashboard and hasattr(self.dashboard, "playerdashboard_interface"):
                    self.dashboard.playerdashboard_interface(
                        self.dashboard.player_name,
                        self.dashboard.saldo,
                        self.dashboard.other_players
                    )
                    print("DEBUG: Interface principal do PlayerDashboard aberta com sucesso")
                else:
                    print("DEBUG: ERRO - PlayerDashboard não disponível ou método playerdashboard_interface não encontrado")

            try:
                # Carregar ícone do jogador
                user_icon_path = os.path.join(IMG_DIR, f"{self.player_color}_user_icon.png")
                user_icon_img = ImageTk.PhotoImage(Image.open(user_icon_path).resize((48, 48)))
                btn_player = tk.Button(self, image=user_icon_img, bg="black", relief="flat", borderwidth=0, 
                                      command=abrir_playerdashboard, cursor="hand2", activebackground="black",
                                      highlightthickness=0)
                btn_player.image = user_icon_img  # Manter referência para evitar garbage collection
                btn_player.place(x=screen_width-15, y=5, anchor="ne")  # Movido mais para a direita e para cima
                print(f"DEBUG: Botão Player criado com ícone {self.player_color}_user_icon.png")
            except Exception as e:
                print(f"DEBUG: Erro ao carregar ícone do jogador {self.player_color}_user_icon.png: {e}")
                # Fallback para botão de texto se não conseguir carregar a imagem
                btn_player = tk.Button(self, text="👤", font=("Helvetica", 20), bg="black", fg="white", 
                                      relief="flat", borderwidth=0, command=abrir_playerdashboard, cursor="hand2",
                                      activebackground="black", activeforeground="white", highlightthickness=0)
                btn_player.place(x=screen_width-15, y=5, anchor="ne")  # Movido mais para a direita e para cima
                print("DEBUG: Botão Player criado com ícone de fallback")
            
            # Garante que a janela está em primeiro plano
            self.lift()
            self.focus_force()
            
            print("DEBUG: rebuild_store_interface terminado com sucesso")
        except Exception as e:
            print(f"DEBUG: ERRO em rebuild_store_interface: {e}")
            import traceback
            traceback.print_exc()

    def show_inventory_matrix_challenges(self, tipos, page=0, carta_fullscreen_path=None):
        """
        Página de inventário Activities/Challenges sincronizada para casas de Challenges.
        O botão Back volta para a carta fullscreen de Challenge.
        """
        print(f"DEBUG: show_inventory_matrix_challenges chamado - tipos: {tipos}, page: {page}")
        
        # Limpa todos os widgets da Store
        for widget in self.winfo_children():
            widget.destroy()
        self.configure(bg="black")
        
        # Sincronizar inventário com o PlayerDashboard
        if hasattr(self, 'dashboard') and self.dashboard and hasattr(self.dashboard, 'inventario'):
            self.inventario = self.dashboard.inventario
            print("DEBUG: Inventário sincronizado com PlayerDashboard")
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Barra superior com imagem Store_awning.png
        try:
            awning_img = ImageTk.PhotoImage(Image.open(AWNING_IMG).resize((screen_width, 50)))
            awning_label = tk.Label(self, image=awning_img, bg="black")
            awning_label.image = awning_img
            awning_label.pack(pady=(0, 10), fill="x")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar awning: {e}")
            # Fallback para barra simples
            header_frame = tk.Frame(self, bg="#DC8392", height=50)
            header_frame.pack(fill="x", pady=(0, 10))
            header_frame.pack_propagate(False)
        
        # Título
        if len(tipos) == 1:
            title_str = tipos[0].capitalize()
        else:
            title_str = "Activities / Challenges"
        title = tk.Label(self, text=title_str, font=("Helvetica", 22, "bold"), fg="white", bg="black")
        title.place(relx=0.5, y=65, anchor="n")
        
        # Junta todas as cartas dos tipos (sincronizada com PlayerDashboard)
        cartas = []
        for t in tipos:
            if hasattr(self, 'inventario') and self.inventario and t in self.inventario:
                cartas += self.inventario[t]
        
        print(f"DEBUG: Total de cartas encontradas: {len(cartas)}")
        
        # Paginação
        cards_per_page = 4
        total_pages = max(1, (len(cartas) + cards_per_page - 1) // cards_per_page)
        page = max(0, min(page, total_pages - 1))
        start_idx = page * cards_per_page
        end_idx = start_idx + cards_per_page
        cartas_page = cartas[start_idx:end_idx]
        
        # Frame para as cartas
        matriz_frame = tk.Frame(self, bg="black")
        matriz_frame.place(relx=0.5, rely=0.5, anchor="center")
        n_col = 2
        card_w, card_h = 85, 120
        
        # Manter referências das imagens
        self._challenge_inv_imgs = []
        
        for idx, carta_path in enumerate(cartas_page):
            row = idx // n_col
            col = idx % n_col
            try:
                img = ImageTk.PhotoImage(Image.open(carta_path).resize((card_w, card_h)))
                self._challenge_inv_imgs.append(img)
            except Exception as e:
                print(f"DEBUG: Erro ao carregar carta {carta_path}: {e}")
                continue
            
            carta_lbl = tk.Label(matriz_frame, image=img, bg="black", cursor="hand2")
            carta_lbl.image = img
            carta_lbl.grid(row=row, column=col, padx=8, pady=8)
            # Callback para mostrar carta fullscreen
            carta_lbl.bind("<Button-1>", lambda e, p=carta_path: self.show_card_fullscreen_inventory_challenges(p, tipos, page, carta_fullscreen_path))
        
        # Mensagem se não houver cartas
        if not cartas_page:
            empty_lbl = tk.Label(self, text="No cards available", font=("Helvetica", 18), fg="gray", bg="black")
            empty_lbl.place(relx=0.5, rely=0.5, anchor="center")
        
        # Setas de navegação à direita
        if total_pages > 1:
            seta_x = 0.90
            if page > 0:
                seta_cima = tk.Button(self, text="▲", font=("Helvetica", 18, "bold"), bg="#222", fg="white", width=2, 
                                    command=lambda: self.show_inventory_matrix_challenges(tipos, page-1, carta_fullscreen_path))
                seta_cima.place(relx=seta_x, rely=0.38, anchor="center")
            if page < total_pages - 1:
                seta_baixo = tk.Button(self, text="▼", font=("Helvetica", 18, "bold"), bg="#222", fg="white", width=2, 
                                     command=lambda: self.show_inventory_matrix_challenges(tipos, page+1, carta_fullscreen_path))
                seta_baixo.place(relx=seta_x, rely=0.62, anchor="center")
        
        # Botão Back centrado na parte inferior - volta para a carta fullscreen de Challenge
        def voltar_carta_challenge():
            print("DEBUG: Voltando para carta fullscreen de Challenge com botões de aceitar/recusar")
            if carta_fullscreen_path and os.path.exists(carta_fullscreen_path):
                self.mostrar_carta_fullscreen_escolha(carta_fullscreen_path, "challenges")
            else:
                print("DEBUG: Carta fullscreen path não encontrado, voltando para store")
                self.voltar_para_store()
        
        back_btn = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), bg="#005c75", fg="white", width=10, 
                           command=voltar_carta_challenge)
        back_btn.place(relx=0.5, rely=0.98, anchor="s")
        
        # Barra inferior com imagem BelowBar_store.png
        belowbar_img = ImageTk.PhotoImage(Image.open(BELOWBAR_IMG).resize((screen_width, 50)))
        belowbar_label = tk.Label(self, image=belowbar_img, bg="black")
        belowbar_label.image = belowbar_img  # type: ignore[attr-defined]
        belowbar_label.pack(side="bottom", fill="x")

        # Mover saldo e piccoin para parte inferior direita (por cima do BelowBar)
        coin_img_bottom = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24, 24)))
        coin_lbl_bottom = tk.Label(self, image=coin_img_bottom, bg="#DC8392")
        coin_lbl_bottom.image = coin_img_bottom  # type: ignore[attr-defined]
        coin_lbl_bottom.place(x=screen_width-100, rely=1.0, y=-25, anchor="w")
        
        saldo_lbl_bottom = tk.Label(self, text=f"{self.saldo}", font=("Helvetica", 16, "bold"), fg="black", bg="#DC8392")
        saldo_lbl_bottom.place(x=screen_width-70, rely=1.0, y=-25, anchor="w")
        
        # Botão do Player no canto superior direito para ir ao PlayerDashboard
        def abrir_playerdashboard():
            """Abre o PlayerDashboard e fecha a Store"""
            print("DEBUG: Botão Player pressionado - abrindo PlayerDashboard")
            if self.dashboard:
                self.destroy()  # Fecha a Store
                self.dashboard.deiconify()  # Mostra o PlayerDashboard
                self.dashboard.lift()  # Traz para a frente
                self.dashboard.focus_force()  # Força o foco
                print("DEBUG: PlayerDashboard aberto com sucesso")
            else:
                print("DEBUG: ERRO - PlayerDashboard não disponível")

        try:
            # Carregar ícone do jogador
            user_icon_path = os.path.join(IMG_DIR, f"{self.player_color}_user_icon.png")
            user_icon_img = ImageTk.PhotoImage(Image.open(user_icon_path).resize((48, 48)))
            btn_player = tk.Button(self, image=user_icon_img, bg="black", relief="flat", borderwidth=0, 
                                  command=abrir_playerdashboard, cursor="hand2", activebackground="black")
            btn_player.image = user_icon_img  # Manter referência para evitar garbage collection
            btn_player.place(x=screen_width-60, y=10, anchor="ne")  # Canto superior direito
            print(f"DEBUG: Botão Player criado com ícone {self.player_color}_user_icon.png")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar ícone do jogador {self.player_color}_user_icon.png: {e}")
            # Fallback para botão de texto se não conseguir carregar a imagem
            btn_player = tk.Button(self, text="👤", font=("Helvetica", 20), bg="black", fg="white", 
                                  relief="flat", borderwidth=0, command=abrir_playerdashboard, cursor="hand2",
                                  activebackground="black", activeforeground="white")
            btn_player.place(x=screen_width-60, y=10, anchor="ne")  # Canto superior direito
            print("DEBUG: Botão Player criado com ícone de fallback")
        
        # Atualizar display
        self.update_idletasks()
        self.update()
        
        print("DEBUG: show_inventory_matrix_challenges terminado com sucesso")

    def show_card_fullscreen_inventory_challenges(self, carta_path, tipos, page=0, carta_fullscreen_path=None):
        """
        Mostra uma carta do inventário em fullscreen com botão Back para voltar ao inventário de challenges.
        """
        print(f"DEBUG: show_card_fullscreen_inventory_challenges chamado - carta_path: {carta_path}")
        
        # Limpa widgets
        for widget in self.winfo_children():
            widget.destroy()
        self.configure(bg="black")
        
        # Carregar e mostrar a carta
        try:
            pil_img = Image.open(carta_path)
            img_w, img_h = pil_img.size
            max_w, max_h = self.winfo_screenwidth(), self.winfo_screenheight()
            ratio = min(max_w/img_w, max_h/img_h)
            new_w, new_h = int(img_w*ratio), int(img_h*ratio)
            pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            carta_img = ImageTk.PhotoImage(pil_img)
            carta_real_lbl = tk.Label(self, image=carta_img, bg="black", borderwidth=0, highlightthickness=0)
            carta_real_lbl.image = carta_img
            carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center")
            
        except Exception as e:
            print(f"DEBUG: Erro ao carregar carta: {e}")
            # Mostrar placeholder em caso de erro
            error_lbl = tk.Label(self, text="Error loading card", font=("Helvetica", 20), fg="red", bg="black")
            error_lbl.place(relx=0.5, rely=0.5, anchor="center")
        
        # Botão X para voltar ao inventário
        def voltar_inventario():
            print("DEBUG: Voltando ao inventário de challenges")
            self.show_inventory_matrix_challenges(tipos, page, carta_fullscreen_path)
        
        x_btn = tk.Button(self, text="✖", font=("Helvetica", 24, "bold"), bg="#AAAAAA", fg="white", width=2, height=1, 
                         borderwidth=0, highlightthickness=0, command=voltar_inventario, cursor="hand2", activebackground="#CCCCCC")
        x_btn.place(relx=0.98, rely=0, anchor="ne")
        
        print("DEBUG: show_card_fullscreen_inventory_challenges terminado com sucesso")

    def show_inventory_matrix_buy(self, tipos, page=0, current_card_type=None):
        """
        Página de inventário sincronizada para páginas de compra.
        O botão Back volta para a página de compra.
        """
        print(f"DEBUG: show_inventory_matrix_buy chamado - tipos: {tipos}, page: {page}, current_card_type: {current_card_type}")
        
        # Limpa todos os widgets da Store
        for widget in self.winfo_children():
            widget.destroy()
        self.configure(bg="black")
        
        # Sincronizar inventário com o PlayerDashboard
        if hasattr(self, 'dashboard') and self.dashboard and hasattr(self.dashboard, 'inventario'):
            self.inventario = self.dashboard.inventario
            print("DEBUG: Inventário sincronizado com PlayerDashboard")
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Barra superior com imagem TopBar da cor do jogador
        try:
            topbar_img_path = os.path.join(IMG_DIR, f"TopBar_{self.player_color}.png")
            topbar_img = ImageTk.PhotoImage(Image.open(topbar_img_path).resize((screen_width, 60)))
            topbar_label = tk.Label(self, image=topbar_img, bg="black", borderwidth=0, highlightthickness=0)
            topbar_label.image = topbar_img  # type: ignore[attr-defined]
            topbar_label.pack(side="top", fill="x")
            
            # Nome do jogador centralizado sobre a imagem
            name_lbl = tk.Label(self, text=self.player_name, 
                               font=("Helvetica", 18, "bold"), bg=self.player_color_hex, fg="black")
            name_lbl.place(relx=0.5, y=25, anchor="n")
            
            # Saldo e piccoin na barra superior, à direita
            coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24, 24)))
            coin_lbl = tk.Label(self, image=coin_img, bg=self.player_color_hex)
            coin_lbl.image = coin_img  # type: ignore[attr-defined]
            coin_lbl.place(x=screen_width-100, y=30)
            
            # Usar o saldo do jogador em vez do saldo da Store
            saldo_jogador = self.dashboard.saldo if self.dashboard else self.saldo
            saldo_lbl = tk.Label(self, text=f"{saldo_jogador}", 
                               font=("Helvetica", 16, "bold"), fg="black", bg=self.player_color_hex)
            saldo_lbl.place(x=screen_width-70, y=30)
            
        except Exception as e:
            print(f"DEBUG: Erro ao carregar TopBar, usando header simples: {e}")
            # Fallback para header simples se não conseguir carregar a imagem
            header_frame = tk.Frame(self, bg=self.player_color_hex, height=60)
            header_frame.pack(fill="x", pady=0)
            header_frame.pack_propagate(False)
            
            name_lbl = tk.Label(header_frame, text=self.player_name, 
                               font=("Helvetica", 18, "bold"), bg=self.player_color_hex, fg="black")
            name_lbl.place(relx=0.5, rely=0.5, anchor="center")
            
            coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24, 24)))
            coin_lbl = tk.Label(header_frame, image=coin_img, bg=self.player_color_hex)
            coin_lbl.image = coin_img  # type: ignore[attr-defined]
            coin_lbl.place(x=screen_width-100, rely=0.5, anchor="w")
            
            # Usar o saldo do jogador em vez do saldo da Store
            saldo_jogador = self.dashboard.saldo if self.dashboard else self.saldo
            saldo_lbl = tk.Label(header_frame, text=f"{saldo_jogador}", 
                               font=("Helvetica", 16, "bold"), bg=self.player_color_hex, fg="black")
            saldo_lbl.place(x=screen_width-70, rely=0.5, anchor="w")
        
        # Título
        if len(tipos) == 1:
            title_str = tipos[0].capitalize()
        else:
            title_str = " / ".join([t.capitalize() for t in tipos])
        title = tk.Label(self, text=title_str, font=("Helvetica", 22, "bold"), fg="white", bg="black")
        title.place(relx=0.5, y=75, anchor="n")  # Ajustado para ficar abaixo da TopBar
        
        # Junta todas as cartas dos tipos (sincronizada com PlayerDashboard)
        cartas = []
        for t in tipos:
            if hasattr(self, 'inventario') and self.inventario and t in self.inventario:
                cartas += self.inventario[t]
        
        print(f"DEBUG: Total de cartas encontradas: {len(cartas)}")
        
        # Paginação
        cards_per_page = 4
        total_pages = max(1, (len(cartas) + cards_per_page - 1) // cards_per_page)
        page = max(0, min(page, total_pages - 1))
        start_idx = page * cards_per_page
        end_idx = start_idx + cards_per_page
        cartas_page = cartas[start_idx:end_idx]
        
        # Frame para as cartas
        matriz_frame = tk.Frame(self, bg="black")
        matriz_frame.place(relx=0.5, rely=0.5, anchor="center")
        n_col = 2
        card_w, card_h = 85, 120
        
        # Manter referências das imagens
        self._buy_inv_imgs = []
        
        for idx, carta_path in enumerate(cartas_page):
            row = idx // n_col
            col = idx % n_col
            try:
                img = ImageTk.PhotoImage(Image.open(carta_path).resize((card_w, card_h)))
                self._buy_inv_imgs.append(img)
            except Exception as e:
                print(f"DEBUG: Erro ao carregar carta {carta_path}: {e}")
                continue
            
            carta_lbl = tk.Label(matriz_frame, image=img, bg="black", cursor="hand2")
            carta_lbl.image = img
            carta_lbl.grid(row=row, column=col, padx=8, pady=8)
            # Callback para mostrar carta fullscreen
            carta_lbl.bind("<Button-1>", lambda e, p=carta_path: self.show_card_fullscreen_inventory_buy(p, tipos, page, current_card_type))
        
        # Mensagem se não houver cartas
        if not cartas_page:
            empty_lbl = tk.Label(self, text="No cards available", font=("Helvetica", 18), fg="gray", bg="black")
            empty_lbl.place(relx=0.5, rely=0.5, anchor="center")
        
        # Setas de navegação à direita
        if total_pages > 1:
            seta_x = 0.90
            if page > 0:
                seta_cima = tk.Button(self, text="▲", font=("Helvetica", 18, "bold"), bg="#222", fg="white", width=2, 
                                    command=lambda: self.show_inventory_matrix_buy(tipos, page-1, current_card_type))
                seta_cima.place(relx=seta_x, rely=0.38, anchor="center")
            if page < total_pages - 1:
                seta_baixo = tk.Button(self, text="▼", font=("Helvetica", 18, "bold"), bg="#222", fg="white", width=2, 
                                     command=lambda: self.show_inventory_matrix_buy(tipos, page+1, current_card_type))
                seta_baixo.place(relx=seta_x, rely=0.62, anchor="center")
        
        # Botão Back centrado na parte inferior - volta para a página de compra
        def voltar_pagina_compra():
            print("DEBUG: Voltando para página de compra")
            if current_card_type:
                # Restaurar o tipo atual e mostrar a página de compra
                self.current_card_type = current_card_type
                self.show_buy_page()
            else:
                print("DEBUG: Tipo de carta não encontrado, voltando para store")
                self.voltar_para_store()
        
        back_btn = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), bg="#005c75", fg="white", width=10, 
                           command=voltar_pagina_compra)
        back_btn.place(relx=0.5, rely=0.98, anchor="s")
        
        # Atualizar display
        self.update_idletasks()
        self.update()
        
        print("DEBUG: show_inventory_matrix_buy terminado com sucesso")

    def show_card_fullscreen_inventory_buy(self, carta_path, tipos, page=0, current_card_type=None):
        """
        Mostra uma carta do inventário em fullscreen com botão Back para voltar ao inventário de compra.
        """
        print(f"DEBUG: show_card_fullscreen_inventory_buy chamado - carta_path: {carta_path}")
        
        # Limpa widgets
        for widget in self.winfo_children():
            widget.destroy()
        self.configure(bg="black")
        
        # Carregar e mostrar a carta
        try:
            pil_img = Image.open(carta_path)
            img_w, img_h = pil_img.size
            max_w, max_h = self.winfo_screenwidth(), self.winfo_screenheight()
            ratio = min(max_w/img_w, max_h/img_h)
            new_w, new_h = int(img_w*ratio), int(img_h*ratio)
            pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            carta_img = ImageTk.PhotoImage(pil_img)
            carta_real_lbl = tk.Label(self, image=carta_img, bg="black", borderwidth=0, highlightthickness=0)
            carta_real_lbl.image = carta_img
            carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center")
            
        except Exception as e:
            print(f"DEBUG: Erro ao carregar carta: {e}")
            # Mostrar placeholder em caso de erro
            error_lbl = tk.Label(self, text="Error loading card", font=("Helvetica", 20), fg="red", bg="black")
            error_lbl.place(relx=0.5, rely=0.5, anchor="center")
        
        # Botão X para voltar ao inventário
        def voltar_inventario():
            print("DEBUG: Voltando ao inventário de compra")
            self.show_inventory_matrix_buy(tipos, page, current_card_type)
        
        x_btn = tk.Button(self, text="✖", font=("Helvetica", 24, "bold"), bg="#AAAAAA", fg="white", width=2, height=1, 
                         borderwidth=0, highlightthickness=0, command=voltar_inventario, cursor="hand2", activebackground="#CCCCCC")
        x_btn.place(relx=0.98, rely=0, anchor="ne")
        
        print("DEBUG: show_card_fullscreen_inventory_buy terminado com sucesso")