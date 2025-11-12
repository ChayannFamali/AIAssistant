"""
Statistics Viewer - просмотр расширенной статистики
"""
import logging
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QComboBox, QHeaderView, QFileDialog, QMessageBox,
    QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from utils.statistics_manager import StatisticsManager
from utils.clipboard_helper import ClipboardHelper

logger = logging.getLogger("AIAssistant.StatisticsViewer")


class StatisticsViewerDialog(QDialog):
    """Диалог просмотра статистики"""
    
    def __init__(self, stats_manager: StatisticsManager, parent=None):
        super().__init__(parent)
        self.stats_manager = stats_manager
        
        self.setup_ui()
        self.load_statistics()
        
        self.setWindowTitle("Statistics & Analytics")
        self.resize(900, 700)
    
    def setup_ui(self):
        """Создать UI"""
        layout = QVBoxLayout(self)
        
        
        title = QLabel("📊 Usage Statistics")
        title_font = title.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        tabs = QTabWidget()
        
        tabs.addTab(self.create_summary_tab(), "Summary")
        tabs.addTab(self.create_timeline_tab(), "Timeline")
        tabs.addTab(self.create_top_questions_tab(), "Top Questions")
        tabs.addTab(self.create_export_tab(), "Export")
        
        layout.addWidget(tabs)
        
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_statistics)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #e0e0e0;
            }
            QTableWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #444;
                gridline-color: #444;
            }
            QTableWidget::item:selected {
                background-color: #0d7377;
            }
            QHeaderView::section {
                background-color: #2b2b2b;
                color: #e0e0e0;
                padding: 5px;
                border: 1px solid #444;
                font-weight: bold;
            }
            QTabWidget::pane {
                border: 1px solid #444;
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
            QGroupBox {
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
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
            QComboBox {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #444;
                padding: 5px;
            }
        """)
    
    def create_summary_tab(self) -> QWidget:
        """Вкладка сводной статистики"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        overall_group = QGroupBox("Overall Statistics")
        overall_layout = QFormLayout()
        
        self.total_questions_label = QLabel("0")
        self.total_questions_label.setStyleSheet("QLabel { color: #4caf50; font-size: 18px; font-weight: bold; }")
        overall_layout.addRow("Total Questions:", self.total_questions_label)
        
        self.total_tokens_label = QLabel("0")
        self.total_tokens_label.setStyleSheet("QLabel { color: #2196f3; font-size: 18px; font-weight: bold; }")
        overall_layout.addRow("Total Tokens:", self.total_tokens_label)
        
        self.total_time_label = QLabel("0 hours")
        overall_layout.addRow("Total Time:", self.total_time_label)
        
        self.avg_tokens_label = QLabel("0")
        overall_layout.addRow("Avg Tokens/Question:", self.avg_tokens_label)
        
        self.avg_time_label = QLabel("0 sec")
        overall_layout.addRow("Avg Time/Question:", self.avg_time_label)
        
        overall_group.setLayout(overall_layout)
        layout.addWidget(overall_group)
        
        usage_group = QGroupBox("Usage Statistics")
        usage_layout = QFormLayout()
        
        self.days_used_label = QLabel("0")
        usage_layout.addRow("Days Used:", self.days_used_label)
        
        self.questions_per_day_label = QLabel("0")
        usage_layout.addRow("Avg Questions/Day:", self.questions_per_day_label)
        
        self.first_use_label = QLabel("-")
        usage_layout.addRow("First Use:", self.first_use_label)
        
        self.last_use_label = QLabel("-")
        usage_layout.addRow("Last Use:", self.last_use_label)
        
        usage_group.setLayout(usage_layout)
        layout.addWidget(usage_group)
        
        layout.addStretch()
        
        return widget
    
    def create_timeline_tab(self) -> QWidget:
        """Вкладка временной шкалы"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        period_layout = QHBoxLayout()
        
        period_layout.addWidget(QLabel("Period:"))
        
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Last 7 days", "Last 30 days", "Last 90 days", "All time"])
        self.period_combo.currentIndexChanged.connect(self.update_timeline)
        period_layout.addWidget(self.period_combo)
        
        period_layout.addStretch()
        
        layout.addLayout(period_layout)
        
        self.timeline_table = QTableWidget()
        self.timeline_table.setColumnCount(4)
        self.timeline_table.setHorizontalHeaderLabels(["Date", "Questions", "Tokens", "Avg Time (sec)"])
        
        header = self.timeline_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.timeline_table)
        
        return widget
    
    def create_top_questions_tab(self) -> QWidget:
        """Вкладка топ вопросов"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info = QLabel("Most frequently asked questions:")
        info.setStyleSheet("QLabel { color: #888; font-size: 10px; }")
        layout.addWidget(info)
        
        self.top_questions_table = QTableWidget()
        self.top_questions_table.setColumnCount(4)
        self.top_questions_table.setHorizontalHeaderLabels(["Question", "Count", "Avg Tokens", "Avg Time (sec)"])
        
        header = self.top_questions_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.top_questions_table)
        
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_top_questions)
        layout.addWidget(copy_btn)
        
        return widget
    
    def create_export_tab(self) -> QWidget:
        """Вкладка экспорта"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("Export your statistics:"))
        
        csv_group = QGroupBox("CSV Export")
        csv_layout = QVBoxLayout()
        
        csv_info = QLabel("Export all questions and answers to CSV file (Excel compatible)")
        csv_info.setWordWrap(True)
        csv_info.setStyleSheet("QLabel { color: #888; font-size: 10px; }")
        csv_layout.addWidget(csv_info)
        
        csv_btn = QPushButton("Export to CSV")
        csv_btn.clicked.connect(self.export_to_csv)
        csv_layout.addWidget(csv_btn)
        
        csv_group.setLayout(csv_layout)
        layout.addWidget(csv_group)
        
        excel_group = QGroupBox("Excel Export")
        excel_layout = QVBoxLayout()
        
        excel_info = QLabel("Export statistics with multiple sheets (requires pandas and openpyxl)")
        excel_info.setWordWrap(True)
        excel_info.setStyleSheet("QLabel { color: #888; font-size: 10px; }")
        excel_layout.addWidget(excel_info)
        
        excel_btn = QPushButton("Export to Excel")
        excel_btn.clicked.connect(self.export_to_excel)
        excel_layout.addWidget(excel_btn)
        
        excel_group.setLayout(excel_layout)
        layout.addWidget(excel_group)
        
        layout.addStretch()
        
        return widget
    
    def load_statistics(self):
        """Загрузить и отобразить статистику"""
        self.stats_manager.stats_data = self.stats_manager.load_stats()
        
        self.update_summary()
        self.update_timeline()
        self.update_top_questions()
    
    def update_summary(self):
        """Обновить сводную статистику"""
        summary = self.stats_manager.get_summary_stats()
        
        self.total_questions_label.setText(f"{summary['total_questions']:,}")
        self.total_tokens_label.setText(f"{summary['total_tokens']:,}")
        
        hours = summary['total_time'] / 3600
        self.total_time_label.setText(f"{hours:.1f} hours")
        
        self.avg_tokens_label.setText(f"{summary['avg_tokens_per_question']}")
        self.avg_time_label.setText(f"{summary['avg_time_per_question']} sec")
        
        self.days_used_label.setText(f"{summary['days_used']}")
        self.questions_per_day_label.setText(f"{summary['questions_per_day']}")
        
        self.first_use_label.setText(summary['first_use'])
        self.last_use_label.setText(summary['last_use'])
    
    def update_timeline(self):
        """Обновить временную шкалу"""
        period_map = {
            0: 7,    
            1: 30,  
            2: 90,  
            3: 999999  
        }
        
        days = period_map.get(self.period_combo.currentIndex(), 30)
        
        timeline_data = self.stats_manager.get_stats_by_period(days)
        
        self.timeline_table.setRowCount(len(timeline_data))
        
        for row, data in enumerate(timeline_data):
            date_item = QTableWidgetItem(data['date'])
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.timeline_table.setItem(row, 0, date_item)
            
            questions_item = QTableWidgetItem(str(data['questions']))
            questions_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if data['questions'] > 0:
                questions_item.setForeground(Qt.GlobalColor.green)
            self.timeline_table.setItem(row, 1, questions_item)
            
            tokens_item = QTableWidgetItem(f"{data['tokens']:,}")
            tokens_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.timeline_table.setItem(row, 2, tokens_item)
            
            avg_time = data.get('avg_time', 0.0)
            time_item = QTableWidgetItem(f"{avg_time:.2f}")
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.timeline_table.setItem(row, 3, time_item)
    
    def update_top_questions(self):
        """Обновить топ вопросов"""
        top_questions = self.stats_manager.get_top_questions(limit=10)
        
        self.top_questions_table.setRowCount(len(top_questions))
        
        for row, data in enumerate(top_questions):
            question_item = QTableWidgetItem(data['question'])
            self.top_questions_table.setItem(row, 0, question_item)
            
            count_item = QTableWidgetItem(str(data['count']))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            count_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            count_item.setForeground(Qt.GlobalColor.cyan)
            self.top_questions_table.setItem(row, 1, count_item)
            
            tokens_item = QTableWidgetItem(str(data['avg_tokens']))
            tokens_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.top_questions_table.setItem(row, 2, tokens_item)
            
            time_item = QTableWidgetItem(f"{data['avg_time']:.2f}")
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.top_questions_table.setItem(row, 3, time_item)
    
    def copy_top_questions(self):
        """Скопировать топ вопросов в буфер обмена"""
        top_questions = self.stats_manager.get_top_questions(limit=10)
        
        lines = ["Top 10 Questions:\n"]
        for i, data in enumerate(top_questions, 1):
            lines.append(f"{i}. {data['question']} (asked {data['count']} times)")
        
        text = "\n".join(lines)
        
        if ClipboardHelper.copy_to_clipboard(text):
            QMessageBox.information(self, "Success", "Top questions copied to clipboard!")
    
    def export_to_csv(self):
        """Экспортировать в CSV"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export to CSV",
            str(Path.home() / f"statistics_{datetime.now().strftime('%Y%m%d')}.csv"),
            "CSV Files (*.csv);;All Files (*.*)"
        )
        
        if filename:
            try:
                self.stats_manager.export_to_csv(filename)
                QMessageBox.information(
                    self,
                    "Success",
                    f"Statistics exported to:\n{filename}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Failed to export CSV:\n{str(e)}"
                )
    
    def export_to_excel(self):
        """Экспортировать в Excel"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export to Excel",
            str(Path.home() / f"statistics_{datetime.now().strftime('%Y%m%d')}.xlsx"),
            "Excel Files (*.xlsx);;All Files (*.*)"
        )
        
        if filename:
            try:
                self.stats_manager.export_to_excel(filename)
                QMessageBox.information(
                    self,
                    "Success",
                    f"Statistics exported to:\n{filename}\n\n"
                    "Contains 4 sheets:\n"
                    "- All Questions\n"
                    "- Daily Stats\n"
                    "- Top Questions\n"
                    "- Summary"
                )
            except ImportError:
                QMessageBox.critical(
                    self,
                    "Missing Dependencies",
                    "Excel export requires pandas and openpyxl.\n\n"
                    "Install with:\npip install pandas openpyxl"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Failed to export Excel:\n{str(e)}"
                )
