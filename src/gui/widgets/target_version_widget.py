"""
Модуль виджета информации о найденной версии модификации.

TargetVersionWidget отображает информацию о доступном обновлении мода,
включая название версии, changelog, зависимости и кнопку обновления.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QGroupBox, QPushButton)
from PySide6.QtGui import QFont
from PySide6.QtCore import Signal


class TargetVersionWidget(QWidget):
    """Виджет для отображения информации о найденной версии.

    Отображает данные об обновлении мода, включая название новой версии,
    changelog, зависимости и кнопку загрузки обновления.
    """

    NAME_PLACEHOLDER_TEXT = "Выберите мод для проверки"
    DEPS_PLACEHOLDER_TEXT = "Нет зависимостей"
    
    update_requested = Signal(str)
    
    def __init__(self, parent=None):
        """Инициализирует виджет и создает его визуальные компоненты.

        Создает групповой блок, метки и кнопку загрузки обновления.
        Кнопка обновления изначально отключена.
        """
        super().__init__(parent)
        
        self.group_box = QGroupBox("Информация о новой версии", self)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.group_box)
        layout.setContentsMargins(0, 0, 0, 0)

        group_layout = QVBoxLayout(self.group_box)
        
        self.new_version_name = QLabel(self.NAME_PLACEHOLDER_TEXT)
        version_font = QFont()
        version_font.setBold(True)
        self.new_version_name.setFont(version_font)
        group_layout.addWidget(self.new_version_name)
        
        self.changelog = QLabel()
        self.changelog.setWordWrap(True)
        group_layout.addWidget(self.changelog)

        dependencies_layout = QHBoxLayout()
        dependencies_layout.addWidget(QLabel("Зависимости:"))
        # Будет отображать зависимости мода, полученные через api
        self.dependencies = QLabel(self.DEPS_PLACEHOLDER_TEXT)
        dependencies_layout.addWidget(self.dependencies)
        dependencies_layout.addStretch()
        group_layout.addLayout(dependencies_layout)
        
        # Кнопка обновления
        # Запускает процесс загрузки новой версии мода
        # Изначально неактивна, пока не выбран мод с доступным обновлением
        self.update_btn = QPushButton("Загрузить обновление")
        self.update_btn.setEnabled(False)
        group_layout.addWidget(self.update_btn)
