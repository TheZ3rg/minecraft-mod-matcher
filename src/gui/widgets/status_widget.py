"""
Модуль виджета статуса.
Отображает системные сообщения, ошибки и прогресс выполнения фоновых задач.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt

class StatusWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Текстовая метка для сообщений
        self.status_label = QLabel("Готов к работе")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Полоса прогресса (по умолчанию скрыта)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def show_message(self, message: str, color: str = "white"):
        """Показывает обычное сообщение заданного цвета."""
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.status_label.setText(message)
        self.progress_bar.setVisible(False)

    def show_success(self, message: str):
        """Показывает сообщение об успехе (зеленое)."""
        self.show_message(message, "#4CAF50")

    def show_error(self, message: str):
        """Показывает сообщение об ошибке (красное)."""
        self.show_message(f"⚠️ {message}", "#F44336")

    def show_info(self, message: str):
        """Показывает информационное сообщение."""
        self.show_message(message, "#9E9E9E")

    def start_progress(self, message: str):
        """Показывает сообщение и включает полосу загрузки."""
        self.show_message(message, "#2196F3") # Синий цвет для процесса
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

    def update_progress(self, current: int, total: int):
        """Обновляет значение полосы загрузки."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        if not self.progress_bar.isVisible():
            self.progress_bar.setVisible(True)
