"""
Notification Manager - управление уведомлениями
"""
import logging
from typing import Optional
from PyQt6.QtWidgets import QSystemTrayIcon

logger = logging.getLogger("AIAssistant.Notifications")


class NotificationManager:
    """
    Менеджер Windows notifications через system tray
    """
    
    def __init__(self, tray_icon: Optional[QSystemTrayIcon] = None):
        """
        Args:
            tray_icon: QSystemTrayIcon для показа notifications
        """
        self.tray_icon = tray_icon
        self.enabled = True
        self.sound_enabled = False
        
        logger.info("NotificationManager initialized")
    
    def set_tray_icon(self, tray_icon: QSystemTrayIcon):
        """Установить tray icon"""
        self.tray_icon = tray_icon
    
    def set_enabled(self, enabled: bool):
        """Включить/выключить notifications"""
        self.enabled = enabled
        logger.info(f"Notifications {'enabled' if enabled else 'disabled'}")
    
    def set_sound_enabled(self, enabled: bool):
        """Включить/выключить звук"""
        self.sound_enabled = enabled
    
    def show_info(self, title: str, message: str, duration: int = 3000):
        """
        Показать информационное уведомление
        
        Args:
            title: Заголовок
            message: Текст
            duration: Длительность в мс
        """
        if not self.enabled or not self.tray_icon:
            return
        
        self.tray_icon.showMessage(
            title,
            message,
            QSystemTrayIcon.MessageIcon.Information,
            duration
        )
        
        logger.info(f"Notification shown: {title}")
    
    def show_warning(self, title: str, message: str, duration: int = 5000):
        """Показать предупреждение"""
        if not self.enabled or not self.tray_icon:
            return
        
        self.tray_icon.showMessage(
            title,
            message,
            QSystemTrayIcon.MessageIcon.Warning,
            duration
        )
    
    def show_error(self, title: str, message: str, duration: int = 5000):
        """Показать ошибку"""
        if not self.enabled or not self.tray_icon:
            return
        
        self.tray_icon.showMessage(
            title,
            message,
            QSystemTrayIcon.MessageIcon.Critical,
            duration
        )
    
    def notify_question_detected(self, question: str):
        """Уведомление: обнаружен вопрос"""
        self.show_info(
            "Question Detected",
            f"Processing: {question[:50]}...",
            duration=2000
        )
    
    def notify_answer_ready(self, answer_preview: str):
        """Уведомление: ответ готов"""
        self.show_info(
            "Answer Ready",
            f"{answer_preview[:100]}...",
            duration=3000
        )
    
    def notify_listening_started(self):
        """Уведомление: started listening"""
        self.show_info(
            "Listening Started",
            "AI Assistant is now listening...",
            duration=2000
        )
    
    def notify_listening_stopped(self):
        """Уведомление: stopped listening"""
        self.show_info(
            "Listening Stopped",
            "AI Assistant stopped listening",
            duration=2000
        )
