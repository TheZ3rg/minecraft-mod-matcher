"""
Модуль виджета статуса.
Отображает системные сообщения, ошибки и прогресс выполнения фоновых задач.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QSizePolicy
from PySide6.QtCore import Qt

class StatusWidget(QWidget):
    """Виджет для отображения статуса приложения.
    
    Содержит QLabel для отображения сообщений и QProgressBar для отображения прогресса выполнения задач.
    Предоставляет методы для отображения различных типов сообщений (информационные, ошибки, успехи) и управления прогресс-баром.

    Attributes:
        status_label (QLabel): текстовое поле для отображения статуса.
        progress_bar (QProgressBar): Полоса прогресса для отображения выполнения задач.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.status_label = QLabel("Готов к работе")
        self.status_label.setStyleSheet("color: #d5d3d3; font-weight: bold;")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
    
    def show_message(self, message: str, color: str = "white"):
        """Показывает обычное сообщение заданного цвета."""
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.status_label.setText(message)
        self.progress_bar.setVisible(False)

    def update_text(self, message: str):
        """Обновляет только текст сообщения."""
        self.status_label.setText(message)

    def show_success(self, message: str):
        """Показывает сообщение об успехе (green)."""
        self.show_message(message, "#4CAF50")

    def show_error(self, message: str):
        """Показывает сообщение об ошибке (red)."""
        self.show_message(f"⚠️ {message}", "#F44336")

    def show_info(self, message: str):
        """Показывает информационное сообщение (gray)."""
        self.show_message(message, "#9E9E9E")

    def start_indeterminate_progress(self, message: str):
        """Показывает сообщение и включает бесконечный прогресс-бар."""
        self.show_message(message, "#2196F3")
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0) 
        self.progress_bar.setVisible(True)

    def start_progress(self, message: str):
        """Показывает сообщение (blue) и включает полосу загрузки."""
        self.show_message(message, "#2196F3")
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 100) 
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

    def update_progress(self, current: int, total: int):
        """Обновляет значение полосы загрузки."""
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        if not self.progress_bar.isTextVisible():
            self.progress_bar.setTextVisible(True)    
        if not self.progress_bar.isVisible():
            self.progress_bar.setVisible(True)

    def clear(self):
        """Очищает статус и скрывает прогресс-бар."""
        self.status_label.setText("Готов к работе")
        self.status_label.setStyleSheet("color: #d5d3d3; font-weight: bold;")
        self.progress_bar.setVisible(False)
