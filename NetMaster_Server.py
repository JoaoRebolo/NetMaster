#!/usr/bin/env python3
"""
NetMaster Game Server
Servidor para o jogo NetMaster que suporta múltiplas sessões de até 4 jogadores.
Configurado para rodar na VM: netmaster.vps.tecnico.ulisboa.pt:8000
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import websockets
import logging
from dataclasses import dataclass, asdict
from enum import Enum

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('netmaster_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configurações do servidor
SERVER_HOST = "0.0.0.0"  # Bind em todas as interfaces
SERVER_PORT = 8000
MAX_PLAYERS_PER_SESSION = 4
SESSION_DURATION_MINUTES = 30
WAITING_TIMEOUT_MINUTES = 1  # Tempo limite para outros jogadores se juntarem
HEARTBEAT_INTERVAL = 30  # segundos

class GameState(Enum):
    WAITING = "waiting"
    STARTING = "starting"  
    PLAYING = "playing"
    FINISHED = "finished"
    EXPIRED = "expired"

class PlayerColor(Enum):
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"

@dataclass
class Player:
    """Representa um jogador na sessão"""
    id: str
    name: str
    color: PlayerColor
    websocket: Optional[object] = None
    connected: bool = True
    last_heartbeat: float = 0
    position: int = 0
    score: int = 1000  # Saldo inicial
    
    def to_dict(self):
        """Converte para dict sem o websocket"""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color.value if isinstance(self.color, PlayerColor) else self.color,
            'connected': self.connected,
            'last_heartbeat': self.last_heartbeat,
            'position': self.position,
            'score': self.score
        }

@dataclass 
class GameSession:
    """Representa uma sessão de jogo"""
    id: str
    host_player_id: str
    players: Dict[str, Player]
    state: GameState
    created_at: datetime
    expires_at: datetime
    waiting_expires_at: datetime  # Tempo limite para fase de espera
    max_players: int = MAX_PLAYERS_PER_SESSION
    duration_minutes: int = SESSION_DURATION_MINUTES  # Duração personalizada da sessão
    player_order: List[str] = None  # Ordem dos jogadores por entrada na sessão
    current_turn_index: int = 0  # Índice do jogador atual no player_order
    
    def is_expired(self) -> bool:
        """Verifica se a sessão expirou"""
        return datetime.now() > self.expires_at
    
    def is_waiting_expired(self) -> bool:
        """Verifica se o tempo de espera da sessão expirou"""
        return self.state == GameState.WAITING and datetime.now() > self.waiting_expires_at
    
    def is_full(self) -> bool:
        """Verifica se a sessão está cheia"""
        return len(self.players) >= self.max_players
    
    def get_available_colors(self) -> List[PlayerColor]:
        """Retorna cores disponíveis"""
        used_colors = {player.color for player in self.players.values()}
        return [color for color in PlayerColor if color not in used_colors]
    
    def get_current_player_id(self) -> Optional[str]:
        """Retorna o ID do jogador que tem a vez atual"""
        if not self.player_order or len(self.player_order) == 0:
            return None
        if self.current_turn_index >= len(self.player_order):
            return None
        return self.player_order[self.current_turn_index]
    
    def get_current_player(self) -> Optional[Player]:
        """Retorna o jogador que tem a vez atual"""
        current_id = self.get_current_player_id()
        if current_id and current_id in self.players:
            return self.players[current_id]
        return None
    
    def next_turn(self) -> Optional[str]:
        """Avança para o próximo turno e retorna o ID do próximo jogador"""
        if not self.player_order or len(self.player_order) == 0:
            return None
        
        self.current_turn_index = (self.current_turn_index + 1) % len(self.player_order)
        return self.get_current_player_id()
    
    def add_player_to_order(self, player_id: str):
        """Adiciona jogador à ordem de turnos"""
        if self.player_order is None:
            self.player_order = []
        if player_id not in self.player_order:
            self.player_order.append(player_id)
    
    def remove_player_from_order(self, player_id: str):
        """Remove jogador da ordem de turnos"""
        if self.player_order and player_id in self.player_order:
            old_index = self.player_order.index(player_id)
            self.player_order.remove(player_id)
            
            # Ajustar current_turn_index se necessário
            if self.current_turn_index >= len(self.player_order) and len(self.player_order) > 0:
                self.current_turn_index = 0
            elif old_index < self.current_turn_index:
                self.current_turn_index -= 1
    
    def to_dict(self):
        """Converte para dict serializável"""
        return {
            'id': self.id,
            'host_player_id': self.host_player_id,
            'players': {pid: player.to_dict() for pid, player in self.players.items()},
            'state': self.state.value,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'waiting_expires_at': self.waiting_expires_at.isoformat(),
            'max_players': self.max_players,
            'duration_minutes': self.duration_minutes,
            'current_players': len(self.players),
            'is_full': self.is_full(),
            'available_colors': [color.value for color in self.get_available_colors()],
            'waiting_time_left': max(0, int((self.waiting_expires_at - datetime.now()).total_seconds())) if self.state == GameState.WAITING else 0,
            'player_order': self.player_order or [],
            'current_turn_index': self.current_turn_index,
            'current_player_id': self.get_current_player_id()
        }

class NetMasterServer:
    """Servidor principal do NetMaster"""
    
    def __init__(self):
        self.sessions: Dict[str, GameSession] = {}
        self.connected_clients: Dict[str, object] = {}  # websocket connections
        self.player_to_session: Dict[str, str] = {}  # player_id -> session_id mapping
        self.running = False
        
    async def start_server(self):
        """Inicia o servidor WebSocket"""
        logger.info(f"Iniciando NetMaster Server em {SERVER_HOST}:{SERVER_PORT}")
        logger.info(f"Configurações:")
        logger.info(f"   - Máximo {MAX_PLAYERS_PER_SESSION} jogadores por sessão")
        logger.info(f"   - Duração máxima: {SESSION_DURATION_MINUTES} minutos")
        logger.info(f"   - Tempo de espera para outros jogadores: {WAITING_TIMEOUT_MINUTES} minuto(s)")
        logger.info(f"   - Heartbeat: {HEARTBEAT_INTERVAL} segundos")
        
        self.running = True
        
        # Iniciar tarefas de background
        asyncio.create_task(self.cleanup_expired_sessions())
        asyncio.create_task(self.heartbeat_monitor())
        
        # Iniciar servidor WebSocket
        async with websockets.serve(self.handle_client, SERVER_HOST, SERVER_PORT):
            logger.info(f"Servidor NetMaster ativo em ws://{SERVER_HOST}:{SERVER_PORT}")
            logger.info(f"Acesso público: ws://netmaster.vps.tecnico.ulisboa.pt:8000")
            await asyncio.Future()  # run forever
    
    async def handle_client(self, websocket, path):
        """Lida com conexões de clientes"""
        client_id = str(uuid.uuid4())
        self.connected_clients[client_id] = websocket
        
        try:
            logger.info(f"Cliente conectado: {client_id} de {websocket.remote_address}")
            
            # Enviar mensagem de boas-vindas
            await self.send_message(websocket, {
                'type': 'welcome',
                'client_id': client_id,
                'server_info': {
                    'name': 'NetMaster Server',
                    'version': '1.0.0',
                    'max_players_per_session': MAX_PLAYERS_PER_SESSION,
                    'session_duration_minutes': SESSION_DURATION_MINUTES
                }
            })
            
            # Processar mensagens do cliente
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.process_message(client_id, websocket, data)
                except json.JSONDecodeError:
                    logger.error(f"Mensagem JSON inválida de {client_id}: {message}")
                    await self.send_error(websocket, "Formato de mensagem inválido")
                except Exception as e:
                    logger.error(f"Erro ao processar mensagem de {client_id}: {e}")
                    await self.send_error(websocket, f"Erro interno: {str(e)}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Cliente desconectado: {client_id}")
        except Exception as e:
            logger.error(f"Erro na conexão {client_id}: {e}")
        finally:
            await self.cleanup_client(client_id)
    
    async def process_message(self, client_id: str, websocket, data: dict):
        """Processa mensagens recebidas dos clientes"""
        message_type = data.get('type')
        logger.info(f"Mensagem de {client_id}: {message_type}")
        
        handlers = {
            'create_session': self.handle_create_session,
            'join_session': self.handle_join_session,
            'leave_session': self.handle_leave_session,
            'list_sessions': self.handle_list_sessions,
            'start_game': self.handle_start_game,
            'game_action': self.handle_game_action,
            'heartbeat': self.handle_heartbeat,
            'get_session_info': self.handle_get_session_info
        }
        
        handler = handlers.get(message_type)
        if handler:
            await handler(client_id, websocket, data)
        else:
            logger.warning(f"Tipo de mensagem desconhecido: {message_type}")
            await self.send_error(websocket, f"Tipo de mensagem não suportado: {message_type}")
    
    async def handle_create_session(self, client_id: str, websocket, data: dict):
        """Cria uma nova sessão de jogo"""
        try:
            player_name = data.get('player_name', 'Player')
            player_color = data.get('color', 'red')
            duration_minutes = data.get('duration_minutes', SESSION_DURATION_MINUTES)
            
            # Validar duração (entre 15 e 120 minutos)
            if not isinstance(duration_minutes, int) or duration_minutes < 15 or duration_minutes > 120:
                await self.send_error(websocket, f"Duração inválida: {duration_minutes}. Deve ser entre 15 e 120 minutos.")
                return
            
            # Validar cor
            try:
                color_enum = PlayerColor(player_color.lower())
            except ValueError:
                await self.send_error(websocket, f"Cor inválida: {player_color}")
                return
            
            # Criar nova sessão
            session_id = str(uuid.uuid4())[:8]  # ID curto para facilitar compartilhamento
            player_id = str(uuid.uuid4())
            
            # Criar jogador host
            host_player = Player(
                id=player_id,
                name=player_name,
                color=color_enum,
                websocket=websocket,
                connected=True,
                last_heartbeat=time.time()
            )
            
            # Criar sessão
            session = GameSession(
                id=session_id,
                host_player_id=player_id,
                players={player_id: host_player},
                state=GameState.WAITING,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(minutes=duration_minutes),
                waiting_expires_at=datetime.now() + timedelta(minutes=WAITING_TIMEOUT_MINUTES),
                duration_minutes=duration_minutes
            )
            
            # CORREÇÃO: Adicionar host à ordem de turnos imediatamente
            session.add_player_to_order(player_id)
            logger.info(f"Host {player_name} adicionado à ordem de turnos: {session.player_order}")
            
            self.sessions[session_id] = session
            self.player_to_session[player_id] = session_id
            
            logger.info(f"Nova sessão criada: {session_id} por {player_name} ({player_color}) - Duração: {duration_minutes}min")
            
            # Responder ao criador
            try:
                session_dict = session.to_dict()
                player_dict = host_player.to_dict()
                logger.info(f"Enviando resposta de criação de sessão...")
                
                await self.send_message(websocket, {
                    'type': 'session_created',
                    'session': session_dict,
                    'player_id': player_id,
                    'player_info': player_dict
                })
                
                logger.info(f"Resposta enviada com sucesso")
            except Exception as response_error:
                logger.error(f"Erro ao enviar resposta de criação: {response_error}")
                raise response_error
            
            # Broadcast para outros clientes sobre nova sessão disponível
            try:
                logger.info(f"Fazendo broadcast da lista de sessões...")
                await self.broadcast_session_list_update()
                logger.info(f"Broadcast concluído com sucesso")
            except Exception as broadcast_error:
                logger.error(f"Erro no broadcast: {broadcast_error}")
                # Não fazer raise aqui para não falhar a criação da sessão
            
        except Exception as e:
            logger.error(f"Erro ao criar sessão: {e}")
            await self.send_error(websocket, f"Erro ao criar sessão: {str(e)}")
    
    async def handle_join_session(self, client_id: str, websocket, data: dict):
        """Permite que um jogador se junte a uma sessão existente"""
        try:
            session_id = data.get('session_id')
            player_name = data.get('player_name', 'Player')
            player_color = data.get('color')
            
            # Verificar se sessão existe
            session = self.sessions.get(session_id)
            if not session:
                await self.send_error(websocket, "Sessão não encontrada")
                return
            
            # Verificar se sessão não expirou
            if session.is_expired():
                await self.send_error(websocket, "Sessão expirada")
                return
            
            # Verificar se sessão não está cheia
            if session.is_full():
                await self.send_error(websocket, "Sessão lotada")
                return
            
            # Verificar se cor está disponível
            if player_color:
                try:
                    color_enum = PlayerColor(player_color.lower())
                    if color_enum not in session.get_available_colors():
                        await self.send_error(websocket, f"Cor {player_color} não disponível")
                        return
                except ValueError:
                    await self.send_error(websocket, f"Cor inválida: {player_color}")
                    return
            else:
                # Atribuir primeira cor disponível
                available_colors = session.get_available_colors()
                if not available_colors:
                    await self.send_error(websocket, "Nenhuma cor disponível")
                    return
                color_enum = available_colors[0]
            
            # Criar novo jogador
            player_id = str(uuid.uuid4())
            new_player = Player(
                id=player_id,
                name=player_name,
                color=color_enum,
                websocket=websocket,
                connected=True,
                last_heartbeat=time.time()
            )
            
            # Adicionar à sessão
            session.players[player_id] = new_player
            self.player_to_session[player_id] = session_id
            
            # Adicionar jogador à ordem de turnos
            session.add_player_to_order(player_id)
            
            # Se é o segundo jogador, estender o tempo de espera
            if len(session.players) == 2 and session.state == GameState.WAITING:
                # Estender o tempo de espera para permitir mais jogadores se juntarem
                session.waiting_expires_at = datetime.now() + timedelta(minutes=5)  # 5 minutos adicionais
                logger.info(f"Segundo jogador juntou-se à sessão {session_id}. Tempo de espera estendido para 5 minutos.")
            
            logger.info(f"{player_name} ({color_enum.value}) juntou-se à sessão {session_id}")
            
            # Responder ao novo jogador
            await self.send_message(websocket, {
                'type': 'session_joined',
                'session': session.to_dict(),
                'player_id': player_id,
                'player_info': new_player.to_dict()
            })
            
            # Notificar outros jogadores na sessão
            await self.broadcast_to_session(session_id, {
                'type': 'player_joined',
                'player': new_player.to_dict(),
                'session': session.to_dict()
            }, exclude_player=player_id)
            
            # Broadcast atualização da lista de sessões
            await self.broadcast_session_list_update()
            
        except Exception as e:
            logger.error(f"Erro ao juntar à sessão: {e}")
            await self.send_error(websocket, f"Erro ao juntar à sessão: {str(e)}")
    
    async def handle_leave_session(self, client_id: str, websocket, data: dict):
        """Remove jogador da sessão"""
        try:
            player_id = data.get('player_id')
            session_id = self.player_to_session.get(player_id)
            
            if not session_id or session_id not in self.sessions:
                await self.send_error(websocket, "Jogador não está em nenhuma sessão")
                return
            
            await self.remove_player_from_session(player_id)
            
            await self.send_message(websocket, {
                'type': 'session_left',
                'message': 'Saiu da sessão com sucesso'
            })
            
        except Exception as e:
            logger.error(f"Erro ao sair da sessão: {e}")
            await self.send_error(websocket, f"Erro ao sair da sessão: {str(e)}")
    
    async def handle_list_sessions(self, client_id: str, websocket, data: dict):
        """Lista sessões disponíveis"""
        try:
            # Filtrar apenas sessões ativas e não cheias
            available_sessions = []
            for session in self.sessions.values():
                if (session.state in [GameState.WAITING, GameState.STARTING] and 
                    not session.is_expired() and 
                    not session.is_full()):
                    available_sessions.append(session.to_dict())
            
            await self.send_message(websocket, {
                'type': 'sessions_list',
                'sessions': available_sessions,
                'total_sessions': len(self.sessions),
                'available_sessions': len(available_sessions)
            })
            
        except Exception as e:
            logger.error(f"Erro ao listar sessões: {e}")
            await self.send_error(websocket, f"Erro ao listar sessões: {str(e)}")
    
    async def handle_start_game(self, client_id: str, websocket, data: dict):
        """Inicia o jogo (apenas o host pode fazer isso)"""
        try:
            player_id = data.get('player_id')
            session_id = self.player_to_session.get(player_id)
            
            if not session_id or session_id not in self.sessions:
                await self.send_error(websocket, "Sessão não encontrada")
                return
            
            session = self.sessions[session_id]
            
            # Verificar se é o host
            if session.host_player_id != player_id:
                await self.send_error(websocket, "Apenas o host pode iniciar o jogo")
                return
            
            # Verificar se há pelo menos 2 jogadores
            if len(session.players) < 2:
                await self.send_error(websocket, "Necessário pelo menos 2 jogadores para iniciar")
                return
            
            # Mudar estado da sessão
            session.state = GameState.PLAYING
            
            # Inicializar ordem dos jogadores se não existe
            if not session.player_order:
                session.player_order = list(session.players.keys())
                logger.info(f"Ordem dos jogadores inicializada: {session.player_order}")
            
            # Definir o primeiro jogador como atual (índice 0)
            session.current_turn_index = 0
            first_player_id = session.get_current_player_id()
            logger.info(f"Primeiro jogador definido: {first_player_id}")
            
            logger.info(f"Jogo iniciado na sessão {session_id} com {len(session.players)} jogadores")
            
            # Notificar todos os jogadores
            await self.broadcast_to_session(session_id, {
                'type': 'game_started',
                'session': session.to_dict(),
                'message': 'O jogo começou!'
            })
            
            # Atualizar lista de sessões (sessão não estará mais disponível)
            await self.broadcast_session_list_update()
            
        except Exception as e:
            logger.error(f"Erro ao iniciar jogo: {e}")
            await self.send_error(websocket, f"Erro ao iniciar jogo: {str(e)}")
    
    async def handle_game_action(self, client_id: str, websocket, data: dict):
        """Processa ações de jogo (movimento, cartas, etc.)"""
        try:
            player_id = data.get('player_id')
            action_type = data.get('action_type')
            action_data = data.get('action_data', {})
            
            session_id = self.player_to_session.get(player_id)
            if not session_id or session_id not in self.sessions:
                await self.send_error(websocket, "Sessão não encontrada")
                return
            
            session = self.sessions[session_id]
            
            # Verificar se jogo está ativo
            if session.state != GameState.PLAYING:
                await self.send_error(websocket, "Jogo não está ativo")
                return
            
            # Processar ação específica
            response = await self.process_game_action(session, player_id, action_type, action_data, session_id)
            
            # Enviar resposta ao jogador
            await self.send_message(websocket, {
                'type': 'action_result',
                'action_type': action_type,
                'success': True,
                'result': response
            })
            
            # Broadcast da ação para outros jogadores
            await self.broadcast_to_session(session_id, {
                'type': 'player_action',
                'player_id': player_id,
                'action_type': action_type,
                'action_data': action_data,
                'result': response
            }, exclude_player=player_id)
            
        except Exception as e:
            logger.error(f"Erro ao processar ação de jogo: {e}")
            await self.send_error(websocket, f"Erro na ação: {str(e)}")
    
    async def handle_heartbeat(self, client_id: str, websocket, data: dict):
        """Processa heartbeat de jogadores"""
        try:
            player_id = data.get('player_id')
            session_id = self.player_to_session.get(player_id)
            
            if session_id and session_id in self.sessions:
                session = self.sessions[session_id]
                if player_id in session.players:
                    session.players[player_id].last_heartbeat = time.time()
            
            await self.send_message(websocket, {
                'type': 'heartbeat_ack',
                'timestamp': time.time()
            })
            
        except Exception as e:
            logger.error(f"Erro no heartbeat: {e}")
    
    async def handle_get_session_info(self, client_id: str, websocket, data: dict):
        """Retorna informações detalhadas de uma sessão"""
        try:
            session_id = data.get('session_id')
            session = self.sessions.get(session_id)
            
            if not session:
                await self.send_error(websocket, "Sessão não encontrada")
                return
            
            await self.send_message(websocket, {
                'type': 'session_info',
                'session': session.to_dict()
            })
            
        except Exception as e:
            logger.error(f"Erro ao obter info da sessão: {e}")
            await self.send_error(websocket, f"Erro ao obter informações: {str(e)}")
    
    async def process_game_action(self, session: GameSession, player_id: str, action_type: str, action_data: dict, session_id: str = None):
        """Processa ações específicas do jogo NetMaster"""
        player = session.players.get(player_id)
        if not player:
            raise ValueError("Jogador não encontrado na sessão")
        
        # Se session_id não foi fornecido, tentar encontrá-lo
        if session_id is None:
            session_id = self.player_to_session.get(player_id)
        
        # Implementar lógica específica baseada no tipo de ação
        if action_type == "move":
            # Movimento no tabuleiro
            new_position = action_data.get('position', player.position)
            player.position = new_position
            return {'new_position': new_position}
        
        elif action_type == "buy_card":
            # Compra de carta
            card_id = action_data.get('card_id')
            cost = action_data.get('cost', 0)
            
            if player.score >= cost:
                player.score -= cost
                return {'card_purchased': card_id, 'new_score': player.score}
            else:
                raise ValueError("Saldo insuficiente")
        
        elif action_type == "end_turn":
            # Final de turno - avançar para próximo jogador se há mais de um jogador
            logger.info(f"Processando end_turn para jogador {player_id} na sessão {session_id}")
            logger.info(f"Jogadores na sessão: {len(session.players)}")
            logger.info(f"Player order atual: {session.player_order}")
            logger.info(f"Current turn index: {session.current_turn_index}")
            
            if len(session.players) > 1:
                # Verificar se ainda é o turno do jogador que está tentando terminar
                current_player_id = session.get_current_player_id()
                if current_player_id != player_id:
                    logger.warning(f"Jogador {player_id} tentou terminar turno, mas é a vez de {current_player_id}")
                    raise ValueError(f"Não é a sua vez. É a vez do jogador {current_player_id}")
                
                next_player_id = session.next_turn()
                next_player = session.get_current_player()
                
                logger.info(f"Próximo jogador: {next_player_id} ({next_player.name if next_player else 'Unknown'})")
                logger.info(f"Novo turn index: {session.current_turn_index}")
                
                # Notificar todos os jogadores sobre a mudança de turno
                turn_changed_message = {
                    'type': 'turn_changed',
                    'current_player_id': next_player_id,
                    'current_player_name': next_player.name if next_player else 'Unknown',
                    'current_player_color': next_player.color.value if next_player and hasattr(next_player.color, 'value') else str(next_player.color) if next_player else 'unknown',
                    'player_order': session.player_order,
                    'current_turn_index': session.current_turn_index
                }
                
                logger.info(f"Enviando turn_changed: {turn_changed_message}")
                await self.broadcast_to_session(session_id, turn_changed_message)
                
                return {
                    'message': 'Turno finalizado',
                    'next_player_id': next_player_id,
                    'next_player_name': next_player.name if next_player else 'Unknown'
                }
            else:
                logger.info("Sessão com apenas um jogador - modo solo")
                return {'message': 'Turno finalizado (modo solo)'}
        
        else:
            return {'message': f'Ação {action_type} processada'}
    
    async def send_message(self, websocket, message: dict):
        """Envia mensagem para um websocket"""
        try:
            # Testar serialização JSON antes de enviar
            json_message = json.dumps(message)
            await websocket.send(json_message)
        except TypeError as json_error:
            logger.error(f"Erro de serialização JSON: {json_error}")
            logger.error(f"Mensagem problemática: {message}")
            raise json_error
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}")
            raise e
    
    async def send_error(self, websocket, error_message: str):
        """Envia mensagem de erro"""
        await self.send_message(websocket, {
            'type': 'error',
            'message': error_message,
            'timestamp': time.time()
        })
    
    async def broadcast_to_session(self, session_id: str, message: dict, exclude_player: str = None):
        """Envia mensagem para todos os jogadores de uma sessão"""
        session = self.sessions.get(session_id)
        if not session:
            return
        
        for player_id, player in session.players.items():
            if exclude_player and player_id == exclude_player:
                continue
            
            if player.websocket and player.connected:
                try:
                    await self.send_message(player.websocket, message)
                except:
                    # Marcar jogador como desconectado
                    player.connected = False
    
    async def broadcast_session_list_update(self):
        """Envia atualização da lista de sessões para todos os clientes conectados"""
        try:
            available_sessions = []
            for session in self.sessions.values():
                if (session.state in [GameState.WAITING, GameState.STARTING] and 
                    not session.is_expired() and 
                    not session.is_full()):
                    try:
                        session_dict = session.to_dict()
                        available_sessions.append(session_dict)
                    except Exception as session_error:
                        logger.error(f"Erro ao serializar sessão {session.id}: {session_error}")
                        continue
            
            message = {
                'type': 'sessions_list_update',
                'sessions': available_sessions
            }
            
            logger.info(f"Broadcasting lista de sessões: {len(available_sessions)} sessões disponíveis")
            
            # Enviar para todos os clientes conectados
            for client_id, websocket in list(self.connected_clients.items()):
                try:
                    await self.send_message(websocket, message)
                except Exception as send_error:
                    logger.error(f"Erro ao enviar para cliente {client_id}: {send_error}")
                    # Remover cliente com problema
                    self.connected_clients.pop(client_id, None)
                    
        except Exception as e:
            logger.error(f"Erro geral no broadcast_session_list_update: {e}")
    
    async def remove_player_from_session(self, player_id: str):
        """Remove jogador de uma sessão"""
        session_id = self.player_to_session.get(player_id)
        if not session_id or session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        player = session.players.get(player_id)
        
        if not player:
            return
        
        # Remover jogador
        del session.players[player_id]
        del self.player_to_session[player_id]
        
        # Remover jogador da ordem de turnos
        session.remove_player_from_order(player_id)
        
        # Ajustar current_turn_index se necessário
        if session.player_order and session.current_turn_index >= len(session.player_order):
            session.current_turn_index = 0
        
        logger.info(f"{player.name} saiu da sessão {session_id}")
        logger.info(f"Player order atualizada: {session.player_order}")
        logger.info(f"Current turn index ajustado: {session.current_turn_index}")
        
        # Se era o host e há outros jogadores, transferir host
        if session.host_player_id == player_id and session.players:
            new_host_id = next(iter(session.players.keys()))
            session.host_player_id = new_host_id
            logger.info(f"Host transferido para {session.players[new_host_id].name}")
            
            # Notificar novo host
            await self.broadcast_to_session(session_id, {
                'type': 'host_changed',
                'new_host_id': new_host_id,
                'new_host_name': session.players[new_host_id].name
            })
        
        # Se não há mais jogadores, remover sessão
        if not session.players:
            del self.sessions[session_id]
            logger.info(f"Sessão {session_id} removida (sem jogadores)")
        else:
            # Se a sessão estava PLAYING e agora só tem 1 jogador, ajustar o estado
            if session.state == GameState.PLAYING and len(session.players) == 1:
                logger.info(f"Sessão {session_id} voltou para modo solo (1 jogador restante)")
                # Manter o jogo ativo mas ajustar o turno para o jogador restante
                remaining_player_id = next(iter(session.players.keys()))
                session.current_turn_index = 0  # Reset para o primeiro (e único) jogador
                
                # Notificar o jogador restante que agora é a vez dele
                await self.broadcast_to_session(session_id, {
                    'type': 'turn_changed',
                    'current_player_id': remaining_player_id,
                    'current_player_name': session.players[remaining_player_id].name,
                    'current_player_color': session.players[remaining_player_id].color.value if hasattr(session.players[remaining_player_id].color, 'value') else str(session.players[remaining_player_id].color),
                    'player_order': session.player_order,
                    'current_turn_index': session.current_turn_index,
                    'game_mode': 'solo'  # Indicar que agora é modo solo
                })
            
            # Notificar jogadores restantes sobre o jogador que saiu
            await self.broadcast_to_session(session_id, {
                'type': 'player_left',
                'player_id': player_id,
                'player_name': player.name,
                'session': session.to_dict()
            })
        
        # Atualizar lista de sessões
        await self.broadcast_session_list_update()
    
    async def cleanup_client(self, client_id: str):
        """Limpa recursos quando cliente desconecta"""
        # Remover da lista de clientes conectados
        websocket = self.connected_clients.pop(client_id, None)
        
        # Encontrar jogador por websocket e remover da sessão
        for player_id, session_id in list(self.player_to_session.items()):
            session = self.sessions.get(session_id)
            if session and player_id in session.players:
                player = session.players[player_id]
                # Comparar websockets diretamente
                if player.websocket == websocket:
                    logger.info(f"Removendo jogador {player.name} (ID: {player_id}) da sessão {session_id} devido à desconexão")
                    await self.remove_player_from_session(player_id)
                    break
    
    async def cleanup_expired_sessions(self):
        """Remove sessões expiradas periodicamente"""
        while self.running:
            try:
                expired_sessions = []
                waiting_timeout_sessions = []
                
                for session_id, session in self.sessions.items():
                    if session.is_expired():
                        expired_sessions.append(session_id)
                    elif session.is_waiting_expired():
                        waiting_timeout_sessions.append(session_id)
                
                # Processar sessões com timeout de espera
                for session_id in waiting_timeout_sessions:
                    session = self.sessions[session_id]
                    logger.info(f"Sessão {session_id} expirou por timeout de espera (1 minuto)")
                    
                    # Se há apenas 1 jogador (criador da sessão), permitir jogo solo
                    if len(session.players) == 1:
                        # Mudar estado para permitir que o jogador continue sozinho
                        session.state = GameState.PLAYING  # Permitir continuar como jogo solo
                        
                        # Notificar o jogador sobre timeout mas permanecer na sessão
                        await self.broadcast_to_session(session_id, {
                            'type': 'waiting_timeout',
                            'message': 'Tempo limite de espera atingido. Pode iniciar um jogo solo.',
                            'timeout_reason': 'waiting_expired',
                            'allow_solo': True
                        })
                        
                        logger.info(f"Sessão {session_id} convertida para jogo solo")
                    else:
                        # Se há múltiplos jogadores, processar normalmente
                        await self.broadcast_to_session(session_id, {
                            'type': 'waiting_timeout',
                            'message': 'Tempo limite de espera atingido.',
                            'timeout_reason': 'waiting_expired'
                        })
                        
                        # Remover jogadores apenas se há múltiplos
                        for player_id in list(session.players.keys()):
                            await self.remove_player_from_session(player_id)
                
                # Processar sessões expiradas normalmente
                for session_id in expired_sessions:
                    session = self.sessions[session_id]
                    logger.info(f"Sessão {session_id} expirou por tempo total de jogo")
                    
                    # NOVA FUNCIONALIDADE: Calcular vencedor baseado no saldo
                    if len(session.players) > 0:
                        game_result = self.calculate_game_winner(session)
                        
                        if game_result:
                            logger.info(f"Resultado final da sessão {session_id}:")
                            logger.info(f"  Vencedor: {game_result['winner']['player_name']} ({game_result['winner']['score']} pontos)")
                            
                            # Notificar jogadores sobre o resultado final
                            await self.broadcast_to_session(session_id, {
                                'type': 'game_finished',
                                'message': 'Jogo terminado! Vencedor determinado por maior saldo.',
                                'timeout_reason': 'session_expired',
                                'game_result': game_result
                            })
                            
                            # Aguardar um pouco para garantir que a mensagem é entregue
                            await asyncio.sleep(2)
                        else:
                            # Fallback para caso não seja possível calcular vencedor
                            await self.broadcast_to_session(session_id, {
                                'type': 'session_expired',
                                'message': 'A sessão expirou',
                                'timeout_reason': 'session_expired'
                            })
                    else:
                        # Sessão sem jogadores
                        await self.broadcast_to_session(session_id, {
                            'type': 'session_expired',
                            'message': 'A sessão expirou',
                            'timeout_reason': 'session_expired'
                        })
                    
                    # Remover jogadores após mostrar o resultado
                    for player_id in list(session.players.keys()):
                        await self.remove_player_from_session(player_id)
                
                if expired_sessions or waiting_timeout_sessions:
                    await self.broadcast_session_list_update()
                    
            except Exception as e:
                logger.error(f"Erro na limpeza de sessões: {e}")
            
            await asyncio.sleep(30)  # Verificar a cada 30 segundos para ser mais responsivo
    
    def calculate_game_winner(self, session: GameSession):
        """Calcula o vencedor do jogo baseado no saldo"""
        if not session.players:
            return None
        
        # Ordenar jogadores por saldo (maior para menor)
        players_by_score = sorted(
            session.players.values(), 
            key=lambda p: p.score, 
            reverse=True
        )
        
        winner = players_by_score[0]
        logger.info(f"Vencedor da sessão {session.id}: {winner.name} com {winner.score} pontos")
        
        # Criar ranking completo
        ranking = []
        for i, player in enumerate(players_by_score):
            ranking.append({
                'position': i + 1,
                'player_id': player.id,
                'player_name': player.name,
                'player_color': player.color.value if isinstance(player.color, PlayerColor) else player.color,
                'score': player.score,
                'is_winner': i == 0
            })
        
        return {
            'winner': {
                'player_id': winner.id,
                'player_name': winner.name,
                'player_color': winner.color.value if isinstance(winner.color, PlayerColor) else winner.color,
                'score': winner.score
            },
            'ranking': ranking,
            'total_players': len(session.players)
        }

    async def heartbeat_monitor(self):
        """Monitora heartbeats dos jogadores"""
        while self.running:
            try:
                current_time = time.time()
                disconnected_players = []
                
                for session_id, session in self.sessions.items():
                    for player_id, player in session.players.items():
                        # Se não recebeu heartbeat há mais de 2x o intervalo, considerar desconectado
                        if (current_time - player.last_heartbeat) > (HEARTBEAT_INTERVAL * 2):
                            disconnected_players.append(player_id)
                            logger.warning(f"{player.name} sem heartbeat há {current_time - player.last_heartbeat:.1f}s")
                
                # Remover jogadores desconectados
                for player_id in disconnected_players:
                    await self.remove_player_from_session(player_id)
                    
            except Exception as e:
                logger.error(f"Erro no monitor de heartbeat: {e}")
            
            await asyncio.sleep(HEARTBEAT_INTERVAL)

# Função principal
async def main():
    """Função principal do servidor"""
    server = NetMasterServer()
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("Servidor interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro crítico no servidor: {e}")
    finally:
        server.running = False
        logger.info("Servidor NetMaster finalizado")

if __name__ == "__main__":
    print("NetMaster Server v1.0.0")
    print("=" * 50)
    asyncio.run(main())
