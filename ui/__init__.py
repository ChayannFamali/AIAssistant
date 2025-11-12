"""
UI package
"""
from .main_window import MainWindow
from .model_downloader import ModelDownloaderDialog
from .settings_dialog import SettingsDialog
from .history_viewer import HistoryViewerDialog
from .performance_widget import PerformanceWidget
from .audio_settings_dialog import AudioSettingsDialog
from .tray_icon import TrayIcon
from .quick_input_dialog import QuickInputDialog
from .notification_manager import NotificationManager
from .statistics_viewer import StatisticsViewerDialog  #  НОВОЕ

__all__ = [
    'MainWindow',
    'ModelDownloaderDialog',
    'SettingsDialog',
    'HistoryViewerDialog',
    'PerformanceWidget',
    'AudioSettingsDialog',
    'TrayIcon',
    'QuickInputDialog',
    'NotificationManager',
    'StatisticsViewerDialog'
]
