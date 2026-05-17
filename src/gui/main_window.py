"""
Модуль, содержащий главное окно приложения ModMatcher.

MainWindow — основное окно приложения, которое управляет интерфейсом пользователя,
отображает список модов, информацию о них, а также предоставляет элементы управления
для фильтрации и резервного копирования.
"""
import logging
from PySide6.QtWidgets import (QMainWindow, QMessageBox, QWidget, QHBoxLayout, 
                               QVBoxLayout, QSplitter, QComboBox, QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from pathlib import Path

from .worker_threads import (ModScannerThread, MinecraftVersionsLoaderThread, 
                             CreatingBackupThread)
from .widgets.status_widget import StatusWidget
from .widgets.mod_list_widget import ModListWidget
from .widgets.source_mod_widget import SourceModWidget
from .widgets.target_version_widget import TargetVersionWidget
from .widgets.folders_selector_widget import FolderSelectorWidget


from core.mod_info import ModInfo

from api.minecraft_versions import MinecraftVersions


logger = logging.getLogger(__name__)


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
        self.mod_list.setMinimumWidth(400)
        splitter.addWidget(self.mod_list)
        
        right_panel = QWidget()
        right_panel_layout = QVBoxLayout(right_panel)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        
        # Секция выбора папок и отображения полезной информации
        top_section = QWidget()
        top_layout = QVBoxLayout(top_section)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        self.folders_selector = FolderSelectorWidget()
        top_layout.addWidget(self.folders_selector)

        # Виджет для отображения сообщений состояния и прогресса выполнения задач
        self.status_widget = StatusWidget()
        top_layout.addWidget(self.status_widget)

        right_panel_layout.addWidget(top_section)

        # Информация о текущей версии мода
        self.source_mod_info = SourceModWidget()
        right_panel_layout.addWidget(self.source_mod_info, 1)

        # Комбинированные списки для выбора версии Minecraft и загрузчика
        filters_widget = QWidget()
        filters_layout = QHBoxLayout(filters_widget)
        
        filters_layout.addStretch()
        filters_layout.addWidget(QLabel("Версия:"))
        self.versions_combobox = QComboBox()
        filters_layout.addWidget(self.versions_combobox)
        
        filters_layout.addStretch()

        filters_layout.addWidget(QLabel("Загрузчик:"))
        self.loader_combobox = QComboBox()
        self.loader_combobox.addItems(["Forge", "Fabric", "Quilt", "NeoForge"])
        filters_layout.addWidget(self.loader_combobox)
        filters_layout.addStretch()
        
        right_panel_layout.addWidget(filters_widget)
        
        # Информация о найденной версии
        self.target_version_info = TargetVersionWidget()
        right_panel_layout.addWidget(self.target_version_info, 1)

        splitter.addWidget(right_panel)

        splitter.setSizes([450, 550])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        self.minecraft_versions = MinecraftVersions()
        self.versions_combobox.addItem("Загрузка...") 
        self.start_versions_loading()

        self.folders_selector.backup_requested.connect(self.on_backup_requested)
        self.folders_selector.source_folder_changed.connect(self.on_source_folder_changed)
        self.mod_list.mod_selected.connect(self.on_mod_selected)

    def on_backup_requested(self, source_folder: str, dest_folder: str) -> None:
        """Обрабатывает запрос на резервное копирование от виджета выбора папок.

        Args:
            source_folder: Путь к исходной папке с модами для резервного копирования
            dest_folder: Путь к папке назначения для резервной копии
        """
        self.backup_thread = CreatingBackupThread(source_folder, dest_folder)

        self.backup_thread.progress_updated.connect(self.status_widget.update_progress)
        self.backup_thread.backup_finished.connect(self._on_backup_finished)
        self.backup_thread.backup_error.connect(self._on_backup_error)
        
        self.backup_thread.start()

    def _on_backup_finished(self, backup_path: str) -> None:
        """Вызывается, когда резервная копия успешно создана."""
        self.status_widget.show_success(f"Резервная копия создана:\n{backup_path}")

    def _on_backup_error(self, error_message: str) -> None:
        """Вызывается, когда при создании резервной копии произошла ошибка."""
        self.status_widget.show_error(f"Ошибка создания резервной копии.\n{error_message}")

    def on_source_folder_changed(self, folder_path: str) -> None:
        """Обрабатывает выбор исходной папки, запуская фоновое сканирование директории."""
        if not folder_path:
            self.mod_list.show_placeholder()
            self.source_mod_info.update_info(None)
            return
        
        # Если уже запущен поток сканирования, останавливаем его перед запуском нового
        # Это гарантирует, что не будет конфликтов при быстром выборе директорий
        if hasattr(self, 'scanner_thread') and self.scanner_thread.isRunning():
            self.scanner_thread.terminate()
            self.scanner_thread.wait()
        
        self.mod_list.mod_list.clear()
        self.mod_list.mod_list.addItem("🔍 Сканирование архивов, подождите...")
        self.source_mod_info.update_info(None)

        self.scanner_thread = ModScannerThread(folder_path)

        self.status_widget.start_progress("Сканирование папки с модами...")

        self.scanner_thread.progress_updated.connect(self.status_widget.update_progress)
        self.scanner_thread.status_text_updated.connect(self.status_widget.update_text)
        self.scanner_thread.indeterminate_progress.connect(self.status_widget.start_indeterminate_progress)   
        self.scanner_thread.scan_finished.connect(self._on_scan_finished)
        
        self.scanner_thread.start()

    def _on_scan_finished(self, mods_info_list: list) -> None:
        """Вызывается автоматически, когда фоновый поток заканчивает работу."""
        self.mod_list.update_mod_list(mods_info_list)
        self.status_widget.show_success("Сканирование завершено")
        logger.info(f"Список модов обновлен. Найдено {len(mods_info_list)} модов.")

    def start_versions_loading(self) -> None:
        """Инициализирует и запускает фоновый поток загрузки версий."""
        self.version_thread = MinecraftVersionsLoaderThread(self.minecraft_versions)
        
        self.status_widget.start_indeterminate_progress("Получение списка версий Minecraft...")

        self.version_thread.versions_loaded.connect(self._on_versions_ready)
        self.version_thread.error_occurred.connect(self._on_versions_error)
        
        self.version_thread.start()

    def _on_versions_ready(self, versions: list) -> None:
        """Вызывается, когда список версий успешно загружен."""
        self.versions_combobox.clear()
        self.versions_combobox.addItems(versions)
        self.status_widget.clear()
        logger.info(f"Список версий Minecraft успешно обновлен: {len(versions)} элементов.")

    def _on_versions_error(self, error_msg: str) -> None:
        """Обработка ошибки загрузки версий."""
        self.versions_combobox.clear()
        self.versions_combobox.addItem("Ошибка")
        self.status_widget.show_error(error_msg)

    def on_mod_selected(self, mod_info: ModInfo) -> None:
        """Обрабатывает выбор мода в списке.
        
        Достает информацию из словаря и передает в виджет информации.
        """
        self.source_mod_info.update_info(mod_info)

    def closeEvent(self, event) -> None:
        """Событие, которое срабатывает при закрытии главного окна.

        Безопасно останавливает все запущенные фоновые потоки.
        """
        logger.debug("Закрытие приложения. Проверка активных потоков...")

        if hasattr(self, 'scanner_thread') and self.scanner_thread.isRunning():
            logger.debug("Остановка потока сканирования...")
            self.scanner_thread.terminate()
            self.scanner_thread.wait()

        if hasattr(self, 'version_thread') and self.version_thread.isRunning():
            logger.debug("Остановка потока загрузки версий...")
            self.version_thread.terminate()
            self.version_thread.wait()

        if hasattr(self, 'backup_thread') and self.backup_thread.isRunning():
            logger.debug("Остановка потока резервного копирования...")
            self.backup_thread.terminate()
            self.backup_thread.wait()

        event.accept()
