"""
Модуль для фоновых задач (QThread).

Здесь хранятся классы, которые выполняют тяжелые вычисления (парсинг, хэширование, api-запросы)
в отдельных потоках, чтобы не блокировать графический интерфейс приложения.
"""

import logging
from PySide6.QtCore import QThread, Signal
from typing import List

import core.file_scanner as file_scanner
import core.mod_parser as mod_parser
from core.mod_info import ModInfo
import core.backup as backup


logger = logging.getLogger(__name__)


class ModScannerThread(QThread):
    """
    Фоновый поток для сканирования и парсинга папки с модами.
    """
    progress_updated = Signal(int, int)  # Передает: (текущий_файл, всего_файлов)
    scan_finished = Signal(list)         # Передает: готовый список из объектов ModInfo
    scan_error = Signal(str)             # Передает: текст ошибки

    def __init__(self, folder_path: str):
        super().__init__()
        self.folder_path = folder_path

    def run(self):
        """Основная логика сканирования папки с модами."""
        logger.info(f"Начато сканирование директории: {self.folder_path}")
        
        try:
            mod_paths = file_scanner.get_mod_paths(self.folder_path)
            total_mods = len(mod_paths)
            mods_info_list: List[ModInfo] = []

            for index, file_path in enumerate(mod_paths):
                try:
                    info = mod_parser.parse_mod_file(str(file_path))
                    mods_info_list.append(info)
                except mod_parser.ModParseError as e:
                    logger.warning(f"Не удалось распарсить {file_path.name}: {e}")
                    mods_info_list.append(ModInfo(name=file_path.stem, source_path=file_path))
                
                self.progress_updated.emit(index + 1, total_mods)

            logger.info("Сканирование успешно завершено.")
            self.scan_finished.emit(mods_info_list)

        except Exception as e:
            logger.exception(f"Ошибка в потоке сканирования директории: {e}")
            self.scan_error.emit(str(e))


class MinecraftVersionsLoaderThread(QThread):
    """
    Фоновый поток для загрузки списка версий Minecraft с API Mojang.
    """
    versions_loaded = Signal(list) # Передает: список версий Minecraft
    error_occurred = Signal(str)  # Передает: текст ошибки

    def __init__(self, api_instance):
        super().__init__()
        self.api = api_instance

    def run(self):
        """Запускает сетевой запрос в отдельном потоке."""
        logger.info("Запуск фоновой загрузки версий Minecraft...")
        try:
            if self.api.load_versions():
                self.versions_loaded.emit(self.api.release_versions)
            else:
                self.error_occurred.emit("Не удалось загрузить версии Minecraft.")
        except Exception as e:
            logger.exception(f"Ошибка в потоке загрузки версий: {e}")
            self.error_occurred.emit(str(e))


class CreatingBackupThread(QThread):
    """
    Фоновый поток для создания резервной копии папки с модами.
    """
    progress_updated = Signal(int, int)  # Передает: (текущий_файл, всего_файлов)
    backup_finished = Signal(str)        # Передает: путь к созданной резервной копии
    backup_error = Signal(str)           # Передает: текст ошибки

    def __init__(self, source_folder: str, backup_folder: str):
        super().__init__()
        self.source_folder = source_folder
        self.backup_folder = backup_folder

    def run(self):
        """Создает резервную копию папки с модами."""
        logger.info(f"Начало создания резервной копии из {self.source_folder} в {self.backup_folder}")
        try:
            backup_path = backup.create_backup(
                self.source_folder,
                self.backup_folder,
                progress_callback=self.progress_updated.emit
            )
            self.backup_finished.emit(str(backup_path))
        except backup.BackupError as e:
            logger.warning(f"Не удалось создать бэкап: {e}")
            self.backup_error.emit(str(e))
        except Exception as e:
            logger.exception(f"Критическая ошибка при создании резервной копии: {e}")
            self.backup_error.emit(str(e))
