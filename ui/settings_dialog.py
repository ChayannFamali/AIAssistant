"""
Settings Dialog - диалог настроек приложения
"""
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QGroupBox, QSlider, QLineEdit,
    QFileDialog, QTabWidget, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from utils.settings_manager import SettingsManager
from core.config import AppConfig, ModelConfig, GenerationParams

logger = logging.getLogger("AIAssistant.Settings")


class SettingsDialog(QDialog):
    """Диалог настроек приложения"""
    
    model_reload_requested = pyqtSignal(str) 
    settings_changed = pyqtSignal()
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.changes_made = False
        
        self.setup_ui()
        self.load_current_settings()
        
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(600, 500)
    
    def setup_ui(self):
        """Создать UI"""
        layout = QVBoxLayout(self)
        
        title = QLabel("⚙️ Application Settings")
        title_font = title.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        tabs = QTabWidget()
        
        tabs.addTab(self.create_general_tab(), "General")
        
        tabs.addTab(self.create_model_tab(), "Model")
        
        tabs.addTab(self.create_generation_tab(), "Generation")
        
        tabs.addTab(self.create_ui_tab(), "Interface")
        
        tabs.addTab(self.create_hotkeys_tab(), "Hotkeys")
        
        tabs.addTab(self.create_tray_tab(), "Tray & Notifications")
        
        layout.addWidget(tabs)
        
        button_layout = QHBoxLayout()
        
        self.restore_defaults_btn = QPushButton("Restore Defaults")
        self.restore_defaults_btn.clicked.connect(self.restore_defaults)
        button_layout.addWidget(self.restore_defaults_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setDefault(True)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
            QTabWidget::pane {
                border: 1px solid #444;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #1e1e1e;
                color: #e0e0e0;
                padding: 8px 20px;
                border: 1px solid #444;
            }
            QTabBar::tab:selected {
                background-color: #0d7377;
            }
            QLabel {
                color: #e0e0e0;
            }
            QGroupBox {
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QSpinBox, QDoubleSpinBox, QLineEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 5px;
            }
            QComboBox {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #e0e0e0;
                margin-right: 5px;
            }
            QCheckBox {
                color: #e0e0e0;
            }
            QCheckBox::indicator {
                border: 1px solid #444;
                border-radius: 3px;
                background-color: #1e1e1e;
            }
            QCheckBox::indicator:checked {
                background-color: #0d7377;
            }
            QPushButton {
                background-color: #0d7377;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #14a085;
            }
            QPushButton:pressed {
                background-color: #0a5f62;
            }
        """)
    
    def create_general_tab(self) -> QWidget:
        """Вкладка общих настроек"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        autosave_group = QGroupBox("History Auto-Save")
        autosave_layout = QFormLayout()
        
        self.autosave_enabled = QCheckBox("Enable auto-save")
        autosave_layout.addRow("", self.autosave_enabled)
        
        self.autosave_interval = QSpinBox()
        self.autosave_interval.setRange(10, 600)
        self.autosave_interval.setSuffix(" seconds")
        autosave_layout.addRow("Save interval:", self.autosave_interval)
        
        self.max_history_files = QSpinBox()
        self.max_history_files.setRange(10, 1000)
        self.max_history_files.setSuffix(" files")
        autosave_layout.addRow("Max history files:", self.max_history_files)
        
        autosave_group.setLayout(autosave_layout)
        layout.addWidget(autosave_group)
        
        startup_group = QGroupBox("Startup")
        startup_layout = QFormLayout()
        
        self.start_minimized = QCheckBox("Start minimized to tray")
        startup_layout.addRow("", self.start_minimized)
        
        self.load_last_session = QCheckBox("Load last session on startup")
        startup_layout.addRow("", self.load_last_session)
        
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)
        
        layout.addStretch()
        
        return widget
    
    def create_model_tab(self) -> QWidget:
        """Вкладка настроек модели"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        model_group = QGroupBox("Model File")
        model_layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        self.model_path_edit = QLineEdit()
        self.model_path_edit.setReadOnly(True)
        path_layout.addWidget(self.model_path_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_model_file)
        path_layout.addWidget(browse_btn)
        
        model_layout.addLayout(path_layout)
        
        info_label = QLabel("⚠️ Changing model requires application restart")
        info_label.setStyleSheet("QLabel { color: #ff9800; font-size: 10px; }")
        model_layout.addWidget(info_label)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        params_group = QGroupBox("Model Parameters")
        params_layout = QFormLayout()
        
        self.n_ctx = QSpinBox()
        self.n_ctx.setRange(512, 32768)
        self.n_ctx.setSingleStep(512)
        self.n_ctx.setSuffix(" tokens")
        params_layout.addRow("Context size:", self.n_ctx)
        
        self.n_threads = QSpinBox()
        self.n_threads.setRange(1, 32)
        self.n_threads.setSpecialValueText("Auto-detect")
        params_layout.addRow("CPU threads:", self.n_threads)
        
        self.n_batch = QSpinBox()
        self.n_batch.setRange(128, 2048)
        self.n_batch.setSingleStep(128)
        params_layout.addRow("Batch size:", self.n_batch)
        
        self.use_mlock = QCheckBox("Use mlock (prevent swap)")
        params_layout.addRow("", self.use_mlock)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        layout.addStretch()
        
        return widget
    
    def create_generation_tab(self) -> QWidget:
        """Вкладка параметров генерации"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        gen_group = QGroupBox("Generation Parameters")
        gen_layout = QFormLayout()
        
        temp_layout = QHBoxLayout()
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setSingleStep(0.1)
        self.temperature.setDecimals(1)
        temp_layout.addWidget(self.temperature)
        
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(0, 20)
        self.temp_slider.valueChanged.connect(
            lambda v: self.temperature.setValue(v / 10.0)
        )
        self.temperature.valueChanged.connect(
            lambda v: self.temp_slider.setValue(int(v * 10))
        )
        temp_layout.addWidget(self.temp_slider)
        
        gen_layout.addRow("Temperature:", temp_layout)
        
        temp_help = QLabel("Lower = more factual, Higher = more creative")
        temp_help.setStyleSheet("QLabel { color: #888; font-size: 9px; }")
        gen_layout.addRow("", temp_help)
        
        self.max_tokens = QSpinBox()
        self.max_tokens.setRange(50, 2048)
        self.max_tokens.setSingleStep(50)
        self.max_tokens.setSuffix(" tokens")
        gen_layout.addRow("Max tokens:", self.max_tokens)
        
        self.top_p = QDoubleSpinBox()
        self.top_p.setRange(0.0, 1.0)
        self.top_p.setSingleStep(0.05)
        self.top_p.setDecimals(2)
        gen_layout.addRow("Top P:", self.top_p)
        
        self.top_k = QSpinBox()
        self.top_k.setRange(1, 100)
        gen_layout.addRow("Top K:", self.top_k)
        
        self.repeat_penalty = QDoubleSpinBox()
        self.repeat_penalty.setRange(1.0, 2.0)
        self.repeat_penalty.setSingleStep(0.1)
        self.repeat_penalty.setDecimals(1)
        gen_layout.addRow("Repeat penalty:", self.repeat_penalty)
        
        gen_group.setLayout(gen_layout)
        layout.addWidget(gen_group)
        
        presets_group = QGroupBox("Presets")
        presets_layout = QHBoxLayout()
        
        factual_btn = QPushButton("Factual")
        factual_btn.clicked.connect(lambda: self.apply_preset("factual"))
        presets_layout.addWidget(factual_btn)
        
        balanced_btn = QPushButton("Balanced")
        balanced_btn.clicked.connect(lambda: self.apply_preset("balanced"))
        presets_layout.addWidget(balanced_btn)
        
        creative_btn = QPushButton("Creative")
        creative_btn.clicked.connect(lambda: self.apply_preset("creative"))
        presets_layout.addWidget(creative_btn)
        
        presets_group.setLayout(presets_layout)
        layout.addWidget(presets_group)
        
        layout.addStretch()
        
        return widget
    
    def create_ui_tab(self) -> QWidget:
        """Вкладка настроек интерфейса"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout()
        
        self.theme = QComboBox()
        self.theme.addItems(["Dark", "Light"])
        self.theme.currentIndexChanged.connect(self.on_theme_changed)
        appearance_layout.addRow("Theme:", self.theme)
        
        theme_info = QLabel("⚠️ Theme change applies immediately")
        theme_info.setStyleSheet("QLabel { color: #ff9800; font-size: 9px; }")
        appearance_layout.addRow("", theme_info)
        
        opacity_layout = QHBoxLayout()
        self.opacity_spinbox = QDoubleSpinBox()
        self.opacity_spinbox.setRange(0.3, 1.0)
        self.opacity_spinbox.setSingleStep(0.05)
        self.opacity_spinbox.setDecimals(2)
        self.opacity_spinbox.setSuffix(" (opacity)")
        opacity_layout.addWidget(self.opacity_spinbox)
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.valueChanged.connect(
            lambda v: self.opacity_spinbox.setValue(v / 100.0)
        )
        self.opacity_spinbox.valueChanged.connect(
            lambda v: self.opacity_slider.setValue(int(v * 100))
        )
        opacity_layout.addWidget(self.opacity_slider)
        
        appearance_layout.addRow("Window opacity:", opacity_layout)
        
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 20)
        self.font_size.setSuffix(" pt")
        appearance_layout.addRow("Font size:", self.font_size)
        
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)
        
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QFormLayout()
        
        self.always_on_top = QCheckBox("Always on top")
        behavior_layout.addRow("", self.always_on_top)
        
        self.show_stats = QCheckBox("Show performance stats")
        behavior_layout.addRow("", self.show_stats)
        
        self.animate_text = QCheckBox("Animate text appearance")
        behavior_layout.addRow("", self.animate_text)
        
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)
        
        layout.addStretch()
        
        return widget
    
    def load_current_settings(self):
        """Загрузить текущие настройки"""
        self.autosave_enabled.setChecked(
            self.settings_manager.settings.value("general/autosave_enabled", True, type=bool)
        )
        self.autosave_interval.setValue(
            int(self.settings_manager.settings.value("general/autosave_interval", 60))
        )
        self.max_history_files.setValue(
            int(self.settings_manager.settings.value("general/max_history_files", 100))
        )
        self.start_minimized.setChecked(
            self.settings_manager.settings.value("general/start_minimized", False, type=bool)
        )
        self.load_last_session.setChecked(
            self.settings_manager.settings.value("general/load_last_session", False, type=bool)
        )
        
        self.model_path_edit.setText(
            self.settings_manager.get_model_path() or ""
        )
        
        model_config = ModelConfig()
        self.n_ctx.setValue(
            int(self.settings_manager.settings.value("model/n_ctx", model_config.n_ctx))
        )
        self.n_threads.setValue(
            int(self.settings_manager.settings.value("model/n_threads", 0))
        )
        self.n_batch.setValue(
            int(self.settings_manager.settings.value("model/n_batch", model_config.n_batch))
        )
        self.use_mlock.setChecked(
            self.settings_manager.settings.value("model/use_mlock", True, type=bool)
        )
        
        self.temperature.setValue(self.settings_manager.get_temperature())
        self.max_tokens.setValue(self.settings_manager.get_max_tokens())
        
        gen_params = GenerationParams()
        self.top_p.setValue(
            float(self.settings_manager.settings.value("generation/top_p", gen_params.top_p))
        )
        self.top_k.setValue(
            int(self.settings_manager.settings.value("generation/top_k", gen_params.top_k))
        )
        self.repeat_penalty.setValue(
            float(self.settings_manager.settings.value("generation/repeat_penalty", gen_params.repeat_penalty))
        )
        
        theme_index = ["dark", "light", "system"].index(
            self.settings_manager.settings.value("ui/theme", "dark")
        )
        self.theme.setCurrentIndex(theme_index)
        
        self.opacity_spinbox.setValue(self.settings_manager.get_window_opacity())
        
        self.font_size.setValue(
            int(self.settings_manager.settings.value("ui/font_size", 10))
        )
        self.always_on_top.setChecked(
            self.settings_manager.settings.value("ui/always_on_top", True, type=bool)
        )
        self.show_stats.setChecked(
            self.settings_manager.settings.value("ui/show_stats", True, type=bool)
        )
        self.animate_text.setChecked(
            self.settings_manager.settings.value("ui/animate_text", True, type=bool)
        )

        self.hotkey_toggle_window.setText(
            self.settings_manager.get_hotkey("toggle_window")
        )
        self.hotkey_toggle_listening.setText(
            self.settings_manager.get_hotkey("toggle_listening")
        )
        self.hotkey_quick_input.setText(
            self.settings_manager.get_hotkey("quick_input")
        )
        self.hotkey_stop_generation.setText(
            self.settings_manager.get_hotkey("stop_generation")
        )
        self.minimize_to_tray.setChecked(
            self.settings_manager.get_minimize_to_tray()
        )
        self.start_minimized.setChecked(
            self.settings_manager.get_start_minimized()
        )
        self.notifications_enabled.setChecked(
            self.settings_manager.get_notifications_enabled()
        )
        self.notification_sound.setChecked(
            self.settings_manager.get_notification_sound()
        )
        notif_enabled = self.settings_manager.get_notifications_enabled()
        self.notify_question_detected.setChecked(
            self.settings_manager.settings.value("notifications/question_detected", notif_enabled, type=bool)
        )
        self.notify_answer_ready.setChecked(
            self.settings_manager.settings.value("notifications/answer_ready", notif_enabled, type=bool)
        )
        self.notify_listening_change.setChecked(
            self.settings_manager.settings.value("notifications/listening_change", notif_enabled, type=bool)
        )
 
    def save_settings(self):
        """Сохранить настройки"""
        self.settings_manager.settings.setValue("general/autosave_enabled", self.autosave_enabled.isChecked())
        self.settings_manager.settings.setValue("general/autosave_interval", self.autosave_interval.value())
        self.settings_manager.settings.setValue("general/max_history_files", self.max_history_files.value())
        self.settings_manager.settings.setValue("general/start_minimized", self.start_minimized.isChecked())
        self.settings_manager.settings.setValue("general/load_last_session", self.load_last_session.isChecked())
        
        new_model_path = self.model_path_edit.text()
        old_model_path = self.settings_manager.get_model_path()
        
        if new_model_path != old_model_path:
            self.settings_manager.set_model_path(new_model_path)
            reply = QMessageBox.question(
                self,
                "Model Changed",
                "Model path has changed. Reload model now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.model_reload_requested.emit(new_model_path)
        
        self.settings_manager.settings.setValue("model/n_ctx", self.n_ctx.value())
        self.settings_manager.settings.setValue("model/n_threads", self.n_threads.value())
        self.settings_manager.settings.setValue("model/n_batch", self.n_batch.value())
        self.settings_manager.settings.setValue("model/use_mlock", self.use_mlock.isChecked())
        
        self.settings_manager.set_temperature(self.temperature.value())
        self.settings_manager.set_max_tokens(self.max_tokens.value())
        self.settings_manager.settings.setValue("generation/top_p", self.top_p.value())
        self.settings_manager.settings.setValue("generation/top_k", self.top_k.value())
        self.settings_manager.settings.setValue("generation/repeat_penalty", self.repeat_penalty.value())
        
        theme_map = ["dark", "light", "system"]
        self.settings_manager.settings.setValue("ui/theme", theme_map[self.theme.currentIndex()])
        self.settings_manager.set_window_opacity(self.opacity_spinbox.value())
        self.settings_manager.settings.setValue("ui/font_size", self.font_size.value())
        self.settings_manager.settings.setValue("ui/always_on_top", self.always_on_top.isChecked())
        self.settings_manager.settings.setValue("ui/show_stats", self.show_stats.isChecked())
        self.settings_manager.settings.setValue("ui/animate_text", self.animate_text.isChecked())

        self.settings_manager.set_hotkey("toggle_window", self.hotkey_toggle_window.text())
        self.settings_manager.set_hotkey("toggle_listening", self.hotkey_toggle_listening.text())
        self.settings_manager.set_hotkey("quick_input", self.hotkey_quick_input.text())
        self.settings_manager.set_hotkey("stop_generation", self.hotkey_stop_generation.text())

        self.settings_manager.set_minimize_to_tray(self.minimize_to_tray.isChecked())
        self.settings_manager.set_start_minimized(self.start_minimized.isChecked())
        self.settings_manager.set_notifications_enabled(self.notifications_enabled.isChecked())
        self.settings_manager.set_notification_sound(self.notification_sound.isChecked())

        self.settings_manager.settings.setValue(
            "notifications/question_detected", 
            self.notify_question_detected.isChecked()
        )
        self.settings_manager.settings.setValue(
            "notifications/answer_ready", 
            self.notify_answer_ready.isChecked()
        )
        self.settings_manager.settings.setValue(
            "notifications/listening_change", 
            self.notify_listening_change.isChecked()
        )

        self.settings_manager.sync()
        
        self.changes_made = True
        self.settings_changed.emit()
        
        QMessageBox.information(self, "Success", "Settings saved successfully!")
        logger.info("Settings saved")
        
        self.accept()
    
    def browse_model_file(self):
        """Открыть диалог выбора файла модели"""
        from pathlib import Path
        
        current_path = self.model_path_edit.text() or str(Path.home())
        
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Model File",
            current_path,
            "GGUF Files (*.gguf);;All Files (*.*)"
        )
        
        if filename:
            self.model_path_edit.setText(filename)
    
    def apply_preset(self, preset_name: str):
        """Применить пресет параметров генерации"""
        if preset_name == "factual":
            self.temperature.setValue(0.2)
            self.top_p.setValue(0.9)
            self.top_k.setValue(40)
            self.repeat_penalty.setValue(1.1)
        
        elif preset_name == "balanced":
            self.temperature.setValue(0.5)
            self.top_p.setValue(0.85)
            self.top_k.setValue(40)
            self.repeat_penalty.setValue(1.1)
        
        elif preset_name == "creative":
            self.temperature.setValue(0.8)
            self.top_p.setValue(0.9)
            self.top_k.setValue(50)
            self.repeat_penalty.setValue(1.05)
        
        logger.info(f"Applied preset: {preset_name}")
        
    def on_theme_changed(self, index: int):
        """
        Обработать изменение темы (применяется сразу)
        
        Args:
            index: 0 = Dark, 1 = Light
        """
        from utils.themes import ThemeManager, ThemeType
        
        theme_manager = ThemeManager()
        
        if index == 0: 
            theme_manager.set_theme(ThemeType.DARK)
        else: 
            theme_manager.set_theme(ThemeType.LIGHT)
        
        stylesheet = theme_manager.get_stylesheet()
        self.setStyleSheet(stylesheet)
        
        if self.parent():
            self.parent().apply_theme()
        
        logger.info(f"Theme changed to: {theme_manager.current_theme.name}")

        
    def restore_defaults(self):
        """Восстановить настройки по умолчанию"""
        reply = QMessageBox.question(
            self,
            "Restore Defaults",
            "Are you sure you want to restore default settings?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings_manager.settings.clear()
            
            self.load_current_settings()
            
            QMessageBox.information(self, "Success", "Default settings restored")
            logger.info("Settings restored to defaults")
            
    def create_hotkeys_tab(self) -> QWidget:
        """Вкладка настроек горячих клавиш"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        hotkeys_group = QGroupBox("Global Hotkeys")
        hotkeys_layout = QFormLayout()
        
        info_label = QLabel("Configure global keyboard shortcuts (work even when window is hidden)")
        info_label.setStyleSheet("QLabel { color: #888; font-size: 9px; }")
        info_label.setWordWrap(True)
        hotkeys_layout.addRow("", info_label)
        
        self.hotkey_toggle_window = QLineEdit()
        self.hotkey_toggle_window.setPlaceholderText("e.g. ctrl+shift+a")
        hotkeys_layout.addRow("Show/Hide Window:", self.hotkey_toggle_window)
        
        self.hotkey_toggle_listening = QLineEdit()
        self.hotkey_toggle_listening.setPlaceholderText("e.g. ctrl+shift+s")
        hotkeys_layout.addRow("Start/Stop Listening:", self.hotkey_toggle_listening)
        
        self.hotkey_quick_input = QLineEdit()
        self.hotkey_quick_input.setPlaceholderText("e.g. ctrl+shift+q")
        hotkeys_layout.addRow("Quick Question:", self.hotkey_quick_input)
        
        self.hotkey_stop_generation = QLineEdit()
        self.hotkey_stop_generation.setPlaceholderText("e.g. ctrl+shift+x")
        hotkeys_layout.addRow("Stop Generation:", self.hotkey_stop_generation)
        
        hotkeys_group.setLayout(hotkeys_layout)
        layout.addWidget(hotkeys_group)
        
        warning = QLabel("⚠️ Changes require application restart to take effect")
        warning.setStyleSheet("QLabel { color: #ff9800; font-size: 10px; }")
        layout.addWidget(warning)
        
        layout.addStretch()
        
        return widget

    def create_tray_tab(self) -> QWidget:
        """Вкладка настроек трея и уведомлений"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        tray_group = QGroupBox("System Tray")
        tray_layout = QFormLayout()
        
        self.minimize_to_tray = QCheckBox("Minimize to tray instead of closing")
        tray_layout.addRow("", self.minimize_to_tray)
        
        self.start_minimized = QCheckBox("Start minimized to tray")
        tray_layout.addRow("", self.start_minimized)
        
        tray_group.setLayout(tray_layout)
        layout.addWidget(tray_group)
        
        notif_group = QGroupBox("Notifications")
        notif_layout = QFormLayout()
        
        self.notifications_enabled = QCheckBox("Enable notifications")
        notif_layout.addRow("", self.notifications_enabled)
        
        self.notification_sound = QCheckBox("Play sound with notifications")
        notif_layout.addRow("", self.notification_sound)
        
        notif_types = QLabel("Show notifications for:")
        notif_types.setStyleSheet("QLabel { font-weight: bold; margin-top: 10px; }")
        notif_layout.addRow("", notif_types)
        
        self.notify_question_detected = QCheckBox("Question detected")
        notif_layout.addRow("", self.notify_question_detected)
        
        self.notify_answer_ready = QCheckBox("Answer ready")
        notif_layout.addRow("", self.notify_answer_ready)
        
        self.notify_listening_change = QCheckBox("Listening started/stopped")
        notif_layout.addRow("", self.notify_listening_change)
        
        notif_group.setLayout(notif_layout)
        layout.addWidget(notif_group)
        
        layout.addStretch()
        
        return widget
