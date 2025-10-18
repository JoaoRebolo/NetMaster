#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base de Dados de Cartas NetMaster
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Union
from enum import Enum
import re

class UserType(Enum):
    """Tipos de utilizadores disponíveis"""
    RESIDENTIAL = "residential"
    ENTERPRISE = "enterprise"
    ISP = "isp"

class EquipmentType(Enum):
    """Tipos de equipamentos disponíveis"""
    SMALL_ROUTER = "small_router"       # Small Router nas cartas físicas
    MEDIUM_ROUTER = "medium_router"     # Medium Router nas cartas físicas
    SHORT_LINK = "short_link"           # Short Link nas cartas físicas
    LONG_LINK = "long_link"             # Long Link nas cartas físicas
    
class ServiceType(Enum):
    """Tipos de serviços disponíveis"""
    BANDWIDTH = "bandwidth"
    DATA_VOLUME = "data_volume"
    TEMPORARY = "temporary"

class ActivityType(Enum):
    """Tipos de atividades disponíveis"""
    HOME_SURVEILLANCE = "home_surveillance"
    HOME_SAFETY = "home_safety"
    SHORT_MESSAGE = "short_message"
    GAMING = "gaming"
    FILE_TRANSFER = "file_transfer"

class ChallengeType(Enum):
    """Tipos de desafios disponíveis"""
    MESSAGE_MISSION = "message_mission"
    MESSAGE_SPRINT = "message_sprint"
    JACKPOT = "jackpot"
    PACKET_RACE = "packet_race"

class ActionType(Enum):
    """Tipos de ações disponíveis"""
    ROUTER_UPGRADE = "router_upgrade"
    ROUTER_DOWNGRADE = "router_downgrade"
    LINK_UPGRADE = "link_upgrade"
    LINK_DOWNGRADE = "link_downgrade"
    ADD_ROUTER = "add_router"
    REMOVE_ROUTER = "remove_router"

class EventType(Enum):
    """Tipos de eventos disponíveis"""
    TRANSMISSION_DELAY = "transmission_delay"
    LINK_FAILURE = "link_failure"
    TRAFFIC_BURST = "traffic_burst"
    QUEUE_CONGESTION = "queue_congestion"
    QUEUE_FULL = "queue_full"
    PACKET_DROP = "packet_drop"
    EMPTY_QUEUE = "empty_queue"

@dataclass
class UserCard:
    """Carta de utilizador"""
    user_id: str
    user_type: UserType
    color: str
    users_count: int        # Número de users que a carta representa
    applications: int       # Número de applications (antes era data_volume)
    services: int          # Número de services (antes era priority)
    buy_cost: int          # Preço de compra em picoins (antes era cost)
    sell_cost: int         # Preço de venda em picoins
    
    def __str__(self):
        return f"UserCard(id={self.user_id}, type={self.user_type.value}, color={self.color}, users={self.users_count}, apps={self.applications}, services={self.services})"
    
    def get_sell_price(self):
        """Retorna o preço de venda da carta"""
        return self.sell_cost
    
    # Propriedades para compatibilidade com código antigo
    @property
    def data_volume(self):
        """Compatibilidade: data_volume -> applications"""
        return self.applications
    
    @property
    def priority(self):
        """Compatibilidade: priority -> services"""
        return self.services
    
    @property
    def cost(self):
        """Compatibilidade: cost -> buy_cost"""
        return self.buy_cost

@dataclass
class EquipmentCard:
    """Carta de equipamento"""
    equipment_id: str           # ID único da carta (Equipment_1, Equipment_2, etc.)
    equipment_type: EquipmentType  # SHORT_ROUTER, MEDIUM_ROUTER, SHORT_LINK, LONG_LINK
    color: str                  # Cor da carta
    category: str              # "Router" ou "Link"
    model: str                 # "Short Router", "Medium Router", "Short Link", "Long Link"
    specific_id: int           # Router ID ou Link ID (1, 2, 3)
    # Campos específicos para Routers
    queue_size: Optional[int]  # Tamanho da queue em packets (apenas routers)
    # Campos específicos para Links  
    link_rate: Optional[str]   # Taxa do link, ex: "1 packet per turn" (apenas links)
    link_length: Optional[int] # Comprimento do link em packets (apenas links)
    # Campos comuns
    buy_cost: int             # Preço de compra em picoins
    sell_cost: int            # Preço de venda em picoins
    object_name: Optional[str] = None  # Nome do objeto para deteção (ex: "router_simples_vermelho")

    def __str__(self):
        if self.category == "Router":
            return f"EquipmentCard(id={self.equipment_id}, {self.model}, queue={self.queue_size}, object={self.object_name})"
        else:
            return f"EquipmentCard(id={self.equipment_id}, {self.model}, rate={self.link_rate}, length={self.link_length}, object={self.object_name})"

@dataclass
class ServiceCard:
    """Carta de serviço"""
    service_id: str             # ID único da carta (Service_1, Service_2, etc.)
    service_type: ServiceType   # BANDWIDTH, DATA_VOLUME, TEMPORARY
    color: str                  # Cor da carta
    title: str                  # "BANDWIDTH", "DATA VOLUME", "TEMPORARY"
    description: str            # Descrição do serviço
    valid_for: str             # "1 Residential User" (sempre o mesmo)
    buy_cost: int              # Preço de compra em picoins
    sell_cost: int             # Preço de venda em picoins (sempre 0 nas cartas físicas)
    # Campos opcionais (com valores padrão)
    service_user_id: Optional[int] = None  # ID do utilizador associado (1 a 4) ou None para "1 Residential User"
    service_packet_turn: Optional[int] = None        # Número de pacotes por turno (apenas para BANDWIDTH)
    service_packets: Optional[int] = None        # Número de pacotes que o serviço é válido (apenas para DATA_VOLUME)
    service_turns: Optional[int] = None          # Número de turnos que o serviço é válido
    # Campos de metadados fixos
    collection: str = "Packet Switching Collection"
    level: str = "Level I"

    def __str__(self):
        return f"ServiceCard(id={self.service_id}, {self.title}, type={self.service_type}, buy={self.buy_cost})"

@dataclass
@dataclass
class ActivityCard:
    """Carta de atividade/aplicação"""
    activity_id: str                    # ID único da carta (Activity_1, Activity_2, etc.)
    activity_type: ActivityType         # HOME_SURVEILLANCE, HOME_SAFETY, SHORT_MESSAGE, GAMING, FILE_TRANSFER
    color: str                         # Cor da carta
    title: str                         # "HOME SURVEILLANCE", "HOME SAFETY", etc.
    description: str                   # Descrição da aplicação
    message_size: int                  # Número de pacotes por mensagem
    rate: Union[int, List[int]]       # Taxa de envio: "1 packet per turn" OU ["1 packet per turn", "up to 1 packet per turn"]
    destination: str                  # Destino das mensagens (sempre "Central node")
    drops_allowed: bool               # Se permite drops ou não
    reward_per_packet: int            # Picoins ganhos por pacote recebido
    application_fee: int              # Taxa de aplicação em picoins
    # Campos opcionais com valores padrão
    message_received: Optional[int] = None   # Picoins ganhos por mensagem completa recebida
    message_received_bonus: Optional[int] = None   # Picoins ganhos por bonus mensagem completa recebida
    penalty_per_packet: Optional[int] = None # Penalização por pacote perdido
    packet_bonus: Optional[int] = None       # Bónus extra por pacote em condições específicas
    message_bonus: Optional[int] = None      # Bónus por mensagem completa recebida
    bonus_condition: Optional[int] = None    # Condição para bónus: "After 10 packets received", "Message received", etc.
    penalty_condition: Optional[int] = None  # Condição para penalização: "10 or fewer packets drops", etc.
    sell_cost: int = 0                # Valor de venda (sempre 0 para Activities)
    # Campos de metadados fixos
    collection: str = "Packet Switching Collection"
    level: str = "Level I"

    def get_rate_options(self) -> List[int]:
        """Retorna todas as opções de rate disponíveis para esta carta"""
        if isinstance(self.rate, list):
            return self.rate
        else:
            return [self.rate]
    
    def get_default_rate(self) -> int:
        """Retorna o rate padrão (primeiro da lista se for múltiplo)"""
        if isinstance(self.rate, list):
            return self.rate[0]
        else:
            return self.rate
    
    def has_multiple_rates(self) -> bool:
        """Verifica se a carta tem múltiplas opções de rate"""
        return isinstance(self.rate, list) and len(self.rate) > 1

    def __str__(self):
        return f"ActivityCard(id={self.activity_id}, {self.title}, size={self.message_size}, fee={self.application_fee})"

@dataclass
class ChallengeCard:
    """Carta de desafio"""
    challenge_id: str                   # ID único da carta (Challenge_1, Challenge_2, etc.)
    challenge_type: ChallengeType       # MESSAGE_MISSION, MESSAGE_SPRINT, JACKPOT, PACKET_RACE
    title: str                         # "MESSAGE MISSION", "MESSAGE SPRINT", "JACKPOT", "PACKET RACE"
    description: str                   # Descrição do desafio
    n_turns: int                       # Número de turnos disponíveis
    message_size: int                  # Tamanho da mensagem em pacotes
    rate: Union[int, List[int]]       # Taxa de envio: "1 packet per turn" OU ["1 packet per turn", "up to 1 packet per turn"]
    destination: str                  # Destino (sempre "Central node")
    drops_allowed: bool               # Se permite drops ou não
    # Campos de recompensas específicas
    reward_per_packet: Optional[int]  # Picoins por pacote recebido
    message_bonus: Optional[int]      # Bónus por mensagem completa/recebida
    time_limit_bonus: Optional[int]   # Bónus por completar dentro do prazo
    message_received_bonus: Optional[int] = None  # Bónus por mensagem completa recebida (JACKPOT)
    # Campos de penalizações
    challenge_quit_fee: int = 0       # Taxa por desistir do desafio
    # Campos específicos para alguns tipos
    time_limit: Optional[int] = None  # Limite de tempo em turnos (MESSAGE_SPRINT)
    time_to_receive: Optional[int] = None  # Tempo para receber mensagem (PACKET_RACE)
    # Campos de metadados fixos
    collection: str = "Packet Switching Collection"
    level: str = "Level I"

    def __str__(self):
        return f"ChallengeCard(id={self.challenge_id}, {self.title}, turns={self.n_turns}, size={self.message_size})"

@dataclass
class ActionCard:
    """Carta de ação"""
    action_id: str                      # ID único da carta (Action_1, Action_2, etc.)
    action_type: ActionType             # LINK_DOWNGRADE, ADD_ROUTER, REMOVE_ROUTER
    title: str                         # "LINK DOWNGRADE", "ADD ROUTER", "REMOVE ROUTER"
    description: str                   # Descrição detalhada da ação
    effect_description: str            # Descrição do efeito da carta
    target: Optional[str]              # Alvo específico da ação (green, red, blue, yellow ou None para o próprio jogador)
    router_id: Optional[int]           # ID do router extraído do action_id (e.g., 3 de "action_3")
    # Campos de metadados fixos
    collection: str = "Packet Switching Collection"
    level: str = "Level I"

    def __str__(self):
        return f"ActionCard(id={self.action_id}, {self.title}, target={self.target}, router_id={self.router_id})"

@dataclass
class EventCard:
    """Carta de evento"""
    event_id: str                       # ID único da carta (Event_1, Event_2, etc.)
    event_type: EventType               # TRANSMISSION_DELAY
    title: str                         # "TRANSMISSION DELAY"
    description: str                   # Descrição detalhada do evento
    effect_description: str            # Descrição do efeito da carta
    duration_turns: Union[int, str]    # Duração em turnos (1, 2, 4, ou "variable" para duração determinada por dado)
    target_link: Optional[str]         # Link alvo: "Link to Residential Router 1/2/3"
    target_queue: Optional[str]        # Queue alvo: "Queue of Residential Router 1/2/3"
    router_id: int                     # ID do router (1, 2, ou 3)
    target_player: Optional[str]       # Jogador alvo (green, red, blue, yellow ou None para escolha do jogador)
    player_choice: bool                # True se o jogador pode escolher o alvo, False se afeta jogador específico
    # Campos de metadados fixos
    collection: str = "Packet Switching Collection"
    level: str = "Level I"

    def __str__(self):
        return f"EventCard(id={self.event_id}, {self.title}, duration={self.duration_turns}, router={self.router_id}, target={self.target_player})"

class UserDatabase:
    """
    Base de dados principal de cartas NetMaster
    """
    
    def __init__(self):
        self.users: Dict[str, UserCard] = {}
        self.equipments: Dict[str, EquipmentCard] = {}
        self.services: Dict[str, ServiceCard] = {}
        self.activities: Dict[str, ActivityCard] = {}
        self.challenges: Dict[str, ChallengeCard] = {}
        self.actions: Dict[str, ActionCard] = {}
        self.events: Dict[str, EventCard] = {}
        self._initialize_database()
    
    def _initialize_database(self):
        """Inicializa a base de dados com cartas padrão"""
        self._create_user_cards()
        self._create_equipment_cards()
        self._create_service_cards()
        self._create_activity_cards()
        self._create_challenge_cards()
        self._create_action_cards()
        self._create_event_cards()
    
    def _create_user_cards(self):
        """Cria as cartas de utilizadores"""
        # Cartas de utilizadores residenciais
        colors = ["red", "green", "blue", "yellow"]
        
        for i in range(1, 7):  # User_1 a User_6 (mas User_6 não existe fisicamente)
            for color in colors:
                if i == 1:
                    # User_1 é um Residential Contract
                    user_id = f"contract_{color}"
                    users_count = 4     # up to 4 residential users
                    applications = 0    # Contract não tem applications
                    services = 0        # Contract não tem services
                    buy_cost = 0        # Contract não tem custo de compra
                    sell_cost = 0       # Contract não tem custo de venda
                else:
                    # User_2 a User_6 correspondem a User IDs 1 a 5
                    actual_user_id = i - 1  # User_2=1, User_3=2, User_4=3, User_5=4, User_6=5
                    user_id = f"{actual_user_id}_{color}"
                    
                    # Todos os User IDs têm as mesmas características conforme cartas físicas
                    users_count = 1     # 1 user per card
                    applications = 1    # 1 application
                    services = 1        # 1 service
                    buy_cost = 2        # Buy cost: 1 picoin
                    sell_cost = 1       # Sell cost: 2 picoins
                
                user_card = UserCard(
                    user_id=user_id,
                    user_type=UserType.RESIDENTIAL,
                    color=color,
                    users_count=users_count,
                    applications=applications,
                    services=services,
                    buy_cost=buy_cost,
                    sell_cost=sell_cost
                )
                
                self.users[user_id] = user_card
    
    def _create_equipment_cards(self):
        """Cria as cartas de equipamentos"""
        colors = ["red", "green", "blue", "yellow"]
        
        # Dicionário de mapeamento para valores individuais de compra e venda
        # Podes alterar estes valores conforme necessário
        equipment_costs = {
            # Small Router (Equipment_1 a Equipment_3)
            "small_router_1": {"buy": 40, "sell": 20, "queue_size": 4},
            "small_router_2": {"buy": 40, "sell": 20, "queue_size": 4},
            "small_router_3": {"buy": 40, "sell": 20, "queue_size": 4},
            
            
            # Medium Router (Equipment_4 a Equipment_6)
            "medium_router_1": {"buy": 80, "sell": 40, "queue_size": 8},
            "medium_router_2": {"buy": 80, "sell": 40, "queue_size": 8},
            "medium_router_3": {"buy": 80, "sell": 40, "queue_size": 8},
            
            
            # Short Link (Equipment_7 a Equipment_9)
            "short_link_1": {"buy": 40, "sell": 20, "link_length": 4},
            "short_link_2": {"buy": 40, "sell": 20, "link_length": 4},
            "short_link_3": {"buy": 40, "sell": 20, "link_length": 4},
            
            
            # Long Link (Equipment_10 a Equipment_12)
            "long_link_1": {"buy": 80, "sell": 40, "link_length": 8},
            "long_link_2": {"buy": 80, "sell": 40, "link_length": 8},
            "long_link_3": {"buy": 80, "sell": 40, "link_length": 8},
            
        }
        
        # Dicionário de mapeamento para object_names usados na deteção de objetos
        # Formato: "tipo_cor" -> "nome_do_objeto_para_detecao"
        object_names = {
            # Small Routers
            "small_router_red": "small_router_red",
            "small_router_green": "small_router_green", 
            "small_router_blue": "small_router_blue",
            "small_router_yellow": "small_router_yellow",
            
            # Medium Routers  
            "medium_router_red": "medium_router_red",
            "medium_router_green": "medium_router_green",
            "medium_router_blue": "medium_router_blue", 
            "medium_router_yellow": "medium_router_yellow",
            
            # Short Links
            "short_link_red": "short_link_red",
            "short_link_green": "short_link_green",
            "short_link_blue": "short_link_blue",
            "short_link_yellow": "short_link_yellow",
            
            # Long Links
            "long_link_red": "long_link_red", 
            "long_link_green": "long_link_green",
            "long_link_blue": "long_link_blue",
            "long_link_yellow": "long_link_yellow",
        }
        
        # Small Router (Equipment_1 a Equipment_3)
        for i in range(1, 4):
            for color in colors:
                equipment_id = f"small_router_{i}_{color}"
                base_id = f"small_router_{i}"
                
                # Obter valores do dicionário ou usar valores padrão
                costs = equipment_costs.get(base_id, {"buy": 100 + (i * 50), "sell": 50 + (i * 25), "queue_size": 2 + i})
                
                # Obter object_name baseado no tipo e cor
                object_name = object_names.get(f"small_router_{color}")
                
                equipment_card = EquipmentCard(
                    equipment_id=equipment_id,
                    equipment_type=EquipmentType.SMALL_ROUTER,
                    color=color,
                    category="Router",
                    model="Small Router",
                    specific_id=i,
                    queue_size=costs["queue_size"],  # Tamanho da queue
                    link_rate=None,
                    link_length=None,
                    buy_cost=costs["buy"],
                    sell_cost=costs["sell"],
                    object_name=object_name
                )
                
                self.equipments[equipment_id] = equipment_card
        
        # Medium Router (Equipment_4 a Equipment_6)
        for i in range(4, 7):
            for color in colors:
                equipment_id = f"medium_router_{i-3}_{color}"
                base_id = f"medium_router_{i-3}"
                
                # Obter valores do dicionário ou usar valores padrão
                costs = equipment_costs.get(base_id, {"buy": 200 + ((i-4) * 75), "sell": 100 + ((i-4) * 37), "queue_size": 5 + (i-4)})
                
                # Obter object_name baseado no tipo e cor
                object_name = object_names.get(f"medium_router_{color}")
                
                equipment_card = EquipmentCard(
                    equipment_id=equipment_id,
                    equipment_type=EquipmentType.MEDIUM_ROUTER,
                    color=color,
                    category="Router",
                    model="Medium Router",
                    specific_id=i-3,
                    queue_size=costs["queue_size"],  # Tamanho da queue
                    link_rate=None,
                    link_length=None,
                    buy_cost=costs["buy"],
                    sell_cost=costs["sell"],
                    object_name=object_name
                )
                
                self.equipments[equipment_id] = equipment_card
        
        # Short Link (Equipment_7 a Equipment_9)
        for i in range(7, 10):
            for color in colors:
                equipment_id = f"short_link_{i-6}_{color}"
                base_id = f"short_link_{i-6}"
                
                # Obter valores do dicionário ou usar valores padrão
                costs = equipment_costs.get(base_id, {"buy": 150 + ((i-8) * 50), "sell": 75 + ((i-8) * 25), "link_length": 2 + (i-8)})
                
                # Obter object_name baseado no tipo e cor
                object_name = object_names.get(f"short_link_{color}")
                
                equipment_card = EquipmentCard(
                    equipment_id=equipment_id,
                    equipment_type=EquipmentType.SHORT_LINK,
                    color=color,
                    category="Link",
                    model="Short Link",
                    specific_id=i-6,
                    queue_size=None,
                    link_rate="1 packet per turn",
                    link_length=costs["link_length"],  # Comprimento do link
                    buy_cost=costs["buy"],
                    sell_cost=costs["sell"],
                    object_name=object_name
                )
                
                self.equipments[equipment_id] = equipment_card
        
        # Long Link (Equipment_10 a Equipment_12)
        for i in range(10, 13):
            for color in colors:
                equipment_id = f"long_link_{i-9}_{color}"
                base_id = f"long_link_{i-9}"
                
                # Obter valores do dicionário ou usar valores padrão
                costs = equipment_costs.get(base_id, {"buy": 250 + ((i-12) * 75), "sell": 125 + ((i-12) * 37), "link_length": 5 + (i-12)})
                
                # Obter object_name baseado no tipo e cor
                object_name = object_names.get(f"long_link_{color}")
                
                equipment_card = EquipmentCard(
                    equipment_id=equipment_id,
                    equipment_type=EquipmentType.LONG_LINK,
                    color=color,
                    category="Link",
                    model="Long Link",
                    specific_id=i-9,
                    queue_size=None,
                    link_rate="1 packet per turn",
                    link_length=costs["link_length"],  # Comprimento do link
                    buy_cost=costs["buy"],
                    sell_cost=costs["sell"],
                    object_name=object_name
                )
                
                self.equipments[equipment_id] = equipment_card
    
    def _create_service_cards(self):
        """Cria as cartas de serviços"""
        colors = ["red", "green", "blue", "yellow"]
        
        # Dicionário de mapeamento para valores individuais de serviços
        # Podes alterar estes valores conforme necessário
        service_costs = {
            # Bandwidth Services (1 por cor)
            "bandwidth_1": {
                "service_packets_turn": 1,  # 1 packet per turn (valor máximo para "up to")
                "buy_price": 80,
                "sell_price": 0
            },
            
            # Data Volume Services (3 por cor)
            "data_volume_1": {
                "service_packets": 5,
                "buy_price": 5,
                "sell_price": 0
            },
            "data_volume_2": {
                "service_packets": 10,
                "buy_price": 8,
                "sell_price": 0
            },
            "data_volume_3": {
                "service_packets": 20,
                "buy_price": 15,
                "sell_price": 0
            },
            
            # Temporary Services (3 por cor)
            "temporary_1": {
                "service_turns": 4,
                "buy_price": 4,
                "sell_price": 0
            },
            "temporary_2": {
                "service_turns": 8,
                "buy_price": 7,
                "sell_price": 0
            },
            "temporary_3": {
                "service_turns": 16,
                "buy_price": 14,
                "sell_price": 0
            }
        }
        
        # Definir dados das cartas Services baseado no service_costs definido acima
        service_templates = [
            # Bandwidth Services (1 por cor) - mapeia para bandwidth_1
            {
                "type": ServiceType.BANDWIDTH,
                "base_key": "bandwidth_1",
                "name_template": "Bandwidth Service {color}",
                "title": "BANDWIDTH",
                "description": "Subscribe to our Bandwidth Service and enjoy seamless network access whenever you need it"
            },
            # Data Volume Services (3 por cor) - mapeia para data_volume_1, data_volume_2, data_volume_3
            {
                "type": ServiceType.DATA_VOLUME,
                "base_key": "data_volume_1",
                "name_template": "Data Volume Service {color} 5",
                "title": "DATA VOLUME",
                "description": "Subscribe to our Data Volume Service and pay only for the data you actually use. Enjoy flexible access without long-term obligations!"
            },
            {
                "type": ServiceType.DATA_VOLUME,
                "base_key": "data_volume_2",
                "name_template": "Data Volume Service {color} 8",
                "title": "DATA VOLUME",
                "description": "Subscribe to our Data Volume Service and pay only for the data you actually use. Enjoy flexible access without long-term obligations!"
            },
            {
                "type": ServiceType.DATA_VOLUME,
                "base_key": "data_volume_3",
                "name_template": "Data Volume Service {color} 15",
                "title": "DATA VOLUME",
                "description": "Subscribe to our Data Volume Service and pay only for the data you actually use. Enjoy flexible access without long-term obligations!"
            },
            # Temporary Services (3 por cor) - mapeia para temporary_1, temporary_2, temporary_3
            {
                "type": ServiceType.TEMPORARY,
                "base_key": "temporary_1",
                "name_template": "Temporary Service {color} 4",
                "title": "TEMPORARY",
                "description": "Subscribe to our Temporary Service and pay only for the time you need. Access the network as long as you require, with no long-term commitments."
            },
            {
                "type": ServiceType.TEMPORARY,
                "base_key": "temporary_2",
                "name_template": "Temporary Service {color} 7",
                "title": "TEMPORARY",
                "description": "Subscribe to our Temporary Service and pay only for the time you need. Access the network as long as you require, with no long-term commitments."
            },
            {
                "type": ServiceType.TEMPORARY,
                "base_key": "temporary_3",
                "name_template": "Temporary Service {color} 14",
                "title": "TEMPORARY",
                "description": "Subscribe to our Temporary Service and pay only for the time you need. Access the network as long as you require, with no long-term commitments."
            }
        ]
        
        # Contador global sequencial para IDs simples
        service_counter = 1
        
        # Criar cartas para cada cor
        for color in colors:
            for template in service_templates:
                # ID simples sequencial: Service_1, Service_2, etc.
                service_id = f"Service_{service_counter}"
                base_key = template["base_key"]
                
                # Incrementar contador global
                service_counter += 1
                
                # Obter valores do dicionário usando a chave correta
                costs = service_costs.get(base_key, {
                    "buy_price": 80,
                    "sell_price": 0  # Services sempre têm sell_price = 0
                })
                
                # Extrair valores específicos baseados no tipo de serviço
                service_packet_turn_value = None
                service_packets_value = None
                service_turns_value = None
                
                if template["type"] == ServiceType.BANDWIDTH:
                    service_packet_turn_value = costs.get("service_packets_turn", 1)
                elif template["type"] == ServiceType.DATA_VOLUME:
                    service_packets_value = costs.get("service_packets", 5)
                elif template["type"] == ServiceType.TEMPORARY:
                    service_turns_value = costs.get("service_turns", 4)
                
                service_card = ServiceCard(
                    service_id=service_id,
                    service_type=template["type"],
                    color=color,
                    title=template["title"],
                    description=template["description"],
                    valid_for="1 Residential User",
                    service_packet_turn=service_packet_turn_value,
                    service_packets=service_packets_value,
                    service_turns=service_turns_value,
                    buy_cost=costs["buy_price"],
                    sell_cost=0  # Services sempre têm sell_cost = 0
                )
                
                self.services[service_id] = service_card
    
    def _create_activity_cards(self):
        """Cria as cartas de atividades"""
        colors = ["red", "green", "blue", "yellow"]
        
        # Definir dados das cartas Activities baseadas nas imagens anexadas
        activity_templates = [
            # HOME SURVEILLANCE - 4 variações diferentes
            {
                "type": ActivityType.HOME_SURVEILLANCE,
                "title": "HOME SURVEILLANCE",
                "description": "With our Home Surveillance application, you can monitor your home from anywhere. It's simple and low-traffic, but it doesn't guarantee delivery—avoid it for critical information!",
                "message_size": 20,
                "rate": [1],  # VALOR ÚNICO
                "drops_allowed": True,
                "reward_per_packet": 4,
                "message_received": None,
                "penalty_per_packet": 0,  # ALTERADO: Activity_1 agora tem penalidade zero
                "application_fee": 40,
                "bonus_condition": None,
                "penalty_condition": None
            },
            {
                "type": ActivityType.HOME_SURVEILLANCE,
                "title": "HOME SURVEILLANCE",
                "description": "With our Home Surveillance application, you can monitor your home from anywhere. It's simple and low on traffic, but it doesn't guarantee delivery—avoid it for critical information!",
                "message_size": 20,
                "rate": [1],  # VALOR ÚNICO 
                "drops_allowed": True,
                "reward_per_packet": 3,
                "packet_bonus": 4,
                "penalty_per_packet": 0,  # ALTERADO: Activity_2 agora tem penalidade zero
                "application_fee": 40,
                "bonus_condition": 10,  # "After 10 packets received",
                "penalty_condition": None
            },
            {
                "type": ActivityType.HOME_SURVEILLANCE,
                "title": "HOME SURVEILLANCE",
                "description": "With our Home Surveillance application, you can monitor your home from anywhere. It's simple and low-traffic, but it doesn't guarantee delivery—avoid it for critical information!",
                "message_size": 20,
                "rate": [1],  # VALOR ÚNICO
                "drops_allowed": True,
                "reward_per_packet": 4,
                "packet_bonus": 20,
                "penalty_per_packet": 0,  # ALTERADO: Activity_3 agora tem penalidade zero
                "application_fee": 60,
                "bonus_condition": 15,  # "After 15 packets received",
                "penalty_condition": None
            },
            {
                "type": ActivityType.HOME_SURVEILLANCE,
                "title": "HOME SURVEILLANCE",
                "description": "With our Home Surveillance application, you can monitor your home from anywhere. It's simple and low-traffic, but it doesn't guarantee delivery—avoid it for critical information!",
                "message_size": 20,
                "rate": [1],  # VALOR ÚNICO
                "drops_allowed": True,
                "reward_per_packet": 1,
                "message_received": 160,
                "penalty_per_packet": 0,  # ALTERADO: Activity_4 agora tem penalidade zero
                "application_fee": 40,
                "bonus_condition": 0,  # "No drops",
                "penalty_condition": None
            },
            # HOME SAFETY - 3 variações diferentes
            {
                "type": ActivityType.HOME_SAFETY,
                "title": "HOME SAFETY",
                "description": "Keep your home safe with our Emergency application. It's simple, low-traffic, and guarantees delivery—perfect for emergency situations!",
                "message_size": 20,
                "rate": [0,1], # MÚLTIPLAS OPÇÕES
                "drops_allowed": False,
                "reward_per_packet": 0,
                "message_received": 160,
                "penalty_per_packet": None,
                "application_fee": 40,
                "bonus_condition": None,
                "penalty_condition": None
            },
            {
                "type": ActivityType.HOME_SAFETY,
                "title": "HOME SAFETY",
                "description": "Keep your home safe with our Emergency application. It's simple, low-traffic, and guarantees delivery—perfect for emergency situations!",
                "message_size": 20,
                "rate": [0,1], # MÚLTIPLAS OPÇÕES
                "drops_allowed": False,
                "reward_per_packet": 0,
                "message_received": 320,
                "penalty_per_packet": 8,
                "application_fee": 60,
                "bonus_condition": None,
                "penalty_condition": 10  # "10 or fewer packets drops"
            },
            {
                "type": ActivityType.HOME_SAFETY,
                "title": "HOME SAFETY",
                "description": "Keep your home safe with our Emergency application. It's simple, low-traffic, and guarantees delivery—perfect for emergency situations!",
                "message_size": 20,
                "rate": [0,1], # MÚLTIPLAS OPÇÕES
                "drops_allowed": False,
                "reward_per_packet": 0,
                "message_received": 480,
                "penalty_per_packet": 4,
                "application_fee": 60,
                "bonus_condition": None,
                "penalty_condition": 5  # "5 or fewer packets drops"
            },
            # SHORT MESSAGE - 2 variações diferentes
            {
                "type": ActivityType.SHORT_MESSAGE,
                "title": "SHORT MESSAGE",
                "description": "Take a quick break and connect with friends using our Short Message application. It's easy to use, traffic-friendly, and ensures your packets are delivered—perfect for everyday chats!",
                "message_size": 4,
                "rate": [0,1], # MÚLTIPLAS OPÇÕES
                "drops_allowed": False,
                "reward_per_packet": 0,
                "message_received": 12,
                "penalty_per_packet": None,
                "application_fee": 5,
                "bonus_condition": None,
                "penalty_condition": None
            },
            {
                "type": ActivityType.SHORT_MESSAGE,
                "title": "SHORT MESSAGE",
                "description": "Take a quick break and connect with friends using our Short Message application. It's easy to use, traffic-friendly, and ensures your packets are delivered—perfect for everyday chats!",
                "message_size": 4,
                "rate": [0,1], # MÚLTIPLAS OPÇÕES
                "drops_allowed": False,
                "reward_per_packet": 0,
                "message_received": 16,
                "penalty_per_packet": 2,
                "application_fee": 5,
                "bonus_condition": None,
                "penalty_condition": 1  # "Per packet drop"
            },
            # GAMING - 2 variações diferentes
            {
                "type": ActivityType.GAMING,
                "title": "GAMING",
                "description": "Enjoy your gaming moments with our Gaming application. It's easy to use and consumes minimal traffic, but sometimes it might miss a few moves—no big deal!",
                "message_size": 4,
                "rate": 1, # VALOR ÚNICO
                "drops_allowed": True,
                "reward_per_packet": 3,
                "message_received": None,
                "penalty_per_packet": 0,  # ALTERADO: Activity_10 agora tem penalidade zero
                "application_fee": 5,
                "bonus_condition": None,
                "penalty_condition": None
            },
            {
                "type": ActivityType.GAMING,
                "title": "GAMING",
                "description": "Enjoy your gaming moments with our Gaming application. It's easy to use and consumes minimal traffic, but sometimes it might miss a few moves—no big deal!",
                "message_size": 4,
                "rate": 1, # VALOR ÚNICO
                "drops_allowed": True,
                "reward_per_packet": 2,
                "message_received": 16,
                "penalty_per_packet": 0,  # ALTERADO: Activity_11 agora tem penalidade zero
                "application_fee": 5,
                "bonus_condition": "Message received",
                "penalty_condition": None
            },
            # FILE TRANSFER - 1 variação
            {
                "type": ActivityType.FILE_TRANSFER,
                "title": "FILE TRANSFER",
                "description": "Work from home without missing deadlines. Send your text reports using our File Transfer application. It's easy to use, consumes minimal bandwidth, but requires reliable delivery.",
                "message_size": 8,
                "rate": [0,1], # MÚLTIPLAS OPÇÕES
                "drops_allowed": False,
                "reward_per_packet": 0,
                "message_received": 80,
                "penalty_per_packet": None,
                "application_fee": 10,
                "bonus_condition": None,
                "penalty_condition": None
            }
        ]
        
        # Criar cartas para cada cor
        for color in colors:
            for idx, template in enumerate(activity_templates):
                # Gerar ID simples que corresponde aos arquivos físicos: Activity_1.png -> activity_1_red
                activity_id = f"activity_{idx+1}_{color}"
                
                activity_card = ActivityCard(
                    activity_id=activity_id,
                    activity_type=template["type"],
                    color=color,
                    title=template["title"],
                    description=template["description"],
                    message_size=template["message_size"],
                    rate=template["rate"],
                    destination="Central node",
                    drops_allowed=template["drops_allowed"],
                    reward_per_packet=template["reward_per_packet"],
                    message_received=template.get("message_received"),
                    penalty_per_packet=template.get("penalty_per_packet"),
                    packet_bonus=template.get("packet_bonus"),
                    message_bonus=template.get("message_bonus"),
                    application_fee=template["application_fee"],
                    bonus_condition=template.get("bonus_condition"),
                    penalty_condition=template.get("penalty_condition"),
                    sell_cost=0  # Valor de venda sempre 0 para Activities
                )
                
                self.activities[activity_id] = activity_card
    
    def _create_challenge_cards(self):
        """Cria as cartas de desafios"""
        # Como não há cores específicas para challenges, são cartas únicas
        
        # Definir dados das cartas Challenges baseadas nas imagens anexadas
        challenge_templates = [
            # MESSAGE MISSION - 4 variações (adicionadas as 2 que faltavam)
            {
                "type": ChallengeType.MESSAGE_MISSION,
                "title": "MESSAGE MISSION",
                "description": "You're on a mission to deliver an important message. Don't lose any part—receive the complete message or lose the reward!",
                "n_turns": 2,
                "message_size": 1,
                "rate": [0,1],
                "drops_allowed": False,
                "reward_per_packet": None,
                "message_received": 5,
                "time_limit_bonus": None,
                "challenge_quit_fee": 5,
                "time_limit": None,
                "time_to_receive": None
            },
            {
                "type": ChallengeType.MESSAGE_MISSION,
                "title": "MESSAGE MISSION",
                "description": "You're on a mission to deliver an important message. Don't lose any part—receive the complete message or lose the reward!",
                "n_turns": 4,
                "message_size": 2,
                "rate": [0,1],
                "drops_allowed": False,
                "reward_per_packet": None,
                "message_received": 20,
                "time_limit_bonus": None,
                "challenge_quit_fee": 10,
                "time_limit": None,
                "time_to_receive": None
            },
            {
                "type": ChallengeType.MESSAGE_MISSION,
                "title": "MESSAGE MISSION",
                "description": "You're on a mission to deliver an important message. Don't lose any part—receive the complete message or lose the reward!",
                "n_turns": 8,
                "message_size": 4,
                "rate": [0,1],
                "drops_allowed": False,
                "reward_per_packet": None,
                "message_received": 80,
                "time_limit_bonus": None,
                "challenge_quit_fee": 40,
                "time_limit": None,
                "time_to_receive": None
            },
            {
                "type": ChallengeType.MESSAGE_MISSION,
                "title": "MESSAGE MISSION",
                "description": "You're on a mission to deliver an important message. Don't lose any part—receive the complete message or lose the reward!",
                "n_turns": 16,
                "message_size": 8,
                "rate": [0,1],
                "drops_allowed": False,
                "reward_per_packet": None,
                "message_received": 320,
                "time_limit_bonus": None,
                "challenge_quit_fee": 80,
                "time_limit": None,
                "time_to_receive": None
            },
            # MESSAGE SPRINT - 3 variações
            {
                "type": ChallengeType.MESSAGE_SPRINT,
                "title": "MESSAGE SPRINT",
                "description": "Time is running out, and the message is urgent! It can't arrive too late! Once transmission starts, you have a limited time to receive the complete message. Good luck!",
                "n_turns": 4,
                "message_size": 2,
                "rate": [0,1],
                "drops_allowed": False,
                "reward_per_packet": None,
                "message_received": 20,
                "time_limit_bonus": 20,
                "challenge_quit_fee": 10,
                "time_limit": 2,
                "time_to_receive": None
            },
            {
                "type": ChallengeType.MESSAGE_SPRINT,
                "title": "MESSAGE SPRINT",
                "description": "Time is running out, and the message is urgent! It can't arrive too late! Once transmission starts, you have a limited time to receive the complete message. Good luck!",
                "n_turns": 8,
                "message_size": 4,
                "rate": [0,1],
                "drops_allowed": False,
                "reward_per_packet": None,
                "message_received": 80,
                "time_limit_bonus": 80,
                "challenge_quit_fee": 40,
                "time_limit": 4,
                "time_to_receive": None
            },
            {
                "type": ChallengeType.MESSAGE_SPRINT,
                "title": "MESSAGE SPRINT",
                "description": "Time is running out, and the message is urgent! It can't arrive too late! Once transmission starts, you have a limited time to receive the complete message. Good luck!",
                "n_turns": 16,
                "message_size": 8,
                "rate": [0,1],
                "drops_allowed": False,
                "reward_per_packet": None,
                "message_received": 320,
                "time_limit_bonus": 320,
                "challenge_quit_fee": 80,
                "time_limit": 8,
                "time_to_receive": None
            },
            # JACKPOT - 3 variações
            {
                "type": ChallengeType.JACKPOT,
                "title": "JACKPOT",
                "description": "Don't waste time! Get paid for the packets received and rewarded for the message! This is an absolute jackpot!",
                "n_turns": 2,
                "message_size": 2,
                "rate": [0,1],
                "drops_allowed": True,
                "reward_per_packet": 20,
                "message_received_bonus": 40,
                "time_limit_bonus": None,
                "challenge_quit_fee": 10,
                "time_limit": None,
                "time_to_receive": None
            },
            {
                "type": ChallengeType.JACKPOT,
                "title": "JACKPOT",
                "description": "Don't waste time! Get paid for the packets received and rewarded for the message! This is an absolute jackpot!",
                "n_turns": 4,
                "message_size": 4,
                "rate": [0,1],
                "drops_allowed": True,
                "reward_per_packet": 80,
                "message_received_bonus": 160,
                "time_limit_bonus": None,
                "challenge_quit_fee": 40,
                "time_limit": None,
                "time_to_receive": None
            },
            {
                "type": ChallengeType.JACKPOT,
                "title": "JACKPOT",
                "description": "Don't waste time! Get paid for the packets received and rewarded for the message! This is an absolute jackpot!",
                "n_turns": 8,
                "message_size": 8,
                "rate": [0,1],
                "drops_allowed": True,
                "reward_per_packet": 320,
                "message_received_bonus": 640,
                "time_limit_bonus": None,
                "challenge_quit_fee": 80,
                "time_limit": None,
                "time_to_receive": None
            },
            # PACKET RACE - 4 variações
            {
                "type": ChallengeType.PACKET_RACE,
                "title": "PACKET RACE",
                "description": "You're in a race to deliver a message, but luckily, even a few packets are enough to understand it. Get paid for the packets received within the timeframe! A great deal! Let's go!",
                "n_turns": 1,
                "message_size": 1,
                "rate": [0,1],
                "drops_allowed": True,
                "reward_per_packet": 2,
                "message_received": None,
                "time_limit_bonus": None,
                "challenge_quit_fee": 5,
                "time_limit": None,
                "time_to_receive": 2
            },
            {
                "type": ChallengeType.PACKET_RACE,
                "title": "PACKET RACE",
                "description": "You're in a race to deliver a message, but luckily, even a few packets are enough to understand it. Get paid for the packets received within the timeframe! A great deal! Let's go!",
                "n_turns": 2,
                "message_size": 2,
                "rate": [0,1],
                "drops_allowed": True,
                "reward_per_packet": 20,
                "message_received": None,
                "time_limit_bonus": None,
                "challenge_quit_fee": 10,
                "time_limit": None,
                "time_to_receive": 2
            },
            {
                "type": ChallengeType.PACKET_RACE,
                "title": "PACKET RACE",
                "description": "You're in a race to deliver a message, but luckily, even a few packets are enough to understand it. Get paid for the packets received within the timeframe! A great deal! Let's go!",
                "n_turns": 4,
                "message_size": 4,
                "rate": [0,1],
                "drops_allowed": True,
                "reward_per_packet": 80,
                "message_received": None,
                "time_limit_bonus": None,
                "challenge_quit_fee": 40,
                "time_limit": None,
                "time_to_receive": 4
            },
            {
                "type": ChallengeType.PACKET_RACE,
                "title": "PACKET RACE",
                "description": "You're in a race to deliver a message, but luckily, even a few packets are enough to understand it. Get paid for the packets received within the timeframe! A great deal! Let's go!",
                "n_turns": 8,
                "message_size": 4,
                "rate": [0,1],
                "drops_allowed": True,
                "reward_per_packet": 320,
                "message_received": None,
                "time_limit_bonus": None,
                "challenge_quit_fee": 80,
                "time_limit": None,
                "time_to_receive": 4
            }
        ]
        
        # Criar cartas de desafio
        for idx, template in enumerate(challenge_templates):
            # Gerar ID simples que corresponde aos arquivos físicos: Challenge_1.png -> challenge_1
            challenge_id = f"challenge_{idx+1}"
            
            challenge_card = ChallengeCard(
                challenge_id=challenge_id,
                challenge_type=template["type"],
                title=template["title"],
                description=template["description"],
                n_turns=template["n_turns"],
                message_size=template["message_size"],
                rate=template["rate"],
                destination="Central node",
                drops_allowed=template["drops_allowed"],
                reward_per_packet=template.get("reward_per_packet"),
                message_bonus=template.get("message_received"),
                message_received_bonus=template.get("message_received_bonus"),  # ADICIONADO: Campo para JACKPOT
                time_limit_bonus=template.get("time_limit_bonus"),
                challenge_quit_fee=template.get("challenge_quit_fee", 0),
                time_limit=template.get("time_limit"),
                time_to_receive=template.get("time_to_receive")
            )
            
            self.challenges[challenge_id] = challenge_card
    
    def _extract_router_id(self, action_id: str, action_type: ActionType) -> Optional[int]:
        """Extrai o router_id baseado no padrão das cartas físicas"""
        if not action_id:
            return None
        
        # Extrair número do action_id (e.g., "action_3" -> 3)
        import re
        match = re.search(r'action_(\d+)', action_id)
        if not match:
            return None
            
        action_num = int(match.group(1))
        
        # Mapeamento personalizado de router_ids por carta
        # Podes alterar estes valores conforme necessário
        router_id_mapping = {
            # Router Upgrade (cartas 1-7)
            1: 1,   # Action_1 -> Router 1
            2: 2,   # Action_2 -> Router 2  
            3: 3,   # Action_3 -> Router 3
            4: 1,   # Action_4 -> Router 1
            5: 1,   # Action_5 -> Router 1
            6: 1,   # Action_6 -> Router 1
            7: 1,   # Action_7 -> Router 1
            
            # Router Downgrade (cartas 8-14)
            8: 1,   # Action_8 -> Router 1
            9: 2,   # Action_9 -> Router 2
            10: 3,  # Action_10 -> Router 3
            11: 1,  # Action_11 -> Router 1
            12: 1,  # Action_12 -> Router 1
            13: 1,  # Action_13 -> Router 1
            14: 1,  # Action_14 -> Router 1
            
            # Link Upgrade (cartas 15-21)
            15: 1,  # Action_15 -> Router 1
            16: 2,  # Action_16 -> Router 2
            17: 3,  # Action_17 -> Router 3
            18: 1,  # Action_18 -> Router 1
            19: 1,  # Action_19 -> Router 1
            20: 1,  # Action_20 -> Router 1
            21: 1,  # Action_21 -> Router 1
            
            # Link Downgrade (cartas 22-28)
            22: 1,  # Action_22 -> Router 1
            23: 2,  # Action_23 -> Router 2
            24: 3,  # Action_24 -> Router 3
            25: 1,  # Action_25 -> Router 1
            26: 1,  # Action_26 -> Router 1
            27: 1,  # Action_27 -> Router 1
            28: 1,  # Action_28 -> Router 1
            
            # Add Router (cartas 29-33) - não têm router específico
            29: None,  # Action_29 -> None
            30: None,  # Action_30 -> None
            31: None,  # Action_31 -> None
            32: None,  # Action_32 -> None
            33: None,  # Action_33 -> None
            
            # Remove Router (cartas 34-38) - não têm router específico
            34: None,  # Action_34 -> None
            35: None,  # Action_35 -> None
            36: None,  # Action_36 -> None
            37: None,  # Action_37 -> None
            38: None,  # Action_38 -> None
        }
        
        # Retornar o router_id mapeado ou None se não existir
        return router_id_mapping.get(action_num, None)
    

    def _create_action_cards(self):
        """Cria as cartas de ação"""
        # 70 cartas Action no total baseadas na pasta fornecida
        action_templates = []
        
        # ROUTER UPGRADE - 15 cartas (Action_1 a Action_15)
        # Padrão: 3 cartas para cada router (1,2,3) para próprio jogador + 1 carta de cada router para cada cor de jogador
        router_upgrade_sequence = [
            # Cartas 1-3: Router 1,2,3 para próprio jogador
            {"router_id": 1, "target": None},
            {"router_id": 2, "target": None}, 
            {"router_id": 3, "target": None},
            # Cartas 4-6: Router 1,2,3 para jogador amarelo
            {"router_id": 1, "target": "yellow"},
            {"router_id": 2, "target": "yellow"},
            {"router_id": 3, "target": "yellow"},
            # Cartas 7-9: Router 1,2,3 para jogador verde
            {"router_id": 1, "target": "green"},
            {"router_id": 2, "target": "green"},
            {"router_id": 3, "target": "green"},
            # Cartas 10-12: Router 1,2,3 para jogador azul
            {"router_id": 1, "target": "blue"},
            {"router_id": 2, "target": "blue"},
            {"router_id": 3, "target": "blue"},
            # Cartas 13-15: Router 1,2,3 para jogador vermelho
            {"router_id": 1, "target": "red"},
            {"router_id": 2, "target": "red"},
            {"router_id": 3, "target": "red"}
        ]
        
        for config in router_upgrade_sequence:
            action_templates.append({
                "type": ActionType.ROUTER_UPGRADE,
                "title": "ROUTER UPGRADE",
                "description": "A bigger queue means more space for packets. \nUpgrade the queue on your Small Router to \nreduce drops, and you'll unlock your Medium \nRouter for free!",
                "effect_description": "Move packets from the old queue to the new one, \nkeeping them in the same order.",
                "target": config["target"],
                "router_id": config["router_id"]
            })

        # ROUTER DOWNGRADE - 15 cartas (Action_16 a Action_30)
        router_downgrade_sequence = [
            # Cartas 16-18: Router 1,2,3 para próprio jogador
            {"router_id": 1, "target": None},
            {"router_id": 2, "target": None},
            {"router_id": 3, "target": None},
            # Cartas 19-21: Router 1,2,3 para jogador amarelo
            {"router_id": 1, "target": "yellow"},
            {"router_id": 2, "target": "yellow"},
            {"router_id": 3, "target": "yellow"},
            # Cartas 22-24: Router 1,2,3 para jogador verde
            {"router_id": 1, "target": "green"},
            {"router_id": 2, "target": "green"},
            {"router_id": 3, "target": "green"},
            # Cartas 25-27: Router 1,2,3 para jogador azul
            {"router_id": 1, "target": "blue"},
            {"router_id": 2, "target": "blue"},
            {"router_id": 3, "target": "blue"},
            # Cartas 28-30: Router 1,2,3 para jogador vermelho
            {"router_id": 1, "target": "red"},
            {"router_id": 2, "target": "red"},
            {"router_id": 3, "target": "red"}
        ]
        
        for config in router_downgrade_sequence:
            action_templates.append({
                "type": ActionType.ROUTER_DOWNGRADE,
                "title": "ROUTER DOWNGRADE", 
                "description": "Smaller queues mean less waiting. Reduce the \nMedium Router's queue size to speed up packet \ndelivery and unlock your Small Router!",
                "effect_description": "Move packets from the old queue to \nthe new one, keeping the \nsame order, and discard any excess \npackets.",
                "target": config["target"],
                "router_id": config["router_id"]
            })
        
        # LINK UPGRADE - 15 cartas (Action_31 a Action_45)
        link_upgrade_sequence = [
            # Cartas 31-33: Link 1,2,3 para próprio jogador
            {"router_id": 1, "target": None},
            {"router_id": 2, "target": None},
            {"router_id": 3, "target": None},
            # Cartas 34-36: Link 1,2,3 para jogador amarelo
            {"router_id": 1, "target": "yellow"},
            {"router_id": 2, "target": "yellow"},
            {"router_id": 3, "target": "yellow"},
            # Cartas 37-39: Link 1,2,3 para jogador verde
            {"router_id": 1, "target": "green"},
            {"router_id": 2, "target": "green"},
            {"router_id": 3, "target": "green"},
            # Cartas 40-42: Link 1,2,3 para jogador azul
            {"router_id": 1, "target": "blue"},
            {"router_id": 2, "target": "blue"},
            {"router_id": 3, "target": "blue"},
            # Cartas 43-45: Link 1,2,3 para jogador vermelho
            {"router_id": 1, "target": "red"},
            {"router_id": 2, "target": "red"},
            {"router_id": 3, "target": "red"}
        ]
        
        for config in link_upgrade_sequence:
            action_templates.append({
                "type": ActionType.LINK_UPGRADE,
                "title": "LINK UPGRADE",
                "description": "Short links have lower transmission times. \nSwitch from a Long Link to a short one and \nenjoy faster communications!",
                "effect_description": "Move packets from the old link to \nthe new one, keeping the \nsame order, and discard any excess \npackets.",
                "target": config["target"],
                "router_id": config["router_id"]
            })
        
        # LINK DOWNGRADE - 15 cartas (Action_46 a Action_57)
        link_downgrade_sequence = [
            # Cartas 46-48: Link 1,2,3 para próprio jogador
            {"router_id": 1, "target": None},
            {"router_id": 2, "target": None},
            {"router_id": 3, "target": None},
            # Cartas 49-51: Link 1,2,3 para jogador amarelo
            {"router_id": 1, "target": "yellow"},
            {"router_id": 2, "target": "yellow"},
            {"router_id": 3, "target": "yellow"},
            # Cartas 52-54: Link 1,2,3 para jogador verde
            {"router_id": 1, "target": "green"},
            {"router_id": 2, "target": "green"},
            {"router_id": 3, "target": "green"},
            # Cartas 55-57: Link 1,2,3 para jogador azul
            {"router_id": 1, "target": "blue"},
            {"router_id": 2, "target": "blue"},
            {"router_id": 3, "target": "blue"},
            # Cartas 55-57: Link 1,2,3 para jogador vermelho
            {"router_id": 1, "target": "red"},
            {"router_id": 2, "target": "red"},
            {"router_id": 3, "target": "red"}
        ]
        
        for config in link_downgrade_sequence:
            action_templates.append({
                "type": ActionType.LINK_DOWNGRADE,
                "title": "LINK DOWNGRADE",
                "description": "We moved far from central node and, you'll \nneed a long link to stay connected — but get \nready for longer delays.",
                "effect_description": "Move packets from the old link to \nthe new one, keeping the \nsame order.",
                "target": config["target"],
                "router_id": config["router_id"]
            })
        
        # ADD ROUTER - 5 cartas (Action_61 a Action_65)
        add_router_targets = [
            None,     # Carta 61: Próprio jogador
            "yellow", # Carta 62: Jogador amarelo
            "green",  # Carta 63: Jogador verde
            "blue",   # Carta 64: Jogador azul
            "red",    # Carta 65: Jogador vermelho
        ]
        
        for i, target in enumerate(add_router_targets):
            action_templates.append({
                "type": ActionType.ADD_ROUTER,
                "title": "ADD ROUTER",
                "description": "A new Residential User requested access to \nNetMaster. Head to the Store to see if you can \ngrab a Small Router for free. Good luck!",
                "effect_description": "Add the router to the network board if there is \na link to connect it. Otherwise, return it to \nthe store.",
                "target": target,
                "router_id": None  # ADD ROUTER não especifica router_id
            })
        
        # REMOVE ROUTER - 5 cartas (Action_66 a Action_70)
        remove_router_targets = [
            None,     # Carta 66: Próprio jogador
            "yellow", # Carta 67: Jogador amarelo
            "green",  # Carta 68: Jogador verde
            "blue",   # Carta 69: Jogador azul
            "red",    # Carta 70: Jogador vermelho
        ]
        
        for i, target in enumerate(remove_router_targets):
            action_templates.append({
                "type": ActionType.REMOVE_ROUTER,
                "title": "REMOVE ROUTER",
                "description": "The Small Router is no longer needed! \nReturn it to the store if possible!",
                "effect_description": "If there's more than one Small Router on the \nnetwork board, remove the latest one added, \nalong with all packets in its queue \nand the associated link.",
                "target": target,
                "router_id": None  # REMOVE ROUTER não especifica router_id
            })
        
        # Criar cartas de ação
        for idx, template in enumerate(action_templates):
            action_id = f"action_{idx+1}"
            target = template["target"]
            action_type = template["type"]
            
            # Usar router_id do template se existir, senão usar a função _extract_router_id
            router_id = template.get("router_id", self._extract_router_id(action_id, action_type))
            
            action_card = ActionCard(
                action_id=action_id,
                action_type=action_type,
                title=template["title"],
                description=template["description"],
                effect_description=template["effect_description"],
                target=target,
                router_id=router_id
            )
            
            self.actions[action_id] = action_card
    
    def _create_event_cards(self):
        """Cria as cartas de eventos"""
        
        
        event_templates = [
            # Event_1: TRANSMISSION DELAY, Router 1, 1 TURN, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": False
            },
            # Event_2: TRANSMISSION DELAY, Router 2, 1 TURN, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": None,
                "player_choice": False
            },
            # Event_3: TRANSMISSION DELAY, Router 3, 1 TURN, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": None,
                "player_choice": False
            },
            # Event_4: TRANSMISSION DELAY, Router 1, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False
            },
            # Event_5: TRANSMISSION DELAY, Router 2, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False
            },
            # Event_6: TRANSMISSION DELAY, Router 3, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False
            },
            # Event_7: TRANSMISSION DELAY, Router 1, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False
            },
            # Event_8: TRANSMISSION DELAY, Router 2, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False
            },
            # Event_9: TRANSMISSION DELAY, Router 3, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False
            },
            # Event_10: TRANSMISSION DELAY, Router 1, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False
            },
            # Event_11: TRANSMISSION DELAY, Router 2, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False
            },
            # Event_12: TRANSMISSION DELAY, Router 3, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False
            },
            # Event_13: TRANSMISSION DELAY, Router 1, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False
            },
            # Event_14: TRANSMISSION DELAY, Router 2, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False
            },
            # Event_15: TRANSMISSION DELAY, Router 3, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False
            },
            # Event_16: TRANSMISSION DELAY, Router 1, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": True
            },
            # Event_17: TRANSMISSION DELAY, Router 2, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": None,
                "player_choice": True
            },
            # Event_18: TRANSMISSION DELAY, Router 3, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": None,
                "player_choice": True
            },
            # Event_19: TRANSMISSION DELAY, Router 1, 2 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": False
            },
            # Event_20: TRANSMISSION DELAY, Router 2, 2 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": False
            },
            # Event_21: TRANSMISSION DELAY, Router 3, 2 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": False
            },
            # Event_22: TRANSMISSION DELAY, Router 1, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False
            },
            # Event_23: TRANSMISSION DELAY, Router 2, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False
            },
            # Event_24: TRANSMISSION DELAY, Router 3, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False
            },
            # Event_25: TRANSMISSION DELAY, Router 1, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False
            },
            # Event_26: TRANSMISSION DELAY, Router 2, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False
            },
            # Event_27: TRANSMISSION DELAY, Router 3, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False
            },
            # Event_28: TRANSMISSION DELAY, Router 1, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False
            },
            # Event_29: TRANSMISSION DELAY, Router 2, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False
            },
            # Event_30: TRANSMISSION DELAY, Router 3, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False
            },
            # Event_31: TRANSMISSION DELAY, Router 1, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False
            },
            # Event_32: TRANSMISSION DELAY, Router 2, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False
            },
            # Event_33: TRANSMISSION DELAY, Router 3, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False
            },
            # Event_34: TRANSMISSION DELAY, Router 1, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": True
            },
            # Event_35: TRANSMISSION DELAY, Router 2, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": True
            },
            # Event_36: TRANSMISSION DELAY, Router 3, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": True
            },
            # Event_37: TRANSMISSION DELAY, Router 1, 4 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": False
            },
            # Event_38: TRANSMISSION DELAY, Router 2, 4 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": False
            },
            # Event_39: TRANSMISSION DELAY, Router 3, 4 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": None,
                "player_choice": False
            },
            # Event_40: TRANSMISSION DELAY, Router 1, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False
            },
            # Event_41: TRANSMISSION DELAY, Router 2, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False
            },
            # Event_42: TRANSMISSION DELAY, Router 3, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False
            },
            # Event_43: TRANSMISSION DELAY, Router 1, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False
            },
            # Event_44: TRANSMISSION DELAY, Router 2, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False
            },
            # Event_45: TRANSMISSION DELAY, Router 3, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False
            },
            # Event_46: TRANSMISSION DELAY, Router 1, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False
            },
            # Event_47: TRANSMISSION DELAY, Router 2, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False
            },
            # Event_48: TRANSMISSION DELAY, Router 3, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False
            },
            # Event_49: TRANSMISSION DELAY, Router 1, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False
            },
            # Event_50: TRANSMISSION DELAY, Router 2, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False
            },
            # Event_51: TRANSMISSION DELAY, Router 3, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False
            },
            # Event_52: TRANSMISSION DELAY, Router 1, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": True
            },
            # Event_53: TRANSMISSION DELAY, Router 2, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": True
            },
            # Event_54: TRANSMISSION DELAY, Router 3, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": None,
                "player_choice": True
            },
            # Event_55: TRANSMISSION DELAY, Router 1, ? TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": "variable",  # ? TURNS - será determinado por dado
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
            },
            # Event_56: TRANSMISSION DELAY, Router 2, ? TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": "variable",  # ? TURNS - será determinado por dado
                "router_id": 2,
                "target_player": None,
                "player_choice": False, 
            },
            # Event_57: TRANSMISSION DELAY, Router 3, ? TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": None,
                "player_choice": False,  
            },
            # Event_58: TRANSMISSION DELAY, Router 1, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,  
            },
            # Event_59: TRANSMISSION DELAY, Router 2, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,  
            },
            # Event_60: TRANSMISSION DELAY, Router 3, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,  
            },
            # Event_61: TRANSMISSION DELAY, Router 1, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,   
            },
            # Event_62: TRANSMISSION DELAY, Router 2, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,   
            },
            # Event_63: TRANSMISSION DELAY, Router 3, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,   
            },
            # Event_64: TRANSMISSION DELAY, Router 1, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,    
            },
            # Event_65: TRANSMISSION DELAY, Router 2, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,    
            },
            # Event_66: TRANSMISSION DELAY, Router 3, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,    
            },
            # Event_67: TRANSMISSION DELAY, Router 1, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,   
            },
            # Event_68: TRANSMISSION DELAY, Router 2, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,   
            },
            # Event_69: TRANSMISSION DELAY, Router 3, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,   
            },
            # Event_70: TRANSMISSION DELAY, Router 1, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": True,   
            },
            # Event_71: TRANSMISSION DELAY, Router 2, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": None,
                "player_choice": True,   
            },
            # Event_72: TRANSMISSION DELAY, Router 3, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": None,
                "player_choice": True,   
            },
            # Event_73: LINK FAILURE, Router 1, 1 TURN, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_74: LINK FAILURE, Router 2, 1 TURN, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,            
            },
            # Event_75: LINK FAILURE, Router 3, 1 TURN, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_76: LINK FAILURE, Router 1, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_77: LINK FAILURE, Router 2, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_78: LINK FAILURE, Router 3, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_79: LINK FAILURE, Router 1, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_80: LINK FAILURE, Router 2, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_81: LINK FAILURE, Router 3, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_82: LINK FAILURE, Router 1, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_83: LINK FAILURE, Router 2, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_84: LINK FAILURE, Router 3, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_85: LINK FAILURE, Router 1, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_86: LINK FAILURE, Router 2, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_87: LINK FAILURE, Router 3, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_88: LINK FAILURE, Router 1, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_89: LINK FAILURE, Router 2, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_90: LINK FAILURE, Router 3, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_91: LINK FAILURE, Router 1, 2 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_92: LINK FAILURE, Router 2, 2 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,                  
            },
            # Event_93: LINK FAILURE, Router 3, 2 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_94: LINK FAILURE, Router 1, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_95: LINK FAILURE, Router 2, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_96: LINK FAILURE, Router 3, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_97: LINK FAILURE, Router 1, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_98: LINK FAILURE, Router 2, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_99: LINK FAILURE, Router 3, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_100: LINK FAILURE, Router 1, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_101: LINK FAILURE, Router 2, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_102: LINK FAILURE, Router 3, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_103: LINK FAILURE, Router 1, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_104: LINK FAILURE, Router 2, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_105: LINK FAILURE, Router 3, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_106: LINK FAILURE, Router 1, 2 TURNS, jogadores cinzentos COM ? (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_107: LINK FAILURE, Router 2, 2 TURNS, jogadores cinzentos COM ? (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_108: LINK FAILURE, Router 3, 2 TURNS, jogadores cinzentos COM ? (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_109: LINK FAILURE, Router 1, 4 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_110: LINK FAILURE, Router 2, 4 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_111: LINK FAILURE, Router 3, 4 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_112: LINK FAILURE, Router 1, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_113: LINK FAILURE, Router 2, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_114: LINK FAILURE, Router 3, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_115: LINK FAILURE, Router 1, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_116: LINK FAILURE, Router 2, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_117: LINK FAILURE, Router 3, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_118: LINK FAILURE, Router 1, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_119: LINK FAILURE, Router 2, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_120: LINK FAILURE, Router 3, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_121: LINK FAILURE, Router 1, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_122: LINK FAILURE, Router 2, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_123: LINK FAILURE, Router 3, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_124: LINK FAILURE, Router 1, 4 TURNS, jogadores cinzentos COM ? (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_125: LINK FAILURE, Router 2, 4 TURNS, jogadores cinzentos COM ? (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_126: LINK FAILURE, Router 3, 4 TURNS, jogadores cinzentos COM ? (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_127: LINK FAILURE, Router 1, ? TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_128: LINK FAILURE, Router 2, ? TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_129: LINK FAILURE, Router 3, ? TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_130: LINK FAILURE, Router 1, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_131: LINK FAILURE, Router 2, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_132: LINK FAILURE, Router 3, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_133: LINK FAILURE, Router 1, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_134: LINK FAILURE, Router 2, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_135: LINK FAILURE, Router 3, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_136: LINK FAILURE, Router 1, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_137: LINK FAILURE, Router 2, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_138: LINK FAILURE, Router 3, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_139: LINK FAILURE, Router 1, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_140: LINK FAILURE, Router 2, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_141: LINK FAILURE, Router 3, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_142: LINK FAILURE, Router 1, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_143: LINK FAILURE, Router 2, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_144: LINK FAILURE, Router 3, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_145: TRAFFIC BURST, Router 1, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_146: TRAFFIC BURST, Router 2, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_147: TRAFFIC BURST, Router 3, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_148: TRAFFIC BURST, Router 1, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 1, 
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_149: TRAFFIC BURST, Router 2, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_150: TRAFFIC BURST, Router 3, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_151: TRAFFIC BURST, Router 1, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_152: TRAFFIC BURST, Router 2, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_153: TRAFFIC BURST, Router 3, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_154: TRAFFIC BURST, Router 1, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_155: TRAFFIC BURST, Router 2, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_156: TRAFFIC BURST, Router 3, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_157: TRAFFIC BURST, Router 1, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_158: TRAFFIC BURST, Router 2, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_159: TRAFFIC BURST, Router 3, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_160: TRAFFIC BURST, Router 1, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_161: TRAFFIC BURST, Router 2, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_162: TRAFFIC BURST, Router 3, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_163: TRAFFIC BURST, Router 1, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_164: TRAFFIC BURST, Router 2, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_165: TRAFFIC BURST, Router 3, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_166: TRAFFIC BURST, Router 1, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_167: TRAFFIC BURST, Router 2, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_168: TRAFFIC BURST, Router 3, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_169: TRAFFIC BURST, Router 1, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_170: TRAFFIC BURST, Router 2, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_171: TRAFFIC BURST, Router 3, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_172: TRAFFIC BURST, Router 1, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_173: TRAFFIC BURST, Router 2, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_174: TRAFFIC BURST, Router 3, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_175: TRAFFIC BURST, Router 1, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_176: TRAFFIC BURST, Router 2, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_177: TRAFFIC BURST, Router 3, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_178: TRAFFIC BURST, Router 1, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_179: TRAFFIC BURST, Router 2, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_180: TRAFFIC BURST, Router 3, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_181: TRAFFIC BURST, Router 1, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_182: TRAFFIC BURST, Router 2, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_183: TRAFFIC BURST, Router 3, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 3, 
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_184: TRAFFIC BURST, Router 1, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_185: TRAFFIC BURST, Router 2, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_186: TRAFFIC BURST, Router 3, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_187: TRAFFIC BURST, Router 1, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_188: TRAFFIC BURST, Router 2, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_189: TRAFFIC BURST, Router 3, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_190: TRAFFIC BURST, Router 1, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_191: TRAFFIC BURST, Router 2, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_192: TRAFFIC BURST, Router 3, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_193: TRAFFIC BURST, Router 1, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_194: TRAFFIC BURST, Router 2, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_195: TRAFFIC BURST, Router 3, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_196: TRAFFIC BURST, Router 1, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_197: TRAFFIC BURST, Router 2, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_198: TRAFFIC BURST, Router 3, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_199: TRAFFIC BURST, Router 1, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 1, 
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_200: TRAFFIC BURST, Router 2, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_201: TRAFFIC BURST, Router 3, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_202: TRAFFIC BURST, Router 1, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_203: TRAFFIC BURST, Router 2, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_204: TRAFFIC BURST, Router 3, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_205: TRAFFIC BURST, Router 1, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_206: TRAFFIC BURST, Router 2, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_207: TRAFFIC BURST, Router 3, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_208: TRAFFIC BURST, Router 1, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_209: TRAFFIC BURST, Router 2, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_210: TRAFFIC BURST, Router 3, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_211: TRAFFIC BURST, Router 1, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_212: TRAFFIC BURST, Router 2, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_213: TRAFFIC BURST, Router 3, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_214: TRAFFIC BURST, Router 1, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_215: TRAFFIC BURST, Router 2, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_216: TRAFFIC BURST, Router 3, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.TRAFFIC_BURST,
            },
            
            # QUEUE CONGESTION Events (Event_217 to Event_288)
            # Event_217: QUEUE CONGESTION, Router 1, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_218: QUEUE CONGESTION, Router 2, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_219: QUEUE CONGESTION, Router 3, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_220: QUEUE CONGESTION, Router 1, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_221: QUEUE CONGESTION, Router 2, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_222: QUEUE CONGESTION, Router 3, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_223: QUEUE CONGESTION, Router 1, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_224: QUEUE CONGESTION, Router 2, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_225: QUEUE CONGESTION, Router 3, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_226: QUEUE CONGESTION, Router 1, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_227: QUEUE CONGESTION, Router 2, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_228: QUEUE CONGESTION, Router 3, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_229: QUEUE CONGESTION, Router 1, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_230: QUEUE CONGESTION, Router 2, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_231: QUEUE CONGESTION, Router 3, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_232: QUEUE CONGESTION, Router 1, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_233: QUEUE CONGESTION, Router 2, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_234: QUEUE CONGESTION, Router 3, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_235: QUEUE CONGESTION, Router 1, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_236: QUEUE CONGESTION, Router 2, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_237: QUEUE CONGESTION, Router 3, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_238: QUEUE CONGESTION, Router 1, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_239: QUEUE CONGESTION, Router 2, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_240: QUEUE CONGESTION, Router 3, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_241: QUEUE CONGESTION, Router 1, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_242: QUEUE CONGESTION, Router 2, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_243: QUEUE CONGESTION, Router 3, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_244: QUEUE CONGESTION, Router 1, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_245: QUEUE CONGESTION, Router 2, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_246: QUEUE CONGESTION, Router 3, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_247: QUEUE CONGESTION, Router 1, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_248: QUEUE CONGESTION, Router 2, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_249: QUEUE CONGESTION, Router 3, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_250: QUEUE CONGESTION, Router 1, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_251: QUEUE CONGESTION, Router 2, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_252: QUEUE CONGESTION, Router 3, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_253: QUEUE CONGESTION, Router 1, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_254: QUEUE CONGESTION, Router 2, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_255: QUEUE CONGESTION, Router 3, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_256: QUEUE CONGESTION, Router 1, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_257: QUEUE CONGESTION, Router 2, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_258: QUEUE CONGESTION, Router 3, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_259: QUEUE CONGESTION, Router 1, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_260: QUEUE CONGESTION, Router 2, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_261: QUEUE CONGESTION, Router 3, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_262: QUEUE CONGESTION, Router 1, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_263: QUEUE CONGESTION, Router 2, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_264: QUEUE CONGESTION, Router 3, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_265: QUEUE CONGESTION, Router 1, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_266: QUEUE CONGESTION, Router 2, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_267: QUEUE CONGESTION, Router 3, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_268: QUEUE CONGESTION, Router 1, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_269: QUEUE CONGESTION, Router 2, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_270: QUEUE CONGESTION, Router 3, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_271: QUEUE CONGESTION, Router 1, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_272: QUEUE CONGESTION, Router 2, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_273: QUEUE CONGESTION, Router 3, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_274: QUEUE CONGESTION, Router 1, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_275: QUEUE CONGESTION, Router 2, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_276: QUEUE CONGESTION, Router 3, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_277: QUEUE CONGESTION, Router 1, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_278: QUEUE CONGESTION, Router 2, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_279: QUEUE CONGESTION, Router 3, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_280: QUEUE CONGESTION, Router 1, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_281: QUEUE CONGESTION, Router 2, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_282: QUEUE CONGESTION, Router 3, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_283: QUEUE CONGESTION, Router 1, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_284: QUEUE CONGESTION, Router 2, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_285: QUEUE CONGESTION, Router 3, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_286: QUEUE CONGESTION, Router 1, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_287: QUEUE CONGESTION, Router 2, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_288: QUEUE CONGESTION, Router 3, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            
            # QUEUE FULL Events (Event_289 to Event_360)
            # Event_289: QUEUE FULL, Router 1, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_290: QUEUE FULL, Router 2, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_291: QUEUE FULL, Router 3, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_292: QUEUE FULL, Router 1, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_293: QUEUE FULL, Router 2, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_294: QUEUE FULL, Router 3, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_295: QUEUE FULL, Router 1, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_296: QUEUE FULL, Router 2, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_297: QUEUE FULL, Router 3, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_298: QUEUE FULL, Router 1, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_299: QUEUE FULL, Router 2, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_300: QUEUE FULL, Router 3, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_301: QUEUE FULL, Router 1, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_302: QUEUE FULL, Router 2, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_303: QUEUE FULL, Router 3, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_304: QUEUE FULL, Router 1, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_305: QUEUE FULL, Router 2, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_306: QUEUE FULL, Router 3, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_307: QUEUE FULL, Router 1, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_308: QUEUE FULL, Router 2, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_309: QUEUE FULL, Router 3, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_310: QUEUE FULL, Router 1, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_311: QUEUE FULL, Router 2, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_312: QUEUE FULL, Router 3, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_313: QUEUE FULL, Router 1, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_314: QUEUE FULL, Router 2, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_315: QUEUE FULL, Router 3, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_316: QUEUE FULL, Router 1, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_317: QUEUE FULL, Router 2, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_318: QUEUE FULL, Router 3, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_319: QUEUE FULL, Router 1, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_320: QUEUE FULL, Router 2, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_321: QUEUE FULL, Router 3, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_322: QUEUE FULL, Router 1, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_323: QUEUE FULL, Router 2, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_324: QUEUE FULL, Router 3, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_325: QUEUE FULL, Router 1, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_326: QUEUE FULL, Router 2, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_327: QUEUE FULL, Router 3, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_328: QUEUE FULL, Router 1, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_329: QUEUE FULL, Router 2, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_330: QUEUE FULL, Router 3, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_331: QUEUE FULL, Router 1, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_332: QUEUE FULL, Router 2, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_333: QUEUE FULL, Router 3, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_334: QUEUE FULL, Router 1, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_335: QUEUE FULL, Router 2, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_336: QUEUE FULL, Router 3, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_337: QUEUE FULL, Router 1, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_338: QUEUE FULL, Router 2, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_339: QUEUE FULL, Router 3, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_340: QUEUE FULL, Router 1, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_341: QUEUE FULL, Router 2, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_342: QUEUE FULL, Router 3, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_343: QUEUE FULL, Router 1, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_344: QUEUE FULL, Router 2, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_345: QUEUE FULL, Router 3, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_346: QUEUE FULL, Router 1, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_347: QUEUE FULL, Router 2, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_348: QUEUE FULL, Router 3, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_349: QUEUE FULL, Router 1, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_350: QUEUE FULL, Router 2, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_351: QUEUE FULL, Router 3, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_352: QUEUE FULL, Router 1, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_353: QUEUE FULL, Router 2, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_354: QUEUE FULL, Router 3, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_355: QUEUE FULL, Router 1, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_356: QUEUE FULL, Router 2, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_357: QUEUE FULL, Router 3, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_358: QUEUE FULL, Router 1, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_359: QUEUE FULL, Router 2, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_360: QUEUE FULL, Router 3, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_FULL,
            },
            
            # PACKET DROP Events (Event_361 to Event_432)
            # Event_361: PACKET DROP, Router 1, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_362: PACKET DROP, Router 2, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_363: PACKET DROP, Router 3, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_364: PACKET DROP, Router 1, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_365: PACKET DROP, Router 2, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_366: PACKET DROP, Router 3, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_367: PACKET DROP, Router 1, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_368: PACKET DROP, Router 2, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_369: PACKET DROP, Router 3, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_370: PACKET DROP, Router 1, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_371: PACKET DROP, Router 2, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_372: PACKET DROP, Router 3, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_373: PACKET DROP, Router 1, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_374: PACKET DROP, Router 2, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_375: PACKET DROP, Router 3, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_376: PACKET DROP, Router 1, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_377: PACKET DROP, Router 2, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_378: PACKET DROP, Router 3, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_379: PACKET DROP, Router 1, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_380: PACKET DROP, Router 2, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_381: PACKET DROP, Router 3, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_382: PACKET DROP, Router 1, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_383: PACKET DROP, Router 2, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_384: PACKET DROP, Router 3, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_385: PACKET DROP, Router 1, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_386: PACKET DROP, Router 2, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_387: PACKET DROP, Router 3, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_388: PACKET DROP, Router 1, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_389: PACKET DROP, Router 2, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_390: PACKET DROP, Router 3, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_391: PACKET DROP, Router 1, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_392: PACKET DROP, Router 2, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_393: PACKET DROP, Router 3, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_394: PACKET DROP, Router 1, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_395: PACKET DROP, Router 2, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_396: PACKET DROP, Router 3, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_397: PACKET DROP, Router 1, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_398: PACKET DROP, Router 2, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_399: PACKET DROP, Router 3, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_400: PACKET DROP, Router 1, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_401: PACKET DROP, Router 2, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_402: PACKET DROP, Router 3, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_403: PACKET DROP, Router 1, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_404: PACKET DROP, Router 2, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_405: PACKET DROP, Router 3, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_406: PACKET DROP, Router 1, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_407: PACKET DROP, Router 2, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_408: PACKET DROP, Router 3, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_409: PACKET DROP, Router 1, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_410: PACKET DROP, Router 2, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_411: PACKET DROP, Router 3, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_412: PACKET DROP, Router 1, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_413: PACKET DROP, Router 2, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_414: PACKET DROP, Router 3, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_415: PACKET DROP, Router 1, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_416: PACKET DROP, Router 2, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_417: PACKET DROP, Router 3, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_418: PACKET DROP, Router 1, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_419: PACKET DROP, Router 2, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_420: PACKET DROP, Router 3, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_421: PACKET DROP, Router 1, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_422: PACKET DROP, Router 2, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_423: PACKET DROP, Router 3, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_424: PACKET DROP, Router 1, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_425: PACKET DROP, Router 2, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_426: PACKET DROP, Router 3, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_427: PACKET DROP, Router 1, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_428: PACKET DROP, Router 2, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_429: PACKET DROP, Router 3, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_430: PACKET DROP, Router 1, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_431: PACKET DROP, Router 2, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_432: PACKET DROP, Router 3, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.PACKET_DROP,
            },
            
            # EMPTY QUEUE Events (Event_433 to Event_504)
            # Event_433: EMPTY QUEUE, Router 1, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_434: EMPTY QUEUE, Router 2, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_435: EMPTY QUEUE, Router 3, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_436: EMPTY QUEUE, Router 1, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_437: EMPTY QUEUE, Router 2, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_438: EMPTY QUEUE, Router 3, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_439: EMPTY QUEUE, Router 1, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_440: EMPTY QUEUE, Router 2, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_441: EMPTY QUEUE, Router 3, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_442: EMPTY QUEUE, Router 1, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_443: EMPTY QUEUE, Router 2, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_444: EMPTY QUEUE, Router 3, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_445: EMPTY QUEUE, Router 1, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_446: EMPTY QUEUE, Router 2, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_447: EMPTY QUEUE, Router 3, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_448: EMPTY QUEUE, Router 1, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_449: EMPTY QUEUE, Router 2, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_450: EMPTY QUEUE, Router 3, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_451: EMPTY QUEUE, Router 1, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_452: EMPTY QUEUE, Router 2, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_453: EMPTY QUEUE, Router 3, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_454: EMPTY QUEUE, Router 1, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_455: EMPTY QUEUE, Router 2, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_456: EMPTY QUEUE, Router 3, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_457: EMPTY QUEUE, Router 1, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_458: EMPTY QUEUE, Router 2, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_459: EMPTY QUEUE, Router 3, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_460: EMPTY QUEUE, Router 1, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_461: EMPTY QUEUE, Router 2, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_462: EMPTY QUEUE, Router 3, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_463: EMPTY QUEUE, Router 1, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_464: EMPTY QUEUE, Router 2, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_465: EMPTY QUEUE, Router 3, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_466: EMPTY QUEUE, Router 1, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_467: EMPTY QUEUE, Router 2, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_468: EMPTY QUEUE, Router 3, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_469: EMPTY QUEUE, Router 1, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_470: EMPTY QUEUE, Router 2, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_471: EMPTY QUEUE, Router 3, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_472: EMPTY QUEUE, Router 1, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_473: EMPTY QUEUE, Router 2, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_474: EMPTY QUEUE, Router 3, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_475: EMPTY QUEUE, Router 1, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_476: EMPTY QUEUE, Router 2, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_477: EMPTY QUEUE, Router 3, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_478: EMPTY QUEUE, Router 1, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_479: EMPTY QUEUE, Router 2, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_480: EMPTY QUEUE, Router 3, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_481: EMPTY QUEUE, Router 1, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_482: EMPTY QUEUE, Router 2, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_483: EMPTY QUEUE, Router 3, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_484: EMPTY QUEUE, Router 1, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_485: EMPTY QUEUE, Router 2, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_486: EMPTY QUEUE, Router 3, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_487: EMPTY QUEUE, Router 1, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_488: EMPTY QUEUE, Router 2, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_489: EMPTY QUEUE, Router 3, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_490: EMPTY QUEUE, Router 1, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_491: EMPTY QUEUE, Router 2, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_492: EMPTY QUEUE, Router 3, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_493: EMPTY QUEUE, Router 1, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_494: EMPTY QUEUE, Router 2, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_495: EMPTY QUEUE, Router 3, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_496: EMPTY QUEUE, Router 1, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_497: EMPTY QUEUE, Router 2, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_498: EMPTY QUEUE, Router 3, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_499: EMPTY QUEUE, Router 1, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_500: EMPTY QUEUE, Router 2, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_501: EMPTY QUEUE, Router 3, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_502: EMPTY QUEUE, Router 1, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_503: EMPTY QUEUE, Router 2, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_504: EMPTY QUEUE, Router 3, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.EMPTY_QUEUE,
            },
            
            
        ]
        
        # Criar cartas de eventos
        for idx, template in enumerate(event_templates):
            event_id = f"event_{idx+1}"
            router_id = template["router_id"]
            player_choice = template["player_choice"]
            
            # Determinar o tipo de evento
            event_type = template.get("event_type", EventType.TRANSMISSION_DELAY)
            
            # Determinar título, descrição e efeito baseado no tipo de evento
            if event_type == EventType.LINK_FAILURE:
                title = "LINK FAILURE"
                description = "A network connection failed, disrupting communication. All in-transit packets are lost!"
                if template["duration_turns"] == "variable":
                    if player_choice:
                        effect_text = "Remove all packets from the link. \nNo packets will be added to the link during \nthe event."
                    else:
                        effect_text = "Remove all packets from the link. \nNo packets will be added to the link during \nthe event."
                else:
                    if player_choice:
                        effect_text = "Remove all packets from the link. \nNo packets will be added to the link during \nthe event."
                    else:
                        effect_text = "Remove all packets from the link. \nNo packets will be added to the link during \nthe event."
            elif event_type == EventType.TRAFFIC_BURST:
                title = "TRAFFIC BURST"
                description = "Some users are generating a burst of traffic, and the queue is growing fast. New transmissions are postponed!"
                if template["duration_turns"] == "variable":
                    # Cartas com duração variável (? TURNS)
                    if player_choice:
                        effect_text = "At each turn of the event, \nadd 1 dummy packet to the queue and \nkeep transmitting 1 packet per turn."
                    else:
                        effect_text = "At each turn of the event, \nadd 1 dummy packet to the queue and \nkeep transmitting 1 packet per turn."
                else:
                    # Cartas com duração fixa
                    if player_choice:
                        effect_text = "At each turn of the event, \nadd 1 dummy packet to the queue and \nkeep transmitting 1 packet per turn."
                    else:
                        effect_text = "At each turn of the event, \nadd 1 dummy packet to the queue and \nkeep transmitting 1 packet per turn."
            elif event_type == EventType.QUEUE_CONGESTION:
                title = "QUEUE CONGESTION"
                description = "Too many users are attempting to transmit video! The queue is growing too fast, becoming congested."
                if template["duration_turns"] == "variable":
                    # Cartas com duração variável (? TURNS)
                    if player_choice:
                        effect_text = "At each turn, \nadd 2 dummy packets to the queue and \nkeep transmitting 1 packet per turn."
                    else:
                        effect_text = "At each turn, \nadd 2 dummy packets to the queue and \nkeep transmitting 1 packet per turn."
                else:
                    # Cartas com duração fixa
                    if player_choice:
                        effect_text = "At each turn, \nadd 2 dummy packets to the queue and \nkeep transmitting 1 packet per turn."
                    else:
                        effect_text = "At each turn, \nadd 2 dummy packets to the queue and \nkeep transmitting 1 packet per turn."
            elif event_type == EventType.QUEUE_FULL:
                title = "QUEUE FULL"
                description = "The high volume of incoming packets has overwhelmed the network devices, and the queue is full!"
                if template["duration_turns"] == "variable":
                    # Cartas com duração variável (? TURNS)
                    if player_choice:
                        effect_text = "At each event turn, \nfill the queue with dummy packets and \ntransmit one packet per turn."
                    else:
                        effect_text = "At each event turn, \nfill the queue with dummy packets and \ntransmit one packet per turn."
                else:
                    # Cartas com duração fixa
                    if player_choice:
                        effect_text = "At each event turn, \nfill the queue with dummy packets and \ntransmit one packet per turn."
                    else:
                        effect_text = "At each event turn, \nfill the queue with dummy packets and \ntransmit one packet per turn."
            elif event_type == EventType.PACKET_DROP:
                title = "PACKET DROP"
                description = "Due to several errors, packets have been dropped in the queue, disrupting communication."
                if template["duration_turns"] == "variable":
                    # Cartas com duração variável (? TURNS)
                    if player_choice:
                        effect_text = "At each turn of the event, \nremove 1 packet from the queue and \ndo not transmit any packet."
                    else:
                        effect_text = "At each turn of the event, \nremove 1 packet from the queue and \ndo not transmit any packet."
                else:
                    # Cartas com duração fixa
                    if player_choice:
                        effect_text = "At each turn of the event, \nremove 1 packet from the queue and \ndo not transmit any packet."
                    else:
                        effect_text = "At each turn of the event, \nremove 1 packet from the queue and \ndo not transmit any packet."
            elif event_type == EventType.EMPTY_QUEUE:
                title = "EMPTY QUEUE"
                description = "Due to severe errors, packets have been dropped in the queue, severely disrupting the communication."
                if template["duration_turns"] == "variable":
                    # Cartas com duração variável (? TURNS)
                    if player_choice:
                        effect_text = "At each turn, \nremove all packets from the queue."
                    else:
                        effect_text = "At each turn, \nremove all packets from the queue."
                else:
                    # Cartas com duração fixa
                    if player_choice:
                        effect_text = "At each turn, \nremove all packets from the queue."
                    else:
                        effect_text = "At each turn, \nremove all packets from the queue."


            else:  # TRANSMISSION DELAY
                title = "TRANSMISSION DELAY"
                description = "Currently, the traffic is being transmitted through a low-capacity link, which is causing a significant delay in the delivery of the traffic."
                # Para TRANSMISSION DELAY, usar a lógica existente baseada na regra dos jogadores cinzentos
                if template["duration_turns"] == "variable":
                    # Cartas com duração variável (? TURNS)
                    if player_choice:
                        effect_text = "At each turn, \ndo not add packets or \nmove the packets in the link."
                    else:
                        effect_text = "At each turn, \ndo not add packets or \nmove the packets in the link."
                else:
                    # Cartas com duração fixa
                    if player_choice:
                        effect_text = "At each turn, \ndo not add packets or \nmove the packets in the link."
                    else:
                        effect_text = "At each turn, \ndo not add packets or \nmove the packets in the link."


                         
            
            # Tratar duração - preservar "variable" como string
            duration = template["duration_turns"]
            # Não converter "variable" para 0 - manter como string para o sistema de tracking
            
            # Determinar se deve usar target_link ou target_queue baseado no número do evento
            event_number = int(event_id.split('_')[1])
            
            # Event_1 a Event_144: usar target_link
            # Event_145 a Event_504: usar target_queue
            if 1 <= event_number <= 144:
                target_link = f"Link to Residential Router {router_id}"
                target_queue = None
            elif 145 <= event_number <= 504:
                target_link = None
                target_queue = f"Queue of Residential Router {router_id}"
            else:
                # Para outros eventos, usar ambos
                target_link = f"Link to Residential Router {router_id}"
                target_queue = f"Queue of Residential Router {router_id}"
            
            event_card = EventCard(
                event_id=event_id,
                event_type=event_type,
                title=title,
                description=description,
                effect_description=effect_text,
                duration_turns=duration,
                target_link=target_link,
                target_queue=target_queue,
                router_id=router_id,
                target_player=template["target_player"],
                player_choice=player_choice
            )
            
            self.events[event_id] = event_card
    
    # Métodos de acesso aos dados
    def get_user(self, user_id: str) -> Optional[UserCard]:
        """Obtém carta de utilizador por ID"""
        return self.users.get(user_id)
    
    def get_equipment(self, equipment_id: str) -> Optional[EquipmentCard]:
        """Obtém carta de equipamento por ID"""
        return self.equipments.get(equipment_id)
    
    def get_service(self, service_id: str) -> Optional[ServiceCard]:
        """Obtém carta de serviço por ID"""
        return self.services.get(service_id)
    
    def get_activity(self, activity_id: str) -> Optional[ActivityCard]:
        """Obtém carta de atividade por ID"""
        return self.activities.get(activity_id)
    
    def get_challenge(self, challenge_id: str) -> Optional[ChallengeCard]:
        """Obtém carta de desafio por ID"""
        return self.challenges.get(challenge_id)
    
    def get_action(self, action_id: str) -> Optional[ActionCard]:
        """Obtém carta de ação por ID"""
        return self.actions.get(action_id)
    
    def get_event(self, event_id: str) -> Optional[EventCard]:
        """Obtém carta de evento por ID"""
        return self.events.get(event_id)
    
    def get_users_by_color(self, color: str) -> List[UserCard]:
        """Obtém todas as cartas de utilizadores de uma cor"""
        return [card for card in self.users.values() if card.color == color]
    
    def get_equipments_by_color(self, color: str) -> List[EquipmentCard]:
        """Obtém todas as cartas de equipamentos de uma cor"""
        return [card for card in self.equipments.values() if card.color == color]
    
    def get_services_by_color(self, color: str) -> List[ServiceCard]:
        """Obtém todas as cartas de serviços de uma cor"""
        return [card for card in self.services.values() if card.color == color]
    
    def get_activities_by_color(self, color: str) -> List[ActivityCard]:
        """Obtém todas as cartas de atividades de uma cor"""
        return [card for card in self.activities.values() if card.color == color]
    
    def get_all_challenges(self) -> List[ChallengeCard]:
        """Obtém todas as cartas de desafios"""
        return list(self.challenges.values())
    
    def get_all_users(self) -> List[UserCard]:
        """Obtém todas as cartas de utilizadores"""
        return list(self.users.values())
    
    def get_all_equipments(self) -> List[EquipmentCard]:
        """Obtém todas as cartas de equipamentos"""
        return list(self.equipments.values())
    
    def get_all_services(self) -> List[ServiceCard]:
        """Obtém todas as cartas de serviços"""
        return list(self.services.values())
    
    def get_all_activities(self) -> List[ActivityCard]:
        """Obtém todas as cartas de atividades"""
        return list(self.activities.values())
    
    def get_all_actions(self) -> List[ActionCard]:
        """Obtém todas as cartas de ação"""
        return list(self.actions.values())
    
    def get_all_events(self) -> List[EventCard]:
        """Obtém todas as cartas de eventos"""
        return list(self.events.values())
    
    def get_user_ids(self) -> List[str]:
        """Obtém todos os IDs de utilizadores"""
        return list(self.users.keys())
    
    def get_equipment_ids(self) -> List[str]:
        """Obtém todos os IDs de equipamentos"""
        return list(self.equipments.keys())
    
    def get_service_ids(self) -> List[str]:
        """Obtém todos os IDs de serviços"""
        return list(self.services.keys())
    
    def get_activity_ids(self) -> List[str]:
        """Obtém todos os IDs de atividades"""
        return list(self.activities.keys())
    
    def get_challenge_ids(self) -> List[str]:
        """Obtém todos os IDs de desafios"""
        return list(self.challenges.keys())
    
    def get_action_ids(self) -> List[str]:
        """Obtém todos os IDs de ações"""
        return list(self.actions.keys())
    
    def get_event_ids(self) -> List[str]:
        """Obtém todos os IDs de eventos"""
        return list(self.events.keys())
    
    def get_actions_by_player_color(self, color: str) -> List[ActionCard]:
        """Obtém todas as cartas de ação que afetam um jogador de cor específica"""
        return [action for action in self.actions.values() if action.target == color.lower()]
    
    def get_actions_with_player_choice(self) -> List[ActionCard]:
        """Obtém todas as cartas de ação onde afeta o próprio jogador que tirou a carta"""
        return [action for action in self.actions.values() if action.target is None]
    
    def get_actions_with_specific_targets(self) -> List[ActionCard]:
        """Obtém todas as cartas de ação com alvos específicos"""
        return [action for action in self.actions.values() if action.target is not None]
    
    def get_actions_by_router_id(self, router_id: int) -> List[ActionCard]:
        """Obtém todas as cartas de ação que correspondem a um router_id específico"""
        return [action for action in self.actions.values() if action.router_id == router_id]
    
    def get_events_by_router_id(self, router_id: int) -> List[EventCard]:
        """Obtém todas as cartas de eventos que afetam um router_id específico"""
        return [event for event in self.events.values() if event.router_id == router_id]
    
    def get_events_by_player_color(self, color: str) -> List[EventCard]:
        """Obtém todas as cartas de eventos que afetam um jogador de cor específica"""
        return [event for event in self.events.values() if event.target_player == color.lower()]
    
    def get_events_with_player_choice(self) -> List[EventCard]:
        """Obtém todas as cartas de eventos onde o jogador pode escolher o alvo"""
        return [event for event in self.events.values() if event.player_choice]
    
    def get_events_with_specific_targets(self) -> List[EventCard]:
        """Obtém todas as cartas de eventos com alvos específicos"""
        return [event for event in self.events.values() if not event.player_choice]
    
    def get_events_by_duration(self, duration: int) -> List[EventCard]:
        """Obtém todas as cartas de eventos com duração específica"""
        return [event for event in self.events.values() if event.duration_turns == duration]
    
    def get_available_colors(self) -> Set[str]:
        """Obtém todas as cores disponíveis"""
        return {"red", "green", "blue", "yellow"}
    
    def get_statistics(self) -> Dict[str, int]:
        """Obtém estatísticas da base de dados"""
        return {
            "total_users": len(self.users),
            "total_equipments": len(self.equipments),
            "total_services": len(self.services),
            "total_activities": len(self.activities),
            "total_challenges": len(self.challenges),
            "total_actions": len(self.actions),
            "total_events": len(self.events),
            "total_cards": len(self.users) + len(self.equipments) + len(self.services) + len(self.activities) + len(self.challenges) + len(self.actions) + len(self.events)
        }

def get_event_duration(carta_path: str) -> Optional[Union[int, str]]:
    """
    Obtém a duração em turnos de uma carta Event baseada no seu caminho.
    
    Args:
        carta_path: Caminho para a carta Event (ex: "/path/Event_1.png")
        
    Returns:
        Duração em turnos da carta (int para duração fixa, "variable" para duração variável) ou None se não encontrada
    """
    import os
    import re
    
    # Extrair o ID da carta do caminho (ex: "Event_1" de "/path/Event_1.png")
    filename = os.path.basename(carta_path)
    match = re.match(r'Event_(\d+)', filename)
    
    if not match:
        return None
    
    event_id = f"event_{match.group(1)}"
    
    # Criar instância da base de dados se não existir globalmente
    if not hasattr(get_event_duration, 'db'):
        get_event_duration.db = UserDatabase()
    
    # Obter a carta Event
    event_card = get_event_duration.db.get_event(event_id)
    
    if event_card:
        return event_card.duration_turns
    
    return None

def main():
    """
    Função de demonstração da base de dados
    """
    print("=" * 60)
    print("        BASE DE DADOS DE CARTAS NETMASTER")
    print("=" * 60)
    
    # Criar base de dados
    db = UserDatabase()
    
    # Mostrar estatísticas
    stats = db.get_statistics()
    print(f"\nEstatísticas da Base de Dados:")
    print(f"- Cartas de Utilizadores: {stats['total_users']}")
    print(f"- Cartas de Equipamentos: {stats['total_equipments']}")
    print(f"- Cartas de Servicos: {stats['total_services']}")
    print(f"- Cartas de Atividades: {stats['total_activities']}")
    print(f"- Cartas de Desafios: {stats['total_challenges']}")
    print(f"- Cartas de Acoes: {stats['total_actions']}")
    print(f"- Total de Cartas: {stats['total_cards']}")
    
    # Exemplo de cartas
    print(f"\nExemplos de Cartas:")
    
    # Utilizador exemplo
    user = db.get_user("1_red")
    if user:
        print(f"- {user}")
    
    # Equipamento exemplo
    equipment = db.get_equipment("small_router_1_red")
    if equipment:
        print(f"- {equipment}")
    
    # Servico exemplo
    service = db.get_service("service_bandwidth_1_red")
    if service:
        print(f"- {service}")
    
    # Atividade exemplo
    activity = db.get_activity("activity_home_surveillance_1_red")
    if activity:
        print(f"- {activity}")
    
    # Desafio exemplo
    challenge = db.get_challenge("challenge_message_mission_1")
    if challenge:
        print(f"- {challenge}")
    
    # Acao exemplo
    action = db.get_action("action_1")
    if action:
        print(f"- {action}")
    
    print(f"\nCores disponiveis: {', '.join(db.get_available_colors())}")

if __name__ == "__main__":
    main()
