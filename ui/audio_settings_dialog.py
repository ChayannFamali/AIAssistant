"""
Audio Settings Dialog - диалог настроек аудио
"""
import logging
import sounddevice as sd
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QGroupBox,
    QCheckBox, QSpinBox, QSlider, QMessageBox,
    QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.config import AudioConfig, STTConfig

logger = logging.getLogger("AIAssistant.AudioSettings")


class AudioSettingsDialog(QDialog):
    """Диалог настроек аудио и STT"""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setup_ui()
        self.load_current_settings()
        
        self.setWindowTitle("Audio & STT Settings")
        self.setModal(True)
        self.resize(500, 400)
    
    def setup_ui(self):
        """Создать UI"""
        layout = QVBoxLayout(self)
        
        title = QLabel("🎤 Audio & Speech-to-Text Settings")
        title_font = title.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        audio_group = QGroupBox("Audio Capture")
        audio_layout = QFormLayout()
        
        self.audio_source = QComboBox()
        self.audio_source.addItems(["System Audio (Loopback)", "Microphone"])
        audio_layout.addRow("Source:", self.audio_source)
        
        self.device_combo = QComboBox()
        self.refresh_devices()
        audio_layout.addRow("Device:", self.device_combo)
        
        refresh_btn = QPushButton("Refresh Devices")
        refresh_btn.clicked.connect(self.refresh_devices)
        audio_layout.addRow("", refresh_btn)
        
        self.vad_mode = QSpinBox()
        self.vad_mode.setRange(0, 3)
        self.vad_mode.setSuffix(" (0=least, 3=most aggressive)")
        audio_layout.addRow("VAD Mode:", self.vad_mode)
        
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)
        
        stt_group = QGroupBox("Speech-to-Text")
        stt_layout = QFormLayout()
        
        self.model_size = QComboBox()
        self.model_size.addItems(["tiny", "base", "small", "medium", "large"])
        stt_layout.addRow("Whisper Model:", self.model_size)
        
        model_info = QLabel("tiny: fastest, base: balanced, small: better quality")
        model_info.setStyleSheet("QLabel { color: #888; font-size: 9px; }")
        stt_layout.addRow("", model_info)
        
        self.language = QComboBox()
        self.language.addItems(["Auto-detect", "English", "Russian", "Spanish", "German", "French"])
        stt_layout.addRow("Language:", self.language)
        
        self.vad_filter = QCheckBox("Enable Whisper VAD filter")
        stt_layout.addRow("", self.vad_filter)
        
        stt_group.setLayout(stt_layout)
        layout.addWidget(stt_group)
        
        question_group = QGroupBox("Question Detection")
        question_layout = QFormLayout()
        
        self.auto_detect = QCheckBox("Automatically detect questions")
        question_layout.addRow("", self.auto_detect)
        
        self.cooldown = QSpinBox()
        self.cooldown.setRange(1, 60)
        self.cooldown.setSuffix(" seconds")
        question_layout.addRow("Cooldown:", self.cooldown)
        
        question_group.setLayout(question_layout)
        layout.addWidget(question_group)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        
        test_btn = QPushButton("Test Audio")
        test_btn.clicked.connect(self.test_audio)
        button_layout.addWidget(test_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
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
            QComboBox, QSpinBox {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 5px;
            }
            QCheckBox {
                color: #e0e0e0;
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
        """)
    
    def refresh_devices(self):
        """Обновить список аудио устройств"""
        self.device_combo.clear()
        
        try:
            devices = sd.query_devices()
            
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    name = device['name']
                    self.device_combo.addItem(f"[{i}] {name}", userData=i)
        
        except Exception as e:
            logger.error(f"Failed to query devices: {e}")
            self.device_combo.addItem("Error loading devices")
    
    def load_current_settings(self):
        """Загрузить текущие настройки"""
        from PyQt6.QtCore import QSettings
        settings = QSettings("YourCompany", "AI Assistant")
        
        use_loopback = settings.value("audio/use_loopback", True, type=bool)
        self.audio_source.setCurrentIndex(0 if use_loopback else 1)
        
        self.vad_mode.setValue(int(settings.value("audio/vad_mode", AudioConfig.VAD_MODE)))
        
        model_size = settings.value("stt/model_size", STTConfig.MODEL_SIZE)
        index = self.model_size.findText(model_size)
        if index >= 0:
            self.model_size.setCurrentIndex(index)
        
        language = settings.value("stt/language", "Auto-detect")
        lang_index = self.language.findText(language)
        if lang_index >= 0:
            self.language.setCurrentIndex(lang_index)
        
        self.vad_filter.setChecked(settings.value("stt/vad_filter", True, type=bool))
        
        self.auto_detect.setChecked(settings.value("question/auto_detect", True, type=bool))
        self.cooldown.setValue(int(settings.value("question/cooldown", 5)))
    
    def save_settings(self):
        """Сохранить настройки"""
        from PyQt6.QtCore import QSettings
        settings = QSettings("YourCompany", "AI Assistant")
        use_loopback = self.audio_source.currentIndex() == 0
        settings.setValue("audio/use_loopback", use_loopback)
        settings.setValue("audio/vad_mode", self.vad_mode.value())
        
        device_index = self.device_combo.currentData()
        if device_index is not None:
            settings.setValue("audio/device_index", device_index)
        
        settings.setValue("stt/model_size", self.model_size.currentText())
        settings.setValue("stt/language", self.language.currentText())
        settings.setValue("stt/vad_filter", self.vad_filter.isChecked())
        
        settings.setValue("question/auto_detect", self.auto_detect.isChecked())
        settings.setValue("question/cooldown", self.cooldown.value())
        
        settings.sync()
        
        self.settings_changed.emit()
        
        QMessageBox.information(self, "Success", "Audio settings saved!")
        logger.info("Audio settings saved")
        
        self.accept()
    
    def test_audio(self):
        """Тестировать аудио захват"""
        QMessageBox.information(
            self,
            "Test Audio",
            "Audio testing will be implemented in full version.\n\n"
            "For now, check that your device is properly configured in Windows Sound Settings."
        )
