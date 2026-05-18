"""
Модуль виджета выбора папок.

FolderSelectorWidget предоставляет интерфейс для выбора директории с модами
и папки для сохранения обновлений.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QLineEdit, QPushButton, QLabel, QFileDialog)
from PySide6.QtCore import Signal


class FolderSelectorWidget(QWidget):
    """Виджет для выбора директорий.

    Содержит поля для исходной и целевой папки, кнопки открытия диалога выбора папки.
    """
    
    SOURCE_PLACEHOLDER = "Выберите директорию с модами..."
    DESTINATION_PLACEHOLDER = "Выберите директорию для сохранения модов..."

    source_folder_changed = Signal(str)
    destination_folder_changed = Signal(str)
    
    def __init__(self, parent=None):
        """Инициализирует виджет выбора папок и настраивает элементы управления."""
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        
        # Виджеты выбора исходной папки с модами
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Исходная папка:"))
        
        self.source_path = QLineEdit()
        self.source_path.setPlaceholderText(self.SOURCE_PLACEHOLDER)
        self.source_path.setReadOnly(True)
        source_layout.addWidget(self.source_path)
        
        self.source_browse_btn = QPushButton("Обзор...")
        self.source_browse_btn.clicked.connect(self.select_source_folder)
        source_layout.addWidget(self.source_browse_btn)
        
        main_layout.addLayout(source_layout)
        
        # Виджеты выбора папки для сохранения модов
        dest_layout = QHBoxLayout()
        dest_layout.addWidget(QLabel("Папка сохранения:"))
        
        self.dest_path = QLineEdit()
        self.dest_path.setPlaceholderText(self.DESTINATION_PLACEHOLDER)
        self.dest_path.setReadOnly(True)
        dest_layout.addWidget(self.dest_path)
        
        self.dest_browse_btn = QPushButton("Обзор...")
        self.dest_browse_btn.clicked.connect(self.select_dest_folder)
        dest_layout.addWidget(self.dest_browse_btn)
        
        main_layout.addLayout(dest_layout)
    
    def select_source_folder(self):
        """Выбор исходной директории с модами"""
        folder = QFileDialog.getExistingDirectory(self, self.SOURCE_PLACEHOLDER)
        if folder:
            self.source_path.setText(folder)
            self.source_folder_changed.emit(folder)
 
    def select_dest_folder(self):
        """Выбор директории для сохранения"""
        folder = QFileDialog.getExistingDirectory(self, self.DESTINATION_PLACEHOLDER)
        if folder:
            self.dest_path.setText(folder)
            self.destination_folder_changed.emit(folder)
