"""
Hotkeys Manager - управление глобальными горячими клавишами
"""
import logging
from typing import Dict, Callable, Optional
from PyQt6.QtCore import QObject, pyqtSignal
import keyboard

logger = logging.getLogger("AIAssistant.Hotkeys")


class HotkeysManager(QObject):
    """
    Менеджер глобальных горячих клавиш
    Использует библиотеку keyboard для Windows hotkeys
    """
    
    toggle_window_requested = pyqtSignal()
    toggle_listening_requested = pyqtSignal()
    quick_input_requested = pyqtSignal()
    stop_generation_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        self.hotkeys_registered = False
        self.registered_hotkeys: Dict[str, str] = {}
        
        logger.info("HotkeysManager initialized")
    
    def register_hotkeys(self, hotkeys_config: Dict[str, str]) -> bool:
        """
        Зарегистрировать глобальные hotkeys
        
        Args:
            hotkeys_config: Словарь {action: hotkey}
                Например: {"toggle_window": "ctrl+shift+a"}
        
        Returns:
            True если успешно
        """
        try:
            self.unregister_all()
            
            for action, hotkey in hotkeys_config.items():
                if not hotkey:  
                    continue
                
                # Получить callback для действия
                callback = self._get_callback_for_action(action)
                
                if callback:
                    keyboard.add_hotkey(hotkey, callback, suppress=False)
                    self.registered_hotkeys[hotkey] = action
                    logger.info(f"Registered hotkey: {hotkey} -> {action}")
            
            self.hotkeys_registered = True
            logger.info(f"Registered {len(self.registered_hotkeys)} hotkeys")
            return True
        
        except Exception as e:
            logger.error(f"Failed to register hotkeys: {e}", exc_info=True)
            return False
    
    def _get_callback_for_action(self, action: str) -> Optional[Callable]:
        """Получить callback для действия"""
        callbacks = {
            "toggle_window": lambda: self.toggle_window_requested.emit(),
            "toggle_listening": lambda: self.toggle_listening_requested.emit(),
            "quick_input": lambda: self.quick_input_requested.emit(),
            "stop_generation": lambda: self.stop_generation_requested.emit(),
        }
        
        return callbacks.get(action)
    
    def unregister_all(self):
        """Отменить регистрацию всех hotkeys"""
        if not self.hotkeys_registered:
            return
        
        try:
            for hotkey in self.registered_hotkeys.keys():
                keyboard.remove_hotkey(hotkey)
            
            self.registered_hotkeys.clear()
            self.hotkeys_registered = False
            
            logger.info("All hotkeys unregistered")
        
        except Exception as e:
            logger.error(f"Error unregistering hotkeys: {e}")
    
    def is_hotkey_available(self, hotkey: str) -> bool:
        """
        Проверить доступность hotkey (не занят ли системой)
        
        Args:
            hotkey: Комбинация клавиш (например "ctrl+shift+a")
        
        Returns:
            True если доступен
        """
        try:
            keyboard.add_hotkey(hotkey, lambda: None)
            keyboard.remove_hotkey(hotkey)
            return True
        except:
            return False


DEFAULT_HOTKEYS = {
    "toggle_window": "ctrl+shift+a",
    "toggle_listening": "ctrl+shift+s",
    "quick_input": "ctrl+shift+q",
    "stop_generation": "ctrl+shift+x",
}
