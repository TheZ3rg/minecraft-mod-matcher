"""
Модуль виджета информации о текущем моде.

SourceModWidget отображает название модификации, её описание, текущую версию
и автора. Используется для показа сведений о выбранном моде.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QGroupBox)
from PySide6.QtGui import QFont

from core.mod_info import ModInfo


class SourceModWidget(QWidget):
    """Виджет для отображения информации о выбранном моде.

    Показывает имя мода, описание и текущую версию. Если мод не выбран,
    отображаются заполнители.
    """
    
    LABEL_PLACEHOLDER_TEXT = "Мод не выбран"
    DESCRIPTION_PLACEHOLDER_TEXT = "Выберите мод из списка слева"
    VERSIONS_PLACEHOLDER_TEXT = "—"

    def __init__(self, parent=None):
        """Инициализирует виджет и задаёт начальные заполнители для полей."""
        super().__init__(parent)
        
        self.group_box = QGroupBox("Текущая версия мода", self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.group_box)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group_layout = QVBoxLayout(self.group_box)
        
        self.mod_name = QLabel(self.LABEL_PLACEHOLDER_TEXT)
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(16)
        self.mod_name.setFont(name_font)
        self.mod_name.setWordWrap(True)
        group_layout.addWidget(self.mod_name)
        
        self.description = QLabel(self.DESCRIPTION_PLACEHOLDER_TEXT)
        description_font = QFont()
        description_font.setBold(True)
        description_font.setPointSize(12)
        self.description.setFont(description_font)
        self.description.setWordWrap(True)
        group_layout.addWidget(self.description)

        versions_layout = QHBoxLayout()
        versions_layout.addWidget(QLabel("Текущая версия:"))
        self.versions = QLabel(self.VERSIONS_PLACEHOLDER_TEXT)
        versions_layout.addWidget(self.versions)
        versions_layout.addStretch()
        group_layout.addLayout(versions_layout)

    def update_info(self, mod_info: ModInfo | None) -> None:
        """Обновляет текстовые поля виджета на основе данных о моде.

        Args:
            mod_info: Объект ModInfo с данными мода. Если None, возвращает заглушки.
        """
        if not mod_info:
            self.mod_name.setText(self.LABEL_PLACEHOLDER_TEXT)
            self.description.setText(self.DESCRIPTION_PLACEHOLDER_TEXT)
            self.versions.setText(self.VERSIONS_PLACEHOLDER_TEXT)
            return

        self.mod_name.setText(mod_info.name or "Неизвестный мод")

        self.description.setText(mod_info.description or "Описание отсутствует.")

        # Формируем строку версии (пример: "1.0.0 (Minecraft: xx.xx) [Fabric]")
        version_text = mod_info.version or "Неизвестная версия"
        if mod_info.minecraft_version:
            version_text += f" (Minecraft: {mod_info.minecraft_version})"
        if mod_info.loader_type:
            version_text += f" [{mod_info.loader_type}]"
        self.versions.setText(version_text)
