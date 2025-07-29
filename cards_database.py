#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base de Dados de Cartas NetMaster
Sistema de armazenamento e gestão de cartas Users, Equipments e Contracts
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from enum import Enum
import re

class UserType(Enum):
    """Tipos de utilizadores disponíveis"""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"

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

    def __str__(self):
        if self.category == "Router":
            return f"EquipmentCard(id={self.equipment_id}, {self.model}, queue={self.queue_size})"
        else:
            return f"EquipmentCard(id={self.equipment_id}, {self.model}, rate={self.link_rate}, length={self.link_length})"

@dataclass
class ServiceCard:
    """Carta de serviço"""
    service_id: str             # ID único da carta (Service_1, Service_2, etc.)
    service_type: ServiceType   # BANDWIDTH, DATA_VOLUME, TEMPORARY
    color: str                  # Cor da carta
    title: str                  # "BANDWIDTH", "DATA VOLUME", "TEMPORARY"
    description: str            # Descrição do serviço
    valid_for: str             # "1 Residential User" (sempre o mesmo)
    service_conditions: str     # Condições específicas: "up to 1 packet per turn", "5 packets", "4 turns"
    buy_cost: int              # Preço de compra em picoins
    sell_cost: int             # Preço de venda em picoins (sempre 0 nas cartas físicas)
    # Campos de metadados fixos
    collection: str = "Packet Switching Collection"
    level: str = "Level I"

    def __str__(self):
        return f"ServiceCard(id={self.service_id}, {self.title}, conditions={self.service_conditions}, buy={self.buy_cost})"

@dataclass
class ActivityCard:
    """Carta de atividade/aplicação"""
    activity_id: str                    # ID único da carta (Activity_1, Activity_2, etc.)
    activity_type: ActivityType         # HOME_SURVEILLANCE, HOME_SAFETY, SHORT_MESSAGE, GAMING, FILE_TRANSFER
    color: str                         # Cor da carta
    title: str                         # "HOME SURVEILLANCE", "HOME SAFETY", etc.
    description: str                   # Descrição da aplicação
    message_size: int                  # Número de pacotes por mensagem
    rate: str                         # Taxa de envio: "1 packet per turn", "up to 1 packet per turn"
    destination: str                  # Destino das mensagens (sempre "Central node")
    drops_allowed: bool               # Se permite drops ou não
    # Campos de recompensas e penalizações
    reward_per_packet: int            # Picoins ganhos por pacote recebido
    message_bonus: Optional[int]      # Bónus por mensagem completa recebida
    penalty_per_packet: Optional[int] # Penalização por pacote perdido
    application_fee: int              # Taxa de aplicação em picoins
    # Campos de condições especiais
    bonus_condition: Optional[str]    # Condição para bónus: "After 10 packets received", "Message received", etc.
    penalty_condition: Optional[str]  # Condição para penalização: "10 or fewer packets drops", etc.
    # Campos de metadados fixos
    collection: str = "Packet Switching Collection"
    level: str = "Level I"

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
    rate: str                         # Taxa de envio de pacotes
    destination: str                  # Destino (sempre "Central node")
    drops_allowed: bool               # Se permite drops ou não
    # Campos de recompensas específicas
    reward_per_packet: Optional[int]  # Picoins por pacote recebido
    message_bonus: Optional[int]      # Bónus por mensagem completa/recebida
    time_limit_bonus: Optional[int]   # Bónus por completar dentro do prazo
    # Campos de penalizações
    challenge_quit_fee: int           # Taxa por desistir do desafio
    # Campos específicos para alguns tipos
    time_limit: Optional[int]         # Limite de tempo em turnos (MESSAGE_SPRINT)
    time_to_receive: Optional[int]    # Tempo para receber mensagem (PACKET_RACE)
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
    duration_turns: int                # Duração em turnos (1, 2, 4, ou 0 para duração variável determinada por dado)
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
        
        for i in range(1, 6):  # User_1 a User_5
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
                    # User_2 a User_5 correspondem a User IDs 1 a 4
                    actual_user_id = i - 1  # User_2=1, User_3=2, User_4=3, User_5=4
                    user_id = f"{actual_user_id}_{color}"
                    
                    # Todos os User IDs têm as mesmas características conforme cartas físicas
                    users_count = 1     # 1 user per card
                    applications = 1    # 1 application
                    services = 1        # 1 service
                    buy_cost = 1        # Buy cost: 1 picoin
                    sell_cost = 2       # Sell cost: 2 picoins
                
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
        
        # Small Router (Equipment_1 a Equipment_4)
        for i in range(1, 5):
            for color in colors:
                equipment_id = f"small_router_{i}_{color}"
                
                equipment_card = EquipmentCard(
                    equipment_id=equipment_id,
                    equipment_type=EquipmentType.SMALL_ROUTER,
                    color=color,
                    category="Router",
                    model="Small Router",
                    specific_id=i,
                    queue_size=2 + i,  # Tamanho da queue
                    link_rate=None,
                    link_length=None,
                    buy_cost=100 + (i * 50),
                    sell_cost=50 + (i * 25)
                )
                
                self.equipments[equipment_id] = equipment_card
        
        # Medium Router (Equipment_5 a Equipment_8)
        for i in range(5, 9):
            for color in colors:
                equipment_id = f"medium_router_{i}_{color}"
                
                equipment_card = EquipmentCard(
                    equipment_id=equipment_id,
                    equipment_type=EquipmentType.MEDIUM_ROUTER,
                    color=color,
                    category="Router",
                    model="Medium Router",
                    specific_id=i-4,
                    queue_size=5 + (i-4),  # Tamanho da queue
                    link_rate=None,
                    link_length=None,
                    buy_cost=200 + ((i-4) * 75),
                    sell_cost=100 + ((i-4) * 37)
                )
                
                self.equipments[equipment_id] = equipment_card
        
        # Short Link (Equipment_9 a Equipment_12)
        for i in range(9, 13):
            for color in colors:
                equipment_id = f"short_link_{i}_{color}"
                
                equipment_card = EquipmentCard(
                    equipment_id=equipment_id,
                    equipment_type=EquipmentType.SHORT_LINK,
                    color=color,
                    category="Link",
                    model="Short Link",
                    specific_id=i-8,
                    queue_size=None,
                    link_rate="1 packet per turn",
                    link_length=2 + (i-8),  # Comprimento do link
                    buy_cost=150 + ((i-8) * 50),
                    sell_cost=75 + ((i-8) * 25)
                )
                
                self.equipments[equipment_id] = equipment_card
        
        # Long Link (Equipment_13 a Equipment_16)
        for i in range(13, 17):
            for color in colors:
                equipment_id = f"long_link_{i}_{color}"
                
                equipment_card = EquipmentCard(
                    equipment_id=equipment_id,
                    equipment_type=EquipmentType.LONG_LINK,
                    color=color,
                    category="Link",
                    model="Long Link",
                    specific_id=i-12,
                    queue_size=None,
                    link_rate="1 packet per turn",
                    link_length=5 + (i-12),  # Comprimento do link
                    buy_cost=250 + ((i-12) * 75),
                    sell_cost=125 + ((i-12) * 37)
                )
                
                self.equipments[equipment_id] = equipment_card
    
    def _create_service_cards(self):
        """Cria as cartas de serviços"""
        colors = ["red", "green", "blue", "yellow"]
        
        # Definir dados das cartas Services (baseado no services_card_integration.py)
        service_templates = [
            # Bandwidth Services (1 por cor)
            {
                "type": ServiceType.BANDWIDTH,
                "name_template": "Bandwidth Service {color}",
                "title": "BANDWIDTH",
                "description": "Subscribe to our Bandwidth Service and enjoy seamless network access whenever you need it",
                "service_conditions": "up to 1 packet per turn",
                "buy_price": 80
            },
            # Data Volume Services (3 por cor)
            {
                "type": ServiceType.DATA_VOLUME,
                "name_template": "Data Volume Service {color} 5",
                "title": "DATA VOLUME",
                "description": "Subscribe to our Data Volume Service and pay only for the data you actually use. Enjoy flexible access without long-term obligations!",
                "service_conditions": "5 packets",
                "buy_price": 5
            },
            {
                "type": ServiceType.DATA_VOLUME,
                "name_template": "Data Volume Service {color} 8",
                "title": "DATA VOLUME",
                "description": "Subscribe to our Data Volume Service and pay only for the data you actually use. Enjoy flexible access without long-term obligations!",
                "service_conditions": "10 packets",
                "buy_price": 8
            },
            {
                "type": ServiceType.DATA_VOLUME,
                "name_template": "Data Volume Service {color} 15",
                "title": "DATA VOLUME",
                "description": "Subscribe to our Data Volume Service and pay only for the data you actually use. Enjoy flexible access without long-term obligations!",
                "service_conditions": "20 packets",
                "buy_price": 15
            },
            # Temporary Services (3 por cor)
            {
                "type": ServiceType.TEMPORARY,
                "name_template": "Temporary Service {color} 4",
                "title": "TEMPORARY",
                "description": "Subscribe to our Temporary Service and pay only for the time you need. Access the network as long as you require, with no long-term commitments.",
                "service_conditions": "4 turns",
                "buy_price": 4
            },
            {
                "type": ServiceType.TEMPORARY,
                "name_template": "Temporary Service {color} 7",
                "title": "TEMPORARY",
                "description": "Subscribe to our Temporary Service and pay only for the time you need. Access the network as long as you require, with no long-term commitments.",
                "service_conditions": "8 turns",
                "buy_price": 7
            },
            {
                "type": ServiceType.TEMPORARY,
                "name_template": "Temporary Service {color} 14",
                "title": "TEMPORARY",
                "description": "Subscribe to our Temporary Service and pay only for the time you need. Access the network as long as you require, with no long-term commitments.",
                "service_conditions": "16 turns",
                "buy_price": 14
            }
        ]
        
        # Criar cartas para cada cor
        for color in colors:
            for idx, template in enumerate(service_templates):
                service_id = f"service_{template['type'].value}_{idx+1}_{color}"
                
                service_card = ServiceCard(
                    service_id=service_id,
                    service_type=template["type"],
                    color=color,
                    title=template["title"],
                    description=template["description"],
                    valid_for="1 Residential User",
                    service_conditions=template["service_conditions"],
                    buy_cost=template["buy_price"],
                    sell_cost=template["buy_price"] // 2  # Venda é metade do preço de compra
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
                "rate": "1 packet per turn",
                "drops_allowed": True,
                "reward_per_packet": 4,
                "message_bonus": None,
                "penalty_per_packet": None,
                "application_fee": 40,
                "bonus_condition": None,
                "penalty_condition": None
            },
            {
                "type": ActivityType.HOME_SURVEILLANCE,
                "title": "HOME SURVEILLANCE",
                "description": "With our Home Surveillance application, you can monitor your home from anywhere. It's simple and low on traffic, but it doesn't guarantee delivery—avoid it for critical information!",
                "message_size": 20,
                "rate": "1 packet per turn",
                "drops_allowed": True,
                "reward_per_packet": 3,
                "message_bonus": 4,
                "penalty_per_packet": None,
                "application_fee": 40,
                "bonus_condition": "After 10 packets received",
                "penalty_condition": None
            },
            {
                "type": ActivityType.HOME_SURVEILLANCE,
                "title": "HOME SURVEILLANCE",
                "description": "With our Home Surveillance application, you can monitor your home from anywhere. It's simple and low-traffic, but it doesn't guarantee delivery—avoid it for critical information!",
                "message_size": 20,
                "rate": "1 packet per turn",
                "drops_allowed": True,
                "reward_per_packet": 4,
                "message_bonus": 20,
                "penalty_per_packet": None,
                "application_fee": 60,
                "bonus_condition": "After 15 packets received",
                "penalty_condition": None
            },
            {
                "type": ActivityType.HOME_SURVEILLANCE,
                "title": "HOME SURVEILLANCE",
                "description": "With our Home Surveillance application, you can monitor your home from anywhere. It's simple and low-traffic, but it doesn't guarantee delivery—avoid it for critical information!",
                "message_size": 20,
                "rate": "1 packet per turn",
                "drops_allowed": True,
                "reward_per_packet": 1,
                "message_bonus": 160,
                "penalty_per_packet": None,
                "application_fee": 40,
                "bonus_condition": "No drops",
                "penalty_condition": None
            },
            # HOME SAFETY - 3 variações diferentes
            {
                "type": ActivityType.HOME_SAFETY,
                "title": "HOME SAFETY",
                "description": "Keep your home safe with our Emergency application. It's simple, low-traffic, and guarantees delivery—perfect for emergency situations!",
                "message_size": 20,
                "rate": "up to 1 packet per turn",
                "drops_allowed": False,
                "reward_per_packet": 0,
                "message_bonus": 160,
                "penalty_per_packet": None,
                "application_fee": 40,
                "bonus_condition": "Message received",
                "penalty_condition": None
            },
            {
                "type": ActivityType.HOME_SAFETY,
                "title": "HOME SAFETY",
                "description": "Keep your home safe with our Emergency application. It's simple, low-traffic, and guarantees delivery—perfect for emergency situations!",
                "message_size": 20,
                "rate": "up to 1 packet per turn",
                "drops_allowed": False,
                "reward_per_packet": 0,
                "message_bonus": 320,
                "penalty_per_packet": 8,
                "application_fee": 60,
                "bonus_condition": "Message received",
                "penalty_condition": "10 or fewer packets drops"
            },
            {
                "type": ActivityType.HOME_SAFETY,
                "title": "HOME SAFETY",
                "description": "Keep your home safe with our Emergency application. It's simple, low-traffic, and guarantees delivery—perfect for emergency situations!",
                "message_size": 20,
                "rate": "up to 1 packet per turn",
                "drops_allowed": False,
                "reward_per_packet": 0,
                "message_bonus": 480,
                "penalty_per_packet": 4,
                "application_fee": 60,
                "bonus_condition": "Message received",
                "penalty_condition": "5 or fewer packets drops"
            },
            # SHORT MESSAGE - 2 variações diferentes
            {
                "type": ActivityType.SHORT_MESSAGE,
                "title": "SHORT MESSAGE",
                "description": "Take a quick break and connect with friends using our Short Message application. It's easy to use, traffic-friendly, and ensures your packets are delivered—perfect for everyday chats!",
                "message_size": 4,
                "rate": "up to 1 packet per turn",
                "drops_allowed": False,
                "reward_per_packet": 0,
                "message_bonus": 12,
                "penalty_per_packet": None,
                "application_fee": 5,
                "bonus_condition": "Message received",
                "penalty_condition": None
            },
            {
                "type": ActivityType.SHORT_MESSAGE,
                "title": "SHORT MESSAGE",
                "description": "Take a quick break and connect with friends using our Short Message application. It's easy to use, traffic-friendly, and ensures your packets are delivered—perfect for everyday chats!",
                "message_size": 4,
                "rate": "up to 1 packet per turn",
                "drops_allowed": False,
                "reward_per_packet": 0,
                "message_bonus": 16,
                "penalty_per_packet": 2,
                "application_fee": 5,
                "bonus_condition": "Message received",
                "penalty_condition": "Per packet drop"
            },
            # GAMING - 2 variações diferentes
            {
                "type": ActivityType.GAMING,
                "title": "GAMING",
                "description": "Enjoy your gaming moments with our Gaming application. It's easy to use and consumes minimal traffic, but sometimes it might miss a few moves—no big deal!",
                "message_size": 4,
                "rate": "1 packet per turn",
                "drops_allowed": True,
                "reward_per_packet": 3,
                "message_bonus": None,
                "penalty_per_packet": None,
                "application_fee": 5,
                "bonus_condition": None,
                "penalty_condition": None
            },
            {
                "type": ActivityType.GAMING,
                "title": "GAMING",
                "description": "Enjoy your gaming moments with our Gaming application. It's easy to use and consumes minimal traffic, but sometimes it might miss a few moves—no big deal!",
                "message_size": 4,
                "rate": "1 packet per turn",
                "drops_allowed": True,
                "reward_per_packet": 2,
                "message_bonus": 16,
                "penalty_per_packet": None,
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
                "rate": "up to 1 packet per turn",
                "drops_allowed": False,
                "reward_per_packet": 0,
                "message_bonus": 80,
                "penalty_per_packet": None,
                "application_fee": 10,
                "bonus_condition": "Message received",
                "penalty_condition": None
            }
        ]
        
        # Criar cartas para cada cor
        for color in colors:
            for idx, template in enumerate(activity_templates):
                activity_id = f"activity_{template['type'].value}_{idx+1}_{color}"
                
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
                    message_bonus=template["message_bonus"],
                    penalty_per_packet=template["penalty_per_packet"],
                    application_fee=template["application_fee"],
                    bonus_condition=template["bonus_condition"],
                    penalty_condition=template["penalty_condition"]
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
                "rate": "up to 1 packet per turn",
                "drops_allowed": False,
                "reward_per_packet": None,
                "message_bonus": 5,
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
                "rate": "up to 1 packet per turn",
                "drops_allowed": False,
                "reward_per_packet": None,
                "message_bonus": 20,
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
                "rate": "up to 1 packet per turn",
                "drops_allowed": False,
                "reward_per_packet": None,
                "message_bonus": 80,
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
                "rate": "up to 1 packet per turn",
                "drops_allowed": False,
                "reward_per_packet": None,
                "message_bonus": 320,
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
                "rate": "up to 1 packet per turn",
                "drops_allowed": False,
                "reward_per_packet": None,
                "message_bonus": 20,
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
                "rate": "up to 1 packet per turn",
                "drops_allowed": False,
                "reward_per_packet": None,
                "message_bonus": 80,
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
                "rate": "up to 1 packet per turn",
                "drops_allowed": False,
                "reward_per_packet": None,
                "message_bonus": 320,
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
                "rate": "1 packet per turn",
                "drops_allowed": True,
                "reward_per_packet": 20,
                "message_bonus": 40,
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
                "rate": "1 packet per turn",
                "drops_allowed": True,
                "reward_per_packet": 80,
                "message_bonus": 160,
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
                "rate": "1 packet per turn",
                "drops_allowed": True,
                "reward_per_packet": 320,
                "message_bonus": 640,
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
                "rate": "1 packet per turn",
                "drops_allowed": True,
                "reward_per_packet": 2,
                "message_bonus": None,
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
                "rate": "1 packet per turn",
                "drops_allowed": True,
                "reward_per_packet": 20,
                "message_bonus": None,
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
                "rate": "1 packet per turn",
                "drops_allowed": True,
                "reward_per_packet": 80,
                "message_bonus": None,
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
                "rate": "1 packet per turn",
                "drops_allowed": True,
                "reward_per_packet": 320,
                "message_bonus": None,
                "time_limit_bonus": None,
                "challenge_quit_fee": 80,
                "time_limit": None,
                "time_to_receive": 4
            }
        ]
        
        # Criar cartas de desafio
        for idx, template in enumerate(challenge_templates):
            challenge_id = f"challenge_{template['type'].value}_{idx+1}"
            
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
                reward_per_packet=template["reward_per_packet"],
                message_bonus=template["message_bonus"],
                time_limit_bonus=template["time_limit_bonus"],
                challenge_quit_fee=template["challenge_quit_fee"],
                time_limit=template["time_limit"],
                time_to_receive=template["time_to_receive"]
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
        
        # Para Router Upgrade (cartas 1-7) e Router Downgrade (cartas 8-14)
        if action_type in [ActionType.ROUTER_UPGRADE, ActionType.ROUTER_DOWNGRADE]:
            if action_type == ActionType.ROUTER_UPGRADE:
                # Cartas 1-7: Router Upgrade
                if 1 <= action_num <= 3:
                    # Cartas 1-3: "Residential Router 1/2/3" (escolha do jogador)
                    return action_num  # 1, 2, 3
                elif 4 <= action_num <= 7:
                    # Cartas 4-7: "Residential Router 1" (jogadores específicos)
                    return 1
            elif action_type == ActionType.ROUTER_DOWNGRADE:
                # Cartas 8-14: Router Downgrade
                if 8 <= action_num <= 10:
                    # Cartas 8-10: "Residential Router 1/2/3" (escolha do jogador)
                    return action_num - 7  # 1, 2, 3
                elif 11 <= action_num <= 14:
                    # Cartas 11-14: "Residential Router 1" (jogadores específicos)
                    return 1
                    
        # Para Link Upgrade (cartas 15-21) e Link Downgrade (cartas 22-28)
        elif action_type in [ActionType.LINK_UPGRADE, ActionType.LINK_DOWNGRADE]:
            if action_type == ActionType.LINK_UPGRADE:
                # Cartas 15-21: Link Upgrade
                if 15 <= action_num <= 17:
                    # Cartas 15-17: "Link to Residential Router 1/2/3" (escolha do jogador)
                    return action_num - 14  # 1, 2, 3
                elif 18 <= action_num <= 21:
                    # Cartas 18-21: "Link to Residential Router 1" (jogadores específicos)
                    return 1
            elif action_type == ActionType.LINK_DOWNGRADE:
                # Cartas 22-28: Link Downgrade
                if 22 <= action_num <= 24:
                    # Cartas 22-24: "Link to Residential Router 1/2/3" (escolha do jogador)
                    return action_num - 21  # 1, 2, 3
                elif 25 <= action_num <= 28:
                    # Cartas 25-28: "Link to Residential Router 1" (jogadores específicos)
                    return 1
        
        # Para Add Router (cartas 29-33) e Remove Router (cartas 34-38)
        # Estas não têm router específico, retornar None
        return None
    
    def _create_action_cards(self):
        """Cria as cartas de ação"""
        # 38 cartas Action no total: 7 router upgrade, 7 router downgrade, 7 link upgrade, 7 link downgrade, 5 add router, 5 remove router
        action_templates = []
        
    def _create_action_cards(self):
        """Cria as cartas de ação"""
        # 38 cartas Action no total: 7 router upgrade, 7 router downgrade, 7 link upgrade, 7 link downgrade, 5 add router, 5 remove router
        action_templates = []
        
        # ROUTER UPGRADE - 7 cartas
        # Baseado nas imagens fornecidas: sequência específica de alvos
        router_upgrade_targets = [
            None,     # Carta 1: Jogadores cinzentos → Afeta o próprio jogador
            None,     # Carta 2: Jogadores cinzentos → Afeta o próprio jogador
            None,     # Carta 3: Jogadores cinzentos → Afeta o próprio jogador
            "yellow", # Carta 4: Jogador amarelo
            "green",  # Carta 5: Jogador verde
            "blue",   # Carta 6: Jogador azul
            "red"     # Carta 7: Jogador vermelho
        ]
        
        for i, target in enumerate(router_upgrade_targets):
            action_templates.append({
                "type": ActionType.ROUTER_UPGRADE,
                "title": "ROUTER UPGRADE",
                "description": "A bigger queue means more space for packets. Upgrade the queue on your Small Router to reduce drops, and you'll unlock your Medium Router for free!",
                "effect_description": "Move packets from the old queue to the new one, keeping them in the same order.",
                "target": target
            })
        
        # ROUTER DOWNGRADE - 7 cartas
        # Baseado nas imagens fornecidas: sequência específica de alvos
        router_downgrade_targets = [
            None,     # Carta 1: Jogadores cinzentos → Afeta o próprio jogador
            None,     # Carta 2: Jogadores cinzentos → Afeta o próprio jogador
            None,     # Carta 3: Jogadores cinzentos → Afeta o próprio jogador
            "yellow", # Carta 4: Jogador amarelo
            "green",  # Carta 5: Jogador verde
            "blue",   # Carta 6: Jogador azul
            "red"     # Carta 7: Jogador vermelho
        ]
        
        for i, target in enumerate(router_downgrade_targets):
            action_templates.append({
                "type": ActionType.ROUTER_DOWNGRADE,
                "title": "ROUTER DOWNGRADE", 
                "description": "Smaller queues mean less waiting. Reduce the Medium Router's queue size to speed up packet delivery and unlock your Small Router!",
                "effect_description": "Move packets from the old queue to the new one, keeping the same order, and discard any excess packets.",
                "target": target
            })
        
        # LINK UPGRADE - 7 cartas
        # Baseado nas imagens fornecidas: sequência específica de alvos
        link_upgrade_targets = [
            None,     # Carta 1: "Link to Residential Router 1" - Jogadores cinzentos (afeta o próprio jogador)
            None,     # Carta 2: "Link to Residential Router 2" - Jogadores cinzentos (afeta o próprio jogador)  
            None,     # Carta 3: "Link to Residential Router 3" - Jogadores cinzentos (afeta o próprio jogador)
            "yellow", # Carta 4: "Link to Residential Router 1" - Jogador amarelo específico
            "green",  # Carta 5: "Link to Residential Router 1" - Jogador verde específico
            "blue",   # Carta 6: "Link to Residential Router 1" - Jogador azul específico
            "red"     # Carta 7: "Link to Residential Router 1" - Jogador vermelho específico
        ]
        
        for i, target in enumerate(link_upgrade_targets):
            action_templates.append({
                "type": ActionType.LINK_UPGRADE,
                "title": "LINK UPGRADE",
                "description": "Short links have lower transmission times. Switch from a Long Link to a short one and enjoy faster communications!",
                "effect_description": "Move packets from the old link to the new one, keeping the same order, and discard any excess packets",
                "target": target
            })
        
        # LINK DOWNGRADE - 7 cartas
        # Baseado nas imagens fornecidas: sequência específica de alvos
        link_downgrade_targets = [
            None,     # Carta 1: "Link to Residential Router 1" - Jogadores cinzentos (afeta o próprio jogador)
            None,     # Carta 2: "Link to Residential Router 2" - Jogadores cinzentos (afeta o próprio jogador)
            None,     # Carta 3: "Link to Residential Router 3" - Jogadores cinzentos (afeta o próprio jogador)
            "yellow", # Carta 4: "Link to Residential Router 1" - Jogador amarelo específico
            "green",  # Carta 5: "Link to Residential Router 1" - Jogador verde específico
            "blue",   # Carta 6: "Link to Residential Router 1" - Jogador azul específico
            "red"     # Carta 7: "Link to Residential Router 1" - Jogador vermelho específico
        ]
        
        for i, target in enumerate(link_downgrade_targets):
            action_templates.append({
                "type": ActionType.LINK_DOWNGRADE,
                "title": "LINK DOWNGRADE",
                "description": "We moved far from central node and, you'll need a long link to stay connected—but get ready for longer delays.",
                "effect_description": "Move packets from the old queue to the new one, keeping them in the same order.",
                "target": target
            })
        
        # ADD ROUTER - 5 cartas  
        # Baseado nas imagens fornecidas: sequência específica de alvos
        add_router_targets = [
            None,     # Carta 1: Jogadores cinzentos (afeta o próprio jogador)
            "yellow", # Carta 2: Jogador amarelo específico
            "green",  # Carta 3: Jogador verde específico
            "blue",   # Carta 4: Jogador azul específico
            "red"     # Carta 5: Jogador vermelho específico
        ]
        
        for i, target in enumerate(add_router_targets):
            action_templates.append({
                "type": ActionType.ADD_ROUTER,
                "title": "ADD ROUTER",
                "description": "A new Residential User requested access to NetMaster. Head to the Store to see if you can grab a Small Router for free. Good luck!",
                "effect_description": "Add the router to the network board if there is a link to connect it. Otherwise, return it to the store.",
                "target": target
            })
        
        # REMOVE ROUTER - 5 cartas
        # Baseado nas imagens fornecidas: sequência específica de alvos
        remove_router_targets = [
            None,     # Carta 1: Jogadores cinzentos (afeta o próprio jogador)
            "yellow", # Carta 2: Jogador amarelo específico
            "green",  # Carta 3: Jogador verde específico
            "blue",   # Carta 4: Jogador azul específico
            "red"     # Carta 5: Jogador vermelho específico
        ]
        
        for i, target in enumerate(remove_router_targets):
            action_templates.append({
                "type": ActionType.REMOVE_ROUTER,
                "title": "REMOVE ROUTER",
                "description": "The Small Router is no longer needed! Return it to the store if possible!",
                "effect_description": "If there's more than one Small Router on the network board, remove the latest one added, along with all packets in its queue and the associated link",
                "target": target
            })
        
        # Criar cartas de ação
        for idx, template in enumerate(action_templates):
            action_id = f"action_{idx+1}"
            target = template["target"]
            action_type = template["type"]
            
            action_card = ActionCard(
                action_id=action_id,
                action_type=action_type,
                title=template["title"],
                description=template["description"],
                effect_description=template["effect_description"],
                target=target,
                router_id=self._extract_router_id(action_id, action_type)
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
            # Event_5: TRANSMISSION DELAY, Router 1, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False
            },
            # Event_6: TRANSMISSION DELAY, Router 1, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False
            },
            # Event_7: TRANSMISSION DELAY, Router 1, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False
            },
            # Event_8: TRANSMISSION DELAY, Router 1, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": True
            },
            # Event_9: TRANSMISSION DELAY, Router 1, 2 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": False
            },
            # Event_10: TRANSMISSION DELAY, Router 2, 2 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": False
            },
            # Event_11: TRANSMISSION DELAY, Router 3, 2 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": False
            },
            # Event_12: TRANSMISSION DELAY, Router 1, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False
            },
            # Event_13: TRANSMISSION DELAY, Router 1, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False
            },
            # Event_14: TRANSMISSION DELAY, Router 1, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False
            },
            # Event_15: TRANSMISSION DELAY, Router 1, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False
            },
            # Event_16: TRANSMISSION DELAY, Router 1, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": True
            },
            # Event_17: TRANSMISSION DELAY, Router 1, 4 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": False
            },
            # Event_18: TRANSMISSION DELAY, Router 2, 4 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": False
            },
            # Event_19: TRANSMISSION DELAY, Router 3, 4 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": None,
                "player_choice": False
            },
            # Event_20: TRANSMISSION DELAY, Router 1, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False
            },
            # Event_21: TRANSMISSION DELAY, Router 1, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False
            },
            # Event_22: TRANSMISSION DELAY, Router 1, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False
            },
            # Event_23: TRANSMISSION DELAY, Router 1, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False
            },
            # Event_24: TRANSMISSION DELAY, Router 1, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": True
            },
            # Event_25: TRANSMISSION DELAY, Router 1, ? TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": "variable",  # ? TURNS - será determinado por dado
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
            },
            # Event_26: TRANSMISSION DELAY, Router 2, ? TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": "variable",  # ? TURNS - será determinado por dado
                "router_id": 2,
                "target_player": None,
                "player_choice": False, 
            },
            # Event_27: TRANSMISSION DELAY, Router 3, ? TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": None,
                "player_choice": False,  
            },
            # Event_28: TRANSMISSION DELAY, Router 1, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,  
            },
            # Event_29: TRANSMISSION DELAY, Router 1, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,   
            },
            # Event_30: TRANSMISSION DELAY, Router 1, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "blue",
                "player_choice": True,    
            },
            # Event_31: TRANSMISSION DELAY, Router 1, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,   
            },
            # Event_32: TRANSMISSION DELAY, Router 1, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": True,   
            },
            # Event_33: LINK FAILURE, Router 1, 1 TURN, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_34: LINK FAILURE, Router 2, 1 TURN, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,            
            },
            # Event_35: LINK FAILURE, Router 3, 1 TURN, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_36: LINK FAILURE, Router 1, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_37: LINK FAILURE, Router 1, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_38: LINK FAILURE, Router 1, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_39: LINK FAILURE, Router 1, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_40: LINK FAILURE, Router 1, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_41: LINK FAILURE, Router 1, 2 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_42: LINK FAILURE, Router 2, 2 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,                  
            },
            # Event_43: LINK FAILURE, Router 3, 2 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_44: LINK FAILURE, Router 1, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_45: LINK FAILURE, Router 1, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_46: LINK FAILURE, Router 1, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_47: LINK FAILURE, Router 1, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_48: LINK FAILURE, Router 1, 2 TURNS, jogadores cinzentos COM ? (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_49: LINK FAILURE, Router 1, 4 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_50: LINK FAILURE, Router 2, 4 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_51: LINK FAILURE, Router 3, 4 TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_52: LINK FAILURE, Router 1, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_53: LINK FAILURE, Router 1, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_54: LINK FAILURE, Router 1, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_55: LINK FAILURE, Router 1, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_56: LINK FAILURE, Router 1, 4 TURNS, jogadores cinzentos COM ? (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_57: LINK FAILURE, Router 1, ? TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_58: LINK FAILURE, Router 2, ? TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_59: LINK FAILURE, Router 3, ? TURNS, jogadores cinzentos SEM ? (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_60: LINK FAILURE, Router 1, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_61: LINK FAILURE, Router 1, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_62: LINK FAILURE, Router 1, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_63: LINK FAILURE, Router 1, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_64: LINK FAILURE, Router 1, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.LINK_FAILURE,
            },
            # Event_65: TRAFFIC BURST, Router 1, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_66: TRAFFIC BURST, Router 2, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_67: TRAFFIC BURST, Router 3, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_68: TRAFFIC BURST, Router 1, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 1, 
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_69: TRAFFIC BURST, Router 1, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_70: TRAFFIC BURST, Router 1, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_71: TRAFFIC BURST, Router 1, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_72: TRAFFIC BURST, Router 1, 1 TURN, jogador jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_73: TRAFFIC BURST, Router 1, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_74: TRAFFIC BURST, Router 2, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_75: TRAFFIC BURST, Router 3, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_76: TRAFFIC BURST, Router 1, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_77: TRAFFIC BURST, Router 1, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_78: TRAFFIC BURST, Router 1, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_79: TRAFFIC BURST, Router 1, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_80: TRAFFIC BURST, Router 1, 2 TURNS, jogador jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_81: TRAFFIC BURST, Router 1, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_82: TRAFFIC BURST, Router 2, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_83: TRAFFIC BURST, Router 3, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 3, 
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_84: TRAFFIC BURST, Router 1, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_85: TRAFFIC BURST, Router 1, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_86: TRAFFIC BURST, Router 1, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_87: TRAFFIC BURST, Router 1, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_88: TRAFFIC BURST, Router 1, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_89: TRAFFIC BURST, Router 1, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_90: TRAFFIC BURST, Router 2, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_91: TRAFFIC BURST, Router 3, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 3, 
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_92: TRAFFIC BURST, Router 1, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_93: TRAFFIC BURST, Router 1, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_94: TRAFFIC BURST, Router 1, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_95: TRAFFIC BURST, Router 1, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_96: TRAFFIC BURST, Router 1, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.TRAFFIC_BURST,
            },
            # Event_97: QUEUE CONGESTION, Router 1, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_98: QUEUE CONGESTION, Router 2, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_99: QUEUE CONGESTION, Router 3, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 3, 
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_100: QUEUE CONGESTION, Router 1, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_101: QUEUE CONGESTION, Router 1, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_102: QUEUE CONGESTION, Router 1, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_103: QUEUE CONGESTION, Router 1, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_104: QUEUE CONGESTION, Router 1, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_105: QUEUE CONGESTION, Router 1, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_106: QUEUE CONGESTION, Router 2, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_107: QUEUE CONGESTION, Router 3, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_108: QUEUE CONGESTION, Router 1, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_109: QUEUE CONGESTION, Router 1, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_110: QUEUE CONGESTION, Router 1, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_111: QUEUE CONGESTION, Router 1, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_112: QUEUE CONGESTION, Router 1, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_113: QUEUE CONGESTION, Router 1, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_114: QUEUE CONGESTION, Router 2, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_115: QUEUE CONGESTION, Router 3, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_116: QUEUE CONGESTION, Router 1, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_117: QUEUE CONGESTION, Router 1, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_118: QUEUE CONGESTION, Router 1, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_119: QUEUE CONGESTION, Router 1, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_120: QUEUE CONGESTION, Router 1, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_CONGESTION,    
            },
            # Event_121: QUEUE CONGESTION, Router 1, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_122: QUEUE CONGESTION, Router 2, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_123: QUEUE CONGESTION, Router 3, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_124: QUEUE CONGESTION, Router 1, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_125: QUEUE CONGESTION, Router 1, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_126: QUEUE CONGESTION, Router 1, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_127: QUEUE CONGESTION, Router 1, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_128: QUEUE CONGESTION, Router 1, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_CONGESTION,
            },
            # Event_129: QUEUE FULL, Router 1, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
           # Event_130: QUEUE FULL, Router 2, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_131: QUEUE FULL, Router 3, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_132: QUEUE FULL, Router 1, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_133: QUEUE FULL, Router 1, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_134: QUEUE FULL, Router 1, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_135: QUEUE FULL, Router 1, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_136: QUEUE FULL, Router 1, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_137: QUEUE FULL, Router 1, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_138: QUEUE FULL, Router 2, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_139: QUEUE FULL, Router 3, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_140: QUEUE FULL, Router 1, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_141: QUEUE FULL, Router 1, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_142: QUEUE FULL, Router 1, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_143: QUEUE FULL, Router 1, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_144: QUEUE FULL, Router 1, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_145: QUEUE FULL, Router 1, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_146: QUEUE FULL, Router 2, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_147: QUEUE FULL, Router 3, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_148: QUEUE FULL, Router 1, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_149: QUEUE FULL, Router 1, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_150: QUEUE FULL, Router 1, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_151: QUEUE FULL, Router 1, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_152: QUEUE FULL, Router 1, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_153: QUEUE FULL, Router 1, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_154: QUEUE FULL, Router 2, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_155: QUEUE FULL, Router 3, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_156: QUEUE FULL, Router 1, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_157: QUEUE FULL, Router 1, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_158: QUEUE FULL, Router 1, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_159: QUEUE FULL, Router 1, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_160: QUEUE FULL, Router 1, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.QUEUE_FULL,
            },
            # Event_161: PACKET DROP, Router 1, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_162: PACKET DROP, Router 2, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_163: PACKET DROP, Router 3, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_164: PACKET DROP, Router 1, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_165: PACKET DROP, Router 1, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_166: PACKET DROP, Router 1, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_167: PACKET DROP, Router 1, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_168: PACKET DROP, Router 1, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_169: PACKET DROP, Router 1, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_170: PACKET DROP, Router 2, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_171: PACKET DROP, Router 3, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_172: PACKET DROP, Router 1, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_173: PACKET DROP, Router 1, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_174: PACKET DROP, Router 1, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_175: PACKET DROP, Router 1, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_176: PACKET DROP, Router 1, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_177: PACKET DROP, Router 1, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_178: PACKET DROP, Router 2, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_179: PACKET DROP, Router 3, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },  
            # Event_180: PACKET DROP, Router 1, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_181: PACKET DROP, Router 1, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_182: PACKET DROP, Router 1, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_183: PACKET DROP, Router 1, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_184: PACKET DROP, Router 1, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_185: PACKET DROP, Router 1, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_186: PACKET DROP, Router 2, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_187: PACKET DROP, Router 3, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_188: PACKET DROP, Router 1, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_189: PACKET DROP, Router 1, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_190: PACKET DROP, Router 1, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_191: PACKET DROP, Router 1, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_192: PACKET DROP, Router 1, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.PACKET_DROP,
            },
            # Event_193: EMPTY QUEUE, Router 1, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_194: EMPTY QUEUE, Router 2, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_195: EMPTY QUEUE, Router 3, 1 TURN, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 1,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_196: EMPTY QUEUE, Router 1, 1 TURN, jogador amarelo
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_197: EMPTY QUEUE, Router 1, 1 TURN, jogador verde
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_198: EMPTY QUEUE, Router 1, 1 TURN, jogador azul
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_199: EMPTY QUEUE, Router 1, 1 TURN, jogador vermelho
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_200: EMPTY QUEUE, Router 1, 1 TURN, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 1,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_201: EMPTY QUEUE, Router 1, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_202: EMPTY QUEUE, Router 2, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador) 
            {
                "duration_turns": 2,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },  
            # Event_203: EMPTY QUEUE, Router 3, 2 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 2,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_204: EMPTY QUEUE, Router 1, 2 TURNS, jogador amarelo
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_205: EMPTY QUEUE, Router 1, 2 TURNS, jogador verde
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_206: EMPTY QUEUE, Router 1, 2 TURNS, jogador azul
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_207: EMPTY QUEUE, Router 1, 2 TURNS, jogador vermelho
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_208: EMPTY QUEUE, Router 1, 2 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 2,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_209: EMPTY QUEUE, Router 1, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_210: EMPTY QUEUE, Router 2, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_211: EMPTY QUEUE, Router 3, 4 TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": 4,
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_212: EMPTY QUEUE, Router 1, 4 TURNS, jogador amarelo
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
            },
            # Event_213: EMPTY QUEUE, Router 1, 4 TURNS, jogador verde
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },  
            # Event_214: EMPTY QUEUE, Router 1, 4 TURNS, jogador azul
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_215: EMPTY QUEUE, Router 1, 4 TURNS, jogador vermelho
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_216: EMPTY QUEUE, Router 1, 4 TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": 4,
                "router_id": 1,
                "target_player": None,
                "player_choice": True,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_217: EMPTY QUEUE, Router 1, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_218: EMPTY QUEUE, Router 2, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 2,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_219: EMPTY QUEUE, Router 3, ? TURNS, jogadores cinzentos SEM interrogação (próprio jogador)
            {
                "duration_turns": "variable",
                "router_id": 3,
                "target_player": None,
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_220: EMPTY QUEUE, Router 1, ? TURNS, jogador amarelo
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "yellow",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_221: EMPTY QUEUE, Router 1, ? TURNS, jogador verde
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "green",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_222: EMPTY QUEUE, Router 1, ? TURNS, jogador azul
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "blue",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_223: EMPTY QUEUE, Router 1, ? TURNS, jogador vermelho
            {
                "duration_turns": "variable",
                "router_id": 1,
                "target_player": "red",
                "player_choice": False,
                "event_type": EventType.EMPTY_QUEUE,
            },
            # Event_224: EMPTY QUEUE, Router 1, ? TURNS, jogadores cinzentos COM interrogação (escolha do jogador)
            {
                "duration_turns": "variable",
                "router_id": 1,
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
            
            # Determinar o tipo de evento (padrão é TRANSMISSION_DELAY para compatibilidade)
            event_type_str = template.get("event_type", "TRANSMISSION_DELAY")
            event_type = EventType.TRANSMISSION_DELAY if event_type_str == "TRANSMISSION_DELAY" else EventType.LINK_FAILURE
            
            # Determinar título, descrição e efeito baseado no tipo de evento
            if event_type == EventType.LINK_FAILURE:
                title = "LINK FAILURE"
                description = "A network connection failed, disrupting communication. All in-transit packets are lost!"
                if template["duration_turns"] == "variable":
                    if player_choice:
                        effect_text = "Select a player to run the event. Roll the dice to get the number of turns N. Remove all packets from the link. No packets will be added to the link during the event."
                    else:
                        effect_text = "Roll the dice to get the number of turns N. Remove all packets from the link. No packets will be added to the link during the event."
                else:
                    if player_choice:
                        effect_text = "Remove all packets from the link. No packets will be added to the link during the event. Select a player to run the event."
                    else:
                        effect_text = "Remove all packets from the link. No packets will be added to the link during the event."
            elif event_type == EventType.TRAFFIC_BURST:
                title = "TRAFFIC BURST"
                description = "Some users are generating a burst of traffic, and the queue is growing fast. New transmissions are postponed!"
                if template["duration_turns"] == "variable":
                    # Cartas com duração variável (? TURNS)
                    if player_choice:
                        effect_text = "Select a player to run the event. Roll the dice to get the number of turns N. At each turn of the event, add 1 dummy packet to the queue and keep transmitting 1 packet per turn."
                    else:
                        effect_text = "Roll the dice to get the number of turns N. At each turn of the event, add 1 dummy packet to the queue and keep transmitting 1 packet per turn."
                else:
                    # Cartas com duração fixa
                    if player_choice:
                        effect_text = "Select a player to run the event. At each turn of the event, add 1 dummy packet to the queue and keep transmitting 1 packet per turn."
                    else:
                        effect_text = "At each turn of the event, add 1 dummy packet to the queue and keep transmitting 1 packet per turn."
            elif event_type == EventType.QUEUE_CONGESTION:
                title = "QUEUE CONGESTION"
                description = "Too many users are attempting to transmit video! The queue is growing too fast, becoming congested."
                if template["duration_turns"] == "variable":
                    # Cartas com duração variável (? TURNS)
                    if player_choice:
                        effect_text = "Select a player to run the event. Roll the dice to get the number of turns N. At each turn, add 2 dummy packets to the queue and keep transmitting 1 packet per turn."
                    else:
                        effect_text = "Roll the dice to get the number of turns N. At each turn, add 2 dummy packets to the queue and keep transmitting 1 packet per turn."
                else:
                    # Cartas com duração fixa
                    if player_choice:
                        effect_text = "Select a player to run the event. At each turn, add 2 dummy packets to the queue and keep transmitting 1 packet per turn."
                    else:
                        effect_text = "At each turn, add 2 dummy packets to the queue and keep transmitting 1 packet per turn."
            elif event_type == EventType.QUEUE_FULL:
                title = "QUEUE FULL"
                description = "The high volume of incoming packets has overwhelmed the network devices, and the queue is full!"
                if template["duration_turns"] == "variable":
                    # Cartas com duração variável (? TURNS)
                    if player_choice:
                        effect_text = "Select a player to run the event. Roll the dice to get the number of turns N. At each event turn, fill the queue with dummy packets and transmit one packet per turn."
                    else:
                        effect_text = "Roll the dice to get the number of turns N. At each event turn, fill the queue with dummy packets and transmit one packet per turn."
                else:
                    # Cartas com duração fixa
                    if player_choice:
                        effect_text = "Select a player to run the event. At each event turn, fill the queue with dummy packets and transmit one packet per turn."
                    else:
                        effect_text = "At each event turn, fill the queue with dummy packets and transmit one packet per turn."
            elif event_type == EventType.PACKET_DROP:
                title = "PACKET DROP"
                description = "Due to several errors, packets have been dropped in the queue, disrupting communication."
                if template["duration_turns"] == "variable":
                    # Cartas com duração variável (? TURNS)
                    if player_choice:
                        effect_text = "Select a player to run the event. Roll the dice to get the number of turns N. At each turn of the event, remove 1 packet from the queue and do not transmit any packet."
                    else:
                        effect_text = "Roll the dice to get the number of turns N. At each turn of the event, remove 1 packet from the queue and do not transmit any packet."
                else:
                    # Cartas com duração fixa
                    if player_choice:
                        effect_text = "Select a player to run the event. At each turn of the event, remove 1 packet from the queue and do not transmit any packet."
                    else:
                        effect_text = "At each turn of the event, remove 1 packet from the queue and do not transmit any packet."
            elif event_type == EventType.EMPTY_QUEUE:
                title = "EMPTY QUEUE"
                description = "Due to severe errors, packets have been dropped in the queue, severely disrupting the communication."
                if template["duration_turns"] == "variable":
                    # Cartas com duração variável (? TURNS)
                    if player_choice:
                        effect_text = "Select a player to run the event. Roll the dice to get the number of turns N. At each turn, remove all packets from the queue."
                    else:
                        effect_text = "Roll the dice to get the number of turns N. At each turn, remove all packets from the queue."
                else:
                    # Cartas com duração fixa
                    if player_choice:
                        effect_text = "Select a player to run the event. At each turn, remove all packets from the queue."
                    else:
                        effect_text = "At each turn, remove all packets from the queue."
                
                
            else:  # TRANSMISSION_DELAY
                title = "TRANSMISSION DELAY"
                description = "Currently, the traffic is being transmitted through a low-capacity link, which is causing a significant delay in the delivery of the traffic."
                # Para TRANSMISSION DELAY, usar a lógica existente baseada na regra dos jogadores cinzentos
                if template["duration_turns"] == "variable":
                    # Cartas com duração variável (? TURNS)
                    if player_choice:
                        effect_text = "Select a player to run the event. Roll the dice to get the number of turns N. At each turn, do not add packets or move the packets in the link."
                    else:
                        effect_text = "Roll the dice to get the number of turns N. At each turn, do not add packets or move the packets in the link."
                else:
                    # Cartas com duração fixa
                    if player_choice:
                        effect_text = "Select a player to run the event. At each turn, do not add packets or move the packets in the link."
                    else:
                        effect_text = "At each turn, do not add packets or move the packets in the link."
                        
                        
                        
                         
            
            # Tratar duração variável
            duration = template["duration_turns"]
            if duration == "variable":
                duration = 0  # Será determinado por dado no jogo
            
            # Determinar se deve usar target_link ou target_queue baseado no número do evento
            event_number = int(event_id.split('_')[1])
            
            # Event_1 a Event_64: usar target_link
            # Event_65 a Event_224: usar target_queue
            if 1 <= event_number <= 64:
                target_link = f"Link to Residential Router {router_id}"
                target_queue = None
            elif 65 <= event_number <= 224:
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
    print(f"- Cartas de Serviços: {stats['total_services']}")
    print(f"- Cartas de Atividades: {stats['total_activities']}")
    print(f"- Cartas de Desafios: {stats['total_challenges']}")
    print(f"- Cartas de Ações: {stats['total_actions']}")
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
    
    # Serviço exemplo
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
    
    # Ação exemplo
    action = db.get_action("action_1")
    if action:
        print(f"- {action}")
    
    print(f"\nCores disponíveis: {', '.join(db.get_available_colors())}")

if __name__ == "__main__":
    main()
