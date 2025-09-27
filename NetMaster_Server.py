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
    empty_since: Optional[float] = None  # Timestamp quando ficou vazia (para remoção adiada)
    pending_cards: Dict[str, List[Dict]] = None  # Cartas pendentes por cor do jogador
    timer_finished: bool = False  # Flag para indicar que o timer já processou esta sessão
    
    # *** NOVO SISTEMA DE BROADCAST DE JOGADORES ***
    players_info: Dict[str, Dict] = None  # {player_id: {'color': 'red', 'name': 'J', 'websocket': ws}}
    active_players: List[str] = None  # Lista ordenada dos player_ids ativos
    
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
    
    def store_card_for_player(self, target_player_color: str, card_data: Dict):
        """Armazena carta pendente para um jogador"""
        if self.pending_cards is None:
            self.pending_cards = {}
        
        if target_player_color not in self.pending_cards:
            self.pending_cards[target_player_color] = []
        
        self.pending_cards[target_player_color].append(card_data)
        logger.info(f"[CARD_STORAGE] Carta armazenada para jogador {target_player_color}: {card_data.get('card_path', 'Unknown')}")
        logger.info(f"[CARD_STORAGE] Total cartas pendentes para {target_player_color}: {len(self.pending_cards[target_player_color])}")
    
    def get_pending_cards(self, player_color: str) -> List[Dict]:
        """Obtém e remove cartas pendentes para um jogador"""
        if self.pending_cards is None or player_color not in self.pending_cards:
            return []
        
        cards = self.pending_cards[player_color].copy()
        self.pending_cards[player_color].clear()
        
        logger.info(f"[CARD_DELIVERY] Entregando {len(cards)} cartas pendentes para jogador {player_color}")
        for card in cards:
            logger.info(f"[CARD_DELIVERY] - {card.get('card_path', 'Unknown')} de {card.get('from_player', 'Unknown')}")
        
        return cards
    
    def get_pending_cards_count(self, player_color: str) -> int:
        """Obtém número de cartas pendentes para um jogador"""
        if self.pending_cards is None or player_color not in self.pending_cards:
            return 0
        return len(self.pending_cards[player_color])
    
    # *** NOVO SISTEMA DE BROADCAST DE JOGADORES ***
    
    def add_player_info(self, player_id: str, color: str, name: str, websocket):
        """Adiciona informações completas do jogador ao sistema de broadcast"""
        if self.players_info is None:
            self.players_info = {}
        if self.active_players is None:
            self.active_players = []
            
        self.players_info[player_id] = {
            'color': color,
            'name': name,
            'websocket': websocket,
            'joined_at': time.time()
        }
        
        if player_id not in self.active_players:
            self.active_players.append(player_id)
        
        logger.info(f"[PLAYERS_INFO] *** JOGADOR ADICIONADO AO BROADCAST SYSTEM ***")
        logger.info(f"[PLAYERS_INFO] Jogador: {name} ({color}) - ID: {player_id}")
        logger.info(f"[PLAYERS_INFO] Total jogadores ativos: {len(self.active_players)}")
        logger.info(f"[PLAYERS_INFO] Lista ativa: {[self.players_info[pid]['name'] + '(' + self.players_info[pid]['color'] + ')' for pid in self.active_players]}")
        
        # *** BROADCAST AUTOMÁTICO QUANDO JOGADOR SE JUNTA ***
        self.broadcast_players_info()
    
    def remove_player_info(self, player_id: str):
        """Remove jogador do sistema de broadcast"""
        if self.players_info and player_id in self.players_info:
            player_info = self.players_info[player_id]
            logger.info(f"[PLAYERS_INFO] *** JOGADOR REMOVIDO DO BROADCAST SYSTEM ***")
            logger.info(f"[PLAYERS_INFO] Jogador: {player_info['name']} ({player_info['color']}) - ID: {player_id}")
            
            del self.players_info[player_id]
            
        if self.active_players and player_id in self.active_players:
            self.active_players.remove(player_id)
            
        logger.info(f"[PLAYERS_INFO] Total jogadores ativos restantes: {len(self.active_players) if self.active_players else 0}")
        
        # *** BROADCAST AUTOMÁTICO QUANDO JOGADOR SAI ***
        if self.active_players:  # Só faz broadcast se ainda há jogadores
            self.broadcast_players_info()
    
    def broadcast_players_info(self):
        """Envia lista de jogadores para TODOS na sessão"""
        if not self.players_info or not self.active_players:
            logger.info(f"[PLAYERS_BROADCAST] Sem jogadores para broadcast")
            return
            
        players_data = {}
        
        for player_id, info in self.players_info.items():
            players_data[player_id] = {
                'color': info['color'],
                'name': info['name'],
                'is_active': player_id in self.active_players
            }
        
        message = {
            'type': 'players_info_sync',
            'players': players_data,
            'total_players': len(self.active_players),
            'session_id': self.id,
            'source': 'server'
        }
        
        logger.info(f"[PLAYERS_BROADCAST] *** ENVIANDO BROADCAST PARA {len(self.active_players)} JOGADORES ***")
        logger.info(f"[PLAYERS_BROADCAST] Dados enviados: {players_data}")
        
        # Enviar para TODOS os jogadores ativos
        for player_id in self.active_players:
            try:
                if player_id in self.players_info:
                    player_ws = self.players_info[player_id]['websocket']
                    asyncio.create_task(player_ws.send(json.dumps(message)))
                    logger.info(f"[PLAYERS_BROADCAST] Broadcast enviado para {self.players_info[player_id]['name']} ({self.players_info[player_id]['color']})")
            except Exception as e:
                logger.error(f"[PLAYERS_BROADCAST] ❌ Erro enviando para {player_id}: {e}")
    
    def get_players_summary(self) -> str:
        """Retorna resumo dos jogadores para logs"""
        if not self.players_info or not self.active_players:
            return "Nenhum jogador ativo"
            
        summary = []
        for player_id in self.active_players:
            if player_id in self.players_info:
                info = self.players_info[player_id]
                summary.append(f"{info['name']}({info['color']})")
                
        return ", ".join(summary)
    
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
        self.session_timers: Dict[str, dict] = {}  # session_id -> timer_info
        
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
        async with websockets.serve(
            self.handle_client, 
            SERVER_HOST, 
            SERVER_PORT
        ):
            logger.info(f"Servidor NetMaster ativo em ws://{SERVER_HOST}:{SERVER_PORT}")
            logger.info(f"Acesso público: ws://netmaster.vps.tecnico.ulisboa.pt:8000")
            await asyncio.Future()  # run forever
    
    async def handle_client(self, websocket):
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
            'get_session_info': self.handle_get_session_info,
            'end_turn': self.handle_end_turn,
            'timer_sync': self.handle_timer_sync,  # NOVO: Handler para sincronização do timer
            'store_card_for_player': self.handle_store_card_for_player,  # NOVO: Handler para armazenar carta
            'get_pending_cards': self.handle_get_pending_cards,  # NOVO: Handler para obter cartas pendentes
            'update_player_score': self.handle_update_player_score  # NOVO: Handler para atualizar saldo do jogador
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
            
            # *** ADICIONAR HOST AO SISTEMA DE BROADCAST ***
            session.add_player_info(player_id, player_color, player_name, websocket)
            
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
            
            # Limpar marcação de sessão vazia se existir
            if hasattr(session, 'empty_since') and session.empty_since:
                session.empty_since = None
                logger.info(f"Sessão {session_id} não está mais vazia - cancelando remoção automática")
            
            # Adicionar jogador à ordem de turnos
            session.add_player_to_order(player_id)
            
            # *** ADICIONAR JOGADOR AO SISTEMA DE BROADCAST ***
            session.add_player_info(player_id, color_enum.value, player_name, websocket)
            
            # Se é o segundo jogador, estender o tempo de espera
            if len(session.players) == 2 and session.state == GameState.WAITING:
                # Estender o tempo de espera para permitir mais jogadores se juntarem
                session.waiting_expires_at = datetime.now() + timedelta(minutes=1)  # 1 minuto adicional
                logger.info(f"Segundo jogador juntou-se à sessão {session_id}. Tempo de espera estendido para 1 minuto.")
            
            logger.info(f"{player_name} ({color_enum.value}) juntou-se à sessão {session_id}")
            
            # Responder ao novo jogador
            session_joined_message = {
                'type': 'session_joined',
                'session': session.to_dict(),
                'player_id': player_id,
                'player_info': new_player.to_dict()
            }
            logger.info(f"*** ENVIANDO SESSION_JOINED PARA {player_name} (ID: {player_id}) ***")
            logger.info(f"*** WEBSOCKET VÁLIDO: {not self.is_websocket_closed(websocket)} ***")
            logger.info(f"*** WEBSOCKET ORIGINAL: {websocket} ***")
            logger.info(f"*** CLIENT_ID MAPEADO: {client_id} ***")
            
            # Verificar se o client está na lista de conexões ativas
            connected_client = None
            for connected_id, connected_ws in self.connected_clients.items():
                if connected_id == client_id:
                    connected_client = connected_ws
                    logger.info(f"*** FOUND CLIENT {client_id} IN CONNECTED_CLIENTS: {connected_ws} ***")
                    break
            
            if connected_client is None:
                logger.error(f"*** ERRO: CLIENT {client_id} NÃO ENCONTRADO EM CONNECTED_CLIENTS! ***")
            elif connected_client != websocket:
                logger.error(f"*** ERRO: WEBSOCKET MISMATCH! ORIGINAL: {websocket}, MAPPED: {connected_client} ***")
            else:
                logger.info(f"*** WEBSOCKET MATCH OK - USANDO WEBSOCKET CORRETO ***")
            
            # TESTE: Verificar serialização JSON antes de enviar
            try:
                test_json = json.dumps(session_joined_message)
                logger.info(f"*** JSON SERIALIZATION TEST: PASSED - {len(test_json)} chars ***")
            except Exception as json_error:
                logger.error(f"*** JSON SERIALIZATION ERROR: {json_error} ***")
                logger.error(f"*** PROBLEMATIC MESSAGE: {session_joined_message} ***")
                # Tentar enviar uma mensagem simplificada
                fallback_message = {
                    'type': 'session_joined',
                    'player_id': player_id,
                    'success': True
                }
                logger.info(f"*** USANDO FALLBACK MESSAGE: {fallback_message} ***")
                session_joined_message = fallback_message
            
            # SOLUÇÃO CRÍTICA: Usar sempre o WebSocket da mensagem original
            # O problema pode estar em usar websockets diferentes
            original_websocket = websocket
            
            # Verificar qual cliente está enviando o join
            sender_client_id = None
            for cid, ws in self.connected_clients.items():
                if ws == websocket:
                    sender_client_id = cid
                    break
            
            if sender_client_id:
                logger.info(f"*** JOIN de cliente identificado: {sender_client_id} ***")
                # Usar SEMPRE o websocket do cliente que enviou a mensagem
                target_websocket = self.connected_clients[sender_client_id]
                logger.info(f"*** USANDO WEBSOCKET DO SENDER: {target_websocket} ***")
            else:
                logger.error(f"*** ERRO CRÍTICO: Cliente não encontrado para websocket {websocket} ***")
                logger.error(f"*** CONNECTED_CLIENTS: {list(self.connected_clients.keys())} ***")
                target_websocket = websocket
            
            # TESTE: Enviar uma mensagem simples primeiro para verificar conectividade
            test_message = {'type': 'test_connectivity', 'player_id': player_id}
            try:
                logger.info(f"*** TESTE DE CONECTIVIDADE ANTES DE SESSION_JOINED ***")
                await self.send_message(target_websocket, test_message)
                logger.info(f"*** TESTE DE CONECTIVIDADE PASSOU! ***")
            except Exception as test_error:
                logger.error(f"*** TESTE DE CONECTIVIDADE FALHOU: {test_error} ***")
                # Tentar encontrar outro websocket para este cliente
                logger.error(f"*** PROCURANDO WEBSOCKET ALTERNATIVO ***")
                for alt_cid, alt_ws in self.connected_clients.items():
                    if alt_cid != sender_client_id:
                        continue
                    try:
                        logger.info(f"*** TENTANDO WEBSOCKET ALTERNATIVO: {alt_ws} ***")
                        await self.send_message(alt_ws, test_message)
                        target_websocket = alt_ws
                        logger.info(f"*** WEBSOCKET ALTERNATIVO FUNCIONOU! ***")
                        break
                    except:
                        continue

            await self.send_message(target_websocket, session_joined_message)
            logger.info(f"*** SESSION_JOINED ENVIADO PARA {player_name} VIA WEBSOCKET: {target_websocket} ***")
            
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
            logger.info(f"*** HANDLE_LIST_SESSIONS CHAMADO POR {client_id} ***")
            logger.info(f"Total de sessões no servidor: {len(self.sessions)}")
            
            # Filtrar apenas sessões ativas e não cheias
            available_sessions = []
            for session_id, session in self.sessions.items():
                logger.info(f"Verificando sessão {session_id}:")
                logger.info(f"  - Estado: {session.state}")
                logger.info(f"  - Expirou: {session.is_expired()} (expires_at: {session.expires_at})")
                logger.info(f"  - Cheia: {session.is_full()} (players: {len(session.players)}/{session.max_players})")
                logger.info(f"  - Espera expirou: {session.is_waiting_expired()} (waiting_expires_at: {session.waiting_expires_at})")
                logger.info(f"  - Data atual: {datetime.now()}")
                
                if (session.state in [GameState.WAITING, GameState.STARTING] and 
                    not session.is_expired() and 
                    not session.is_full()):
                    logger.info(f"  Sessão {session_id} INCLUÍDA na lista")
                    available_sessions.append(session.to_dict())
                else:
                    logger.info(f"  ❌ Sessão {session_id} EXCLUÍDA da lista")
            
            logger.info(f"*** RESULTADO: {len(available_sessions)} sessões disponíveis de {len(self.sessions)} totais ***")

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
            
            # CRÍTICO: Preparar mensagem game_started
            game_started_message = {
                'type': 'game_started',
                'session': session.to_dict(),
                'message': 'O jogo começou!'
            }
            logger.info(f"*** ENVIANDO MENSAGEM game_started para sessão {session_id} ***")
            logger.info(f"Players na sessão: {list(session.players.keys())}")
            logger.info(f"Dados da mensagem: {game_started_message['type']}")
            
            # NOVA ABORDAGEM: Enviar game_started com retry individual e verificação de conexão
            successful_sends = 0
            failed_players = []
            
            for player_id, player in session.players.items():
                logger.info(f"GAME_STARTED: Enviando para {player.name} (ID: {player_id})")
                
                # Verificação detalhada da conexão
                if not player.websocket:
                    logger.error(f"GAME_STARTED: Player {player.name} sem websocket")
                    failed_players.append(player_id)
                    continue
                    
                if self.is_websocket_closed(player.websocket):
                    logger.error(f"GAME_STARTED: WebSocket de {player.name} está fechado")
                    player.connected = False
                    failed_players.append(player_id)
                    continue
                    
                if not player.connected:
                    logger.error(f"GAME_STARTED: Player {player.name} marcado como desconectado")
                    failed_players.append(player_id)
                    continue
                
                # Tentar enviar com retry e delay progressivo
                retry_count = 0
                max_retries = 3
                sent_successfully = False
                
                while retry_count < max_retries and not sent_successfully:
                    try:
                        # Delay crescente entre tentativas
                        if retry_count > 0:
                            delay = 0.5 * retry_count  # 0.5s, 1.0s, 1.5s
                            logger.info(f"GAME_STARTED: Aguardando {delay}s antes da tentativa {retry_count + 1}")
                            await asyncio.sleep(delay)
                        else:
                            # Pequeno delay inicial para evitar sobrecarga
                            await asyncio.sleep(0.1)
                        
                        # Verificar novamente se a conexão ainda está ativa
                        if self.is_websocket_closed(player.websocket):
                            logger.error(f"GAME_STARTED: WebSocket de {player.name} fechou durante retry")
                            player.connected = False
                            break
                        
                        await self.send_message(player.websocket, game_started_message)
                        logger.info(f"GAME_STARTED: Enviado para {player.name} (tentativa {retry_count + 1})")
                        successful_sends += 1
                        sent_successfully = True
                        
                    except Exception as send_error:
                        retry_count += 1
                        logger.error(f"GAME_STARTED: ❌ Erro enviando para {player.name} (tentativa {retry_count}): {send_error}")
                        
                        # Verificar se é erro de conexão fechada
                        if "closed" in str(send_error).lower() or "connection" in str(send_error).lower():
                            logger.error(f"GAME_STARTED: Conexão perdida para {player.name} - parando tentativas")
                            player.connected = False
                            break
                        
                        if retry_count < max_retries:
                            logger.info(f"GAME_STARTED: Tentando novamente para {player.name}...")
                        else:
                            logger.error(f"GAME_STARTED: Falha definitiva para {player.name} após {max_retries} tentativas")
                            player.connected = False
                            failed_players.append(player_id)
            
            logger.info(f"GAME_STARTED: {successful_sends} envios bem-sucedidos de {len(session.players)} jogadores")
            if failed_players:
                logger.warning(f"GAME_STARTED: Falhas para jogadores: {failed_players}")
            
            logger.info(f"*** MENSAGEM game_started PROCESSADA ***")
            
            # *** BROADCAST INICIAL DOS JOGADORES QUANDO JOGO COMEÇAR ***
            session.broadcast_players_info()
            logger.info(f"*** BROADCAST DE JOGADORES ENVIADO NO INÍCIO DO JOGO ***")
            
            # Iniciar timer controlado pelo servidor
            await self.start_session_timer(session_id, session.duration_minutes)
            logger.info(f"Timer do servidor iniciado para sessão {session_id} - {session.duration_minutes} minutos")
            
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
    
    async def handle_end_turn(self, client_id: str, websocket, data: dict):
        """Processa fim de turno e passa para o próximo jogador"""
        try:
            session_id = data.get('session_id')
            player_id = data.get('player_id')
            
            if not session_id or not player_id:
                await self.send_error(websocket, "session_id e player_id são obrigatórios")
                return
            
            session = self.sessions.get(session_id)
            if not session:
                await self.send_error(websocket, "Sessão não encontrada")
                return
            
            if session.state != GameState.PLAYING:
                await self.send_error(websocket, "Sessão não está em jogo")
                return
            
            # Verificar se é a vez do jogador
            current_player_id = session.get_current_player_id()
            if player_id != current_player_id:
                await self.send_error(websocket, "Não é o seu turno")
                return
            
            logger.info(f"Fim de turno do jogador {player_id} na sessão {session_id}")
            
            # Avançar para o próximo jogador
            session.next_turn()
            
            # Obter dados do novo jogador atual
            new_current_player_id = session.get_current_player_id()
            new_current_player = session.players.get(new_current_player_id)
            
            # Enviar notificação de mudança de turno para todos os jogadores
            turn_changed_message = {
                'type': 'turn_changed',
                'current_player_id': new_current_player_id,
                'current_player_name': new_current_player.name,
                'current_player_color': new_current_player.color.value if hasattr(new_current_player.color, 'value') else str(new_current_player.color),
                'player_order': session.player_order,
                'current_turn_index': session.current_turn_index,
                'session_id': session_id
            }
            
            logger.info(f"Enviando turn_changed: novo jogador {new_current_player.name} ({new_current_player_id})")
            await self.broadcast_to_session(session_id, turn_changed_message)
            
            # NOTA: Com o novo sistema, as cartas pendentes são obtidas automaticamente 
            # quando o jogador inicia sua interface (playerdashboard_interface)
            
            # Enviar confirmação para o jogador que terminou o turno
            await self.send_message(websocket, {
                'type': 'end_turn_ack',
                'success': True,
                'next_player_id': new_current_player_id,
                'next_player_name': new_current_player.name
            })
            
        except Exception as e:
            logger.error(f"Erro ao processar fim de turno: {e}")
            await self.send_error(websocket, f"Erro ao processar fim de turno: {str(e)}")
    
    async def start_session_timer(self, session_id: str, duration_minutes: int):
        """Inicia um timer controlado pelo servidor para uma sessão"""
        try:
            total_seconds = duration_minutes * 60
            timer_info = {
                'task': None,
                'start_time': time.time(),
                'duration_seconds': total_seconds,
                'remaining_seconds': total_seconds
            }
            
            # Cancelar timer anterior se existir
            if session_id in self.session_timers:
                old_timer = self.session_timers[session_id]
                if old_timer.get('task') and not old_timer['task'].done():
                    old_timer['task'].cancel()
            
            # Criar nova tarefa de timer
            timer_task = asyncio.create_task(self.run_session_timer(session_id, total_seconds))
            timer_info['task'] = timer_task
            self.session_timers[session_id] = timer_info
            
            logger.info(f"[SERVER_TIMER] Timer iniciado para sessão {session_id}: {duration_minutes}min ({total_seconds}s)")
            
        except Exception as e:
            logger.error(f"Erro ao iniciar timer da sessão {session_id}: {e}")
    
    async def run_session_timer(self, session_id: str, total_seconds: int):
        """Executa o timer da sessão enviando atualizações a cada segundo"""
        try:
            remaining = total_seconds
            
            while remaining > 0 and session_id in self.sessions:
                session = self.sessions.get(session_id)
                if not session or session.state != GameState.PLAYING:
                    logger.info(f"[SERVER_TIMER] Sessão {session_id} não está mais a jogar - parando timer")
                    break
                
                # Atualizar info do timer
                if session_id in self.session_timers:
                    self.session_timers[session_id]['remaining_seconds'] = remaining
                
                # Enviar atualização do timer para todos os jogadores
                timer_message = {
                    'type': 'timer_sync',
                    'time_remaining': remaining,
                    'source': 'server'
                }
                
                await self.broadcast_to_session(session_id, timer_message)
                logger.info(f"[SERVER_TIMER] Enviado timer_sync para sessão {session_id}: {remaining}s restantes")
                
                # Aguardar 1 segundo
                await asyncio.sleep(1)
                remaining -= 1
            
            # Timer expirou
            if remaining <= 0:
                logger.info(f"[SERVER_TIMER] Timer expirou para sessão {session_id}")
                await self.handle_session_timeout(session_id)
            
        except asyncio.CancelledError:
            logger.info(f"[SERVER_TIMER] Timer cancelado para sessão {session_id}")
        except Exception as e:
            logger.error(f"[SERVER_TIMER] Erro no timer da sessão {session_id}: {e}")
        finally:
            # Limpar timer
            if session_id in self.session_timers:
                del self.session_timers[session_id]
    
    async def handle_session_timeout(self, session_id: str):
        """Lida com o timeout de uma sessão"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return
            
            logger.info(f"[SERVER_TIMER] Sessão {session_id} expirou por timeout")
            
            # Marcar como processado pelo timer para evitar processamento duplo pelo cleanup
            session.timer_finished = True
            logger.info(f"[SERVER_TIMER] Sessão {session_id} marcada como timer_finished")
            
            # Marcar sessão como expirada
            session.state = GameState.EXPIRED
            
            # CORREÇÃO: Calcular vencedor e enviar game_finished ao invés de session_timeout
            if len(session.players) > 0:
                game_result = self.calculate_game_winner(session)
                
                if game_result:
                    logger.info(f"Resultado final da sessão {session_id} (timer expirado):")
                    logger.info(f"  Vencedor: {game_result['winner']['player_name']} ({game_result['winner']['score']} pontos)")
                    
                    # Notificar jogadores sobre o resultado final
                    game_finished_message = {
                        'type': 'game_finished',
                        'message': 'Jogo terminado! Vencedor determinado por maior saldo.',
                        'timeout_reason': 'timer_expired',
                        'game_result': game_result
                    }
                    
                    await self.broadcast_to_session(session_id, game_finished_message)
                    logger.info(f"[SERVER_TIMER] ✓ Enviado game_finished para sessão {session_id}")
                    
                    # Aguardar um pouco para garantir que a mensagem é entregue
                    await asyncio.sleep(2)
                else:
                    # Fallback para caso não seja possível calcular vencedor
                    fallback_message = {
                        'type': 'game_finished',
                        'message': 'Jogo terminado! Tempo esgotado.',
                        'timeout_reason': 'timer_expired'
                    }
                    
                    await self.broadcast_to_session(session_id, fallback_message)
                    logger.info(f"[SERVER_TIMER] ✓ Enviado game_finished (fallback) para sessão {session_id}")
            
            # Remover sessão após algum tempo
            await asyncio.sleep(3)
            await self.cleanup_session(session_id)
            
        except Exception as e:
            logger.error(f"Erro ao lidar com timeout da sessão {session_id}: {e}")
    
    async def cleanup_session(self, session_id: str):
        """Remove completamente uma sessão"""
        try:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                
                # Remover jogadores do mapeamento
                for player_id in list(session.players.keys()):
                    if player_id in self.player_to_session:
                        del self.player_to_session[player_id]
                
                # Remover sessão
                del self.sessions[session_id]
                
                # Cancelar timer se existir
                if session_id in self.session_timers:
                    timer_info = self.session_timers[session_id]
                    if timer_info.get('task') and not timer_info['task'].done():
                        timer_info['task'].cancel()
                    del self.session_timers[session_id]
                
                logger.info(f"[SERVER_TIMER] Sessão {session_id} removida completamente")
                
                # Atualizar lista de sessões
                await self.broadcast_session_list_update()
                
        except Exception as e:
            logger.error(f"Erro ao limpar sessão {session_id}: {e}")
    
    async def handle_timer_sync(self, client_id: str, websocket, data: dict):
        """Handler para timer_sync - agora controlado pelo servidor, ignora tentativas dos clientes"""
        try:
            # O timer é agora controlado pelo servidor, ignorar tentativas dos clientes
            logger.info(f"[SERVER_TIMER] Cliente {client_id} tentou enviar timer_sync - ignorado (timer controlado pelo servidor)")
            
            # Enviar resposta informativa
            await self.send_message(websocket, {
                'type': 'timer_sync_response',
                'message': 'Timer é controlado pelo servidor',
                'server_controlled': True
            })
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem timer_sync: {e}")
    
    def return_card_to_store(self, card_data: dict, session_id: str) -> bool:
        """
        Devolve uma carta ao baralho correspondente na Store quando não pode ser entregue
        
        Args:
            card_data: Dados da carta incluindo card_path e card_type
            session_id: ID da sessão
            
        Returns:
            bool: True se sucesso, False se erro
        """
        try:
            card_path = card_data.get('card_path', '')
            card_type = card_data.get('card_type', '')
            
            logger.info(f"[RETURN_TO_STORE] Devolvendo carta à Store:")
            logger.info(f"[RETURN_TO_STORE]   Carta: {card_path}")
            logger.info(f"[RETURN_TO_STORE]   Tipo: {card_type}")
            logger.info(f"[RETURN_TO_STORE]   Sessão: {session_id}")
            
            # Obter a sessão
            if session_id not in self.sessions:
                logger.error(f"[RETURN_TO_STORE] Sessão {session_id} não encontrada")
                return False
                
            session = self.sessions[session_id]
            
            # Devolver carta ao baralho correspondente na Store da sessão
            if card_type == 'actions':
                # Actions voltam para o baralho Actions da Store
                if not hasattr(session, 'store_actions_deck'):
                    session.store_actions_deck = []
                session.store_actions_deck.append(card_path)
                logger.info(f"[RETURN_TO_STORE] Action devolvida ao baralho Actions da Store")
                
            elif card_type == 'events':
                # Events voltam para o baralho Events da Store  
                if not hasattr(session, 'store_events_deck'):
                    session.store_events_deck = []
                session.store_events_deck.append(card_path)
                logger.info(f"[RETURN_TO_STORE] Event devolvido ao baralho Events da Store")
                
            else:
                logger.error(f"[RETURN_TO_STORE] Tipo de carta desconhecido: {card_type}")
                return False
            
            logger.info(f"[RETURN_TO_STORE] SUCCESS: Carta devolvida com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"[RETURN_TO_STORE] ERRO: {e}")
            return False
    
    async def handle_store_card_for_player(self, client_id: str, websocket, data: dict):
        """NOVO SISTEMA: Handler para armazenar carta no servidor para entrega posterior"""
        try:
            sender_player_id = data.get('sender_player_id')
            sender_color = data.get('sender_color')
            target_player_color = data.get('target_player_color')
            target_player_id = data.get('target_player_id')
            card_data = data.get('card_data', {})
            
            logger.info(f"[CARD_STORAGE] Armazenando carta de {sender_color} para {target_player_color}")
            logger.info(f"[CARD_STORAGE] Carta: {card_data.get('card_path', 'Unknown')}")
            
            # Verificar dados necessários
            if not all([sender_player_id, sender_color, target_player_color, card_data]):
                logger.error(f"[CARD_STORAGE] Dados incompletos")
                await self.send_error(websocket, "Dados incompletos para armazenar carta")
                return
            
            # Encontrar a sessão do jogador remetente
            session_id = self.player_to_session.get(sender_player_id)
            if not session_id or session_id not in self.sessions:
                logger.error(f"[CARD_STORAGE] Sessão não encontrada para jogador {sender_color}")
                await self.send_error(websocket, "Sessão não encontrada")
                return
            
            session = self.sessions[session_id]
            
            # Verificar se o jogador alvo existe na mesma sessão
            target_player_found = False
            for player in session.players.values():
                if player.color.value == target_player_color:
                    target_player_found = True
                    break
            
            if not target_player_found:
                logger.error(f"[CARD_STORAGE] Jogador alvo {target_player_color} não encontrado na sessão")
                logger.info(f"[CARD_STORAGE] SOLUÇÃO: Devolvendo carta ao baralho da Store")
                
                # CORREÇÃO CRÍTICA: Devolver carta à Store em vez de perder
                success = self.return_card_to_store(card_data, session_id)
                
                if success:
                    logger.info(f"[CARD_STORAGE] SUCCESS: Carta devolvida à Store com sucesso")
                    await self.send_message(websocket, {
                        'type': 'card_returned_to_store',
                        'reason': 'target_player_not_in_session',
                        'message': f'Player {target_player_color} not in session. Card returned to store.',
                        'card_path': card_data.get('card_path', ''),
                        'card_type': card_data.get('card_type', ''),
                        'status': 'returned_to_store'
                    })
                else:
                    logger.error(f"[CARD_STORAGE] ERRO: Falha ao devolver carta à Store")
                    await self.send_error(websocket, "Failed to return card to store")
                
                return
            
            # Armazenar carta na sessão
            session.store_card_for_player(target_player_color, card_data)
            
            # Confirmar sucesso para o remetente
            await self.send_message(websocket, {
                'type': 'card_stored_confirmation',
                'target_player_color': target_player_color,
                'card_type': card_data.get('card_type', 'Unknown'),
                'status': 'stored',
                'message': f"Carta armazenada para {target_player_color}"
            })
            
        except Exception as e:
            logger.error(f"[CARD_STORAGE] Erro ao armazenar carta: {e}")
            await self.send_error(websocket, f"Erro ao armazenar carta: {str(e)}")
    
    async def handle_get_pending_cards(self, client_id: str, websocket, data: dict):
        """NOVO SISTEMA: Handler para obter cartas pendentes de um jogador"""
        try:
            player_id = data.get('player_id')
            player_color = data.get('player_color')
            
            logger.info(f"[CARD_DELIVERY] Solicitação de cartas pendentes de {player_color}")
            
            # Verificar dados necessários
            if not all([player_id, player_color]):
                logger.error(f"[CARD_DELIVERY] Dados incompletos")
                await self.send_error(websocket, "Dados incompletos para obter cartas")
                return
            
            # Encontrar a sessão do jogador
            session_id = self.player_to_session.get(player_id)
            if not session_id or session_id not in self.sessions:
                logger.error(f"[CARD_DELIVERY] Sessão não encontrada para jogador {player_color}")
                await self.send_error(websocket, "Sessão não encontrada")
                return
            
            session = self.sessions[session_id]
            
            # Obter cartas pendentes
            pending_cards = session.get_pending_cards(player_color)
            
            # Enviar resposta com cartas pendentes
            await self.send_message(websocket, {
                'type': 'pending_cards',
                'cards': pending_cards
            })
            
        except Exception as e:
            logger.error(f"[CARD_DELIVERY] Erro ao obter cartas pendentes: {e}")
            await self.send_error(websocket, f"Erro ao obter cartas pendentes: {str(e)}")
    
    async def handle_update_player_score(self, client_id: str, websocket, data: dict):
        """Atualiza o saldo/score de um jogador"""
        try:
            player_id = data.get('player_id')
            new_score = data.get('score')
            session_id = data.get('session_id')
            
            logger.info(f"[SCORE_SYNC] Atualização de saldo: jogador {player_id}, novo saldo: {new_score}")
            
            if not player_id or new_score is None:
                await self.send_error(websocket, "player_id e score são obrigatórios")
                return
            
            # Se session_id não foi fornecido, tentar encontrá-lo através do player_id
            if not session_id:
                session_id = self.player_to_session.get(player_id)
            
            if not session_id or session_id not in self.sessions:
                logger.error(f"[SCORE_SYNC] Sessão não encontrada para jogador {player_id}")
                await self.send_error(websocket, "Sessão não encontrada")
                return
            
            session = self.sessions[session_id]
            player = session.players.get(player_id)
            
            if not player:
                logger.error(f"[SCORE_SYNC] Jogador {player_id} não encontrado na sessão {session_id}")
                await self.send_error(websocket, "Jogador não encontrado na sessão")
                return
            
            # Atualizar o saldo do jogador no servidor
            old_score = player.score
            player.score = new_score
            
            logger.info(f"[SCORE_SYNC] ✓ Saldo atualizado: {player.name} ({player_id}): {old_score} → {new_score}")
            
            # Enviar confirmação
            await self.send_message(websocket, {
                'type': 'score_updated',
                'player_id': player_id,
                'old_score': old_score,
                'new_score': new_score,
                'success': True
            })
            
        except Exception as e:
            logger.error(f"[SCORE_SYNC] Erro ao atualizar saldo do jogador: {e}")
            await self.send_error(websocket, f"Erro ao atualizar saldo: {str(e)}")
    
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
    
    def is_websocket_closed(self, websocket):
        """Verifica se websocket está fechado (compatível com diferentes versões)"""
        try:
            # Versão nova do websockets
            return websocket.close_code is not None
        except AttributeError:
            try:
                # Versão antiga
                return websocket.closed
            except AttributeError:
                # Fallback: assumir que está aberto
                return False
    
    async def send_message(self, websocket, message: dict):
        """Envia mensagem para um websocket"""
        try:
            message_type = message.get('type', 'UNKNOWN')
            
            # Log especial para session_joined
            if message_type == 'session_joined':
                logger.info(f"*** SEND_MESSAGE: Enviando SESSION_JOINED ***")
                logger.info(f"*** WEBSOCKET: {websocket} ***")
                logger.info(f"*** WEBSOCKET CLOSED: {self.is_websocket_closed(websocket)} ***")
                logger.info(f"*** MESSAGE: {message} ***")
            
            # Verificar se websocket ainda está aberto
            if self.is_websocket_closed(websocket):
                logger.error(f"SEND_MESSAGE: WebSocket está fechado - não é possível enviar")
                raise websockets.exceptions.ConnectionClosed(None, None)
            
            # Testar serialização JSON antes de enviar
            json_message = json.dumps(message)
            
            if message_type == 'session_joined':
                logger.info(f"*** JSON_MESSAGE: {json_message[:200]}... ***")
            
            # Enviar com timeout
            logger.info(f"*** INICIANDO WEBSOCKET.SEND() PARA {message_type} ***")
            await asyncio.wait_for(websocket.send(json_message), timeout=5.0)
            logger.info(f"*** WEBSOCKET.SEND() COMPLETADO PARA {message_type} ***")
            
            if message_type == 'session_joined':
                logger.info(f"*** SESSION_JOINED ENVIADO COM SUCESSO! ***")
                
                # EXTRA: Verificar se a conexão ainda está ativa após envio
                logger.info(f"*** POST-SEND: WEBSOCKET CLOSED: {self.is_websocket_closed(websocket)} ***")
                try:
                    logger.info(f"*** POST-SEND: WEBSOCKET STATE: {websocket.state} ***")
                except AttributeError:
                    logger.info("*** POST-SEND: WEBSOCKET STATE: Não disponível ***")
            
        except asyncio.TimeoutError:
            logger.error(f"SEND_MESSAGE: Timeout ao enviar mensagem tipo {message.get('type', 'UNKNOWN')}")
            raise Exception("Timeout ao enviar mensagem")
        except websockets.exceptions.ConnectionClosed:
            logger.error(f"SEND_MESSAGE: Conexão WebSocket fechada para mensagem tipo {message.get('type', 'UNKNOWN')}")
            raise Exception("Conexão WebSocket fechada")
        except TypeError as json_error:
            logger.error(f"SEND_MESSAGE: Erro de serialização JSON: {json_error}")
            logger.error(f"SEND_MESSAGE: Mensagem problemática: {message}")
            raise json_error
        except Exception as e:
            logger.error(f"SEND_MESSAGE: Erro geral ao enviar mensagem: {e}")
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
            logger.error(f"BROADCAST_ERROR: Sessão {session_id} não encontrada")
            return
        
        logger.info(f"BROADCAST_TO_SESSION: Enviando {message.get('type')} para sessão {session_id}")
        logger.info(f"BROADCAST_TO_SESSION: Players na sessão: {list(session.players.keys())}")
        logger.info(f"BROADCAST_TO_SESSION: Exclude player: {exclude_player}")
        
        for player_id, player in session.players.items():
            if exclude_player and player_id == exclude_player:
                logger.info(f"BROADCAST_TO_SESSION: Pulando player excluído: {player_id}")
                continue
            
            logger.info(f"BROADCAST_TO_SESSION: Tentando enviar para {player.name} (ID: {player_id})")
            logger.info(f"BROADCAST_TO_SESSION: - WebSocket exists: {player.websocket is not None}")
            logger.info(f"BROADCAST_TO_SESSION: - Player connected: {player.connected}")
            
            if player.websocket and player.connected:
                try:
                    await self.send_message(player.websocket, message)
                    logger.info(f"BROADCAST_TO_SESSION: Mensagem enviada para {player.name}")
                except Exception as send_error:
                    logger.error(f"BROADCAST_TO_SESSION: ❌ Erro ao enviar para {player.name}: {send_error}")
                    # Marcar jogador como desconectado
                    player.connected = False
            else:
                logger.warning(f"BROADCAST_TO_SESSION: Player {player.name} sem websocket ou desconectado")
    
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
        
        # *** REMOVER JOGADOR DO SISTEMA DE BROADCAST ***
        session.remove_player_info(player_id)
        
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
        
        # Se não há mais jogadores, marcar para remoção adiada
        if not session.players:
            # MUDANÇA: Não remover imediatamente - dar tempo para reconexão
            session.empty_since = time.time()
            session.state = GameState.WAITING  # Voltar para waiting para permitir novos joins
            logger.info(f"Sessão {session_id} ficou vazia - marcada para remoção em 30 segundos")
            
            # Agendar remoção após 30 segundos se ainda estiver vazia
            async def delayed_removal():
                await asyncio.sleep(30)  # Aguardar 30 segundos
                if (session_id in self.sessions and 
                    not self.sessions[session_id].players and 
                    hasattr(self.sessions[session_id], 'empty_since')):
                    del self.sessions[session_id]
                    logger.info(f"Sessão {session_id} removida após 30s vazia")
                    await self.broadcast_session_list_update()
            
            asyncio.create_task(delayed_removal())
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
                    
                    # NOVO: Verificar se esta sessão já foi processada pelo timer
                    if getattr(session, 'timer_finished', False):
                        logger.info(f"Sessão {session_id} já foi processada pelo timer, pulando cleanup")
                        continue
                        
                    logger.info(f"Sessão {session_id} expirou por tempo total de jogo (cleanup)")
                    
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
