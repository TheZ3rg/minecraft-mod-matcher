"""
Модуль, содержащий главное окно приложения ModMatcher.

MainWindow — основное окно приложения, которое управляет интерфейсом пользователя,
отображает список модов, информацию о них, а также предоставляет элементы управления
для фильтрации и резервного копирования.
"""
import logging
from pathlib import Path

from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                               QSplitter, QComboBox, QLabel, QPushButton)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap

from .worker_threads import (ModScannerThread, FiltersLoaderThread, 
                             CreatingBackupThread, CheckUpdatesThread, DownloadModsThread)
from .widgets.status_widget import StatusWidget
from .widgets.mod_list_widget import ModListWidget
from .widgets.source_mod_widget import SourceModWidget
from .widgets.target_version_widget import TargetVersionWidget
from .widgets.folders_selector_widget import FolderSelectorWidget

from core.mod_info import ModInfo


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

        # Секция с кнопками настроек и создания бэкапа
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)

        # Кнопка настроек
        self.settings_btn = QPushButton("⚙️ Настройки ")
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.setStyleSheet("QPushButton { padding: 6px; } QPushButton:hover { color: #a0a0a0; }")
        self.settings_btn.clicked.connect(self.open_settings)
        actions_layout.addWidget(self.settings_btn)

        actions_layout.addStretch()

        # Кнопка создания бэкапа
        self.backup_btn = QPushButton("💾 Создать бэкап модов")
        self.backup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.backup_btn.setEnabled(False) # Изначально выключена, пока директории не выбраны
        self.backup_btn.setStyleSheet("QPushButton { padding: 6px; } QPushButton:hover { color: #a0a0a0; }")
        self.backup_btn.clicked.connect(self.on_backup_btn_clicked)
        actions_layout.addWidget(self.backup_btn)

        top_layout.addWidget(actions_widget)

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
        self.versions_combobox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        
        filters_layout.addWidget(self.versions_combobox)
        
        filters_layout.addStretch()

        filters_layout.addWidget(QLabel("Загрузчик:"))
        self.loader_combobox = QComboBox()
        self.loader_combobox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        filters_layout.addWidget(self.loader_combobox)
        filters_layout.addStretch()
        
        right_panel_layout.addWidget(filters_widget)
        
        # Информация о найденной версии
        self.target_version_info = TargetVersionWidget()
        self.target_version_info.update_btn.clicked.connect(self.on_single_download_clicked)
        right_panel_layout.addWidget(self.target_version_info, 1)

        # Кнопка для запуска проверки наличия версий
        self.update_btn = QPushButton("Проверить наличие версий")
        self.update_btn.setMinimumHeight(30)
        font = self.update_btn.font()
        font.setPointSize(10)
        self.update_btn.setFont(font)
        self.update_btn.setEnabled(False)
        
        # Подключаем сигнал клика к обработчику, который будет запускать проверку наличия версий
        self.update_btn.clicked.connect(self.on_update_btn_clicked)

        right_panel_layout.addWidget(self.update_btn)

        splitter.addWidget(right_panel)

        splitter.setSizes([450, 550])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        self.start_filters_loading()

        # Запуск резервного копирования
        self.folders_selector.destination_folder_changed.connect(self.update_backup_button_state)
        # Запуск сканирования директории с модами
        self.folders_selector.source_folder_changed.connect(self.on_source_folder_changed)
        # Запуск обработки выбора мода в списке
        self.mod_list.mod_selected.connect(self.on_mod_selected)

    def open_settings(self):
        """Открывает диалоговое окно настроек."""
        logger.info("Открытие окна настроек")
        self.status_widget.show_info("Окно настроек скоро появится!")
    
    # --- Методы обработки резервного копирования ---
    def update_backup_button_state(self) -> None:
        """Проверяет, выбраны ли обе папки, и управляет доступностью кнопки бэкапа."""
        has_source = bool(self.folders_selector.source_path.text())
        has_dest = bool(self.folders_selector.dest_path.text())
        self.backup_btn.setEnabled(has_source and has_dest)

    def on_backup_btn_clicked(self) -> None:
        """Обработчик нажатия на кнопку бэкапа."""
        source = self.folders_selector.source_path.text()
        dest = self.folders_selector.dest_path.text()
        if source and dest:
            self.on_backup_requested(source, dest)

    def on_backup_requested(self, source_folder: str, dest_folder: str) -> None:
        """Обрабатывает запрос на резервное копирование от виджета выбора папок.

        Args:
            source_folder: Путь к исходной папке с модами для резервного копирования
            dest_folder: Путь к папке назначения для резервной копии
        """
        self.backup_thread = CreatingBackupThread(source_folder, dest_folder)

        self.backup_thread.start_progress.connect(self.status_widget.start_progress)
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

    # --- Методы обработки сканирования директории с модами ---
    def on_source_folder_changed(self, folder_path: str) -> None:
        """Обрабатывает выбор исходной папки, запуская сканирование директории в отдельном потоке."""
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

        self.update_backup_button_state()

    def _on_scan_finished(self, mods_info_list: list) -> None:
        """Вызывается автоматически, когда фоновый поток заканчивает работу."""
        self.mod_list.update_mod_list(mods_info_list)
        self.status_widget.show_success("Сканирование завершено")
        logger.info(f"Список модов обновлен. Найдено {len(mods_info_list)} модов.")

        if mods_info_list:
            self.update_btn.setEnabled(True)
            self.update_btn.setText("Проверить наличие версий")

    # --- Методы обработки загрузки фильтров (версий и загрузчиков) ---
    def start_filters_loading(self) -> None:
        """Инициализирует и запускает фоновый поток загрузки версий и загрузчиков."""
        self.filters_thread = FiltersLoaderThread()

        self.versions_combobox.addItem("Загрузка...")
        self.loader_combobox.addItem("Загрузка...")
        
        self.status_widget.start_indeterminate_progress("Загрузка фильтров из базы Modrinth...")

        self.filters_thread.filters_loaded.connect(self._on_filters_ready)
        self.filters_thread.error_occurred.connect(self._on_filters_error)
        
        self.filters_thread.start()

    def _on_filters_ready(self, versions: list, loaders: list) -> None:
        """Вызывается, когда списки успешно загружены."""
        self.versions_combobox.clear()
        self.versions_combobox.addItems(versions)
        
        self.loader_combobox.clear()
        
        for loader_data in loaders:
            name = loader_data["name"]
            svg_string = loader_data["icon"]
            
            # Цвета самых популярных загрузчиков для замены в SVG
            brand_colors = {
            "Fabric": "#DBB69B",
            "Forge": "#959EEF",
            "Neoforge": "#DF8F64",
            "Quilt": "#C796F9"
            }
            
            # Устанавливаем иконки
            if svg_string:
                # Ищем цвет в словаре. Если загрузчика там нет, используем стандартный белый
                icon_color = brand_colors.get(name, "#ffffff")
                svg_string = svg_string.replace('currentColor', icon_color)
                # Превращаем строку SVG в байты и загружаем прямо в память как картинку
                pixmap = QPixmap()
                pixmap.loadFromData(svg_string.encode('utf-8'))
                self.loader_combobox.addItem(QIcon(pixmap), name)
            else:
                # Если иконки нет, добавляем просто текст
                self.loader_combobox.addItem(name)
        
        self.status_widget.clear()
        logger.info(f"Загрузка фильтров завершена: {len(versions)} версий, {len(loaders)} загрузчиков.")

    def _on_filters_error(self, error_msg: str) -> None:
        """Обработка ошибки загрузки фильтров."""
        self.versions_combobox.clear()
        self.versions_combobox.addItem("Ошибка")
        
        self.loader_combobox.clear()
        self.loader_combobox.addItem("Ошибка")
        
        self.status_widget.show_error(error_msg)

    # --- Методы обработки проверки обновлений и загрузки модов --- 
    def on_update_btn_clicked(self):
        """Обрабатывает клик по кнопке обновления всех модов.
        
        Выполняет проверку наличия обновлений для всех или только для выделенных модов в отдельном потоке,
        а если обновления уже были найдены - запускает процесс загрузки.
        """
        current_text = self.update_btn.text()
        
        if current_text == "Проверить наличие версий":
            # Читаем фильтры
            game_version = self.versions_combobox.currentText()
            loader = self.loader_combobox.currentText()
            
            if not game_version or game_version == "Загрузка...":
                self.status_widget.show_error("Дождитесь загрузки списка версий Minecraft!")
                return
            elif game_version == "Ошибка":
                self.status_widget.show_error("Невозможно проверить версии без списка версий Minecraft!")
                return
            
            # Получаем моды для проверки
            mods_to_check = self.mod_list.get_selected_mods()
            if not mods_to_check:
                # Если не выбрано ни одного мода, берем все
                mods_to_check = self.mod_list.get_all_mods()
            
            # Обновляем UI
            self.status_widget.start_indeterminate_progress("Сверяем версии с базой Modrinth...")
            self.update_btn.setEnabled(False)
            self.mod_list.setEnabled(False) # Блокируем список, чтобы не кликали во время проверки
            
            # Запускаем проверку обновлений в отдельном потоке
            self.updates_thread = CheckUpdatesThread(mods_to_check, game_version, loader)
            self.updates_thread.updates_found.connect(self._on_updates_found)
            self.updates_thread.error_occurred.connect(self._on_updates_error)
            self.updates_thread.start()
            
        elif current_text.startswith("Загрузить"):
            dest_folder = self.folders_selector.dest_path.text()
            if not dest_folder:
                self.status_widget.show_error("Пожалуйста, выберите папку для сохранения модов вверху окна!")
                return
                
            # Берем выделенные моды. Если их нет - берем все.
            mods_to_download = self.mod_list.get_selected_mods()
            if not mods_to_download:
                mods_to_download = self.mod_list.get_all_mods()
                
            # Оставляем только те, для которых есть обновление
            mods_to_download = [m for m in mods_to_download if m.has_update]
            
            if not mods_to_download:
                self.status_widget.show_info("Нет модов, требующих обновления.")
                return
                
            self._start_download_process(mods_to_download, dest_folder)

    def _on_updates_found(self, updates_data: dict):
        """Обрабатывает результаты проверки обновлений."""
        self.mod_list.setEnabled(True)
        
        if not updates_data:
            self.status_widget.show_info("Обновлений для выбранных параметров не найдено.")
            self.update_btn.setEnabled(True)
            self.update_btn.setText("Проверить наличие версий")
            return
        
        all_mods = self.mod_list.get_all_mods()
        for mod in all_mods:
            if mod.file_hash and mod.file_hash in updates_data:
                new_version_info = updates_data[mod.file_hash]
                
                # Записываем версию и патчноут
                mod.update_version = new_version_info.get("version_number")
                mod.update_changelog = new_version_info.get("changelog")
                
                # API возвращает список файлов для этой версии. Ищем главный (.jar)
                files = new_version_info.get("files", [])
                if files:
                    # Пытаемся найти файл с пометкой primary, иначе берем первый попавшийся
                    primary_file = next((f for f in files if f.get("primary")), files[0])
                    mod.update_filename = primary_file.get("filename")
                    mod.update_download_url = primary_file.get("url")

        # Перерисовываем список модов, чтобы применились новые стили
        self.mod_list.update_mod_list(all_mods)

        self.status_widget.show_success(f"Найдено обновлений: {len(updates_data)}")

        # Обновляем кнопку
        self.update_btn.setEnabled(True)
        if len(self.mod_list.get_selected_mods()) > 0:
            self.update_btn.setText("Загрузить выбранные")
        else:
            self.update_btn.setText("Загрузить все")

    def _on_updates_error(self, error_msg: str):
        self.status_widget.show_error(error_msg)
        self.update_btn.setEnabled(True)
        self.mod_list.setEnabled(True)

    def on_single_download_clicked(self):
        """Обрабатывает клик по кнопке индивидуальной загрузки из нижней панели."""
        dest_folder = self.folders_selector.dest_path.text()
        if not dest_folder:
            self.status_widget.show_error("Пожалуйста, выберите папку для сохранения модов!")
            return
            
        # Берем только выделенные в списке моды
        selected_mods = self.mod_list.get_selected_mods()
        if not selected_mods or len(selected_mods) != 1:
            self.status_widget.show_error("Пожалуйста, выделите один мод для загрузки.")
            return
            
        mod = selected_mods[0]
        if not mod.has_update:
            return
            
        self._start_download_process([mod], dest_folder)

    def _start_download_process(self, mods: list, dest_folder: str):
        """Общий метод для запуска потока загрузки модов."""
        self.status_widget.start_progress("Подготовка к загрузке...")
        self.update_btn.setEnabled(False)
        self.mod_list.setEnabled(False)
        self.target_version_info.update_btn.setEnabled(False)
        
        self.download_thread = DownloadModsThread(mods, dest_folder)
        self.download_thread.progress_updated.connect(self.status_widget.update_progress)
        self.download_thread.status_text_updated.connect(self.status_widget.update_text)
        self.download_thread.download_finished.connect(self._on_download_finished)
        self.download_thread.download_error.connect(self._on_download_error)
        self.download_thread.start()

    def _on_download_finished(self, success_count: int):
        """Обработка успешного завершения загрузки модов."""
        self.mod_list.setEnabled(True)
        self.update_btn.setEnabled(True)
        self.status_widget.show_success(f"Загрузка завершена! Успешно скачано: {success_count}")

    def _on_download_error(self, error_msg: str):
        """Обработка ошибки при загрузке модов."""
        self.mod_list.setEnabled(True)
        self.update_btn.setEnabled(True)
        self.status_widget.show_error(error_msg)

    def on_mod_selected(self, mod_info: ModInfo) -> None:
        """Обрабатывает выбор мода в списке.
        
        Достает информацию из словаря и передает в виджеты информации.
        """
        self.source_mod_info.update_info(mod_info)
        self.target_version_info.update_info(mod_info)

    def closeEvent(self, event) -> None:
        """Событие, которое срабатывает при закрытии главного окна.

        Безопасно останавливает все запущенные фоновые потоки.
        """
        logger.debug("Закрытие приложения. Проверка активных потоков...")

        if hasattr(self, 'scanner_thread') and self.scanner_thread.isRunning():
            logger.debug("Остановка потока сканирования...")
            self.scanner_thread.terminate()
            self.scanner_thread.wait()

        if hasattr(self, 'filters_thread') and self.filters_thread.isRunning():
            logger.debug("Остановка потока загрузки фильтров...")
            self.filters_thread.terminate()
            self.filters_thread.wait()

        if hasattr(self, 'backup_thread') and self.backup_thread.isRunning():
            logger.debug("Остановка потока резервного копирования...")
            self.backup_thread.terminate()
            self.backup_thread.wait()

        event.accept()
