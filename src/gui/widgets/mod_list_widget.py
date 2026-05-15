"""
Модуль виджета списка модов.

ModListWidget управляет отображением списка файлов модификаций из выбранной
директории, показывает заглушку, когда папка не выбрана или пуста, и
оповещает приложение о выборе мода (клике на мод).
"""

from pathlib import Path

from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel
from PySide6.QtCore import QSize, Signal, Qt
from PySide6.QtGui import QFont, QColor, QIcon

from core.mod_parser import ModInfo
import core.icon_loader as icon_loader


class ModListWidget(QWidget):
    """Виджет для работы со списком модов.

    Обеспечивает отображение списка модов, заглушку при отсутствии файлов и
    сигнал выбора элемента.
    """
    
    PLACEHOLDER_TEXT = "Выберите папку с модами"

    mod_selected = Signal(ModInfo)
    
    def __init__(self, parent=None):
        """Инициализирует виджет списка модов и настраивает его макет."""
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Список модов")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        layout.addWidget(title)

        self.mod_list = QListWidget()
        self.mod_list.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.mod_list)

        self.show_placeholder()
    
    def show_placeholder(self):
        """Показывает подсказку, когда не выбрана директория с модами"""
        self.mod_list.clear()
        placeholder = QListWidgetItem(self.PLACEHOLDER_TEXT)
        placeholder.setForeground(QColor("#7B7A7A"))
        # Отключаем возможность выбирать подсказку как элемент списка
        placeholder.setFlags(placeholder.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        self.mod_list.addItem(placeholder)
    
    def update_mod_list(self, mods: list[ModInfo]):
        """Принимает список объектов ModInfo и отображает их."""
        self.mod_list.clear()

        self.mod_list.setIconSize(QSize(40, 40))
        
        if not mods:
            self.show_placeholder()
            return
        
        for mod_info in mods:
            item = QListWidgetItem(mod_info.name)

            item_font = QFont()
            item_font.setPointSize(14)
            item_font.setBold(True)
            item.setForeground(QColor("#8A6CDC"))
            item.setFont(item_font)

            item.setData(Qt.ItemDataRole.UserRole, mod_info)

            item.setIcon(self._set_icon(mod_info))

            self.mod_list.addItem(item)
    
    def on_item_clicked(self, item):
        """Обработка клика по элементу списка
        
        Извлекает ModInfo из кликнутого элемента и отправляет сигнал"""
        mod_info = item.data(Qt.ItemDataRole.UserRole)
        if mod_info:
            self.mod_selected.emit(mod_info)

    def _set_icon(self, mod_info: ModInfo) -> QIcon:
        """Устанавливает иконку для элемента списка модов."""
        default_icon_path = Path(__file__).resolve().parents[2] / "resources" / "icons" / "default_mod_icon.png"
            
        if mod_info.source_path and mod_info.icon_path:
            pixmap = icon_loader.load_icon_from_archive(mod_info.source_path, mod_info.icon_path)
            if not pixmap.isNull():
                return QIcon(pixmap)    

        print(f"Мод '{mod_info.name}' не содержит иконки.")
        return QIcon(str(default_icon_path))
        