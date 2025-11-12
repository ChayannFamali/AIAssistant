"""
Performance Widget - виджет отображения метрик производительности
"""
import logging
from typing import List, Deque
from collections import deque

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

from core.config import PerformanceConfig

logger = logging.getLogger("AIAssistant.Performance")


class PerformanceChart(QWidget):
    """Простой график производительности"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_points: Deque[float] = deque(maxlen=PerformanceConfig.MAX_HISTORY_POINTS)
        self.max_value = 20.0  # Максимум для масштабирования
        self.setMinimumHeight(100)
        
        self.setStyleSheet("background-color: #1e1e1e; border: 1px solid #444; border-radius: 5px;")
    
    def add_data_point(self, value: float):
        """Добавить точку данных"""
        self.data_points.append(value)
        
        if value > self.max_value:
            self.max_value = value * 1.2
        
        self.update()
    
    def clear_data(self):
        """Очистить данные"""
        self.data_points.clear()
        self.max_value = 20.0
        self.update()
    
    def paintEvent(self, event):
        """Отрисовка графика"""
        if not self.data_points:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        margin = 5
        chart_width = width - 2 * margin
        chart_height = height - 2 * margin
        
        painter.setPen(QPen(QColor("#333"), 1))
        
        for i in range(5):
            y = margin + (chart_height * i / 4)
            painter.drawLine(margin, int(y), width - margin, int(y))
        
        if len(self.data_points) > 1:
            painter.setPen(QPen(QColor("#0d7377"), 2))
            
            points = []
            step = chart_width / (len(self.data_points) - 1)
            
            for i, value in enumerate(self.data_points):
                x = margin + i * step
                # Инвертировать Y (0 вверху)
                y = margin + chart_height - (value / self.max_value * chart_height)
                points.append((int(x), int(y)))
            
            for i in range(len(points) - 1):
                painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
            
            painter.setBrush(QColor("#0d7377"))
            for x, y in points:
                painter.drawEllipse(x - 2, y - 2, 4, 4)
        
        painter.setPen(QColor("#888"))
        painter.setFont(QFont("Segoe UI", 8))
        
        painter.drawText(margin, margin + 10, f"{self.max_value:.1f} t/s")
        
        painter.drawText(margin, height - margin - 5, "0 t/s")


class PerformanceWidget(QWidget):
    """Виджет отображения метрик производительности"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.stats_history: List[dict] = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Создать UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        title = QLabel("📊 Performance Monitor")
        title.setStyleSheet("QLabel { font-weight: bold; color: #e0e0e0; }")
        layout.addWidget(title)
        
        metrics_frame = QFrame()
        metrics_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #444;
                border-radius: 5px;
            }
        """)
        metrics_layout = QVBoxLayout(metrics_frame)
        
        current_layout = QHBoxLayout()
        
        self.current_tps_label = QLabel("-- t/s")
        self.current_tps_label.setStyleSheet("QLabel { color: #4caf50; font-size: 18px; font-weight: bold; }")
        current_layout.addWidget(QLabel("Current:"))
        current_layout.addWidget(self.current_tps_label)
        current_layout.addStretch()
        
        metrics_layout.addLayout(current_layout)
        
        avg_layout = QHBoxLayout()
        
        self.avg_tps_label = QLabel("-- t/s")
        self.avg_tps_label.setStyleSheet("QLabel { color: #2196f3; }")
        avg_layout.addWidget(QLabel("Average:"))
        avg_layout.addWidget(self.avg_tps_label)
        avg_layout.addStretch()
        
        metrics_layout.addLayout(avg_layout)
        
        ttft_layout = QHBoxLayout()
        
        self.ttft_label = QLabel("-- s")
        self.ttft_label.setStyleSheet("QLabel { color: #ff9800; }")
        ttft_layout.addWidget(QLabel("First Token:"))
        ttft_layout.addWidget(self.ttft_label)
        ttft_layout.addStretch()
        
        metrics_layout.addLayout(ttft_layout)
        
        total_layout = QHBoxLayout()
        
        self.total_time_label = QLabel("-- s")
        self.total_time_label.setStyleSheet("QLabel { color: #888; }")
        total_layout.addWidget(QLabel("Total Time:"))
        total_layout.addWidget(self.total_time_label)
        total_layout.addStretch()
        
        metrics_layout.addLayout(total_layout)
        
        layout.addWidget(metrics_frame)
        
        if PerformanceConfig.SHOW_CHART:
            chart_label = QLabel("Tokens/sec History")
            chart_label.setStyleSheet("QLabel { color: #888; font-size: 9px; margin-top: 10px; }")
            layout.addWidget(chart_label)
            
            self.chart = PerformanceChart()
            layout.addWidget(self.chart)
        else:
            self.chart = None
        
        summary_layout = QHBoxLayout()
        
        self.total_generations_label = QLabel("Generations: 0")
        self.total_generations_label.setStyleSheet("QLabel { color: #888; font-size: 9px; }")
        summary_layout.addWidget(self.total_generations_label)
        
        summary_layout.addStretch()
        
        clear_btn_label = QLabel("<a href='#'>Clear</a>")
        clear_btn_label.setStyleSheet("QLabel { color: #0d7377; font-size: 9px; }")
        clear_btn_label.setTextFormat(Qt.TextFormat.RichText)
        clear_btn_label.linkActivated.connect(self.clear_stats)
        summary_layout.addWidget(clear_btn_label)
        
        layout.addLayout(summary_layout)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)
    
    def update_stats(self, stats: dict):
        """
        Обновить метрики
        
        Args:
            stats: Словарь со статистикой
        """
        self.stats_history.append(stats)
        
        tps = stats.get('tokens_per_second', 0)
        ttft = stats.get('time_to_first_token', 0)
        total_time = stats.get('total_time', 0)
        
        self.current_tps_label.setText(f"{tps:.2f} t/s")
        self.ttft_label.setText(f"{ttft:.2f} s")
        self.total_time_label.setText(f"{total_time:.2f} s")
        
        if self.stats_history:
            avg_tps = sum(s.get('tokens_per_second', 0) for s in self.stats_history) / len(self.stats_history)
            self.avg_tps_label.setText(f"{avg_tps:.2f} t/s")
        
        if self.chart:
            self.chart.add_data_point(tps)
        
        self.total_generations_label.setText(f"Generations: {len(self.stats_history)}")
        
        logger.debug(f"Performance updated: {tps:.2f} t/s")
    
    def clear_stats(self):
        """Очистить статистику"""
        self.stats_history.clear()
        
        self.current_tps_label.setText("-- t/s")
        self.avg_tps_label.setText("-- t/s")
        self.ttft_label.setText("-- s")
        self.total_time_label.setText("-- s")
        self.total_generations_label.setText("Generations: 0")
        
        if self.chart:
            self.chart.clear_data()
        
        logger.info("Performance stats cleared")
