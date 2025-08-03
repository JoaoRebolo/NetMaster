import tkinter as tk
from PIL import Image, ImageTk
import os
import re
import traceback
from card_integration import IntegratedCardDatabase
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
AWNING_IMG = os.path.join(IMG_DIR, "Store_awning_v3.png")
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
        
        # ADICIONAR: Identificador único para rastreamento
        import time
        self._store_id = f"Store_{int(time.time() * 1000)}"
        print(f"DEBUG: [__init__] Criando nova Store com ID: {self._store_id}")
        
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
        
        # CORREÇÃO: Inicializar baralho da Store sincronizado com estado atual dos baralhos globais
        # Isso garante que cartas já tiradas não apareçam novamente
        import copy
        self.cartas = copy.deepcopy(baralhos)
        print(f"DEBUG: [__init__] Baralho da Store inicializado e sincronizado com estado global")
        print(f"DEBUG: [__init__] Challenges neutral disponíveis: {len(self.cartas.get('neutral', {}).get('challenges', []))}")
        
        # IMPORTANTE: Sincronização inicial - remover cartas já no inventário do jogador
        if dashboard and hasattr(dashboard, 'inventario') and dashboard.inventario:
            print(f"DEBUG: [__init__] Iniciando sincronização com inventário do jogador...")
            total_removidas = 0
            for tipo_carta, cartas_inventario in dashboard.inventario.items():
                if cartas_inventario:  # Se há cartas deste tipo no inventário
                    print(f"DEBUG: [__init__] Verificando tipo '{tipo_carta}' - {len(cartas_inventario)} cartas no inventário")
                    
                    # Remover do baralho da cor do jogador
                    if (self.player_color in self.cartas and tipo_carta in self.cartas[self.player_color]):
                        for carta_path in cartas_inventario:
                            if carta_path in self.cartas[self.player_color][tipo_carta]:
                                self.cartas[self.player_color][tipo_carta].remove(carta_path)
                                total_removidas += 1
                                print(f"DEBUG: [__init__] Removida do baralho {self.player_color}/{tipo_carta}: {os.path.basename(carta_path)}")
                    
                    # Remover do baralho neutral
                    if ("neutral" in self.cartas and tipo_carta in self.cartas["neutral"]):
                        for carta_path in cartas_inventario:
                            if carta_path in self.cartas["neutral"][tipo_carta]:
                                self.cartas["neutral"][tipo_carta].remove(carta_path)
                                total_removidas += 1
                                print(f"DEBUG: [__init__] Removida do baralho neutral/{tipo_carta}: {os.path.basename(carta_path)}")
            
            print(f"DEBUG: [__init__] Sincronização inicial completa - {total_removidas} cartas removidas dos baralhos da Store")
        else:
            print(f"DEBUG: [__init__] Sem inventário para sincronizar ou inventário vazio")
        
        # Inicializar base de dados de cartas integrada
        try:
            self.card_database = IntegratedCardDatabase(".")
            print("DEBUG: [__init__] Base de dados de cartas inicializada com sucesso")
        except Exception as e:
            print(f"DEBUG: [__init__] Erro ao inicializar base de dados de cartas: {e}")
            self.card_database = None
        
        # Debug dos baralhos para verificar sincronização
        if 'neutral' in baralhos and 'challenges' in baralhos['neutral']:
            print(f"DEBUG: [__init__] Baralho global challenges neutral tem: {len(baralhos['neutral']['challenges'])} cartas")
        else:
            print("DEBUG: [__init__] Baralho global challenges neutral não encontrado")
        
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
        
        # Label pequeno à esquerda do logo
        left_label = tk.Label(self, text="••••", font=("Helvetica", 12, "bold"), bg="#DC8392", fg="#DC8392")
        left_label.place(relx=0.46, y=10, anchor="center")
        
        # Logo NetMaster posicionado independentemente
        try:
            logo_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "logo_netmaster_store.png")).resize((20, 20)))
            logo_lbl = tk.Label(self, image=logo_img, bg="#DC8392")
            logo_lbl.image = logo_img  # type: ignore[attr-defined]
            logo_lbl.place(relx=0.5, y=10, anchor="center")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar logo: {e}")
        
        # Label largo à direita do logo para cobrir área amarela
        right_logo_label = tk.Label(self, text="     ", font=("Helvetica", 12, "bold"), bg="#DC8392", fg="#DC8392")
        right_logo_label.place(relx=0.53, y=10, anchor="w")
        
        # Label adicional para garantir cobertura completa
        extra_cover_label = tk.Label(self, text="     ", font=("Helvetica", 10), bg="#DC8392", fg="#DC8392")
        extra_cover_label.place(relx=0.55, y=10, anchor="w")
        
        # Texto "Store" posicionado independentemente
        store_name_lbl = tk.Label(self, text="Store", 
                                 font=("Helvetica", 15, "bold"), bg="#DC8392", fg="black")
        store_name_lbl.place(relx=0.5, y=30, anchor="center")
        
        # Label pequeno à direita do nome Store
        right_store_label = tk.Label(self, text="•", font=("Helvetica", 12, "bold"), bg="#DC8392", fg="#DC8392")
        right_store_label.place(relx=0.6, y=30, anchor="center")
        
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

        # Frame para os botões de ação na parte inferior (não usado mais)
        self.action_frame = tk.Frame(self, bg="black")

        # Sub-frame centralizado para os botões (não usado mais)
        self.action_buttons_frame = tk.Frame(self.action_frame, bg="black")
        self.action_buttons_frame.pack(anchor="center", pady=2)

        # Variáveis para controlar estado de navegação
        self.current_card_type = None  # Tipo de carta atual para compra
        self.current_sell_type = None  # Tipo de carta sendo vendida
        self.current_sell_page = 0     # Página atual de venda
        
        # Variáveis para controlar estado de carta fullscreen
        self.fullscreen_carta_path = None  # Caminho da carta em fullscreen ativa
        self.fullscreen_carta_tipo = None  # Tipo da carta em fullscreen ativa

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
        # IMPORTANTE: Só mostrar o botão Player se NÃO for casa neutra (Actions/Events/Challenges)
        show_player_button = True
        if casa_tipo and casa_cor:
            # Se for casa neutra (Actions, Events, Challenges), não mostrar o botão Player
            if casa_tipo.lower() in ["actions", "action", "events", "event", "challenges", "challenge"] and casa_cor.lower() == "neutral":
                show_player_button = False
                print(f"DEBUG: Casa neutra detectada ({casa_tipo}, {casa_cor}) - botão Player NÃO será mostrado")
            else:
                print(f"DEBUG: Casa não neutra detectada ({casa_tipo}, {casa_cor}) - botão Player será mostrado")
        
        if show_player_button:
            def abrir_playerdashboard():
                """Abre a interface principal do PlayerDashboard (igual ao botão Player das cartas de Challenges)"""
                print("DEBUG: Botão Player pressionado - abrindo interface principal do PlayerDashboard")
                try:
                    if self.dashboard and hasattr(self.dashboard, "playerdashboard_interface"):
                        # Esconder a Store primeiro
                        self.withdraw()
                        print("DEBUG: Store escondida")
                        
                        # Mostrar o PlayerDashboard
                        self.dashboard.deiconify()
                        self.dashboard.state('normal')
                        self.dashboard.lift()
                        self.dashboard.focus_force()
                        print("DEBUG: PlayerDashboard mostrado")
                        
                        # Chamar a interface principal do PlayerDashboard
                        self.dashboard.playerdashboard_interface(
                            self.dashboard.player_name,
                            self.dashboard.saldo,
                            self.dashboard.other_players
                        )
                        print("DEBUG: Interface principal do PlayerDashboard aberta com sucesso")
                    else:
                        print("DEBUG: ERRO - PlayerDashboard não disponível ou método playerdashboard_interface não encontrado")
                except Exception as e:
                    print(f"DEBUG: Erro ao abrir PlayerDashboard: {e}")

            try:
                # Carregar ícone do jogador
                user_icon_path = os.path.join(IMG_DIR, f"{self.player_color}_user_icon.png")
                user_icon_img = ImageTk.PhotoImage(Image.open(user_icon_path).resize((30, 30)))
                btn_player = tk.Button(self, image=user_icon_img, bg="#DC8392", relief="flat", borderwidth=0, 
                                      command=abrir_playerdashboard, cursor="hand2", activebackground="#DC8392",
                                      highlightthickness=0)
                btn_player.image = user_icon_img  # Manter referência para evitar garbage collection
                btn_player.place(x=root.winfo_screenwidth()-10, y=5, anchor="ne")  # Movido mais para a direita e para cima
                print(f"DEBUG: Botão Player criado com ícone {self.player_color}_user_icon.png")
            except Exception as e:
                print(f"DEBUG: Erro ao carregar ícone do jogador {self.player_color}_user_icon.png: {e}")
                # Fallback para botão de texto se não conseguir carregar a imagem
                btn_player = tk.Button(self, text="👤", font=("Helvetica", 20), bg="black", fg="white", 
                                      relief="flat", borderwidth=0, command=abrir_playerdashboard, cursor="hand2",
                                      activebackground="black", activeforeground="white", highlightthickness=0)
                btn_player.place(x=root.winfo_screenwidth()-15, y=5, anchor="ne")  # Movido mais para a direita e para cima
                print("DEBUG: Botão Player criado com ícone de fallback")
        else:
            print("DEBUG: Botão Player NÃO criado - casa neutra detectada")

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
        print("DEBUG: [disable_all_buttons] Desabilitando todos os botões")
        
        # Desabilita botões neutros (Actions, Events, Challenges) e reseta aparência visual
        for btn in getattr(self, "store_buttons", []):
            btn.config(command="", state="normal", highlightbackground="black", highlightthickness=0)
        
        # Para casas de outro jogador, o comportamento é diferente
        if self.other_player_house:
            # Em casas de outro jogador, desabilita TODOS os botões inicialmente
            # O highlight_casa irá reabilitar apenas o correto
            for btn in getattr(self, "card_buttons", {}).values():
                btn.config(command="", state="disabled")
            print("DEBUG: [disable_all_buttons] Casa de outro jogador - todos os botões de carta desabilitados")
        else:
            # Para casas próprias ou neutras, desabilita todos os botões de carta
            for btn in getattr(self, "card_buttons", {}).values():
                btn.config(command="", state="disabled")
            print("DEBUG: [disable_all_buttons] Casa própria/neutra - todos os botões de carta desabilitados")

    def enable_only_highlighted_button(self, casa_tipo, casa_cor):
        """Habilita apenas o botão destacado e desativa todos os outros (neutros e inventário)."""
        print(f"DEBUG: [enable_only_highlighted_button] Configurando comando para tipo '{casa_tipo}' cor '{casa_cor}'")
        
        # Mapear qual botão deve ser destacado
        tipo_to_btn = {
            "action": self.btn_a,
            "actions": self.btn_a,
            "event": self.btn_e,
            "events": self.btn_e,
            "challenge": self.btn_d,
            "challenges": self.btn_d,
            "users": self.card_buttons.get("users"),
            "equipment": self.card_buttons.get("equipments"),
            "equipments": self.card_buttons.get("equipments"),
            "activities": self.card_buttons.get("activities"),
            "services": self.card_buttons.get("services"),
        }
        btn_destacado = tipo_to_btn.get(casa_tipo)
        
        # Desabilita todos os botões neutros, EXCETO o que deve ser destacado
        for btn in getattr(self, "store_buttons", []):
            if btn != btn_destacado:
                btn.config(command="", state="normal", highlightbackground="black", highlightthickness=0)
        
        # Desabilita todos os botões do inventário
        for btn in getattr(self, "card_buttons", {}).values():
            btn.config(command="", state="disabled")
        
        # Ativa só o botão correto e mantém/aplica o destaque
        if btn_destacado:
            print(f"DEBUG: [enable_only_highlighted_button] Habilitando botão para tipo '{casa_tipo}'")
            btn_destacado.config(command=lambda: self.tirar_carta(casa_tipo, casa_cor), state="normal")
            # Garantir que o destaque permanece aplicado
            btn_destacado.config(highlightbackground="#A020F0", highlightcolor="#A020F0", highlightthickness=6)
        else:
            print(f"DEBUG: [enable_only_highlighted_button] ERRO - Botão não encontrado para tipo '{casa_tipo}'")

    def highlight_casa(self, casa_tipo, casa_cor):
        print(f"DEBUG: [highlight_casa] Chamado com casa_tipo='{casa_tipo}', casa_cor='{casa_cor}'")
        
        # Remove destaque anterior de todos os botões
        for btn in getattr(self, "store_buttons", []):
            btn.config(highlightbackground="black", highlightthickness=0)
        for btn in getattr(self, "card_buttons", {}).values():
            btn.config(highlightbackground="black", highlightthickness=0)
        print(f"DEBUG: [highlight_casa] Destaque anterior removido de todos os botões")

        # Se for casa de outro jogador, destaca apenas o botão correspondente ao tipo da casa
        if self.other_player_house:
            print(f"DEBUG: [highlight_casa] Casa de outro jogador detectada")
            if casa_tipo in ["equipments", "services", "users", "equipment", "activities"]:
                # Normalizar tipo
                normalized_tipo = casa_tipo
                if casa_tipo == "equipment":
                    normalized_tipo = "equipments"
                
                # PRIMEIRO: Desabilita COMPLETAMENTE todos os botões (incluindo comandos)
                print(f"DEBUG: Casa de outro jogador - desabilitando todos os botões primeiro")
                for btn in getattr(self, "store_buttons", []):
                    btn.config(command="", state="normal", highlightbackground="black", highlightthickness=0)
                for btn_name, btn in getattr(self, "card_buttons", {}).items():
                    btn.config(command="", state="disabled")
                
                # SEGUNDO: Só depois habilita e destaca o botão específico da casa
                if self.card_buttons.get(normalized_tipo):
                    self.card_buttons[normalized_tipo].config(highlightbackground="#A020F0", highlightcolor="#A020F0", highlightthickness=6)
                    self.card_buttons[normalized_tipo].config(command=lambda: self.tirar_carta(normalized_tipo, casa_cor))
                    self.card_buttons[normalized_tipo].config(state="normal")
                    print(f"DEBUG: Casa de outro jogador - APENAS botão {normalized_tipo} habilitado e destacado")
                
                # TERCEIRO: Garantir que todos os outros botões permanecem desabilitados
                for btn_name, btn in getattr(self, "card_buttons", {}).items():
                    if btn_name != normalized_tipo:
                        btn.config(command="", state="disabled")
                        print(f"DEBUG: Botão {btn_name} mantido desabilitado")
            else:
                # Para casas de outro jogador não permitidas, desabilita todos completamente
                print(f"DEBUG: Casa de outro jogador não permitida - desabilitando todos os botões")
                for btn in getattr(self, "store_buttons", []):
                    btn.config(command="", state="normal", highlightbackground="black", highlightthickness=0)
                for btn in getattr(self, "card_buttons", {}).values():
                    btn.config(command="", state="disabled")
            return

        # Comportamento normal para casas próprias ou neutras
        print(f"DEBUG: [highlight_casa] Casa própria ou neutra - processando tipo '{casa_tipo}'")
        tipo_to_btn = {
            "action": self.btn_a,
            "actions": self.btn_a,
            "event": self.btn_e,
            "events": self.btn_e,
            "challenge": self.btn_d,
            "challenges": self.btn_d,
            "users": self.card_buttons.get("users"),
            "equipment": self.card_buttons.get("equipments"),  # Mapeia 'equipment' para o botão de equipamentos
            "equipments": self.card_buttons.get("equipments"),
            "activities": self.card_buttons.get("activities"),
            "services": self.card_buttons.get("services"),
        }
        btn = tipo_to_btn.get(casa_tipo)
        if btn:
            print(f"DEBUG: [highlight_casa] Botão encontrado para tipo '{casa_tipo}' - aplicando destaque ROXO")
            btn.config(highlightbackground="#A020F0", highlightcolor="#A020F0", highlightthickness=6)
            print(f"DEBUG: [highlight_casa] Destaque roxo aplicado ao botão {casa_tipo}")
            
            # Só permite clicar no botão destacado
            # Se a casa for neutra, tira carta da cor neutral
            if casa_cor == "neutral":
                print(f"DEBUG: [highlight_casa] Configurando comando para casa neutra: tirar_carta('{casa_tipo}', 'neutral')")
                btn.config(command=lambda: self.tirar_carta(casa_tipo, "neutral"))
            else:
                print(f"DEBUG: [highlight_casa] Configurando comando: tirar_carta('{casa_tipo}', '{casa_cor}')")
                btn.config(command=lambda: self.tirar_carta(casa_tipo, casa_cor))
            
            # Habilita apenas o botão destacado
            print(f"DEBUG: [highlight_casa] Chamando enable_only_highlighted_button para '{casa_tipo}'")
            self.enable_only_highlighted_button(casa_tipo, casa_cor)
            print(f"DEBUG: [highlight_casa] enable_only_highlighted_button concluído")
        else:
            print(f"DEBUG: [highlight_casa] ERRO - Botão não encontrado para tipo '{casa_tipo}'")

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

        # Label pequeno à esquerda do logo
        left_label = tk.Label(self, text="••••", font=("Helvetica", 12, "bold"), bg="#DC8392", fg="#DC8392")
        left_label.place(relx=0.46, y=10, anchor="center")

        # Logo NetMaster posicionado independentemente
        try:
            logo_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "logo_netmaster_store.png")).resize((24, 24)))
            logo_lbl = tk.Label(self, image=logo_img, bg="#DC8392")
            logo_lbl.image = logo_img  # type: ignore[attr-defined]
            logo_lbl.place(relx=0.5, y=10, anchor="center")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar logo: {e}")
        
        # Label largo à direita do logo para cobrir área amarela
        right_logo_label = tk.Label(self, text="     ", font=("Helvetica", 12, "bold"), bg="#DC8392", fg="#DC8392")
        right_logo_label.place(relx=0.53, y=10, anchor="w")
        
        # Label adicional para garantir cobertura completa
        extra_cover_label = tk.Label(self, text="     ", font=("Helvetica", 10), bg="#DC8392", fg="#DC8392")
        extra_cover_label.place(relx=0.55, y=10, anchor="w")
        
        # Texto "Store" posicionado independentemente
        store_name_lbl = tk.Label(self, text="Store", 
                                 font=("Helvetica", 15, "bold"), bg="#DC8392", fg="black")
        store_name_lbl.place(relx=0.5, y=30, anchor="center")
        
        # Label pequeno à direita do nome Store
        right_store_label = tk.Label(self, text="•", font=("Helvetica", 12, "bold"), bg="#DC8392", fg="#DC8392")
        right_store_label.place(relx=0.6, y=30, anchor="center")

        # Título
        tipo_atual = getattr(self, 'current_card_type', None)
        if not tipo_atual:
            messagebox.showinfo("Erro", "Tipo de carta não definido!")
            return
        titulo = tipo_atual.capitalize()
        title_lbl = tk.Label(self, text=f"{titulo}", font=("Helvetica", 22, "bold"), fg="white", bg="black")
        title_lbl.pack(pady=(20, 10))

        # Obter cartas disponíveis para compra do baralho LOCAL da Store (sincronizado)
        print(f"DEBUG: Buscando cartas para tipo '{tipo_atual}' e cor '{self.player_color}' no baralho LOCAL da Store")
        
        # Verificar se o tipo existe nos baralhos LOCAIS da Store (APENAS da cor do jogador)
        cartas_disp = []
        if (hasattr(self, 'cartas') and self.player_color in self.cartas and 
            tipo_atual in self.cartas[self.player_color]):
            cartas_disp = self.cartas[self.player_color][tipo_atual].copy()
            print(f"DEBUG: Encontradas {len(cartas_disp)} cartas no baralho LOCAL do jogador")
        
        # Debug adicional do baralho LOCAL
        print(f"DEBUG: Baralhos LOCAL disponíveis para {self.player_color}:")
        if hasattr(self, 'cartas') and self.player_color in self.cartas:
            for tipo, cartas in self.cartas[self.player_color].items():
                print(f"  {tipo}: {len(cartas)} cartas")
        else:
            print(f"  Nenhum baralho LOCAL encontrado para {self.player_color}")
        
        if not cartas_disp:
            print(f"DEBUG: Nenhuma carta encontrada para {tipo_atual} na cor {self.player_color}")
            
            # Mostrar mensagem de "sem cartas disponíveis" com interface completa
            sem_cartas_lbl = tk.Label(self, text="Sem cartas disponíveis!", 
                                    font=("Helvetica", 18, "bold"), 
                                    bg="black", fg="white")
            sem_cartas_lbl.place(relx=0.5, rely=0.4, anchor="center")
            
            # Adicionar mensagem adicional
            info_lbl = tk.Label(self, text="Não há mais cartas desta cor para comprar", 
                              font=("Helvetica", 14), 
                              bg="black", fg="#AAAAAA")
            info_lbl.place(relx=0.5, rely=0.5, anchor="center")
            
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

            # Botão Back para voltar à Store principal
            btn_voltar = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), 
                                  bg="#8C04A0", fg="white", width=6, 
                                  command=self.voltar_para_store)
            btn_voltar.place(relx=0.5, rely=0.98, anchor="s")
            
            return

        # IMPORTANTE: Filtrar cartas que já estão no inventário do jogador (sincronização completa)
        if self.dashboard and hasattr(self.dashboard, 'inventario') and tipo_atual in self.dashboard.inventario:
            cartas_no_inventario = self.dashboard.inventario[tipo_atual]
            cartas_antes_filtro = len(cartas_disp)
            
            # Comparar apenas nomes de arquivos (não caminhos completos) para melhor sincronização
            nomes_no_inventario = {os.path.basename(carta) for carta in cartas_no_inventario}
            cartas_disp = [carta for carta in cartas_disp if os.path.basename(carta) not in nomes_no_inventario]
            
            cartas_depois_filtro = len(cartas_disp)
            print(f"DEBUG: SINCRONIZAÇÃO - Filtrado cartas do inventário: {cartas_antes_filtro} → {cartas_depois_filtro} (removidas {cartas_antes_filtro - cartas_depois_filtro} cartas)")
            
            if cartas_antes_filtro != cartas_depois_filtro:
                print(f"DEBUG: Cartas removidas do inventário por nome:")
                for nome in nomes_no_inventario:
                    print(f"  - {nome}")
        else:
            print(f"DEBUG: Sem inventário para filtrar ou tipo '{tipo_atual}' não existe no inventário")

        # Verificar se ainda há cartas disponíveis após filtrar o inventário
        if not cartas_disp:
            print(f"DEBUG: Todas as cartas {tipo_atual} já estão no inventário do jogador")
            
            # Mostrar mensagem de "sem cartas disponíveis" com interface completa
            sem_cartas_lbl = tk.Label(self, text="Sem cartas disponíveis!", 
                                    font=("Helvetica", 18, "bold"), 
                                    bg="black", fg="white")
            sem_cartas_lbl.place(relx=0.5, rely=0.4, anchor="center")
            
            # Adicionar mensagem adicional
            info_lbl = tk.Label(self, text="Todas as cartas já estão no seu inventário", 
                              font=("Helvetica", 14), 
                              bg="black", fg="#AAAAAA")
            info_lbl.place(relx=0.5, rely=0.5, anchor="center")
            
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

            # Botão Back para voltar à Store principal
            btn_voltar = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), 
                                  bg="#8C04A0", fg="white", width=6, 
                                  command=self.voltar_para_store)
            btn_voltar.place(relx=0.5, rely=0.98, anchor="s")
            
            return

        # Filtrar User_1.png das páginas de compra (conforme solicitado)
        if tipo_atual.lower() == "users":
            cartas_antes = len(cartas_disp)
            cartas_disp = [carta for carta in cartas_disp if not os.path.basename(carta).startswith("User_1.")]
            cartas_depois = len(cartas_disp)
            if cartas_antes != cartas_depois:
                print(f"DEBUG: Filtrado User_1.png - cartas antes: {cartas_antes}, depois: {cartas_depois}")
        
        # Verificar novamente se ainda há cartas disponíveis após filtragem do User_1.png
        if not cartas_disp:
            print(f"DEBUG: Não há cartas {tipo_atual} disponíveis após todas as filtragens")
            
            # Mostrar mensagem de "sem cartas disponíveis" com interface completa
            sem_cartas_lbl = tk.Label(self, text="Sem cartas disponíveis!", 
                                    font=("Helvetica", 18, "bold"), 
                                    bg="black", fg="white")
            sem_cartas_lbl.place(relx=0.5, rely=0.4, anchor="center")
            
            # Adicionar mensagem adicional
            info_lbl = tk.Label(self, text="Não há mais cartas para comprar", 
                              font=("Helvetica", 14), 
                              bg="black", fg="#AAAAAA")
            info_lbl.place(relx=0.5, rely=0.5, anchor="center")
            
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

            # Botão Back para voltar à Store principal
            btn_voltar = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), 
                                  bg="#8C04A0", fg="white", width=6, 
                                  command=self.voltar_para_store)
            btn_voltar.place(relx=0.5, rely=0.98, anchor="s")
            
            return

        # Remover cartas duplicadas (mesmo nome de arquivo de diferentes caminhos)
        cartas_unicas = []
        nomes_vistos = set()
        for carta_path in cartas_disp:
            nome_arquivo = os.path.basename(carta_path)
            if nome_arquivo not in nomes_vistos:
                nomes_vistos.add(nome_arquivo)
                cartas_unicas.append(carta_path)
        
        if len(cartas_disp) != len(cartas_unicas):
            print(f"DEBUG: Cartas duplicadas removidas: {len(cartas_disp)} → {len(cartas_unicas)}")
            cartas_disp = cartas_unicas
        
        # Verificar mais uma vez se ainda há cartas disponíveis após remover duplicatas
        if not cartas_disp:
            print(f"DEBUG: Não há cartas {tipo_atual} disponíveis após remover duplicatas")
            
            # Mostrar mensagem de "sem cartas disponíveis" com interface completa
            sem_cartas_lbl = tk.Label(self, text="Sem cartas disponíveis!", 
                                    font=("Helvetica", 18, "bold"), 
                                    bg="black", fg="white")
            sem_cartas_lbl.place(relx=0.5, rely=0.4, anchor="center")
            
            # Adicionar mensagem adicional
            info_lbl = tk.Label(self, text="Não há mais cartas para comprar", 
                              font=("Helvetica", 14), 
                              bg="black", fg="#AAAAAA")
            info_lbl.place(relx=0.5, rely=0.5, anchor="center")
            
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

            # Botão Back para voltar à Store principal
            btn_voltar = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), 
                                  bg="#8C04A0", fg="white", width=6, 
                                  command=self.voltar_para_store)
            btn_voltar.place(relx=0.5, rely=0.98, anchor="s")
            
            return

        # Ordenar cartas por número (User_1, User_2, User_3, etc.)
        def extrair_numero_carta(carta_path):
            nome = os.path.basename(carta_path)
            match = re.search(r'_(\d+)\.', nome)
            return int(match.group(1)) if match else float('inf')  # Cartas sem número vão para o fim
        
        cartas_disp.sort(key=extrair_numero_carta)
        print(f"DEBUG: Cartas ordenadas por número: {[os.path.basename(c) for c in cartas_disp[:5]]}")  # Mostra os primeiros 5

        # === SISTEMA GRID IGUAL À PÁGINA DE VENDA ===
        # Paginação
        cards_per_page = 4
        total_pages = max(1, (len(cartas_disp) + cards_per_page - 1) // cards_per_page)
        self._current_buy_page = getattr(self, '_current_buy_page', 0)
        self._current_buy_page = max(0, min(self._current_buy_page, total_pages - 1))
        start_idx = self._current_buy_page * cards_per_page
        end_idx = start_idx + cards_per_page
        cartas_page = cartas_disp[start_idx:end_idx]
        
        # Frame para as cartas (centralizado, mas mais abaixo para não tapar o título)
        self.matriz_frame = tk.Frame(self, bg="black")
        self.matriz_frame.place(relx=0.5, rely=0.55, anchor="center")  # Movido para baixo
        
        n_col = 2  # 2 colunas
        card_w, card_h = 85, 120  # Tamanho igual ao da página de venda
        self.cards_per_page = cards_per_page
        self._buy_imgs = []
        
        # Callback para fullscreen das cartas (igual à página de venda)
        def make_fullscreen_callback(carta_path, global_idx):
            def callback(event=None):
                print(f"DEBUG: Carta clicada para compra fullscreen: {carta_path}")
                self._abrir_fullscreen_carta(global_idx)
            return callback
        
        # Criar grid de cartas
        for idx, carta_path in enumerate(cartas_page):
            row = idx // n_col
            col = idx % n_col
            global_idx = start_idx + idx
            try:
                img = ImageTk.PhotoImage(Image.open(carta_path).resize((card_w, card_h)))
                self._buy_imgs.append(img)
            except Exception as e:
                print(f"DEBUG: Erro ao carregar carta {carta_path}: {e}")
                continue
            
            carta_lbl = tk.Label(self.matriz_frame, image=img, bg="black", cursor="hand2")
            carta_lbl.image = img
            carta_lbl.grid(row=row, column=col, padx=8, pady=8)
            carta_lbl.bind("<Button-1>", make_fullscreen_callback(carta_path, global_idx))
        
        # Setas de navegação iguais à página de venda
        if total_pages > 1:
            seta_x = 0.90  # Posição igual à página de venda
            if self._current_buy_page > 0:
                seta_cima = tk.Button(self, text="▲", font=("Helvetica", 18, "bold"), bg="#222", fg="white", width=2,
                                    command=self._prev_buy_page)
                seta_cima.place(relx=seta_x, rely=0.38, anchor="center")  # Posição igual à página de venda
            if self._current_buy_page < total_pages - 1:
                seta_baixo = tk.Button(self, text="▼", font=("Helvetica", 18, "bold"), bg="#222", fg="white", width=2,
                                     command=self._next_buy_page)
                seta_baixo.place(relx=seta_x, rely=0.62, anchor="center")  # Posição igual à página de venda
        
        # Guardar dados para navegação
        self._cartas_disponiveis = cartas_disp
        self._total_pages = total_pages

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

        # Botão Back igual à página de venda (depois da barra para ficar visível)
        btn_voltar = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), 
                              bg="#8C04A0", fg="white", width=6, 
                              command=self.voltar_para_store)
        btn_voltar.place(relx=0.5, rely=0.98, anchor="s")  # Movido para cima da barra inferior

    def _prev_buy_page(self):
        """Navega para a página anterior"""
        if self._current_buy_page > 0:
            self._current_buy_page -= 1
            self._update_buy_page()

    def _next_buy_page(self):
        """Navega para a próxima página"""
        if self._current_buy_page < self._total_pages - 1:
            self._current_buy_page += 1
            self._update_buy_page()

    def _update_buy_page(self):
        """Atualiza a exibição da página atual"""
        # Limpar cartas atuais
        for widget in self.matriz_frame.winfo_children():
            widget.destroy()
        
        # Calcular cartas para esta página
        start_idx = self._current_buy_page * self.cards_per_page
        end_idx = min(start_idx + self.cards_per_page, len(self._cartas_disponiveis))
        cartas_pagina = self._cartas_disponiveis[start_idx:end_idx]
        
        # Callback para fullscreen das cartas
        def make_fullscreen_callback(carta_path, global_idx):
            def callback(event=None):
                print(f"DEBUG: Carta clicada para compra fullscreen: {carta_path}")
                self._abrir_fullscreen_carta(global_idx)
            return callback
        
        # Criar grid de cartas
        card_w, card_h = 85, 120
        for i, carta_path in enumerate(cartas_pagina):
            row = i // 2
            col = i % 2
            carta_idx_global = start_idx + i
            
            try:
                img = ImageTk.PhotoImage(Image.open(carta_path).resize((card_w, card_h)))
                carta_lbl = tk.Label(self.matriz_frame, image=img, bg="black", cursor="hand2")
                carta_lbl.image = img  # Manter referência
                carta_lbl.grid(row=row, column=col, padx=8, pady=8)
                carta_lbl.bind("<Button-1>", make_fullscreen_callback(carta_path, carta_idx_global))
                
            except Exception as e:
                print(f"Erro ao carregar carta: {e}")
                carta_lbl = tk.Label(self.matriz_frame, text="?", bg="black", fg="white")
                carta_lbl.grid(row=row, column=col, padx=8, pady=8)
        
        # Atualizar setas de navegação
        # Primeiro, remover setas existentes
        for widget in self.winfo_children():
            if isinstance(widget, tk.Button) and widget.cget("text") in ["▲", "▼"]:
                widget.destroy()
        
        # Recriar setas se necessário (iguais à página de venda)
        if hasattr(self, '_total_pages') and self._total_pages > 1:
            seta_x = 0.90  # Posição igual à página de venda
            if self._current_buy_page > 0:
                seta_cima = tk.Button(self, text="▲", font=("Helvetica", 18, "bold"), bg="#222", fg="white", width=2,
                                    command=self._prev_buy_page)
                seta_cima.place(relx=seta_x, rely=0.38, anchor="center")
            if self._current_buy_page < self._total_pages - 1:
                seta_baixo = tk.Button(self, text="▼", font=("Helvetica", 18, "bold"), bg="#222", fg="white", width=2,
                                     command=self._next_buy_page)
                seta_baixo.place(relx=seta_x, rely=0.62, anchor="center")

    def _abrir_fullscreen_carta(self, carta_idx):
        """Abre carta em fullscreen para compra, igual ao estilo da página de venda"""
        print(f"DEBUG: _abrir_fullscreen_carta chamado - carta_idx: {carta_idx}")
        
        if not hasattr(self, '_cartas_disponiveis') or carta_idx >= len(self._cartas_disponiveis):
            print(f"DEBUG: Índice de carta inválido: {carta_idx}")
            return
            
        carta_path = self._cartas_disponiveis[carta_idx]
        
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
            print(f"DEBUG: ERRO ao carregar carta para compra: {e}")
            # Mostrar um placeholder em caso de erro
            carta_real_lbl = tk.Label(self, text="Erro ao carregar carta", font=("Helvetica", 20), fg="red", bg="black")
            carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center")
        
        # Botão X para voltar à página de compra (movido para canto superior esquerdo)
        def fechar():
            print("DEBUG: Botão X pressionado - voltando à página de compra")
            try:
                # Volta à página de compra
                self.show_buy_page()
            except Exception as e:
                print(f"DEBUG: Erro ao fechar compra: {e}")
                # Em caso de erro, tenta voltar à Store
                self.voltar_para_store()
                
        x_btn = tk.Button(self, text="✖", font=("Helvetica", 24, "bold"), bg="#AAAAAA", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=fechar, cursor="hand2", activebackground="#CCCCCC")
        x_btn.place(relx=0.02, rely=0, anchor="nw")  # Canto superior esquerdo
        
        # Botão checkmark (✓) para comprar no canto superior direito (só mostra se não for casa de outro jogador)
        if not self.other_player_house:
            def comprar():
                # Definir a carta selecionada e chamar confirmação de compra
                self._selected_card_idx = carta_idx
                self._comprar_carta()
            btn_comprar = tk.Button(self, text="✓", font=("Helvetica", 24, "bold"), bg="#4CAF50", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=comprar, cursor="hand2", activebackground="#43A047")
            btn_comprar.place(relx=0.98, rely=0, anchor="ne")  # Canto superior direito
        else:
            print("DEBUG: Casa de outro jogador - botão de compra ocultado")
        
        # Força update final
        self.update_idletasks()
        self.update()

    def _extrair_valor_carta(self, carta_path):
        """
        Extrai o valor de compra da carta usando a base de dados integrada
        """
        print(f"DEBUG: [_extrair_valor_carta] Iniciando extração para: {carta_path}")
        
        if not self.card_database:
            print(f"DEBUG: [_extrair_valor_carta] Base de dados não inicializada, usando fallback")
            # Fallback para extração do nome do arquivo se não houver base de dados
            import re
            nome = os.path.basename(carta_path)
            match = re.search(r'_(\d+)\.', nome)
            if match:
                valor = int(match.group(1))
                print(f"DEBUG: [_extrair_valor_carta] Valor extraído do nome (fallback): {valor}")
                return valor
            print(f"DEBUG: [_extrair_valor_carta] Fallback falhou - retornando None")
            return None
        
        try:
            # Extrair informações do caminho do arquivo
            nome_arquivo = os.path.basename(carta_path)
            print(f"DEBUG: [_extrair_valor_carta] Nome do arquivo: {nome_arquivo}")
            
            tipo_carta = self._get_card_type_from_path(carta_path)
            print(f"DEBUG: [_extrair_valor_carta] Tipo da carta detectado: {tipo_carta}")
            
            if not tipo_carta:
                print(f"DEBUG: [_extrair_valor_carta] ERRO: Não foi possível determinar o tipo da carta: {carta_path}")
                return None
            
            # Mapear arquivo para ID da carta na base de dados
            card_id = self._map_file_to_card_id(carta_path, tipo_carta)
            print(f"DEBUG: [_extrair_valor_carta] Card ID mapeado: {card_id}")
            
            if not card_id:
                print(f"DEBUG: [_extrair_valor_carta] ERRO: Não foi possível mapear arquivo para ID: {carta_path}")
                return None
            
            # Obter valor da base de dados
            if tipo_carta == "users":
                card = self.card_database.get_user(card_id)
                print(f"DEBUG: [_extrair_valor_carta] Carta User encontrada: {card is not None}")
                if card:
                    print(f"DEBUG: [_extrair_valor_carta] User card details: {card}")
                valor = card.buy_cost if card else None
                print(f"DEBUG: [_extrair_valor_carta] User card {card_id}: valor = {valor}")
                return valor
            elif tipo_carta == "equipments":
                card = self.card_database.get_equipment(card_id)
                print(f"DEBUG: [_extrair_valor_carta] Carta Equipment encontrada: {card is not None}")
                if card:
                    print(f"DEBUG: [_extrair_valor_carta] Equipment card details: {card}")
                valor = card.buy_cost if card else None
                print(f"DEBUG: [_extrair_valor_carta] Equipment card {card_id}: valor = {valor}")
                return valor
            elif tipo_carta == "services":
                card = self.card_database.get_service(card_id)
                print(f"DEBUG: [_extrair_valor_carta] Carta Service encontrada: {card is not None}")
                if card:
                    print(f"DEBUG: [_extrair_valor_carta] Service card details: {card}")
                valor = card.buy_cost if card else None
                print(f"DEBUG: [_extrair_valor_carta] Service card {card_id}: valor = {valor}")
                return valor
            elif tipo_carta == "activities":
                card = self.card_database.get_activity(card_id)
                print(f"DEBUG: [_extrair_valor_carta] Carta Activity encontrada: {card is not None}")
                if card:
                    print(f"DEBUG: [_extrair_valor_carta] Activity card details: {card}")
                valor = card.application_fee if card else None  # Activities usam application_fee como preço de compra
                print(f"DEBUG: [_extrair_valor_carta] Activity card {card_id}: valor = {valor}")
                return valor
            
            print(f"DEBUG: [_extrair_valor_carta] ERRO: Tipo de carta não suportado: {tipo_carta}")
            return None
            
        except Exception as e:
            print(f"DEBUG: [_extrair_valor_carta] EXCEÇÃO ao extrair valor da carta {carta_path}: {e}")
            import traceback
            traceback.print_exc()
            # Fallback para extração do nome do arquivo
            import re
            nome = os.path.basename(carta_path)
            match = re.search(r'_(\d+)\.', nome)
            if match:
                valor = int(match.group(1))
                print(f"DEBUG: [_extrair_valor_carta] Valor extraído do nome (fallback após erro): {valor}")
                return valor
            print(f"DEBUG: [_extrair_valor_carta] Fallback após erro falhou - retornando None")
            return None
    
    def _get_card_type_from_path(self, carta_path):
        """
        Determina o tipo da carta baseado no caminho do arquivo
        """
        path_lower = carta_path.lower()
        print(f"DEBUG: [_get_card_type_from_path] Analisando caminho: {path_lower}")
        
        # Verificar padrões de diretório com /tipo/
        if "/users/" in path_lower:
            print(f"DEBUG: [_get_card_type_from_path] Tipo detectado (padrão /users/): users")
            return "users"
        elif "/equipments/" in path_lower:
            print(f"DEBUG: [_get_card_type_from_path] Tipo detectado (padrão /equipments/): equipments")
            return "equipments"
        elif "/services/" in path_lower:
            print(f"DEBUG: [_get_card_type_from_path] Tipo detectado (padrão /services/): services")
            return "services"
        elif "/activities/" in path_lower:
            print(f"DEBUG: [_get_card_type_from_path] Tipo detectado (padrão /activities/): activities")
            return "activities"
        
        # Verificar padrões de nome de diretório Residential-tipo-
        if "residential-users-" in path_lower or "-users-" in path_lower:
            print(f"DEBUG: [_get_card_type_from_path] Tipo detectado (padrão Residential-users-): users")
            return "users"
        elif "residential-equipments-" in path_lower or "-equipments-" in path_lower:
            print(f"DEBUG: [_get_card_type_from_path] Tipo detectado (padrão Residential-equipments-): equipments")
            return "equipments"
        elif "residential-services-" in path_lower or "-services-" in path_lower:
            print(f"DEBUG: [_get_card_type_from_path] Tipo detectado (padrão Residential-services-): services")
            return "services"
        elif "residential-activities-" in path_lower or "-activities-" in path_lower:
            print(f"DEBUG: [_get_card_type_from_path] Tipo detectado (padrão Residential-activities-): activities")
            return "activities"
        
        print(f"DEBUG: [_get_card_type_from_path] ERRO: Tipo não reconhecido no caminho")
        return None
    
    def _map_file_to_card_id(self, carta_path, tipo_carta):
        """
        Mapeia um arquivo de carta para o ID correspondente na base de dados
        """
        import re
        nome_arquivo = os.path.basename(carta_path)
        print(f"DEBUG: [_map_file_to_card_id] Mapeando {nome_arquivo} do tipo {tipo_carta}")
        
        # Extrair número da carta (ex: User_1.png -> 1)
        match = re.search(r'_(\d+)\.', nome_arquivo)
        if not match:
            print(f"DEBUG: [_map_file_to_card_id] ERRO: Não foi possível extrair número de {nome_arquivo}")
            return None
        
        numero = int(match.group(1))
        print(f"DEBUG: [_map_file_to_card_id] Número extraído: {numero}")
        
        # Extrair cor do caminho
        cor = self._get_color_from_path(carta_path)
        print(f"DEBUG: [_map_file_to_card_id] Cor extraída: {cor}")
        if not cor:
            print(f"DEBUG: [_map_file_to_card_id] ERRO: Não foi possível extrair cor de {carta_path}")
            return None
        
        # Mapear para ID da base de dados baseado no tipo (usando mesma lógica do card_integration.py)
        if tipo_carta == "users":
            card_id = f"{numero}_{cor}"
            print(f"DEBUG: [_map_file_to_card_id] User ID gerado: {card_id}")
            return card_id
        elif tipo_carta == "equipments":
            # Equipments têm mapeamento específico baseado no número
            if numero >= 1 and numero <= 3:
                card_id = f"small_router_{numero}_{cor}"
            elif numero >= 4 and numero <= 6:
                card_id = f"medium_router_{numero-3}_{cor}"
            elif numero >= 7 and numero <= 9:
                card_id = f"short_link_{numero-6}_{cor}"
            elif numero >= 10 and numero <= 12:
                card_id = f"long_link_{numero-9}_{cor}"
            else:
                print(f"DEBUG: [_map_file_to_card_id] ERRO: Equipment número {numero} fora do range")
                return None
            print(f"DEBUG: [_map_file_to_card_id] Equipment ID gerado: {card_id}")
            return card_id
        elif tipo_carta == "services":
            # Services têm mapeamento específico conforme card_integration.py
            service_mapping = {
                1: "service_bandwidth_1", 2: "service_data_volume_2", 
                3: "service_data_volume_3", 4: "service_data_volume_4",
                5: "service_temporary_5", 6: "service_temporary_6", 
                7: "service_temporary_7"
            }
            if numero in service_mapping:
                service_type = service_mapping[numero]
                card_id = f"{service_type}_{cor}"
                print(f"DEBUG: [_map_file_to_card_id] Service ID gerado: {card_id}")
                return card_id
            else:
                print(f"DEBUG: [_map_file_to_card_id] ERRO: Service número {numero} não encontrado no mapeamento")
                return None
        elif tipo_carta == "activities":
            card_id = f"activity_{numero}_{cor}"
            print(f"DEBUG: [_map_file_to_card_id] Activity ID gerado: {card_id}")
            return card_id
        
        print(f"DEBUG: [_map_file_to_card_id] ERRO: Tipo não reconhecido: {tipo_carta}")
        return None
    
    def _get_color_from_path(self, carta_path):
        """
        Extrai a cor do caminho do arquivo
        """
        path_lower = carta_path.lower()
        print(f"DEBUG: [_get_color_from_path] Analisando caminho: {path_lower}")
        
        # Verificar padrões de diretório com /cor/
        if "/red/" in path_lower:
            print(f"DEBUG: [_get_color_from_path] Cor detectada (padrão /red/): red")
            return "red"
        elif "/blue/" in path_lower:
            print(f"DEBUG: [_get_color_from_path] Cor detectada (padrão /blue/): blue")
            return "blue"
        elif "/green/" in path_lower:
            print(f"DEBUG: [_get_color_from_path] Cor detectada (padrão /green/): green")
            return "green"
        elif "/yellow/" in path_lower:
            print(f"DEBUG: [_get_color_from_path] Cor detectada (padrão /yellow/): yellow")
            return "yellow"
        
        # Verificar padrões de sufixo -cor
        if "-red" in path_lower or "red" in path_lower:
            print(f"DEBUG: [_get_color_from_path] Cor detectada (padrão -red): red")
            return "red"
        elif "-blue" in path_lower or "blue" in path_lower:
            print(f"DEBUG: [_get_color_from_path] Cor detectada (padrão -blue): blue")
            return "blue"
        elif "-green" in path_lower or "green" in path_lower:
            print(f"DEBUG: [_get_color_from_path] Cor detectada (padrão -green): green")
            return "green"
        elif "-yellow" in path_lower or "yellow" in path_lower:
            print(f"DEBUG: [_get_color_from_path] Cor detectada (padrão -yellow): yellow")
            return "yellow"
        
        print(f"DEBUG: [_get_color_from_path] ERRO: Nenhuma cor encontrada no caminho")
        return None

    def _comprar_carta(self):
        # Se houver carta selecionada, mostra página de confirmação
        if self._selected_card_idx is None or self._selected_card_idx >= len(self._cartas_disponiveis):
            from tkinter import messagebox
            messagebox.showwarning("Nenhuma carta selecionada", "Por favor seleciona uma carta primeiro!")
            return
            
        carta_path = self._cartas_disponiveis[self._selected_card_idx]
        valor = self._extrair_valor_carta(carta_path)
        # Esconde todos os widgets exceto barra superior
        for widget in self.winfo_children():
            if isinstance(widget, tk.Label) and hasattr(widget, 'image') and widget.winfo_y() == 0:
                continue  # Mantém a barra superior
            widget.destroy()
        self.configure(bg="black")
        # Frase de confirmação
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
                
                # IMPORTANTE: Remover a carta comprada dos baralhos (local e global)
                print(f"DEBUG: Removendo carta comprada dos baralhos - carta: {os.path.basename(carta_path)}")
                carta_removida = False
                
                # Determinar cor e tipo para remoção
                cor_para_remover = self.player_color
                tipo_para_remover = self.current_card_type
                
                # Tentar remover do baralho da cor do jogador primeiro
                if (hasattr(self, 'cartas') and cor_para_remover in self.cartas and 
                    tipo_para_remover in self.cartas[cor_para_remover] and 
                    carta_path in self.cartas[cor_para_remover][tipo_para_remover]):
                    self.cartas[cor_para_remover][tipo_para_remover].remove(carta_path)
                    print(f"DEBUG: Carta removida do baralho local {cor_para_remover}/{tipo_para_remover}")
                    carta_removida = True
                
                # Se não foi removida da cor do jogador, tentar neutral
                if not carta_removida and (hasattr(self, 'cartas') and "neutral" in self.cartas and 
                                         tipo_para_remover in self.cartas["neutral"] and 
                                         carta_path in self.cartas["neutral"][tipo_para_remover]):
                    self.cartas["neutral"][tipo_para_remover].remove(carta_path)
                    print(f"DEBUG: Carta removida do baralho local neutral/{tipo_para_remover}")
                    carta_removida = True
                
                # Remover também do baralho global
                global baralhos
                if baralhos:
                    # Tentar remover da cor do jogador
                    if (cor_para_remover in baralhos and tipo_para_remover in baralhos[cor_para_remover] and 
                        carta_path in baralhos[cor_para_remover][tipo_para_remover]):
                        baralhos[cor_para_remover][tipo_para_remover].remove(carta_path)
                        print(f"DEBUG: Carta removida do baralho global {cor_para_remover}/{tipo_para_remover}")
                    # Tentar remover do neutral
                    elif ("neutral" in baralhos and tipo_para_remover in baralhos["neutral"] and 
                          carta_path in baralhos["neutral"][tipo_para_remover]):
                        baralhos["neutral"][tipo_para_remover].remove(carta_path)
                        print(f"DEBUG: Carta removida do baralho global neutral/{tipo_para_remover}")
                
                if carta_removida:
                    print(f"DEBUG: Sincronização completa - carta {os.path.basename(carta_path)} removida dos baralhos")
                else:
                    print(f"DEBUG: AVISO - carta {os.path.basename(carta_path)} não foi encontrada nos baralhos para remoção")
                
                # Garantir tipo correto para inventário
                tipo_inv = self.current_card_type
                if tipo_inv == "equipment":
                    tipo_inv = "equipments"
                elif tipo_inv == "actions":
                    tipo_inv = "actions"  # PlayerDashboard usa "actions" (plural)
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
        btn_no = tk.Button(btns_frame, text="No", font=("Helvetica", 14, "bold"), bg="#F44336", fg="white", width=8, command=cancelar)
        btn_yes = tk.Button(btns_frame, text="Yes", font=("Helvetica", 14, "bold"), bg="#4CAF50", fg="white", width=8, command=confirmar)
        btn_no.pack(side="left", padx=20, pady=10)
        btn_yes.pack(side="left", padx=20, pady=10)

    def voltar_para_store(self):
        print("DEBUG: voltar_para_store chamado")
        print(f"DEBUG: [voltar_para_store] ID do objeto Store: {id(self)}")
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
            print("DEBUG: Estado limpo, verificando carta pendente...")
            
            # USAR A NOVA FUNÇÃO ESPECÍFICA
            if self.restaurar_carta_fullscreen_pendente():
                print("DEBUG: Carta em fullscreen restaurada com sucesso")
            else:
                print("DEBUG: Nenhuma carta pendente - reconstruindo interface normal")
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
                    # CORREÇÃO: Usar função do PlayerDashboard em vez do Store
                    if self.dashboard and hasattr(self.dashboard, 'show_sell_confirmation'):
                        self.dashboard.show_sell_confirmation(carta_path, carta_tipo, self)
                    else:
                        print("DEBUG: ERRO - PlayerDashboard não encontrado ou não tem show_sell_confirmation")
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
                              bg="#8C04A0", fg="white", width=6, 
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
                    # CORREÇÃO: Usar função do PlayerDashboard em vez do Store
                    if self.dashboard and hasattr(self.dashboard, 'show_sell_confirmation'):
                        self.dashboard.show_sell_confirmation(carta_path, carta_tipo, self)
                    else:
                        print("DEBUG: ERRO - PlayerDashboard não encontrado ou não tem show_sell_confirmation")
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
                              bg="#8C04A0", fg="white", width=6, 
                              command=self.voltar_para_store)
        btn_voltar.place(relx=0.5, rely=0.98, anchor="s")  # Posição igual ao PlayerDashboard
        
        print("DEBUG: show_sell_inventory_paginated concluído")

    def skip_action(self):
        """Ação do botão Skip - sai da loja"""
        
        print("DEBUG: skip_action chamado") # Esconde os botões de ação
        
        # Se houver um dashboard, mostra o PlayerDashboard primeiro
        if self.dashboard:
            try:
                # Mostrar o PlayerDashboard
                self.dashboard.deiconify()
                self.dashboard.state('normal')
                self.dashboard.lift()
                self.dashboard.focus_force()
                print("DEBUG: PlayerDashboard mostrado no skip")
                
                # Chamar a interface principal do PlayerDashboard
                self.dashboard.playerdashboard_interface(
                    self.dashboard.player_name,
                    self.dashboard.saldo,  # Usar o saldo atualizado do PlayerDashboard (já foi decrementado)
                    self.dashboard.other_players
                )
                print("DEBUG: Interface principal do PlayerDashboard aberta com sucesso no skip")
            except Exception as e:
                print(f"DEBUG: Erro ao mostrar PlayerDashboard no skip: {e}")
        
        # Fecha a Store depois
        self.destroy()

    def tirar_carta(self, casa_tipo, casa_cor):
        print(f"DEBUG: tirar_carta chamado com casa_tipo={casa_tipo!r}, casa_cor={casa_cor!r}")
        
        # Normalizar o tipo para consistent naming
        if casa_tipo == "equipment":
            casa_tipo = "equipments"
        
        # NOVO: Caso específico para Challenges - usar função dedicada
        if casa_tipo in ["challenges", "challenge"]:
            print("DEBUG: Casa tipo 'challenges' detectada - usando função específica")
            self.processar_casa_challenges(casa_cor)
            return
        
        # Se for casa de outro jogador, vai para a página de compra (NÃO tira carta diretamente)
        if self.other_player_house and casa_tipo in ["equipments", "services", "users", "activities"]:
            print(f"DEBUG: Casa de outro jogador - indo para página de compra de {casa_tipo}")
            # Armazenar o tipo de carta atual para mostrar a página de compra
            self.current_card_type = casa_tipo
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
        elif casa_tipo in ["actions", "action", "events"]:
            # Para actions e events, usa o método original
            self.mostrar_carta(casa_cor, casa_tipo)
        else:
            # Para outros tipos, não faz nada
            print(f"DEBUG: Tipo {casa_tipo} não reconhecido - nenhuma ação executada")
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
        
        # Guardar estado da carta fullscreen para poder restaurar depois
        self.fullscreen_carta_path = carta_path
        self.fullscreen_carta_tipo = casa_tipo
        print(f"DEBUG: Guardando estado fullscreen - carta: {carta_path}, tipo: {casa_tipo}")
        
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

        # Adicionar botão X cinza no canto superior direito
        def fechar():
            print("DEBUG: Botão X pressionado - verificando tipo de carta")
            # Limpar estado de fullscreen porque a carta foi aceita
            self.fullscreen_carta_path = None
            self.fullscreen_carta_tipo = None
            print("DEBUG: Estado de fullscreen limpo ao aceitar carta")
            
            # Guarda a carta no inventário do dashboard, se aplicável
            tipo_inv = casa_tipo.lower()
            if tipo_inv == "equipment":
                tipo_inv = "equipments"
            elif tipo_inv == "action":
                tipo_inv = "actions"
            elif tipo_inv == "event":
                tipo_inv = "events"
            elif tipo_inv == "challenge":
                tipo_inv = "challenges"
            print(f"DEBUG: Mapping card type '{casa_tipo}' to inventory key '{tipo_inv}'")
            if self.dashboard and hasattr(self.dashboard, 'adicionar_carta_inventario'):
                self.dashboard.adicionar_carta_inventario(carta_path, tipo_inv)
                print(f"DEBUG: Carta {carta_path} adicionada ao inventário {tipo_inv}")
                
                # IMPORTANTE: Remover carta do baralho local da Store para sincronização
                self._remover_carta_do_baralho_local(carta_path, tipo_inv)
            
            # Para Actions e Events, vai para PlayerDashboard SEM botão Store
            if casa_tipo in ["actions", "action", "events", "event"]:
                print("DEBUG: Carta de Actions/Events - indo para PlayerDashboard SEM botão Store")
                try:
                    if self.dashboard and hasattr(self.dashboard, "playerdashboard_interface"):
                        # IMPORTANTE: Desativar permanentemente o botão Store
                        if hasattr(self.dashboard, 'disable_store_button'):
                            self.dashboard.disable_store_button()
                            print("DEBUG: Botão Store desativado permanentemente")
                        
                        # Esconder a Store primeiro
                        self.withdraw()
                        print("DEBUG: Store escondida ao aceitar carta Actions/Events")
                        
                        # Mostrar o PlayerDashboard
                        self.dashboard.deiconify()
                        self.dashboard.state('normal')
                        self.dashboard.lift()
                        self.dashboard.focus_force()
                        print("DEBUG: PlayerDashboard mostrado ao aceitar carta Actions/Events")
                        
                        # Chamar a interface principal do PlayerDashboard SEM botão Store
                        self.dashboard.playerdashboard_interface(
                            self.dashboard.player_name,
                            self.dashboard.saldo,
                            self.dashboard.other_players,
                            show_store_button=False
                        )
                        print("DEBUG: Interface principal do PlayerDashboard aberta SEM botão Store")
                except Exception as e:
                    print(f"DEBUG: Erro ao voltar ao PlayerDashboard após aceitar carta Actions/Events: {e}")
            else:
                # Para outros tipos, volta à Store
                print("DEBUG: Outro tipo de carta - voltando à Store")
                self.voltar_para_store()
        
        # Botão diferente dependendo do tipo de carta (igual ao mostrar_carta_fullscreen_simples)
        if casa_tipo in ["actions", "action", "events", "event"]:
            # Botão ✓ verde para Actions e Events - abre overlay de seleção de jogador
            def abrir_overlay_jogador():
                print(f"DEBUG: *** abrir_overlay_jogador CHAMADO em mostrar_carta_fullscreen ***")
                print(f"DEBUG: Sobre a carta: {carta_path}")
                print(f"DEBUG: Tipo da carta: {casa_tipo}")
                self.mostrar_overlay_selecao_jogador(carta_path, casa_tipo)
            
            certo_btn = tk.Button(self, text="✓", font=("Helvetica", 24, "bold"), bg="#4CAF50", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=abrir_overlay_jogador, cursor="hand2", activebackground="#43d17a")
        else:
            # Botão ✔ verde para outros tipos - funcionalidade normal
            certo_btn = tk.Button(self, text="✔", font=("Helvetica", 24, "bold"), bg="#4CAF50", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=fechar, cursor="hand2", activebackground="#43d17a")
        
        certo_btn.place(relx=0.98, rely=0, anchor="ne")

    def mostrar_carta_fullscreen_simples(self, carta_path, casa_tipo):
        """Mostra uma carta em fullscreen para casas de outro jogador - apenas visualização, sem compra/venda"""
        print(f"DEBUG: Store.mostrar_carta_fullscreen_simples chamado com carta_path={carta_path}, casa_tipo={casa_tipo}")
        
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
            
            print("DEBUG: Carta mostrada em fullscreen simples com sucesso")
        except Exception as e:
            print(f"DEBUG: ERRO ao carregar carta em fullscreen simples: {e}")
            # Mostrar mensagem de erro e voltar
            error_frame = tk.Frame(self, bg="black")
            error_frame.pack(expand=True)
            tk.Label(error_frame, text="Erro ao carregar carta!", font=("Helvetica", 16), bg="black", fg="red").pack(pady=20)
            tk.Button(error_frame, text="Back", font=("Helvetica", 14, "bold"), bg="#005c75", fg="white", command=self.voltar_para_store).pack(pady=10)
            return

        # Botão X para voltar à Store (único botão disponível)
        def fechar():
            print("DEBUG: Botão X pressionado - voltando à Store")
            self.voltar_para_store()
                
        x_btn = tk.Button(self, text="✖", font=("Helvetica", 24, "bold"), bg="#AAAAAA", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=fechar, cursor="hand2", activebackground="#CCCCCC")
        x_btn.place(relx=1, rely=0, anchor="ne")  # Canto superior direito
        
        print("DEBUG: Carta de outro jogador - apenas visualização, sem botões de compra/venda")

        # Botão no canto superior direito - X cinza para challenges, ✓ verde para actions/events
        def fechar():
            # Limpar estado de fullscreen porque a carta foi aceita
            self.fullscreen_carta_path = None
            self.fullscreen_carta_tipo = None
            print("DEBUG: Estado de fullscreen limpo ao aceitar carta")
            
            carta_real_lbl.destroy()
            btn_fechar.destroy()
            # Guarda a carta no inventário do dashboard, se aplicável
            tipo_inv = casa_tipo
            if tipo_inv == "equipment":
                tipo_inv = "equipments"
            elif tipo_inv == "actions":
                tipo_inv = "actions"  # PlayerDashboard usa "actions" (plural)
            print(f"DEBUG: Mapping card type '{casa_tipo}' to inventory key '{tipo_inv}'")
            if self.dashboard and hasattr(self.dashboard, 'adicionar_carta_inventario'):
                self.dashboard.adicionar_carta_inventario(carta_path, tipo_inv)
                print(f"DEBUG: Card added to inventory: {tipo_inv} -> {carta_path}")
                
                # IMPORTANTE: Remover carta do baralho local da Store para sincronização
                self._remover_carta_do_baralho_local(carta_path, tipo_inv)
            
            # Para Actions e Events de casas neutras, volta ao PlayerDashboard
            # Para Actions e Events de casas próprias, volta à página principal da Store
            if casa_tipo in ["actions", "action", "events", "event"]:
                if self.casa_cor == "neutral":
                    print("DEBUG: Carta de Actions/Events de casa neutra aceita - voltando ao PlayerDashboard")
                    try:
                        if self.dashboard and hasattr(self.dashboard, "playerdashboard_interface"):
                            # Esconder a Store primeiro
                            self.withdraw()
                            print("DEBUG: Store escondida ao aceitar carta neutra")
                            
                            # Mostrar o PlayerDashboard
                            self.dashboard.deiconify()
                            self.dashboard.state('normal')
                            self.dashboard.lift()
                            self.dashboard.focus_force()
                            print("DEBUG: PlayerDashboard mostrado ao aceitar carta neutra")
                            
                            # Chamar a interface principal do PlayerDashboard SEM botão Store
                            self.dashboard.playerdashboard_interface(
                                self.dashboard.player_name,
                                self.dashboard.saldo,
                                self.dashboard.other_players,
                                show_store_button=False
                            )
                            print("DEBUG: Interface principal do PlayerDashboard aberta SEM botão Store ao aceitar carta neutra")
                    except Exception as e:
                        print(f"DEBUG: Erro ao voltar ao PlayerDashboard após aceitar carta neutra: {e}")
                else:
                    print("DEBUG: Carta de Actions/Events de casa própria aceita - voltando ao PlayerDashboard SEM botão Store")
                    try:
                        if self.dashboard and hasattr(self.dashboard, "playerdashboard_interface"):
                            # Esconder a Store primeiro
                            self.withdraw()
                            print("DEBUG: Store escondida ao aceitar carta própria")
                            
                            # Mostrar o PlayerDashboard
                            self.dashboard.deiconify()
                            self.dashboard.state('normal')
                            self.dashboard.lift()
                            self.dashboard.focus_force()
                            print("DEBUG: PlayerDashboard mostrado ao aceitar carta própria")
                            
                            # Chamar a interface principal do PlayerDashboard SEM botão Store
                            self.dashboard.playerdashboard_interface(
                                self.dashboard.player_name,
                                self.dashboard.saldo,
                                self.dashboard.other_players,
                                show_store_button=False
                            )
                            print("DEBUG: Interface principal do PlayerDashboard aberta SEM botão Store ao aceitar carta própria")
                    except Exception as e:
                        print(f"DEBUG: Erro ao voltar ao PlayerDashboard após aceitar carta própria: {e}")
            else:
                # Para outros tipos (como Challenges), volta ao PlayerDashboard
                try:
                    if self.dashboard and hasattr(self.dashboard, "playerdashboard_interface"):
                        # Esconder a Store primeiro
                        self.withdraw()
                        print("DEBUG: Store escondida ao aceitar carta")
                        
                        # Mostrar o PlayerDashboard
                        self.dashboard.deiconify()
                        self.dashboard.state('normal')
                        self.dashboard.lift()
                        self.dashboard.focus_force()
                        print("DEBUG: PlayerDashboard mostrado ao aceitar carta")
                        
                        # Chamar a interface principal do PlayerDashboard sem mostrar botão Store
                        self.dashboard.playerdashboard_interface(
                            self.dashboard.player_name,
                            self.dashboard.saldo,
                            self.dashboard.other_players,
                            show_store_button=False
                        )
                        print("DEBUG: Interface principal do PlayerDashboard aberta com sucesso ao aceitar carta")
                except Exception as e:
                    print(f"DEBUG: Erro ao voltar ao PlayerDashboard após aceitar carta: {e}")
        
        # Botão diferente dependendo do tipo de carta
        if casa_tipo in ["actions", "action", "events", "event"]:
            # Botão ✓ verde para Actions e Events - abre overlay de seleção de jogador
            def abrir_overlay_jogador():
                print(f"DEBUG: *** abrir_overlay_jogador CHAMADO ***")
                print(f"DEBUG: Sobre a carta: {carta_path}")
                print(f"DEBUG: Tipo da carta: {casa_tipo}")
                self.mostrar_overlay_selecao_jogador(carta_path, casa_tipo)
            
            btn_fechar = tk.Button(self, text="✓", font=("Helvetica", 24, "bold"), bg="#4CAF50", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=abrir_overlay_jogador, cursor="hand2", activebackground="#43d17a")
        else:
            # Botão ✖ cinza para outros tipos (como Challenges)
            btn_fechar = tk.Button(self, text="✖", font=("Helvetica", 24, "bold"), bg="#AAAAAA", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=fechar, cursor="hand2", activebackground="#CCCCCC")
        
        btn_fechar.place(relx=0.98, rely=0, anchor="ne")

        # Se for Challenge, adicionar botão Inventory centrado em cima
        if casa_tipo in ["challenges", "challenge"]:
            def abrir_playerdashboard():
                print("DEBUG: Abrindo interface principal do PlayerDashboard")
                try:
                    # Vai para a interface principal do PlayerDashboard
                    if self.dashboard and hasattr(self.dashboard, "playerdashboard_interface"):
                        # Esconder a Store primeiro
                        self.withdraw()
                        print("DEBUG: Store escondida")
                        
                        # Mostrar o PlayerDashboard
                        self.dashboard.deiconify()
                        self.dashboard.state('normal')
                        self.dashboard.lift()
                        self.dashboard.focus_force()
                        print("DEBUG: PlayerDashboard mostrado")
                        
                        # Chamar a interface principal do PlayerDashboard sem mostrar botão Store
                        self.dashboard.playerdashboard_interface(
                            self.dashboard.player_name,
                            self.dashboard.saldo,
                            self.dashboard.other_players,
                            show_store_button=False
                        )
                        print("DEBUG: Interface principal do PlayerDashboard aberta com sucesso")
                    else:
                        print("DEBUG: ERRO - PlayerDashboard não disponível")
                except Exception as e:
                    print(f"DEBUG: Erro ao abrir PlayerDashboard: {e}")
            
            # Carregamento do ícone do jogador
            try:
                user_icon_path = os.path.join(IMG_DIR, f"{self.player_color}_user_icon.png")
                user_icon_img = ImageTk.PhotoImage(Image.open(user_icon_path).resize((30, 30)))
                btn_inventory = tk.Button(self, image=user_icon_img, bg="#DC8392", relief="flat", borderwidth=0, command=abrir_playerdashboard, cursor="hand2")
                btn_inventory.image = user_icon_img  # Manter referência para evitar garbage collection
            except Exception as e:
                print(f"DEBUG: Erro ao carregar ícone do jogador {self.player_color}_user_icon.png: {e}")
                # Fallback para texto se não conseguir carregar a imagem
                btn_inventory = tk.Button(self, text="Player", font=("Helvetica", 16, "bold"), bg="#8A2BE2", fg="white", relief="flat", borderwidth=0, command=abrir_playerdashboard)
            
            btn_inventory.place(relx=0.5, rely=0, anchor="n")

    def mostrar_overlay_selecao_jogador(self, carta_path, casa_tipo):
        """
        Mostra overlay para seleção de jogador para cartas Actions/Events
        """
        print(f"DEBUG: *** mostrar_overlay_selecao_jogador INICIADO ***")
        print(f"DEBUG: mostrar_overlay_selecao_jogador chamado - carta: {os.path.basename(carta_path)}, tipo: {casa_tipo}")
        print(f"DEBUG: Caminho completo da carta: {carta_path}")
        print(f"DEBUG: Base de dados disponível: {self.card_database is not None}")
        
        # Primeiro, vamos determinar se a carta tem alvo específico ou permite escolha
        # Usando a base de dados para obter informações da carta
        if not self.card_database:
            print("DEBUG: Base de dados não disponível - procedendo com overlay de escolha")
            self._criar_overlay_escolha_jogador(carta_path, casa_tipo)
            return
        
        try:
            # Mapear arquivo para ID da base de dados
            if casa_tipo in ["actions", "action"]:
                card_id = self._map_action_file_to_id(carta_path)
                print(f"DEBUG: Action card_id mapeado: {card_id}")
                if card_id:
                    action_card = self.card_database.get_action(card_id)
                    print(f"DEBUG: Action card obtido da base de dados: {action_card}")
                    if action_card:
                        print(f"DEBUG: Carta Action encontrada - target: {action_card.target}")
                        if action_card.target is None:
                            # Target None = jogadores cinzentos = afeta o próprio jogador
                            print("DEBUG: Carta afeta o próprio jogador - mostrando overlay com ícone próprio")
                            self._criar_overlay_jogador_especifico(carta_path, casa_tipo, self.player_color)
                        else:
                            # Target específico = jogador específico
                            print(f"DEBUG: Carta afeta jogador específico: {action_card.target} - mostrando overlay com ícone específico")
                            self._criar_overlay_jogador_especifico(carta_path, casa_tipo, action_card.target)
                        return
                    else:
                        print(f"DEBUG: Action card {card_id} não encontrado na base de dados")
                else:
                    print(f"DEBUG: Não foi possível mapear arquivo Action para ID: {carta_path}")
            elif casa_tipo in ["events", "event"]:
                card_id = self._map_event_file_to_id(carta_path)
                print(f"DEBUG: Event card_id mapeado: {card_id}")
                if card_id:
                    event_card = self.card_database.get_event(card_id)
                    print(f"DEBUG: Event card obtido da base de dados: {event_card}")
                    if event_card:
                        print(f"DEBUG: Carta Event encontrada - target: {event_card.target_player}, choice: {event_card.player_choice}")
                        if event_card.player_choice:
                            # Player choice = true = jogador pode escolher
                            print("DEBUG: Jogador pode escolher o alvo - mostrando overlay de escolha")
                            self._criar_overlay_escolha_jogador(carta_path, casa_tipo)
                        elif event_card.target_player is None:
                            # Target None = jogadores cinzentos = afeta o próprio jogador
                            print("DEBUG: Carta afeta o próprio jogador - mostrando overlay com ícone próprio")
                            self._criar_overlay_jogador_especifico(carta_path, casa_tipo, self.player_color)
                        else:
                            # Target específico = jogador específico
                            print(f"DEBUG: Carta afeta jogador específico: {event_card.target_player} - mostrando overlay com ícone específico")
                            self._criar_overlay_jogador_especifico(carta_path, casa_tipo, event_card.target_player)
                        return
                    else:
                        print(f"DEBUG: Event card {card_id} não encontrado na base de dados")
                else:
                    print(f"DEBUG: Não foi possível mapear arquivo Event para ID: {carta_path}")
        except Exception as e:
            print(f"DEBUG: Erro ao processar carta na base de dados: {e}")
            import traceback
            traceback.print_exc()
        
        # Fallback: mostrar overlay de escolha se não conseguir determinar
        print("DEBUG: Fallback - mostrando overlay de escolha")
        self._criar_overlay_escolha_jogador(carta_path, casa_tipo)

    def _map_action_file_to_id(self, carta_path):
        """Mapeia arquivo Action para ID da base de dados"""
        import re
        nome_arquivo = os.path.basename(carta_path)
        match = re.search(r'Action_(\d+)\.', nome_arquivo)
        if match:
            numero = int(match.group(1))
            return f"action_{numero}"
        return None

    def _map_event_file_to_id(self, carta_path):
        """Mapeia arquivo Event para ID da base de dados"""
        import re
        nome_arquivo = os.path.basename(carta_path)
        match = re.search(r'Event_(\d+)\.', nome_arquivo)
        if match:
            numero = int(match.group(1))
            return f"event_{numero}"
        return None

    def _criar_overlay_escolha_jogador(self, carta_path, casa_tipo):
        """
        Cria overlay com ícones dos outros jogadores para escolha
        """
        print("DEBUG: Criando overlay de escolha de jogador")
        
        # Limpar tela completamente
        for widget in self.winfo_children():
            widget.destroy()
        self.configure(bg="black")
        
        # Primeiro, mostrar a carta em fullscreen como fundo
        try:
            pil_img = Image.open(carta_path)
            img_w, img_h = pil_img.size
            # Usa todo o ecrã (sem margem)
            max_w, max_h = self.winfo_screenwidth(), self.winfo_screenheight()
            ratio = min(max_w/img_w, max_h/img_h)
            new_w, new_h = int(img_w*ratio), int(img_h*ratio)
            pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            carta_img = ImageTk.PhotoImage(pil_img)
            carta_bg_label = tk.Label(self, image=carta_img, bg="black")
            carta_bg_label.image = carta_img  # Manter referência
            carta_bg_label.place(relx=0.5, rely=0.5, anchor="center")
            
            print("DEBUG: Carta colocada como fundo do overlay")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar carta como fundo: {e}")
            self.configure(bg="black")
        
        # Aplicar o mesmo formato da página de confirmação de compra
        confirm_frame = tk.Frame(self, bg="black")
        confirm_frame.pack(expand=True)
        
        # Título do overlay (mesmo estilo da confirmação de compra)
        tk.Label(confirm_frame, 
                text="Choose target player:", 
                font=("Helvetica", 16, "bold"), 
                fg="white", bg="black").pack(pady=(40, 20))
        
        # Frame para os ícones dos jogadores (centralizado, mesmo estilo da confirmação)
        players_frame = tk.Frame(confirm_frame, bg="black")
        players_frame.pack(pady=(0, 10))
        
        # Obter lista de outros jogadores (excluindo o jogador atual)
        if hasattr(self, 'dashboard') and hasattr(self.dashboard, 'other_players'):
            outros_jogadores = self.dashboard.other_players.copy()
        else:
            # Fallback para todos os jogadores menos o atual
            todos_jogadores = ["red", "green", "blue", "yellow"]
            outros_jogadores = [p for p in todos_jogadores if p != self.player_color]
        
        print(f"DEBUG: Outros jogadores disponíveis: {outros_jogadores}")
        
        # Criar botões com ícones para cada jogador (em linha horizontal)
        for i, cor_jogador in enumerate(outros_jogadores):
            try:
                # Carregar ícone do jogador
                icon_path = os.path.join(IMG_DIR, f"{cor_jogador}_user_icon.png")
                if os.path.exists(icon_path):
                    icon_img = ImageTk.PhotoImage(Image.open(icon_path).resize((65, 65)))
                    
                    # Criar botão com ícone
                    def criar_callback(cor=cor_jogador):
                        return lambda: self._enviar_carta_para_jogador(carta_path, casa_tipo, cor)
                    
                    # Frame para cada jogador (ícone + nome)
                    player_container = tk.Frame(players_frame, bg="black")
                    player_container.pack(side="left", padx=20)
                    
                    btn_jogador = tk.Button(player_container, 
                                          image=icon_img,
                                          bg="black", 
                                          bd=0, 
                                          activebackground="black", 
                                          highlightthickness=0,
                                          command=criar_callback(),
                                          cursor="hand2")
                    
                    btn_jogador.image = icon_img  # Manter referência
                    btn_jogador.pack()
                    
                    # Label com nome da cor (mesmo estilo da confirmação)
                    cor_label = tk.Label(player_container,
                                        text=cor_jogador.upper(),
                                        font=("Helvetica", 14, "bold"),
                                        fg=self._get_color_hex(cor_jogador),
                                        bg="black")
                    cor_label.pack(pady=(5, 0))
                else:
                    print(f"DEBUG: Ícone não encontrado para {cor_jogador}: {icon_path}")
            except Exception as e:
                print(f"DEBUG: Erro ao criar botão para {cor_jogador}: {e}")
        
        # SEM botão Cancel - removido conforme solicitado

    def _criar_overlay_jogador_especifico(self, carta_path, casa_tipo, jogador_alvo):
        """
        Cria overlay com apenas o ícone do jogador alvo específico
        """
        print(f"DEBUG: _criar_overlay_jogador_especifico chamado - jogador_alvo: {jogador_alvo}")
        print(f"DEBUG: _criar_overlay_jogador_especifico - carta: {carta_path}, tipo: {casa_tipo}")
        
        # Limpar tela completamente
        for widget in self.winfo_children():
            widget.destroy()
        self.configure(bg="black")
        
        # Primeiro, mostrar a carta em fullscreen como fundo
        try:
            pil_img = Image.open(carta_path)
            img_w, img_h = pil_img.size
            # Usa todo o ecrã (sem margem)
            max_w, max_h = self.winfo_screenwidth(), self.winfo_screenheight()
            ratio = min(max_w/img_w, max_h/img_h)
            new_w, new_h = int(img_w*ratio), int(img_h*ratio)
            pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            carta_img = ImageTk.PhotoImage(pil_img)
            carta_bg_label = tk.Label(self, image=carta_img, bg="black")
            carta_bg_label.image = carta_img  # Manter referência
            carta_bg_label.place(relx=0.5, rely=0.5, anchor="center")
            
            print("DEBUG: Carta colocada como fundo do overlay específico")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar carta como fundo: {e}")
            self.configure(bg="black")
        
        
        # Aplicar o mesmo formato da página de confirmação de compra
        confirm_frame = tk.Frame(self, bg="black")
        confirm_frame.pack(expand=True)
        
        # Título do overlay (mesmo estilo da confirmação de compra)
        if jogador_alvo == self.player_color:
            title_text = "        Card affects you:        " 
            
            tk.Label(confirm_frame, 
            text=title_text, 
            font=("Helvetica", 16, "bold"), 
            fg="white", bg="black").pack(pady=(40, 20))
            
        else:
            title_text = "Send card to the following player:" 
            
            tk.Label(confirm_frame, 
            text=title_text, 
            font=("Helvetica", 15, "bold"), 
            fg="white", bg="black").pack(pady=(40, 20))
        
    
        # Frame para o ícone do jogador (centralizado, mesmo estilo da confirmação)
        player_frame = tk.Frame(confirm_frame, bg="black")
        player_frame.pack(pady=(0, 20))
        
        try:
            # Carregar ícone do jogador alvo
            icon_path = os.path.join(IMG_DIR, f"{jogador_alvo}_user_icon.png")
            if os.path.exists(icon_path):
                icon_img = ImageTk.PhotoImage(Image.open(icon_path).resize((65, 65)))
                
                # Criar botão com ícone do jogador alvo
                def confirmar_envio():
                    self._enviar_carta_para_jogador(carta_path, casa_tipo, jogador_alvo)
                
                btn_jogador = tk.Button(player_frame, 
                                      image=icon_img,
                                      bg="black", 
                                      relief="flat", 
                                      borderwidth=0,
                                      highlightthickness=0,
                                      activebackground="black",
                                      command=confirmar_envio,
                                      cursor="hand2")
                btn_jogador.image = icon_img  # Manter referência
                btn_jogador.pack()
                
                # Label com nome da cor (mesmo estilo da confirmação)
                cor_label = tk.Label(player_frame,
                                    text=jogador_alvo.upper(),
                                    font=("Helvetica", 16, "bold"),
                                    fg=self._get_color_hex(jogador_alvo),
                                    bg="black")
                cor_label.pack(pady=(10, 0))
            else:
                print(f"DEBUG: Ícone não encontrado para {jogador_alvo}: {icon_path}")
                # Fallback com texto (mesmo estilo da confirmação)
                btn_text = tk.Button(player_frame,
                                   text=jogador_alvo.upper(),
                                   font=("Helvetica", 20, "bold"),
                                   bg=self._get_color_hex(jogador_alvo),
                                   fg="white",
                                   width=12,
                                   height=3,
                                   command=lambda: self._enviar_carta_para_jogador(carta_path, casa_tipo, jogador_alvo))
                btn_text.pack()
        except Exception as e:
            print(f"DEBUG: Erro ao criar overlay para jogador {jogador_alvo}: {e}")
        
        # SEM botão Cancel - removido conforme solicitado

    def _get_color_hex(self, color):
        """Retorna cor hexadecimal para uma cor de jogador"""
        color_map = {
            "red": "#EE6F68",
            "green": "#70AD47", 
            "blue": "#43BEF2",
            "yellow": "#F2BA0D"
        }
        return color_map.get(color, "#FFFFFF")

    def _enviar_carta_para_jogador(self, carta_path, casa_tipo, jogador_alvo):
        """
        Envia a carta para o jogador alvo e finaliza a ação
        """
        print(f"DEBUG: Enviando carta {os.path.basename(carta_path)} para jogador {jogador_alvo}")
        
        # Aqui você pode implementar a lógica de envio da carta
        # Por enquanto, vamos apenas adicionar ao inventário do jogador atual
        # e mostrar uma mensagem de confirmação
        
        # Adicionar carta ao inventário
        tipo_inv = casa_tipo
        if tipo_inv == "actions":
            tipo_inv = "actions"
        elif tipo_inv == "events":
            tipo_inv = "events"
        
        if self.dashboard and hasattr(self.dashboard, 'adicionar_carta_inventario'):
            self.dashboard.adicionar_carta_inventario(carta_path, tipo_inv)
            print(f"DEBUG: Carta adicionada ao inventário: {tipo_inv} -> {carta_path}")
            
            # Remover carta do baralho local da Store
            self._remover_carta_do_baralho_local(carta_path, tipo_inv)
        
        # Mostrar overlay de confirmação
        self._mostrar_confirmacao_envio(carta_path, casa_tipo, jogador_alvo)

    def _mostrar_confirmacao_envio(self, carta_path, casa_tipo, jogador_alvo):
        """
        Mostra overlay de confirmação de envio da carta
        """
        # Limpar tela completamente
        for widget in self.winfo_children():
            widget.destroy()
        self.configure(bg="black")
        
        # Primeiro, mostrar a carta em fullscreen como fundo
        try:
            pil_img = Image.open(carta_path)
            img_w, img_h = pil_img.size
            # Usa todo o ecrã (sem margem)
            max_w, max_h = self.winfo_screenwidth(), self.winfo_screenheight()
            ratio = min(max_w/img_w, max_h/img_h)
            new_w, new_h = int(img_w*ratio), int(img_h*ratio)
            pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            carta_img = ImageTk.PhotoImage(pil_img)
            carta_bg_label = tk.Label(self, image=carta_img, bg="black")
            carta_bg_label.image = carta_img  # Manter referência
            carta_bg_label.place(relx=0.5, rely=0.5, anchor="center")
            
            print("DEBUG: Carta colocada como fundo do overlay de confirmação")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar carta como fundo: {e}")
            self.configure(bg="black")
        
        # Aplicar o mesmo formato da página de seleção
        confirm_frame = tk.Frame(self, bg="black")
        confirm_frame.pack(expand=True)
        
        # Título da confirmação (mesmo estilo da página de seleção)
        tk.Label(confirm_frame, 
                text=f"   Card sent to {jogador_alvo.upper()} player!    ",
                font=("Helvetica", 15, "bold"),
                fg="white",
                bg="black").pack(pady=(40,  20))
        
        # Frame para o ícone do jogador (centralizado, mesmo estilo da seleção)
        player_frame = tk.Frame(confirm_frame, bg="black")
        player_frame.pack(pady=(0, 20))
        
        
        # Mostrar ícone do jogador alvo (mesmo estilo da página de seleção)
        try:
            icon_path = os.path.join(IMG_DIR, f"{jogador_alvo}_user_icon.png")
            if os.path.exists(icon_path):
                icon_img = ImageTk.PhotoImage(Image.open(icon_path).resize((65, 65)))
                icon_label = tk.Label(player_frame, image=icon_img, bg="black")
                icon_label.image = icon_img
                icon_label.pack()
                
                # Label com nome da cor (mesmo estilo da página de seleção)
                cor_label = tk.Label(player_frame,
                                    text=jogador_alvo.upper(),
                                    font=("Helvetica", 14, "bold"),
                                    fg=self._get_color_hex(jogador_alvo),
                                    bg="black")
                cor_label.pack(pady=(5, 0))
        except Exception as e:
            print(f"DEBUG: Erro ao mostrar ícone de confirmação: {e}")
        
        # Botão OK centralizado (mesmo estilo)
        btn_frame = tk.Frame(confirm_frame, bg="black")
        btn_frame.pack(pady=5)
        
        # Botão OK para continuar
        def continuar():
            if casa_tipo in ["actions", "action", "events", "event"]:
                # Para Actions/Events, voltar ao PlayerDashboard sem botão Store
                try:
                    if self.dashboard and hasattr(self.dashboard, "playerdashboard_interface"):
                        self.withdraw()
                        self.dashboard.deiconify()
                        self.dashboard.state('normal')
                        self.dashboard.lift()
                        self.dashboard.focus_force()
                        self.dashboard.playerdashboard_interface(
                            self.dashboard.player_name,
                            self.dashboard.saldo,
                            self.dashboard.other_players,
                            show_store_button=False
                        )
                        print("DEBUG: Voltando ao PlayerDashboard após envio da carta")
                except Exception as e:
                    print(f"DEBUG: Erro ao voltar ao PlayerDashboard: {e}")
            else:
                self.voltar_para_store()
        
        btn_ok = tk.Button(btn_frame,
                          text="OK",
                          font=("Helvetica", 14, "bold"),
                          bg="#4CAF50",
                          fg="white",
                          width=8,
                          command=continuar)
        btn_ok.pack()

    def mostrar_carta_fullscreen_escolha(self, carta_path, carta_tipo):
        # Guardar estado da carta fullscreen para poder restaurar depois
        self.fullscreen_carta_path = carta_path
        self.fullscreen_carta_tipo = carta_tipo
        # ADICIONAR: Múltiplos backups para garantir preservação
        self._backup_fullscreen_carta_path = carta_path
        self._backup_fullscreen_carta_tipo = carta_tipo
        self._original_carta_path = carta_path
        self._original_carta_tipo = carta_tipo
        
        print(f"DEBUG: [mostrar_carta_fullscreen_escolha] Guardando estado fullscreen - carta: {carta_path}, tipo: {carta_tipo}")
        print(f"DEBUG: [mostrar_carta_fullscreen_escolha] Estado guardado: fullscreen_carta_path={self.fullscreen_carta_path}, fullscreen_carta_tipo={self.fullscreen_carta_tipo}")
        print(f"DEBUG: [mostrar_carta_fullscreen_escolha] Backups criados: _backup={self._backup_fullscreen_carta_path}, _original={self._original_carta_path}")
        print(f"DEBUG: [mostrar_carta_fullscreen_escolha] ID do objeto Store: {id(self)}")
        
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
                print("DEBUG: [botão Player] Abrindo interface principal do PlayerDashboard")
                print(f"DEBUG: [botão Player] Estado antes de ir para PlayerDashboard: fullscreen_carta_path={getattr(self, 'fullscreen_carta_path', 'NOT_SET')}, fullscreen_carta_tipo={getattr(self, 'fullscreen_carta_tipo', 'NOT_SET')}")
                print(f"DEBUG: [botão Player] ID do objeto Store: {id(self)}")
                try:
                    # CRÍTICO: Garantir que o estado da carta fullscreen seja preservado
                    # Usar os valores corretos da função atual
                    fullscreen_carta_path_backup = carta_path  # Usar diretamente o parâmetro da função
                    fullscreen_carta_tipo_backup = carta_tipo  # Usar diretamente o parâmetro da função
                    
                    print(f"DEBUG: [botão Player] Usando parâmetros da função atual: path={fullscreen_carta_path_backup}, tipo={fullscreen_carta_tipo_backup}")
                    
                    # IMPORTANTE: Garantir que o estado seja preservado MÚLTIPLAS VEZES
                    self.fullscreen_carta_path = fullscreen_carta_path_backup
                    self.fullscreen_carta_tipo = fullscreen_carta_tipo_backup
                    self._backup_fullscreen_carta_path = fullscreen_carta_path_backup
                    self._backup_fullscreen_carta_tipo = fullscreen_carta_tipo_backup
                    self._original_carta_path = fullscreen_carta_path_backup
                    self._original_carta_tipo = fullscreen_carta_tipo_backup
                    
                    print(f"DEBUG: [botão Player] Estado GARANTIDAMENTE preservado em todos os backups")
                    print(f"DEBUG: [botão Player] fullscreen_carta_path = {self.fullscreen_carta_path}")
                    print(f"DEBUG: [botão Player] _backup_fullscreen_carta_path = {self._backup_fullscreen_carta_path}")
                    print(f"DEBUG: [botão Player] _original_carta_path = {self._original_carta_path}")
                    
                    # Vai para a interface principal do PlayerDashboard
                    if self.dashboard and hasattr(self.dashboard, "playerdashboard_interface"):
                        # Esconder a Store primeiro
                        print("DEBUG: [botão Player] Escondendo Store...")
                        self.withdraw()
                        print("DEBUG: [botão Player] Store escondida")
                        
                        # VERIFICAÇÃO CRÍTICA: Confirmar que o estado ainda está preservado após withdraw
                        print(f"DEBUG: [botão Player] Após withdraw - fullscreen_carta_path: {getattr(self, 'fullscreen_carta_path', 'PERDIDO!')}")
                        print(f"DEBUG: [botão Player] Após withdraw - _backup_fullscreen_carta_path: {getattr(self, '_backup_fullscreen_carta_path', 'PERDIDO!')}")
                        
                        # Se perdeu o estado, restaurar dos backups
                        if not getattr(self, 'fullscreen_carta_path', None):
                            print("DEBUG: [botão Player] Estado perdido após withdraw - restaurando dos backups")
                            self.fullscreen_carta_path = fullscreen_carta_path_backup
                            self.fullscreen_carta_tipo = fullscreen_carta_tipo_backup
                        
                        # Mostrar o PlayerDashboard
                        self.dashboard.deiconify()
                        self.dashboard.state('normal')
                        self.dashboard.lift()
                        self.dashboard.focus_force()
                        print("DEBUG: [botão Player] PlayerDashboard mostrado")
                        
                        # Chamar a interface principal do PlayerDashboard
                        self.dashboard.playerdashboard_interface(
                            self.dashboard.player_name,
                            self.dashboard.saldo,
                            self.dashboard.other_players
                        )
                        print("DEBUG: [botão Player] Interface principal do PlayerDashboard aberta com sucesso")
                        print(f"DEBUG: [botão Player] Estado FINAL depois de ir para PlayerDashboard:")
                        print(f"DEBUG: [botão Player] fullscreen_carta_path = {getattr(self, 'fullscreen_carta_path', 'NOT_SET')}")
                        print(f"DEBUG: [botão Player] fullscreen_carta_tipo = {getattr(self, 'fullscreen_carta_tipo', 'NOT_SET')}")
                        print(f"DEBUG: [botão Player] _backup_fullscreen_carta_path = {getattr(self, '_backup_fullscreen_carta_path', 'NOT_SET')}")
                    else:
                        print("DEBUG: [botão Player] ERRO - PlayerDashboard não disponível")
                except Exception as e:
                    print(f"DEBUG: [botão Player] Erro ao abrir PlayerDashboard: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Carregamento do ícone do jogador
            try:
                user_icon_path = os.path.join(IMG_DIR, f"{self.player_color}_user_icon.png")
                user_icon_img = ImageTk.PhotoImage(Image.open(user_icon_path).resize((40, 40)))
                btn_inventory = tk.Button(self, image=user_icon_img, bg="#8A2BE2", relief="flat", borderwidth=0, command=abrir_playerdashboard, cursor="hand2")
                btn_inventory.image = user_icon_img  # Manter referência para evitar garbage collection
            except Exception as e:
                print(f"DEBUG: Erro ao carregar ícone do jogador {self.player_color}_user_icon.png: {e}")
                # Fallback para texto se não conseguir carregar a imagem
                btn_inventory = tk.Button(self, text="Player", font=("Helvetica", 16, "bold"), bg="#8A2BE2", fg="white", relief="flat", borderwidth=0, command=abrir_playerdashboard)
            
            btn_inventory.place(relx=0.5, rely=0, anchor="n")
        # Botões Sim/Não
        def aceitar():
            # Limpar estado de fullscreen porque a carta foi aceita
            self.fullscreen_carta_path = None
            self.fullscreen_carta_tipo = None
            print("DEBUG: Estado de fullscreen limpo ao aceitar carta")
            
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
                        
                        # Chamar a interface principal do PlayerDashboard sem mostrar botão Store
                        self.dashboard.playerdashboard_interface(
                            self.dashboard.player_name,
                            self.dashboard.saldo,
                            self.dashboard.other_players,
                            show_store_button=False
                        )
                        print("DEBUG: Interface principal do PlayerDashboard aberta com sucesso ao aceitar escolha")
                    except Exception as e:
                        print(f"DEBUG: Erro ao voltar ao PlayerDashboard após aceitar escolha: {e}")
        def recusar():
            # Limpar estado de fullscreen porque a carta foi recusada
            self.fullscreen_carta_path = None
            self.fullscreen_carta_tipo = None
            print("DEBUG: Estado de fullscreen limpo ao recusar carta")
            
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
                    
                    # Chamar a interface principal do PlayerDashboard sem mostrar botão Store
                    self.dashboard.playerdashboard_interface(
                        self.dashboard.player_name,
                        self.dashboard.saldo,
                        self.dashboard.other_players,
                        show_store_button=False
                    )
                    print("DEBUG: Interface principal do PlayerDashboard aberta com sucesso ao recusar escolha")
                except Exception as e:
                    print(f"DEBUG: Erro ao voltar ao PlayerDashboard após recusar escolha: {e}")
                
        # Botão verde (✔) canto superior direito
        btn_certo = tk.Button(self, text="✔", font=("Helvetica", 24, "bold"), bg="#4CAF50", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=aceitar, cursor="hand2", activebackground="#43d17a")
        btn_certo.place(relx=0.98, rely=0, anchor="ne")
        # Botão cinza (✖) canto superior esquerdo
        btn_x = tk.Button(self, text="✖", font=("Helvetica", 24, "bold"), bg="#AAAAAA", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=recusar, cursor="hand2", activebackground="#CCCCCC")
        btn_x.place(relx=0., rely=0, anchor="nw")

    def iniciar_venda_carta(self, carta_path, carta_tipo, player_dashboard):
        """FUNÇÃO DEPRECATED - Redireciona para PlayerDashboard"""
        print(f"DEBUG: iniciar_venda_carta (deprecated) - redirecionando para PlayerDashboard")
        if player_dashboard and hasattr(player_dashboard, 'show_sell_confirmation'):
            player_dashboard.show_sell_confirmation(carta_path, carta_tipo, self)
        else:
            print("DEBUG: ERRO - PlayerDashboard não encontrado")
            # Fallback: volta à página de inventário
            if hasattr(self, 'current_sell_type') and self.current_sell_type:
                self.show_sell_inventory_paginated(self.current_sell_type, getattr(self, 'current_sell_page', 0))
            else:
                self.voltar_para_store()
        
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

    def mostrar_confirmacao_venda_overlay(self, carta_path, carta_tipo, player_dashboard):
        """Mostra a confirmação de venda como overlay sobre a carta em fullscreen."""
        print(f"DEBUG: mostrar_confirmacao_venda_overlay chamado - carta_path: {carta_path}")
        
        # Extrair valor da carta
        valor = None
        try:
            import re
            nome = os.path.basename(carta_path)
            print(f"DEBUG: Extraindo valor do arquivo: {nome}")
            
            # Se for carta de Activities, valor é sempre 0
            if carta_tipo == "activities":
                valor = 0
                print(f"DEBUG: Carta de Activities - valor definido como 0")
            else:
                # Tentar diferentes padrões de extração para outros tipos
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
        
        # Criar frame de overlay
        overlay_frame = tk.Frame(self, bg="black")
        overlay_frame.place(relx=0.5, rely=0.5, anchor="center", width=400, height=300)
        
        # Frame interno para centrar conteúdo
        content_frame = tk.Frame(overlay_frame, bg="black")
        content_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Título
        tk.Label(content_frame, text="Are you sure you want to sell?", 
                font=("Helvetica", 16, "bold"), fg="white", bg="black").pack(pady=(20, 15))
        
        # Saldo atual do player
        player_saldo = player_dashboard.saldo if player_dashboard else self.saldo
        tk.Label(content_frame, text=f"Your balance: {player_saldo}", 
                font=("Helvetica", 14), fg="yellow", bg="black").pack(pady=(0, 10))
        
        # Valor da carta
        value_frame = tk.Frame(content_frame, bg="black")
        value_frame.pack(pady=(0, 20))
        
        value_text_lbl = tk.Label(value_frame, text="Card value: ", 
                                 font=("Helvetica", 14), fg="white", bg="black")
        value_text_lbl.pack(side="left")
        
        value_amount_lbl = tk.Label(value_frame, text=str(valor) if valor is not None else "?", 
                                   font=("Helvetica", 14, "bold"), fg="yellow", bg="black")
        value_amount_lbl.pack(side="left", padx=(5, 5))
        
        # Ícone da moeda
        try:
            picoin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((20,20)))
            picoin_lbl = tk.Label(value_frame, image=picoin_img, bg="black")
            picoin_lbl.image = picoin_img
            picoin_lbl.pack(side="left")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar ícone da moeda: {e}")
        
        # Frame dos botões
        btns_frame = tk.Frame(content_frame, bg="black")
        btns_frame.pack(side="bottom", pady=(20, 10))
        
        def confirmar():
            print("DEBUG: Confirmar venda - início (overlay)")
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
                
                # Sincronizar o inventário da Store com o do PlayerDashboard
                if hasattr(self, 'inventario') and self.inventario is not None:
                    self.inventario = player_dashboard.inventario
                    print(f"DEBUG: Inventário da Store sincronizado com o PlayerDashboard")
            
            print(f"DEBUG: Venda confirmada - Player saldo: {player_dashboard.saldo}, Store saldo: {self.saldo}")
            
            # Remove o overlay
            overlay_frame.destroy()
            
            # Volta à página de venda
            if hasattr(self, 'current_sell_type') and self.current_sell_type:
                self.show_sell_inventory_paginated(self.current_sell_type, getattr(self, 'current_sell_page', 0))
                print(f"DEBUG: Voltando à página de venda de {self.current_sell_type}")
            else:
                self.voltar_para_store()
                print("DEBUG: Voltando à página inicial da Store (fallback)")
        
        def cancelar():
            print("DEBUG: Venda cancelada - removendo overlay")
            overlay_frame.destroy()
        
        # Botões Yes e No
        btn_yes = tk.Button(btns_frame, text="Yes", font=("Helvetica", 12, "bold"), 
                           bg="#4CAF50", fg="white", width=8, command=confirmar)
        btn_no = tk.Button(btns_frame, text="No", font=("Helvetica", 12, "bold"), 
                          bg="#F44336", fg="white", width=8, command=cancelar)
        btn_yes.pack(side="left", padx=10)
        btn_no.pack(side="left", padx=10)
        
        print("DEBUG: Overlay de confirmação de venda criado com sucesso")

    def confirmar_venda_carta(self, carta_path, carta_tipo, player_dashboard):
        """FUNÇÃO DEPRECATED - Redireciona para PlayerDashboard"""
        print(f"DEBUG: confirmar_venda_carta (deprecated) - redirecionando para PlayerDashboard")
        if player_dashboard and hasattr(player_dashboard, 'show_sell_confirmation'):
            player_dashboard.show_sell_confirmation(carta_path, carta_tipo, self)
        else:
            print("DEBUG: ERRO - PlayerDashboard não encontrado")
            # Fallback: volta à página de inventário
            if hasattr(self, 'current_sell_type') and self.current_sell_type:
                self.show_sell_inventory_paginated(self.current_sell_type, getattr(self, 'current_sell_page', 0))
            else:
                self.voltar_para_store()
        
        # PRIMEIRO: Mostra a carta em fullscreen como fundo
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
            
            # Carta em fullscreen como fundo
            carta_real_lbl = tk.Label(self, image=carta_img, bg="black", borderwidth=0, highlightthickness=0)
            carta_real_lbl.image = carta_img  # Manter referência para evitar garbage collection
            carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center")
            print("DEBUG: Carta carregada em fullscreen como fundo")
            
        except Exception as e:
            print(f"DEBUG: ERRO ao carregar carta para fundo: {e}")
            # Mostrar um placeholder em caso de erro
            carta_real_lbl = tk.Label(self, text="Erro ao carregar carta", font=("Helvetica", 20), fg="red", bg="black")
            carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center")
        
        # SEGUNDO: Criar overlay de confirmação sobre a carta
        overlay_frame = tk.Frame(self, bg="black")
        overlay_frame.place(relx=0.5, rely=0.5, anchor="center", width=500, height=350)
        
        # Frame de confirmação dentro do overlay
        confirm_frame = tk.Frame(overlay_frame, bg="black")
        confirm_frame.pack(expand=True, fill="both", padx=40, pady=40)
        
        # Extrair valor da carta
        valor = None
        try:
            import re
            nome = os.path.basename(carta_path)
            print(f"DEBUG: Extraindo valor do arquivo: {nome}")
            
            # Se for carta de Activities, valor é sempre 0
            if carta_tipo == "activities":
                valor = 0
                print(f"DEBUG: Carta de Activities - valor definido como 0")
            else:
                # Tentar diferentes padrões de extração para outros tipos
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
        
        # Título da confirmação
        tk.Label(confirm_frame, text="Are you sure you want to sell?", font=("Helvetica", 16, "bold"), fg="white", bg="black").pack(pady=(20, 15))
        
        # Usar o saldo do Player
        player_saldo = player_dashboard.saldo if player_dashboard else self.saldo
        tk.Label(confirm_frame, text=f"Your balance: {player_saldo}", font=("Helvetica", 16), fg="yellow", bg="black").pack(pady=(0, 10))
        
        # Valor da carta
        value_frame = tk.Frame(confirm_frame, bg="black")
        value_frame.pack(pady=(0, 20))
        
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
            picoin_lbl.image = picoin_img
            picoin_lbl.pack(side="left")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar ícone da moeda: {e}")
        
        btns_frame = tk.Frame(confirm_frame, bg="black")
        btns_frame.pack(side="bottom", pady=(20, 0))
        
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
                
                print(f"DEBUG: Carta vendida não será adicionada ao inventário da Store para evitar duplicação")
            
            print(f"DEBUG: Venda confirmada - Player saldo: {player_dashboard.saldo}, Store saldo: {self.saldo}")
            
            # ALTERAÇÃO: Volta à página de venda em vez da página inicial da Store (igual à compra)
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
            # CORREÇÃO: Usar função do PlayerDashboard em vez do Store
            if player_dashboard and hasattr(player_dashboard, 'show_sell_confirmation'):
                player_dashboard.show_sell_confirmation(carta_path, carta_tipo, self)
            else:
                print("DEBUG: ERRO - PlayerDashboard não encontrado ou não tem show_sell_confirmation")
                # Fallback: volta à página de inventário de venda
                if hasattr(self, 'current_sell_type') and self.current_sell_type:
                    self.show_sell_inventory_paginated(self.current_sell_type, getattr(self, 'current_sell_page', 0))
                else:
                    self.voltar_para_store()
        
        # Botões Yes e No (igual ao da compra)
        btn_yes = tk.Button(btns_frame, text="Yes", font=("Helvetica", 14, "bold"), bg="#4CAF50", fg="white", width=8, command=confirmar)
        btn_no = tk.Button(btns_frame, text="No", font=("Helvetica", 14, "bold"), bg="#F44336", fg="white", width=8, command=cancelar)
        btn_yes.pack(side="left", padx=20, pady=10)
        btn_no.pack(side="left", padx=20, pady=10)
        
        print("DEBUG: confirmar_venda_carta interface criada com sucesso")

    def rebuild_store_interface(self):
        """Reconstrói a interface da Store após voltar da página de compra"""
        print("DEBUG: rebuild_store_interface chamado")
        print(f"DEBUG: [rebuild_store_interface] ID do objeto Store: {id(self)}")
        
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
            
            awning_img = ImageTk.PhotoImage(Image.open(AWNING_IMG).resize((screen_width, 65)))
            awning_label = tk.Label(self, image=awning_img, bg="black")
            awning_label.image = awning_img  # type: ignore[attr-defined]
            awning_label.pack(pady=(0, 10), fill="x")
            print(f"DEBUG: Barra superior criada com largura {screen_width}")
            
            # Label pequeno à esquerda do logo
            left_label = tk.Label(self, text="••••", font=("Helvetica", 12, "bold"), bg="#DC8392", fg="#DC8392")
            left_label.place(relx=0.46, y=10, anchor="center")
            
            # Logo NetMaster posicionado independentemente
            try:
                logo_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "logo_netmaster_store.png")).resize((24, 24)))
                logo_lbl = tk.Label(self, image=logo_img, bg="#DC8392")
                logo_lbl.image = logo_img  # type: ignore[attr-defined]
                logo_lbl.place(relx=0.5, y=10, anchor="center")
            except Exception as e:
                print(f"DEBUG: Erro ao carregar logo: {e}")
            
            # Label largo à direita do logo para cobrir área amarela
            right_logo_label = tk.Label(self, text="     ", font=("Helvetica", 12, "bold"), bg="#DC8392", fg="#DC8392")
            right_logo_label.place(relx=0.53, y=10, anchor="w")
            
            # Label adicional para garantir cobertura completa
            extra_cover_label = tk.Label(self, text="     ", font=("Helvetica", 10), bg="#DC8392", fg="#DC8392")
            extra_cover_label.place(relx=0.55, y=10, anchor="w")
            
            # Texto "Store" posicionado independentemente
            store_name_lbl = tk.Label(self, text="Store", 
                                     font=("Helvetica", 15, "bold"), bg="#DC8392", fg="black")
            store_name_lbl.place(relx=0.5, y=30, anchor="center")
            
            # Label pequeno à direita do nome Store
            right_store_label = tk.Label(self, text="•", font=("Helvetica", 12, "bold"), bg="#DC8392", fg="#DC8392")
            right_store_label.place(relx=0.6, y=30, anchor="center")
            
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

            # Frame para os botões de ação na parte inferior (não usado mais)
            self.action_frame = tk.Frame(self, bg="black")

            # Sub-frame centralizado para os botões (não usado mais)
            self.action_buttons_frame = tk.Frame(self.action_frame, bg="black")
            self.action_buttons_frame.pack(anchor="center", pady=2)

            # --- CORREÇÃO: Verificar se há carta em fullscreen pendente ---
            print(f"DEBUG: [rebuild_store_interface] Verificando estado da carta fullscreen...")
            print(f"DEBUG: [rebuild_store_interface] hasattr(self, 'fullscreen_carta_path'): {hasattr(self, 'fullscreen_carta_path')}")
            print(f"DEBUG: [rebuild_store_interface] hasattr(self, 'fullscreen_carta_tipo'): {hasattr(self, 'fullscreen_carta_tipo')}")
            if hasattr(self, 'fullscreen_carta_path'):
                print(f"DEBUG: [rebuild_store_interface] self.fullscreen_carta_path: {self.fullscreen_carta_path}")
            if hasattr(self, 'fullscreen_carta_tipo'):
                print(f"DEBUG: [rebuild_store_interface] self.fullscreen_carta_tipo: {self.fullscreen_carta_tipo}")
            
            # USAR A NOVA FUNÇÃO ESPECÍFICA
            if self.restaurar_carta_fullscreen_pendente():
                print("DEBUG: [rebuild_store_interface] Carta em fullscreen restaurada - saindo do método")
                return  # Sair do método para não continuar com a interface normal
            else:
                print("DEBUG: [rebuild_store_interface] Nenhuma carta pendente - continuando com interface normal")
            
            # --- CORREÇÃO: Aplicar destaque e comandos corretos para casas neutras e normais ---
            if hasattr(self, 'casa_tipo') and hasattr(self, 'casa_cor') and self.casa_tipo and self.casa_cor:
                print(f"DEBUG: Aplicando destaque para {self.casa_tipo} {self.casa_cor}")
                # Para todos os tipos, garantir que o tipo é plural (actions, events, challenges)
                tipo_map = {"action": "actions", "event": "events", "challenge": "challenges"}
                casa_tipo = tipo_map.get(self.casa_tipo, self.casa_tipo)
                print(f"DEBUG: Tipo normalizado de '{self.casa_tipo}' para '{casa_tipo}'")
                self.highlight_casa(casa_tipo, self.casa_cor)
            else:
                print("DEBUG: Desabilitando todos os botões - sem destaque")
                self.disable_all_buttons()
            
            # Força update final para garantir que tudo é exibido
            self.update_idletasks()
            self.update()
            
            # Barra inferior com imagem BelowBar_store.png
            belowbar_img = ImageTk.PhotoImage(Image.open(BELOWBAR_IMG).resize((screen_width, 65)))
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
                try:
                    if self.dashboard and hasattr(self.dashboard, "playerdashboard_interface"):
                        # Esconder a Store primeiro
                        self.withdraw()
                        print("DEBUG: Store escondida")
                        
                        # Mostrar o PlayerDashboard
                        self.dashboard.deiconify()
                        self.dashboard.state('normal')
                        self.dashboard.lift()
                        self.dashboard.focus_force()
                        print("DEBUG: PlayerDashboard mostrado")
                        
                        # Chamar a interface principal do PlayerDashboard
                        self.dashboard.playerdashboard_interface(
                            self.dashboard.player_name,
                            self.dashboard.saldo,
                            self.dashboard.other_players
                        )
                        print("DEBUG: Interface principal do PlayerDashboard aberta com sucesso")
                    else:
                        print("DEBUG: ERRO - PlayerDashboard não disponível ou método playerdashboard_interface não encontrado")
                except Exception as e:
                    print(f"DEBUG: Erro ao abrir PlayerDashboard: {e}")

            try:
                # Carregar ícone do jogador
                user_icon_path = os.path.join(IMG_DIR, f"{self.player_color}_user_icon.png")
                user_icon_img = ImageTk.PhotoImage(Image.open(user_icon_path).resize((30, 30)))
                btn_player = tk.Button(self, image=user_icon_img, bg="#DC8392", relief="flat", borderwidth=0, 
                                      command=abrir_playerdashboard, cursor="hand2", activebackground="#DC8392",
                                      highlightthickness=0)
                btn_player.image = user_icon_img  # Manter referência para evitar garbage collection
                btn_player.place(x=screen_width-10, y=5, anchor="ne")  # Movido mais para a direita e para cima
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
            awning_img = ImageTk.PhotoImage(Image.open(AWNING_IMG).resize((screen_width, 65)))
            awning_label = tk.Label(self, image=awning_img, bg="black")
            awning_label.image = awning_img
            awning_label.pack(pady=(0, 10), fill="x")
            
            # Label pequeno à esquerda do logo
            left_label = tk.Label(self, text="••••", font=("Helvetica", 12, "bold"), bg="#DC8392", fg="#DC8392")
            left_label.place(relx=0.46, y=10, anchor="center")
            
            # Logo NetMaster posicionado independentemente
            try:
                logo_img = ImageTk.PhotoImage(Image.open(os.path.join(IMG_DIR, "logo_netmaster_store.png")).resize((24, 24)))
                logo_lbl = tk.Label(self, image=logo_img, bg="#DC8392")
                logo_lbl.image = logo_img  # type: ignore[attr-defined]
                logo_lbl.place(relx=0.5, y=10, anchor="center")
            except Exception as e:
                print(f"DEBUG: Erro ao carregar logo: {e}")
            
            # Label largo à direita do logo para cobrir área amarela
            right_logo_label = tk.Label(self, text="     ", font=("Helvetica", 12, "bold"), bg="#DC8392", fg="#DC8392")
            right_logo_label.place(relx=0.53, y=10, anchor="w")
            
            # Label adicional para garantir cobertura completa
            extra_cover_label = tk.Label(self, text="     ", font=("Helvetica", 10), bg="#DC8392", fg="#DC8392")
            extra_cover_label.place(relx=0.55, y=10, anchor="w")
            
            # Texto "Store" posicionado independentemente
            store_name_lbl = tk.Label(self, text="Store", 
                                     font=("Helvetica", 15, "bold"), bg="#DC8392", fg="black")
            store_name_lbl.place(relx=0.5, y=30, anchor="center")
            
            # Label pequeno à direita do nome Store
            right_store_label = tk.Label(self, text="•", font=("Helvetica", 12, "bold"), bg="#DC8392", fg="#DC8392")
            right_store_label.place(relx=0.6, y=30, anchor="center")
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
        
        back_btn = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), bg="#005c75", fg="white", width=6, 
                           command=voltar_carta_challenge)
        back_btn.place(relx=0.5, rely=0.98, anchor="s")
        
        # Barra inferior com imagem BelowBar_store.png
        belowbar_img = ImageTk.PhotoImage(Image.open(BELOWBAR_IMG).resize((screen_width, 65)))
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
            btn_player = tk.Button(self, image=user_icon_img, bg="#DC8392", relief="flat", borderwidth=0, 
                                  command=abrir_playerdashboard, cursor="hand2", activebackground="#DC8392",highlightthickness=0)
            btn_player.image = user_icon_img  # Manter referência para evitar garbage collection
            btn_player.place(x=screen_width-10, y=5, anchor="ne")  # Canto superior direito
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

    def processar_casa_challenges(self, casa_cor):
        """
        Função específica para processar casas de tipo 'challenges'.
        Simplifica todo o fluxo: tirar carta -> mostrar fullscreen -> botão Player funcional.
        """
        print(f"DEBUG: [processar_casa_challenges] Iniciando processamento para casa challenges cor={casa_cor}")
        print(f"DEBUG: [processar_casa_challenges] ID do objeto Store: {id(self)}")
        
        try:
            # Tirar uma carta de challenges
            carta_path = self.tirar_carta_especifica("challenges", casa_cor)
            if not carta_path:
                print("DEBUG: [processar_casa_challenges] Nenhuma carta de challenges disponível")
                return False
            
            print(f"DEBUG: [processar_casa_challenges] Carta obtida: {carta_path}")
            
            # Mostrar a carta em fullscreen com opções de aceitar/recusar
            self.mostrar_carta_challenge_fullscreen(carta_path)
            
            print("DEBUG: [processar_casa_challenges] Processamento concluído com sucesso")
            return True
            
        except Exception as e:
            print(f"DEBUG: [processar_casa_challenges] Erro: {e}")
            import traceback
            traceback.print_exc()
            return False

    def tirar_carta_especifica(self, tipo, cor):
        """
        Tira uma carta específica de um tipo e cor, retornando o caminho da carta.
        Remove a carta tanto do baralho local quanto do baralho global.
        """
        print(f"DEBUG: [tirar_carta_especifica] Tentando tirar carta tipo={tipo}, cor={cor}")
        
        # Verificar se há cartas disponíveis no baralho local
        if not hasattr(self, 'cartas') or not self.cartas:
            print("DEBUG: [tirar_carta_especifica] Nenhuma carta disponível no baralho local")
            return None
        
        # Usar a estrutura correta: cartas[cor][tipo]
        if cor not in self.cartas:
            print(f"DEBUG: [tirar_carta_especifica] Cor '{cor}' não encontrada no baralho local")
            return None
            
        if tipo not in self.cartas[cor]:
            print(f"DEBUG: [tirar_carta_especifica] Tipo '{tipo}' não encontrado para cor '{cor}' no baralho local")
            return None
            
        if not self.cartas[cor][tipo]:
            print(f"DEBUG: [tirar_carta_especifica] Nenhuma carta disponível para {cor}/{tipo} no baralho local")
            return None
        
        # Tirar uma carta aleatória
        import random
        carta_path = random.choice(self.cartas[cor][tipo])
        
        # CORREÇÃO: Remover carta do baralho local E do baralho global
        self.cartas[cor][tipo].remove(carta_path)
        
        # Remover também do baralho global para persistir entre instâncias da Store
        global baralhos
        if (baralhos and cor in baralhos and tipo in baralhos[cor] and 
            carta_path in baralhos[cor][tipo]):
            baralhos[cor][tipo].remove(carta_path)
            print(f"DEBUG: [tirar_carta_especifica] Carta removida do baralho global também")
        
        print(f"DEBUG: [tirar_carta_especifica] Carta tirada: {carta_path}")
        print(f"DEBUG: [tirar_carta_especifica] Cartas restantes em {cor}/{tipo}: {len(self.cartas[cor][tipo])}")
        print(f"DEBUG: [tirar_carta_especifica] Cartas restantes no baralho global {cor}/{tipo}: {len(baralhos[cor][tipo]) if baralhos and cor in baralhos and tipo in baralhos[cor] else 'N/A'}")
        
        return carta_path

    def adicionar_carta_ao_baralho(self, carta_path, carta_tipo, carta_cor=None):
        """
        Adiciona uma carta vendida de volta aos baralhos (local e global).
        Usado quando um jogador vende uma carta para a Store.
        """
        print(f"DEBUG: [adicionar_carta_ao_baralho] Adicionando carta ao baralho - carta: {os.path.basename(carta_path)}, tipo: {carta_tipo}, cor: {carta_cor}")
        
        # Se cor não foi especificada, determinar a partir do player_color
        if carta_cor is None:
            carta_cor = self.player_color
        
        # Garantir que a estrutura do baralho local existe
        if not hasattr(self, 'cartas'):
            self.cartas = {}
        if carta_cor not in self.cartas:
            self.cartas[carta_cor] = {}
        if carta_tipo not in self.cartas[carta_cor]:
            self.cartas[carta_cor][carta_tipo] = []
        
        # Adicionar ao baralho local se ainda não existir
        if carta_path not in self.cartas[carta_cor][carta_tipo]:
            self.cartas[carta_cor][carta_tipo].append(carta_path)
            print(f"DEBUG: [adicionar_carta_ao_baralho] Carta adicionada ao baralho local {carta_cor}/{carta_tipo}")
        
        # Adicionar também ao baralho global
        global baralhos
        if baralhos:
            if carta_cor not in baralhos:
                baralhos[carta_cor] = {}
            if carta_tipo not in baralhos[carta_cor]:
                baralhos[carta_cor][carta_tipo] = []
            
            if carta_path not in baralhos[carta_cor][carta_tipo]:
                baralhos[carta_cor][carta_tipo].append(carta_path)
                print(f"DEBUG: [adicionar_carta_ao_baralho] Carta adicionada ao baralho global {carta_cor}/{carta_tipo}")
        
        print(f"DEBUG: [adicionar_carta_ao_baralho] Sincronização completa - carta {os.path.basename(carta_path)} adicionada aos baralhos")
        print(f"DEBUG: [adicionar_carta_ao_baralho] Cartas agora em {carta_cor}/{carta_tipo}: local={len(self.cartas[carta_cor][carta_tipo])}, global={len(baralhos[carta_cor][carta_tipo]) if baralhos and carta_cor in baralhos and carta_tipo in baralhos[carta_cor] else 'N/A'}")

    def _remover_carta_do_baralho_local(self, carta_path, carta_tipo):
        """
        Remove uma carta específica do baralho local da Store após ela ser tirada.
        Usado para sincronizar com o baralho global e evitar que cartas tiradas apareçam novamente.
        """
        print(f"DEBUG: [_remover_carta_do_baralho_local] Removendo carta: {os.path.basename(carta_path)}, tipo: {carta_tipo}")
        
        if not hasattr(self, 'cartas') or not self.cartas:
            print("DEBUG: [_remover_carta_do_baralho_local] Nenhum baralho local encontrado")
            return
        
        # Para cartas Actions/Events/Challenges, elas são tipicamente neutras
        # Mas também podem ser da cor do jogador para alguns tipos
        cores_para_verificar = ["neutral"]
        if hasattr(self, 'player_color') and self.player_color:
            cores_para_verificar.append(self.player_color)
        
        carta_removida = False
        for cor in cores_para_verificar:
            if cor in self.cartas and carta_tipo in self.cartas[cor]:
                if carta_path in self.cartas[cor][carta_tipo]:
                    self.cartas[cor][carta_tipo].remove(carta_path)
                    carta_removida = True
                    print(f"DEBUG: [_remover_carta_do_baralho_local] Carta removida do baralho local {cor}/{carta_tipo}")
                    print(f"DEBUG: [_remover_carta_do_baralho_local] Cartas restantes em {cor}/{carta_tipo}: {len(self.cartas[cor][carta_tipo])}")
                    break
        
        if not carta_removida:
            print(f"DEBUG: [_remover_carta_do_baralho_local] AVISO: Carta não encontrada nos baralhos locais para remoção")
            # Debug das cartas disponíveis
            for cor in cores_para_verificar:
                if cor in self.cartas and carta_tipo in self.cartas[cor]:
                    cartas_disponiveis = [os.path.basename(c) for c in self.cartas[cor][carta_tipo][:5]]
                    print(f"DEBUG: [_remover_carta_do_baralho_local] Cartas disponíveis em {cor}/{carta_tipo}: {cartas_disponiveis}")

    def mostrar_carta_challenge_fullscreen(self, carta_path):
        """
        Mostra uma carta de Challenge em fullscreen com funcionalidade completa.
        Inclui botão Player que preserva o estado corretamente.
        """
        print(f"DEBUG: [mostrar_carta_challenge_fullscreen] Mostrando carta: {carta_path}")
        
        # Guardar estado da carta fullscreen com múltiplos backups
        self.fullscreen_carta_path = carta_path
        self.fullscreen_carta_tipo = "challenges"
        self._backup_fullscreen_carta_path = carta_path
        self._backup_fullscreen_carta_tipo = "challenges"
        self._original_carta_path = carta_path
        self._original_carta_tipo = "challenges"
        
        print(f"DEBUG: [mostrar_carta_challenge_fullscreen] Estado preservado em múltiplos backups")
        print(f"DEBUG: [mostrar_carta_challenge_fullscreen] ID do objeto Store: {id(self)}")
        
        # Verificar se o arquivo existe
        if not os.path.exists(carta_path):
            print(f"DEBUG: [mostrar_carta_challenge_fullscreen] ERRO - Arquivo não existe: {carta_path}")
            return
        
        # Limpar interface e configurar fundo
        for widget in self.winfo_children():
            widget.destroy()
        self.configure(bg="black")
        
        # Carregar e mostrar a carta em fullscreen
        try:
            pil_img = Image.open(carta_path)
            img_w, img_h = pil_img.size
            max_w, max_h = self.winfo_screenwidth(), self.winfo_screenheight()
            ratio = min(max_w/img_w, max_h/img_h)
            new_w, new_h = int(img_w*ratio), int(img_h*ratio)
            pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            carta_img = ImageTk.PhotoImage(pil_img)
            carta_real_lbl = tk.Label(self, image=carta_img, bg="black")
            carta_real_lbl.image = carta_img  # Manter referência
            carta_real_lbl.place(relx=0.5, rely=0.5, anchor="center")
            
            print("DEBUG: [mostrar_carta_challenge_fullscreen] Carta carregada e exibida com sucesso")
            
        except Exception as e:
            print(f"DEBUG: [mostrar_carta_challenge_fullscreen] Erro ao carregar carta: {e}")
            # Mostrar placeholder em caso de erro
            error_lbl = tk.Label(self, text="Erro ao carregar carta", font=("Helvetica", 20), fg="red", bg="black")
            error_lbl.place(relx=0.5, rely=0.5, anchor="center")
        
        # Botão Player centrado no topo
        def abrir_playerdashboard():
            """Abre o PlayerDashboard preservando o estado da carta"""
            print("DEBUG: [Challenge Player] Abrindo PlayerDashboard")
            print(f"DEBUG: [Challenge Player] Estado atual: fullscreen_carta_path={self.fullscreen_carta_path}")
            
            try:
                # Garantir que o estado está preservado
                carta_backup = carta_path  # Usar parâmetro da função
                self.fullscreen_carta_path = carta_backup
                self.fullscreen_carta_tipo = "challenges"
                self._backup_fullscreen_carta_path = carta_backup
                self._backup_fullscreen_carta_tipo = "challenges"
                self._original_carta_path = carta_backup
                self._original_carta_tipo = "challenges"
                
                print(f"DEBUG: [Challenge Player] Estado reforçado antes de ir para PlayerDashboard")
                
                if self.dashboard and hasattr(self.dashboard, "playerdashboard_interface"):
                    # CORREÇÃO: Transferir estado para o PlayerDashboard ANTES de esconder Store
                    self.dashboard._store_challenge_carta_path = carta_backup
                    self.dashboard._store_challenge_carta_tipo = "challenges"
                    print(f"DEBUG: [Challenge Player] Estado transferido para PlayerDashboard: {carta_backup}")
                    
                    # Esconder Store DEPOIS de transferir estado
                    self.withdraw()
                    print("DEBUG: [Challenge Player] Store escondida DEPOIS de transferir estado")
                    
                    # Mostrar PlayerDashboard e recriar interface principal COM botão Store
                    self.dashboard.deiconify()
                    self.dashboard.state('normal')
                    self.dashboard.lift()
                    self.dashboard.focus_force()
                    
                    # Chamar interface principal (vai recriar mas com botão Store ativo)
                    self.dashboard.playerdashboard_interface(
                        self.dashboard.player_name,
                        self.dashboard.saldo,
                        self.dashboard.other_players,
                        show_store_button=True  # IMPORTANTE: mostrar botão Store
                    )
                    
                    print("DEBUG: [Challenge Player] PlayerDashboard interface principal criada com botão Store")
                    
                else:
                    print("DEBUG: [Challenge Player] ERRO - PlayerDashboard não disponível")
                    
            except Exception as e:
                print(f"DEBUG: [Challenge Player] Erro: {e}")
                traceback.print_exc()
        
        # Carregamento do ícone do Player
        try:
            user_icon_path = os.path.join(IMG_DIR, f"{self.player_color}_user_icon.png")
            user_icon_img = ImageTk.PhotoImage(Image.open(user_icon_path).resize((40, 40)))
            btn_player = tk.Button(self, image=user_icon_img, bg="#8A2BE2", relief="flat", 
                                 borderwidth=0, command=abrir_playerdashboard, cursor="hand2")
            btn_player.image = user_icon_img  # Manter referência
        except Exception as e:
            print(f"DEBUG: [mostrar_carta_challenge_fullscreen] Erro ao carregar ícone: {e}")
            # Fallback para texto
            btn_player = tk.Button(self, text="Player", font=("Helvetica", 16, "bold"), 
                                 bg="#8A2BE2", fg="white", relief="flat", borderwidth=0, 
                                 command=abrir_playerdashboard)
        
        btn_player.place(relx=0.5, rely=0, anchor="n")
        
        # Botões Aceitar/Recusar
        def aceitar_carta():
            """Aceita a carta e adiciona ao inventário"""
            print("DEBUG: [Challenge] Carta aceita")
            
            # IMPORTANTE: Desativar permanentemente o botão Store
            if self.dashboard and hasattr(self.dashboard, 'disable_store_button'):
                self.dashboard.disable_store_button()
                print("DEBUG: [Challenge] Botão Store desativado permanentemente")
            
            # Limpar estado fullscreen
            self.fullscreen_carta_path = None
            self.fullscreen_carta_tipo = None
            self._backup_fullscreen_carta_path = None
            self._backup_fullscreen_carta_tipo = None
            
            # Adicionar carta ao inventário
            if self.dashboard and hasattr(self.dashboard, 'inventario'):
                if 'challenges' not in self.dashboard.inventario:
                    self.dashboard.inventario['challenges'] = []
                self.dashboard.inventario['challenges'].append(carta_path)
                print(f"DEBUG: [Challenge] Carta adicionada ao inventário: {carta_path}")
            
            # Voltar ao PlayerDashboard SEM botão Store
            self._voltar_playerdashboard_sem_botao_store()
        
        def recusar_carta():
            """Recusa a carta"""
            print("DEBUG: [Challenge] Carta recusada")
            
            # IMPORTANTE: Desativar permanentemente o botão Store
            if self.dashboard and hasattr(self.dashboard, 'disable_store_button'):
                self.dashboard.disable_store_button()
                print("DEBUG: [Challenge] Botão Store desativado permanentemente")
            
            # Limpar estado fullscreen
            self.fullscreen_carta_path = None
            self.fullscreen_carta_tipo = None
            self._backup_fullscreen_carta_path = None
            self._backup_fullscreen_carta_tipo = None
            
            # Voltar ao PlayerDashboard SEM botão Store
            self._voltar_playerdashboard_sem_botao_store()
        
        # Botão Aceitar (✔) - canto superior direito
        btn_aceitar = tk.Button(self, text="✔", font=("Helvetica", 24, "bold"), 
                              bg="#4CAF50", fg="white", width=2, height=1, 
                              borderwidth=0, highlightthickness=0, command=aceitar_carta, 
                              cursor="hand2", activebackground="#43d17a")
        btn_aceitar.place(relx=0.98, rely=0, anchor="ne")
        
        # Botão Recusar (✖) - canto superior esquerdo (VERMELHO para Challenges)
        btn_recusar = tk.Button(self, text="✖", font=("Helvetica", 24, "bold"), 
                              bg="#F44336", fg="white", width=2, height=1, 
                              borderwidth=0, highlightthickness=0, command=recusar_carta, 
                              cursor="hand2", activebackground="#e57373")
        btn_recusar.place(relx=0, rely=0, anchor="nw")
        
        print("DEBUG: [mostrar_carta_challenge_fullscreen] Interface criada com sucesso")

    def _voltar_playerdashboard_sem_botao_store(self):
        """Volta ao PlayerDashboard sem mostrar o botão Store"""
        print("DEBUG: [_voltar_playerdashboard_sem_botao_store] Voltando ao PlayerDashboard")
        
        try:
            if self.dashboard:
                # Esconder a Store primeiro
                self.withdraw()
                print("DEBUG: [_voltar_playerdashboard_sem_botao_store] Store escondida")
                
                # Mostrar o PlayerDashboard
                self.dashboard.deiconify()
                self.dashboard.state('normal')
                self.dashboard.lift()
                self.dashboard.focus_force()
                print("DEBUG: [_voltar_playerdashboard_sem_botao_store] PlayerDashboard mostrado")
                
                # Chamar a interface principal do PlayerDashboard SEM botão Store
                self.dashboard.playerdashboard_interface(
                    self.dashboard.player_name,
                    self.dashboard.saldo,
                    self.dashboard.other_players,
                    show_store_button=False
                )
                print("DEBUG: [_voltar_playerdashboard_sem_botao_store] Interface principal criada SEM botão Store")
                
            else:
                print("DEBUG: [_voltar_playerdashboard_sem_botao_store] ERRO - PlayerDashboard não disponível")
                
        except Exception as e:
            print(f"DEBUG: [_voltar_playerdashboard_sem_botao_store] Erro: {e}")
            traceback.print_exc()

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
        
        back_btn = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), bg="#005c75", fg="white", width=6, 
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
        
        # Botão X para voltar ao inventário (movido para canto superior esquerdo)
        def voltar_inventario():
            print("DEBUG: Voltando ao inventário de compra")
            self.show_inventory_matrix_buy(tipos, page, current_card_type)
        
        x_btn = tk.Button(self, text="✖", font=("Helvetica", 24, "bold"), bg="#AAAAAA", fg="white", width=2, height=1, 
                         borderwidth=0, highlightthickness=0, command=voltar_inventario, cursor="hand2", activebackground="#CCCCCC")
        x_btn.place(relx=0.02, rely=0, anchor="nw")  # Canto superior esquerdo
        
        print("DEBUG: show_card_fullscreen_inventory_buy terminado com sucesso")

    def restaurar_carta_fullscreen_pendente(self):
        """
        Função específica para restaurar uma carta em fullscreen pendente.
        Retorna True se restaurou uma carta, False caso contrário.
        """
        print(f"DEBUG: [restaurar_carta_fullscreen_pendente] Verificando carta pendente...")
        print(f"DEBUG: [restaurar_carta_fullscreen_pendente] ID do objeto Store: {id(self)}")
        
        # Verificar se há uma carta em fullscreen pendente - ORDEM PRIORITÁRIA
        fullscreen_carta_path = getattr(self, 'fullscreen_carta_path', None)
        fullscreen_carta_tipo = getattr(self, 'fullscreen_carta_tipo', None)
        
        # Se não encontrou no local principal, verificar backup principal
        if not fullscreen_carta_path:
            fullscreen_carta_path = getattr(self, '_backup_fullscreen_carta_path', None)
            fullscreen_carta_tipo = getattr(self, '_backup_fullscreen_carta_tipo', None)
            if fullscreen_carta_path:
                print(f"DEBUG: [restaurar_carta_fullscreen_pendente] Estado recuperado do _backup")
                # Restaurar no local principal
                self.fullscreen_carta_path = fullscreen_carta_path
                self.fullscreen_carta_tipo = fullscreen_carta_tipo
        
        # Se ainda não encontrou, verificar backup original
        if not fullscreen_carta_path:
            fullscreen_carta_path = getattr(self, '_original_carta_path', None)
            fullscreen_carta_tipo = getattr(self, '_original_carta_tipo', None)
            if fullscreen_carta_path:
                print(f"DEBUG: [restaurar_carta_fullscreen_pendente] Estado recuperado do _original")
                # Restaurar no local principal
                self.fullscreen_carta_path = fullscreen_carta_path
                self.fullscreen_carta_tipo = fullscreen_carta_tipo
        
        print(f"DEBUG: [restaurar_carta_fullscreen_pendente] fullscreen_carta_path: {fullscreen_carta_path}")
        print(f"DEBUG: [restaurar_carta_fullscreen_pendente] fullscreen_carta_tipo: {fullscreen_carta_tipo}")
        
        # Se não há carta pendente, retornar False
        if not fullscreen_carta_path or not fullscreen_carta_tipo:
            print(f"DEBUG: [restaurar_carta_fullscreen_pendente] Nenhuma carta pendente encontrada")
            return False
        
        # Verificar se o arquivo da carta existe
        if not os.path.exists(fullscreen_carta_path):
            print(f"DEBUG: [restaurar_carta_fullscreen_pendente] Arquivo da carta não existe: {fullscreen_carta_path}")
            return False
        
        print(f"DEBUG: [restaurar_carta_fullscreen_pendente] Restaurando carta: {fullscreen_carta_path}, tipo: {fullscreen_carta_tipo}")
        
        # Restaurar a carta em fullscreen baseado no tipo
        if fullscreen_carta_tipo in ["challenges", "challenge"]:
            print(f"DEBUG: [restaurar_carta_fullscreen_pendente] Restaurando carta Challenge em fullscreen escolha")
            self.mostrar_carta_fullscreen_escolha(fullscreen_carta_path, fullscreen_carta_tipo)
        else:
            print(f"DEBUG: [restaurar_carta_fullscreen_pendente] Restaurando carta normal em fullscreen")
            self.mostrar_carta_fullscreen(fullscreen_carta_path, fullscreen_carta_tipo)
        
        print(f"DEBUG: [restaurar_carta_fullscreen_pendente] Carta restaurada com sucesso")
        return True