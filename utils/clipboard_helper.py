"""
Clipboard Helper - работа с буфером обмена
"""
import logging
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger("AIAssistant.Clipboard")


class ClipboardHelper:
    """Помощник для работы с буфером обмена"""
    
    @staticmethod
    def copy_to_clipboard(text: str) -> bool:
        """
        Скопировать текст в буфер обмена
        
        Args:
            text: Текст для копирования
            
        Returns:
            True если успешно
        """
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            logger.info(f"Copied to clipboard: {len(text)} chars")
            return True
        
        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}")
            return False
    
    @staticmethod
    def get_from_clipboard() -> str:
        """
        Получить текст из буфера обмена
        
        Returns:
            Текст из буфера
        """
        try:
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            logger.debug(f"Read from clipboard: {len(text)} chars")
            return text
        
        except Exception as e:
            logger.error(f"Failed to read from clipboard: {e}")
            return ""
