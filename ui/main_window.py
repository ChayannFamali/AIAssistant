"""
Main Window - главное окно приложения (overlay) - PHASE 2 VERSION
Audio + STT Integration
"""
"""
Main Window - главное окно приложения (overlay) - PHASE 3 VERSION
System Tray + Hotkeys + Notifications
"""
import logging
from typing import Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QLineEdit,
    QStatusBar, QMessageBox, QSplitter, QProgressBar
)
from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QTextCursor, QColor, QCloseEvent

from threads.llm_thread import LLMWorker
from threads.audio_thread import AudioWorker
from threads.stt_thread import STTWorker
from ui.model_downloader import ModelDownloaderDialog
from ui.settings_dialog import SettingsDialog
from ui.history_viewer import HistoryViewerDialog
from ui.performance_widget import PerformanceWidget
from ui.audio_settings_dialog import AudioSettingsDialog
from ui.tray_icon import TrayIcon  
from ui.quick_input_dialog import QuickInputDialog  
from ui.notification_manager import NotificationManager  
from utils.settings_manager import SettingsManager
from utils.history_manager import HistoryManager
from utils.clipboard_helper import ClipboardHelper
from utils.hotkeys_manager import HotkeysManager, DEFAULT_HOTKEYS  
from core.config import AppConfig, PipelineConfig, STTConfig
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QPen

logger = logging.getLogger("AIAssistant.MainWindow")


from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtCore import QRect

class MinimizeButton(QPushButton):
    """Кнопка minimize с нарисованной линией"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 28)
        self.setToolTip("Minimize")
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: #555;
                border-radius: 4px;
            }
        """)
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(QColor("#e0e0e0"), 2)
        painter.setPen(pen)
        
        y = self.height() // 2
        x_start = 8
        x_end = self.width() - 8
        
        painter.drawLine(x_start, y, x_end, y)


class CloseButton(QPushButton):
    """Кнопка close с нарисованным крестиком"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 28)
        self.setToolTip("Close")
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: #d32f2f;
                border-radius: 4px;
            }
        """)
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(QColor("#e0e0e0"), 2)
        painter.setPen(pen)
        
        margin = 8
        x1, y1 = margin, margin
        x2, y2 = self.width() - margin, self.height() - margin
        
        painter.drawLine(x1, y1, x2, y2)
        painter.drawLine(x2, y1, x1, y2)


class MainWindow(QMainWindow):
    """
    Главное окно приложения - Phase 2 Complete
    Audio Capture + STT + LLM Pipeline
    """
    
    def __init__(self):
        super().__init__()
        
        self.settings_manager = SettingsManager()
        self.history_manager = HistoryManager()
        
        from utils.statistics_manager import StatisticsManager
        self.statistics_manager = StatisticsManager()
        
        from utils.themes import ThemeManager, ThemeType
        self.theme_manager = ThemeManager()
        
        saved_theme = self.settings_manager.settings.value("ui/theme", "dark")
        if saved_theme == "light":
            self.theme_manager.set_theme(ThemeType.LIGHT)
        else:
            self.theme_manager.set_theme(ThemeType.DARK)
        
        self.llm_worker: Optional[LLMWorker] = None
        self.audio_worker: Optional[AudioWorker] = None
        self.stt_worker: Optional[STTWorker] = None
        
        self.tray_icon: Optional[TrayIcon] = None
        self.hotkeys_manager: Optional[HotkeysManager] = None
        self.notification_manager: Optional[NotificationManager] = None
        self.quick_input_dialog: Optional[QuickInputDialog] = None
        
        self.current_question = ""
        self.current_answer = ""
        
        self.current_mode = PipelineConfig.DEFAULT_MODE
        
        self.is_window_visible = True
        
        self.drag_position = QPoint()
        
        self.autosave_timer: Optional[QTimer] = None
        
        self.setup_window()
        self.setup_ui()
        self.setup_workers()
        self.setup_phase3_components()  
        self.setup_autosave()
        self.restore_settings()
        
        self.history_manager.start_new_session()
        
        if self.settings_manager.get_start_minimized():
            self.hide()
            self.is_window_visible = False
            logger.info("Started minimized to tray")
        
        logger.info("MainWindow initialized (Phase 3 Complete)")

    
    def setup_window(self):
        """Настроить свойства окна"""
        self.setWindowTitle(f"{AppConfig.APP_NAME} v{AppConfig.APP_VERSION} - Phase 3")
        
        always_on_top = self.settings_manager.settings.value("ui/always_on_top", True, type=bool)
        
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        
        self.setWindowFlags(flags)
        
        self.setMinimumSize(600, 400)
        self.resize(900, 600)
        
        opacity = self.settings_manager.get_window_opacity()
        self.setWindowOpacity(opacity)
        
        self.apply_theme()
    
    def setup_ui(self):
        """Создать UI элементы"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_panel = self.create_main_panel()
        splitter.addWidget(left_panel)
        
        show_stats = self.settings_manager.settings.value("ui/show_stats", True, type=bool)
        if show_stats:
            self.performance_widget = PerformanceWidget()
            splitter.addWidget(self.performance_widget)
            splitter.setStretchFactor(0, 4)
            splitter.setStretchFactor(1, 1)
        else:
            self.performance_widget = None
            splitter.setStretchFactor(0, 1)
        
        main_layout.addWidget(splitter)
    
    def create_main_panel(self) -> QWidget:
        """Создать основную панель"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        title_bar = self.create_title_bar()
        layout.addWidget(title_bar)
        
        mode_layout = self.create_mode_selector()
        layout.addLayout(mode_layout)
        
        self.audio_indicator_widget = self.create_audio_indicator()
        self.audio_indicator_widget.setVisible(False)
        layout.addWidget(self.audio_indicator_widget)
        
        font_size = int(self.settings_manager.settings.value("ui/font_size", 10))
        
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setFont(QFont("Segoe UI", font_size))
        self.text_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.text_display, stretch=1)
        
        # Action buttons
        action_buttons_layout = QHBoxLayout()
        
        self.copy_answer_btn = QPushButton("📋 Copy Answer")
        self.copy_answer_btn.setEnabled(False)
        self.copy_answer_btn.clicked.connect(self.copy_last_answer)
        self.copy_answer_btn.setStyleSheet(self._get_action_button_style())
        action_buttons_layout.addWidget(self.copy_answer_btn)
        
        self.copy_all_btn = QPushButton("📄 Copy All")
        self.copy_all_btn.clicked.connect(self.copy_all_text)
        self.copy_all_btn.setStyleSheet(self._get_action_button_style())
        action_buttons_layout.addWidget(self.copy_all_btn)
        
        action_buttons_layout.addStretch()
        
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.clicked.connect(self.on_clear)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 10px;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        action_buttons_layout.addWidget(self.clear_btn)
        
        layout.addLayout(action_buttons_layout)
        
        self.input_widget = self.create_input_area()
        layout.addWidget(self.input_widget)
        
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #1e1e1e;
                color: #888;
                border-top: 1px solid #444;
            }
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        return widget
    def _get_text_button_style(self) -> str:
        return """
            QPushButton {
                background-color: transparent;
                color: #e0e0e0;
                border: none;
                padding: 5px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #0d7377;
                border-radius: 5px;
            }
        """

    def create_title_bar(self) -> QWidget:
        """Создать title bar"""
        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                border-radius: 5px;
            }
        """)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(10, 0, 5, 0)
        layout.setSpacing(3)
        

        title_label = QLabel("≡ AI Assistant")
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("QLabel { color: #e0e0e0; }")
        layout.addWidget(title_label)

        
        layout.addStretch()
        
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)
        
        self.llm_status_label = QLabel("LLM")
        self.llm_status_label.setToolTip("LLM Status: Not loaded")
        self.llm_status_label.setStyleSheet("""
            QLabel { 
                color: #ff9800; 
                font-size: 9px; 
                font-weight: bold;
                background-color: #2b2b2b;
                padding: 2px 5px;
                border-radius: 3px;
            }
        """)
        status_layout.addWidget(self.llm_status_label)
        
        self.stt_status_label = QLabel("STT")
        self.stt_status_label.setToolTip("STT Status: Not loaded")
        self.stt_status_label.setStyleSheet("""
            QLabel { 
                color: #ff9800; 
                font-size: 9px; 
                font-weight: bold;
                background-color: #2b2b2b;
                padding: 2px 5px;
                border-radius: 3px;
            }
        """)
        status_layout.addWidget(self.stt_status_label)
        
        layout.addWidget(status_container)
        
        layout.addSpacing(5)
        
        self.history_btn = QPushButton()
        self.history_btn.setIcon(self.style().standardIcon(
            self.style().StandardPixmap.SP_FileDialogDetailedView
        ))
        self.history_btn.setIconSize(QSize(16, 16))
        self.history_btn.setToolTip("History")
        self.history_btn.setFixedSize(28, 28)
        self.history_btn.clicked.connect(self.show_history_viewer)
        self.history_btn.setStyleSheet(self._get_icon_button_style())
        layout.addWidget(self.history_btn)
        
        self.stats_btn = QPushButton()
        self.stats_btn.setIcon(self.style().standardIcon(
            self.style().StandardPixmap.SP_FileDialogInfoView
        ))
        self.stats_btn.setIconSize(QSize(16, 16))
        self.stats_btn.setToolTip("Statistics")
        self.stats_btn.setFixedSize(28, 28)
        self.stats_btn.clicked.connect(self.show_statistics_viewer)
        self.stats_btn.setStyleSheet(self._get_icon_button_style())
        layout.addWidget(self.stats_btn)
        
        self.audio_settings_btn = QPushButton()
        self.audio_settings_btn.setIcon(self.style().standardIcon(
            self.style().StandardPixmap.SP_MediaVolume
        ))
        self.audio_settings_btn.setIconSize(QSize(16, 16))
        self.audio_settings_btn.setToolTip("Audio")
        self.audio_settings_btn.setFixedSize(28, 28)
        self.audio_settings_btn.clicked.connect(self.show_audio_settings)
        self.audio_settings_btn.setStyleSheet(self._get_icon_button_style())
        layout.addWidget(self.audio_settings_btn)
        
        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(self.style().standardIcon(
            self.style().StandardPixmap.SP_FileDialogListView
        ))
        self.settings_btn.setIconSize(QSize(16, 16))
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.setFixedSize(28, 28)
        self.settings_btn.clicked.connect(self.show_settings)
        self.settings_btn.setStyleSheet(self._get_icon_button_style())
        layout.addWidget(self.settings_btn)
        
        layout.addSpacing(5)
        
        minimize_btn = QPushButton()
        minimize_btn.setIcon(self.style().standardIcon(
            self.style().StandardPixmap.SP_TitleBarMinButton
        ))
        minimize_btn.setIconSize(QSize(16, 16))
        minimize_btn.setFixedSize(28, 28)
        minimize_btn.setToolTip("Minimize")
        minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: #555;
                border-radius: 4px;
            }
        """)
        minimize_btn.clicked.connect(self.showMinimized)
        layout.addWidget(minimize_btn)
        
        close_btn = QPushButton()
        close_btn.setIcon(self.style().standardIcon(
            self.style().StandardPixmap.SP_TitleBarCloseButton
        ))
        close_btn.setIconSize(QSize(16, 16))
        close_btn.setFixedSize(28, 28)
        close_btn.setToolTip("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: #d32f2f;
                border-radius: 4px;
            }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        return title_bar



    def show_statistics_viewer(self):
        """Показать диалог статистики"""
        from ui.statistics_viewer import StatisticsViewerDialog
        dialog = StatisticsViewerDialog(self.statistics_manager, self)
        dialog.exec()

    def create_mode_selector(self) -> QHBoxLayout:
        """Создать селектор режима работы"""
        layout = QHBoxLayout()
        
        mode_label = QLabel("Mode:")
        mode_label.setStyleSheet("QLabel { color: #e0e0e0; font-weight: bold; }")
        layout.addWidget(mode_label)
        
        self.manual_mode_btn = QPushButton("\u270F Manual")  # ✏ Manual
        self.manual_mode_btn.setCheckable(True)
        self.manual_mode_btn.setChecked(True)
        self.manual_mode_btn.clicked.connect(lambda: self.switch_mode(PipelineConfig.MODE_MANUAL))
        self.manual_mode_btn.setStyleSheet(self._get_mode_button_style())
        layout.addWidget(self.manual_mode_btn)
        
        self.listening_mode_btn = QPushButton("\U0001F3A7 Listening")  # 🎧 Listening
        self.listening_mode_btn.setCheckable(True)
        self.listening_mode_btn.clicked.connect(lambda: self.switch_mode(PipelineConfig.MODE_LISTENING))
        self.listening_mode_btn.setStyleSheet(self._get_mode_button_style())
        layout.addWidget(self.listening_mode_btn)
        
        self.auto_mode_btn = QPushButton("\U0001F916 Auto")  # 🤖 Auto
        self.auto_mode_btn.setCheckable(True)
        self.auto_mode_btn.clicked.connect(lambda: self.switch_mode(PipelineConfig.MODE_AUTO))
        self.auto_mode_btn.setStyleSheet(self._get_mode_button_style())
        layout.addWidget(self.auto_mode_btn)
        
        layout.addStretch()
        
        self.listening_toggle_btn = QPushButton("\u25B6 Start Listening")  # ▶ Start
        self.listening_toggle_btn.clicked.connect(self.toggle_listening)
        self.listening_toggle_btn.setVisible(False)
        self.listening_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66bb6a;
            }
        """)
        layout.addWidget(self.listening_toggle_btn)
        
        return layout

    
    def create_audio_indicator(self) -> QWidget:
        """Создать индикатор аудио активности"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.audio_status_label = QLabel("🔴 Not listening")
        self.audio_status_label.setStyleSheet("QLabel { color: #f44336; font-weight: bold; }")
        layout.addWidget(self.audio_status_label)
        
        layout.addStretch()
        
        volume_label = QLabel("Volume:")
        volume_label.setStyleSheet("QLabel { color: #888; }")
        layout.addWidget(volume_label)
        
        self.volume_bar = QProgressBar()
        self.volume_bar.setRange(0, 100)
        self.volume_bar.setValue(0)
        self.volume_bar.setTextVisible(False)
        self.volume_bar.setMaximumWidth(150)
        self.volume_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 3px;
                background-color: #2b2b2b;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.volume_bar)
        
        return widget
    
    def create_input_area(self) -> QWidget:
        """Создать область ввода (для manual mode)"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        font_size = int(self.settings_manager.settings.value("ui/font_size", 10))
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter your question here...")
        self.input_field.setFont(QFont("Segoe UI", font_size))
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 8px;
            }
            QLineEdit:focus {
                border: 1px solid #0d7377;
            }
        """)
        self.input_field.returnPressed.connect(self.on_send_question)
        layout.addWidget(self.input_field)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setMinimumWidth(80)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d7377;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #14a085;
            }
            QPushButton:pressed {
                background-color: #0a5f62;
            }
            QPushButton:disabled {
                background-color: #444;
                color: #888;
            }
        """)
        self.send_btn.clicked.connect(self.on_send_question)
        layout.addWidget(self.send_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumWidth(80)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f44336;
            }
            QPushButton:disabled {
                background-color: #444;
                color: #888;
            }
        """)
        self.stop_btn.clicked.connect(self.on_stop_generation)
        layout.addWidget(self.stop_btn)
        
        return widget
    
    def _get_icon_button_style(self) -> str:
        return """
            QPushButton {
                background-color: transparent;
                color: #e0e0e0;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0d7377;
                border-radius: 5px;
            }
        """
    
    def _get_action_button_style(self) -> str:
        return """
            QPushButton {
                background-color: #555;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 10px;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: #666;
            }
            QPushButton:disabled {
                background-color: #333;
                color: #666;
            }
        """
    
    def _get_mode_button_style(self) -> str:
        return """
            QPushButton {
                background-color: #555;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #666;
            }
            QPushButton:checked {
                background-color: #0d7377;
            }
        """
    
    def setup_workers(self):
        """Инициализировать все worker threads"""
        self.llm_worker = LLMWorker()
        self.llm_worker.token_generated.connect(self.on_token_generated)
        self.llm_worker.generation_started.connect(self.on_generation_started)
        self.llm_worker.generation_finished.connect(self.on_generation_finished)
        self.llm_worker.generation_error.connect(self.on_generation_error)
        self.llm_worker.model_load_started.connect(self.on_llm_load_started)
        self.llm_worker.model_load_progress.connect(self.on_llm_load_progress)
        self.llm_worker.model_load_finished.connect(self.on_llm_load_finished)
        self.llm_worker.model_load_error.connect(self.on_llm_load_error)
        self.llm_worker.performance_stats.connect(self.on_performance_stats)
        self.llm_worker.context_cleared.connect(self.on_context_cleared)
        self.llm_worker.start()
        
        self.audio_worker = AudioWorker()
        self.audio_worker.audio_ready.connect(self.on_audio_ready)
        self.audio_worker.speech_started.connect(self.on_speech_started)
        self.audio_worker.speech_ended.connect(self.on_speech_ended)
        self.audio_worker.volume_level.connect(self.on_volume_level)
        self.audio_worker.error_occurred.connect(self.on_audio_error)
        self.audio_worker.start()
        
        self.stt_worker = STTWorker()
        self.stt_worker.transcription_ready.connect(self.on_transcription_ready)
        self.stt_worker.question_detected.connect(self.on_question_detected)
        self.stt_worker.model_load_started.connect(self.on_stt_load_started)
        self.stt_worker.model_load_finished.connect(self.on_stt_load_finished)
        self.stt_worker.model_load_error.connect(self.on_stt_load_error)
        self.stt_worker.transcription_started.connect(self.on_transcription_started)
        self.stt_worker.transcription_error.connect(self.on_transcription_error)
        self.stt_worker.start()
        
        logger.info("All worker threads started")
        
        self.check_and_load_llm_model()
        self.load_stt_model()
        
    def setup_phase3_components(self):
        """Инициализировать Phase 3 компоненты"""
        
        self.tray_icon = TrayIcon(self)
        
        self.tray_icon.show_window_requested.connect(self.show_window_from_tray)
        self.tray_icon.hide_window_requested.connect(self.hide_window_to_tray)
        self.tray_icon.toggle_listening_requested.connect(self.toggle_listening)
        self.tray_icon.open_settings_requested.connect(self.show_settings)
        self.tray_icon.quit_requested.connect(self.quit_application)
        
        self.tray_icon.show()
        
        logger.info("System tray initialized")
        
        self.notification_manager = NotificationManager(self.tray_icon.tray_icon)
        self.notification_manager.set_enabled(
            self.settings_manager.get_notifications_enabled()
        )
        self.notification_manager.set_sound_enabled(
            self.settings_manager.get_notification_sound()
        )
        
        logger.info("Notification manager initialized")
        
        self.hotkeys_manager = HotkeysManager()
        
        self.hotkeys_manager.toggle_window_requested.connect(self.toggle_window_visibility)
        self.hotkeys_manager.toggle_listening_requested.connect(self.toggle_listening_hotkey)
        self.hotkeys_manager.quick_input_requested.connect(self.show_quick_input)
        self.hotkeys_manager.stop_generation_requested.connect(self.on_stop_generation)
        
        self.load_and_register_hotkeys()
        
        logger.info("Hotkeys manager initialized")
        
        self.quick_input_dialog = QuickInputDialog(self)
        self.quick_input_dialog.question_submitted.connect(self.on_quick_question)
        
        logger.info("Quick input dialog initialized")

    def check_and_load_llm_model(self):
        """Проверить и загрузить LLM модель"""
        model_path = self.settings_manager.get_model_path()
        
        if model_path and Path(model_path).exists():
            logger.info(f"Found existing LLM model: {model_path}")
            self.llm_worker.load_model(model_path)
        else:
            default_path = AppConfig.get_default_model_path()
            if Path(default_path).exists():
                logger.info(f"Found LLM model in default location: {default_path}")
                self.settings_manager.set_model_path(default_path)
                self.llm_worker.load_model(default_path)
            else:
                logger.info("LLM model not found, showing downloader dialog")
                self.show_model_downloader()
    
    def load_stt_model(self):
        """Загрузить STT модель"""
        model_size = self.settings_manager.settings.value("stt/model_size", STTConfig.MODEL_SIZE)
        logger.info(f"Loading STT model: {model_size}")
        self.stt_worker.load_model(model_size)
    
    def setup_autosave(self):
        """Настроить автосохранение"""
        autosave_enabled = self.settings_manager.settings.value("general/autosave_enabled", True, type=bool)
        
        if not autosave_enabled:
            return
        
        interval_sec = int(self.settings_manager.settings.value("general/autosave_interval", 60))
        
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.autosave_session)
        self.autosave_timer.start(interval_sec * 1000)
        
        logger.info(f"Autosave enabled: every {interval_sec} seconds")
    
    def autosave_session(self):
        """Автосохранение сессии"""
        if self.history_manager.current_session:
            if self.history_manager.save_session():
                logger.debug("Session autosaved")
    
    
    def switch_mode(self, mode: str):
        """Переключить режим работы"""
        logger.info(f"Switching mode to: {mode}")
        
        if self.audio_worker.is_listening:
            self.audio_worker.stop_listening()
            self.audio_status_label.setText("🔴 Not listening")
            self.audio_status_label.setStyleSheet("QLabel { color: #f44336; font-weight: bold; }")
            self.listening_toggle_btn.setText("▶️ Start Listening")
        
        self.current_mode = mode
        
        self.manual_mode_btn.setChecked(mode == PipelineConfig.MODE_MANUAL)
        self.listening_mode_btn.setChecked(mode == PipelineConfig.MODE_LISTENING)
        self.auto_mode_btn.setChecked(mode == PipelineConfig.MODE_AUTO)
        
        if mode == PipelineConfig.MODE_MANUAL:
            self.input_widget.setVisible(True)
            self.listening_toggle_btn.setVisible(False)
            self.audio_indicator_widget.setVisible(False)
            self.status_bar.showMessage("Manual input mode")
        
        else:  # LISTENING or AUTO
            self.input_widget.setVisible(False)
            self.listening_toggle_btn.setVisible(True)
            self.audio_indicator_widget.setVisible(True)
            
            # Настройки STT
            auto_detect = mode == PipelineConfig.MODE_AUTO
            self.stt_worker.set_auto_detect_questions(auto_detect)
            
            status_msg = "Listening mode (transcription only)" if mode == PipelineConfig.MODE_LISTENING else "Auto mode (auto-answer questions)"
            self.status_bar.showMessage(status_msg)
    
    def toggle_listening(self):
        """Переключить listening on/off"""
        if not self.stt_worker.transcriber.is_loaded:
            QMessageBox.warning(self, "STT Not Ready", "Please wait for STT model to load")
            return
        
        if self.audio_worker.is_listening:
            # Stop
            self.audio_worker.stop_listening()
            self.audio_status_label.setText("🔴 Not listening")
            self.audio_status_label.setStyleSheet("QLabel { color: #f44336; font-weight: bold; }")
            self.listening_toggle_btn.setText("▶️ Start Listening")
            self.listening_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4caf50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #66bb6a;
                }
            """)
            logger.info("Audio listening stopped")
        
        else:
            use_loopback = self.settings_manager.settings.value("audio/use_loopback", True, type=bool)
            self.audio_worker.start_listening(use_loopback=use_loopback)
            self.audio_status_label.setText("🟢 Listening...")
            self.audio_status_label.setStyleSheet("QLabel { color: #4caf50; font-weight: bold; }")
            self.listening_toggle_btn.setText("⏸️ Stop Listening")
            self.listening_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #d32f2f;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #f44336;
                }
            """)
            logger.info("Audio listening started")
    
    
    @pyqtSlot(object)
    def on_audio_ready(self, audio_data):
        """Аудио чанк готов для транскрипции"""
        logger.debug("Audio chunk ready for transcription")
        self.stt_worker.transcribe_audio(audio_data)
    
    @pyqtSlot()
    def on_speech_started(self):
        """Обнаружена речь"""
        self.audio_status_label.setText("🟡 Speech detected...")
        self.audio_status_label.setStyleSheet("QLabel { color: #ffc107; font-weight: bold; }")
    
    @pyqtSlot()
    def on_speech_ended(self):
        """Речь закончилась"""
        self.audio_status_label.setText("🟢 Listening...")
        self.audio_status_label.setStyleSheet("QLabel { color: #4caf50; font-weight: bold; }")
    
    @pyqtSlot(float)
    def on_volume_level(self, rms):
        """Обновить индикатор громкости"""
        volume_percent = min(int(rms * 1000), 100)  # Масштабировать для visibility
        self.volume_bar.setValue(volume_percent)
    
    @pyqtSlot(str)
    def on_audio_error(self, error_msg):
        """Ошибка аудио"""
        logger.error(f"Audio error: {error_msg}")
        QMessageBox.critical(self, "Audio Error", error_msg)
        
        if self.audio_worker.is_listening:
            self.toggle_listening()
    
    @pyqtSlot()
    def on_transcription_started(self):
        """Началась транскрипция"""
        self.status_bar.showMessage("Transcribing...")
    
    @pyqtSlot(str, str)
    def on_transcription_ready(self, text, language):
        """Транскрипция готова"""
        logger.info(f"Transcription ready: '{text}' (lang: {language})")
        
        self.text_display.append(f"\n<span style='color: #888;'>[Transcribed]:</span> {text}\n")
        
        self.status_bar.showMessage(f"Transcribed: {text[:50]}...", 3000)
    
    @pyqtSlot(str)
    def on_question_detected(self, question):
        """Обнаружен вопрос (только в AUTO mode)"""
        logger.info(f"Question detected: {question}")
        
        self.text_display.append(f"<span style='color: #ff9800;'>[Auto-detected Question]</span>\n")
        
        if self.notification_manager:
            self.notification_manager.notify_question_detected(question)
        
        if self.llm_worker.engine.is_loaded():
            self.llm_worker.generate_answer(question)
        else:
            self.text_display.append("<span style='color: #f44336;'>LLM not loaded!</span>\n")

    
    @pyqtSlot(str)
    def on_transcription_error(self, error_msg):
        """Ошибка транскрипции"""
        logger.error(f"Transcription error: {error_msg}")
        self.status_bar.showMessage(f"Transcription error: {error_msg}", 5000)
    
    @pyqtSlot()
    def on_stt_load_started(self):
        self.stt_status_label.setText("STT")
        self.stt_status_label.setToolTip("STT Status: Loading...")
        self.stt_status_label.setStyleSheet("""
            QLabel { 
                color: #ffc107; 
                font-size: 9px; 
                font-weight: bold;
                background-color: #3d3d00;
                padding: 2px 5px;
                border-radius: 3px;
            }
        """)
        self.status_bar.showMessage("Loading STT model...")
        
    @pyqtSlot(bool)
    def on_stt_load_finished(self, success):
        if success:
            self.stt_status_label.setText("STT")
            self.stt_status_label.setToolTip("STT Status: Ready")
            self.stt_status_label.setStyleSheet("""
                QLabel { 
                    color: #4caf50; 
                    font-size: 9px; 
                    font-weight: bold;
                    background-color: #1b5e20;
                    padding: 2px 5px;
                    border-radius: 3px;
                }
            """)
            self.status_bar.showMessage("STT model loaded!", 2000)
            logger.info("STT model loaded successfully")
        else:
            self.stt_status_label.setText("STT")
            self.stt_status_label.setToolTip("STT Status: Failed")
            self.stt_status_label.setStyleSheet("""
                QLabel { 
                    color: #f44336; 
                    font-size: 9px; 
                    font-weight: bold;
                    background-color: #5d1f1f;
                    padding: 2px 5px;
                    border-radius: 3px;
                }
            """)
            self.status_bar.showMessage("STT model loading failed")
    
    @pyqtSlot(str)
    def on_stt_load_error(self, error_msg):
        """Ошибка загрузки STT"""
        QMessageBox.critical(self, "STT Load Error", error_msg)
    
    @pyqtSlot()
    def on_llm_load_started(self):
        self.llm_status_label.setText("LLM")
        self.llm_status_label.setToolTip("LLM Status: Loading...")
        self.llm_status_label.setStyleSheet("""
            QLabel { 
                color: #ffc107; 
                font-size: 9px; 
                font-weight: bold;
                background-color: #3d3d00;
                padding: 2px 5px;
                border-radius: 3px;
            }
        """)
        self.send_btn.setEnabled(False)
    
    @pyqtSlot(float)
    def on_llm_load_progress(self, progress):
        percentage = int(progress * 100)
        self.status_bar.showMessage(f"Loading LLM model... {percentage}%")
    
    @pyqtSlot(bool)
    def on_llm_load_finished(self, success):
        if success:
            self.llm_status_label.setText("LLM")
            self.llm_status_label.setToolTip("LLM Status: Ready")
            self.llm_status_label.setStyleSheet("""
                QLabel { 
                    color: #4caf50; 
                    font-size: 9px; 
                    font-weight: bold;
                    background-color: #1b5e20;
                    padding: 2px 5px;
                    border-radius: 3px;
                }
            """)
            self.send_btn.setEnabled(True)
            self.settings_manager.set_model_loaded(True)
            self.input_field.setFocus()
            logger.info("LLM model loaded successfully")
        else:
            self.llm_status_label.setText("LLM")
            self.llm_status_label.setToolTip("LLM Status: Failed")
            self.llm_status_label.setStyleSheet("""
                QLabel { 
                    color: #f44336; 
                    font-size: 9px; 
                    font-weight: bold;
                    background-color: #5d1f1f;
                    padding: 2px 5px;
                    border-radius: 3px;
                }
            """)


    @pyqtSlot(str)
    def on_llm_load_error(self, error_msg):
        QMessageBox.critical(self, "LLM Load Error", error_msg)
    
    @pyqtSlot(str)
    def on_generation_started(self, question):
        self.current_question = question
        self.current_answer = ""
        
        self.status_bar.showMessage("Generating answer...")
        self.send_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.input_field.setEnabled(False)
        self.copy_answer_btn.setEnabled(False)
        
        self.text_display.append(f"\n<b style='color: #4caf50;'>Q:</b> {question}\n")
        self.text_display.append("<b style='color: #2196f3;'>A:</b> ")
        
        self.history_manager.add_message("user", question)
    
    @pyqtSlot(str)
    def on_token_generated(self, token):
        self.current_answer += token
        
        cursor = self.text_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(token)
        self.text_display.setTextCursor(cursor)
        self.text_display.ensureCursorVisible()
    
    @pyqtSlot(str)
    def on_generation_finished(self, full_answer: str):
        """Генерация завершена"""
        self.status_bar.showMessage("Generation complete")
        self.send_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.input_field.setEnabled(True)
        self.input_field.clear()
        self.input_field.setFocus()
        self.copy_answer_btn.setEnabled(True)
        
        self.history_manager.add_message("assistant", full_answer.strip())
        
        if not self.is_window_visible and self.notification_manager:
            preview = full_answer[:100]
            self.notification_manager.notify_answer_ready(preview)
        
        logger.info(f"Answer generated: {len(full_answer)} chars")

    
    @pyqtSlot(str)
    def on_generation_error(self, error_msg):
        self.text_display.append(f"\n<span style='color: #f44336;'>{error_msg}</span>\n")
        self.status_bar.showMessage("Generation error")
        self.send_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.input_field.setEnabled(True)
    
    @pyqtSlot(dict)
    def on_performance_stats(self, stats):
        tokens_per_sec = stats.get('tokens_per_second', 0)
        total_time = stats.get('total_time', 0)
        total_tokens = stats.get('total_tokens', 0)
        
        context_size = self.llm_worker.engine.get_context_size()
        self.status_bar.showMessage(
            f"✓ {tokens_per_sec:.1f} t/s | {total_time:.1f}s | {total_tokens} tokens | Context: {context_size}"
        )
        
        if self.performance_widget:
            self.performance_widget.update_stats(stats)
        
        self.history_manager.update_stats(total_tokens, tokens_per_sec, total_time)
        
        if self.current_question:
            self.statistics_manager.record_question(
                self.current_question,
                total_tokens,
                total_time
            )

    
    @pyqtSlot()
    def on_context_cleared(self):
        self.status_bar.showMessage("Context cleared")
    
    
    def on_send_question(self):
        question = self.input_field.text().strip()
        
        if not question:
            return
        
        if not self.llm_worker.engine.is_loaded():
            QMessageBox.warning(self, "Model Not Loaded", "Please load a model first")
            return
        
        logger.info(f"Sending question: {question}")
        self.llm_worker.generate_answer(question)
    
    def on_stop_generation(self):
        logger.info("User requested stop generation")
        self.llm_worker.stop_generation()
        self.status_bar.showMessage("Generation stopped")
        self.send_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.input_field.setEnabled(True)
    
    def on_clear(self):
        reply = QMessageBox.question(
            self,
            "Clear Conversation",
            "Clear conversation history and context?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.text_display.clear()
            self.llm_worker.clear_context()
            self.current_answer = ""
            self.copy_answer_btn.setEnabled(False)
            
            self.history_manager.save_session()
            self.history_manager.start_new_session()
            
            self.status_bar.showMessage("Cleared")
    
    def copy_last_answer(self):
        if self.current_answer:
            if ClipboardHelper.copy_to_clipboard(self.current_answer):
                self.status_bar.showMessage("Answer copied to clipboard!", 2000)
    
    def copy_all_text(self):
        text = self.text_display.toPlainText()
        if text:
            if ClipboardHelper.copy_to_clipboard(text):
                self.status_bar.showMessage("All text copied to clipboard!", 2000)
    
    
    def show_model_downloader(self):
        dialog = ModelDownloaderDialog(self)
        dialog.model_ready.connect(self.on_model_downloaded)
        dialog.exec()
    
    def on_model_downloaded(self, model_path: str):
        logger.info(f"LLM model ready: {model_path}")
        self.settings_manager.set_model_path(model_path)
        self.settings_manager.set_first_run(False)
        self.llm_worker.load_model(model_path)
    
    def show_history_viewer(self):
        dialog = HistoryViewerDialog(self.history_manager, self)
        dialog.exec()
    
    def show_settings(self):
        dialog = SettingsDialog(self.settings_manager, self)
        dialog.settings_changed.connect(self.on_settings_changed)
        dialog.model_reload_requested.connect(self.on_model_reload_requested)
        dialog.exec()
    
    def show_audio_settings(self):
        dialog = AudioSettingsDialog(self)
        dialog.settings_changed.connect(self.on_audio_settings_changed)
        dialog.exec()
    
    @pyqtSlot()
    def on_settings_changed(self):
        logger.info("Settings changed, applying...")
        
        from utils.themes import ThemeType
        saved_theme = self.settings_manager.settings.value("ui/theme", "dark")
        if saved_theme == "light":
            self.theme_manager.set_theme(ThemeType.LIGHT)
        else:
            self.theme_manager.set_theme(ThemeType.DARK)
        
        self.apply_theme()
        
        opacity = self.settings_manager.get_window_opacity()
        self.setWindowOpacity(opacity)
        
        font_size = int(self.settings_manager.settings.value("ui/font_size", 10))
        self.text_display.setFont(QFont("Segoe UI", font_size))
        self.input_field.setFont(QFont("Segoe UI", font_size))
        
        always_on_top = self.settings_manager.settings.value("ui/always_on_top", True, type=bool)
        flags = self.windowFlags()
        
        if always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        
        self.setWindowFlags(flags)
        self.show()
        
        if self.autosave_timer:
            self.autosave_timer.stop()
        self.setup_autosave()
        
        self.status_bar.showMessage("Settings applied", 2000)

    
    @pyqtSlot()
    def on_audio_settings_changed(self):
        logger.info("Audio settings changed")
        
        if self.audio_worker.is_listening:
            self.audio_worker.stop_listening()
            use_loopback = self.settings_manager.settings.value("audio/use_loopback", True, type=bool)
            self.audio_worker.start_listening(use_loopback=use_loopback)
        
        self.status_bar.showMessage("Audio settings applied", 2000)
    
    @pyqtSlot(str)
    def on_model_reload_requested(self, model_path: str):
        reply = QMessageBox.question(
            self,
            "Reload Model",
            f"This will unload the current model and load:\n{model_path}\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logger.info(f"Reloading LLM model: {model_path}")
            self.llm_worker.clear_context()
            self.llm_worker.unload_model()
            self.llm_worker.load_model(model_path)
    
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    
    def restore_settings(self):
        geometry = self.settings_manager.get_window_geometry()
        if geometry:
            self.restoreGeometry(geometry)
        
        opacity = self.settings_manager.get_window_opacity()
        self.setWindowOpacity(opacity)
    
    def save_settings(self):
        self.settings_manager.set_window_geometry(self.saveGeometry())
        self.settings_manager.sync()
        self.history_manager.save_session()

    def apply_theme(self):
        """Применить текущую тему"""
        stylesheet = self.theme_manager.get_stylesheet()
        
        window_style = """
            QMainWindow {
                border: 2px solid #444;
                border-radius: 10px;
            }
        """
        
        self.setStyleSheet(stylesheet + window_style)
        
        logger.info(f"Theme applied: {self.theme_manager.current_theme.name}")

    def load_and_register_hotkeys(self):
        """Загрузить и зарегистрировать hotkeys из настроек"""
        hotkeys_config = {}
        
        for action in DEFAULT_HOTKEYS.keys():
            hotkey = self.settings_manager.get_hotkey(action)
            if hotkey:
                hotkeys_config[action] = hotkey
        
        success = self.hotkeys_manager.register_hotkeys(hotkeys_config)
        
        if success:
            logger.info("Global hotkeys registered")
        else:
            logger.warning("Failed to register some hotkeys")

    def toggle_window_visibility(self):
        """Переключить видимость окна (hotkey)"""
        if self.is_window_visible:
            self.hide_window_to_tray()
        else:
            self.show_window_from_tray()

    def show_window_from_tray(self):
        """Показать окно из трея"""
        self.show()
        self.activateWindow()
        self.raise_()
        self.is_window_visible = True
        logger.info("Window shown from tray")

    def hide_window_to_tray(self):
        """Скрыть окно в трей"""
        self.hide()
        self.is_window_visible = False
        logger.info("Window hidden to tray")

    def toggle_listening(self):
        """Переключить listening on/off"""
        if not self.stt_worker.transcriber.is_loaded:
            QMessageBox.warning(self, "STT Not Ready", "Please wait for STT model to load")
            return
        
        if self.audio_worker.is_listening:
            self.audio_worker.stop_listening()
            self.audio_status_label.setText("🔴 Not listening")
            self.audio_status_label.setStyleSheet("QLabel { color: #f44336; font-weight: bold; }")
            self.listening_toggle_btn.setText("▶️ Start Listening")
            self.listening_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4caf50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #66bb6a;
                }
            """)
            
            if self.tray_icon:
                self.tray_icon.update_listening_status(False)
            
            if self.notification_manager:
                self.notification_manager.notify_listening_stopped()
            
            logger.info("Audio listening stopped")
        
        else:
            use_loopback = self.settings_manager.settings.value("audio/use_loopback", True, type=bool)
            self.audio_worker.start_listening(use_loopback=use_loopback)
            self.audio_status_label.setText("🟢 Listening...")
            self.audio_status_label.setStyleSheet("QLabel { color: #4caf50; font-weight: bold; }")
            self.listening_toggle_btn.setText("⏸️ Stop Listening")
            self.listening_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #d32f2f;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #f44336;
                }
            """)
            
            #  Update tray
            if self.tray_icon:
                self.tray_icon.update_listening_status(True)
            
            #  Notification
            if self.notification_manager:
                self.notification_manager.notify_listening_started()
            
            logger.info("Audio listening started")

    def toggle_listening_hotkey(self):
        """Переключить listening через hotkey"""
        if self.current_mode == PipelineConfig.MODE_MANUAL:
            self.switch_mode(PipelineConfig.MODE_AUTO)
        
        self.toggle_listening()
    def show_quick_input(self):
        """Показать диалог быстрого ввода"""
        logger.info("Quick input requested")
        self.quick_input_dialog.show()

    def on_quick_question(self, question: str):
        """Обработать вопрос из quick input"""
        logger.info(f"Quick question: {question}")
        
        if not self.is_window_visible:
            self.show_window_from_tray()
        
        if self.current_mode != PipelineConfig.MODE_MANUAL:
            self.switch_mode(PipelineConfig.MODE_MANUAL)
        
        if self.llm_worker.engine.is_loaded():
            self.llm_worker.generate_answer(question)
        else:
            QMessageBox.warning(self, "Model Not Loaded", "Please load LLM model first")

    def quit_application(self):
        """Выйти из приложения (полностью)"""
        logger.info("Quit requested from tray")
        
        reply = QMessageBox.question(
            self,
            "Quit Application",
            "Are you sure you want to quit AI Assistant?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.show()
            self.close()
    
    def closeEvent(self, event: QCloseEvent):
        """Обработать закрытие окна"""
        
        minimize_to_tray = self.settings_manager.get_minimize_to_tray()
        
        if minimize_to_tray and self.is_window_visible:
            event.ignore()
            self.hide_window_to_tray()
            
            if self.settings_manager.settings.value("tray/first_minimize", True, type=bool):
                self.notification_manager.show_info(
                    "Minimized to Tray",
                    "AI Assistant is still running. Right-click tray icon to quit.",
                    duration=5000
                )
                self.settings_manager.settings.setValue("tray/first_minimize", False)
            
            return
        
        logger.info("Closing application")
        
        if self.autosave_timer:
            self.autosave_timer.stop()
        
        self.save_settings()
        
        if self.hotkeys_manager:
            self.hotkeys_manager.unregister_all()
        
        if self.tray_icon:
            self.tray_icon.hide()
        
        if self.llm_worker:
            self.llm_worker.shutdown()
        
        if self.audio_worker:
            self.audio_worker.shutdown()
        
        if self.stt_worker:
            self.stt_worker.shutdown()
        
        event.accept()

