"""
History Manager - управление историей диалогов
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from core.config import HistoryConfig

logger = logging.getLogger("AIAssistant.History")


class DialogMessage:
    """Сообщение в диалоге"""
    
    def __init__(self, role: str, content: str, timestamp: Optional[str] = None):
        self.role = role 
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'DialogMessage':
        return DialogMessage(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp")
        )


class DialogSession:
    """Сессия диалога"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.created_at = datetime.now().isoformat()
        self.messages: List[DialogMessage] = []
        self.stats = {
            "total_questions": 0,
            "total_tokens": 0,
            "avg_tokens_per_sec": 0.0,
            "total_time": 0.0
        }
    
    def add_message(self, role: str, content: str):
        """Добавить сообщение"""
        msg = DialogMessage(role, content)
        self.messages.append(msg)
        
        if role == "user":
            self.stats["total_questions"] += 1
    
    def update_stats(self, tokens: int, tokens_per_sec: float, time_sec: float):
        """Обновить статистику"""
        self.stats["total_tokens"] += tokens
        self.stats["total_time"] += time_sec
        
        # Средний t/s
        total_gens = self.stats["total_questions"]
        if total_gens > 0:
            current_avg = self.stats["avg_tokens_per_sec"]
            self.stats["avg_tokens_per_sec"] = (
                (current_avg * (total_gens - 1) + tokens_per_sec) / total_gens
            )
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "messages": [msg.to_dict() for msg in self.messages],
            "stats": self.stats
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'DialogSession':
        session = DialogSession(session_id=data["session_id"])
        session.created_at = data.get("created_at", "")
        session.messages = [
            DialogMessage.from_dict(msg) for msg in data.get("messages", [])
        ]
        session.stats = data.get("stats", {})
        return session


class HistoryManager:
    """Менеджер истории диалогов"""
    
    def __init__(self):
        self.current_session: Optional[DialogSession] = None
        self.history_dir = HistoryConfig.HISTORY_DIR
        logger.info(f"History directory: {self.history_dir}")
    
    def start_new_session(self) -> DialogSession:
        """Начать новую сессию"""
        self.current_session = DialogSession()
        logger.info(f"New session started: {self.current_session.session_id}")
        return self.current_session
    
    def add_message(self, role: str, content: str):
        """Добавить сообщение в текущую сессию"""
        if not self.current_session:
            self.start_new_session()
        
        self.current_session.add_message(role, content)
        logger.debug(f"Message added: {role}")
    
    def update_stats(self, tokens: int, tokens_per_sec: float, time_sec: float):
        """Обновить статистику текущей сессии"""
        if self.current_session:
            self.current_session.update_stats(tokens, tokens_per_sec, time_sec)
    
    def save_session(self, session: Optional[DialogSession] = None) -> bool:
        """
        Сохранить сессию в файл
        
        Args:
            session: Сессия для сохранения (или текущая)
            
        Returns:
            True если успешно
        """
        session = session or self.current_session
        
        if not session or not session.messages:
            logger.warning("No session to save or session is empty")
            return False
        
        try:
            filename = f"session_{session.session_id}.json"
            filepath = self.history_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Session saved: {filepath}")
            
            self._cleanup_old_files()
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to save session: {e}", exc_info=True)
            return False
    
    def load_session(self, session_id: str) -> Optional[DialogSession]:
        """
        Загрузить сессию из файла
        
        Args:
            session_id: ID сессии
            
        Returns:
            DialogSession или None
        """
        try:
            filename = f"session_{session_id}.json"
            filepath = self.history_dir / filename
            
            if not filepath.exists():
                logger.warning(f"Session file not found: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            session = DialogSession.from_dict(data)
            logger.info(f"Session loaded: {session_id}")
            return session
        
        except Exception as e:
            logger.error(f"Failed to load session: {e}", exc_info=True)
            return None
    
    def list_sessions(self) -> List[Dict]:
        """
        Получить список всех сессий
        
        Returns:
            Список словарей с метаданными сессий
        """
        sessions = []
        
        try:
            for filepath in sorted(self.history_dir.glob("session_*.json"), reverse=True):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    sessions.append({
                        "session_id": data["session_id"],
                        "created_at": data.get("created_at", ""),
                        "message_count": len(data.get("messages", [])),
                        "stats": data.get("stats", {}),
                        "filepath": str(filepath)
                    })
                
                except Exception as e:
                    logger.warning(f"Failed to read session file {filepath}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
        
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Удалить сессию"""
        try:
            filename = f"session_{session_id}.json"
            filepath = self.history_dir / filename
            
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Session deleted: {session_id}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False
    
    def export_session_to_text(self, session: DialogSession) -> str:
        """
        Экспортировать сессию в текстовый формат
        
        Args:
            session: Сессия для экспорта
            
        Returns:
            Текстовое представление
        """
        lines = [
            f"Session: {session.session_id}",
            f"Created: {session.created_at}",
            f"Total Questions: {session.stats.get('total_questions', 0)}",
            f"Total Tokens: {session.stats.get('total_tokens', 0)}",
            f"Avg Speed: {session.stats.get('avg_tokens_per_sec', 0):.2f} t/s",
            "=" * 60,
            ""
        ]
        
        for msg in session.messages:
            role_label = "Q:" if msg.role == "user" else "A:"
            lines.append(f"{role_label} {msg.content}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _cleanup_old_files(self):
        """Удалить старые файлы истории (превышающие лимит)"""
        try:
            files = sorted(self.history_dir.glob("session_*.json"), key=lambda p: p.stat().st_mtime)
            
            if len(files) > HistoryConfig.MAX_HISTORY_FILES:
                to_delete = len(files) - HistoryConfig.MAX_HISTORY_FILES
                
                for filepath in files[:to_delete]:
                    filepath.unlink()
                    logger.info(f"Deleted old session: {filepath.name}")
        
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
