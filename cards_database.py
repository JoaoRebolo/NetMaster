#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base de Dados de Cartas NetMaster
Sistema de armazenamento e gestão de cartas Users, Equipments e Contracts
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from enum import Enum

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
class ContractCard:
    """Carta de contrato"""
    contract_id: str
    color: str
    bandwidth_provided: int  # Mbps
    data_allowance: int  # GB
    cost: int
    duration: int  # meses
    penalty: int

    def __str__(self):
        return f"ContractCard(id={self.contract_id}, color={self.color}, bandwidth={self.bandwidth_provided}Mbps)"

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

class UserDatabase:
    """
    Base de dados principal de cartas NetMaster
    """
    
    def __init__(self):
        self.users: Dict[str, UserCard] = {}
        self.equipments: Dict[str, EquipmentCard] = {}
        self.contracts: Dict[str, ContractCard] = {}
        self.services: Dict[str, ServiceCard] = {}
        self.activities: Dict[str, ActivityCard] = {}
        self._initialize_database()
    
    def _initialize_database(self):
        """Inicializa a base de dados com cartas padrão"""
        self._create_user_cards()
        self._create_equipment_cards()
        self._create_contract_cards()
        self._create_service_cards()
        self._create_activity_cards()
    
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
    
    def _create_contract_cards(self):
        """Cria as cartas de contratos"""
        colors = ["red", "green", "blue", "yellow"]
        
        for i in range(1, 8):  # Contract_1 a Contract_7
            for color in colors:
                contract_id = f"contract_{i}_{color}"
                
                # Definir características baseadas no número
                bandwidth = 25 * i
                data_allowance = 100 * i
                cost = 50 + (i * 25)
                duration = 6 + i
                penalty = cost // 2
                
                contract_card = ContractCard(
                    contract_id=contract_id,
                    color=color,
                    bandwidth_provided=bandwidth,
                    data_allowance=data_allowance,
                    cost=cost,
                    duration=duration,
                    penalty=penalty
                )
                
                self.contracts[contract_id] = contract_card
    
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
    
    # Métodos de acesso aos dados
    def get_user(self, user_id: str) -> Optional[UserCard]:
        """Obtém carta de utilizador por ID"""
        return self.users.get(user_id)
    
    def get_equipment(self, equipment_id: str) -> Optional[EquipmentCard]:
        """Obtém carta de equipamento por ID"""
        return self.equipments.get(equipment_id)
    
    def get_contract(self, contract_id: str) -> Optional[ContractCard]:
        """Obtém carta de contrato por ID"""
        return self.contracts.get(contract_id)
    
    def get_service(self, service_id: str) -> Optional[ServiceCard]:
        """Obtém carta de serviço por ID"""
        return self.services.get(service_id)
    
    def get_activity(self, activity_id: str) -> Optional[ActivityCard]:
        """Obtém carta de atividade por ID"""
        return self.activities.get(activity_id)
    
    def get_users_by_color(self, color: str) -> List[UserCard]:
        """Obtém todas as cartas de utilizadores de uma cor"""
        return [card for card in self.users.values() if card.color == color]
    
    def get_equipments_by_color(self, color: str) -> List[EquipmentCard]:
        """Obtém todas as cartas de equipamentos de uma cor"""
        return [card for card in self.equipments.values() if card.color == color]
    
    def get_contracts_by_color(self, color: str) -> List[ContractCard]:
        """Obtém todas as cartas de contratos de uma cor"""
        return [card for card in self.contracts.values() if card.color == color]
    
    def get_services_by_color(self, color: str) -> List[ServiceCard]:
        """Obtém todas as cartas de serviços de uma cor"""
        return [card for card in self.services.values() if card.color == color]
    
    def get_activities_by_color(self, color: str) -> List[ActivityCard]:
        """Obtém todas as cartas de atividades de uma cor"""
        return [card for card in self.activities.values() if card.color == color]
    
    def get_all_users(self) -> List[UserCard]:
        """Obtém todas as cartas de utilizadores"""
        return list(self.users.values())
    
    def get_all_equipments(self) -> List[EquipmentCard]:
        """Obtém todas as cartas de equipamentos"""
        return list(self.equipments.values())
    
    def get_all_contracts(self) -> List[ContractCard]:
        """Obtém todas as cartas de contratos"""
        return list(self.contracts.values())
    
    def get_all_services(self) -> List[ServiceCard]:
        """Obtém todas as cartas de serviços"""
        return list(self.services.values())
    
    def get_all_activities(self) -> List[ActivityCard]:
        """Obtém todas as cartas de atividades"""
        return list(self.activities.values())
    
    def get_user_ids(self) -> List[str]:
        """Obtém todos os IDs de utilizadores"""
        return list(self.users.keys())
    
    def get_equipment_ids(self) -> List[str]:
        """Obtém todos os IDs de equipamentos"""
        return list(self.equipments.keys())
    
    def get_contract_ids(self) -> List[str]:
        """Obtém todos os IDs de contratos"""
        return list(self.contracts.keys())
    
    def get_service_ids(self) -> List[str]:
        """Obtém todos os IDs de serviços"""
        return list(self.services.keys())
    
    def get_activity_ids(self) -> List[str]:
        """Obtém todos os IDs de atividades"""
        return list(self.activities.keys())
    
    def get_available_colors(self) -> Set[str]:
        """Obtém todas as cores disponíveis"""
        return {"red", "green", "blue", "yellow"}
    
    def get_statistics(self) -> Dict[str, int]:
        """Obtém estatísticas da base de dados"""
        return {
            "total_users": len(self.users),
            "total_equipments": len(self.equipments),
            "total_contracts": len(self.contracts),
            "total_services": len(self.services),
            "total_activities": len(self.activities),
            "total_cards": len(self.users) + len(self.equipments) + len(self.contracts) + len(self.services) + len(self.activities)
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
    print(f"- Cartas de Contratos: {stats['total_contracts']}")
    print(f"- Cartas de Serviços: {stats['total_services']}")
    print(f"- Cartas de Atividades: {stats['total_activities']}")
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
    
    # Contrato exemplo
    contract = db.get_contract("contract_1_red")
    if contract:
        print(f"- {contract}")
    
    # Serviço exemplo
    service = db.get_service("service_bandwidth_1_red")
    if service:
        print(f"- {service}")
    
    # Atividade exemplo
    activity = db.get_activity("activity_home_surveillance_1_red")
    if activity:
        print(f"- {activity}")
    
    print(f"\nCores disponíveis: {', '.join(db.get_available_colors())}")

if __name__ == "__main__":
    main()
