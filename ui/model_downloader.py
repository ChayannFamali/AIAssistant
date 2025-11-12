"""
Model Downloader Dialog - диалог для скачивания модели с Hugging Face
"""
import os
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from huggingface_hub import hf_hub_download
from huggingface_hub.utils import HfHubHTTPError

from core.config import AppConfig

logger = logging.getLogger("AIAssistant.Downloader")


class DownloadWorker(QThread):
    """Worker для скачивания модели в отдельном потоке"""
    
    progress = pyqtSignal(float)  # Прогресс 0.0-1.0
    finished = pyqtSignal(str)  # Путь к скачанному файлу
    error = pyqtSignal(str)  # Сообщение об ошибке
    
    def __init__(self, repo_id: str, filename: str, local_dir: str):
        super().__init__()
        self.repo_id = repo_id
        self.filename = filename
        self.local_dir = local_dir
        self.should_stop = False
    
    def run(self):
        """Скачать модель с Hugging Face"""
        try:
            logger.info(f"Downloading {self.filename} from {self.repo_id}")
            
            # huggingface_hub не предоставляет удобный callback, поэтому используем индикацию
            self.progress.emit(0.1)
            
            model_path = hf_hub_download(
                repo_id=self.repo_id,
                filename=self.filename,
                local_dir=self.local_dir,
                resume_download=True,
                local_dir_use_symlinks=False
            )
            
            if self.should_stop:
                logger.info("Download cancelled")
                return
            
            self.progress.emit(1.0)
            logger.info(f"Downloaded to: {model_path}")
            self.finished.emit(model_path)
        
        except HfHubHTTPError as e:
            logger.error(f"HTTP error downloading model: {e}")
            self.error.emit(f"Network error: {e.response.status_code}")
        
        except Exception as e:
            logger.error(f"Error downloading model: {e}", exc_info=True)
            self.error.emit(str(e))
    
    def stop(self):
        """Остановить скачивание"""
        self.should_stop = True


class ModelDownloaderDialog(QDialog):
    """
    Диалог для скачивания или выбора модели
    Показывается при первом запуске если модель не найдена
    """
    
    model_ready = pyqtSignal(str)  # Путь к модели
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.download_worker: Optional[DownloadWorker] = None
        self.model_path: Optional[str] = None
        
        self.setup_ui()
        self.setWindowTitle("Download AI Model")
        self.setModal(True)
        self.resize(500, 250)
    
    def setup_ui(self):
        """Создать UI элементы"""
        layout = QVBoxLayout(self)
        
        title = QLabel("AI Model Required")
        title_font = title.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        description = QLabel(
            f"This application requires an AI model to function.\n\n"
            f"Model: {AppConfig.HF_REPO_ID}\n"
            f"Size: ~{AppConfig.HF_MODEL_SIZE_MB} MB\n\n"
            f"You can download it automatically or select an existing file."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)
        
        layout.addSpacing(20)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("QLabel { color: #666; }")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("Download Automatically")
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setMinimumHeight(40)
        button_layout.addWidget(self.download_btn)
        
        self.browse_btn = QPushButton("Select Existing File...")
        self.browse_btn.clicked.connect(self.browse_file)
        self.browse_btn.setMinimumHeight(40)
        button_layout.addWidget(self.browse_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setMinimumHeight(40)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def start_download(self):
        """Начать автоматическое скачивание"""
        logger.info("Starting automatic model download")
        
        self.download_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.cancel_btn.setText("Downloading...")
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Connecting to Hugging Face...")
        
        models_dir = AppConfig.get_models_dir()
        self.download_worker = DownloadWorker(
            repo_id=AppConfig.HF_REPO_ID,
            filename=AppConfig.HF_FILENAME,
            local_dir=models_dir
        )
        
        self.download_worker.progress.connect(self.on_download_progress)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.error.connect(self.on_download_error)
        
        self.download_worker.start()
    
    def on_download_progress(self, progress: float):
        """Обновить прогресс скачивания"""
        percentage = int(progress * 100)
        self.progress_bar.setValue(percentage)
        
        if progress < 0.2:
            self.status_label.setText("Downloading model...")
        elif progress < 0.9:
            self.status_label.setText(f"Downloading... {percentage}%")
        else:
            self.status_label.setText("Finalizing download...")
    
    def on_download_finished(self, model_path: str):
        """Скачивание завершено"""
        logger.info(f"Download finished: {model_path}")
        
        self.progress_bar.setValue(100)
        self.status_label.setText("Download complete!")
        
        self.model_path = model_path
        
        QMessageBox.information(
            self,
            "Success",
            f"Model downloaded successfully!\n\nPath: {model_path}"
        )
        
        self.model_ready.emit(model_path)
        self.accept()
    
    def on_download_error(self, error_msg: str):
        """Ошибка скачивания"""
        logger.error(f"Download error: {error_msg}")
        
        self.progress_bar.setVisible(False)
        self.status_label.setText("")
        
        self.download_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.cancel_btn.setText("Cancel")
        
        QMessageBox.critical(
            self,
            "Download Failed",
            f"Failed to download model:\n\n{error_msg}\n\n"
            "Please check your internet connection or select an existing file."
        )
    
    def browse_file(self):
        """Открыть диалог выбора файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Model File",
            str(Path.home()),
            "GGUF Files (*.gguf);;All Files (*.*)"
        )
        
        if file_path:
            logger.info(f"User selected model: {file_path}")
            
            if not os.path.exists(file_path):
                QMessageBox.warning(self, "Error", "File does not exist")
                return
            
            if not file_path.endswith('.gguf'):
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Selected file does not have .gguf extension. Are you sure this is a valid model?"
                )
            
            self.model_path = file_path
            self.model_ready.emit(file_path)
            self.accept()
    
    def closeEvent(self, event):
        """Обработать закрытие окна"""
        if self.download_worker and self.download_worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Cancel Download?",
                "Download is in progress. Do you want to cancel?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.download_worker.stop()
                self.download_worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
