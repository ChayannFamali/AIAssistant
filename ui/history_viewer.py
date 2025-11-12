"""
History Viewer - просмотр истории диалогов
"""
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QPushButton, QTextEdit, QLabel, QMessageBox,
    QSplitter, QListWidgetItem
)
from PyQt6.QtCore import Qt

from utils.history_manager import HistoryManager
from utils.clipboard_helper import ClipboardHelper

logger = logging.getLogger("AIAssistant.HistoryViewer")


class HistoryViewerDialog(QDialog):
    """Диалог просмотра истории"""
    
    def __init__(self, history_manager: HistoryManager, parent=None):
        super().__init__(parent)
        self.history_manager = history_manager
        self.current_session_data = None
        
        self.setup_ui()
        self.load_sessions_list()
        
        self.setWindowTitle("Dialog History")
        self.resize(900, 600)
    
    def setup_ui(self):
        """Создать UI"""
        layout = QVBoxLayout(self)
        
        title = QLabel("📜 Dialog History")
        title_font = title.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_widget = self.create_sessions_panel()
        splitter.addWidget(left_widget)
        
        right_widget = self.create_content_panel()
        splitter.addWidget(right_widget)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        layout.addWidget(splitter)
        
        button_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("Export to Text")
        self.export_btn.clicked.connect(self.export_session)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)
        
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.copy_btn.setEnabled(False)
        button_layout.addWidget(self.copy_btn)
        
        self.delete_btn = QPushButton("Delete Session")
        self.delete_btn.clicked.connect(self.delete_session)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("QPushButton { background-color: #d32f2f; color: white; }")
        button_layout.addWidget(self.delete_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
            QListWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #0d7377;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 5px;
            }
            QLabel {
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
            QPushButton:disabled {
                background-color: #444;
                color: #888;
            }
        """)
    
    def create_sessions_panel(self):
        """Создать панель списка сессий"""
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("Sessions")
        label.setStyleSheet("QLabel { font-weight: bold; font-size: 12px; }")
        layout.addWidget(label)
        
        self.sessions_list = QListWidget()
        self.sessions_list.itemClicked.connect(self.on_session_selected)
        layout.addWidget(self.sessions_list)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_sessions_list)
        layout.addWidget(refresh_btn)
        
        return widget
    
    def create_content_panel(self):
        """Создать панель содержимого"""
        from PyQt6.QtWidgets import QWidget, QVBoxLayout
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.info_label = QLabel("Select a session to view")
        self.info_label.setStyleSheet("QLabel { font-size: 11px; color: #888; }")
        layout.addWidget(self.info_label)
        
        self.content_viewer = QTextEdit()
        self.content_viewer.setReadOnly(True)
        layout.addWidget(self.content_viewer)
        
        return widget
    
    def load_sessions_list(self):
        """Загрузить список сессий"""
        self.sessions_list.clear()
        
        sessions = self.history_manager.list_sessions()
        
        if not sessions:
            item = QListWidgetItem("No sessions found")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.sessions_list.addItem(item)
            return
        
        for session_data in sessions:
            created_at = session_data.get("created_at", "")
            if created_at:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(created_at)
                    date_str = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    date_str = created_at[:16]
            else:
                date_str = "Unknown"
            
            msg_count = session_data.get("message_count", 0)
            stats = session_data.get("stats", {})
            questions = stats.get("total_questions", 0)
            
            item_text = f"{date_str} | {questions} questions, {msg_count} messages"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, session_data)
            self.sessions_list.addItem(item)
        
        logger.info(f"Loaded {len(sessions)} sessions")
    
    def on_session_selected(self, item: QListWidgetItem):
        """Обработать выбор сессии"""
        self.current_session_data = item.data(Qt.ItemDataRole.UserRole)
        
        if not self.current_session_data:
            return
        
        session_id = self.current_session_data["session_id"]
        session = self.history_manager.load_session(session_id)
        
        if not session:
            QMessageBox.warning(self, "Error", "Failed to load session")
            return
        
        self.display_session(session)
        
        self.export_btn.setEnabled(True)
        self.copy_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
    
    def display_session(self, session):
        """Отобразить содержимое сессии"""
        stats = session.stats
        info_text = (
            f"Session: {session.session_id} | "
            f"Questions: {stats.get('total_questions', 0)} | "
            f"Tokens: {stats.get('total_tokens', 0)} | "
            f"Avg: {stats.get('avg_tokens_per_sec', 0):.2f} t/s"
        )
        self.info_label.setText(info_text)
        
        html_parts = []
        
        for msg in session.messages:
            if msg.role == "user":
                html_parts.append(f"<p><b style='color: #4caf50;'>Q:</b> {msg.content}</p>")
            else:
                html_parts.append(f"<p><b style='color: #2196f3;'>A:</b> {msg.content}</p>")
        
        self.content_viewer.setHtml("".join(html_parts))
    
    def export_session(self):
        """Экспортировать сессию в текстовый файл"""
        if not self.current_session_data:
            return
        
        session_id = self.current_session_data["session_id"]
        session = self.history_manager.load_session(session_id)
        
        if not session:
            return
        
        text = self.history_manager.export_session_to_text(session)
        
        from PyQt6.QtWidgets import QFileDialog
        from pathlib import Path
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Session",
            str(Path.home() / f"session_{session_id}.txt"),
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                QMessageBox.information(self, "Success", f"Session exported to:\n{filename}")
                logger.info(f"Session exported: {filename}")
            
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {e}")
    
    def copy_to_clipboard(self):
        """Скопировать сессию в буфер обмена"""
        if not self.current_session_data:
            return
        
        session_id = self.current_session_data["session_id"]
        session = self.history_manager.load_session(session_id)
        
        if not session:
            return
        
        text = self.history_manager.export_session_to_text(session)
        
        if ClipboardHelper.copy_to_clipboard(text):
            QMessageBox.information(self, "Success", "Session copied to clipboard!")
    
    def delete_session(self):
        """Удалить сессию"""
        if not self.current_session_data:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this session?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            session_id = self.current_session_data["session_id"]
            
            if self.history_manager.delete_session(session_id):
                QMessageBox.information(self, "Success", "Session deleted")
                self.load_sessions_list()
                self.content_viewer.clear()
                self.info_label.setText("Select a session to view")
                
                self.export_btn.setEnabled(False)
                self.copy_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
            else:
                QMessageBox.critical(self, "Error", "Failed to delete session")
