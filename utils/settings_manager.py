"""
Управление настройками приложения через QSettings
"""
from PyQt6.QtCore import QSettings
from typing import Any, Optional
from core.config import AppConfig
import logging

logger = logging.getLogger("AIAssistant.Settings")


class SettingsManager:
    """Wrapper над QSettings для удобного доступа"""
    
    def __init__(self):
        self.settings = QSettings(AppConfig.COMPANY_NAME, AppConfig.APP_NAME)
        logger.info(f"Settings location: {self.settings.fileName()}")
    
    def get_window_geometry(self) -> Optional[bytes]:
        return self.settings.value("general/window_geometry")
    
    def set_window_geometry(self, geometry: bytes):
        self.settings.setValue("general/window_geometry", geometry)
    
    def get_window_opacity(self) -> float:
        return float(self.settings.value("general/window_opacity", AppConfig.WINDOW_OPACITY))
    
    def set_window_opacity(self, opacity: float):
        self.settings.setValue("general/window_opacity", opacity)
    
    def is_first_run(self) -> bool:
        return self.settings.value("general/first_run", True, type=bool)
    
    def set_first_run(self, value: bool):
        self.settings.setValue("general/first_run", value)
    
    def get_model_path(self) -> Optional[str]:
        return self.settings.value("models/llm_model_path")
    
    def set_model_path(self, path: str):
        self.settings.setValue("models/llm_model_path", path)
    
    def is_model_loaded(self) -> bool:
        return self.settings.value("models/llm_loaded", False, type=bool)
    
    def set_model_loaded(self, loaded: bool):
        self.settings.setValue("models/llm_loaded", loaded)
    
    def get_temperature(self) -> float:
        return float(self.settings.value("generation/temperature", 0.4))
    
    def set_temperature(self, temp: float):
        self.settings.setValue("generation/temperature", temp)
    
    def get_max_tokens(self) -> int:
        return int(self.settings.value("generation/max_tokens", 150))
    
    def set_max_tokens(self, tokens: int):
        self.settings.setValue("generation/max_tokens", tokens)
    
    def sync(self):
        """Принудительно сохранить все настройки"""
        self.settings.sync()
        logger.debug("Settings synced to disk")

    def get_hotkey(self, action: str) -> str:
        """Получить hotkey для действия"""
        from utils.hotkeys_manager import DEFAULT_HOTKEYS
        default = DEFAULT_HOTKEYS.get(action, "")
        return self.settings.value(f"hotkeys/{action}", default)

    def set_hotkey(self, action: str, hotkey: str):
        """Установить hotkey для действия"""
        self.settings.setValue(f"hotkeys/{action}", hotkey)

    def get_minimize_to_tray(self) -> bool:
        """Сворачивать в трей при закрытии"""
        return self.settings.value("tray/minimize_to_tray", True, type=bool)

    def set_minimize_to_tray(self, enabled: bool):
        """Установить minimize to tray"""
        self.settings.setValue("tray/minimize_to_tray", enabled)

    def get_start_minimized(self) -> bool:
        """Запускать свернутым в трей"""
        return self.settings.value("tray/start_minimized", False, type=bool)

    def set_start_minimized(self, enabled: bool):
        """Установить start minimized"""
        self.settings.setValue("tray/start_minimized", enabled)

    def get_notifications_enabled(self) -> bool:
        """Включены ли notifications"""
        return self.settings.value("notifications/enabled", True, type=bool)

    def set_notifications_enabled(self, enabled: bool):
        """Установить notifications enabled"""
        self.settings.setValue("notifications/enabled", enabled)

    def get_notification_sound(self) -> bool:
        """Звук для notifications"""
        return self.settings.value("notifications/sound", False, type=bool)

    def set_notification_sound(self, enabled: bool):
        """Установить notification sound"""
        self.settings.setValue("notifications/sound", enabled)
