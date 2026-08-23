"""
shared_state.py
Almacena datos en memoria que comparten el bot y el dashboard.
NO MODIFICAR ESTE ARCHIVO A MENOS QUE SEPAS LO QUE HACES.
"""
from typing import Dict, Any, List
from datetime import datetime
class SharedState:
    def __init__(self):
        self.bot_ready: bool = False
        self.bot_user: str = "Conectando..."
        self.bot_avatar: str = ""
        self.guild_count: int = 0
        self.member_count: int = 0
        self.ping_ms: float = 0.0
        self.commands_used: int = 0
        self.start_time: datetime = datetime.now()
        self.last_command: str = "Ninguno aún"
        self.guilds_list: List[Dict[str, Any]] = []
        self.recent_logs: List[str] = []
        
    def add_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.recent_logs.insert(0, f"[{timestamp}] {message}")
        if len(self.recent_logs) > 50:
            self.recent_logs.pop()
    
    def get_uptime(self) -> str:
        delta = datetime.now() - self.start_time
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{days}d {hours}h {minutes}m {seconds}s"
# Instancia global - importar esto en bot.py y dashboard.py
state = SharedState()
