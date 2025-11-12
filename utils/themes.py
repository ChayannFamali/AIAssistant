"""
Themes Manager - управление темами оформления
"""
import logging
from enum import Enum
from typing import Dict

logger = logging.getLogger("AIAssistant.Themes")


class ThemeType(Enum):
    """Типы тем"""
    DARK = "dark"
    LIGHT = "light"


class Theme:
    """Базовый класс темы"""
    
    def __init__(self, name: str):
        self.name = name
        self.colors: Dict[str, str] = {}
    
    def get_stylesheet(self) -> str:
        """Получить QSS stylesheet"""
        raise NotImplementedError


class DarkTheme(Theme):
    """Темная тема"""
    
    def __init__(self):
        super().__init__("Dark")
        
        self.colors = {
            "background": "#2b2b2b",
            "background_dark": "#1e1e1e",
            "border": "#444",
            "text": "#e0e0e0",
            "text_secondary": "#888",
            
            "primary": "#0d7377",
            "primary_hover": "#14a085",
            "primary_pressed": "#0a5f62",
            
            "success": "#4caf50",
            "warning": "#ff9800",
            "error": "#f44336",
            "info": "#2196f3",
            
            "button_bg": "#555",
            "button_hover": "#666",
            "button_disabled": "#333",
        }
    
    def get_stylesheet(self) -> str:
        """Получить QSS для темной темы"""
        return f"""
            /* Main Window */
            QMainWindow {{
                background-color: {self.colors['background']};
                color: {self.colors['text']};
            }}
            
            /* Widgets */
            QWidget {{
                background-color: {self.colors['background']};
                color: {self.colors['text']};
            }}
            
            /* Text Edit */
            QTextEdit {{
                background-color: {self.colors['background_dark']};
                color: {self.colors['text']};
                border: 1px solid {self.colors['border']};
                border-radius: 5px;
                padding: 10px;
                selection-background-color: {self.colors['primary']};
            }}
            
            /* Line Edit */
            QLineEdit {{
                background-color: {self.colors['background_dark']};
                color: {self.colors['text']};
                border: 1px solid {self.colors['border']};
                border-radius: 5px;
                padding: 8px;
                selection-background-color: {self.colors['primary']};
            }}
            
            QLineEdit:focus {{
                border: 1px solid {self.colors['primary']};
            }}
            
            /* Buttons */
            QPushButton {{
                background-color: {self.colors['primary']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {self.colors['primary_hover']};
            }}
            
            QPushButton:pressed {{
                background-color: {self.colors['primary_pressed']};
            }}
            
            QPushButton:disabled {{
                background-color: {self.colors['button_disabled']};
                color: {self.colors['text_secondary']};
            }}
            
            /* Status Bar */
            QStatusBar {{
                background-color: {self.colors['background_dark']};
                color: {self.colors['text_secondary']};
                border-top: 1px solid {self.colors['border']};
            }}
            
            /* Progress Bar */
            QProgressBar {{
                border: 1px solid {self.colors['border']};
                border-radius: 5px;
                text-align: center;
                background-color: {self.colors['background_dark']};
                color: {self.colors['text']};
            }}
            
            QProgressBar::chunk {{
                background-color: {self.colors['primary']};
                border-radius: 4px;
            }}
            
            /* Labels */
            QLabel {{
                color: {self.colors['text']};
            }}
            
            /* GroupBox */
            QGroupBox {{
                color: {self.colors['text']};
                border: 1px solid {self.colors['border']};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            
            /* ComboBox */
            QComboBox {{
                background-color: {self.colors['background_dark']};
                color: {self.colors['text']};
                border: 1px solid {self.colors['border']};
                border-radius: 5px;
                padding: 5px;
            }}
            
            QComboBox::drop-down {{
                border: none;
            }}
            
            QComboBox:hover {{
                border: 1px solid {self.colors['primary']};
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {self.colors['background_dark']};
                color: {self.colors['text']};
                selection-background-color: {self.colors['primary']};
            }}
            
            /* SpinBox */
            QSpinBox, QDoubleSpinBox {{
                background-color: {self.colors['background_dark']};
                color: {self.colors['text']};
                border: 1px solid {self.colors['border']};
                border-radius: 5px;
                padding: 5px;
            }}
            
            /* CheckBox */
            QCheckBox {{
                color: {self.colors['text']};
            }}
            
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {self.colors['border']};
                border-radius: 3px;
                background-color: {self.colors['background_dark']};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {self.colors['primary']};
            }}
            
            /* TabWidget */
            QTabWidget::pane {{
                border: 1px solid {self.colors['border']};
                background-color: {self.colors['background']};
            }}
            
            QTabBar::tab {{
                background-color: {self.colors['background_dark']};
                color: {self.colors['text']};
                padding: 8px 20px;
                border: 1px solid {self.colors['border']};
            }}
            
            QTabBar::tab:selected {{
                background-color: {self.colors['primary']};
            }}
            
            QTabBar::tab:hover {{
                background-color: {self.colors['button_hover']};
            }}
            
            /* Scroll Bar */
            QScrollBar:vertical {{
                background-color: {self.colors['background_dark']};
                width: 12px;
                border: none;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {self.colors['button_bg']};
                border-radius: 6px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {self.colors['button_hover']};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            /* Table */
            QTableWidget {{
                background-color: {self.colors['background_dark']};
                color: {self.colors['text']};
                border: 1px solid {self.colors['border']};
                gridline-color: {self.colors['border']};
            }}
            
            QTableWidget::item:selected {{
                background-color: {self.colors['primary']};
            }}
            
            QHeaderView::section {{
                background-color: {self.colors['background']};
                color: {self.colors['text']};
                padding: 5px;
                border: 1px solid {self.colors['border']};
                font-weight: bold;
            }}
        """


class LightTheme(Theme):
    """Светлая тема"""
    
    def __init__(self):
        super().__init__("Light")
        
        self.colors = {
            "background": "#f5f5f5",
            "background_dark": "#ffffff",
            "border": "#ddd",
            "text": "#2b2b2b",
            "text_secondary": "#666",
            
            "primary": "#0d7377",
            "primary_hover": "#14a085",
            "primary_pressed": "#0a5f62",
            
            "success": "#4caf50",
            "warning": "#ff9800",
            "error": "#f44336",
            "info": "#2196f3",
            
            "button_bg": "#e0e0e0",
            "button_hover": "#d0d0d0",
            "button_disabled": "#f0f0f0",
        }
    
    def get_stylesheet(self) -> str:
        """Получить QSS для светлой темы"""
        return f"""
            /* Main Window */
            QMainWindow {{
                background-color: {self.colors['background']};
                color: {self.colors['text']};
            }}
            
            QWidget {{
                background-color: {self.colors['background']};
                color: {self.colors['text']};
            }}
            
            QTextEdit {{
                background-color: {self.colors['background_dark']};
                color: {self.colors['text']};
                border: 1px solid {self.colors['border']};
                border-radius: 5px;
                padding: 10px;
            }}
            
            QLineEdit {{
                background-color: {self.colors['background_dark']};
                color: {self.colors['text']};
                border: 1px solid {self.colors['border']};
                border-radius: 5px;
                padding: 8px;
            }}
            
            QLineEdit:focus {{
                border: 2px solid {self.colors['primary']};
            }}
            
            QPushButton {{
                background-color: {self.colors['primary']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {self.colors['primary_hover']};
            }}
            
            QPushButton:pressed {{
                background-color: {self.colors['primary_pressed']};
            }}
            
            QPushButton:disabled {{
                background-color: {self.colors['button_disabled']};
                color: {self.colors['text_secondary']};
            }}
            
            QStatusBar {{
                background-color: {self.colors['background_dark']};
                color: {self.colors['text_secondary']};
                border-top: 1px solid {self.colors['border']};
            }}
            
            QProgressBar {{
                border: 1px solid {self.colors['border']};
                border-radius: 5px;
                text-align: center;
                background-color: {self.colors['background_dark']};
            }}
            
            QProgressBar::chunk {{
                background-color: {self.colors['primary']};
            }}
            
            QLabel {{
                color: {self.colors['text']};
            }}
            
            QGroupBox {{
                color: {self.colors['text']};
                border: 1px solid {self.colors['border']};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }}
            
            QComboBox {{
                background-color: {self.colors['background_dark']};
                color: {self.colors['text']};
                border: 1px solid {self.colors['border']};
                border-radius: 5px;
                padding: 5px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {self.colors['background_dark']};
                color: {self.colors['text']};
                selection-background-color: {self.colors['primary']};
            }}
            
            QSpinBox, QDoubleSpinBox {{
                background-color: {self.colors['background_dark']};
                color: {self.colors['text']};
                border: 1px solid {self.colors['border']};
                border-radius: 5px;
                padding: 5px;
            }}
            
            QCheckBox {{
                color: {self.colors['text']};
            }}
            
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {self.colors['border']};
                border-radius: 3px;
                background-color: {self.colors['background_dark']};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {self.colors['primary']};
            }}
            
            QTabWidget::pane {{
                border: 1px solid {self.colors['border']};
                background-color: {self.colors['background']};
            }}
            
            QTabBar::tab {{
                background-color: {self.colors['button_bg']};
                color: {self.colors['text']};
                padding: 8px 20px;
                border: 1px solid {self.colors['border']};
            }}
            
            QTabBar::tab:selected {{
                background-color: {self.colors['primary']};
                color: white;
            }}
            
            QScrollBar:vertical {{
                background-color: {self.colors['background_dark']};
                width: 12px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {self.colors['button_bg']};
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {self.colors['button_hover']};
            }}
            
            QTableWidget {{
                background-color: {self.colors['background_dark']};
                color: {self.colors['text']};
                border: 1px solid {self.colors['border']};
            }}
            
            QTableWidget::item:selected {{
                background-color: {self.colors['primary']};
                color: white;
            }}
            
            QHeaderView::section {{
                background-color: {self.colors['button_bg']};
                color: {self.colors['text']};
                padding: 5px;
                border: 1px solid {self.colors['border']};
                font-weight: bold;
            }}
        """


class ThemeManager:
    """Менеджер тем"""
    
    def __init__(self):
        self.themes = {
            ThemeType.DARK: DarkTheme(),
            ThemeType.LIGHT: LightTheme(),
        }
        
        self.current_theme: Theme = self.themes[ThemeType.DARK]
        
        logger.info("ThemeManager initialized")
    
    def set_theme(self, theme_type: ThemeType):
        """Установить тему"""
        self.current_theme = self.themes[theme_type]
        logger.info(f"Theme changed to: {self.current_theme.name}")
    
    def get_current_theme(self) -> Theme:
        """Получить текущую тему"""
        return self.current_theme
    
    def get_stylesheet(self) -> str:
        """Получить stylesheet текущей темы"""
        return self.current_theme.get_stylesheet()
