"""
Модуль, содержащий главное окно приложения ModMatcher.

MainWindow — основное окно приложения, которое управляет интерфейсом пользователя,
отображает список модов, информацию о них, а также предоставляет элементы управления
для фильтрации и резервного копирования.
"""

from PySide6.QtWidgets import (QMainWindow, QMessageBox, QWidget, QHBoxLayout, 
                               QVBoxLayout, QSplitter, QComboBox, QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from pathlib import Path

from .widgets.mod_list_widget import ModListWidget
from .widgets.source_mod_widget import SourceModWidget
from .widgets.target_version_widget import TargetVersionWidget
from .widgets.folders_selector_widget import FolderSelectorWidget

import core.backup as backup
import core.mod_parser as mod_parser
import core.file_scanner as file_scanner
from core.mod_info import ModInfo

from api.minecraft_versions import MinecraftVersions


class MainWindow(QMainWindow):
    """Главное окно приложения ModMatcher.

    Предоставляет пользовательский интерфейс для:
        - Указания директории с модами и директории для загрузки.
        - Отображения списка модов.
        - Фильтрации модов по версии Minecraft и загрузчику.
        - Просмотра информации о выбранном моде.
        - Просмотра информации о найденной версии мода.
        - Создания резервных копий модов.

    Attributes:
        mod_list (ModListWidget): Виджет для отображения списка модов.
        source_mod_info (SourceModWidget): Виджет для отображения информации о выбранном моде.
        target_version_info (TargetVersionWidget): Виджет для отображения информации о найденной версии.
        folders_selector (FolderSelectorWidget): Виджет выбора папок.
        versions_combobox (QComboBox): Выбор версии Minecraft.
        loader_combobox (QComboBox): Выбор загрузчика (Forge/Fabric/Quilt/NeoForge).
    """
    def __init__(self):
        """Инициализирует главное окно приложения и настраивает макет пользовательского интерфейса.

        Создает и размещает все компоненты пользовательского интерфейса, включая список модов,
        панели информации, элементы управления фильтрами и выбора папок.
        Подключает сигналы и загружает начальные данные.
        """
        super().__init__()
        self.setWindowTitle("ModMatcher")
        self.setMinimumSize(1000, 700)

        icon_path = Path(__file__).resolve().parents[1] / "resources" / "icons" / "icon.png"
        self.setWindowIcon(QIcon(str(icon_path)))
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 5, 10, 10)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        self.mod_list = ModListWidget()
        splitter.addWidget(self.mod_list)
        
        right_panel = QWidget()
        right_panel_layout = QVBoxLayout(right_panel)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        
        top_section = QWidget()
        top_layout = QVBoxLayout(top_section)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        self.folders_selector = FolderSelectorWidget()
        top_layout.addWidget(self.folders_selector)

        filters_widget = QWidget()
        filters_layout = QHBoxLayout(filters_widget)
        filters_layout.setContentsMargins(20, 0, 20, 0)
        
        filters_layout.addWidget(QLabel("Версия:"))
        self.versions_combobox = QComboBox()
        filters_layout.addWidget(self.versions_combobox)
        filters_layout.addStretch(1)

        filters_layout.addWidget(QLabel("Загрузчик:"))
        self.loader_combobox = QComboBox()
        self.loader_combobox.addItems(["Forge", "Fabric", "Quilt", "NeoForge"])
        filters_layout.addWidget(self.loader_combobox)
        
        top_layout.addWidget(filters_widget)
        
        right_panel_layout.addWidget(top_section)
        
        # Информация о текущей версии мода
        self.source_mod_info = SourceModWidget()
        right_panel_layout.addWidget(self.source_mod_info)
        
        # Информация о найденной версии
        self.target_version_info = TargetVersionWidget()
        right_panel_layout.addWidget(self.target_version_info)

        splitter.addWidget(right_panel)

        splitter.setSizes([450, 550])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        self.minecraft_versions = MinecraftVersions()
        self.load_minecraft_versions()

        self.folders_selector.backup_requested.connect(self.on_backup_requested)
        self.folders_selector.source_folder_changed.connect(self.on_source_folder_changed)
        self.mod_list.mod_selected.connect(self.on_mod_selected)

    def load_minecraft_versions(self) -> None:
        """Загружает версии Minecraft в комбобокс выбора версий.

        Получает список версий Minecraft с использованием класса 
        MinecraftVersions и заполняет versions_combobox этими версиями.
        """
        self.versions_combobox.addItems(self.minecraft_versions.release_versions)

    def on_backup_requested(self, source_folder: str, dest_folder: str) -> None:
        """Обрабатывает запрос на резервное копирование от виджета выбора папок.

        Вызывает create_backup() для создания бэкапа модов
        из source_folder в dest_folder.

        Args:
            source_folder: Путь к исходной папке с модами для резервного копирования
            dest_folder: Путь к папке назначения для резервной копии
        """
        backup_path = backup.create_backup(source_folder, dest_folder)
    
        if backup_path:
            QMessageBox.information(self, "Успешно", f"Резервная копия создана:\n{backup_path}")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось создать резервную копию")

    def on_source_folder_changed(self, folder_path: str) -> None:
        """Обрабатывает изменение исходной папки с модами.

        Сканирует папку, парсит найденные файлы модов и обновляет виджет списка модов.
        """
        if not folder_path:
            self.mod_list.show_placeholder()
            self.source_mod_info.update_info(None)
            return
        
        mod_paths = file_scanner.get_mod_paths(folder_path)
        mods_info_list = []
        
        for file_path in mod_paths:
            try:
                info = mod_parser.parse_mod_file(str(file_path))
                mods_info_list.append(info)
            except mod_parser.ModParseError as e:
                print(f"Ошибка: {e}")
                mods_info_list.append(ModInfo(name=file_path.stem, source_path=file_path))

        self.mod_list.update_mod_list(mods_info_list)
        
        self.source_mod_info.update_info(None)

    def on_mod_selected(self, mod_info: ModInfo) -> None:
        """Обрабатывает выбор мода в списке.
        
        Достает информацию из словаря и передает в виджет информации.
        """
        self.source_mod_info.update_info(mod_info)
