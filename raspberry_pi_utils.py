#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilitários para detecção automática de ambiente Raspberry Pi
Torna o sistema resiliente a diferentes nomes de utilizadores
"""

import os
import glob
import platform
import subprocess

def detect_raspberry_pi_user():
    """
    Detecta automaticamente o utilizador do Raspberry Pi onde o netmaster_menu está instalado
    
    Returns:
        str: Nome do utilizador encontrado ou None se não for encontrado
    """
    # Verificar se estamos num Raspberry Pi primeiro
    if not is_raspberry_pi():
        return None
    
    # Lista de utilizadores comuns em Raspberry Pi
    common_users = ["pi", "joao_rebolo", "joaorebolo2", "raspberry", "admin", "user"]
    
    # Primeiro tentar encontrar baseado na existência do diretório netmaster_menu
    for user in common_users:
        netmaster_path = f"/home/{user}/netmaster_menu"
        if os.path.exists(netmaster_path):
            print(f"DEBUG: [detect_raspberry_pi_user] Encontrado netmaster_menu em: {netmaster_path}")
            return user
    
    # Se não encontrar, tentar descobrir utilizadores no sistema
    try:
        # Listar todos os utilizadores no /home
        home_users = []
        if os.path.exists("/home"):
            home_users = [d for d in os.listdir("/home") if os.path.isdir(f"/home/{d}")]
        
        # Verificar se algum tem netmaster_menu
        for user in home_users:
            netmaster_path = f"/home/{user}/netmaster_menu"
            if os.path.exists(netmaster_path):
                print(f"DEBUG: [detect_raspberry_pi_user] Encontrado netmaster_menu em: {netmaster_path}")
                return user
    except Exception as e:
        print(f"DEBUG: [detect_raspberry_pi_user] Erro ao listar utilizadores: {e}")
    
    # Como último recurso, tentar obter o utilizador atual se estivermos no Pi
    try:
        current_user = os.getlogin()
        if current_user and current_user != "root":
            netmaster_path = f"/home/{current_user}/netmaster_menu"
            if os.path.exists(netmaster_path):
                print(f"DEBUG: [detect_raspberry_pi_user] Utilizador atual {current_user} tem netmaster_menu")
                return current_user
    except Exception as e:
        print(f"DEBUG: [detect_raspberry_pi_user] Erro ao obter utilizador atual: {e}")
    
    print("DEBUG: [detect_raspberry_pi_user] Nenhum utilizador com netmaster_menu encontrado")
    return None

def is_raspberry_pi():
    """
    Detecta se estamos a executar num Raspberry Pi
    
    Returns:
        bool: True se for Raspberry Pi, False caso contrário
    """
    # Método 1: Verificar hardware específico do Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read().lower()
            if 'raspberry pi' in cpuinfo or 'bcm' in cpuinfo:
                return True
    except FileNotFoundError:
        pass
    
    # Método 2: Verificar modelo do device
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read().lower()
            if 'raspberry pi' in model:
                return True
    except FileNotFoundError:
        pass
    
    # Método 3: Verificar hostname
    try:
        hostname = platform.node().lower()
        if 'raspberry' in hostname or 'raspberrypi' in hostname:
            return True
    except:
        pass
    
    # Método 4: Verificar se existe algum dos caminhos típicos do Pi
    raspberry_indicators = [
        '/opt/vc/bin/vcgencmd',
        '/boot/config.txt', 
        '/boot/cmdline.txt'
    ]
    
    for indicator in raspberry_indicators:
        if os.path.exists(indicator):
            return True
    
    return False

def get_raspberry_pi_base_path():
    """
    Obtém o caminho base para o netmaster_menu no Raspberry Pi
    
    Returns:
        str: Caminho completo para netmaster_menu ou None se não encontrado
    """
    user = detect_raspberry_pi_user()
    if user:
        return f"/home/{user}/netmaster_menu"
    return None

def get_raspberry_pi_paths():
    """
    Obtém todos os caminhos relevantes para o Raspberry Pi
    
    Returns:
        dict: Dicionário com todos os caminhos ou None se não for Raspberry Pi
    """
    if not is_raspberry_pi():
        return None
    
    user = detect_raspberry_pi_user()
    if not user:
        return None
    
    base_path = f"/home/{user}/netmaster_menu"
    
    return {
        'user': user,
        'base': base_path,
        'img': f"{base_path}/img",
        'cartas': f"{base_path}/img/cartas",
        'object_detection': f"{base_path}/object_detection",
        'detection_script': f"{base_path}/object_detection/detection_fullscreen.sh"
    }

def get_universal_paths():
    """
    Obtém caminhos que funcionam tanto em desenvolvimento como no Raspberry Pi
    
    Returns:
        dict: Dicionário com caminhos para diferentes ambientes
    """
    # Detectar ambiente
    pi_paths = get_raspberry_pi_paths()
    
    if pi_paths:
        # Estamos no Raspberry Pi
        return {
            'environment': 'raspberry_pi',
            'user': pi_paths['user'],
            'base_dir': pi_paths['base'],
            'img_dir': pi_paths['img'],
            'cartas_dir': pi_paths['cartas'],
            'object_detection_dir': pi_paths['object_detection'],
            'detection_script': pi_paths['detection_script']
        }
    else:
        # Estamos em desenvolvimento local
        current_dir = os.path.dirname(__file__)
        return {
            'environment': 'development',
            'user': None,
            'base_dir': current_dir,
            'img_dir': os.path.join(current_dir, "img"),
            'cartas_dir': os.path.join(current_dir, "img", "cartas"),
            'object_detection_dir': os.path.join(current_dir, "object_detection"),
            'detection_script': os.path.join(current_dir, "detection_fullscreen.sh")
        }

def get_possible_raspberry_pi_paths(relative_path):
    """
    Gera lista de caminhos possíveis para um caminho relativo no Raspberry Pi
    
    Args:
        relative_path: Caminho relativo a partir do netmaster_menu (ex: "img/cartas")
        
    Returns:
        list: Lista de caminhos possíveis ordenados por prioridade
    """
    paths = []
    
    # Se tivermos um utilizador detectado, usar esse primeiro
    user = detect_raspberry_pi_user()
    if user:
        paths.append(f"/home/{user}/netmaster_menu/{relative_path}")
    
    # Adicionar utilizadores comuns como fallback
    common_users = ["joaorebolo2", "joao_rebolo", "pi", "raspberry", "admin", "user"]
    for user in common_users:
        path = f"/home/{user}/netmaster_menu/{relative_path}"
        if path not in paths:  # Evitar duplicados
            paths.append(path)
    
    # Adicionar caminhos de desenvolvimento como último recurso
    current_dir = os.path.dirname(__file__)
    dev_paths = [
        os.path.join(current_dir, relative_path),
        os.path.join(os.path.dirname(current_dir), relative_path)
    ]
    
    for path in dev_paths:
        if path not in paths:
            paths.append(path)
    
    return paths

def find_existing_path(relative_path):
    """
    Encontra o primeiro caminho existente para um caminho relativo
    
    Args:
        relative_path: Caminho relativo (ex: "img/cartas")
        
    Returns:
        str: Primeiro caminho que existe ou None se nenhum existir
    """
    possible_paths = get_possible_raspberry_pi_paths(relative_path)
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def main():
    """
    Função de demonstração e teste
    """
    print("=" * 60)
    print("        UTILITÁRIOS RASPBERRY PI - TESTE")
    print("=" * 60)
    
    print(f"\nDetecção de Raspberry Pi: {is_raspberry_pi()}")
    
    user = detect_raspberry_pi_user()
    print(f"Utilizador detectado: {user}")
    
    pi_paths = get_raspberry_pi_paths()
    if pi_paths:
        print(f"\nCaminhos do Raspberry Pi:")
        for key, path in pi_paths.items():
            exists = "✅" if os.path.exists(path) else "❌"
            print(f"  {key}: {path} {exists}")
    
    universal_paths = get_universal_paths()
    print(f"\nCaminhos Universais:")
    print(f"  Ambiente: {universal_paths['environment']}")
    for key, path in universal_paths.items():
        if key != 'environment' and path:
            exists = "✅" if os.path.exists(path) else "❌"
            print(f"  {key}: {path} {exists}")
    
    # Testar busca de caminhos
    test_paths = ["img/cartas", "object_detection", "img"]
    print(f"\nTeste de busca de caminhos:")
    for rel_path in test_paths:
        found_path = find_existing_path(rel_path)
        if found_path:
            print(f"  {rel_path}: {found_path} ✅")
        else:
            print(f"  {rel_path}: Não encontrado ❌")

if __name__ == "__main__":
    main()
