"""
Quick Input Dialog - быстрый ввод вопроса по hotkey
"""
import logging
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

logger = logging.getLogger("AIAssistant.QuickInput")


class QuickInputDialog(QDialog):
    """
    Диалог для быстрого ввода вопроса
    Вызывается по Ctrl+Shift+Q
    """
    
    question_submitted = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setup_ui()
        
        # Флаги окна - поверх всего, без рамки
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        
        self.setWindowTitle("Quick Question")
        self.resize(500, 100)
        
        logger.info("QuickInputDialog initialized")
    
    def setup_ui(self):
        """Создать UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter your question here...")
        self.input_field.setFont(QFont("Segoe UI", 12))
        self.input_field.returnPressed.connect(self.submit_question)
        
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 2px solid #0d7377;
                border-radius: 5px;
                padding: 10px;
            }
            QLineEdit:focus {
                border: 2px solid #14a085;
            }
        """)
        
        layout.addWidget(self.input_field)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.submit_btn = QPushButton("Ask (Enter)")
        self.submit_btn.clicked.connect(self.submit_question)
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d7377;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #14a085;
            }
        """)
        button_layout.addWidget(self.submit_btn)
        
        self.cancel_btn = QPushButton("Cancel (Esc)")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                border: 2px solid #0d7377;
                border-radius: 8px;
            }
        """)
    
    def submit_question(self):
        """Отправить вопрос"""
        question = self.input_field.text().strip()
        
        if question:
            logger.info(f"Quick question submitted: {question}")
            self.question_submitted.emit(question)
            self.accept()
        else:
            logger.debug("Empty question, ignoring")
    
    def showEvent(self, event):
        """При показе диалога"""
        super().showEvent(event)
        
        self.input_field.clear()
        
        self.input_field.setFocus()
        
        screen = self.screen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def keyPressEvent(self, event):
        """Обработать нажатие клавиш"""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
