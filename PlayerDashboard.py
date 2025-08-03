import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import re
import traceback
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
from Store_v2 import StoreWindow
# Importar sistema de integração da base de dados
try:
    from card_integration import IntegratedCardDatabase
    print("DEBUG: IntegratedCardDatabase importada com sucesso")
except ImportError as e:
    print(f"DEBUG: ERRO ao importar IntegratedCardDatabase: {e}")
    IntegratedCardDatabase = None

IMG_DIR = os.path.join(os.path.dirname(__file__), "img")
# Verificar se existe no Raspberry Pi
if not os.path.exists(IMG_DIR):
    raspberry_img_dir = "/home/joao_rebolo/netmaster_menu/img"
    if os.path.exists(raspberry_img_dir):
        IMG_DIR = raspberry_img_dir
        print(f"DEBUG: Usando img do Raspberry Pi: {IMG_DIR}")
    else:
        print(f"DEBUG: Diretório img não encontrado, usando fallback: {IMG_DIR}")

# Detectar automaticamente onde estão as cartas
def detect_cartas_base_dir():
    """Detecta automaticamente o diretório base das cartas"""
    possible_dirs = [
        # Raspberry Pi - nova estrutura
        "/home/joao_rebolo/netmaster_menu",
        # Desenvolvimento local - nova estrutura  
        os.path.dirname(__file__),
        # Fallback para img/cartas se existir
        os.path.join(os.path.dirname(__file__), "img", "cartas")
    ]
    
    for dir_path in possible_dirs:
        # Verificar se existe pelo menos um dos diretórios de cartas esperados
        test_paths = [
            os.path.join(dir_path, "Activities", "Residential-level"),
            os.path.join(dir_path, "Users", "Residential-level"),
            os.path.join(dir_path, "Events", "Residential-level")
        ]
        
        if any(os.path.exists(test_path) for test_path in test_paths):
            print(f"DEBUG: Usando diretório de cartas: {dir_path}")
            return dir_path
    
    print("DEBUG: Nenhum diretório de cartas encontrado!")
    return possible_dirs[0]  # fallback

def detect_player_inventory_base_dir():
    """Detecta automaticamente o diretório base do inventário do jogador"""
    # Detectar se estamos no Raspberry Pi
    is_raspberry_pi = os.path.exists("/home/joao_rebolo") or "raspberry" in os.uname().nodename.lower()
    
    if is_raspberry_pi:
        possible_dirs = [
            # Raspberry Pi - estruturas possíveis
            "/home/joao_rebolo/netmaster_menu/img/cartas",
            "/home/joao_rebolo/netmaster_menu",
            "/home/joao_rebolo/netmaster_menu/img",
        ]
    else:
        possible_dirs = [
            # Desenvolvimento local - inventário do jogador  
            os.path.dirname(__file__),
            # Fallback para estrutura local
            os.path.join(os.path.dirname(__file__), "img", "cartas")
        ]
    
    print(f"DEBUG: [detect_player_inventory_base_dir] Ambiente detectado: {'Raspberry Pi' if is_raspberry_pi else 'Desenvolvimento Local'}")
    print(f"DEBUG: [detect_player_inventory_base_dir] Verificando diretórios possíveis...")
    for i, dir_path in enumerate(possible_dirs):
        print(f"DEBUG: [detect_player_inventory_base_dir] Opção {i+1}: {dir_path}")
        print(f"DEBUG: [detect_player_inventory_base_dir] Diretório existe? {os.path.exists(dir_path)}")
        
        # Verificar se existe pelo menos um dos diretórios de inventário esperados
        test_paths = [
            os.path.join(dir_path, "Activities", "Residential-level"),
            os.path.join(dir_path, "Users", "Residential-level"),
            os.path.join(dir_path, "Events", "Residential-level"),
            # Para Raspberry Pi, testar também estrutura alternativa
            os.path.join(dir_path, "activities", "Residential-level"),
            os.path.join(dir_path, "users", "Residential-level"),
            os.path.join(dir_path, "events", "Residential-level")
        ]
        
        print(f"DEBUG: [detect_player_inventory_base_dir] Testando caminhos:")
        for j, test_path in enumerate(test_paths):
            exists = os.path.exists(test_path)
            print(f"DEBUG: [detect_player_inventory_base_dir]   Teste {j+1}: {test_path} -> {exists}")
        
        if any(os.path.exists(test_path) for test_path in test_paths):
            print(f"DEBUG: Usando diretório de inventário do jogador: {dir_path}")
            return dir_path
    
    print("DEBUG: Nenhum diretório de inventário do jogador encontrado!")
    # Retornar o primeiro diretório como fallback
    fallback = possible_dirs[0] if possible_dirs else os.path.dirname(__file__)
    print(f"DEBUG: Usando fallback: {fallback}")
    return fallback
    return possible_dirs[1]  # fallback para desenvolvimento local

CARTAS_BASE_DIR = detect_cartas_base_dir()
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
        
        # Variáveis para controlar a casa atual (para o botão Store)
        self.current_casa_tipo = "neutral"
        self.current_casa_cor = "neutral"
        self.current_other_player_house = False  # Se está numa casa de outro jogador
        
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
            "actions": [],
            "events": [],
            "challenges": [],
            "activities": [],
        }

        # Variável para controlar se o botão Store deve estar desabilitado
        self._store_button_disabled = False
        
        # Inicializar base de dados integrada para valores das cartas
        try:
            if IntegratedCardDatabase:
                self.card_database = IntegratedCardDatabase(".")
                print("DEBUG: Base de dados de cartas inicializada com sucesso")
            else:
                self.card_database = None
                print("DEBUG: Base de dados de cartas não disponível")
        except Exception as e:
            print(f"DEBUG: ERRO ao inicializar base de dados: {e}")
            self.card_database = None
        
        # Variável para controlar se Next Phase está ativo (desabilita vendas)
        self._next_phase_active = False
        
        # Variável para controlar se Final Phase está ativo (bloqueia ativação/desativação de cartas)
        self._final_phase_active = False

        # PROTEÇÃO CONTRA LOOP: Flag para evitar abrir inventário recursivamente
        self._inventory_opening = False
        
        # Cache de User IDs para controlo do carrossel durante Next Phase
        self._cached_user_ids = []

        # INICIALIZAÇÃO DAS LISTAS DE CARTAS ATIVAS (movido do playerdashboard_interface)
        self.active_challenge = None  # Só pode haver 1 challenge ativo
        self.active_users = []        # Lista de users ativos (máx 4)
        self.active_equipments = []   # Lista de equipments ativos (sem limite)
        self.active_services = []     # Lista de services ativos (sem limite)
        self.max_users = 4
        # Equipments e Services não têm limite após Next Phase

        # CONTROLE DE SELEÇÃO DO CARROSSEL
        self.selected_carousel_card = None  # Carta atualmente selecionada
        self.selected_carousel_index = None  # Índice da carta selecionada

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
        
        # Cargas de cartas usando a nova estrutura: cartas/[tipo]/Residential-level/[cor]/
        def load_cards_from_new_structure(card_type, player_color):
            """Carrega cartas da nova estrutura de pastas"""
            cards = []
            
            # Tentar múltiplas estruturas de pastas
            possible_paths = []
            
            # Para cartas que têm cores específicas (equipments, services, users, activities)
            if card_type in ["equipments", "services", "users", "activities"]:
                # Mapear cor do jogador para diferentes formatos de nome
                color_variants = []
                if player_color == "blue":
                    color_variants = ["Blue", "blue", "BLUE"]
                elif player_color == "green": 
                    color_variants = ["Green", "green", "GREEN"]
                elif player_color == "red":
                    color_variants = ["Red", "red", "RED"]
                elif player_color == "yellow":
                    color_variants = ["Yellow", "yellow", "YELLOW"]
                else:
                    color_variants = ["Blue", "blue"]  # default
                
                # Estruturas possíveis:
                for color_var in color_variants:
                    # 1. cartas/[tipo]/Residential-level/[cor]/
                    possible_paths.append(os.path.join(CARTAS_BASE_DIR, card_type, "Residential-level", color_var))
                    # 2. cartas/Residential-[tipo]-[cor]/
                    possible_paths.append(os.path.join(CARTAS_BASE_DIR, f"Residential-{card_type}-{color_var}"))
                    # 3. cartas/[tipo]/[cor]/
                    possible_paths.append(os.path.join(CARTAS_BASE_DIR, card_type, color_var))
            else:
                # Para cartas sem cor específica (challenges, events, actions)
                possible_paths = [
                    # 1. cartas/[tipo]/Residential-level/
                    os.path.join(CARTAS_BASE_DIR, card_type, "Residential-level"),
                    # 2. cartas/Residential-[tipo]/
                    os.path.join(CARTAS_BASE_DIR, f"Residential-{card_type}"),
                    # 3. cartas/[tipo]/
                    os.path.join(CARTAS_BASE_DIR, card_type)
                ]
            
            # Tentar encontrar cartas em qualquer uma das estruturas possíveis
            for path in possible_paths:
                if os.path.exists(path):
                    try:
                        card_files = [os.path.join(path, f) for f in os.listdir(path) 
                                    if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                        if card_files:
                            cards.extend(card_files)
                            break  # Para no primeiro caminho que funcionar
                    except Exception as e:
                        continue
            
            return cards
        
        print("DEBUG: [PlayerDashboard] Iniciando carregamento de cartas do inventário...")
        
        # INVENTÁRIO INICIAL: O jogador deve começar com inventário vazio ou apenas algumas cartas básicas
        # As cartas são adicionadas quando compradas na Store, não carregadas de pastas externas
        
        # Verificar se há cartas do inventário do jogador nas pastas do NetMaster
        def load_player_inventory_cards(card_type, player_color):
            """Carrega cartas do inventário do jogador (não da loja)"""
            cards = []
            # Usar a detecção automática para Raspberry Pi e desenvolvimento local
            base_path = detect_player_inventory_base_dir()
            
            # Para cartas que têm cores específicas
            if card_type in ["equipments", "services", "users", "activities"]:
                color_variants = []
                if player_color == "blue":
                    color_variants = ["Blue", "blue", "BLUE"]
                elif player_color == "green": 
                    color_variants = ["Green", "green", "GREEN"]
                elif player_color == "red":
                    color_variants = ["Red", "red", "RED"]
                elif player_color == "yellow":
                    color_variants = ["Yellow", "yellow", "YELLOW"]
                else:
                    color_variants = ["Blue", "blue"]  # default
                
                # Estrutura: NetMaster/[Tipo]/Residential-level/[Cor]/
                folder_mapping = {
                    "users": "Users",
                    "equipments": "Equipments", 
                    "services": "Services",
                    "activities": "Activities"
                }
                folder_name = folder_mapping.get(card_type, card_type.capitalize())
                
                for color_var in color_variants:
                    path = os.path.join(base_path, folder_name, "Residential-level", color_var)
                    if os.path.exists(path):
                        try:
                            card_files = [os.path.join(path, f) for f in os.listdir(path) 
                                        if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                            if card_files:
                                cards.extend(card_files)
                                print(f"DEBUG: [PlayerDashboard] Cartas do inventário encontradas em: {path}")
                                break
                        except Exception as e:
                            continue
            else:
                # Para cartas sem cor específica (challenges, events, actions)
                folder_mapping = {
                    "challenges": "Challenges",
                    "actions": "Actions",
                    "events": "Events"
                }
                folder_name = folder_mapping.get(card_type, card_type.capitalize())
                path = os.path.join(base_path, folder_name, "Residential-level")
                if os.path.exists(path):
                    try:
                        card_files = [os.path.join(path, f) for f in os.listdir(path) 
                                    if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                        if card_files:
                            cards.extend(card_files)
                            print(f"DEBUG: [PlayerDashboard] Cartas do inventário encontradas em: {path}")
                    except Exception as e:
                        print(f"DEBUG: [PlayerDashboard] Erro ao carregar {card_type}: {e}")
            
            return cards
        
        # INVENTÁRIO INICIAL VAZIO - o jogador começa sem cartas
        # As cartas só são adicionadas quando compradas na Store
        print("DEBUG: [PlayerDashboard] Inicializando inventário vazio - cartas serão adicionadas via compras na Store")
        
        # OPCIONAL: Se quiseres dar algumas cartas iniciais ao jogador, descomenta isto:
        print("DEBUG: [PlayerDashboard] CHAMANDO add_starter_cards()...")
        self.add_starter_cards()  # ✅ ATIVADO - adicionar cartas de exemplo
        print("DEBUG: [PlayerDashboard] add_starter_cards() TERMINADO")

        print(f"DEBUG: [PlayerDashboard] Inventário inicial:")
        for tipo, cartas in self.inventario.items():
            print(f"DEBUG: [PlayerDashboard]   {tipo}: {len(cartas)} cartas")

        # --- BARRA SUPERIOR COM IMAGEM ---
        try:
            topbar_img_path = os.path.join(IMG_DIR, f"TopBar_{self.player_color.lower()}.png")
            print(f"DEBUG: Tentando carregar TopBar de: {topbar_img_path}")
            
            if os.path.exists(topbar_img_path):
                img = Image.open(topbar_img_path).convert("RGBA")
                img = img.resize((screen_width, 60), Image.Resampling.LANCZOS)
                topbar_img = ImageTk.PhotoImage(img)
                self.topbar_label = tk.Label(self, image=topbar_img, bg="black", borderwidth=0, highlightthickness=0)
                self.topbar_label.image = topbar_img  # type: ignore[attr-defined]
                self.topbar_label.pack(side="top", fill="x")
                print("DEBUG: TopBar criada com sucesso!")
            else:
                print(f"DEBUG: Arquivo TopBar não encontrado, criando fallback")
                # Fallback: criar uma barra colorida simples
                topbar_frame = tk.Frame(self, bg=self.bar_color, height=60)
                topbar_frame.pack(side="top", fill="x")
                topbar_frame.pack_propagate(False)
                self.topbar_label = topbar_frame
                print("DEBUG: TopBar fallback criada!")
        except Exception as e:
            print(f"DEBUG: ERRO ao criar TopBar: {e}")
            # Fallback: criar uma barra colorida simples
            topbar_frame = tk.Frame(self, bg=self.bar_color, height=60)
            topbar_frame.pack(side="top", fill="x")
            topbar_frame.pack_propagate(False)
            self.topbar_label = topbar_frame
            print("DEBUG: TopBar fallback criada após erro!")

        # Chama a tela de lançamento de dado
        print("DEBUG: [PlayerDashboard] Chamando show_dice_roll_screen...")
        self.show_dice_roll_screen(player_name, saldo, other_players, screen_width, screen_height)
    
    def add_starter_cards(self):
        """
        Função opcional para dar cartas iniciais ao jogador.
        Adicionado para demonstração das páginas de inventário.
        """
        print("DEBUG: [PlayerDashboard] Adicionando cartas iniciais de demonstração...")
        
        # Usar a detecção automática para Raspberry Pi e desenvolvimento local
        base_path = detect_player_inventory_base_dir()
        print(f"DEBUG: [add_starter_cards] Base path detectado: {base_path}")
        print(f"DEBUG: [add_starter_cards] Player color: {self.player_color}")
        
        # Exemplo: dar 2-3 cartas de cada tipo da cor do jogador
        card_types = {
            "users": "Users",
            "equipments": "Equipments", 
            "services": "Services",
            "activities": "Activities"
        }
        
        color_variants = []
        if self.player_color == "blue":
            color_variants = ["Blue", "blue", "BLUE"]
        elif self.player_color == "green": 
            color_variants = ["Green", "green", "GREEN"]
        elif self.player_color == "red":
            color_variants = ["Red", "red", "RED"]
        elif self.player_color == "yellow":
            color_variants = ["Yellow", "yellow", "YELLOW"]
        else:
            color_variants = ["Blue", "blue"]  # default
        
        for card_type, folder_name in card_types.items():
            print(f"DEBUG: [add_starter_cards] Processando tipo: {card_type} -> pasta: {folder_name}")
            cards_found = False
            for color_var in color_variants:
                # Tentar estrutura do desenvolvimento local: NetMaster/Users/Residential-level/Red/
                path1 = os.path.join(base_path, folder_name, "Residential-level", color_var)
                # Tentar estrutura do Raspberry Pi: /img/cartas/users/Residential-level/Red/
                path2 = os.path.join(base_path, card_type, "Residential-level", color_var)
                
                for path_attempt, path_name in [(path1, "estrutura local"), (path2, "estrutura Raspberry Pi")]:
                    print(f"DEBUG: [add_starter_cards] Tentando {path_name}: {path_attempt}")
                    print(f"DEBUG: [add_starter_cards] Caminho existe? {os.path.exists(path_attempt)}")
                    if os.path.exists(path_attempt):
                        try:
                            files_in_path = os.listdir(path_attempt)
                            print(f"DEBUG: [add_starter_cards] Arquivos encontrados: {files_in_path}")
                            card_files = [os.path.join(path_attempt, f) for f in files_in_path 
                                        if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                            print(f"DEBUG: [add_starter_cards] Arquivos de carta filtrados: {[os.path.basename(f) for f in card_files]}")
                            if card_files:
                                # Adicionar 2-3 cartas de cada tipo para demonstração
                                max_cards = min(3, len(card_files))
                                print(f"DEBUG: [add_starter_cards] Adicionando {max_cards} cartas de {card_type}")
                                for i in range(max_cards):
                                    self.inventario[card_type].append(card_files[i])
                                    print(f"DEBUG: [PlayerDashboard] Carta inicial adicionada: {os.path.basename(card_files[i])} ({card_type})")
                                cards_found = True
                                break
                            else:
                                print(f"DEBUG: [add_starter_cards] Nenhum arquivo de carta encontrado em {path_attempt}")
                        except Exception as e:
                            print(f"DEBUG: [add_starter_cards] Erro ao listar arquivos em {path_attempt}: {e}")
                            continue
                    else:
                        print(f"DEBUG: [add_starter_cards] Caminho não existe: {path_attempt}")
                
                if cards_found:
                    break
            
            if not cards_found:
                print(f"DEBUG: [add_starter_cards] NENHUMA ESTRUTURA FUNCIONOU para {card_type}")
        
        # Adicionar algumas cartas neutras (challenges, actions, events)
        print("DEBUG: [add_starter_cards] Processando cartas neutras...")
        neutral_types = {
            "challenges": "Challenges",
            "actions": "Actions", 
            "events": "Events"
        }
        
        for card_type, folder_name in neutral_types.items():
            # Tentar estrutura do desenvolvimento local: NetMaster/Challenges/Residential-level/
            path1 = os.path.join(base_path, folder_name, "Residential-level")
            # Tentar estrutura do Raspberry Pi: /img/cartas/challenges/Residential-level/
            path2 = os.path.join(base_path, card_type, "Residential-level")
            
            print(f"DEBUG: [add_starter_cards] Processando tipo neutro: {card_type} -> pasta: {folder_name}")
            cards_found = False
            
            for path_attempt, path_name in [(path1, "estrutura local"), (path2, "estrutura Raspberry Pi")]:
                print(f"DEBUG: [add_starter_cards] Tentando {path_name}: {path_attempt}")
                print(f"DEBUG: [add_starter_cards] Caminho neutro existe? {os.path.exists(path_attempt)}")
                if os.path.exists(path_attempt):
                    try:
                        files_in_path = os.listdir(path_attempt)
                        print(f"DEBUG: [add_starter_cards] Arquivos neutros encontrados: {files_in_path}")
                        card_files = [os.path.join(path_attempt, f) for f in files_in_path 
                                    if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                        print(f"DEBUG: [add_starter_cards] Arquivos de carta neutros filtrados: {[os.path.basename(f) for f in card_files]}")
                        if card_files:
                            # Para actions e events, filtrar apenas cartas válidas para o jogador
                            if card_type in ["actions", "events"] and hasattr(self, 'card_database') and self.card_database:
                                valid_cards = []
                                player_color = self.player_color.lower()
                                
                                for card_file in card_files:
                                    filename = os.path.basename(card_file)
                                    try:
                                        if card_type == "actions":
                                            # Action_1.png -> action_1
                                            match = re.search(r'Action_(\d+)\.', filename)
                                            if match:
                                                card_id = f"action_{match.group(1)}"
                                                card_data = self.card_database.get_action(card_id)
                                                if card_data:
                                                    target = getattr(card_data, 'target', None)
                                                    player_choice = getattr(card_data, 'player_choice', False)
                                                    # Critério de filtragem: target do jogador OU player_choice=True
                                                    if target == player_color or (target is None and player_choice):
                                                        valid_cards.append(card_file)
                                                        print(f"DEBUG: [add_starter_cards] Action VÁLIDA: {filename} (target={target}, player_choice={player_choice})")
                                        elif card_type == "events":
                                            # Event_1.png -> event_1
                                            match = re.search(r'Event_(\d+)\.', filename)
                                            if match:
                                                card_id = f"event_{match.group(1)}"
                                                card_data = self.card_database.get_event(card_id)
                                                if card_data:
                                                    target = getattr(card_data, 'target_player', None)
                                                    player_choice = getattr(card_data, 'player_choice', False)
                                                    # Critério de filtragem: target do jogador OU player_choice=True
                                                    if target == player_color or (target is None and player_choice):
                                                        valid_cards.append(card_file)
                                                        print(f"DEBUG: [add_starter_cards] Event VÁLIDO: {filename} (target_player={target}, player_choice={player_choice})")
                                    except Exception as e:
                                        print(f"DEBUG: [add_starter_cards] Erro ao processar carta {filename}: {e}")
                                
                                card_files = valid_cards
                                print(f"DEBUG: [add_starter_cards] Cartas filtradas para {card_type}: {len(card_files)} válidas de {len(valid_cards)} totais")
                            
                            # Adicionar cartas ao inventário
                            if card_files:
                                if card_type == "events":
                                    max_cards = min(8, len(card_files))  # Mais events para mostrar paginação
                                elif card_type == "actions":
                                    max_cards = min(6, len(card_files))  # Mais actions para variedade
                                else:
                                    max_cards = min(3, len(card_files))
                                
                                print(f"DEBUG: [add_starter_cards] Adicionando {max_cards} cartas neutras de {card_type}")
                                for i in range(max_cards):
                                    self.inventario[card_type].append(card_files[i])
                                    print(f"DEBUG: [PlayerDashboard] Carta inicial neutra adicionada: {os.path.basename(card_files[i])} ({card_type})")
                            else:
                                print(f"DEBUG: [add_starter_cards] Nenhuma carta válida encontrada para {card_type} após filtragem")
                            cards_found = True
                            break
                        else:
                            print(f"DEBUG: [add_starter_cards] Nenhum arquivo de carta neutra encontrado em {path_attempt}")
                    except Exception as e:
                        print(f"DEBUG: [PlayerDashboard] Erro ao carregar carta inicial {card_type}: {e}")
                else:
                    print(f"DEBUG: [add_starter_cards] Caminho neutro não existe: {path_attempt}")
            
            if not cards_found:
                print(f"DEBUG: [add_starter_cards] NENHUMA ESTRUTURA NEUTRA FUNCIONOU para {card_type}")
        
        print(f"DEBUG: [PlayerDashboard] Resumo do inventário após cartas iniciais:")
        for tipo, cartas in self.inventario.items():
            print(f"DEBUG: [PlayerDashboard]   {tipo}: {len(cartas)} cartas")
        
        # Garantir que há cartas suficientes de Actions/Events
        self.add_more_action_event_cards(min_actions=6, min_events=8)
    
    def _get_card_message_size(self, carta_path):
        """
        Extrai o message_size de uma carta Activity ou Challenge usando a base de dados
        """
        try:
            if not self.card_database:
                print("DEBUG: Base de dados não está disponível")
                return 0
            
            # Tentar determinar se é Activity ou Challenge pelo nome do arquivo
            carta_basename = os.path.basename(carta_path).lower()
            print(f"DEBUG: Analisando carta: {carta_basename}")
            
            if "activity" in carta_basename:
                # Extrair ID da carta Activity
                # Assumindo formato Activity_X.png onde X é o número
                import re
                match = re.search(r'activity_(\d+)', carta_basename)
                if match:
                    activity_num = int(match.group(1))
                    # Usar o formato correto da base de dados: activity_X_cor
                    activity_id = f"activity_{activity_num}_{self.player_color.lower()}"
                    print(f"DEBUG: Procurando activity com ID: {activity_id}")
                    
                    activity_card = self.card_database.get_activity(activity_id)
                    if activity_card:
                        print(f"DEBUG: Found activity {activity_id} with message_size: {activity_card.message_size}")
                        return activity_card.message_size
                    else:
                        print(f"DEBUG: Activity {activity_id} não encontrada na base de dados")
                            
            elif "challenge" in carta_basename:
                # Extrair ID da carta Challenge
                import re
                match = re.search(r'challenge_(\d+)', carta_basename)
                if match:
                    challenge_num = int(match.group(1))
                    challenge_id = f"challenge_{challenge_num}"
                    print(f"DEBUG: Procurando challenge com ID: {challenge_id}")
                    
                    challenge_card = self.card_database.get_challenge(challenge_id)
                    if challenge_card:
                        print(f"DEBUG: Found challenge {challenge_id} with message_size: {challenge_card.message_size}")
                        return challenge_card.message_size
                    else:
                        print(f"DEBUG: Challenge {challenge_id} não encontrada na base de dados")
            
            print(f"DEBUG: Could not find message_size for card: {carta_basename}")
            return 0
            
        except Exception as e:
            print(f"DEBUG: Error getting message_size for {carta_path}: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def _select_carousel_card(self, card_index, carta_path):
        """
        Seleciona uma carta no carrossel (primeiro clique) ou abre fullscreen (segundo clique)
        """
        print(f"DEBUG: ===== _select_carousel_card CHAMADA =====")
        print(f"DEBUG: card_index={card_index}, carta_path={os.path.basename(carta_path)}")
        
        # Verificar se é uma carta virada para baixo (não pode ser selecionada)
        if os.path.basename(carta_path).startswith("back_card_"):
            print(f"DEBUG: Carta virada para baixo não pode ser selecionada")
            return
        
        # Verificar se é Activity ou Challenge
        carta_basename = os.path.basename(carta_path).lower()
        if not ("activity" in carta_basename or "challenge" in carta_basename):
            print(f"DEBUG: Carta {carta_basename} não é Activity nem Challenge")
            return
        
        # Se clicar na mesma carta já selecionada, abrir fullscreen
        if (self.selected_carousel_index == card_index and 
            self.selected_carousel_card == carta_path):
            print(f"DEBUG: Segundo clique na carta {card_index} - abrindo fullscreen")
            self.show_card_fullscreen_carrossel(carta_path)
            return
        
        # Primeiro clique: selecionar carta
        print(f"DEBUG: Primeiro clique - Selecionando carta {card_index}: {os.path.basename(carta_path)}")
        
        # Atualizar seleção
        self.selected_carousel_card = carta_path
        self.selected_carousel_index = card_index
        
        # Atualizar destaques visuais
        print(f"DEBUG: Atualizando destaques visuais...")
        self._update_carousel_selection_highlights()
        
        # Atualizar barras de progresso - COM DEBUG ADICIONAL
        print(f"DEBUG: ===== CHAMANDO _update_progress_bars_from_card =====")
        print(f"DEBUG: Caminho da carta: {carta_path}")
        self._update_progress_bars_from_card(carta_path)
        
        # TESTE ADICIONAL: Verificar se as barras realmente foram atualizadas
        if hasattr(self, 'progress_bars') and "To send" in self.progress_bars:
            current_value = self.progress_bars["To send"]["value"]
            print(f"DEBUG: ===== RESULTADO FINAL =====")
            print(f"DEBUG: Valor atual da barra 'To send' após update: {current_value}")
        else:
            print("DEBUG: ===== ERRO CRÍTICO =====")
            print("DEBUG: ERRO - progress_bars não disponíveis após update!")
        print(f"DEBUG: ===== FIM _select_carousel_card =====\n")
    
    def _update_carousel_selection_highlights(self):
        """
        Atualiza os destaques das cartas no carrossel baseado na seleção atual
        """
        if not hasattr(self, 'card_labels') or not self.card_labels:
            return
        
        for i, lbl in enumerate(self.card_labels):
            if i >= len(self.cards):
                continue
                
            try:
                # Testa se o widget ainda é válido
                lbl.winfo_exists()
            except tk.TclError:
                continue
            
            carta_path = self.cards[i]
            is_back_card = os.path.basename(carta_path).startswith("back_card_")
            next_phase_active = getattr(self, '_next_phase_active', False)
            
            # Cor de destaque baseada no estado
            if i == self.selected_carousel_index:
                # Carta selecionada: cor do jogador
                highlight_color = self.bar_color
                border_width = 3
                border_color = self.player_color.lower()
                print(f"DEBUG: Carta {i} destacada com cor do jogador ({self.player_color})")
            elif next_phase_active and is_back_card:
                # Durante Next Phase, verificar se tem User ID para esta posição
                can_select = self._can_access_carousel_position(i)
                if can_select:
                    highlight_color = "#8A2BE2"  # Roxo para cartas que podem ser selecionadas
                    border_width = 3
                    border_color = "#9370DB"
                else:
                    highlight_color = "black"
                    border_width = 0
                    border_color = "black"
            else:
                # Estado normal
                highlight_color = "black"
                border_width = 0
                border_color = "black"
            
            try:
                lbl.config(bg=highlight_color, borderwidth=border_width, relief="solid" if border_width > 0 else "flat",
                          highlightbackground=border_color, highlightcolor=border_color, highlightthickness=border_width)
            except tk.TclError:
                continue
    
    def _update_progress_bars_from_card(self, carta_path):
        """
        Atualiza as barras de progresso com base nos dados da carta selecionada
        """
        try:
            print(f"DEBUG: ===== _update_progress_bars_from_card INICIADA =====")
            print(f"DEBUG: _update_progress_bars_from_card chamada com: {os.path.basename(carta_path)}")
            
            # Verificar se as barras de progresso estão inicializadas
            print(f"DEBUG: Verificando inicialização...")
            print(f"DEBUG: hasattr(self, 'progress_bars'): {hasattr(self, 'progress_bars')}")
            print(f"DEBUG: hasattr(self, 'progress_labels'): {hasattr(self, 'progress_labels')}")
            
            if not hasattr(self, 'progress_bars') or not hasattr(self, 'progress_labels'):
                print("DEBUG: ❌ Barras de progresso não inicializadas")
                return
                
            print(f"DEBUG: ✅ Barras de progresso inicializadas")
            print(f"DEBUG: progress_bars keys: {list(self.progress_bars.keys())}")
            print(f"DEBUG: progress_labels keys: {list(self.progress_labels.keys())}")
                
            # Obter message_size da carta
            print(f"DEBUG: Extraindo message_size...")
            message_size = self._get_card_message_size(carta_path)
            print(f"DEBUG: Message size extraído: {message_size}")
            
            # Verificar se "To send" existe nas barras
            if "To send" not in self.progress_bars:
                print("DEBUG: ❌ 'To send' não encontrado em progress_bars")
                print(f"DEBUG: Chaves disponíveis em progress_bars: {list(self.progress_bars.keys())}")
                return
                
            if "To send" not in self.progress_labels:
                print("DEBUG: ❌ 'To send' não encontrado em progress_labels")
                print(f"DEBUG: Chaves disponíveis em progress_labels: {list(self.progress_labels.keys())}")
                return
            
            print(f"DEBUG: ✅ 'To send' encontrado em ambas as estruturas")
            
            # Atualizar "To send" com lógica de barra cheia inicial
            try:
                print(f"DEBUG: Atualizando 'To send'...")
                
                # Verificar estado atual
                current_value = self.progress_bars["To send"]["value"]
                current_max = self.progress_bars["To send"]["maximum"]
                current_label = self.progress_labels["To send"]["text"]
                
                print(f"DEBUG: Estado atual - value: {current_value}, max: {current_max}, label: '{current_label}'")
                
                # NOVA LÓGICA: Máximo = message_size, Valor inicial = message_size (barra cheia)
                print(f"DEBUG: Configurando barra para message_size={message_size}")
                print(f"DEBUG: - Máximo da barra = {message_size}")
                print(f"DEBUG: - Valor inicial = {message_size} (barra 100% cheia)")
                
                # Definir o máximo da barra como o message_size
                self.progress_bars["To send"]["maximum"] = message_size
                print(f"DEBUG: ✅ Máximo da barra definido para {message_size}")
                
                # Definir o valor inicial como message_size (barra cheia)
                self.progress_bars["To send"]["value"] = message_size
                self.progress_labels["To send"]["text"] = str(message_size)
                
                print(f"DEBUG: ✅ Barra 'To send' configurada:")
                print(f"DEBUG:   - Máximo: {message_size}")
                print(f"DEBUG:   - Valor: {message_size} (100% cheia)")
                print(f"DEBUG:   - Label: '{message_size}'")
                print(f"DEBUG: À medida que pacotes forem enviados, o valor diminuirá de {message_size} para 0")
                
                # Forçar atualização da interface
                print(f"DEBUG: Forçando atualização da interface...")
                self.progress_bars["To send"].update()
                self.progress_labels["To send"].update()
                
                # Verificar se realmente foi atualizado
                final_value = self.progress_bars["To send"]["value"]
                final_max = self.progress_bars["To send"]["maximum"]
                final_label = self.progress_labels["To send"]["text"]
                print(f"DEBUG: ===== VERIFICAÇÃO FINAL =====")
                print(f"DEBUG: Máximo final da barra: {final_max}")
                print(f"DEBUG: Valor final da barra: {final_value}")
                print(f"DEBUG: Texto final do label: '{final_label}'")
                print(f"DEBUG: Percentagem da barra: {(final_value/final_max)*100:.1f}%")
                
                if final_value == message_size and final_max == message_size and final_label == str(message_size):
                    print(f"DEBUG: ✅ SUCESSO - Barra configurada corretamente!")
                    print(f"DEBUG: Barra está 100% cheia e pronta para diminuir à medida que pacotes são enviados")
                else:
                    print(f"DEBUG: ❌ ERRO - Configuração incorreta!")
                    print(f"DEBUG: Esperado: max={message_size}, value={message_size}, label='{message_size}'")
                    print(f"DEBUG: Obtido: max={final_max}, value={final_value}, label='{final_label}'")
                
            except Exception as update_error:
                print(f"DEBUG: ❌ Erro ao configurar progress bar: {update_error}")
                import traceback
                traceback.print_exc()
            
            # Manter outros valores como estão (por enquanto)
            # "Rxd" e "Lost" podem ser atualizados conforme a lógica do jogo
            
        except Exception as e:
            print(f"DEBUG: ❌ Erro geral ao atualizar barras de progresso: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"DEBUG: ===== _update_progress_bars_from_card TERMINADA =====\n")

    def decrement_to_send_progress(self, packets_sent=1):
        """
        Decrementa a barra 'To send' quando pacotes são enviados.
        Esta função deve ser chamada pelo sistema de jogo quando pacotes são efetivamente enviados.
        
        Args:
            packets_sent (int): Número de pacotes enviados (default: 1)
        """
        try:
            if not hasattr(self, 'progress_bars') or "To send" not in self.progress_bars:
                print("DEBUG: Barra 'To send' não disponível para decremento")
                return
            
            current_value = self.progress_bars["To send"]["value"]
            new_value = max(0, current_value - packets_sent)  # Não pode ser negativo
            
            print(f"DEBUG: Decrementando 'To send': {current_value} - {packets_sent} = {new_value}")
            
            # Atualizar barra e label
            self.progress_bars["To send"]["value"] = new_value
            self.progress_labels["To send"]["text"] = str(new_value)
            
            # Forçar atualização da interface
            self.progress_bars["To send"].update()
            self.progress_labels["To send"].update()
            
            # Verificar se todos os pacotes foram enviados
            if new_value == 0:
                print("DEBUG: ✅ Todos os pacotes da mensagem foram enviados! Barra vazia.")
            else:
                percentage = (new_value / self.progress_bars["To send"]["maximum"]) * 100
                print(f"DEBUG: Restam {new_value} pacotes para enviar ({percentage:.1f}% da barra)")
                
        except Exception as e:
            print(f"DEBUG: Erro ao decrementar barra 'To send': {e}")
            import traceback
            traceback.print_exc()

    def _extrair_valor_venda_carta(self, carta_path):
        """
        Extrai o valor de venda da carta usando a base de dados integrada
        Similar ao _extrair_valor_carta do Store_v2.py mas retorna sell_cost
        """
        if not self.card_database:
            print("DEBUG: Base de dados não disponível, usando extração por nome de arquivo")
            return self._extrair_valor_fallback(carta_path)
        
        try:
            # Determinar tipo da carta pelo caminho
            carta_tipo = self._get_card_type_from_path(carta_path)
            if not carta_tipo:
                print(f"DEBUG: Tipo de carta não identificado para: {carta_path}")
                return self._extrair_valor_fallback(carta_path)
            
            # Mapear arquivo para ID da base de dados
            card_id = self._map_file_to_card_id(carta_path, carta_tipo)
            if not card_id:
                print(f"DEBUG: ID da carta não mapeado para: {carta_path}")
                return self._extrair_valor_fallback(carta_path)
            
            # Obter carta da base de dados
            if carta_tipo == "users":
                card = self.card_database.get_user(card_id)
                valor = card.sell_cost if card else None
            elif carta_tipo == "equipments":
                card = self.card_database.get_equipment(card_id)
                valor = card.sell_cost if card else None
            elif carta_tipo == "services":
                card = self.card_database.get_service(card_id)
                valor = card.sell_cost if card else None
            elif carta_tipo == "activities":
                card = self.card_database.get_activity(card_id)
                valor = card.sell_cost if card else None  # Activities têm sell_cost = 0
            else:
                print(f"DEBUG: Tipo de carta não suportado para venda: {carta_tipo}")
                return self._extrair_valor_fallback(carta_path)
            
            if valor is not None:
                print(f"DEBUG: Valor de venda encontrado na base de dados: {valor} para {card_id}")
                return valor
            else:
                print(f"DEBUG: Carta não encontrada na base de dados: {card_id}")
                return self._extrair_valor_fallback(carta_path)
                
        except Exception as e:
            print(f"DEBUG: Erro ao extrair valor da base de dados: {e}")
            return self._extrair_valor_fallback(carta_path)
    
    def _extrair_valor_fallback(self, carta_path):
        """Método fallback para extrair valor do nome do arquivo"""
        try:
            import re
            nome = os.path.basename(carta_path)
            match = re.search(r'_(\d+)\.', nome)
            if match:
                valor = int(match.group(1))
                print(f"DEBUG: Valor extraído por fallback: {valor}")
                return valor
        except Exception as e:
            print(f"DEBUG: Erro no fallback: {e}")
        return 1  # Valor padrão
    
    def _get_card_type_from_path(self, carta_path):
        """Determina o tipo da carta pelo caminho"""
        path_lower = carta_path.lower()
        if "/users/" in path_lower or "user_" in os.path.basename(path_lower):
            return "users"
        elif "/equipments/" in path_lower or "equipment_" in os.path.basename(path_lower):
            return "equipments"
        elif "/services/" in path_lower or "service_" in os.path.basename(path_lower):
            return "services"
        elif "/activities/" in path_lower or "activity_" in os.path.basename(path_lower):
            return "activities"
        return None
    
    def _map_file_to_card_id(self, carta_path, carta_tipo):
        """Mapeia arquivo para ID da base de dados"""
        nome = os.path.basename(carta_path)
        cor = self._get_color_from_path(carta_path)
        
        if carta_tipo == "users":
            # User_1.png -> contract_red, User_2.png -> 1_red, User_3.png -> 2_red, etc.
            match = re.search(r'User_(\d+)\.', nome)
            if match:
                user_num = int(match.group(1))
                if user_num == 1:  # User_1.png = Residential Contract
                    return f"contract_{cor}"
                elif user_num >= 2:  # User_2.png = user ID 1, User_3.png = user ID 2, etc.
                    return f"{user_num - 1}_{cor}"
        
        elif carta_tipo == "equipments":
            # Equipment_1.png -> small_router_1_red, etc.
            match = re.search(r'Equipment_(\d+)\.', nome)
            if match:
                eq_num = int(match.group(1))
                if 1 <= eq_num <= 3:
                    return f"small_router_{eq_num}_{cor}"
                elif 4 <= eq_num <= 6:
                    return f"medium_router_{eq_num - 3}_{cor}"
                elif 7 <= eq_num <= 9:
                    return f"short_link_{eq_num - 6}_{cor}"
                elif 10 <= eq_num <= 12:
                    return f"long_link_{eq_num - 9}_{cor}"
        
        elif carta_tipo == "services":
            # Service_1.png -> service_bandwidth_1_red, etc.
            match = re.search(r'Service_(\d+)\.', nome)
            if match:
                service_num = int(match.group(1))
                if service_num == 1:
                    return f"service_bandwidth_1_{cor}"
                elif 2 <= service_num <= 4:
                    return f"service_data_volume_{service_num}_{cor}"
                elif 5 <= service_num <= 7:
                    return f"service_temporary_{service_num}_{cor}"
        
        elif carta_tipo == "activities":
            # Activity_1.png -> activity_1_red, etc.
            match = re.search(r'Activity_(\d+)\.', nome)
            if match:
                activity_num = int(match.group(1))
                return f"activity_{activity_num}_{cor}"
        
        return None
    
    def _get_color_from_path(self, carta_path):
        """Extrai a cor do caminho da carta"""
        path_lower = carta_path.lower()
        if "/red/" in path_lower or "-red" in path_lower:
            return "red"
        elif "/blue/" in path_lower or "-blue" in path_lower:
            return "blue"
        elif "/green/" in path_lower or "-green" in path_lower:
            return "green"
        elif "/yellow/" in path_lower or "-yellow" in path_lower:
            return "yellow"
        return "red"  # Padrão
        
    # Cargas de cartas usando a nova estrutura: [tipo]/Residential-level/[cor]/
    def load_cards_from_new_structure(self, card_type, player_color):
            """Carrega cartas da nova estrutura de pastas"""
            cards = []
            
            # Mapear tipo para nome da pasta
            folder_mapping = {
                "users": "Users",
                "equipments": "Equipments", 
                "services": "Services",
                "activities": "Activities",
                "challenges": "Challenges",
                "actions": "Actions",
                "events": "Events"
            }
            
            folder_name = folder_mapping.get(card_type, card_type)
            
            # Para cartas que têm cores específicas (equipments, services, users, activities)
            if card_type in ["equipments", "services", "users", "activities"]:
                # Mapear cor do jogador para diferentes formatos de nome
                color_variants = []
                if player_color == "blue":
                    color_variants = ["Blue", "blue", "BLUE"]
                elif player_color == "green": 
                    color_variants = ["Green", "green", "GREEN"]
                elif player_color == "red":
                    color_variants = ["Red", "red", "RED"]
                elif player_color == "yellow":
                    color_variants = ["Yellow", "yellow", "YELLOW"]
                else:
                    color_variants = ["Blue", "blue"]  # default
                
                # Tentar encontrar cartas na estrutura: [tipo]/Residential-level/[cor]/
                for color_var in color_variants:
                    path = os.path.join(CARTAS_BASE_DIR, folder_name, "Residential-level", color_var)
                    if os.path.exists(path):
                        try:
                            card_files = [os.path.join(path, f) for f in os.listdir(path) 
                                        if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                            if card_files:
                                cards.extend(card_files)
                                print(f"DEBUG: Encontradas {len(card_files)} cartas {card_type} em {path}")
                                break  # Para no primeiro caminho que funcionar
                        except Exception as e:
                            continue
            else:
                # Para cartas sem cor específica (challenges, events, actions)
                path = os.path.join(CARTAS_BASE_DIR, folder_name, "Residential-level")
                if os.path.exists(path):
                    try:
                        card_files = [os.path.join(path, f) for f in os.listdir(path) 
                                    if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                        if card_files:
                            cards.extend(card_files)
                            print(f"DEBUG: Encontradas {len(card_files)} cartas {card_type} em {path}")
                    except Exception as e:
                        print(f"DEBUG: Erro ao carregar {card_type}: {e}")
            
            return cards

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
            if hasattr(self, 'topbar_label') and widget == self.topbar_label:
                continue
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
                        
                        # Atualizar variáveis da casa atual para o botão Store
                        self.current_casa_tipo = tipo
                        self.current_casa_cor = casa_cor
                        # Verificar se é casa de outro jogador
                        self.current_other_player_house = (casa_cor != self.player_color.lower() and casa_cor != "neutral")

                        # IMPORTANTE: Reativar botão Store se não for casa Actions/Events/Challenges neutra
                        if not (tipo in ["actions", "events", "challenges"] and casa_cor == "neutral"):
                            self.enable_store_button()
                            print(f"DEBUG: Botão Store reativado - mudou para casa {tipo} {casa_cor}")

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
                                
                                # VERIFICAR SE É CASA START - vai diretamente para interface principal
                                if tipo == "start":
                                    print("DEBUG: [depois_nome] Casa START detectada - indo para interface principal do PlayerDashboard")
                                    # Marcar que está numa casa start (sem botão Store e sem vendas)
                                    self.current_casa_tipo = "start"
                                    self.current_casa_cor = "neutral"
                                    self.current_other_player_house = False
                                    
                                    # IMPORTANTE: Reativar botão Store na casa START (não é Actions/Events neutra)
                                    self.enable_store_button()
                                    print("DEBUG: Botão Store reativado - está na casa START")
                                    
                                    # Ir diretamente para a interface principal sem botão Store
                                    center_frame.destroy()
                                    self.playerdashboard_interface(player_name, saldo, self.other_players, show_store_button=False)
                                    return
                                
                                # VERIFICAR se já existe uma Store antes de criar nova
                                if (hasattr(self, 'store_window') and self.store_window and 
                                    hasattr(self.store_window, 'winfo_exists') and self.store_window.winfo_exists()):
                                    print("DEBUG: [depois_nome] Store já existe, a reutilizar existente")
                                    print(f"DEBUG: [depois_nome] ID da Store existente: {id(self.store_window)}")
                                    print(f"DEBUG: [depois_nome] Estado fullscreen da Store existente: {getattr(self.store_window, 'fullscreen_carta_path', 'NOT_SET')}")
                                    # Restaurar Store existente em vez de criar nova
                                    self.store_window.deiconify()
                                    self.store_window.state('normal')
                                    self.store_window.lift()
                                    self.store_window.focus_force()
                                    return
                                
                                if casa_cor == self.player_color.lower() or casa_cor == "neutral":
                                    # Casa própria ou neutra - Store normal
                                    print("DEBUG: [depois_nome] Criando nova Store para casa própria/neutra")
                                    self.store_window = StoreWindow(self, self.player_color, player_name, saldo, casa_tipo=tipo, casa_cor=casa_cor, inventario=self.inventario, dashboard=self)
                                    print(f"DEBUG: [depois_nome] Nova Store criada com ID: {id(self.store_window)}")
                                    if hasattr(self.store_window, '_store_id'):
                                        print(f"DEBUG: [depois_nome] Store ID único: {self.store_window._store_id}")
                                else:
                                    # Casa de outro jogador - mostra mensagem e depois Store apenas para venda
                                    other_player_lbl = tk.Label(center_frame, text="Square of other player", font=("Helvetica", 18, "bold"), fg="white", bg="black")
                                    other_player_lbl.pack(pady=10)
                                    
                                    def abrir_store_outro_jogador():
                                        other_player_lbl.pack_forget()
                                        
                                        # VERIFICAR se já existe uma Store antes de criar nova (também para outro jogador)
                                        if (hasattr(self, 'store_window') and self.store_window and 
                                            hasattr(self.store_window, 'winfo_exists') and self.store_window.winfo_exists()):
                                            print("DEBUG: [abrir_store_outro_jogador] Store já existe, a reutilizar existente")
                                            # Restaurar Store existente em vez de criar nova
                                            self.store_window.deiconify()
                                            self.store_window.state('normal')
                                            self.store_window.lift()
                                            self.store_window.focus_force()
                                            center_frame.destroy()
                                            return
                                        
                                        # Para casa de outro jogador, sempre abre a Store mas com restrições
                                        print("DEBUG: [abrir_store_outro_jogador] Criando nova Store para casa de outro jogador")
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
        
        # Limpar seleção do carrossel quando atualiza
        self.selected_carousel_card = None
        self.selected_carousel_index = None
        
        # Atualizar destaques
        if hasattr(self, 'card_labels') and self.card_labels:
            self._update_carousel_selection_highlights()

    def disable_store_button(self):
        """Desativa o botão Store permanentemente até ser reativado"""
        self._store_button_disabled = True
        print("DEBUG: [PlayerDashboard] Botão Store desativado")

    def enable_store_button(self):
        """Reativa o botão Store"""
        self._store_button_disabled = False
        print("DEBUG: [PlayerDashboard] Botão Store reativado")

    def playerdashboard_interface(self, player_name, saldo, other_players, show_store_button=None):
        print(f"DEBUG: [INTERFACE] *** playerdashboard_interface CHAMADA ***")
        print(f"DEBUG: [INTERFACE] player_name: {player_name}, saldo: {saldo}")
        print(f"DEBUG: [INTERFACE] show_store_button: {show_store_button}")
        
        # PROTEÇÃO CONTRA LOOP: Limpar flag quando entra na interface principal
        self._inventory_opening = False
        
        # TESTE: Adicionar User cards para testar o sistema de controlo do carrossel
        # Esta linha pode ser removida em produção
        self._teste_adicionar_user_cards()
        
        # Se show_store_button não for especificado, usar o estado atual
        if show_store_button is None:
            show_store_button = not self._store_button_disabled
        else:
            # Atualizar o estado baseado no parâmetro fornecido
            self._store_button_disabled = not show_store_button
            
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

        # Botão da Store no canto superior direito para ir à Store (apenas se show_store_button for True)
        self._store_btn_widget = None
        if show_store_button and not self._next_phase_active:
            def abrir_store():
                """Abre a Store seguindo o mesmo padrão do botão Player"""
                print("DEBUG: Botão Store pressionado - abrindo Store")
                print(f"DEBUG: [abrir_store] Verificando se Store existe...")
                print(f"DEBUG: [abrir_store] hasattr store_window: {hasattr(self, 'store_window')}")
                if hasattr(self, 'store_window'):
                    print(f"DEBUG: [abrir_store] store_window não é None: {self.store_window is not None}")
                    if self.store_window:
                        print(f"DEBUG: [abrir_store] store_window.winfo_exists(): {hasattr(self.store_window, 'winfo_exists') and self.store_window.winfo_exists()}")
                        print(f"DEBUG: [abrir_store] tem fullscreen_carta_path: {hasattr(self.store_window, 'fullscreen_carta_path')}")
                        if hasattr(self.store_window, 'fullscreen_carta_path'):
                            print(f"DEBUG: [abrir_store] fullscreen_carta_path valor: {getattr(self.store_window, 'fullscreen_carta_path', 'NOT_SET')}")
                
                try:
                    # CORREÇÃO: Verificar PRIMEIRO se há carta Challenge guardada no PlayerDashboard
                    if (hasattr(self, '_store_challenge_carta_path') and self._store_challenge_carta_path and
                        hasattr(self, '_store_challenge_carta_tipo') and self._store_challenge_carta_tipo):
                        print(f"DEBUG: [abrir_store] Carta Challenge encontrada no PlayerDashboard: {self._store_challenge_carta_path}")
                        
                        # Verificar se Store existe e pode ser restaurada
                        if (hasattr(self, 'store_window') and self.store_window and 
                            hasattr(self.store_window, 'winfo_exists') and self.store_window.winfo_exists()):
                            print("DEBUG: [abrir_store] Store existente encontrada - transferindo estado Challenge")
                            # Transferir estado de volta para a Store
                            self.store_window.fullscreen_carta_path = self._store_challenge_carta_path
                            self.store_window.fullscreen_carta_tipo = self._store_challenge_carta_tipo
                            self.store_window._backup_fullscreen_carta_path = self._store_challenge_carta_path
                            self.store_window._backup_fullscreen_carta_tipo = self._store_challenge_carta_tipo
                            self.store_window._original_carta_path = self._store_challenge_carta_path
                            self.store_window._original_carta_tipo = self._store_challenge_carta_tipo
                            
                            # Restaurar Store com carta Challenge
                            self.store_window.voltar_para_store()
                            self.withdraw()
                            
                            # Limpar estado do PlayerDashboard
                            self._store_challenge_carta_path = None
                            self._store_challenge_carta_tipo = None
                            print("DEBUG: [abrir_store] Store restaurada com carta Challenge")
                            return
                        else:
                            print("DEBUG: [abrir_store] Store não existe - criando nova com estado Challenge")
                            # Store não existe, criar nova com estado Challenge já definido
                            # (continua para criação abaixo)
                    
                    # Verificar se já existe uma Store com estado de fullscreen guardado
                    elif (hasattr(self, 'store_window') and self.store_window and 
                        hasattr(self.store_window, 'winfo_exists') and self.store_window.winfo_exists() and
                        hasattr(self.store_window, 'fullscreen_carta_path') and self.store_window.fullscreen_carta_path):
                        print(f"DEBUG: Store existente encontrada com estado fullscreen - restaurando carta: {self.store_window.fullscreen_carta_path}")
                        print(f"DEBUG: [abrir_store] ID da Store existente: {id(self.store_window)}")
                        if hasattr(self.store_window, '_store_id'):
                            print(f"DEBUG: [abrir_store] Store ID único: {self.store_window._store_id}")
                        print(f"DEBUG: [abrir_store] Chamando voltar_para_store() na Store existente...")
                        # Restaurar Store existente com estado de fullscreen
                        self.store_window.voltar_para_store()
                        # Esconder PlayerDashboard enquanto Store está aberta
                        self.withdraw()
                        print("DEBUG: Store existente restaurada com sucesso")
                        return
                    else:
                        # Debug das condições que falharam
                        print("DEBUG: [abrir_store] Condições de Store existente com fullscreen:")
                        print(f"DEBUG: [abrir_store] hasattr(self, 'store_window'): {hasattr(self, 'store_window')}")
                        if hasattr(self, 'store_window'):
                            print(f"DEBUG: [abrir_store] self.store_window is not None: {self.store_window is not None}")
                            if self.store_window:
                                print(f"DEBUG: [abrir_store] store_window.winfo_exists(): {hasattr(self.store_window, 'winfo_exists') and self.store_window.winfo_exists()}")
                                print(f"DEBUG: [abrir_store] tem fullscreen_carta_path attr: {hasattr(self.store_window, 'fullscreen_carta_path')}")
                                if hasattr(self.store_window, 'fullscreen_carta_path'):
                                    print(f"DEBUG: [abrir_store] fullscreen_carta_path value: {self.store_window.fullscreen_carta_path}")
                                    print(f"DEBUG: [abrir_store] fullscreen_carta_path is truthy: {bool(self.store_window.fullscreen_carta_path)}")
                        print("DEBUG: [abrir_store] Store existente NÃO tem estado fullscreen válido - criando nova")
                    
                    # Verificar se existe Store sem estado fullscreen
                    if (hasattr(self, 'store_window') and self.store_window and 
                        hasattr(self.store_window, 'winfo_exists') and self.store_window.winfo_exists()):
                        print("DEBUG: [abrir_store] Store existe mas sem estado fullscreen - reutilizando")
                        self.store_window.voltar_para_store()
                        self.withdraw()
                        return
                    
                    # Importar Store aqui para evitar imports circulares
                    from Store_v2 import StoreWindow
                    # Usar as mesmas informações da casa atual (se disponível)
                    casa_tipo = getattr(self, 'current_casa_tipo', 'neutral')
                    casa_cor = getattr(self, 'current_casa_cor', 'neutral')
                    current_other_player_house = getattr(self, 'current_other_player_house', False)
                    
                    print(f"DEBUG: Criando nova Store - casa_tipo: {casa_tipo}, casa_cor: {casa_cor}, other_player_house: {current_other_player_house}")
                    
                    # IMPORTANTE: Reativar botão Store se não estiver numa casa Actions/Events/Challenges neutra
                    if not (casa_tipo in ["actions", "events", "challenges"] and casa_cor == "neutral"):
                        self.enable_store_button()
                        print("DEBUG: Botão Store reativado - não está numa casa Actions/Events/Challenges neutra")
                    
                    # Criar nova janela da Store
                    self.store_window = StoreWindow(
                        self.master,
                        self.player_color,
                        self.player_name,
                        self.saldo,
                        casa_tipo=casa_tipo,
                        casa_cor=casa_cor,
                        inventario=self.inventario,
                        dashboard=self,
                        other_player_house=current_other_player_house
                    )
                    print(f"DEBUG: Nova Store criada via botão Store com ID: {id(self.store_window)}")
                    if hasattr(self.store_window, '_store_id'):
                        print(f"DEBUG: Store ID único (botão Store): {self.store_window._store_id}")
                    
                    # CORREÇÃO: Se há carta Challenge guardada, transferir para a nova Store
                    if (hasattr(self, '_store_challenge_carta_path') and self._store_challenge_carta_path and
                        hasattr(self, '_store_challenge_carta_tipo') and self._store_challenge_carta_tipo):
                        print(f"DEBUG: Transferindo estado Challenge para nova Store: {self._store_challenge_carta_path}")
                        self.store_window.fullscreen_carta_path = self._store_challenge_carta_path
                        self.store_window.fullscreen_carta_tipo = self._store_challenge_carta_tipo
                        self.store_window._backup_fullscreen_carta_path = self._store_challenge_carta_path
                        self.store_window._backup_fullscreen_carta_tipo = self._store_challenge_carta_tipo
                        self.store_window._original_carta_path = self._store_challenge_carta_path
                        self.store_window._original_carta_tipo = self._store_challenge_carta_tipo
                        
                        # Limpar estado do PlayerDashboard
                        self._store_challenge_carta_path = None
                        self._store_challenge_carta_tipo = None
                        print("DEBUG: Estado Challenge transferido para nova Store")
                    
                    # Esconder PlayerDashboard enquanto Store está aberta
                    self.withdraw()
                    
                    # Se há estado Challenge, restaurar carta imediatamente
                    if (hasattr(self.store_window, 'fullscreen_carta_path') and self.store_window.fullscreen_carta_path):
                        print("DEBUG: Restaurando carta Challenge na nova Store")
                        self.store_window.voltar_para_store()  # Vai ativar restaurar_carta_fullscreen_pendente()
                    
                    print("DEBUG: Nova Store criada com sucesso")
                except Exception as e:
                    print(f"DEBUG: Erro ao abrir Store: {e}")
                    import traceback
                    traceback.print_exc()

            try:
                # Carregar ícone da Store
                store_icon_path = os.path.join(IMG_DIR, "Store_button_icon.png")
                store_icon_img = ImageTk.PhotoImage(Image.open(store_icon_path).resize((30, 30)))
                self.btn_store = tk.Button(self, image=store_icon_img, bg=self.bar_color, relief="flat", borderwidth=0, 
                                     command=abrir_store, cursor="hand2", activebackground=self.bar_color,
                                     highlightthickness=0)
                self.btn_store.image = store_icon_img  # Manter referência para evitar garbage collection
                self.btn_store.place(x=screen_width-15, y=20, anchor="ne")  # Mesma posição do botão Player na Store
                print("DEBUG: Botão Store criado com ícone Store_button_icon.png")
            except Exception as e:
                print(f"DEBUG: Erro ao carregar Store_button_icon.png: {e}")
                # Fallback para botão de texto se não conseguir carregar a imagem
                self.btn_store = tk.Button(self, text="🏪", font=("Helvetica", 20), bg=self.bar_color, fg="black", 
                                     relief="flat", borderwidth=0, command=abrir_store, cursor="hand2",
                                     activebackground=self.bar_color, activeforeground="black", highlightthickness=0)
                self.btn_store.place(x=screen_width-15, y=20, anchor="ne")
                print("DEBUG: Botão Store criado com ícone de fallback")
        else:
            print("DEBUG: Botão Store ocultado conforme parâmetro show_store_button=False")
            self.btn_store = None  # Inicializar como None quando não é criado

        # --- NOVO LAYOUT ---

        # Espaço extra antes dos botões
        self.after(0, lambda: self.update())  # Garante update do layout antes de calcular altura
        tk.Frame(self, height=5, bg="black").pack()  # reduzido para menos espaço

        # 1. Botões grandes (layout igual ao carrossel)
        btns_frame = tk.Frame(self, bg="black")
        btns_frame.pack(pady=(12, 18))  # Reduz espaço acima, mantém abaixo
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
            # Associar inventário correto - CORREÇÃO: usar default parameter para evitar closure problem
            if inv_key == "actions_events":
                print(f"DEBUG: Configurando botão '{text}' para Actions/Events")
                def actions_events_handler():
                    print(f"DEBUG: *** BOTÃO ACTIONS/EVENTS CLICADO ***")
                    self.show_inventory_matrix(["actions", "events"])
                btn.config(command=actions_events_handler)
            else:
                print(f"DEBUG: Configurando botão '{text}' para tipo '{inv_key}'")
                def handler(tipo_carta=inv_key):
                    print(f"DEBUG: *** BOTÃO {tipo_carta.upper()} CLICADO ***")
                    self.show_inventory_matrix([tipo_carta])
                btn.config(command=handler)

        # 2. Carrossel de cartas (agora abaixo dos botões)
        carousel_frame = tk.Frame(self, bg="black")
        carousel_frame.pack(pady=2)
        cards_container = tk.Frame(carousel_frame, bg="black")
        cards_container.pack()

        card_width, card_height = 85, 120  # Certifique-se que está definido antes

        self.card_labels = []
        for i, carta_path in enumerate(self.cards):
            img = ImageTk.PhotoImage(Image.open(carta_path).resize((card_width, card_height)))
            
            # Durante Next Phase, verificar se esta posição pode ser selecionada
            can_select = True
            highlight_color = "black"  # Cor padrão do fundo
            border_width = 0
            border_color = "black"
            
            if getattr(self, '_next_phase_active', False) and os.path.basename(carta_path).startswith("back_card_"):
                # Durante Next Phase, verificar se tem User ID para esta posição
                can_select = self._can_access_carousel_position(i)
                if can_select:
                    highlight_color = "#8A2BE2"  # Roxo para cartas que podem ser selecionadas
                    border_width = 3
                    border_color = "#9370DB"  # Roxo mais claro para a borda
                    print(f"DEBUG: Carta {i} destacada em roxo - pode ser selecionada")
                else:
                    print(f"DEBUG: Carta {i} sem destaque - não pode ser selecionada")
            
            lbl = tk.Label(cards_container, image=img, bg=highlight_color, cursor="hand2" if can_select else "arrow",
                          borderwidth=border_width, relief="solid", highlightbackground=border_color, highlightcolor=border_color, highlightthickness=border_width)
            lbl.image = img  # type: ignore[attr-defined]
            lbl.grid(row=0, column=i, padx=2, pady=0)
            
            # Se for carta virada para baixo, abre inventário de Activities/Challenges
            if os.path.basename(carta_path).startswith("back_card_"):
                lbl.bind("<Button-1>", lambda e, idx=i: self.abrir_inventario_para_carrossel(idx))
            else:
                # Para Activities/Challenges: primeiro clique seleciona, segundo abre fullscreen
                lbl.bind("<Button-1>", lambda e, idx=i, path=carta_path: self._select_carousel_card(idx, path))
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
            # Barra de progresso - máximo inicial será ajustado dinamicamente
            if stat == "To send":
                # Para "To send", o máximo será definido dinamicamente baseado no message_size da carta selecionada
                bar = ttk.Progressbar(row, orient="horizontal", length=240, mode="determinate", maximum=20)  # Valor inicial, será ajustado
            else:
                # Para "Rxd" e "Lost", manter lógica original
                bar = ttk.Progressbar(row, orient="horizontal", length=240, mode="determinate", maximum=50)
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
        end_turn_btn = tk.Button(self, text="End Turn", font=("Helvetica", 13, "bold"), bg="#808080", fg="black", command=self.end_turn, width=8, height=1)
        end_turn_btn.place(relx=0.5, rely=1, anchor="s")

        # --- BARRA INFERIOR COM IMAGEM ---
        # Adicionar barra inferior com imagem BelowBar_X.png (onde X é a cor do jogador)
        try:
            belowbar_img_path = os.path.join(IMG_DIR, f"BelowBar_{self.player_color.lower()}.png")
            belowbar_img = ImageTk.PhotoImage(Image.open(belowbar_img_path).resize((screen_width, 50)))
            belowbar_label = tk.Label(self, image=belowbar_img, bg="black")
            belowbar_label.image = belowbar_img  # type: ignore[attr-defined]
            belowbar_label.pack(side="bottom", fill="x")
            print(f"DEBUG: Barra inferior BelowBar_{self.player_color.lower()}.png carregada com sucesso")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar BelowBar_{self.player_color.lower()}.png: {e}")
            # Fallback: criar uma barra simples da cor do jogador se a imagem não existir
            belowbar_frame = tk.Frame(self, bg=self.bar_color, height=50)
            belowbar_frame.pack(side="bottom", fill="x")
            belowbar_frame.pack_propagate(False)

        # Saldo no canto inferior direito (sobre a BelowBar) - criado após para ficar por cima
        self.after(100, lambda: self.create_coin_saldo_overlay(screen_width, screen_height, saldo))

        # Botão Next Phase OU Final Phase (cinza) na parte inferior central - criado no final para ficar visível
        # Verificar qual botão mostrar baseado no estado atual
        if getattr(self, '_next_phase_active', False) and not getattr(self, '_final_phase_active', False):
            # Next Phase já foi ativado mas Final Phase ainda não, mostrar botão Final Phase
            def final_phase_action():
                print("DEBUG: Final Phase ativado")
                # Ativar flag Final Phase para bloquear todas as ações de cartas
                self._final_phase_active = True
                print("DEBUG: Final Phase ativado - ativação/desativação de cartas bloqueada")
                
                # Esconder o botão Final Phase
                if hasattr(self, 'final_phase_btn') and self.final_phase_btn:
                    self.final_phase_btn.place_forget()
                    print("DEBUG: Botão Final Phase escondido")
            
            self.final_phase_btn = tk.Button(
                self,
                text="Final Phase",
                font=("Helvetica", 14, "bold"),
                bg="#808080",  # Mesmo cinza do Next Phase
                fg="black",
                command=final_phase_action,
                width=10,
            )
            # Mesma posição do botão Next Phase
            self.final_phase_btn.place(relx=0.5, rely=0.98, anchor="s")
            # Garantir que fica por cima de todos os outros elementos
            self.final_phase_btn.lift()
            print("DEBUG: Botão Final Phase recriado na interface principal")
        elif getattr(self, '_final_phase_active', False):
            # Final Phase já foi ativado, não mostrar nenhum botão de fase
            print("DEBUG: Final Phase ativo - nenhum botão de fase mostrado")
        else:
            # Next Phase ainda não foi ativado, mostrar botão Next Phase
            def next_phase_action():
                # Esconde o botão Store
                if hasattr(self, 'btn_store') and self.btn_store:
                    self.btn_store.place_forget()
                    print("DEBUG: Botão Store escondido")
                # Ativa flag para desativar vendas nas páginas de inventário
                self._next_phase_active = True
                # Atualiza cache dos User IDs para controlo do carrossel
                self._check_user_inventory_for_carousel_access()
                # Atualiza destaques roxos do carrossel
                self._update_carousel_highlights()
                print("DEBUG: Next Phase ativado - Store escondido, vendas desativadas, User IDs verificados e destaques atualizados")
                
                # Esconder o botão Next Phase e criar o botão Final Phase na mesma posição
                if hasattr(self, 'next_phase_btn') and self.next_phase_btn:
                    self.next_phase_btn.place_forget()
                    print("DEBUG: Botão Next Phase escondido")
                
                # Criar botão Final Phase na mesma posição e com mesmo formato
                def final_phase_action():
                    print("DEBUG: Final Phase ativado")
                    # Ativar flag Final Phase para bloquear todas as ações de cartas
                    self._final_phase_active = True
                    print("DEBUG: Final Phase ativado - ativação/desativação de cartas bloqueada")
                    
                    # Esconder o botão Final Phase
                    if hasattr(self, 'final_phase_btn') and self.final_phase_btn:
                        self.final_phase_btn.place_forget()
                        print("DEBUG: Botão Final Phase escondido")
                
                self.final_phase_btn = tk.Button(
                    self,
                    text="Final Phase",
                    font=("Helvetica", 14, "bold"),
                    bg="#808080",  # Mesmo cinza do Next Phase
                    fg="black",
                    command=final_phase_action,
                    width=10,
                )
                # Mesma posição do botão Next Phase
                self.final_phase_btn.place(relx=0.5, rely=0.98, anchor="s")
                # Garantir que fica por cima de todos os outros elementos
                self.final_phase_btn.lift()
                print("DEBUG: Botão Final Phase criado na mesma posição")

            self.next_phase_btn = tk.Button(
                self,
                text="Next Phase",
                font=("Helvetica", 14, "bold"),
                bg="#808080",  # Cinza
                fg="black",
                command=next_phase_action,
                width=10,
            )
            # Posição igual aos botões Back das páginas de inventário
            self.next_phase_btn.place(relx=0.5, rely=0.98, anchor="s")
            # Garantir que fica por cima de todos os outros elementos
            self.next_phase_btn.lift()
            print("DEBUG: Botão Next Phase recriado na interface principal")

        # NOTA: As listas de cartas ativas (active_challenge, active_users, etc.) 
        # já estão inicializadas no __init__ do PlayerDashboard
    
    def create_coin_saldo_overlay(self, screen_width, screen_height, saldo):
        """Cria o overlay do coin e saldo por cima de todos os outros elementos"""
        try:
            coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24,24)))
            coin_lbl = tk.Label(self, image=coin_img, bg=self.bar_color, borderwidth=0)
            coin_lbl.image = coin_img  # type: ignore[attr-defined]
            coin_lbl.place(x=screen_width-100, y=screen_height-45)
            coin_lbl.lift()  # Garante que fica por cima
            
            saldo_lbl = tk.Label(self, text=f"{saldo}", font=("Helvetica", 16, "bold"), bg=self.bar_color, fg="black", borderwidth=0)
            saldo_lbl.place(x=screen_width-70, y=screen_height-45)
            saldo_lbl.lift()  # Garante que fica por cima
        except Exception as e:
            print(f"DEBUG: Erro ao criar overlay coin/saldo: {e}")
    
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
        # IMPORTANTE: Só pode ativar cartas após Next Phase ser ativado
        if not getattr(self, '_next_phase_active', False):
            print(f"DEBUG: Tentativa de ativar carta {card_type} BLOQUEADA - Next Phase não está ativo")
            return
        
        # IMPORTANTE: Não pode ativar cartas após Final Phase ser ativado
        if getattr(self, '_final_phase_active', False):
            print(f"DEBUG: Tentativa de ativar carta {card_type} BLOQUEADA - Final Phase está ativo")
            return
        
        if card_type == "challenge":
            # Só pode haver 1 challenge ativo
            if self.active_challenge:
                self.discard_card(self.active_challenge)
            self.active_challenge = card_path
            self.show_card_active(card_path)
        elif card_type == "user" or card_type == "users":
            # Máximo de 4 users ativos (apenas Users têm limite)
            if card_path not in self.active_users:
                if len(self.active_users) < self.max_users:
                    self.active_users.append(card_path)
                    self.show_card_active(card_path)
                    print(f"DEBUG: User ativado: {os.path.basename(card_path)} ({len(self.active_users)}/{self.max_users})")
                    # IMPORTANTE: Atualizar destaques do carrossel quando User é ativado
                    self._update_carousel_highlights()
                else:
                    # Opcional: feedback ao jogador que já tem 4 users
                    print("Já tens 4 users ativos!")
        elif card_type == "equipment" or card_type == "equipments":
            # SEM LIMITE para equipments após Next Phase
            if card_path not in self.active_equipments:
                self.active_equipments.append(card_path)
                self.show_card_active(card_path)
                print(f"DEBUG: Equipment ativado: {os.path.basename(card_path)} (total: {len(self.active_equipments)})")
        elif card_type == "service" or card_type == "services":
            # SEM LIMITE para services após Next Phase
            if card_path not in self.active_services:
                self.active_services.append(card_path)
                self.show_card_active(card_path)
                print(f"DEBUG: Service ativado: {os.path.basename(card_path)} (total: {len(self.active_services)})")
    
    def is_card_active(self, card_path, card_type):
        """Verifica se uma carta está ativa"""
        if card_type == "challenge":
            return self.active_challenge == card_path
        elif card_type in ["user", "users"]:
            return card_path in self.active_users
        elif card_type in ["equipment", "equipments"]:
            return card_path in self.active_equipments
        elif card_type in ["service", "services"]:
            return card_path in self.active_services
        return False
    
    def deactivate_card(self, card_path, card_type):
        """Desativa uma carta"""
        # IMPORTANTE: Só pode desativar cartas após Next Phase ser ativado
        if not getattr(self, '_next_phase_active', False):
            print(f"DEBUG: Tentativa de desativar carta {card_type} BLOQUEADA - Next Phase não está ativo")
            return
        
        # IMPORTANTE: Não pode desativar cartas após Final Phase ser ativado
        if getattr(self, '_final_phase_active', False):
            print(f"DEBUG: Tentativa de desativar carta {card_type} BLOQUEADA - Final Phase está ativo")
            return
        
        if card_type == "challenge":
            if self.active_challenge == card_path:
                self.active_challenge = None
                print(f"DEBUG: Challenge desativado: {os.path.basename(card_path)}")
        elif card_type in ["user", "users"]:
            if card_path in self.active_users:
                self.active_users.remove(card_path)
                print(f"DEBUG: User desativado: {os.path.basename(card_path)} ({len(self.active_users)}/{self.max_users})")
                # IMPORTANTE: Atualizar destaques do carrossel quando User é desativado
                self._update_carousel_highlights()
        elif card_type in ["equipment", "equipments"]:
            if card_path in self.active_equipments:
                self.active_equipments.remove(card_path)
                print(f"DEBUG: Equipment desativado: {os.path.basename(card_path)} (total: {len(self.active_equipments)})")
        elif card_type in ["service", "services"]:
            if card_path in self.active_services:
                self.active_services.remove(card_path)
                print(f"DEBUG: Service desativado: {os.path.basename(card_path)} (total: {len(self.active_services)})")

    def discard_card(self, card_path):
        # Remove visualmente/desativa o challenge anterior
        pass

    def show_card_active(self, card_path):
        # Atualiza visualmente a carta como ativa
        pass

    def adicionar_carta_inventario(self, carta_path, carta_tipo):
        if carta_tipo in self.inventario:
            self.inventario[carta_tipo].append(carta_path)
            # Se for uma carta User, atualizar destaques do carrossel
            if carta_tipo == "users":
                # Aguardar um momento para garantir que a carta foi adicionada
                self.after(100, self._update_carousel_highlights)

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

        # Se Next Phase estiver ativo, desabilitar vendas nesta página
        if getattr(self, '_next_phase_active', False):
            self._disable_inventory_sales()
    def _disable_inventory_sales(self):
        """Desativa botões ou funcionalidades de venda nas páginas de inventário."""
        # Aqui você pode implementar a lógica para desabilitar/remover botões de venda
        # Exemplo: desabilitar todos os botões de venda se existirem
        for widget in self.winfo_children():
            if isinstance(widget, tk.Button) and getattr(widget, 'is_sell_button', False):
                widget.config(state='disabled')

        # --- BARRA INFERIOR COM IMAGEM ---
        # Adicionar barra inferior com imagem BelowBar_X.png (onde X é a cor do jogador)
        try:
            belowbar_img_path = os.path.join(IMG_DIR, f"BelowBar_{self.player_color.lower()}.png")
            belowbar_img = ImageTk.PhotoImage(Image.open(belowbar_img_path).resize((self.screen_width, 50)))
            belowbar_label = tk.Label(self, image=belowbar_img, bg="black")
            belowbar_label.image = belowbar_img  # type: ignore[attr-defined]
            belowbar_label.pack(side="bottom", fill="x")
            print(f"DEBUG: Barra inferior BelowBar_{self.player_color.lower()}.png carregada na página de inventário")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar BelowBar_{self.player_color.lower()}.png na página de inventário: {e}")
            # Fallback: criar uma barra simples da cor do jogador se a imagem não existir
            belowbar_frame = tk.Frame(self, bg=self.bar_color, height=50)
            belowbar_frame.pack(side="bottom", fill="x")
            belowbar_frame.pack_propagate(False)

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



    def show_inventory_matrix(self, tipos, page=0, back_callback=None):
        # PROTEÇÃO CONTRA LOOP: Marcar que estamos a abrir inventário
        self._inventory_opening = True
        
        print(f"DEBUG: [show_inventory_matrix] *** FUNÇÃO CHAMADA ***")
        print(f"DEBUG: [show_inventory_matrix] Tipos solicitados: {tipos}")
        print(f"DEBUG: [show_inventory_matrix] Page solicitada: {page}")
        print(f"DEBUG: [show_inventory_matrix] Estado COMPLETO do inventário:")
        total_cartas = 0
        for tipo, cartas_list in self.inventario.items():
            print(f"DEBUG: [show_inventory_matrix]   {tipo}: {len(cartas_list)} cartas")
            total_cartas += len(cartas_list)
            if cartas_list:
                for i, carta in enumerate(cartas_list[:5]):  # Mostrar primeiras 5 para debug
                    print(f"DEBUG: [show_inventory_matrix]     {i+1}. {os.path.basename(carta)}")
        print(f"DEBUG: [show_inventory_matrix] Total de cartas no inventário: {total_cartas}")
        
        # Limpa widgets (menos barra superior)
        for widget in self.winfo_children():
            if widget == self.topbar_label:
                continue
            widget.destroy()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        # --- Nome do jogador ---
        name_lbl = tk.Label(self, text=self.player_name, font=("Helvetica", 18, "bold"), bg=self.bar_color, fg="black", borderwidth=0)
        name_lbl.place(relx=0.5, y=25, anchor="n")
        # Título
        if len(tipos) == 1:
            title_str = tipos[0].capitalize()
        elif set(tipos) == set(["actions", "events"]):
            title_str = "Actions / Events"
        elif set(tipos) == set(["activities", "challenges"]):
            title_str = "Activities / Challenges"
        else:
            # Para outros casos, mostrar os tipos separados por /
            title_str = " / ".join([t.capitalize() for t in tipos])
        title = tk.Label(self, text=title_str, font=("Helvetica", 22, "bold"), fg="white", bg="black")
        title.place(relx=0.5, y=65, anchor="n")
        # Verificar se é Actions/Events ou Activities/Challenges para organização especial em colunas
        if set(tipos) == set(["actions", "events"]):
            # Organização especial: Actions na coluna esquerda, Events na coluna direita
            # NOVA FUNCIONALIDADE: Apenas a primeira carta do topo está virada para cima (por ordem de chegada)
            # Manter grid 2x2 com paginação conforme solicitado
            cartas_actions_raw = self.inventario.get("actions", [])
            cartas_events_raw = self.inventario.get("events", [])
            
            # FILTRAR cartas Actions/Events baseado no target e player_choice
            cartas_actions = self._filter_action_event_cards(cartas_actions_raw, "actions")
            cartas_events = self._filter_action_event_cards(cartas_events_raw, "events")
            
            print(f"DEBUG: [show_inventory_matrix] Cartas Actions (antes do filtro): {len(cartas_actions_raw)}")
            print(f"DEBUG: [show_inventory_matrix] Cartas Actions (após filtro): {len(cartas_actions)}")
            print(f"DEBUG: [show_inventory_matrix] Cartas Events (antes do filtro): {len(cartas_events_raw)}")
            print(f"DEBUG: [show_inventory_matrix] Cartas Events (após filtro): {len(cartas_events)}")
            
            # Calcular total de cartas para paginação (2 linhas, 1 carta de cada tipo por linha)
            max_cards = max(len(cartas_actions), len(cartas_events))
            cards_per_page = 2  # 2 linhas, 1 carta de cada tipo por linha
            total_pages = max(1, (max_cards + cards_per_page - 1) // cards_per_page)
            page = max(0, min(page, total_pages - 1))
            start_idx = page * cards_per_page
            end_idx = start_idx + cards_per_page
            
            # Para cada página, decidir quais cartas mostrar:
            # - Página 0: primeira carta de cada tipo (virada para cima) + segunda carta (virada para baixo)
            # - Página 1: terceira carta (virada para baixo) + quarta carta (virada para baixo), etc.
            
            matriz_frame = tk.Frame(self, bg="black")
            matriz_frame.place(relx=0.5, rely=0.5, anchor="center")
            card_w, card_h = 85, 120
            
            # Configurar colunas do grid para manter estrutura 2x2
            matriz_frame.grid_columnconfigure(0, weight=1, minsize=card_w + 16)  # Coluna Actions
            matriz_frame.grid_columnconfigure(1, weight=1, minsize=card_w + 16)  # Coluna Events
            
            # Colocar Actions na coluna da esquerda (col=0)
            actions_to_show = []
            for i in range(start_idx, min(end_idx, len(cartas_actions))):
                actions_to_show.append((i, cartas_actions[i]))
            
            # Determinar posições das cartas Actions baseado no número de cartas a mostrar
            actions_row_counter = 0
            for original_idx, carta_path in actions_to_show:
                try:
                    # Apenas a primeira carta (índice original 0) fica virada para cima
                    if original_idx == 0:
                        # Primeira carta: virada para cima, clicável
                        img = ImageTk.PhotoImage(Image.open(carta_path).resize((card_w, card_h)))
                        cursor_type = "hand2"
                        # Usar função auxiliar para corrigir closure problem
                        def make_click_handler(path, tipos_param):
                            return lambda e: self.show_card_fullscreen_inventory(path, tipos_param, page)
                        click_handler = make_click_handler(carta_path, tipos)
                        print(f"DEBUG: [show_inventory_matrix] Action do topo (virada para cima): {os.path.basename(carta_path)}")
                    else:
                        # Cartas restantes: viradas para baixo, mas clicáveis para visualização
                        img = ImageTk.PhotoImage(Image.open(CARD_IMG).resize((card_w, card_h)))
                        cursor_type = "hand2"
                        # Usar função auxiliar para corrigir closure problem (visualização apenas)
                        def make_view_handler(path, tipos_param):
                            return lambda e: self.show_card_fullscreen_inventory(path, tipos_param, page)
                        click_handler = make_view_handler(carta_path, tipos)
                        print(f"DEBUG: [show_inventory_matrix] Action virada para baixo (posição {original_idx}): {os.path.basename(carta_path)}")
                    
                    carta_lbl = tk.Label(matriz_frame, image=img, bg="black", cursor=cursor_type)
                    carta_lbl.image = img  # type: ignore[attr-defined]
                    carta_lbl.grid(row=actions_row_counter, column=0, padx=8, pady=8)
                    
                    if click_handler:
                        carta_lbl.bind("<Button-1>", click_handler)
                    
                    print(f"DEBUG: [show_inventory_matrix] Action colocada na linha {actions_row_counter}, coluna 0")
                    actions_row_counter += 1
                except Exception as e:
                    print(f"DEBUG: [show_inventory_matrix] Erro ao carregar Action: {e}")
                    continue
            
            # Colocar Events na coluna da direita (col=1)
            events_to_show = []
            for i in range(start_idx, min(end_idx, len(cartas_events))):
                events_to_show.append((i, cartas_events[i]))
            
            # Determinar posições das cartas Events baseado no número de cartas a mostrar
            events_row_counter = 0
            for original_idx, carta_path in events_to_show:
                try:
                    # Apenas a primeira carta (índice original 0) fica virada para cima
                    if original_idx == 0:
                        # Primeira carta: virada para cima, clicável
                        img = ImageTk.PhotoImage(Image.open(carta_path).resize((card_w, card_h)))
                        cursor_type = "hand2"
                        # Usar função auxiliar para corrigir closure problem
                        def make_click_handler_events(path, tipos_param):
                            return lambda e: self.show_card_fullscreen_inventory(path, tipos_param, page)
                        click_handler = make_click_handler_events(carta_path, tipos)
                        print(f"DEBUG: [show_inventory_matrix] Event do topo (virada para cima): {os.path.basename(carta_path)}")
                    else:
                        # Cartas restantes: viradas para baixo, mas clicáveis para visualização
                        img = ImageTk.PhotoImage(Image.open(CARD_IMG).resize((card_w, card_h)))
                        cursor_type = "hand2"
                        # Usar função auxiliar para corrigir closure problem (visualização apenas)
                        def make_view_handler_events(path, tipos_param):
                            return lambda e: self.show_card_fullscreen_inventory(path, tipos_param, page)
                        click_handler = make_view_handler_events(carta_path, tipos)
                        print(f"DEBUG: [show_inventory_matrix] Event virada para baixo (posição {original_idx}): {os.path.basename(carta_path)}")
                    
                    carta_lbl = tk.Label(matriz_frame, image=img, bg="black", cursor=cursor_type)
                    carta_lbl.image = img  # type: ignore[attr-defined]
                    carta_lbl.grid(row=events_row_counter, column=1, padx=8, pady=8)
                    
                    if click_handler:
                        carta_lbl.bind("<Button-1>", click_handler)
                    
                    print(f"DEBUG: [show_inventory_matrix] Event colocado na linha {events_row_counter}, coluna 1")
                    events_row_counter += 1
                except Exception as e:
                    print(f"DEBUG: [show_inventory_matrix] Erro ao carregar Event: {e}")
                    continue
        elif set(tipos) == set(["activities", "challenges"]):
            # Organização especial: Activities na coluna esquerda, Challenges na coluna direita
            # Estrutura igual ao Actions/Events
            cartas_activities = self.inventario.get("activities", [])
            cartas_challenges = self.inventario.get("challenges", [])
            
            print(f"DEBUG: [show_inventory_matrix] Cartas Activities: {len(cartas_activities)}")
            print(f"DEBUG: [show_inventory_matrix] Cartas Challenges: {len(cartas_challenges)}")
            
            # DEBUG: Verificar se as cartas estão nos inventários corretos
            print("DEBUG: [show_inventory_matrix] === VERIFICAÇÃO DE INVENTÁRIOS ===")
            for i, carta in enumerate(cartas_activities[:3]):  # Mostrar primeiras 3 Activities
                basename = os.path.basename(carta)
                print(f"DEBUG: [show_inventory_matrix] Activities[{i}]: {basename}")
                # Verificar se realmente é uma Activity
                if "activity" not in basename.lower() and "activities" not in carta.lower():
                    print(f"DEBUG: [show_inventory_matrix] *** ERRO: {basename} NÃO parece ser uma Activity! ***")
            
            for i, carta in enumerate(cartas_challenges[:3]):  # Mostrar primeiras 3 Challenges
                basename = os.path.basename(carta)
                print(f"DEBUG: [show_inventory_matrix] Challenges[{i}]: {basename}")
                # Verificar se realmente é uma Challenge
                if "challenge" not in basename.lower() and "challenges" not in carta.lower():
                    print(f"DEBUG: [show_inventory_matrix] *** ERRO: {basename} NÃO parece ser uma Challenge! ***")
            print("DEBUG: [show_inventory_matrix] === FIM VERIFICAÇÃO ===")
            
            # Calcular total de cartas para paginação (2 linhas, 1 carta de cada tipo por linha)
            max_cards = max(len(cartas_activities), len(cartas_challenges))
            cards_per_page = 2  # 2 linhas, 1 carta de cada tipo por linha
            total_pages = max(1, (max_cards + cards_per_page - 1) // cards_per_page)
            page = max(0, min(page, total_pages - 1))
            start_idx = page * cards_per_page
            end_idx = start_idx + cards_per_page
            
            matriz_frame = tk.Frame(self, bg="black")
            matriz_frame.place(relx=0.5, rely=0.5, anchor="center")
            card_w, card_h = 85, 120
            
            # Configurar colunas do grid para manter estrutura 2x2
            matriz_frame.grid_columnconfigure(0, weight=1, minsize=card_w + 16)  # Coluna Activities
            matriz_frame.grid_columnconfigure(1, weight=1, minsize=card_w + 16)  # Coluna Challenges
            
            # Colocar Activities na coluna da esquerda (col=0)
            activities_to_show = []
            for i in range(start_idx, min(end_idx, len(cartas_activities))):
                activities_to_show.append((i, cartas_activities[i]))
            
            # Determinar posições das cartas Activities baseado no número de cartas a mostrar
            activities_row_counter = 0
            for original_idx, carta_path in activities_to_show:
                try:
                    img = ImageTk.PhotoImage(Image.open(carta_path).resize((card_w, card_h)))
                    cursor_type = "hand2"
                    # Usar função auxiliar para corrigir closure problem
                    def make_click_handler_activities(path, tipos_param):
                        return lambda e: self.show_card_fullscreen_inventory(path, tipos_param, page)
                    click_handler = make_click_handler_activities(carta_path, tipos)
                    print(f"DEBUG: [show_inventory_matrix] Activity COLUNA ESQUERDA (col=0): {os.path.basename(carta_path)}")
                    
                    carta_lbl = tk.Label(matriz_frame, image=img, bg="black", cursor=cursor_type)
                    carta_lbl.image = img  # type: ignore[attr-defined]
                    carta_lbl.grid(row=activities_row_counter, column=0, padx=8, pady=8)
                    
                    if click_handler:
                        carta_lbl.bind("<Button-1>", click_handler)
                    
                    print(f"DEBUG: [show_inventory_matrix] Activity colocada na linha {activities_row_counter}, coluna 0 (ESQUERDA)")
                    activities_row_counter += 1
                except Exception as e:
                    print(f"DEBUG: [show_inventory_matrix] Erro ao carregar Activity: {e}")
                    continue
            
            # Colocar Challenges na coluna da direita (col=1)
            challenges_to_show = []
            for i in range(start_idx, min(end_idx, len(cartas_challenges))):
                challenges_to_show.append((i, cartas_challenges[i]))
            
            # Determinar posições das cartas Challenges baseado no número de cartas a mostrar
            challenges_row_counter = 0
            for original_idx, carta_path in challenges_to_show:
                try:
                    img = ImageTk.PhotoImage(Image.open(carta_path).resize((card_w, card_h)))
                    cursor_type = "hand2"
                    # Usar função auxiliar para corrigir closure problem
                    def make_click_handler_challenges(path, tipos_param):
                        return lambda e: self.show_card_fullscreen_inventory(path, tipos_param, page)
                    click_handler = make_click_handler_challenges(carta_path, tipos)
                    print(f"DEBUG: [show_inventory_matrix] Challenge COLUNA DIREITA (col=1): {os.path.basename(carta_path)}")
                    
                    carta_lbl = tk.Label(matriz_frame, image=img, bg="black", cursor=cursor_type)
                    carta_lbl.image = img  # type: ignore[attr-defined]
                    carta_lbl.grid(row=challenges_row_counter, column=1, padx=8, pady=8)
                    
                    if click_handler:
                        carta_lbl.bind("<Button-1>", click_handler)
                    
                    print(f"DEBUG: [show_inventory_matrix] Challenge colocado na linha {challenges_row_counter}, coluna 1 (DIREITA)")
                    challenges_row_counter += 1
                except Exception as e:
                    print(f"DEBUG: [show_inventory_matrix] Erro ao carregar Challenge: {e}")
                    continue
        else:
            # Organização normal para outros tipos
            cartas = []
            for t in tipos:
                cartas_tipo = self.inventario.get(t, [])
                print(f"DEBUG: [show_inventory_matrix] Cartas de {t}: {len(cartas_tipo)}")
                cartas += cartas_tipo
            
            print(f"DEBUG: [show_inventory_matrix] Total de cartas a mostrar: {len(cartas)}")
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
                    # Determinar o tipo da carta para verificar se está ativa
                    carta_tipo = None
                    if len(tipos) == 1:
                        carta_tipo = tipos[0]
                    else:
                        # Se são múltiplos tipos, tentar determinar pelo caminho da carta
                        path_lower = carta_path.lower()
                        if "/users/" in path_lower or "user_" in os.path.basename(path_lower):
                            carta_tipo = "users"
                        elif "/equipments/" in path_lower or "equipment_" in os.path.basename(path_lower):
                            carta_tipo = "equipments"
                        elif "/services/" in path_lower or "service_" in os.path.basename(path_lower):
                            carta_tipo = "services"
                    
                    # Verificar se a carta está ativa para Users/Equipments/Services
                    # IMPORTANTE: Só verificar estado ativo após Next Phase ser ativado
                    is_active = False
                    next_phase_active = getattr(self, '_next_phase_active', False)
                    if carta_tipo in ["users", "equipments", "services"] and next_phase_active:
                        is_active = self.is_card_active(carta_path, carta_tipo)
                    
                    # Escolher imagem baseada no estado da carta
                    if carta_tipo in ["users", "equipments", "services"]:
                        # Verificar se é User_1.png - sempre virada para cima
                        is_user_1 = (carta_tipo == "users" and "User_1.png" in os.path.basename(carta_path))
                        
                        if is_user_1:
                            # User_1.png sempre virada para cima
                            img = ImageTk.PhotoImage(Image.open(carta_path).resize((card_w, card_h)))
                            print(f"DEBUG: [show_inventory_matrix] User_1.png SEMPRE virada para cima: {os.path.basename(carta_path)}")
                        elif next_phase_active and is_active:
                            # Carta ativa: mostrar virada para cima (APENAS após Next Phase)
                            img = ImageTk.PhotoImage(Image.open(carta_path).resize((card_w, card_h)))
                            print(f"DEBUG: [show_inventory_matrix] Carta {carta_tipo} ATIVA (virada para cima): {os.path.basename(carta_path)}")
                        else:
                            # Carta inativa OU antes do Next Phase: mostrar virada para baixo
                            img = ImageTk.PhotoImage(Image.open(CARD_IMG).resize((card_w, card_h)))
                            if next_phase_active:
                                print(f"DEBUG: [show_inventory_matrix] Carta {carta_tipo} INATIVA (virada para baixo): {os.path.basename(carta_path)}")
                            else:
                                print(f"DEBUG: [show_inventory_matrix] Carta {carta_tipo} PRÉ-NEXT PHASE (virada para baixo): {os.path.basename(carta_path)}")
                    else:
                        # Para outros tipos (activities, etc), mostrar normalmente
                        img = ImageTk.PhotoImage(Image.open(carta_path).resize((card_w, card_h)))
                        print(f"DEBUG: [show_inventory_matrix] Carta {carta_tipo} normal: {os.path.basename(carta_path)}")
                        
                except Exception:
                    continue
                carta_lbl = tk.Label(matriz_frame, image=img, bg="black", cursor="hand2")
                carta_lbl.image = img  # type: ignore[attr-defined]
                carta_lbl.grid(row=row, column=col, padx=8, pady=8)
                carta_lbl.bind("<Button-1>", lambda e, p=carta_path, t=tipos, pg=page: self.show_card_fullscreen_inventory(p, t, pg))
        # Setas de navegação à direita
        if total_pages > 1:
            seta_x = 0.90
            if page > 0:
                seta_cima = tk.Button(self, text="▲", font=("Helvetica", 18, "bold"), bg="#222", fg="white", width=2, command=lambda: self.show_inventory_matrix(tipos, page-1, back_callback))
                seta_cima.place(relx=seta_x, rely=0.38, anchor="center")
            if page < total_pages - 1:
                seta_baixo = tk.Button(self, text="▼", font=("Helvetica", 18, "bold"), bg="#222", fg="white", width=2, command=lambda: self.show_inventory_matrix(tipos, page+1, back_callback))
                seta_baixo.place(relx=seta_x, rely=0.62, anchor="center")
        # --- BARRA INFERIOR COM IMAGEM ---
        # Adicionar barra inferior com imagem BelowBar_X.png (onde X é a cor do jogador)
        try:
            bottombar_img_path = os.path.join(IMG_DIR, f"BelowBar_{self.player_color.lower()}.png")
            bottombar_img = ImageTk.PhotoImage(Image.open(bottombar_img_path).resize((self.screen_width, 50)))
            bottombar_label = tk.Label(self, image=bottombar_img, bg="black")
            bottombar_label.image = bottombar_img  # type: ignore[attr-defined]
            bottombar_label.pack(side="bottom", fill="x")
            print(f"DEBUG: Barra inferior BelowBar_{self.player_color.lower()}.png carregada no inventário")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar BelowBar_{self.player_color.lower()}.png no inventário: {e}")
            # Fallback: criar uma barra simples da cor do jogador se a imagem não existir
            bottombar_frame = tk.Frame(self, bg=self.bar_color, height=50)
            bottombar_frame.pack(side="bottom", fill="x")
            bottombar_frame.pack_propagate(False)

        # Botão Back centrado na parte inferior - criado após a barra para ficar por cima
        if back_callback:
            back_btn = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), bg="#808080", fg="white", width=6, command=back_callback)
        else:
            def back_to_dashboard():
                # PROTEÇÃO CONTRA LOOP: Limpar flag antes de voltar ao dashboard
                self._inventory_opening = False
                self.playerdashboard_interface(self.player_name, self.saldo, self.other_players)
            back_btn = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), bg="#808080", fg="white", width=6, command=back_to_dashboard)
        back_btn.place(relx=0.5, rely=0.98, anchor="s")

        # Saldo no canto inferior direito - criado após para ficar por cima
        self.after(100, lambda: self.create_coin_saldo_overlay(screen_width, screen_height, self.saldo))

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
        # Botão X para fechar - movido para canto superior esquerdo
        x_btn = tk.Button(self, text="✖", font=("Helvetica", 24, "bold"), bg="#AAAAAA", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=voltar_inventario, cursor="hand2", activebackground="#CCCCCC")
        x_btn.place(relx=0.02, rely=0, anchor="nw")
        
        # Se for Users, Equipments, Services, Activities ou Challenges, mostrar botão de venda APENAS se estiver numa casa do tipo correspondente
        # Para Activities/Challenges: podem ser vendidas quando estás numa casa Activities
        pode_vender = False
        casa_atual_tipo = getattr(self, 'current_casa_tipo', 'neutral')
        
        # Determinar o tipo da carta atual PRIMEIRO
        carta_tipo = None
        if len(tipos) == 1:
            carta_tipo = tipos[0]
        elif set(tipos) == set(["activities", "challenges"]):
            # Se é uma página Activities/Challenges, determinar tipo pela carta específica
            carta_basename = os.path.basename(carta_path).lower()
            if "activity" in carta_basename or "activities" in carta_basename:
                carta_tipo = "activities"
            elif "challenge" in carta_basename or "challenges" in carta_basename:
                carta_tipo = "challenges"
            else:
                # Tentar determinar pelo caminho da pasta
                carta_dirname = os.path.dirname(carta_path).lower()
                if "activities" in carta_dirname:
                    carta_tipo = "activities"
                elif "challenges" in carta_dirname:
                    carta_tipo = "challenges"
        
        # IMPORTANTE: Se Next Phase estiver ativo, NÃO pode vender nenhuma carta
        if getattr(self, '_next_phase_active', False):
            print(f"DEBUG: NÃO pode vender carta do inventário - Next Phase está ativo (vendas desabilitadas)")
            pode_vender = False
        # IMPORTANTE: Se Final Phase estiver ativo, NÃO pode vender nenhuma carta
        elif getattr(self, '_final_phase_active', False):
            print(f"DEBUG: NÃO pode vender carta do inventário - Final Phase está ativo (vendas desabilitadas)")
            pode_vender = False
        # IMPORTANTE: Se está numa casa START, NÃO pode vender nenhuma carta
        elif casa_atual_tipo == "start":
            print(f"DEBUG: NÃO pode vender carta do inventário - está numa casa START (nenhuma venda permitida)")
            pode_vender = False
        else:
            # Normalizar o tipo da casa atual (equipments vs equipment)
            if casa_atual_tipo == "equipment":
                casa_atual_tipo = "equipments"
            
            print(f"DEBUG: Verificando possibilidade de venda no inventário - carta_tipo: {carta_tipo}, casa_atual_tipo: {casa_atual_tipo}")
            
            # Verificar se pode vender
            if carta_tipo in ["users", "equipments", "services"]:
                # Para estas cartas, precisa estar na casa do mesmo tipo
                if casa_atual_tipo == carta_tipo:
                    pode_vender = True
            elif carta_tipo in ["activities", "challenges"]:
                # Activities só podem ser vendidas numa casa Activities, Challenges só numa casa Challenges
                if casa_atual_tipo == carta_tipo:
                    pode_vender = True
        
        # Botão de venda com checkmark no canto superior direito (substitui o botão verde picoin)
        # APENAS se NÃO for uma carta Activities/Challenges, porque essas têm layout especial
        # IMPORTANTE: User_1.png nunca pode ser vendida
        is_user_1 = (carta_tipo == "users" and "User_1.png" in os.path.basename(carta_path))
        
        if pode_vender and carta_tipo not in ["activities", "challenges"] and not is_user_1:
            print(f"DEBUG: Pode vender carta {carta_tipo} do inventário - está numa casa {casa_atual_tipo}")
            def abrir_confirm():
                # Guardar informações para navegação correta
                self._origem_venda = "inventario"
                self._tipos_venda = None
                self._page_venda = 0
                self.show_sell_confirmation(carta_path, carta_tipo, store_window=None)
            
            # Botão com checkmark (✓) no canto superior direito
            btn_sell = tk.Button(self, text="✓", font=("Helvetica", 24, "bold"), bg="#4CAF50", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=abrir_confirm, cursor="hand2", activebackground="#43d17a")
            btn_sell.place(relx=0.98, rely=0, anchor="ne")
        elif is_user_1:
            print(f"DEBUG: User_1.png NÃO pode ser vendida")
        elif not pode_vender and carta_tipo not in ["activities", "challenges"]:
            print(f"DEBUG: NÃO pode vender carta {carta_tipo} do inventário - casa atual: {casa_atual_tipo}, necessário: activities (para Activities/Challenges) ou {carta_tipo} (para outros tipos)")
        
        # Para Activities e Challenges, layout especial com botões específicos
        # IMPORTANTE: Limpar qualquer estado de venda anterior para garantir comportamento correto
        self._origem_venda = None
        self._tipos_venda = None
        self._page_venda = None
        self._current_sell_page = None
        self._inventario_conjunto = None
        
        if carta_tipo in ["activities", "challenges"]:
            print(f"DEBUG: [FULLSCREEN] Processando carta tipo {carta_tipo} - pode_vender: {pode_vender}")
            print(f"DEBUG: [FULLSCREEN] Casa atual: {getattr(self, 'current_casa_tipo', 'neutral')}")
            print(f"DEBUG: [FULLSCREEN] Next Phase ativo: {getattr(self, '_next_phase_active', False)}")
            
            # Para Activities: botão ✔ abre página de confirmação de venda (se pode vender)
            # Para Challenges: botão ✔ aceita para carrossel (comportamento original)
            if carta_tipo == "activities" and pode_vender:
                # Botão ✔ canto superior direito (para venda)
                btn_certo = tk.Button(self, text="✔", font=("Helvetica", 24, "bold"), bg="#4CAF50", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, cursor="hand2", activebackground="#43d17a")
                btn_certo.place(relx=0.98, rely=0, anchor="ne")
                
                def abrir_confirm_activities():
                    # Limpar estado anterior e guardar informações para navegação correta
                    self._origem_venda = "inventario"
                    # Se viemos de um inventário Activities/Challenges, guardar isso
                    if set(tipos) == set(["activities", "challenges"]):
                        self._tipos_venda = ["activities", "challenges"]
                        self._inventario_conjunto = True
                        print(f"DEBUG: Guardando contexto inventário conjunto Activities/Challenges")
                    else:
                        self._tipos_venda = None
                        self._inventario_conjunto = False
                        print(f"DEBUG: Guardando contexto inventário individual: {carta_tipo}")
                    # Guardar a página atual baseada no parâmetro da função
                    self._page_venda = page
                    self._current_sell_page = page
                    print(f"DEBUG: Iniciando venda Activities - carta_tipo: {carta_tipo}, inventario_conjunto: {getattr(self, '_inventario_conjunto', False)}, page: {page}")
                    self.show_sell_confirmation(carta_path, carta_tipo, store_window=None)
                
                btn_certo.config(command=abrir_confirm_activities)
                print(f"DEBUG: [FULLSCREEN] Botão ✔ configurado para venda de Activities")
            
            elif carta_tipo == "challenges" or (carta_tipo == "activities" and not pode_vender):
                # Botão Switch canto superior direito (para aceitar para carrossel)
                # SÓ APARECE DURANTE NEXT PHASE
                btn_switch_carrossel = None
                next_phase_active = getattr(self, '_next_phase_active', False)
                
                if next_phase_active:
                    try:
                        switch_img_path = os.path.join(IMG_DIR, "switch_card.png")
                        if os.path.exists(switch_img_path):
                            switch_img = ImageTk.PhotoImage(Image.open(switch_img_path).resize((48, 48)))
                            btn_switch_carrossel = tk.Button(self, image=switch_img, bg="#FF9800", borderwidth=0, highlightthickness=0, cursor="hand2", activebackground="#E68900")
                            btn_switch_carrossel.image = switch_img  # Manter referência
                            btn_switch_carrossel.place(relx=0.98, rely=0, anchor="ne")
                            print(f"DEBUG: [FULLSCREEN] Botão Switch carrossel criado durante Next Phase")
                        else:
                            print(f"DEBUG: [FULLSCREEN] Botão Switch carrossel NÃO criado - imagem não encontrada em {switch_img_path}")
                    except Exception as e:
                        btn_switch_carrossel = None
                        print(f"DEBUG: [FULLSCREEN] Botão Switch carrossel NÃO criado - erro ao carregar imagem: {e}")
                else:
                    print(f"DEBUG: [FULLSCREEN] Botão Switch carrossel NÃO criado - Next Phase não está ativo")
                
                # Configurar comando do botão Switch
                def aceitar_carta():
                    # Aceitar carta para o carrossel
                    idx = getattr(self, 'carrossel_idx_selecao', 0)
                    self.cards[idx] = carta_path
                    self.selected_card_idx = idx
                    
                    # Remover carta do inventário
                    if carta_tipo in self.inventario and carta_path in self.inventario[carta_tipo]:
                        self.inventario[carta_tipo].remove(carta_path)
                        print(f"DEBUG: Removida carta {carta_path} do inventário {carta_tipo}")
                    
                    # Voltar à interface principal
                    self.playerdashboard_interface(self.player_name, self.saldo, self.other_players)
                
                if btn_switch_carrossel is not None:
                    btn_switch_carrossel.config(command=aceitar_carta)
                    print(f"DEBUG: [FULLSCREEN] Botão Switch configurado para aceitar {carta_tipo} no carrossel")
            
            # Botão Switch no canto inferior direito (apenas para Activities DURANTE NEXT PHASE)
            if carta_tipo == "activities":
                btn_switch = None
                next_phase_active = getattr(self, '_next_phase_active', False)
                
                if next_phase_active:
                    # Tentar carregar imagem switch_card.png
                    try:
                        switch_img_path = os.path.join(IMG_DIR, "switch_card.png")
                        if os.path.exists(switch_img_path):
                            switch_img = ImageTk.PhotoImage(Image.open(switch_img_path).resize((48, 48)))
                            btn_switch = tk.Button(self, image=switch_img, bg="#FF9800", borderwidth=0, highlightthickness=0, cursor="hand2", activebackground="#E68900")
                            btn_switch.image = switch_img  # Manter referência
                            btn_switch.place(relx=1, rely=1, anchor="se")
                            print(f"DEBUG: [FULLSCREEN] Botão Switch Activities criado durante Next Phase")
                        else:
                            print(f"DEBUG: [FULLSCREEN] Botão Switch Activities NÃO criado - imagem não encontrada em {switch_img_path}")
                    except Exception as e:
                        btn_switch = None
                        print(f"DEBUG: [FULLSCREEN] Botão Switch Activities NÃO criado - erro ao carregar imagem: {e}")
                else:
                    print(f"DEBUG: [FULLSCREEN] Botão Switch Activities NÃO criado - Next Phase não está ativo")
                
                def switch_action():
                    # Aceitar carta para o carrossel (mesmo comportamento do botão ✔ para Challenges)
                    idx = getattr(self, 'carrossel_idx_selecao', 0)
                    self.cards[idx] = carta_path
                    self.selected_card_idx = idx
                    
                    # Remover carta do inventário
                    if carta_tipo in self.inventario and carta_path in self.inventario[carta_tipo]:
                        self.inventario[carta_tipo].remove(carta_path)
                        print(f"DEBUG: Removida carta {carta_path} do inventário {carta_tipo} via Switch")
                    
                    # Voltar à interface principal
                    self.playerdashboard_interface(self.player_name, self.saldo, self.other_players)
                
                if btn_switch is not None:
                    btn_switch.config(command=switch_action)
                    print(f"DEBUG: [FULLSCREEN] Botão Switch configurado para Activities")
        
        # Para Users, Equipments e Services, adicionar botão de ativação/desativação
        # IMPORTANTE: APENAS após Next Phase ser ativado
        elif carta_tipo in ["users", "equipments", "services"]:
            # Verificar se é User_1.png - tratamento especial
            is_user_1 = (carta_tipo == "users" and "User_1.png" in os.path.basename(carta_path))
            
            if is_user_1:
                # Para User_1.png, não criar nenhum botão adicional além do X
                print(f"DEBUG: [FULLSCREEN] User_1.png - sem botões especiais, só o X cinza")
            else:
                next_phase_active = getattr(self, '_next_phase_active', False)
                final_phase_active = getattr(self, '_final_phase_active', False)
                print(f"DEBUG: [FULLSCREEN] Processando carta tipo {carta_tipo} para ativação - Next Phase ativo: {next_phase_active}, Final Phase ativo: {final_phase_active}")
                
                if next_phase_active and not final_phase_active:
                    # Verificar se a carta está ativa
                    is_active = self.is_card_active(carta_path, carta_tipo)
                    
                    if is_active:
                        # Carta ativa: botão para desativar (vermelho com ✔)
                        btn_activate = tk.Button(self, text="✔", font=("Helvetica", 24, "bold"), bg="#F44336", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, cursor="hand2", activebackground="#D32F2F")
                        def desativar_carta():
                            self.show_deactivation_confirmation(carta_path, carta_tipo, tipos, page)
                        btn_activate.config(command=desativar_carta)
                        print(f"DEBUG: [FULLSCREEN] Botão desativar criado para {carta_tipo} ATIVA")
                    else:
                        # Carta inativa: botão para ativar (verde com ✔)
                        btn_activate = tk.Button(self, text="✔", font=("Helvetica", 24, "bold"), bg="#4CAF50", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, cursor="hand2", activebackground="#43d17a")
                        def ativar_carta():
                            self.show_activation_confirmation(carta_path, carta_tipo, tipos, page)
                        btn_activate.config(command=ativar_carta)
                        print(f"DEBUG: [FULLSCREEN] Botão ativar criado para {carta_tipo} INATIVA")
                    
                    # Posicionar o botão no canto superior direito
                    btn_activate.place(relx=0.98, rely=0, anchor="ne")
                    
                else:
                    if final_phase_active:
                        print(f"DEBUG: [FULLSCREEN] Botões de ativação BLOQUEADOS - Final Phase está ativo")
                    else:
                        print(f"DEBUG: [FULLSCREEN] Botões de ativação NÃO criados - Next Phase não está ativo")

    def show_inventory_for_sell(self, carta_tipo, store_window=None, page=0):
        print(f"DEBUG: show_inventory_for_sell chamado - carta_tipo: {carta_tipo}, page: {page}")
        
        # Verificar se o jogador pode vender cartas deste tipo na casa atual
        casa_atual_tipo = getattr(self, 'current_casa_tipo', 'neutral')
        casa_atual_cor = getattr(self, 'current_casa_cor', 'neutral')
        current_other_player_house = getattr(self, 'current_other_player_house', False)
        
        # IMPORTANTE: Se Next Phase estiver ativo, NÃO pode vender nenhuma carta
        if getattr(self, '_next_phase_active', False):
            print(f"DEBUG: NÃO pode vender cartas {carta_tipo} do inventário - Next Phase está ativo (vendas desabilitadas)")
            # Volta à Store ou PlayerDashboard se não pode vender
            if store_window:
                store_window.deiconify()
                store_window.lift()
                store_window.focus_force()
                self.withdraw()
            else:
                self.playerdashboard_interface(self.player_name, self.saldo, self.other_players)
            return
        
        # IMPORTANTE: Se está numa casa START, NÃO pode vender nenhuma carta
        if casa_atual_tipo == "start":
            print(f"DEBUG: NÃO pode vender cartas {carta_tipo} do inventário - está numa casa START (nenhuma venda permitida)")
            # Volta à Store ou PlayerDashboard se não pode vender
            if store_window:
                store_window.deiconify()
                store_window.lift()
                store_window.focus_force()
                self.withdraw()
            else:
                self.playerdashboard_interface(self.player_name, self.saldo, self.other_players)
            return
        
        # Normalizar o tipo da casa atual (equipments vs equipment)
        if casa_atual_tipo == "equipment":
            casa_atual_tipo = "equipments"
        
        # Verificar se pode vender nesta casa (no inventário próprio, qualquer cor serve)
        # Activities só podem ser vendidas numa casa Activities, Challenges só numa casa Challenges
        pode_vender_tipo = False
        if carta_tipo in ["users", "equipments", "services", "activities", "challenges"]:
            pode_vender_tipo = (casa_atual_tipo == carta_tipo)
        
        if not pode_vender_tipo:
            print(f"DEBUG: NÃO pode vender cartas {carta_tipo} do inventário - casa atual: {casa_atual_tipo}, necessário: {carta_tipo}")
            # Volta à Store ou PlayerDashboard se não pode vender
            if store_window:
                store_window.deiconify()
                store_window.lift()
                store_window.focus_force()
                self.withdraw()
            else:
                self.playerdashboard_interface(self.player_name, self.saldo, self.other_players)
            return
        
        print(f"DEBUG: Pode vender cartas {carta_tipo} do inventário - está numa casa {casa_atual_tipo}")
        
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
            if hasattr(self, 'topbar_label') and widget == self.topbar_label:
                continue
            widget.destroy()
        
        # IMPORTANTE: Verificar se a TopBar existe, se não, criá-la
        if not hasattr(self, 'topbar_label') or not self.topbar_label.winfo_exists():
            print("DEBUG: TopBar não existe, criando...")
            screen_width = self.winfo_screenwidth()
            topbar_img_path = os.path.join(IMG_DIR, f"TopBar_{self.player_color.lower()}.png")
            img = Image.open(topbar_img_path).convert("RGBA")
            img = img.resize((screen_width, 60), Image.Resampling.LANCZOS)
            topbar_img = ImageTk.PhotoImage(img)
            self.topbar_label = tk.Label(self, image=topbar_img, bg="black", borderwidth=0, highlightthickness=0)
            self.topbar_label.image = topbar_img  # type: ignore[attr-defined]
            self.topbar_label.pack(side="top", fill="x")
            print("DEBUG: TopBar criada com sucesso")
        
        # Força update para garantir que a limpeza foi feita
        self.update_idletasks()
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # --- Nome do jogador ---
        name_lbl = tk.Label(self, text=self.player_name, font=("Helvetica", 18, "bold"), bg=self.bar_color, fg="black", borderwidth=0)
        name_lbl.place(relx=0.5, y=25, anchor="n")
        
        # Título
        title = tk.Label(self, text=carta_tipo.capitalize(), font=("Helvetica", 22, "bold"), fg="white", bg="black")
        title.place(relx=0.5, y=65, anchor="n")
        
        # Cartas do tipo com paginação
        cartas = self.inventario.get(carta_tipo, [])
        print(f"DEBUG: Cartas encontradas no inventário: {len(cartas)}")
        
        # Paginação
        cards_per_page = 4  # 2 linhas x 2 colunas (grid 2x2)
        total_pages = max(1, (len(cartas) + cards_per_page - 1) // cards_per_page)
        page = max(0, min(page, total_pages - 1))
        start_idx = page * cards_per_page
        end_idx = start_idx + cards_per_page
        cartas_page = cartas[start_idx:end_idx]
        
        # Recria o frame para as cartas
        matriz_frame = tk.Frame(self, bg="black")
        matriz_frame.place(relx=0.5, rely=0.5, anchor="center")
        n_col = 2  # Grid 2x2 como solicitado
        card_w, card_h = 85, 120  # Mesmas dimensões que outras páginas de inventário
        self._sell_imgs = []
        
        def make_fullscreen_callback(carta_path):
            def callback(event=None):
                print(f"DEBUG: Carta clicada para venda: {carta_path}")
                # Guardar página atual para retornar ao mesmo local
                self._current_sell_page = page
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
        
        for idx, carta_path in enumerate(cartas_page):
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
        
        # Setas de navegação (se houver mais de uma página)
        if total_pages > 1:
            seta_x = 0.90
            # Seta para cima (página anterior)
            if page > 0:
                seta_up_btn = tk.Button(self, text="▲", font=("Helvetica", 18, "bold"), 
                                       bg="#222", fg="white", width=2, height=1,
                                       command=lambda: self.show_inventory_for_sell(carta_tipo, store_window, page-1))
                seta_up_btn.place(relx=seta_x, rely=0.35, anchor="center")
            
            # Seta para baixo (página seguinte)
            if page < total_pages - 1:
                seta_down_btn = tk.Button(self, text="▼", font=("Helvetica", 18, "bold"), 
                                         bg="#222", fg="white", width=2, height=1,
                                         command=lambda: self.show_inventory_for_sell(carta_tipo, store_window, page+1))
                seta_down_btn.place(relx=seta_x, rely=0.65, anchor="center")
        
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
                        
                        # CORREÇÃO: Voltar para a interface principal da Store (não para página de compra específica)
                        print(f"DEBUG: Botão Back - Chamando voltar_para_store da Store...")
                        store_window.after(50, lambda: store_window.voltar_para_store())
                        print(f"DEBUG: Interface principal da Store restaurada com sucesso")
                        
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
        
        # --- BARRA INFERIOR COM IMAGEM ---
        # Adicionar barra inferior com imagem BelowBar_X.png (onde X é a cor do jogador)
        try:
            bottombar_img_path = os.path.join(IMG_DIR, f"BelowBar_{self.player_color.lower()}.png")
            bottombar_img = ImageTk.PhotoImage(Image.open(bottombar_img_path).resize((screen_width, 50)))
            bottombar_label = tk.Label(self, image=bottombar_img, bg="black")
            bottombar_label.image = bottombar_img  # type: ignore[attr-defined]
            bottombar_label.pack(side="bottom", fill="x")
            print(f"DEBUG: Barra inferior BelowBar_{self.player_color.lower()}.png carregada no inventário de venda")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar BelowBar_{self.player_color.lower()}.png no inventário de venda: {e}")
            # Fallback: criar uma barra simples da cor do jogador se a imagem não existir
            bottombar_frame = tk.Frame(self, bg=self.bar_color, height=50)
            bottombar_frame.pack(side="bottom", fill="x")
            bottombar_frame.pack_propagate(False)

        # Saldo e piccoin no canto inferior direito, sobre a barra inferior
        coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24,24)))
        coin_lbl = tk.Label(self, image=coin_img, bg=self.bar_color)
        coin_lbl.image = coin_img  # type: ignore[attr-defined]
        coin_lbl.place(x=screen_width-100, rely=1.0, y=-25, anchor="w")
        
        saldo_lbl = tk.Label(self, text=f"{self.saldo}", 
                           font=("Helvetica", 16, "bold"), fg="black", bg=self.bar_color)
        saldo_lbl.place(x=screen_width-70, rely=1.0, y=-25, anchor="w")

        # Botão voltar - criado após a barra para ficar por cima
        if store_window:
            btn_voltar = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), bg="#808080", fg="white", width=6, command=voltar_para_store)
            btn_voltar.place(relx=0.5, rely=0.98, anchor="s")
        else:
            btn_voltar = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), bg="#808080", fg="white", width=6, command=lambda: self.playerdashboard_interface(self.player_name, self.saldo, self.other_players))
            btn_voltar.place(relx=0.5, rely=0.98, anchor="s")

        print("DEBUG: show_inventory_for_sell terminado com sucesso")

    def show_inventory_for_sell_after_sale(self, carta_tipo, store_window=None, page=0):
        """Versão especial de show_inventory_for_sell que ignora verificações de casa após uma venda bem-sucedida"""
        print(f"DEBUG: show_inventory_for_sell_after_sale chamado - carta_tipo: {carta_tipo}, page: {page}")
        
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
            if hasattr(self, 'topbar_label') and widget == self.topbar_label:
                continue
            widget.destroy()
        
        # IMPORTANTE: Verificar se a TopBar existe, se não, criá-la
        if not hasattr(self, 'topbar_label') or not self.topbar_label.winfo_exists():
            print("DEBUG: TopBar não existe, criando...")
            screen_width = self.winfo_screenwidth()
            topbar_img_path = os.path.join(IMG_DIR, f"TopBar_{self.player_color.lower()}.png")
            img = Image.open(topbar_img_path).convert("RGBA")
            img = img.resize((screen_width, 60), Image.Resampling.LANCZOS)
            topbar_img = ImageTk.PhotoImage(img)
            self.topbar_label = tk.Label(self, image=topbar_img, bg="black", borderwidth=0, highlightthickness=0)
            self.topbar_label.image = topbar_img  # type: ignore[attr-defined]
            self.topbar_label.pack(side="top", fill="x")
            print("DEBUG: TopBar criada com sucesso")
        
        # Força update para garantir que a limpeza foi feita
        self.update_idletasks()
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # --- Nome do jogador ---
        name_lbl = tk.Label(self, text=self.player_name, font=("Helvetica", 18, "bold"), bg=self.bar_color, fg="black", borderwidth=0)
        name_lbl.place(relx=0.5, y=25, anchor="n")
        
        # Título
        title = tk.Label(self, text=carta_tipo.capitalize(), font=("Helvetica", 22, "bold"), fg="white", bg="black")
        title.place(relx=0.5, y=65, anchor="n")
        
        # Cartas do tipo com paginação
        cartas = self.inventario.get(carta_tipo, [])
        print(f"DEBUG: Cartas encontradas no inventário após venda: {len(cartas)}")
        
        # Paginação
        cards_per_page = 4  # 2 linhas x 2 colunas (grid 2x2)
        total_pages = max(1, (len(cartas) + cards_per_page - 1) // cards_per_page)
        page = max(0, min(page, total_pages - 1))
        start_idx = page * cards_per_page
        end_idx = start_idx + cards_per_page
        cartas_page = cartas[start_idx:end_idx]
        
        # Recria o frame para as cartas
        matriz_frame = tk.Frame(self, bg="black")
        matriz_frame.place(relx=0.5, rely=0.5, anchor="center")
        n_col = 2  # Grid 2x2 como solicitado
        card_w, card_h = 85, 120  # Mesmas dimensões que outras páginas de inventário
        self._sell_imgs = []
        
        def make_fullscreen_callback(carta_path):
            def callback(event=None):
                print(f"DEBUG: Carta clicada para venda: {carta_path}")
                # Guardar página atual para retornar ao mesmo local
                self._current_sell_page = page
                # Verificar se a Store está disponível
                if store_window and hasattr(store_window, 'iniciar_venda_carta'):
                    store_window.iniciar_venda_carta(carta_path, carta_tipo, self)
                else:
                    self.show_card_fullscreen_sell(carta_path, carta_tipo, store_window)
            return callback
        
        for idx, carta_path in enumerate(cartas_page):
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
        
        # Setas de navegação (se houver mais de uma página)
        if total_pages > 1:
            seta_x = 0.90
            # Seta para cima (página anterior)
            if page > 0:
                seta_up_btn = tk.Button(self, text="▲", font=("Helvetica", 18, "bold"), 
                                       bg="#222", fg="white", width=2, height=1,
                                       command=lambda: self.show_inventory_for_sell_after_sale(carta_tipo, store_window, page-1))
                seta_up_btn.place(relx=seta_x, rely=0.35, anchor="center")
            
            # Seta para baixo (página seguinte)
            if page < total_pages - 1:
                seta_down_btn = tk.Button(self, text="▼", font=("Helvetica", 18, "bold"), 
                                         bg="#222", fg="white", width=2, height=1,
                                         command=lambda: self.show_inventory_for_sell_after_sale(carta_tipo, store_window, page+1))
                seta_down_btn.place(relx=seta_x, rely=0.65, anchor="center")
        
        # --- BARRA INFERIOR COM IMAGEM ---
        # Adicionar barra inferior com imagem BelowBar_X.png (onde X é a cor do jogador)
        try:
            bottombar_img_path = os.path.join(IMG_DIR, f"BelowBar_{self.player_color.lower()}.png")
            bottombar_img = ImageTk.PhotoImage(Image.open(bottombar_img_path).resize((screen_width, 50)))
            bottombar_label = tk.Label(self, image=bottombar_img, bg="black")
            bottombar_label.image = bottombar_img  # type: ignore[attr-defined]
            bottombar_label.pack(side="bottom", fill="x")
            print(f"DEBUG: Barra inferior BelowBar_{self.player_color.lower()}.png carregada no inventário de venda após venda")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar BelowBar_{self.player_color.lower()}.png no inventário de venda após venda: {e}")
            # Fallback: criar uma barra simples da cor do jogador se a imagem não existir
            bottombar_frame = tk.Frame(self, bg=self.bar_color, height=50)
            bottombar_frame.pack(side="bottom", fill="x")
            bottombar_frame.pack_propagate(False)

        # Saldo e piccoin no canto inferior direito, sobre a barra inferior
        coin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24,24)))
        coin_lbl = tk.Label(self, image=coin_img, bg=self.bar_color)
        coin_lbl.image = coin_img  # type: ignore[attr-defined]
        coin_lbl.place(x=screen_width-100, rely=1.0, y=-25, anchor="w")
        
        saldo_lbl = tk.Label(self, text=f"{self.saldo}", 
                           font=("Helvetica", 16, "bold"), fg="black", bg=self.bar_color)
        saldo_lbl.place(x=screen_width-70, rely=1.0, y=-25, anchor="w")

        # Botão voltar - criado após a barra para ficar por cima
        def voltar_para_store():
            print("DEBUG: PlayerDashboard voltar_para_store chamado (após venda)")
            try:
                # Primeiro, esconde o PlayerDashboard
                print("DEBUG: Escondendo PlayerDashboard...")
                self.withdraw()
                
                # Aguarda um pouco para garantir que foi escondido
                print("DEBUG: Aguardando para processar volta à Store...")
                self.after(100, lambda: self._process_back_to_store_after_sale(store_window))
                
            except Exception as e:
                print(f"DEBUG: Erro ao iniciar volta para store após venda: {e}")
                import traceback
                traceback.print_exc()
        
        def _process_back_to_store_after_sale(store_window):
            print("DEBUG: Processando volta à Store após venda...")
            try:
                # Verificar se a Store ainda existe
                if hasattr(store_window, 'winfo_exists') and store_window.winfo_exists():
                    print("DEBUG: Store existe, forçando exibição...")
                    # Força a Store a aparecer
                    store_window.deiconify()
                    store_window.state('normal')
                    store_window.lift()
                    store_window.focus_force()
                    
                    # CORREÇÃO: Voltar para a interface principal da Store (não para página de compra específica)
                    print(f"DEBUG: Botão Back - Chamando voltar_para_store da Store...")
                    store_window.after(50, lambda: store_window.voltar_para_store())
                    print(f"DEBUG: Interface principal da Store restaurada com sucesso")
                    
                else:
                    print("DEBUG: Store não existe mais, voltando ao PlayerDashboard")
                    self.deiconify()
                    self.lift()
                    self.focus_force()
                    self.playerdashboard_interface(self.player_name, self.saldo, self.other_players)
                    
            except Exception as e:
                print(f"DEBUG: Erro ao processar volta à Store após venda: {e}")
                import traceback
                traceback.print_exc()
                # Em caso de erro, volta ao PlayerDashboard
                try:
                    self.deiconify()
                    self.lift()
                    self.focus_force()
                    self.playerdashboard_interface(self.player_name, self.saldo, self.other_players)
                except Exception as fallback_e:
                    print(f"DEBUG: ERRO CRÍTICO no fallback após venda: {fallback_e}")
                    traceback.print_exc()
        
        # Adiciona o método auxiliar à instância
        self._process_back_to_store_after_sale = _process_back_to_store_after_sale
        
        if store_window:
            btn_voltar = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), bg="#808080", fg="white", width=6, command=voltar_para_store)
            btn_voltar.place(relx=0.5, rely=0.98, anchor="s")
        else:
            btn_voltar = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), bg="#808080", fg="white", width=6, command=lambda: self.playerdashboard_interface(self.player_name, self.saldo, self.other_players))
            btn_voltar.place(relx=0.5, rely=0.98, anchor="s")

        print("DEBUG: show_inventory_for_sell_after_sale terminado com sucesso")

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
        
        # Botão X para fechar - movido para canto superior esquerdo
        def fechar():
            # CORREÇÃO: Voltar para a página de inventário correta onde o utilizador estava
            current_page = getattr(self, '_current_sell_page', 0)
            # IMPORTANTE: Usar versão especial que ignora verificações de casa
            self.show_inventory_for_sell_after_sale(carta_tipo, store_window, current_page)
        
        x_btn = tk.Button(self, text="✖", font=("Helvetica", 24, "bold"), bg="#AAAAAA", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=fechar, cursor="hand2", activebackground="#CCCCCC")
        x_btn.place(relx=0.02, rely=0, anchor="nw")
        
        # Botão de venda APENAS se estiver numa casa do tipo correspondente
        # Verificar se o jogador está numa casa do tipo correspondente (no inventário próprio, qualquer cor serve)
        pode_vender = False
        casa_atual_tipo = getattr(self, 'current_casa_tipo', 'neutral')
        
        print(f"DEBUG: Verificando possibilidade de venda fullscreen no inventário - carta_tipo: {carta_tipo}, casa_atual_tipo: {casa_atual_tipo}")
        
        # IMPORTANTE: Se Next Phase estiver ativo, NÃO pode vender nenhuma carta
        if getattr(self, '_next_phase_active', False):
            print(f"DEBUG: NÃO pode vender carta {carta_tipo} do inventário - Next Phase está ativo (vendas desabilitadas)")
            pode_vender = False
        else:
            # Normalizar o tipo da casa atual (equipments vs equipment)
            if casa_atual_tipo == "equipment":
                casa_atual_tipo = "equipments"
            
            # Verificar se pode vender
            if carta_tipo in ["users", "equipments", "services"]:
                # Para estas cartas, precisa estar na casa do mesmo tipo
                if casa_atual_tipo == carta_tipo:
                    pode_vender = True
            elif carta_tipo in ["activities", "challenges"]:
                # Activities só podem ser vendidas numa casa Activities, Challenges só numa casa Challenges
                if casa_atual_tipo == carta_tipo:
                    pode_vender = True
        
        # Botão de venda com checkmark no canto superior direito (substitui o botão verde picoin)
        if pode_vender:
            print(f"DEBUG: Pode vender carta {carta_tipo} do inventário - está numa casa {casa_atual_tipo}")
            def abrir_confirm():
                self.show_sell_confirmation(carta_path, carta_tipo, store_window)
            
            # Botão com checkmark (✓) no canto superior direito
            btn_sell = tk.Button(self, text="✓", font=("Helvetica", 24, "bold"), bg="#4CAF50", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=abrir_confirm, cursor="hand2", activebackground="#43d17a")
            btn_sell.place(relx=0.98, rely=0, anchor="ne")
        else:
            print(f"DEBUG: NÃO pode vender carta {carta_tipo} do inventário - casa atual: {casa_atual_tipo}, necessário: {carta_tipo}")

    def show_sell_confirmation(self, carta_path, carta_tipo, store_window=None):
        import os
        import tkinter.messagebox
        
        # Definir variáveis necessárias
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # PRIMEIRO: Limpar tudo e mostrar a carta em fullscreen como fundo (igual à compra)
        for widget in self.winfo_children():
            widget.destroy()
        self.configure(bg="black")
        
        # Mostrar a carta em fullscreen como fundo (igual à imagem de compra)
        try:
            pil_img = Image.open(carta_path)
            img_w, img_h = pil_img.size
            
            # Área disponível: toda a tela (igual à compra)
            available_width = screen_width
            available_height = screen_height
            
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
        
        # SEGUNDO: Frame de confirmação (igual ao layout da compra na imagem)
        confirm_frame = tk.Frame(self, bg="black")
        confirm_frame.pack(expand=True)
        tk.Label(confirm_frame, text="Are you sure you want to sell?", font=("Helvetica", 16, "bold"), fg="white", bg="black").pack(pady=(40, 20))
        
        # Saldo atual (igual à confirmação de compra)
        tk.Label(confirm_frame, text=f"Your balance: {self.saldo}", font=("Helvetica", 16), fg="yellow", bg="black").pack(pady=(0, 10))
        
        # Valor da carta (usando base de dados integrada)
        valor = self._extrair_valor_venda_carta(carta_path)
        if valor is None:
            print("DEBUG: Valor não encontrado, usando fallback")
            valor = self._extrair_valor_fallback(carta_path)
        
        value_frame = tk.Frame(confirm_frame, bg="black")
        value_frame.pack(pady=(0, 30))
        
        tk.Label(value_frame, text="Card value: ", 
                font=("Helvetica", 16), fg="white", bg="black").pack(side="left")
        tk.Label(value_frame, text=str(valor), 
                font=("Helvetica", 16, "bold"), fg="yellow", bg="black").pack(side="left", padx=(5, 5))
        
        # Ícone da moeda (igual à confirmação de compra)
        try:
            picoin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((24,24)))
            picoin_lbl = tk.Label(value_frame, image=picoin_img, bg="black")
            picoin_lbl.image = picoin_img
            picoin_lbl.pack(side="left")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar ícone da moeda: {e}")
        
        # Frame para os botões (igual à confirmação de compra)
        btns_frame = tk.Frame(confirm_frame, bg="black")
        btns_frame.pack()
        
        def confirmar():
            print("DEBUG: Confirmar venda - início")
            print(f"DEBUG: Variáveis de controle - _inventario_conjunto: {getattr(self, '_inventario_conjunto', 'None')}")
            print(f"DEBUG: Variáveis de controle - _tipos_venda: {getattr(self, '_tipos_venda', 'None')}")
            print(f"DEBUG: Variáveis de controle - _current_sell_page: {getattr(self, '_current_sell_page', 'None')}")
            try:
                # CORREÇÃO: Lógica de venda correta
                # Player vende a carta: perde a carta, ganha dinheiro
                # Store compra a carta: ganha a carta, perde dinheiro
                if valor is not None and valor > 0:
                    # Player recebe o dinheiro pela venda
                    self.saldo += valor
                    print(f"DEBUG: Player vendeu carta por {valor}, novo saldo: {self.saldo}")
                    
                    # Store paga pela carta (perde dinheiro)
                    if store_window:
                        store_window.saldo -= valor
                        print(f"DEBUG: Store pagou {valor}, novo saldo: {store_window.saldo}")
                        
                        # IMPORTANTE: Devolver a carta aos baralhos da Store (sincronização)
                        if hasattr(store_window, 'adicionar_carta_ao_baralho'):
                            store_window.adicionar_carta_ao_baralho(carta_path, carta_tipo)
                            print(f"DEBUG: Carta devolvida aos baralhos da Store: {carta_path}")
                        else:
                            print(f"DEBUG: AVISO - Store não tem método adicionar_carta_ao_baralho")
                
                # Remove carta do inventário do Player
                if carta_tipo in self.inventario and carta_path in self.inventario[carta_tipo]:
                    self.inventario[carta_tipo].remove(carta_path)
                    print(f"DEBUG: Carta removida do inventário do Player: {carta_path}")
                
                print(f"DEBUG: Venda confirmada - Player saldo: {self.saldo}")
                
                # CORREÇÃO: Voltar para a página de inventário correta onde o utilizador estava
                # Se viemos de um inventário Activities/Challenges conjunto, voltar para esse
                if getattr(self, '_inventario_conjunto', False) and hasattr(self, '_tipos_venda') and self._tipos_venda:
                    print("DEBUG: Voltando para inventário conjunto Activities/Challenges")
                    current_page = getattr(self, '_current_sell_page', 0)
                    # CORREÇÃO: Verificar se a página ainda é válida após a venda
                    cartas_totais = []
                    for t in self._tipos_venda:
                        cartas_totais += self.inventario.get(t, [])
                    cards_per_page = 4
                    total_pages = max(1, (len(cartas_totais) + cards_per_page - 1) // cards_per_page) if cartas_totais else 1
                    # IMPORTANTE: Garantir que current_page e total_pages são números válidos
                    if current_page is None:
                        current_page = 0
                    if total_pages is None:
                        total_pages = 1
                    current_page = min(current_page, total_pages - 1)
                    print(f"DEBUG: Cartas totais: {len(cartas_totais)}, total_pages: {total_pages}, current_page: {current_page}")
                    print(f"DEBUG: Chamando show_inventory_matrix_carrossel com tipos: {self._tipos_venda}, page: {current_page}")
                    self.show_inventory_matrix_carrossel(self._tipos_venda, current_page)
                else:
                    print("DEBUG: Voltando para inventário do tipo específico")
                    # Caso normal: voltar para inventário do tipo específico
                    current_page = getattr(self, '_current_sell_page', 0)
                    # CORREÇÃO: Verificar se a página ainda é válida após a venda
                    cartas_restantes = self.inventario.get(carta_tipo, [])
                    cards_per_page = 4
                    total_pages = max(1, (len(cartas_restantes) + cards_per_page - 1) // cards_per_page) if cartas_restantes else 1
                    # IMPORTANTE: Garantir que current_page e total_pages são números válidos
                    if current_page is None:
                        current_page = 0
                    if total_pages is None:
                        total_pages = 1
                    current_page = min(current_page, total_pages - 1)
                    print(f"DEBUG: Cartas restantes: {len(cartas_restantes)}, total_pages: {total_pages}, current_page: {current_page}")
                    print(f"DEBUG: Chamando show_inventory_for_sell_after_sale com carta_tipo: {carta_tipo}, page: {current_page}")
                    # IMPORTANTE: Usar versão especial que ignora verificações de casa para voltar após venda
                    self.show_inventory_for_sell_after_sale(carta_tipo, store_window, current_page)
                
                # Limpar variáveis de controle
                self._origem_venda = None
                self._tipos_venda = None
                self._page_venda = None
                self._current_sell_page = None
                self._inventario_conjunto = None
                
                print("DEBUG: Venda confirmada com sucesso - limpeza concluída")
                
            except Exception as e:
                print(f"DEBUG: ERRO na confirmação: {e}")
                import traceback
                traceback.print_exc()
                # Em caso de erro, tentar voltar à interface principal
                try:
                    print("DEBUG: Tentando voltar à interface principal após erro")
                    self.playerdashboard_interface(self.player_name, self.saldo, self.other_players)
                except Exception as fallback_e:
                    print(f"DEBUG: ERRO CRÍTICO no fallback: {fallback_e}")
                    traceback.print_exc()
        
        def cancelar():
            print(f"DEBUG: Cancelar venda - carta_tipo: {carta_tipo}")
            
            # CORREÇÃO: Voltar para a página de inventário correta onde o utilizador estava
            # Se viemos de um inventário Activities/Challenges conjunto, voltar para esse
            if getattr(self, '_inventario_conjunto', False) and hasattr(self, '_tipos_venda') and self._tipos_venda:
                print("DEBUG: Voltando para inventário conjunto Activities/Challenges")
                current_page = getattr(self, '_current_sell_page', 0)
                # CORREÇÃO: Verificar se a página ainda é válida (mesmo sem venda, por segurança)
                cartas_totais = []
                for t in self._tipos_venda:
                    cartas_totais += self.inventario.get(t, [])
                cards_per_page = 4
                total_pages = max(1, (len(cartas_totais) + cards_per_page - 1) // cards_per_page) if cartas_totais else 1
                # IMPORTANTE: Garantir que current_page e total_pages são números válidos
                if current_page is None:
                    current_page = 0
                if total_pages is None:
                    total_pages = 1
                current_page = min(current_page, total_pages - 1)
                print(f"DEBUG: Cartas totais: {len(cartas_totais)}, total_pages: {total_pages}, current_page: {current_page}")
                self.show_inventory_matrix_carrossel(self._tipos_venda, current_page)
            else:
                # Caso normal: voltar para inventário do tipo específico
                current_page = getattr(self, '_current_sell_page', 0)
                # IMPORTANTE: Garantir que current_page é um número válido
                if current_page is None:
                    current_page = 0
                # IMPORTANTE: Para cancelamento, usar função normal que mostra todas as cartas
                print(f"DEBUG: Cancelamento - chamando show_inventory_for_sell normal com carta_tipo: {carta_tipo}, page: {current_page}")
                self.show_inventory_for_sell(carta_tipo, store_window, current_page)
            
            # Limpar variáveis de controle
            self._origem_venda = None
            self._tipos_venda = None
            self._page_venda = None
            self._current_sell_page = None
            self._inventario_conjunto = None
            
        # Botões No e Yes (posições trocadas)
        btn_no = tk.Button(btns_frame, text="No", font=("Helvetica", 14, "bold"), 
                          bg="#F44336", fg="white", width=8, command=cancelar)
        btn_yes = tk.Button(btns_frame, text="Yes", font=("Helvetica", 14, "bold"), 
                           bg="#4CAF50", fg="white", width=8, command=confirmar)
        btn_no.pack(side="left", padx=20, pady=10)
        btn_yes.pack(side="left", padx=20, pady=10)
        
        print(f"DEBUG: Botões de confirmação criados - Yes e No")
        print(f"DEBUG: Função confirmar configurada: {confirmar}")
        print(f"DEBUG: Função cancelar configurada: {cancelar}")
        
        # Force update para garantir que os botões estão visíveis
        self.update_idletasks()
        self.update()

    def show_activation_confirmation(self, carta_path, carta_tipo, tipos, page):
        """Mostra uma página de confirmação para ativação de carta com a carta como fundo"""
        print(f"DEBUG: Mostrando confirmação de ativação para {carta_path}")
        
        # Limpar TODOS os widgets (incluindo a barra superior para fullscreen completo)
        for widget in self.winfo_children():
            widget.destroy()
        
        # Definir fundo preto para a janela
        self.config(bg="black")
        
        # Carregar a imagem da carta como fundo
        try:
            carta_img = Image.open(carta_path)
            screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()
            
            # Calcular o ratio para ocupar o máximo possível da tela (igual à venda)
            ratio = min(screen_width/carta_img.width, screen_height/carta_img.height)
            new_w, new_h = int(carta_img.width * ratio), int(carta_img.height * ratio)
            carta_resized = carta_img.resize((new_w, new_h), Image.LANCZOS)
            carta_photo = ImageTk.PhotoImage(carta_resized)
            
            # Label com a imagem da carta como fundo (usar place igual à venda)
            carta_label = tk.Label(self, image=carta_photo, bg="black", borderwidth=0, highlightthickness=0)
            carta_label.image = carta_photo  # Manter referência
            carta_label.place(relx=0.5, rely=0.5, anchor="center")
            
        except Exception as e:
            print(f"DEBUG: Erro ao carregar imagem da carta: {e}")
            self.config(bg="black")
        
        # Frame para a dialog de confirmação (centro da tela) - fundo preto com letras brancas
        # Usar pack(expand=True) para dimensionamento dinâmico, igual às páginas de venda
        confirm_frame = tk.Frame(self, bg="black")
        confirm_frame.pack(expand=True)
        
        # Título
        tk.Label(confirm_frame, text="Activation Confirmation", 
                font=("Helvetica", 16, "bold"), fg="yellow", bg="black").pack(pady=(40, 20))
        
        # Mensagem de confirmação
        tk.Label(confirm_frame, text="Do you want to activate this card?", 
                font=("Helvetica", 16), fg="white", bg="black").pack(pady=(0, 10))
        
        # Frame para os botões
        btns_frame = tk.Frame(confirm_frame, bg="black")
        btns_frame.pack(pady=30)
        
        def confirmar():
            print(f"DEBUG: Confirmando ativação da carta {carta_path}")
            try:
                # Ativar a carta
                self.activate_card(carta_tipo, carta_path)
                
                # Recriar a TopBar antes de voltar ao inventário
                screen_width = self.winfo_screenwidth()
                topbar_img_path = os.path.join(IMG_DIR, f"TopBar_{self.player_color.lower()}.png")
                try:
                    img = Image.open(topbar_img_path).convert("RGBA")
                    img = img.resize((screen_width, 60), Image.Resampling.LANCZOS)
                    topbar_img = ImageTk.PhotoImage(img)
                    self.topbar_label = tk.Label(self, image=topbar_img, bg="black", borderwidth=0, highlightthickness=0)
                    self.topbar_label.image = topbar_img
                    self.topbar_label.pack(side="top", fill="x")
                    print("DEBUG: TopBar recriada após confirmar ativação")
                except Exception as e:
                    print(f"DEBUG: Erro ao recriar TopBar: {e}")
                
                # Voltar para a página de inventário
                self.show_inventory_matrix(tipos, page)
                
            except Exception as e:
                print(f"DEBUG: Erro ao confirmar ativação: {e}")
                traceback.print_exc()
                # Em caso de erro, voltar para o inventário
                try:
                    # Recriar a TopBar mesmo em caso de erro
                    screen_width = self.winfo_screenwidth()
                    topbar_img_path = os.path.join(IMG_DIR, f"TopBar_{self.player_color.lower()}.png")
                    try:
                        img = Image.open(topbar_img_path).convert("RGBA")
                        img = img.resize((screen_width, 60), Image.Resampling.LANCZOS)
                        topbar_img = ImageTk.PhotoImage(img)
                        self.topbar_label = tk.Label(self, image=topbar_img, bg="black", borderwidth=0, highlightthickness=0)
                        self.topbar_label.image = topbar_img
                        self.topbar_label.pack(side="top", fill="x")
                        print("DEBUG: TopBar recriada após erro na ativação")
                    except Exception as topbar_e:
                        print(f"DEBUG: Erro ao recriar TopBar após erro: {topbar_e}")
                    
                    self.show_inventory_matrix(tipos, page)
                except Exception as fallback_e:
                    print(f"DEBUG: ERRO CRÍTICO no fallback: {fallback_e}")
                    traceback.print_exc()
        
        def cancelar():
            print(f"DEBUG: Cancelar ativação - carta_tipo: {carta_tipo}")
            
            # Recriar a TopBar antes de voltar ao inventário
            screen_width = self.winfo_screenwidth()
            topbar_img_path = os.path.join(IMG_DIR, f"TopBar_{self.player_color.lower()}.png")
            try:
                img = Image.open(topbar_img_path).convert("RGBA")
                img = img.resize((screen_width, 60), Image.Resampling.LANCZOS)
                topbar_img = ImageTk.PhotoImage(img)
                self.topbar_label = tk.Label(self, image=topbar_img, bg="black", borderwidth=0, highlightthickness=0)
                self.topbar_label.image = topbar_img
                self.topbar_label.pack(side="top", fill="x")
                print("DEBUG: TopBar recriada após cancelar ativação")
            except Exception as e:
                print(f"DEBUG: Erro ao recriar TopBar: {e}")
            
            # Voltar para a página de inventário
            self.show_inventory_matrix(tipos, page)
            
        # Botões No e Yes (posições trocadas)
        btn_no = tk.Button(btns_frame, text="No", font=("Helvetica", 14, "bold"), 
                          bg="#F44336", fg="white", width=8, command=cancelar)
        btn_yes = tk.Button(btns_frame, text="Yes", font=("Helvetica", 14, "bold"), 
                           bg="#4CAF50", fg="white", width=8, command=confirmar)
        btn_no.pack(side="left", padx=20, pady=10)
        btn_yes.pack(side="left", padx=20, pady=10)
        
        print(f"DEBUG: Botões de confirmação de ativação criados - Yes e No")
        
        # Force update para garantir que os botões estão visíveis
        self.update_idletasks()
        self.update()

    def show_deactivation_confirmation(self, carta_path, carta_tipo, tipos, page):
        """Mostra uma página de confirmação para desativação de carta com a carta como fundo"""
        print(f"DEBUG: Mostrando confirmação de desativação para {carta_path}")
        
        # Limpar TODOS os widgets (incluindo a barra superior para fullscreen completo)
        for widget in self.winfo_children():
            widget.destroy()
        
        # Definir fundo preto para a janela
        self.config(bg="black")
        
        # Carregar a imagem da carta como fundo
        try:
            carta_img = Image.open(carta_path)
            screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()
            
            # Calcular o ratio para ocupar o máximo possível da tela (igual à venda)
            ratio = min(screen_width/carta_img.width, screen_height/carta_img.height)
            new_w, new_h = int(carta_img.width * ratio), int(carta_img.height * ratio)
            carta_resized = carta_img.resize((new_w, new_h), Image.LANCZOS)
            carta_photo = ImageTk.PhotoImage(carta_resized)
            
            # Label com a imagem da carta como fundo (usar place igual à venda)
            carta_label = tk.Label(self, image=carta_photo, bg="black", borderwidth=0, highlightthickness=0)
            carta_label.image = carta_photo  # Manter referência
            carta_label.place(relx=0.5, rely=0.5, anchor="center")
            
        except Exception as e:
            print(f"DEBUG: Erro ao carregar imagem da carta: {e}")
            self.config(bg="black")
        
        # Frame para a dialog de confirmação (centro da tela) - fundo preto com letras brancas
        # Usar pack(expand=True) para dimensionamento dinâmico, igual às páginas de venda
        confirm_frame = tk.Frame(self, bg="black")
        confirm_frame.pack(expand=True)
        
        # Título
        tk.Label(confirm_frame, text="Deactivation Confirmation", 
                font=("Helvetica", 16, "bold"), fg="yellow", bg="black").pack(pady=(40, 20))
        
        # Mensagem de confirmação
        tk.Label(confirm_frame, text="Do you want to deactivate this card?", 
                font=("Helvetica", 16), fg="white", bg="black").pack(pady=(0, 10))
        
        # Frame para os botões
        btns_frame = tk.Frame(confirm_frame, bg="black")
        btns_frame.pack(pady=30)
        
        def confirmar():
            print(f"DEBUG: Confirmando desativação da carta {carta_path}")
            try:
                # Desativar a carta
                self.deactivate_card(carta_path, carta_tipo)
                
                # Recriar a TopBar antes de voltar ao inventário
                screen_width = self.winfo_screenwidth()
                topbar_img_path = os.path.join(IMG_DIR, f"TopBar_{self.player_color.lower()}.png")
                try:
                    img = Image.open(topbar_img_path).convert("RGBA")
                    img = img.resize((screen_width, 60), Image.Resampling.LANCZOS)
                    topbar_img = ImageTk.PhotoImage(img)
                    self.topbar_label = tk.Label(self, image=topbar_img, bg="black", borderwidth=0, highlightthickness=0)
                    self.topbar_label.image = topbar_img
                    self.topbar_label.pack(side="top", fill="x")
                    print("DEBUG: TopBar recriada após confirmar desativação")
                except Exception as e:
                    print(f"DEBUG: Erro ao recriar TopBar: {e}")
                
                # Voltar para a página de inventário
                self.show_inventory_matrix(tipos, page)
                
            except Exception as e:
                print(f"DEBUG: Erro ao confirmar desativação: {e}")
                traceback.print_exc()
                # Em caso de erro, voltar para o inventário
                try:
                    # Recriar a TopBar mesmo em caso de erro
                    screen_width = self.winfo_screenwidth()
                    topbar_img_path = os.path.join(IMG_DIR, f"TopBar_{self.player_color.lower()}.png")
                    try:
                        img = Image.open(topbar_img_path).convert("RGBA")
                        img = img.resize((screen_width, 60), Image.Resampling.LANCZOS)
                        topbar_img = ImageTk.PhotoImage(img)
                        self.topbar_label = tk.Label(self, image=topbar_img, bg="black", borderwidth=0, highlightthickness=0)
                        self.topbar_label.image = topbar_img
                        self.topbar_label.pack(side="top", fill="x")
                        print("DEBUG: TopBar recriada após erro na desativação")
                    except Exception as topbar_e:
                        print(f"DEBUG: Erro ao recriar TopBar após erro: {topbar_e}")
                    
                    self.show_inventory_matrix(tipos, page)
                except Exception as fallback_e:
                    print(f"DEBUG: ERRO CRÍTICO no fallback: {fallback_e}")
                    traceback.print_exc()
        
        def cancelar():
            print(f"DEBUG: Cancelar desativação - carta_tipo: {carta_tipo}")
            
            # Recriar a TopBar antes de voltar ao inventário
            screen_width = self.winfo_screenwidth()
            topbar_img_path = os.path.join(IMG_DIR, f"TopBar_{self.player_color.lower()}.png")
            try:
                img = Image.open(topbar_img_path).convert("RGBA")
                img = img.resize((screen_width, 60), Image.Resampling.LANCZOS)
                topbar_img = ImageTk.PhotoImage(img)
                self.topbar_label = tk.Label(self, image=topbar_img, bg="black", borderwidth=0, highlightthickness=0)
                self.topbar_label.image = topbar_img
                self.topbar_label.pack(side="top", fill="x")
                print("DEBUG: TopBar recriada após cancelar desativação")
            except Exception as e:
                print(f"DEBUG: Erro ao recriar TopBar: {e}")
            
            # Voltar para a página de inventário
            self.show_inventory_matrix(tipos, page)
            
        # Botões No e Yes (posições trocadas)
        btn_no = tk.Button(btns_frame, text="No", font=("Helvetica", 14, "bold"), 
                          bg="#F44336", fg="white", width=8, command=cancelar)
        btn_yes = tk.Button(btns_frame, text="Yes", font=("Helvetica", 14, "bold"), 
                           bg="#4CAF50", fg="white", width=8, command=confirmar)
        btn_no.pack(side="left", padx=20, pady=10)
        btn_yes.pack(side="left", padx=20, pady=10)
        
        print(f"DEBUG: Botões de confirmação de desativação criados - Yes e No")
        
        # Force update para garantir que os botões estão visíveis
        self.update_idletasks()
        self.update()

    # Corrigir aceitação de carta Challenge/Activity para adicionar ao carrossel
    def aceitar_carta_challenge_activity(self, carta_path, carta_tipo):
        # Chamar isto ao aceitar uma carta Challenge/Activity
        self.adicionar_carta_carrossel(carta_path, carta_tipo)
        # ... resto do fluxo de aceitação ...
        self.playerdashboard_interface(self.player_name, self.saldo, self.other_players)

    # Corrigir fullscreen do carrossel: botão X volta sempre à interface principal
    def show_card_fullscreen_carrossel(self, carta_path):
        # Preservar valores das barras de progresso ANTES de destruir os widgets
        saved_progress_values = {}
        if hasattr(self, 'progress_bars') and hasattr(self, 'progress_labels'):
            try:
                for stat in self.progress_bars:
                    # Verificar se o widget ainda existe antes de acessar seus valores
                    if self.progress_bars[stat].winfo_exists():
                        saved_progress_values[stat] = {
                            'value': self.progress_bars[stat]['value'],
                            'maximum': self.progress_bars[stat]['maximum']
                        }
                print(f"DEBUG: Valores das barras preservados antes de fullscreen: {saved_progress_values}")
            except Exception as e:
                print(f"DEBUG: Erro ao preservar valores das barras: {e}")
        
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
        
        # Botão X para fechar - canto superior esquerdo (cinza)
        def voltar_dashboard():
            # Preservar seleção da carta do carrossel ao voltar do fullscreen
            selected_carta = getattr(self, 'selected_carousel_card', None)
            selected_index = getattr(self, 'selected_carousel_index', None)
            
            self.playerdashboard_interface(self.player_name, self.saldo, self.other_players)
            
            # Restaurar seleção da carta após recriar interface
            if selected_carta is not None and selected_index is not None:
                self.selected_carousel_card = selected_carta
                self.selected_carousel_index = selected_index
                # Atualizar destaques visuais
                if hasattr(self, 'card_labels') and self.card_labels:
                    self._update_carousel_selection_highlights()
                print(f"DEBUG: Seleção da carta restaurada após voltar do fullscreen: índice {selected_index}")
            
            # Restaurar valores das barras de progresso após recriar interface
            if saved_progress_values and hasattr(self, 'progress_bars') and hasattr(self, 'progress_labels'):
                for stat, values in saved_progress_values.items():
                    if stat in self.progress_bars and stat in self.progress_labels:
                        self.progress_bars[stat]['maximum'] = values['maximum']
                        self.progress_bars[stat]['value'] = values['value']
                        self.progress_labels[stat]['text'] = str(int(values['value']))
                print(f"DEBUG: Valores das barras restaurados após recriar interface: {saved_progress_values}")
        x_btn = tk.Button(self, text="✖", font=("Helvetica", 24, "bold"), bg="#AAAAAA", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=voltar_dashboard, cursor="hand2", activebackground="#CCCCCC")
        x_btn.place(relx=0.02, rely=0, anchor="nw")
        
        # Botão Switch no canto superior direito com imagem switch_card.png
        # SÓ APARECE EM ACTIVITIES/CHALLENGES DURANTE NEXT PHASE (MAS NÃO DURANTE FINAL PHASE)
        switch_btn = None
        
        # Verificar se é uma carta de Activity ou Challenge
        carta_name = os.path.basename(carta_path).lower()
        is_activity_or_challenge = ("activity" in carta_name or "challenge" in carta_name)
        next_phase_active = getattr(self, '_next_phase_active', False)
        final_phase_active = getattr(self, '_final_phase_active', False)
        
        # Durante Final Phase, não mostrar botão Switch
        if is_activity_or_challenge and next_phase_active and not final_phase_active:
            try:
                switch_img_path = os.path.join(IMG_DIR, "switch_card.png")
                if os.path.exists(switch_img_path):
                    switch_img = ImageTk.PhotoImage(Image.open(switch_img_path).resize((48, 48)))
                    switch_btn = tk.Button(self, image=switch_img, bg="#FF9800", borderwidth=0, highlightthickness=0, cursor="hand2", activebackground="#E68900")
                    switch_btn.image = switch_img  # Manter referência
                    switch_btn.place(relx=0.98, rely=0, anchor="ne")
                    print(f"DEBUG: [CARROSSEL FULLSCREEN] Botão Switch criado - Activity/Challenge durante Next Phase (não Final Phase)")
                else:
                    print(f"DEBUG: [CARROSSEL FULLSCREEN] Botão Switch NÃO criado - imagem switch_card.png não encontrada em {switch_img_path}")
            except Exception as e:
                print(f"DEBUG: [CARROSSEL FULLSCREEN] Botão Switch NÃO criado - erro ao carregar imagem: {e}")
        else:
            print(f"DEBUG: [CARROSSEL FULLSCREEN] Botão Switch NÃO criado - condições não atendidas (Activity/Challenge: {is_activity_or_challenge}, Next Phase: {next_phase_active}, Final Phase: {final_phase_active})")
        
        # Configurar comando do botão Switch (abrir inventário para troca)
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
        
        if switch_btn is not None:
            switch_btn.config(command=abrir_inventario_troca)
            print(f"DEBUG: [CARROSSEL FULLSCREEN] Botão Switch configurado para abrir inventário de troca")

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
    
    def _check_user_inventory_for_carousel_access(self):
        """
        Verifica que User IDs o jogador tem no inventário e se estão virados para cima (ativos ou visíveis).
        User_2.png corresponde ao User ID 1, User_3.png ao User ID 2, etc.
        Durante Next Phase, só conta cartas User que estejam viradas para cima.
        """
        user_ids = []
        user_cards = self.inventario.get("users", [])
        next_phase_active = getattr(self, '_next_phase_active', False)
        
        for carta_path in user_cards:
            carta_name = os.path.basename(carta_path)
            if carta_name.startswith("User_") and carta_name.endswith(".png"):
                try:
                    # Extrair número do nome: User_2.png -> 2
                    numero_str = carta_name.replace("User_", "").replace(".png", "")
                    numero = int(numero_str)
                    
                    # Verificar se a carta está virada para cima
                    is_face_up = False
                    if numero == 1:
                        # User_1.png sempre virada para cima
                        is_face_up = True
                    elif next_phase_active:
                        # Durante Next Phase, verificar se a carta está ativa (virada para cima)
                        is_face_up = self.is_card_active(carta_path, "users")
                    else:
                        # Antes de Next Phase, todas as cartas (exceto User_1) estão viradas para baixo
                        is_face_up = False
                    
                    # Só adicionar à lista se estiver virada para cima
                    if is_face_up:
                        # User_2.png corresponde ao User ID 1, User_3.png ao User ID 2, etc.
                        user_id = numero - 1
                        if user_id >= 1:  # User ID começa em 1
                            user_ids.append(user_id)
                            print(f"DEBUG: User_{numero}.png ATIVO - User ID {user_id} disponível para carrossel")
                    else:
                        print(f"DEBUG: User_{numero}.png INATIVO - User ID não disponível para carrossel")
                        
                except (ValueError, IndexError):
                    continue
        
        # Cache dos User IDs para performance
        self._cached_user_ids = sorted(user_ids)
        print(f"DEBUG: User IDs ativos/visíveis encontrados no inventário: {self._cached_user_ids}")
        return self._cached_user_ids
    
    def _can_access_carousel_position(self, carrossel_idx):
        """
        Verifica se o jogador pode aceder a uma posição específica do carrossel durante Next Phase.
        Só pode clicar numa carta virada para baixo se tiver o User ID correspondente.
        Posição 0 (primeira carta da esquerda) requer User ID 1, posição 1 requer User ID 2, etc.
        """
        if not getattr(self, '_next_phase_active', False):
            # Se Next Phase não está ativo, pode aceder a qualquer posição
            return True
        
        # Durante Next Phase, verificar se tem o User ID necessário
        required_user_id = carrossel_idx + 1  # Posição 0 -> User ID 1, posição 1 -> User ID 2, etc.
        user_ids = self._check_user_inventory_for_carousel_access()
        
        can_access = required_user_id in user_ids
        print(f"DEBUG: Posição {carrossel_idx} requer User ID {required_user_id}, tem acesso: {can_access}")
        return can_access
    
    def _teste_adicionar_user_cards(self):
        """
        Função de teste para adicionar cartas User/Equipment/Service ao inventário para testar o sistema de ativação.
        Esta função pode ser removida em produção.
        """
        # Simular caminhos de cartas para teste (usar a cor do player)
        color_name = self.player_color.capitalize()  # Red, Blue, Green, Yellow
        
        test_cards = {
            "users": [
                f"/Users/joaop_27h1t5j/Desktop/IST/Bolsa/NetMaster/Users/Residential-level/{color_name}/User_2.png",
                f"/Users/joaop_27h1t5j/Desktop/IST/Bolsa/NetMaster/Users/Residential-level/{color_name}/User_3.png",
            ],
            "equipments": [
                f"/Users/joaop_27h1t5j/Desktop/IST/Bolsa/NetMaster/Equipments/Residential-level/{color_name}/Equipment_1.png",
                f"/Users/joaop_27h1t5j/Desktop/IST/Bolsa/NetMaster/Equipments/Residential-level/{color_name}/Equipment_2.png",
            ],
            "services": [
                f"/Users/joaop_27h1t5j/Desktop/IST/Bolsa/NetMaster/Services/Residential-level/{color_name}/Service_1.png",
                f"/Users/joaop_27h1t5j/Desktop/IST/Bolsa/NetMaster/Services/Residential-level/{color_name}/Service_2.png",
            ]
        }
        
        # Adicionar ao inventário para teste
        for card_type, card_paths in test_cards.items():
            for carta_path in card_paths:
                if os.path.exists(carta_path) and carta_path not in self.inventario[card_type]:
                    self.inventario[card_type].append(carta_path)
                    print(f"DEBUG: [TESTE] Carta {card_type} adicionada ao inventário: {os.path.basename(carta_path)}")
        
        # Atualizar cache e destaques se necessário
        self._check_user_inventory_for_carousel_access()
        # IMPORTANTE: Só atualizar destaques se estivermos na interface principal e Next Phase estiver ativo
        # Evita erro de widgets destruídos durante transições
        if (getattr(self, '_next_phase_active', False) and 
            hasattr(self, 'card_labels') and 
            self.card_labels and 
            not getattr(self, '_inventory_opening', False)):
            try:
                self._update_carousel_highlights()
            except Exception as e:
                print(f"DEBUG: [TESTE] Erro ao atualizar destaques do carrossel: {e}")
        
        print(f"DEBUG: [TESTE] Inventário atual após adicionar cartas de teste:")
        for tipo, cartas in self.inventario.items():
            if cartas:
                print(f"DEBUG: [TESTE]   {tipo}: {len(cartas)} cartas")
                for carta in cartas[:3]:  # Mostrar primeiras 3
                    print(f"DEBUG: [TESTE]     - {os.path.basename(carta)}")
        
        print(f"DEBUG: [TESTE] Estado inicial das cartas ativas:")
        print(f"DEBUG: [TESTE]   Users ativos: {[os.path.basename(c) for c in self.active_users]} (máx: {self.max_users})")
        print(f"DEBUG: [TESTE]   Equipments ativos: {[os.path.basename(c) for c in self.active_equipments]} (sem limite)")
        print(f"DEBUG: [TESTE]   Services ativos: {[os.path.basename(c) for c in self.active_services]} (sem limite)")
        print(f"DEBUG: [TESTE] NOTA: Ativação só funciona após clicar 'Next Phase'")
        print(f"DEBUG: [TESTE] Inventário Users atual: {[os.path.basename(c) for c in self.inventario['users']]}")
    
    def _update_carousel_highlights(self):
        """
        Atualiza os destaques roxos das cartas do carrossel baseado nos User IDs disponíveis.
        Chama esta função quando Next Phase é ativado ou quando o inventário de Users muda.
        """
        if not hasattr(self, 'card_labels') or not self.card_labels:
            print("DEBUG: _update_carousel_highlights - card_labels não existe ou está vazio, saltando atualização")
            return
        
        # Usar a função de seleção que já inclui a lógica de User IDs
        self._update_carousel_selection_highlights()
    
    def _debug_force_highlight_update(self):
        """
        Função de debug para forçar atualização dos destaques do carrossel.
        Útil para testar o sistema manualmente.
        """
        print("DEBUG: [FORÇA] Forçando atualização dos destaques do carrossel...")
        self._check_user_inventory_for_carousel_access()
        self._update_carousel_highlights()
        print("DEBUG: [FORÇA] Atualização dos destaques concluída")



    def abrir_inventario_para_carrossel(self, carrossel_idx):
        # Verificar se estamos numa casa onde podemos vender Activities ou Challenges
        casa_atual_tipo = getattr(self, 'current_casa_tipo', 'neutral')
        
        # PROTEÇÃO CONTRA LOOP: Se já estamos a mostrar inventário, não abrir novamente
        if getattr(self, '_inventory_opening', False):
            return
        
        # BLOQUEIO DURANTE FINAL PHASE: Não permite abrir inventário
        if getattr(self, '_final_phase_active', False):
            print(f"DEBUG: Abertura de inventário BLOQUEADA durante Final Phase")
            return
        
        # CONTROLO DE ACESSO DURANTE NEXT PHASE
        if getattr(self, '_next_phase_active', False):
            if not self._can_access_carousel_position(carrossel_idx):
                print(f"DEBUG: Acesso negado à posição {carrossel_idx} do carrossel durante Next Phase")
                return
        
        # IMPORTANTE: Se Next Phase está ativo, sempre abrir inventário no modo Next Phase
        if getattr(self, '_next_phase_active', False):
            print("DEBUG: Next Phase ativo - abrindo inventário no modo Next Phase")
            # Abre o inventário de Activities/Challenges para escolher carta para o carrossel
            self.carrossel_idx_selecao = carrossel_idx
            self.show_inventory_matrix_carrossel(["activities", "challenges"])
        # Se estivermos numa casa Activities ou Challenges E Next Phase NÃO está ativo, mostrar inventário para venda
        elif casa_atual_tipo in ["activities", "challenges"]:
            print(f"DEBUG: Em casa {casa_atual_tipo} - abrindo inventário para venda (Activities + Challenges)")
            self.show_inventory_matrix(["activities", "challenges"], page=0)
        else:
            print("DEBUG: Não em casa Activities/Challenges - abrindo inventário para carrossel")
            # Abre o inventário de Activities/Challenges para escolher carta para o carrossel
            self.carrossel_idx_selecao = carrossel_idx
            self.show_inventory_matrix_carrossel(["activities", "challenges"])

    def show_inventory_matrix_carrossel(self, tipos, page=0):
        print(f"DEBUG: show_inventory_matrix_carrossel chamado - tipos: {tipos}, page: {page}")
        
        # PROTEÇÃO CONTRA LOOP: Marcar que estamos a abrir inventário
        self._inventory_opening = True
        
        # Inventário em grelha 2x2 com navegação por páginas
        for widget in self.winfo_children():
            if hasattr(self, 'topbar_label') and widget == self.topbar_label:
                continue
            widget.destroy()
        
        # IMPORTANTE: Verificar se a TopBar existe, se não, criá-la
        if not hasattr(self, 'topbar_label') or not self.topbar_label.winfo_exists():
            print("DEBUG: TopBar não existe no carrossel, criando...")
            screen_width = self.winfo_screenwidth()
            topbar_img_path = os.path.join(IMG_DIR, f"TopBar_{self.player_color.lower()}.png")
            img = Image.open(topbar_img_path).convert("RGBA")
            img = img.resize((screen_width, 60), Image.Resampling.LANCZOS)
            topbar_img = ImageTk.PhotoImage(img)
            self.topbar_label = tk.Label(self, image=topbar_img, bg="black", borderwidth=0, highlightthickness=0)
            self.topbar_label.image = topbar_img  # type: ignore[attr-defined]
            self.topbar_label.pack(side="top", fill="x")
            print("DEBUG: TopBar criada com sucesso no carrossel")
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        name_lbl = tk.Label(self, text=self.player_name, font=("Helvetica", 18, "bold"), bg=self.bar_color, fg="black", borderwidth=0)
        name_lbl.place(relx=0.5, y=25, anchor="n")
        if len(tipos) == 1:
            title_str = tipos[0].capitalize()
        else:
            title_str = "Activities / Challenges"
        title = tk.Label(self, text=title_str, font=("Helvetica", 22, "bold"), fg="white", bg="black")
        title.place(relx=0.5, y=65, anchor="n")
        
        # VERIFICAR SE É ACTIVITIES/CHALLENGES PARA LAYOUT ESPECIAL EM COLUNAS
        if set(tipos) == set(["activities", "challenges"]):
            print("DEBUG: Activities/Challenges detectado - usando layout em colunas")
            
            # Separar cartas por tipo
            cartas_activities = self.inventario.get("activities", [])
            cartas_challenges = self.inventario.get("challenges", [])
            print(f"DEBUG: Activities: {len(cartas_activities)} cartas, Challenges: {len(cartas_challenges)} cartas")
            
            # Paginação baseada no maior número de cartas de qualquer tipo
            max_cards = max(len(cartas_activities), len(cartas_challenges))
            cards_per_page = 2  # 2 linhas, 1 carta de cada tipo por linha
            total_pages = max(1, (max_cards + cards_per_page - 1) // cards_per_page)
            page = max(0, min(page, total_pages - 1))
            start_idx = page * cards_per_page
            end_idx = start_idx + cards_per_page
            
            matriz_frame = tk.Frame(self, bg="black")
            matriz_frame.place(relx=0.5, rely=0.5, anchor="center")
            card_w, card_h = 85, 120
            
            # Configurar colunas do grid
            matriz_frame.grid_columnconfigure(0, weight=1, minsize=card_w + 16)  # Coluna Activities
            matriz_frame.grid_columnconfigure(1, weight=1, minsize=card_w + 16)  # Coluna Challenges
            
            # Colocar Activities na coluna 0 (esquerda)
            activities_row = 0
            for i in range(start_idx, min(end_idx, len(cartas_activities))):
                carta_path = cartas_activities[i]
                try:
                    img = ImageTk.PhotoImage(Image.open(carta_path).resize((card_w, card_h)))
                    carta_lbl = tk.Label(matriz_frame, image=img, bg="black", cursor="hand2")
                    carta_lbl.image = img  # type: ignore[attr-defined]
                    carta_lbl.grid(row=activities_row, column=0, padx=8, pady=8)
                    
                    # Configurar comportamento baseado no modo
                    if getattr(self, '_next_phase_active', False):
                        carta_lbl.bind("<Button-1>", lambda e, p=carta_path, t=tipos, pg=page: self.show_card_fullscreen_next_phase_selection(p, t, pg))
                        print(f"DEBUG: Activity configurada para modo Next Phase na posição ({activities_row}, 0): {os.path.basename(carta_path)}")
                    else:
                        carta_lbl.bind("<Button-1>", lambda e, p=carta_path, t=tipos, pg=page: self.show_card_fullscreen_carrossel_selecao(p, t, pg))
                        print(f"DEBUG: Activity adicionada na posição ({activities_row}, 0): {os.path.basename(carta_path)}")
                    
                    activities_row += 1
                except Exception:
                    print(f"DEBUG: Erro ao carregar Activity {carta_path}")
                    continue
            
            # Colocar Challenges na coluna 1 (direita)
            challenges_row = 0
            for i in range(start_idx, min(end_idx, len(cartas_challenges))):
                carta_path = cartas_challenges[i]
                try:
                    img = ImageTk.PhotoImage(Image.open(carta_path).resize((card_w, card_h)))
                    carta_lbl = tk.Label(matriz_frame, image=img, bg="black", cursor="hand2")
                    carta_lbl.image = img  # type: ignore[attr-defined]
                    carta_lbl.grid(row=challenges_row, column=1, padx=8, pady=8)
                    
                    # Configurar comportamento baseado no modo
                    if getattr(self, '_next_phase_active', False):
                        carta_lbl.bind("<Button-1>", lambda e, p=carta_path, t=tipos, pg=page: self.show_card_fullscreen_next_phase_selection(p, t, pg))
                        print(f"DEBUG: Challenge configurado para modo Next Phase na posição ({challenges_row}, 1): {os.path.basename(carta_path)}")
                    else:
                        carta_lbl.bind("<Button-1>", lambda e, p=carta_path, t=tipos, pg=page: self.show_card_fullscreen_carrossel_selecao(p, t, pg))
                        print(f"DEBUG: Challenge adicionado na posição ({challenges_row}, 1): {os.path.basename(carta_path)}")
                    
                    challenges_row += 1
                except Exception:
                    print(f"DEBUG: Erro ao carregar Challenge {carta_path}")
                    continue
            
            # Se não há cartas em nenhuma das colunas
            if activities_row == 0 and challenges_row == 0:
                no_cards_lbl = tk.Label(matriz_frame, text="Sem cartas disponíveis!", font=("Helvetica", 16), bg="black", fg="white")
                no_cards_lbl.grid(row=0, column=0, columnspan=2, pady=20)
                print("DEBUG: Nenhuma carta de Activities/Challenges - adicionado label 'Sem cartas disponíveis!'")
            
        else:
            # Layout normal para outros tipos (comportamento original)
            cartas = []
            for t in tipos:
                cartas += self.inventario.get(t, [])
            print(f"DEBUG: Cartas encontradas no inventário: {len(cartas)} cartas")
            
            # Paginação
            cards_per_page = 4
            total_pages = max(1, (len(cartas) + cards_per_page - 1) // cards_per_page)
            page = max(0, min(page, total_pages - 1))
            start_idx = page * cards_per_page
            end_idx = start_idx + cards_per_page
            cartas_page = cartas[start_idx:end_idx]
            print(f"DEBUG: Página {page}/{total_pages-1}, mostrando cartas {start_idx} a {end_idx-1}, cartas na página: {len(cartas_page)}")
            
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
                    print(f"DEBUG: Erro ao carregar carta {carta_path}")
                    continue
                carta_lbl = tk.Label(matriz_frame, image=img, bg="black", cursor="hand2")
                carta_lbl.image = img  # type: ignore[attr-defined]
                carta_lbl.grid(row=row, column=col, padx=8, pady=8)
                
                # Verificar se Next Phase está ativo para comportamento especial
                if getattr(self, '_next_phase_active', False):
                    # No modo Next Phase, primeira carta clicada vai direto para fullscreen com X e ✔
                    carta_lbl.bind("<Button-1>", lambda e, p=carta_path, t=tipos, pg=page: self.show_card_fullscreen_next_phase_selection(p, t, pg))
                    print(f"DEBUG: Carta {idx} configurada para modo Next Phase na posição ({row}, {col}): {os.path.basename(carta_path)}")
                else:
                    # Comportamento normal - ir para seleção do carrossel
                    carta_lbl.bind("<Button-1>", lambda e, p=carta_path, t=tipos, pg=page: self.show_card_fullscreen_carrossel_selecao(p, t, pg))
                    print(f"DEBUG: Carta {idx} adicionada na posição ({row}, {col}): {os.path.basename(carta_path)}")
            
            if not cartas_page:
                no_cards_lbl = tk.Label(matriz_frame, text="Sem cartas disponíveis!", font=("Helvetica", 16), bg="black", fg="white")
                no_cards_lbl.pack(pady=20)
                print("DEBUG: Nenhuma carta na página - adicionado label 'Sem cartas disponíveis!'")
        
        # Setas de navegação
        if total_pages > 1:
            # Coordenadas para alinhar as setas à direita da grelha de cartas
            # Assume que a grelha está centrada em relx=0.5, então relx=0.85 fica à direita
            seta_x = 0.90
            # Seta para cima (▲) - parte superior direita da grelha
            if page > 0:
                seta_cima = tk.Button(self, text="▲", font=("Helvetica", 18, "bold"), bg="#222", fg="white", width=2, command=lambda: self.show_inventory_matrix_carrossel(tipos, page-1))
                seta_cima.place(relx=seta_x, rely=0.38, anchor="center")
                print("DEBUG: Seta para cima adicionada")
            # Seta para baixo (▼) - parte inferior direita da grelha
            if page < total_pages - 1:
                seta_baixo = tk.Button(self, text="▼", font=("Helvetica", 18, "bold"), bg="#222", fg="white", width=2, command=lambda: self.show_inventory_matrix_carrossel(tipos, page+1))
                seta_baixo.place(relx=seta_x, rely=0.62, anchor="center")
                print("DEBUG: Seta para baixo adicionada")
        
        # Adicionar barra inferior com imagem BelowBar_X.png (onde X é a cor do jogador)
        try:
            belowbar_img_path = os.path.join(IMG_DIR, f"BelowBar_{self.player_color.lower()}.png")
            belowbar_img = ImageTk.PhotoImage(Image.open(belowbar_img_path).resize((screen_width, 50)))
            belowbar_label = tk.Label(self, image=belowbar_img, bg="black")
            belowbar_label.image = belowbar_img  # type: ignore[attr-defined]
            belowbar_label.pack(side="bottom", fill="x")
            print(f"DEBUG: Barra inferior BelowBar_{self.player_color.lower()}.png carregada com sucesso")
        except Exception as e:
            print(f"DEBUG: Erro ao carregar BelowBar_{self.player_color.lower()}.png: {e}")
            # Fallback: criar uma barra colorida se a imagem não existir
            belowbar_frame = tk.Frame(self, bg=self.bar_color, height=50)
            belowbar_frame.pack(side="bottom", fill="x")
            belowbar_frame.pack_propagate(False)

        # Botão Back centrado na parte inferior - criado após a barra para ficar por cima
        def back_to_dashboard_carrossel():
            # PROTEÇÃO CONTRA LOOP: Limpar flag antes de voltar ao dashboard
            self._inventory_opening = False
            self.playerdashboard_interface(self.player_name, self.saldo, self.other_players)
        back_btn = tk.Button(self, text="Back", font=("Helvetica", 14, "bold"), bg="#808080", fg="white", width=6, command=back_to_dashboard_carrossel)
        back_btn.place(relx=0.5, rely=0.98, anchor="s")

        # Saldo no canto inferior direito - criado após para ficar por cima
        self.after(100, lambda: self.create_coin_saldo_overlay(screen_width, screen_height, self.saldo))
        
        print(f"DEBUG: show_inventory_matrix_carrossel terminado com sucesso")

    def show_card_fullscreen_carrossel_selecao(self, carta_path, tipos, page=0):
        # Mostra carta em fullscreen com botões ✔ (aceitar) e ✖ (cancelar)
        for widget in self.winfo_children():
            if hasattr(self, 'topbar_label') and widget == self.topbar_label:
                continue
            widget.destroy()
        
        # IMPORTANTE: Verificar se a TopBar existe, se não, criá-la
        if not hasattr(self, 'topbar_label') or not self.topbar_label.winfo_exists():
            print("DEBUG: TopBar não existe no fullscreen carrossel, criando...")
            screen_width = self.winfo_screenwidth()
            topbar_img_path = os.path.join(IMG_DIR, f"TopBar_{self.player_color.lower()}.png")
            img = Image.open(topbar_img_path).convert("RGBA")
            img = img.resize((screen_width, 60), Image.Resampling.LANCZOS)
            topbar_img = ImageTk.PhotoImage(img)
            self.topbar_label = tk.Label(self, image=topbar_img, bg="black", borderwidth=0, highlightthickness=0)
            self.topbar_label.image = topbar_img  # type: ignore[attr-defined]
            self.topbar_label.pack(side="top", fill="x")
            print("DEBUG: TopBar criada com sucesso no fullscreen carrossel")
        
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
        # Botão ✖ canto superior esquerdo - volta para página de inventário
        def voltar_inventario():
            self.show_inventory_matrix_carrossel(tipos, page)
        btn_x = tk.Button(self, text="✖", font=("Helvetica", 24, "bold"), bg="#AAAAAA", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=voltar_inventario, cursor="hand2", activebackground="#CCCCCC")
        btn_x.place(relx=0.02, rely=0, anchor="nw")
        # Botão Switch canto superior direito (APENAS se NÃO for Activities vendável)
        # Para Activities vendáveis, o botão ✔ irá ocupar esta posição
        carta_tipo_temp = "challenges"  # Valor padrão
        if set(tipos) == set(["activities", "challenges"]):
            import os
            carta_basename = os.path.basename(carta_path).lower()
            if "activity" in carta_basename or "activities" in carta_basename:
                carta_tipo_temp = "activities"
            elif "challenge" in carta_basename or "challenges" in carta_basename:
                carta_tipo_temp = "challenges"
        
        # Verificar se é Activities vendável
        casa_atual_tipo = getattr(self, 'current_casa_tipo', 'neutral')
        if casa_atual_tipo == "equipment":
            casa_atual_tipo = "equipments"
        
        activities_vendavel = (carta_tipo_temp == "activities" and 
                              not getattr(self, '_next_phase_active', False) and 
                              casa_atual_tipo == "activities")
        
        # Só criar botão Switch se NÃO for Activities vendável E se Next Phase estiver ativo
        next_phase_active = getattr(self, '_next_phase_active', False)
        if not activities_vendavel and next_phase_active:
            try:
                switch_img_path = os.path.join(IMG_DIR, "switch_card.png")
                if os.path.exists(switch_img_path):
                    switch_img = ImageTk.PhotoImage(Image.open(switch_img_path).resize((48, 48)))
                    btn_switch_carrossel = tk.Button(self, image=switch_img, bg="#FF9800", borderwidth=0, highlightthickness=0, cursor="hand2", activebackground="#E68900")
                    btn_switch_carrossel.image = switch_img  # Manter referência
                    btn_switch_carrossel.place(relx=0.98, rely=0, anchor="ne")
                    btn_switch_carrossel.config(command=lambda: self.aceitar_carta_carrossel(carta_path, tipos, page))
                    print(f"DEBUG: [CARROSSEL] Botão Switch criado durante Next Phase")
                else:
                    btn_switch_carrossel = None
                    print(f"DEBUG: [CARROSSEL] Botão Switch NÃO criado - imagem não encontrada em {switch_img_path}")
            except Exception as e:
                btn_switch_carrossel = None
                print(f"DEBUG: [CARROSSEL] Botão Switch NÃO criado - erro ao carregar imagem: {e}")
        else:
            btn_switch_carrossel = None
            if not next_phase_active:
                print(f"DEBUG: [CARROSSEL] Botão Switch NÃO criado - Next Phase não está ativo")
            elif activities_vendavel:
                print(f"DEBUG: [CARROSSEL] Botão Switch NÃO criado - Activities vendável irá usar posição para botão ✔")
        
        # Adicionar lógica de venda (igual ao show_card_fullscreen_inventory)
        pode_vender = False
        casa_atual_tipo = getattr(self, 'current_casa_tipo', 'neutral')
        
        # IMPORTANTE: Se Next Phase estiver ativo, NÃO pode vender nenhuma carta
        if getattr(self, '_next_phase_active', False):
            print(f"DEBUG: NÃO pode vender carta do carrossel - Next Phase está ativo (vendas desabilitadas)")
            pode_vender = False
        else:
            # Normalizar o tipo da casa atual (equipments vs equipment)
            if casa_atual_tipo == "equipment":
                casa_atual_tipo = "equipments"
            
            # Determinar o tipo da carta atual
            carta_tipo = None
            if len(tipos) == 1:
                carta_tipo = tipos[0]
            elif set(tipos) == set(["activities", "challenges"]):
                # Se é uma página Activities/Challenges, determinar tipo pela carta específica
                import os
                carta_basename = os.path.basename(carta_path).lower()
                if "activity" in carta_basename or "activities" in carta_basename:
                    carta_tipo = "activities"
                elif "challenge" in carta_basename or "challenges" in carta_basename:
                    carta_tipo = "challenges"
                else:
                    # Tentar determinar pelo caminho da pasta
                    carta_dirname = os.path.dirname(carta_path).lower()
                    if "activities" in carta_dirname:
                        carta_tipo = "activities"
                    elif "challenges" in carta_dirname:
                        carta_tipo = "challenges"
            
            print(f"DEBUG: Verificando possibilidade de venda carrossel - carta_tipo: {carta_tipo}, casa_atual_tipo: {casa_atual_tipo}")
            
            # Verificar se pode vender
            if carta_tipo in ["users", "equipments", "services"]:
                # Para estas cartas, precisa estar na casa do mesmo tipo
                if casa_atual_tipo == carta_tipo:
                    pode_vender = True
            elif carta_tipo in ["activities", "challenges"]:
                # Activities só podem ser vendidas numa casa Activities, Challenges só numa casa Challenges
                if casa_atual_tipo == carta_tipo:
                    pode_vender = True
        
        # Adicionar lógica de venda (igual ao show_card_fullscreen_inventory)
        # IMPORTANTE: Para Activities e Challenges, usar layout especial sem botão picoin verde
        if pode_vender and carta_tipo not in ["activities", "challenges"]:
            print(f"DEBUG: Pode vender carta {carta_tipo} do carrossel - está numa casa {casa_atual_tipo}")
            picoin_img = ImageTk.PhotoImage(Image.open(COIN_IMG).resize((48,48)))
            def abrir_confirm():
                # Guardar informações para navegação correta
                self._origem_venda = "carrossel"
                self._tipos_venda = tipos
                self._page_venda = page
                self._current_sell_page = page
                # CORREÇÃO: Se viemos de um inventário Activities/Challenges, guardar isso
                if set(tipos) == set(["activities", "challenges"]):
                    self._inventario_conjunto = True
                else:
                    self._inventario_conjunto = False
                print(f"DEBUG: Iniciando venda do carrossel - carta_tipo: {carta_tipo}, inventario_conjunto: {getattr(self, '_inventario_conjunto', False)}, page: {page}")
                self.show_sell_confirmation(carta_path, carta_tipo, store_window=None)
            btn_picoin = tk.Button(self, image=picoin_img, bg="#4CAF50", borderwidth=0, command=abrir_confirm, cursor="hand2")
            btn_picoin.image = picoin_img  # type: ignore[attr-defined]
            btn_picoin.place(relx=0, rely=1, anchor="sw")
        elif pode_vender and carta_tipo in ["activities", "challenges"]:
            print(f"DEBUG: Carta {carta_tipo} pode ser vendida mas usa layout especial - botão ✔ já configurado acima")
        else:
            print(f"DEBUG: NÃO pode vender carta {carta_tipo} do carrossel - casa atual: {casa_atual_tipo}, necessário: {carta_tipo}")
        
        # Para Activities e Challenges no carrossel, aplicar layout especial similar ao inventário
        if carta_tipo in ["activities", "challenges"]:
            print(f"DEBUG: [CARROSSEL] Processando carta tipo {carta_tipo} - pode_vender: {pode_vender}")
            
            # Para Activities que podem ser vendidas, reconfigurar o botão Switch para venda
            if carta_tipo == "activities" and pode_vender:
                # Substituir comando do botão Switch para abrir venda em vez de aceitar para carrossel
                def abrir_confirm_activities():
                    # Limpar estado anterior e guardar informações para navegação correta
                    self._origem_venda = "carrossel"
                    self._tipos_venda = tipos
                    self._page_venda = page
                    self._current_sell_page = page
                    # Se viemos de um inventário Activities/Challenges, guardar isso
                    if set(tipos) == set(["activities", "challenges"]):
                        self._inventario_conjunto = True
                    else:
                        self._inventario_conjunto = False
                    print(f"DEBUG: [CARROSSEL] Iniciando venda Activities - carta_tipo: {carta_tipo}, inventario_conjunto: {getattr(self, '_inventario_conjunto', False)}, page: {page}")
                    self.show_sell_confirmation(carta_path, carta_tipo, store_window=None)
                
                # Criar botão de venda adicional (✔) para Activities vendáveis na mesma posição padrão
                btn_venda_activities = tk.Button(self, text="✔", font=("Helvetica", 24, "bold"), bg="#4CAF50", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, cursor="hand2", activebackground="#43d17a")
                btn_venda_activities.place(relx=0.98, rely=0, anchor="ne")  # Posição consistente com inventário
                btn_venda_activities.config(command=abrir_confirm_activities)
                print(f"DEBUG: [CARROSSEL] Botão ✔ criado para venda de Activities na posição padrão")
                
                # Reposicionar botão Switch para baixo para não conflitar
                try:
                    switch_img_path = os.path.join(IMG_DIR, "switch_card.png")
                    if os.path.exists(switch_img_path):
                        switch_img = ImageTk.PhotoImage(Image.open(switch_img_path).resize((48, 48)))
                        btn_switch_adicional = tk.Button(self, image=switch_img, bg="#FF9800", borderwidth=0, highlightthickness=0, cursor="hand2", activebackground="#E68900")
                        btn_switch_adicional.image = switch_img  # Manter referência
                        btn_switch_adicional.place(relx=1, rely=1, anchor="se")
                        print(f"DEBUG: [CARROSSEL] Botão Switch adicional criado com imagem switch_card.png")
                    else:
                        btn_switch_adicional = None
                        print(f"DEBUG: [CARROSSEL] Botão Switch adicional NÃO criado - imagem não encontrada em {switch_img_path}")
                except Exception as e:
                    btn_switch_adicional = None
                    print(f"DEBUG: [CARROSSEL] Botão Switch adicional NÃO criado - erro ao carregar imagem: {e}")
                
                def switch_action():
                    # Aceitar carta para o carrossel (comportamento original do botão ✔)
                    self.aceitar_carta_carrossel(carta_path, tipos, page)
                
                if btn_switch_adicional is not None:
                    btn_switch_adicional.config(command=switch_action)
                    print(f"DEBUG: [CARROSSEL] Botão Switch adicional configurado para Activities")
            
            # Para Challenges ou Activities que não podem ser vendidas, manter comportamento original do Switch
            elif carta_tipo == "challenges" or (carta_tipo == "activities" and not pode_vender):
                print(f"DEBUG: [CARROSSEL] Botão Switch mantém comportamento original para {carta_tipo} (aceitar no carrossel)")

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

    def show_card_fullscreen_next_phase_selection(self, carta_path, tipos, page=0):
        """
        Mostra carta em fullscreen no modo Next Phase com apenas X e ✔
        Usado quando Next Phase está ativo e o utilizador clica numa carta do inventário
        """
        print(f"DEBUG: show_card_fullscreen_next_phase_selection chamado - Next Phase ativo")
        
        # Limpa widgets (menos barra superior)
        for widget in self.winfo_children():
            if hasattr(self, 'topbar_label') and widget == self.topbar_label:
                continue
            widget.destroy()
        
        # IMPORTANTE: Verificar se a TopBar existe, se não, criá-la
        if not hasattr(self, 'topbar_label') or not self.topbar_label.winfo_exists():
            print("DEBUG: TopBar não existe no fullscreen Next Phase, criando...")
            screen_width = self.winfo_screenwidth()
            topbar_img_path = os.path.join(IMG_DIR, f"TopBar_{self.player_color.lower()}.png")
            img = Image.open(topbar_img_path).convert("RGBA")
            img = img.resize((screen_width, 60), Image.Resampling.LANCZOS)
            topbar_img = ImageTk.PhotoImage(img)
            self.topbar_label = tk.Label(self, image=topbar_img, bg="black", borderwidth=0, highlightthickness=0)
            self.topbar_label.image = topbar_img  # type: ignore[attr-defined]
            self.topbar_label.pack(side="top", fill="x")
            print("DEBUG: TopBar criada com sucesso no fullscreen Next Phase")

        # Mostrar carta em fullscreen
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
        
        # Botão X no canto superior esquerdo - volta para a página de inventário Activities/Challenges
        def voltar_inventario():
            print("DEBUG: Voltando para página de inventário Activities/Challenges do modo Next Phase")
            self.show_inventory_matrix_carrossel(tipos, page)
        
        btn_x = tk.Button(self, text="✖", font=("Helvetica", 24, "bold"), bg="#AAAAAA", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, command=voltar_inventario, cursor="hand2", activebackground="#CCCCCC")
        btn_x.place(relx=0.02, rely=0, anchor="nw")
        
        # Botão Switch no canto superior direito - aceita carta para o carrossel e vai para dashboard
        # APENAS se Final Phase NÃO estiver ativo
        final_phase_active = getattr(self, '_final_phase_active', False)
        
        if not final_phase_active:
            def aceitar_carta():
                print("DEBUG: [NEXT PHASE] *** aceitar_carta CHAMADA ***")
                print(f"DEBUG: [NEXT PHASE] carta_path: {carta_path}")
                print(f"DEBUG: [NEXT PHASE] tipos: {tipos}")
                
                # Substituir a carta no carrossel
                idx = getattr(self, 'carrossel_idx_selecao', 0)
                print(f"DEBUG: [NEXT PHASE] carrossel_idx_selecao: {idx}")
                
                self.cards[idx] = carta_path
                self.selected_card_idx = idx
                print(f"DEBUG: [NEXT PHASE] Carta substituída no carrossel na posição {idx}")
                
                # Remover carta do inventário
                for t in tipos:
                    if carta_path in self.inventario.get(t, []):
                        self.inventario[t].remove(carta_path)
                        print(f"DEBUG: [NEXT PHASE] Removida carta {carta_path} do inventário {t}")
                        break
                
                # Voltar à interface principal
                print("DEBUG: [NEXT PHASE] *** CHAMANDO playerdashboard_interface ***")
                try:
                    self.playerdashboard_interface(self.player_name, self.saldo, self.other_players)
                    print("DEBUG: [NEXT PHASE] playerdashboard_interface chamada com sucesso!")
                except Exception as e:
                    print(f"DEBUG: [NEXT PHASE] ERRO ao chamar playerdashboard_interface: {e}")
                    import traceback
                    traceback.print_exc()
            
            try:
                switch_img_path = os.path.join(IMG_DIR, "switch_card.png")
                if os.path.exists(switch_img_path):
                    switch_img = ImageTk.PhotoImage(Image.open(switch_img_path).resize((48, 48)))
                    btn_switch_next_phase = tk.Button(self, image=switch_img, bg="#FF9800", borderwidth=0, highlightthickness=0, cursor="hand2", activebackground="#E68900")
                    btn_switch_next_phase.image = switch_img  # Manter referência
                    print(f"DEBUG: [NEXT PHASE] Botão Switch criado com imagem switch_card.png")
                else:
                    # Fallback para botão texto se imagem não existir
                    btn_switch_next_phase = tk.Button(self, text="⇄", font=("Helvetica", 20, "bold"), bg="#FF9800", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, cursor="hand2", activebackground="#E68900")
                    print(f"DEBUG: [NEXT PHASE] Botão Switch criado com texto (imagem não encontrada em {switch_img_path})")
            except Exception as e:
                # Fallback para botão texto em caso de erro
                btn_switch_next_phase = tk.Button(self, text="⇄", font=("Helvetica", 20, "bold"), bg="#FF9800", fg="white", width=2, height=1, borderwidth=0, highlightthickness=0, cursor="hand2", activebackground="#E68900")
                print(f"DEBUG: [NEXT PHASE] Botão Switch criado com texto (erro ao carregar imagem: {e})")
            
            if btn_switch_next_phase is not None:
                btn_switch_next_phase.place(relx=0.98, rely=0, anchor="ne")
                btn_switch_next_phase.config(command=aceitar_carta)
        else:
            print(f"DEBUG: [NEXT PHASE] Botão Switch NÃO criado - Final Phase está ativo")
        
        print("DEBUG: Fullscreen Next Phase configurado - apenas X disponível durante Final Phase")

    def add_more_action_event_cards(self, min_actions=5, min_events=6):
        """
        Adiciona mais cartas de Actions/Events ao inventário se houver poucas.
        Usa filtragem baseada na base de dados para adicionar apenas cartas válidas.
        """
        if not hasattr(self, 'card_database') or not self.card_database:
            print("DEBUG: [add_more_action_event_cards] Base de dados não disponível")
            return
        
        player_color = self.player_color.lower()
        base_path = "/Users/joaop_27h1t5j/Desktop/IST/Bolsa/NetMaster"
        
        # Verificar Actions
        current_actions = len(self.inventario.get("actions", []))
        if current_actions < min_actions:
            print(f"DEBUG: [add_more_action_event_cards] Actions insuficientes ({current_actions}/{min_actions}), adicionando mais...")
            actions_path = os.path.join(base_path, "Actions", "Residential-level")
            if os.path.exists(actions_path):
                try:
                    files = os.listdir(actions_path)
                    action_files = [os.path.join(actions_path, f) for f in files if f.lower().endswith('.png')]
                    
                    valid_actions = []
                    for card_file in action_files:
                        filename = os.path.basename(card_file)
                        match = re.search(r'Action_(\d+)\.', filename)
                        if match:
                            card_id = f"action_{match.group(1)}"
                            card_data = self.card_database.get_action(card_id)
                            if card_data:
                                target = getattr(card_data, 'target', None)
                                player_choice = getattr(card_data, 'player_choice', False)
                                if target == player_color or (target is None and player_choice):
                                    if card_file not in self.inventario.get("actions", []):
                                        valid_actions.append(card_file)
                    
                    # Adicionar cartas até atingir o mínimo
                    needed = min_actions - current_actions
                    for i in range(min(needed, len(valid_actions))):
                        self.inventario["actions"].append(valid_actions[i])
                        print(f"DEBUG: [add_more_action_event_cards] Action adicionada: {os.path.basename(valid_actions[i])}")
                
                except Exception as e:
                    print(f"DEBUG: [add_more_action_event_cards] Erro ao adicionar Actions: {e}")
        
        # Verificar Events
        current_events = len(self.inventario.get("events", []))
        if current_events < min_events:
            print(f"DEBUG: [add_more_action_event_cards] Events insuficientes ({current_events}/{min_events}), adicionando mais...")
            events_path = os.path.join(base_path, "Events", "Residential-level")
            if os.path.exists(events_path):
                try:
                    files = os.listdir(events_path)
                    event_files = [os.path.join(events_path, f) for f in files if f.lower().endswith('.png')]
                    
                    valid_events = []
                    for card_file in event_files:
                        filename = os.path.basename(card_file)
                        match = re.search(r'Event_(\d+)\.', filename)
                        if match:
                            card_id = f"event_{match.group(1)}"
                            card_data = self.card_database.get_event(card_id)
                            if card_data:
                                target = getattr(card_data, 'target_player', None)
                                player_choice = getattr(card_data, 'player_choice', False)
                                if target == player_color or (target is None and player_choice):
                                    if card_file not in self.inventario.get("events", []):
                                        valid_events.append(card_file)
                    
                    # Adicionar cartas até atingir o mínimo
                    needed = min_events - current_events
                    for i in range(min(needed, len(valid_events))):
                        self.inventario["events"].append(valid_events[i])
                        print(f"DEBUG: [add_more_action_event_cards] Event adicionado: {os.path.basename(valid_events[i])}")
                
                except Exception as e:
                    print(f"DEBUG: [add_more_action_event_cards] Erro ao adicionar Events: {e}")
        
        print(f"DEBUG: [add_more_action_event_cards] Resultado final - Actions: {len(self.inventario.get('actions', []))}, Events: {len(self.inventario.get('events', []))}")

    def _filter_action_event_cards(self, cartas_paths, card_type):
        """
        Filtra cartas de Actions/Events baseado no target e player_choice.
        Só mostra cartas que:
        1. Têm target igual à cor do jogador atual, OU
        2. Têm target None e player_choice True (jogador pode escolher alvo)
        """
        if not hasattr(self, 'card_database') or not self.card_database:
            print(f"DEBUG: [_filter_action_event_cards] Base de dados não disponível - mostrando todas as cartas")
            return cartas_paths
        
        filtered_cards = []
        player_color = self.player_color.lower()
        
        for carta_path in cartas_paths:
            try:
                # Extrair ID da carta do nome do arquivo
                filename = os.path.basename(carta_path)
                if card_type == "actions":
                    # Action_1.png -> action_1
                    match = re.search(r'Action_(\d+)\.', filename)
                    if match:
                        card_id = f"action_{match.group(1)}"
                        card_data = self.card_database.get_action(card_id)
                    else:
                        continue
                elif card_type == "events":
                    # Event_1.png -> event_1
                    match = re.search(r'Event_(\d+)\.', filename)
                    if match:
                        card_id = f"event_{match.group(1)}"
                        card_data = self.card_database.get_event(card_id)
                    else:
                        continue
                else:
                    continue
                
                if card_data:
                    # Para Events, usar target_player; para Actions, usar target
                    if card_type == "events":
                        target = getattr(card_data, 'target_player', None)
                    else:
                        target = getattr(card_data, 'target', None)
                    player_choice = getattr(card_data, 'player_choice', False)
                    
                    # Critério de filtragem:
                    # 1. Target específico igual à cor do jogador
                    # 2. Target None com player_choice True
                    if target == player_color or (target is None and player_choice):
                        filtered_cards.append(carta_path)
                        print(f"DEBUG: [_filter_action_event_cards] Carta ACEITA: {filename} (target={target}, player_choice={player_choice})")
                    else:
                        print(f"DEBUG: [_filter_action_event_cards] Carta REJEITADA: {filename} (target={target}, player_choice={player_choice})")
                else:
                    print(f"DEBUG: [_filter_action_event_cards] Carta não encontrada na base de dados: {card_id}")
                    
            except Exception as e:
                print(f"DEBUG: [_filter_action_event_cards] Erro ao processar carta {filename}: {e}")
                continue
        
        print(f"DEBUG: [_filter_action_event_cards] Resultado final {card_type}: {len(filtered_cards)}/{len(cartas_paths)} cartas")
        return filtered_cards

    def reload_action_event_inventory(self):
        """
        Função de conveniência para recarregar o inventário de Actions/Events
        com mais cartas válidas para o jogador atual.
        """
        print("DEBUG: [reload_action_event_inventory] Recarregando inventário de Actions/Events...")
        
        # Limpar inventário atual (opcional)
        # self.inventario["actions"] = []
        # self.inventario["events"] = []
        
        # Adicionar mais cartas
        self.add_more_action_event_cards(min_actions=10, min_events=12)
        
        print(f"DEBUG: [reload_action_event_inventory] Inventário atualizado - Actions: {len(self.inventario.get('actions', []))}, Events: {len(self.inventario.get('events', []))}")

# Exemplo de uso isolado:
if __name__ == "__main__":
    root = tk.Tk()
    root.attributes("-fullscreen", True)  
    PlayerDashboard(root, player_color="red", saldo=1000, other_players=["green", "blue", "yellow"])
    check_gpio_key(root)
    root.mainloop()