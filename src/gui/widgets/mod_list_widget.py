"""
Модуль виджета списка модов.

ModListWidget управляет отображением списка файлов модификаций из выбранной
директории, показывает заглушку, когда папка не выбрана или пуста, и
оповещает приложение о выборе мода (клике на мод).
"""
import logging

from pathlib import Path

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                               QListWidgetItem, QLabel, QAbstractItemView, QPushButton)
from PySide6.QtCore import QSize, Signal, Qt, QEvent
from PySide6.QtGui import QFont, QColor, QIcon, QPixmap

import core.icon_loader as icon_loader
from core.mod_info import ModInfo
from core.config import get_resource_path


logger = logging.getLogger(__name__)


class ModListWidget(QWidget):
    """Виджет для работы со списком модов.

    Обеспечивает отображение списка модов, создавая для каждого элемента (мода) отдельный виджет.
    """
    
    PLACEHOLDER_TEXT = "Выберите папку с модами"

    mod_selected = Signal(ModInfo)
    
    def __init__(self, parent=None):
        """Инициализирует виджет списка модов и настраивает его макет."""
        super().__init__(parent)
        
        # Хранит текущий выделенный элемент для предотвращения 
        # его автоматического выделения при клике правой кнопкой мыши
        self.previewed_item = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        top_bar_layout = QHBoxLayout()
        
        title = QLabel("Список модов")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        top_bar_layout.addWidget(title)

        top_bar_layout.addStretch()

        self.select_all_btn = QPushButton("Выделить всё")
        self.select_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        top_bar_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("Снять выделение")
        self.deselect_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        top_bar_layout.addWidget(self.deselect_all_btn)

        layout.addLayout(top_bar_layout)

        self.mod_list = QListWidget()
        # Включает возможность удобного множественного выбора
        self.mod_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.mod_list.itemClicked.connect(self.on_item_selected)

        # Перехватываем события мыши до того, как они попадут в QListWidget,
        # чтобы самостоятельно управлять выделением элементов при кликах
        self.mod_list.viewport().installEventFilter(self)

        layout.addWidget(self.mod_list)

        self.select_all_btn.clicked.connect(self.mod_list.selectAll)
        self.deselect_all_btn.clicked.connect(self.mod_list.clearSelection)

        self.show_placeholder()
    
    def show_placeholder(self):
        """Показывает подсказку, когда не выбрана директория с модами"""
        self.mod_list.clear()
        placeholder = QListWidgetItem(self.PLACEHOLDER_TEXT)
        placeholder.setForeground(QColor("#7B7A7A"))
        # Отключаем возможность выбирать подсказку как элемент списка
        placeholder.setFlags(placeholder.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        self.mod_list.addItem(placeholder)

    def on_item_selected(self, item):
        """Обработка клика по элементу списка.
        
        Извлекает ModInfo из кликнутого элемента и отправляет сигнал.
        """
        mod_info = item.data(Qt.ItemDataRole.UserRole)
        if mod_info:
            self.mod_selected.emit(mod_info)
    
    def update_mod_list(self, mods: list[ModInfo]):
        """Принимает список объектов ModInfo и отображает их.
        
        Для каждого мода создается кастомный виджет с названием, тегами и добавляется иконка.

        Args:
            mods: Список объектов ModInfo, которые нужно отобразить в списке модов.
        """
        # Сбрасываем память о выделенном элементе перед очисткой списка
        self.previewed_item = None
        
        self.mod_list.clear()
        self.mod_list.setIconSize(QSize(40, 40))
        
        if not mods:
            self.show_placeholder()
            return
        
        for mod_info in mods:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, mod_info)
            item.setIcon(self._pick_icon(mod_info))

            item_widget = self._create_item_widget(mod_info)

            # Устанавливаем размер элемента списка равным размеру кастомного виджета
            item.setSizeHint(item_widget.sizeHint())
            
            self.mod_list.addItem(item)
            self.mod_list.setItemWidget(item, item_widget)

    def _create_item_widget(self, mod_info: ModInfo) -> QWidget:
        """Создает кастомный виджет для элемента списка модов.
        
        Args:
            mod_info: Объект ModInfo, содержащий информацию о моде, которая будет отображаться в виджете.
        Returns:
            QWidget: Кастомный виджет для элемента списка модов, включающий название и теги.
        """
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(5, 10, 5, 10)

        # Настройка названия мода
        full_name = mod_info.name or "Неизвестный архив"
        max_chars = 24
        if len(full_name) > max_chars:
            display_name = f"{full_name[:max_chars]}..."
        else:
            display_name = full_name

        name_label = QLabel(display_name)
        name_font = QFont()
        name_font.setPointSize(14)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setToolTip(full_name)
        
        # Цвет текста, зависит от наличия обновления
        if mod_info.update_checked and not mod_info.has_update:
            name_label.setStyleSheet("color: #8b76a0;") 
        else:
            name_label.setStyleSheet("color: #ceb2ec;")

        item_layout.addWidget(name_label)
        item_layout.addStretch() # Прижимаем тег к правому краю

        # Тег наличия обновления
        if mod_info.has_update:
            update_tag = QLabel("⬆")
            update_font = QFont()
            update_font.setBold(True)
            update_font.setPointSize(10)
            update_tag.setFont(update_font)
            update_tag.setStyleSheet("background-color: #349bef; color: white; border-radius: 4px; padding: 2px 6px;")
            item_layout.addWidget(update_tag)
            
        # Тег источника данных
        tag_label = QLabel(mod_info.data_source)
        tag_font = QFont()
        tag_font.setBold(True)
        tag_font.setPointSize(10)
        tag_label.setFont(tag_font)

        if mod_info.data_source == "API":
            # Зеленый фон для найденных в API
            tag_label.setStyleSheet("background-color: #62ae64; color: white; border-radius: 4px; padding: 2px 6px;")
        elif mod_info.data_source == "Local":
            # Оранжевый фон для распаршенных локально
            tag_label.setStyleSheet("background-color: #c59142; color: white; border-radius: 4px; padding: 2px 6px;")
        else:
            # Серый фон для нераспознанных
            tag_label.setStyleSheet("background-color: #9E9E9E; color: white; border-radius: 4px; padding: 2px 6px;")
            
        item_layout.addWidget(tag_label)
            
        return item_widget

    def _pick_icon(self, mod_info: ModInfo) -> QIcon:
        """Выбирает и масштабирует иконку для элемента списка модов.
        
        Выбирает иконку по принципу API(из проекта) > Локальная(из архива) > Стандартная,
        и масштабирует её для единообразия отображения в списке.

        Args:
            mod_info: Объект ModInfo, содержащий информацию о моде, включая данные для иконки.
        Returns:
            QIcon: Иконка для отображения в списке модов.
        """
        default_icon_path = get_resource_path("src/resources/icons/default_mod_icon.png")
        
        pixmap = QPixmap()

        if mod_info.api_icon_data:
            pixmap.loadFromData(mod_info.api_icon_data)

        if pixmap.isNull() and mod_info.source_path and mod_info.icon_path:
            pixmap = icon_loader.load_icon_from_archive(mod_info.source_path, mod_info.icon_path)

        if pixmap.isNull():
            logger.warning(f"Не удалось загрузить иконку для '{mod_info.name}'. Загружаем стандартную.")
            pixmap.load(str(default_icon_path))

        # Масштабируем иконку ровно до 40x40 пикселей
        scaled_pixmap = pixmap.scaled(
            40, 40,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        return QIcon(scaled_pixmap)
    
    def get_selected_mods(self) -> list[ModInfo]:
        """Возвращает список ModInfo для всех выделенных (подсвеченных) элементов."""
        selected_mods = []
        for item in self.mod_list.selectedItems():
            # UserRole используется для хранения ModInfo в каждом элементе списка
            mod_info = item.data(Qt.ItemDataRole.UserRole)
            if mod_info:
                selected_mods.append(mod_info)
                
        return selected_mods
    
    def get_all_mods(self) -> list[ModInfo]:
        """Возвращает список ModInfo для всех загруженных в список модов."""
        all_mods = []
        for i in range(self.mod_list.count()):
            item = self.mod_list.item(i)
            # UserRole используется для хранения ModInfo в каждом элементе списка
            mod_info = item.data(Qt.ItemDataRole.UserRole)
            if mod_info:
                all_mods.append(mod_info)
        return all_mods
    
    def eventFilter(self, source, event) -> bool:
        """Перехватывает события мыши до того, как они попадут в QListWidget.
        
        В частности используется для управления выделением элементов при кликах,
        чтобы при первом клике показывать информацию о моде, а при втором уже выделять сам элемент списка.
        """
        if source is self.mod_list.viewport() and event.type() == QEvent.Type.MouseButtonPress:
            
            # Перехватываем левую кнопку мыши
            if event.button() == Qt.MouseButton.LeftButton:
                item = self.mod_list.itemAt(event.pos())
                
                if item:
                    # Если это первый клик по моду
                    if self.previewed_item != item:
                        self.previewed_item = item
                        self.on_item_selected(item)
                        return True # Не передаем клик Qt: элемент не выделяется в списке
                        
                    # Если это второй клик по тому же самому моду
                    else:
                        self.previewed_item = None # Сбрасываем память
                        return False # Отдаем клик Qt: теперь он выделит элемент как обычно
                else:
                    # Если клик пришелся на пустое пространство списка
                    self.previewed_item = None
                    
        # При нажатии всех остальных кнопок ничего не делаем, возвращаем False
        return super().eventFilter(source, event)
        