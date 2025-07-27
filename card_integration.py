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
from cards_database import UserCard, ContractCard, EquipmentCard, ServiceCard, UserType, EquipmentType, ServiceType, UserDatabase

class CardFileManager:
    """
    Gestor de arquivos de cartas - conecta dados com arquivos físicos
    """
    
    def __init__(self, base_dir="."):
        self.base_dir = base_dir
        self._detect_environment()
        self.card_mappings = self._build_card_mappings()
    
    def _detect_environment(self):
        """
        Detecta se está rodando no Raspberry Pi ou ambiente de desenvolvimento
        """
        import platform
        import os
        
        # Detectar se está no Raspberry Pi
        raspberry_pi_path = "/home/joao_rebolo/netmaster_menu/img/cartas"
        local_dev_path = "."
        
        if os.path.exists(raspberry_pi_path):
            self.base_dir = "/home/joao_rebolo/netmaster_menu"
            self.environment = "raspberry_pi"
            print(f"Ambiente detectado: Raspberry Pi")
            print(f"Caminho base: {self.base_dir}")
        else:
            self.base_dir = local_dev_path
            self.environment = "development"
            print(f"Ambiente detectado: Desenvolvimento Local")
            print(f"Caminho base: {self.base_dir}")
    
    def _get_users_path(self, color):
        """
        Retorna o caminho correto para cartas de users baseado no ambiente
        """
        if self.environment == "raspberry_pi":
            return os.path.join(self.base_dir, "img", "cartas", "Users", "Residential-level", color)
        else:
            return os.path.join(self.base_dir, "Users", "Residential-level", color)
    
    def _get_equipments_path(self, color):
        """
        Retorna o caminho correto para cartas de equipments baseado no ambiente
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
        # Service_Bandwidth_Red_80.png -> ServiceCard
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
                            full_path = os.path.join(services_dir, filename)
                            
                            # Extrair informações do nome do arquivo
                            # Service_Bandwidth_Red_80.png -> type=Bandwidth, color=Red, value=80
                            parts = filename.replace("Service_", "").replace(".png", "").split("_")
                            if len(parts) >= 3:
                                service_type = parts[0].lower()  # bandwidth, datavolume, temporary
                                file_color = parts[1].lower()
                                try:
                                    value = int(parts[2])
                                except (ValueError, IndexError):
                                    value = 0
                                
                                # ID único para a carta service
                                card_id = f"{service_type}_{file_color}_{value}"
                                mappings["services"][card_id] = {
                                    "path": full_path,
                                    "color": color_lower,
                                    "service_type": service_type,
                                    "value": value,
                                    "filename": filename
                                }
                                print(f"Mapeado: Service ID {card_id} -> {filename} ({color})")
                            else:
                                print(f"Formato de service não reconhecido: {filename}")
                        except Exception as e:
                            print(f"Erro ao processar service {filename}: {e}")
                            continue
            else:
                print(f"Diretório de services não encontrado: {services_dir}")
        
        print(f"Total de cartas mapeadas: {len(mappings['users'])} users + {len(mappings['equipments'])} equipments + {len(mappings['services'])} services")
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
        
        # Verificar quais cartas de users têm arquivos correspondentes
        available_user_files = self.file_manager.get_available_cards("users")
        print(f"Arquivos de users encontrados: {available_user_files}")
        
        # Verificar cartas de equipments
        available_equipment_files = self.file_manager.get_available_cards("equipments")
        print(f"Arquivos de equipments encontrados: {available_equipment_files}")
        
        # Verificar cartas na base de dados vs arquivos disponíveis
        users_in_db = list(self.users.keys())
        equipments_in_db = list(self.equipments.keys())
        print(f"Users na base de dados: {users_in_db}")
        print(f"Equipments na base de dados: {equipments_in_db}")
        
        # Contar quantas cartas têm arquivos correspondentes
        valid_user_cards = 0
        for user_id in users_in_db:
            if self.file_manager.card_exists("users", user_id):
                valid_user_cards += 1
                print(f"User ID {user_id}: arquivo encontrado")
            else:
                print(f"User ID {user_id}: arquivo NÃO encontrado")
        
        valid_equipment_cards = 0
        for equipment_id in equipments_in_db:
            if self.file_manager.card_exists("equipments", equipment_id):
                valid_equipment_cards += 1
                print(f"Equipment ID {equipment_id}: arquivo encontrado")
            else:
                print(f"Equipment ID {equipment_id}: arquivo NÃO encontrado")
        
        print(f"Resultado: {valid_user_cards}/{len(users_in_db)} users + {valid_equipment_cards}/{len(equipments_in_db)} equipments têm arquivos válidos")
    
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

def main():
    """
    Demonstração do sistema integrado
    """
    print("=" * 80)
    print("        SISTEMA INTEGRADO - CARTAS NETMASTER + ARQUIVOS FÍSICOS")
    print("=" * 80)
    
    # Inicializar base de dados integrada
    db = IntegratedCardDatabase(".")
    
    print("\nDemonstração concluída!")

if __name__ == "__main__":
    main()
