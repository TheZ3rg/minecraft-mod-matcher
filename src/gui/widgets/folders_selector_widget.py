"""
Модуль виджета выбора папок.

FolderSelectorWidget предоставляет интерфейс для выбора директории с модами
и папки для сохранения обновлений, а также сигнал запроса на создание бэкапа.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QLineEdit, QPushButton, QLabel, QFileDialog)
from PySide6.QtCore import Signal, Qt


class FolderSelectorWidget(QWidget):
    """Виджет для выбора папок и управления запросом резервного копирования.

    Содержит поля для исходной и целевой папки, кнопки открытия диалога выбора папки
    и кнопку запуска создания бэкапа модов.
    """
    
    SOURCE_PLACEHOLDER = "Выберите директорию с модами..."
    DESTINATION_PLACEHOLDER = "Выберите директорию для сохранения обновлений..."

    source_folder_changed = Signal(str)
    destination_folder_changed = Signal(str)
    backup_requested = Signal(str, str)
    
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
        
        self.backup_btn = QPushButton("💾 Создать бэкап модов")
        self.backup_btn.clicked.connect(self._on_backup_clicked)
        self.backup_btn.setEnabled(False)
        main_layout.addWidget(self.backup_btn)
        main_layout.setAlignment(self.backup_btn, Qt.AlignmentFlag.AlignRight)
    
    def select_source_folder(self):
        """Выбор исходной папки с модами"""
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с модами")
        if folder:
            self.source_path.setText(folder)
            self.source_folder_changed.emit(folder)
            self.update_backup_button_state()
    
    def select_dest_folder(self):
        """Выбор папки сохранения"""
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения обновлений")
        if folder:
            self.dest_path.setText(folder)
            self.destination_folder_changed.emit(folder)
            self.update_backup_button_state()
    
    def update_backup_button_state(self):
        """Обновляет состояние кнопки бэкапа"""
        if self.source_path.text() and self.dest_path.text():
            self.backup_btn.setEnabled(True)
        else:
            self.backup_btn.setEnabled(False)
    
    def _on_backup_clicked(self):
        """Обработчик клика по кнопке бэкапа"""
        self.backup_requested.emit(
            self.source_path.text(),
            self.dest_path.text()
        )
