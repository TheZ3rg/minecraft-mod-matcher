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


logger = logging.getLogger(__name__)


class ModScannerThread(QThread):
    """
    Фоновый поток для сканирования и парсинга папки с модами.
    """
    progress_updated = Signal(int, int)  # Передает: (текущий_файл, всего_файлов)
    scan_finished = Signal(list)         # Передает: готовый список [ModInfo, ModInfo, ...]
    scan_error = Signal(str)             # Передает: текст ошибки

    def __init__(self, folder_path: str):
        super().__init__()
        self.folder_path = folder_path

    def run(self):
        """Основная логика сканирования папки с модами."""
        logger.info(f"Начато сканирование папки: {self.folder_path}")
        
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
            logger.exception(f"Критическая ошибка в потоке сканирования: {e}")
            self.scan_error.emit(str(e))


class MinecraftVersionsLoaderThread(QThread):
    """
    Фоновый поток для загрузки списка версий Minecraft с API Mojang.
    """
    versions_loaded = Signal(list)
    error_occurred = Signal(str)

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
                self.error_occurred.emit("Не удалось получить данные от Mojang API.")
        except Exception as e:
            logger.exception("Ошибка в потоке загрузки версий")
            self.error_occurred.emit(str(e))
