#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Integração de Dados de Cartas NetMaster com Arquivos Físicos
Conecta os dados das cartas com os arquivos de imagem reais do Raspberry Pi
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum

# Importar as classes da base de dados existente
from cards_database import (
    UserCard, EquipmentCard, ServiceCard, ActivityCard, ChallengeCard, ActionCard, EventCard,
    UserType, EquipmentType, ServiceType, ActivityType, ChallengeType, ActionType, EventType,
    UserDatabase
)

# Importar utilitários para detecção de Raspberry Pi
from raspberry_pi_utils import get_universal_paths

class CardFileManager:
    """
    Gestor de arquivos de cartas - conecta dados com arquivos físicos
    """
    
    def __init__(self, base_dir="."):
        # Usar os utilitários universais para detecção automática
        self.universal_paths = get_universal_paths()
        self.base_dir = self.universal_paths['base_dir']
        self.environment = self.universal_paths['environment']
        print(f"Ambiente detectado: {self.environment}")
        print(f"Caminho base: {self.base_dir}")
        self.card_mappings = self._build_card_mappings()
    
    def _detect_environment(self):
        """
        Método mantido para compatibilidade, mas usa os utilitários universais
        """
        # Este método agora é redundante pois a detecção é feita no __init__
        pass
    
    def _get_users_path(self, color):
        """
        Retorna o caminho para cartas de users baseado no ambiente
        """
        if self.environment == "raspberry_pi":
            return os.path.join(self.base_dir, "img", "cartas", "users", "Residential-level", color)
        else:
            return os.path.join(self.base_dir, "Users", "Residential-level", color)
    
    def _get_equipments_path(self, color):
        """
        Retorna o caminho para cartas de equipments baseado no ambiente
        """
        if self.environment == "raspberry_pi":
            return os.path.join(self.base_dir, "img", "cartas", "equipments", "Residential-level", color)
        else:
            return os.path.join(self.base_dir, "Equipments", "Residential-level", color)
    
    def get_services_path(self, color):
        """
        Retorna o caminho para cartas Services baseado no ambiente
        """
        if self.environment == "raspberry_pi":
            return os.path.join(self.base_dir, "img", "cartas", "services", "Residential-level", color)
        else:
            return os.path.join(self.base_dir, "Services", "Residential-level", color)
    
    def _get_activities_path(self, color):
        """
        Retorna o caminho para cartas de activities baseado no ambiente
        """
        if self.environment == "raspberry_pi":
            return os.path.join(self.base_dir, "img", "cartas", "activities", "Residential-level", color)
        else:
            return os.path.join(self.base_dir, "Activities", "Residential-level", color)
    
    def _get_challenges_path(self):
        """
        Retorna o caminho para cartas de challenges baseado no ambiente
        """
        if self.environment == "raspberry_pi":
            return os.path.join(self.base_dir, "img", "cartas", "challenges", "Residential-level")
        else:
            return os.path.join(self.base_dir, "Challenges", "Residential-level")
    
    def _get_actions_path(self):
        """
        Retorna o caminho para cartas de actions baseado no ambiente
        """
        if self.environment == "raspberry_pi":
            return os.path.join(self.base_dir, "img", "cartas", "actions", "Residential-level")
        else:
            return os.path.join(self.base_dir, "Actions", "Residential-level")
    
    def _get_events_path(self):
        """
        Retorna o caminho para cartas de events baseado no ambiente
        """
        if self.environment == "raspberry_pi":
            return os.path.join(self.base_dir, "img", "cartas", "events", "Residential-level")
        else:
            return os.path.join(self.base_dir, "Events", "Residential-level")
    
    def _build_card_mappings(self):
        """
        Constrói mapeamento entre IDs de cartas e arquivos físicos
        """
        mappings = {
            "users": {},
            "equipments": {},
            "services": {},
            "actions": {},
            "events": {},
            "challenges": {},
            "activities": {},
            "contracts": {}
        }
        
        # Mapeamento para cartas de Users (todas as cores)
        # User_1.png -> UserCard com user_id="1_red", "1_blue", etc.
        colors = ["Blue", "Red", "Green", "Yellow"]
        
        for color in colors:
            color_lower = color.lower()
            users_dir = self._get_users_path(color)
            print(f"Procurando cartas de users {color_lower} em: {users_dir}")
            
            if os.path.exists(users_dir):
                files_found = os.listdir(users_dir)
                print(f"Arquivos {color_lower} encontrados: {files_found}")
                
                for filename in files_found:
                    if filename.startswith("User_") and filename.endswith(".png"):
                        # Extrair número do arquivo (User_1.png -> 1)
                        try:
                            card_number = int(filename.replace("User_", "").replace(".png", ""))
                            full_path = os.path.join(users_dir, filename)
                            # ID da carta inclui a cor: "1_red", "2_blue", etc.
                            card_id = f"{card_number}_{color_lower}"
                            mappings["users"][card_id] = {
                                "path": full_path,
                                "color": color_lower,
                                "number": card_number,
                                "filename": filename
                            }
                            print(f"Mapeado: User ID {card_id} -> {filename} ({color})")
                        except ValueError:
                            print(f"Não foi possível extrair ID de: {filename}")
                            continue
        
        # Mapeamento para cartas de Equipments (todas as cores)
        # Equipment_1.png -> EquipmentCard com equipment_id="small_router_1_red", etc.
        for color in colors:
            color_lower = color.lower()
            equipments_dir = self._get_equipments_path(color)
            print(f"Procurando cartas de equipments {color_lower} em: {equipments_dir}")
            
            if os.path.exists(equipments_dir):
                files_found = os.listdir(equipments_dir)
                print(f"Arquivos de equipment {color_lower} encontrados: {files_found}")
                
                for filename in files_found:
                    if filename.startswith("Equipment_") and filename.endswith(".png"):
                        # Extrair número do arquivo (Equipment_1.png -> 1)
                        try:
                            card_number = int(filename.replace("Equipment_", "").replace(".png", ""))
                            full_path = os.path.join(equipments_dir, filename)
                            
                            # Mapear números de cartas para equipamentos específicos
                            # Com base nas 12 cartas fornecidas pelo usuário
                            equipment_mapping = {
                                1: "small_router_1", 2: "small_router_2", 3: "small_router_3",
                                4: "medium_router_1", 5: "medium_router_2", 6: "medium_router_3",
                                7: "short_link_1", 8: "short_link_2", 9: "short_link_3",
                                10: "long_link_1", 11: "long_link_2", 12: "long_link_3"
                            }
                            
                            if card_number in equipment_mapping:
                                equipment_type = equipment_mapping[card_number]
                                card_id = f"{equipment_type}_{color_lower}"
                                mappings["equipments"][card_id] = {
                                    "path": full_path,
                                    "color": color_lower,
                                    "number": card_number,
                                    "filename": filename,
                                    "equipment_type": equipment_type
                                }
                                print(f"Mapeado: Equipment ID {card_id} -> {filename} ({color})")
                            else:
                                print(f"Número de equipment não reconhecido: {card_number}")
                        except ValueError:
                            print(f"Não foi possível extrair ID de: {filename}")
                            continue
            else:
                print(f"Diretório de equipments não encontrado: {equipments_dir}")
        
        # Mapeamento para cartas de Services (todas as cores)
        # Service_1.png -> ServiceCard
        for color in colors:
            color_lower = color.lower()
            services_dir = self.get_services_path(color)
            print(f"Procurando cartas de services {color_lower} em: {services_dir}")
            
            if os.path.exists(services_dir):
                files_found = os.listdir(services_dir)
                print(f"Arquivos de services {color_lower} encontrados: {files_found}")
                
                for filename in files_found:
                    if filename.startswith("Service_") and filename.endswith(".png"):
                        try:
                            # Extrair número do arquivo (Service_1.png -> 1)
                            card_number = int(filename.replace("Service_", "").replace(".png", ""))
                            full_path = os.path.join(services_dir, filename)
                            
                            # Mapear números de cartas para os novos IDs simples
                            # Service_1.png -> Service_1, Service_2.png -> Service_2, etc.
                            service_id = f"Service_{card_number}"
                            
                            # Verificar se este service_id existe na base de dados
                            if card_number >= 1 and card_number <= 28:  # Temos 28 services no total
                                mappings["services"][service_id] = {
                                    "path": full_path,
                                    "color": color_lower,
                                    "number": card_number,
                                    "filename": filename,
                                    "service_id": service_id
                                }
                                print(f"Mapeado: Service ID {service_id} -> {filename} ({color})")
                            else:
                                print(f"Número de service fora do range (1-28): {card_number}")
                        except ValueError:
                            print(f"Não foi possível extrair ID de: {filename}")
                            continue
            else:
                print(f"Diretório de services não encontrado: {services_dir}")
        
        # Mapeamento para cartas de Activities (todas as cores)
        # Activity_1.png -> ActivityCard
        for color in colors:
            color_lower = color.lower()
            activities_dir = self._get_activities_path(color)
            print(f"Procurando cartas de activities {color_lower} em: {activities_dir}")
            
            if os.path.exists(activities_dir):
                files_found = os.listdir(activities_dir)
                print(f"Arquivos de activities {color_lower} encontrados: {files_found}")
                
                for filename in files_found:
                    if filename.startswith("Activity_") and filename.endswith(".png"):
                        try:
                            card_number = int(filename.replace("Activity_", "").replace(".png", ""))
                            full_path = os.path.join(activities_dir, filename)
                            card_id = f"activity_{card_number}_{color_lower}"
                            mappings["activities"][card_id] = {
                                "path": full_path,
                                "color": color_lower,
                                "number": card_number,
                                "filename": filename
                            }
                            print(f"Mapeado: Activity ID {card_id} -> {filename} ({color})")
                        except ValueError:
                            print(f"Não foi possível extrair ID de: {filename}")
                            continue
            else:
                print(f"Diretório de activities não encontrado: {activities_dir}")
        
        # Mapeamento para cartas de Challenges
        # Challenge_1.png -> ChallengeCard
        challenges_dir = self._get_challenges_path()
        print(f"Procurando cartas de challenges em: {challenges_dir}")
        
        if os.path.exists(challenges_dir):
            files_found = os.listdir(challenges_dir)
            print(f"Arquivos de challenges encontrados: {files_found}")
            
            for filename in files_found:
                if filename.startswith("Challenge_") and filename.endswith(".png"):
                    try:
                        card_number = int(filename.replace("Challenge_", "").replace(".png", ""))
                        full_path = os.path.join(challenges_dir, filename)
                        card_id = f"challenge_{card_number}"
                        mappings["challenges"][card_id] = {
                            "path": full_path,
                            "number": card_number,
                            "filename": filename
                        }
                        print(f"Mapeado: Challenge ID {card_id} -> {filename}")
                    except ValueError:
                        print(f"Não foi possível extrair ID de: {filename}")
                        continue
        else:
            print(f"Diretório de challenges não encontrado: {challenges_dir}")
        
        # Mapeamento para cartas de Actions
        # Action_1.png -> ActionCard
        actions_dir = self._get_actions_path()
        print(f"Procurando cartas de actions em: {actions_dir}")
        
        if os.path.exists(actions_dir):
            files_found = os.listdir(actions_dir)
            print(f"Arquivos de actions encontrados: {files_found}")
            
            for filename in files_found:
                if filename.startswith("Action_") and filename.endswith(".png"):
                    try:
                        card_number = int(filename.replace("Action_", "").replace(".png", ""))
                        full_path = os.path.join(actions_dir, filename)
                        card_id = f"action_{card_number}"
                        mappings["actions"][card_id] = {
                            "path": full_path,
                            "number": card_number,
                            "filename": filename
                        }
                        print(f"Mapeado: Action ID {card_id} -> {filename}")
                    except ValueError:
                        print(f"Não foi possível extrair ID de: {filename}")
                        continue
        else:
            print(f"Diretório de actions não encontrado: {actions_dir}")
        
        # Mapeamento para cartas de Events
        # Event_1.png -> EventCard
        events_dir = self._get_events_path()
        print(f"Procurando cartas de events em: {events_dir}")
        
        if os.path.exists(events_dir):
            files_found = os.listdir(events_dir)
            print(f"Arquivos de events encontrados: {files_found}")
            
            for filename in files_found:
                if filename.startswith("Event_") and filename.endswith(".png"):
                    try:
                        card_number = int(filename.replace("Event_", "").replace(".png", ""))
                        full_path = os.path.join(events_dir, filename)
                        card_id = f"event_{card_number}"
                        mappings["events"][card_id] = {
                            "path": full_path,
                            "number": card_number,
                            "filename": filename
                        }
                        print(f"Mapeado: Event ID {card_id} -> {filename}")
                    except ValueError:
                        print(f"Não foi possível extrair ID de: {filename}")
                        continue
        else:
            print(f"Diretório de events não encontrado: {events_dir}")
        
        print(f"Total de cartas mapeadas: {len(mappings['users'])} users + {len(mappings['equipments'])} equipments + {len(mappings['services'])} services + {len(mappings['activities'])} activities + {len(mappings['challenges'])} challenges + {len(mappings['actions'])} actions + {len(mappings['events'])} events")
        return mappings
    
    def get_card_file_path(self, card_type: str, card_id: str) -> Optional[str]:
        """
        Obtém o caminho do arquivo para uma carta específica
        """
        card_info = self.card_mappings.get(card_type, {}).get(card_id)
        if card_info and isinstance(card_info, dict):
            return card_info.get("path")
        return card_info  # Para compatibilidade com formato antigo
    
    def get_available_cards(self, card_type: str) -> List[str]:
        """
        Lista IDs de cartas disponíveis para um tipo específico
        """
        return list(self.card_mappings.get(card_type, {}).keys())
    
    def card_exists(self, card_type: str, card_id: str) -> bool:
        """
        Verifica se existe arquivo para uma carta específica
        """
        file_path = self.get_card_file_path(card_type, card_id)
        return file_path is not None and os.path.exists(file_path)

class IntegratedCardDatabase(UserDatabase):
    """
    Base de dados integrada que combina dados das cartas com arquivos físicos
    """
    
    def __init__(self, base_dir="."):
        super().__init__()
        self.file_manager = CardFileManager(base_dir)
        self._sync_with_physical_files()
    
    def _sync_with_physical_files(self):
        """
        Sincroniza a base de dados com os arquivos físicos disponíveis
        """
        print("\nSincronizando base de dados com arquivos físicos...")
        
        # Verificar quais cartas têm arquivos correspondentes
        available_user_files = self.file_manager.get_available_cards("users")
        available_equipment_files = self.file_manager.get_available_cards("equipments")
        available_service_files = self.file_manager.get_available_cards("services")
        available_activity_files = self.file_manager.get_available_cards("activities")
        available_challenge_files = self.file_manager.get_available_cards("challenges")
        available_action_files = self.file_manager.get_available_cards("actions")
        available_event_files = self.file_manager.get_available_cards("events")
        
        print(f"Arquivos encontrados:")
        print(f"  Users: {len(available_user_files)}")
        print(f"  Equipments: {len(available_equipment_files)}")
        print(f"  Services: {len(available_service_files)}")
        print(f"  Activities: {len(available_activity_files)}")
        print(f"  Challenges: {len(available_challenge_files)}")
        print(f"  Actions: {len(available_action_files)}")
        print(f"  Events: {len(available_event_files)}")
        
        # Verificar cartas na base de dados vs arquivos disponíveis
        users_in_db = list(self.users.keys())
        equipments_in_db = list(self.equipments.keys())
        services_in_db = list(self.services.keys())
        activities_in_db = list(self.activities.keys())
        challenges_in_db = list(self.challenges.keys())
        actions_in_db = list(self.actions.keys())
        events_in_db = list(self.events.keys())
        
        print(f"\nCartas na base de dados:")
        print(f"  Users: {len(users_in_db)}")
        print(f"  Equipments: {len(equipments_in_db)}")
        print(f"  Services: {len(services_in_db)}")
        print(f"  Activities: {len(activities_in_db)}")
        print(f"  Challenges: {len(challenges_in_db)}")
        print(f"  Actions: {len(actions_in_db)}")
        print(f"  Events: {len(events_in_db)}")
        
        # Contar quantas cartas têm arquivos correspondentes
        valid_counts = {}
        for card_type, db_cards in [
            ("users", users_in_db),
            ("equipments", equipments_in_db),
            ("services", services_in_db),
            ("activities", activities_in_db),
            ("challenges", challenges_in_db),
            ("actions", actions_in_db),
            ("events", events_in_db)
        ]:
            valid_count = 0
            for card_id in db_cards:
                if self.file_manager.card_exists(card_type, card_id):
                    valid_count += 1
                    print(f"  {card_type.capitalize()} ID {card_id}: arquivo encontrado")
                else:
                    print(f"  {card_type.capitalize()} ID {card_id}: arquivo NÃO encontrado")
            valid_counts[card_type] = valid_count
        
        print(f"\nResultado final:")
        print(f"  Users: {valid_counts['users']}/{len(users_in_db)}")
        print(f"  Equipments: {valid_counts['equipments']}/{len(equipments_in_db)}")
        print(f"  Services: {valid_counts['services']}/{len(services_in_db)}")
        print(f"  Activities: {valid_counts['activities']}/{len(activities_in_db)}")
        print(f"  Challenges: {valid_counts['challenges']}/{len(challenges_in_db)}")
        print(f"  Actions: {valid_counts['actions']}/{len(actions_in_db)}")
        print(f"  Events: {valid_counts['events']}/{len(events_in_db)}")
        
        total_valid = sum(valid_counts.values())
        total_cards = sum([len(users_in_db), len(equipments_in_db), len(services_in_db), 
                          len(activities_in_db), len(challenges_in_db), len(actions_in_db), len(events_in_db)])
        print(f"\nTotal: {total_valid}/{total_cards} cartas têm arquivos válidos")
    
    def get_user_with_file(self, user_id: str) -> Optional[Tuple[UserCard, str]]:
        """
        Obtém carta de utilizador junto com o caminho do arquivo
        Retorna: (UserCard, file_path) ou None
        """
        user_card = self.get_user(user_id)
        if user_card:
            file_path = self.file_manager.get_card_file_path("users", user_id)
            if file_path and os.path.exists(file_path):
                return (user_card, file_path)
        return None
    
    def get_equipment_with_file(self, equipment_id: str) -> Optional[Tuple[EquipmentCard, str]]:
        """
        Obtém carta de equipamento junto com o caminho do arquivo
        Retorna: (EquipmentCard, file_path) ou None
        """
        equipment_card = self.get_equipment(equipment_id)
        if equipment_card:
            file_path = self.file_manager.get_card_file_path("equipments", equipment_id)
            if file_path and os.path.exists(file_path):
                return (equipment_card, file_path)
        return None
    
    def get_service_with_file(self, service_id: str) -> Optional[Tuple[ServiceCard, str]]:
        """
        Obtém carta de serviço junto com o caminho do arquivo
        Retorna: (ServiceCard, file_path) ou None
        """
        service_card = self.get_service(service_id)
        if service_card:
            file_path = self.file_manager.get_card_file_path("services", service_id)
            if file_path and os.path.exists(file_path):
                return (service_card, file_path)
        return None
    
    def get_activity_with_file(self, activity_id: str) -> Optional[Tuple[ActivityCard, str]]:
        """
        Obtém carta de atividade junto com o caminho do arquivo
        Retorna: (ActivityCard, file_path) ou None
        """
        activity_card = self.get_activity(activity_id)
        if activity_card:
            file_path = self.file_manager.get_card_file_path("activities", activity_id)
            if file_path and os.path.exists(file_path):
                return (activity_card, file_path)
        return None
    
    def get_challenge_with_file(self, challenge_id: str) -> Optional[Tuple[ChallengeCard, str]]:
        """
        Obtém carta de desafio junto com o caminho do arquivo
        Retorna: (ChallengeCard, file_path) ou None
        """
        challenge_card = self.get_challenge(challenge_id)
        if challenge_card:
            file_path = self.file_manager.get_card_file_path("challenges", challenge_id)
            if file_path and os.path.exists(file_path):
                return (challenge_card, file_path)
        return None
    
    def get_action_with_file(self, action_id: str) -> Optional[Tuple[ActionCard, str]]:
        """
        Obtém carta de ação junto com o caminho do arquivo
        Retorna: (ActionCard, file_path) ou None
        """
        action_card = self.get_action(action_id)
        if action_card:
            file_path = self.file_manager.get_card_file_path("actions", action_id)
            if file_path and os.path.exists(file_path):
                return (action_card, file_path)
        return None
    
    def get_event_with_file(self, event_id: str) -> Optional[Tuple[EventCard, str]]:
        """
        Obtém carta de evento junto com o caminho do arquivo
        Retorna: (EventCard, file_path) ou None
        """
        event_card = self.get_event(event_id)
        if event_card:
            file_path = self.file_manager.get_card_file_path("events", event_id)
            if file_path and os.path.exists(file_path):
                return (event_card, file_path)
        return None

def main():
    """
    Demonstração do sistema integrado atualizado
    """
    print("=" * 80)
    print("        SISTEMA INTEGRADO - CARTAS NETMASTER + ARQUIVOS FÍSICOS")
    print("        (Suporte para Raspberry Pi e Desenvolvimento Local)")
    print("=" * 80)
    
    # Inicializar base de dados integrada
    db = IntegratedCardDatabase(".")
    
    # Mostrar informações do ambiente
    print(f"\nAmbiente atual: {db.file_manager.environment}")
    print(f"Caminho base: {db.file_manager.base_dir}")
    
    # Demonstração de obtenção de cartas com arquivos
    print("\n" + "=" * 50)
    print("DEMONSTRAÇÃO DE ACESSO A CARTAS COM ARQUIVOS")
    print("=" * 50)
    
    # Testar diferentes tipos de cartas
    test_cases = [
        ("users", "1_red"),
        ("equipments", "small_router_1_blue"),
        ("services", "bandwidth_red"),
        ("activities", "activity_1_red"),
        ("challenges", "challenge_1"),
        ("actions", "action_1"),
        ("events", "event_367")
    ]
    
    for card_type, card_id in test_cases:
        print(f"\nTestando {card_type}: {card_id}")
        
        # Obter método correspondente
        method_name = f"get_{card_type[:-1]}_with_file"  # Remove 's' do final
        if hasattr(db, method_name):
            method = getattr(db, method_name)
            result = method(card_id)
            if result:
                card, file_path = result
                print(f"  ✓ Carta encontrada: {card}")
                print(f"  ✓ Arquivo: {file_path}")
            else:
                print(f"  ✗ Carta não encontrada ou arquivo não existe")
        else:
            print(f"  ✗ Método {method_name} não encontrado")
    
    print("\n" + "=" * 50)
    print("Demonstração concluída!")
    print("=" * 50)

if __name__ == "__main__":
    main()
