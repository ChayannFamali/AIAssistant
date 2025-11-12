"""
System Tray Icon - иконка в системном трее
"""
import logging
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu,QApplication
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal
import sys

logger = logging.getLogger("AIAssistant.Tray")
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)-8s [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(
            stream=sys.stdout 
        )
    ]
)

class TrayIcon(QObject):
    """
    System Tray Icon с контекстным меню
    """
    
    show_window_requested = pyqtSignal()
    hide_window_requested = pyqtSignal()
    toggle_listening_requested = pyqtSignal()
    open_settings_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.tray_icon = QSystemTrayIcon(parent)
        self.menu = QMenu()
        
        self.is_listening = False
        
        self.setup_tray()
        
        logger.info("TrayIcon initialized")
    
    def setup_tray(self):
        """Настроить tray icon и меню"""
        
        icon = QApplication.style().standardIcon(
            QApplication.style().StandardPixmap.SP_ComputerIcon
        )
        self.tray_icon.setIcon(icon)
        
        self.tray_icon.setToolTip("AI Assistant")
        
        self.create_menu()
        
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        logger.info("Tray icon setup complete")
    
    def create_menu(self):
        """Создать контекстное меню"""
        self.menu.clear()
        
        self.show_action = QAction("Show Window", self)
        self.show_action.triggered.connect(self.show_window_requested.emit)
        self.menu.addAction(self.show_action)
        
        self.hide_action = QAction("Hide Window", self)
        self.hide_action.triggered.connect(self.hide_window_requested.emit)
        self.menu.addAction(self.hide_action)
        
        self.menu.addSeparator()
        
        self.listening_action = QAction("Start Listening", self)
        self.listening_action.triggered.connect(self.toggle_listening_requested.emit)
        self.menu.addAction(self.listening_action)
        
        self.menu.addSeparator()
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings_requested.emit)
        self.menu.addAction(settings_action)
        
        self.menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_requested.emit)
        self.menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(self.menu)
    
    def on_tray_activated(self, reason):
        """Обработать клик по иконке трея"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window_requested.emit()
        
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window_requested.emit()
    
    def show(self):
        """Показать иконку в трее"""
        self.tray_icon.show()
        logger.info("Tray icon shown")
    
    def hide(self):
        """Скрыть иконку из трея"""
        self.tray_icon.hide()
        logger.info("Tray icon hidden")
    
    def update_listening_status(self, is_listening: bool):
        """
        Обновить статус прослушивания
        
        Args:
            is_listening: True если listening активен
        """
        self.is_listening = is_listening
        
        if is_listening:
            self.listening_action.setText("Stop Listening")
            self.tray_icon.setToolTip("AI Assistant - Listening...")
        else:
            self.listening_action.setText("Start Listening")
            self.tray_icon.setToolTip("AI Assistant")
    
    def show_message(self, title: str, message: str, icon=QSystemTrayIcon.MessageIcon.Information, duration: int = 3000):
        """
        Показать balloon notification
        
        Args:
            title: Заголовок
            message: Текст сообщения
            icon: Иконка (Information, Warning, Critical)
            duration: Длительность в мс
        """
        self.tray_icon.showMessage(title, message, icon, duration)
        logger.debug(f"Tray notification: {title} - {message}")
