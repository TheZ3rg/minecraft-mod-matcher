"""
Модуль для фоновых задач (QThread).

Здесь хранятся классы, которые выполняют тяжелые вычисления (парсинг, хэширование, api-запросы)
в отдельных потоках, чтобы не блокировать графический интерфейс приложения.
"""

import logging
import requests
import concurrent.futures
from typing import List
from pathlib import Path
from PySide6.QtCore import QThread, Signal

import core.file_scanner as file_scanner
import core.api_parser as api_parser
import core.mod_parser as mod_parser
import core.backup as backup
import core.hasher as hasher
from core.mod_info import ModInfo

from api.modrinth_client import ModrinthClient


logger = logging.getLogger(__name__)


class ModScannerThread(QThread):
    """Фоновый поток для получения информации о модах.
    
    Сканирует папку с модами, получает данные через API Modrinth
    и в случае отсутствия информации в API парсит метаданные мода из архива.
    """
    indeterminate_progress = Signal(str)
    progress_updated = Signal(int, int)
    status_text_updated = Signal(str)
    scan_finished = Signal(list)
    scan_error = Signal(str)

    def __init__(self, folder_path: str):
        super().__init__()
        self.folder_path = folder_path

    def run(self):
        logger.info(f"Начато сканирование директории: {self.folder_path}")
        
        try:
            mod_paths = file_scanner.get_mod_paths(self.folder_path)
            total_mods = len(mod_paths)
            if total_mods == 0:
                self.scan_finished.emit([])
                return

            modrinth_client = ModrinthClient()
            mods_info_list: List[ModInfo] = []

            # 1. Хэширование файлов
            self.status_text_updated.emit("Вычисление хэшей файлов...")
            file_hashes = {}  # {путь_к_файлу: хэш}
            
            for index, mod_path in enumerate(mod_paths):
                file_hashes[mod_path] = hasher.get_file_hash(mod_path)
                self.progress_updated.emit(index + 1, total_mods)

            # 2. Сетевые запросы к API Modrinth
            self.indeterminate_progress.emit("Запрос данных с серверов Modrinth...")
            
            # Собираем список непустых хэшей
            valid_hashes = [h for h in file_hashes.values() if h]
            
            # Получаем все версии разом по хэшам.
            # API Modrinth позволяет запрашивать сразу несколько хэшей.
            versions_data = {}
            if valid_hashes:
                api_versions = modrinth_client.get_versions_by_hashes(valid_hashes)
                if api_versions:
                    versions_data = api_versions
            
            # Извлекаем все уникальные project_id из полученных версий
            project_ids = list({v.get("project_id") for v in versions_data.values() if v.get("project_id")})
            
            # Получаем все проекты разом
            projects_list = []
            if project_ids:
                api_projects = modrinth_client.get_projects_by_ids(project_ids)
                if api_projects:
                    projects_list = api_projects
                    
            projects_data = {p.get("id"): p for p in projects_list}

            # 3. Многопоточная загрузка иконок
            self.status_text_updated.emit("Загрузка иконок...")
            
            # Собираем все уникальные ссылки на иконки, чтобы не качать одно и то же дважды
            icon_urls = {str(p.get("icon_url")) for p in projects_data.values() if p.get("icon_url")}
            urls_count = len(icon_urls)
            icon_cache = {} # {url: байты_картинки}
            
            # Запускаем несколько рабочих потоков для одновременного скачивания
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:

                future_to_url = {executor.submit(modrinth_client.download_icon, url): url for url in icon_urls}
                
                # По мере того, как картинки скачиваются, складываем их в кэш
                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        data = future.result()
                        if data:
                            icon_cache[url] = data
                    except Exception as exc:
                        logger.warning(f"Ошибка параллельной загрузки иконки {url}: {exc}")
                    
                    self.progress_updated.emit(len(icon_cache), urls_count)

            # 4. Сборка данных в объекты ModInfo
            self.status_text_updated.emit("Сборка данных...")
            
            for index, mod_path in enumerate(mod_paths):
                mod_info = None
                mod_hash = file_hashes.get(mod_path)
                
                if mod_hash and mod_hash in versions_data:
                    v_data = versions_data[mod_hash]
                    p_data = projects_data.get(v_data.get("project_id"))
                    
                    if p_data:
                        # Достаем готовую картинку из кэша
                        icon_url = p_data.get("icon_url")
                        icon_data = icon_cache.get(icon_url)
                        
                        # Собираем объект ModInfo из данных API
                        mod_info = api_parser.parse_mod_from_batch(v_data,
                                                                   p_data,
                                                                   mod_path,
                                                                   icon_data,
                                                                   mod_hash)

                # Локальный парсинг
                # На случай, если мод не найден в API.
                # Покрывает только самые популярные форматы загрузчиков (Fabric, Forge, Quilt)
                # и может не сработать для редких/старых модов или модов с нестандартной структурой.
                if not mod_info:
                    logger.debug(f"Файл {mod_path.name} не найден в API. Пробуем распарсить локально.")
                    try:
                        mod_info = mod_parser.parse_mod_file(str(mod_path))
                    except mod_parser.ModParseError as e:
                        logger.warning(f"Не удалось распарсить {mod_path.name}: {e}")
                        mod_info = ModInfo(name=mod_path.stem, source_path=mod_path, data_source="Unknown")

                mods_info_list.append(mod_info)
                self.progress_updated.emit(index + 1, total_mods)

            logger.info("Сканирование успешно завершено.")
            self.scan_finished.emit(mods_info_list)

        except Exception as e:
            logger.exception(f"Ошибка в потоке сканирования директории: {e}")
            self.scan_error.emit(str(e))


class FiltersLoaderThread(QThread):
    """Фоновый поток для загрузки списка версий Minecraft и загрузчиков с API Modrinth."""
    filters_loaded = Signal(list, list) # (список_версий, список_загрузчиков)
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        logger.info("Запуск загрузки фильтров с Modrinth...")
        try:
            client = ModrinthClient()
            
            versions = client.get_game_versions()
            loaders = client.get_loaders()
            
            if versions:
                if loaders:
                    self.filters_loaded.emit(versions, loaders)
                else:
                    logger.warning("Не удалось загрузить список загрузчиков от Modrinth.")
                    self.error_occurred.emit("Не удалось загрузить список загрузчиков от Modrinth.")
            else:
                logger.warning("Не удалось загрузить список версий от Modrinth.")
                self.error_occurred.emit("Не удалось загрузить список версий от Modrinth.")
                
        except Exception as e:
            logger.exception(f"Ошибка в потоке загрузки фильтров: {e}")
            self.error_occurred.emit(str(e))


class CreatingBackupThread(QThread):
    """Фоновый поток для создания резервной копии папки с модами."""
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


class CheckUpdatesThread(QThread):
    """Фоновый поток для проверки обновлений.

    Отправляет хэши модов, версию игры и загрузчик на Modrinth,
    и получает информацию о доступных обновлениях.
    """
    updates_found = Signal(dict) # {старый_хэш: словарь_с_новой_версией}
    error_occurred = Signal(str)

    def __init__(self, mods_to_check: List[ModInfo], game_version: str, loader: str):
        super().__init__()
        self.mods = mods_to_check
        self.game_version = game_version
        self.loader = loader

    def run(self):
        logger.info(f"Запуск проверки обновлений для {self.game_version} [{self.loader}]...")
        try:
            # Собираем только непустые хэши
            hashes = [mod.file_hash for mod in self.mods if mod.file_hash]
            
            if not hashes:
                self.updates_found.emit({})
                return
            
            client = ModrinthClient()
            # Запрашиваем обновления у API
            updates_data = client.check_updates(hashes, self.loader, self.game_version)
            
            if updates_data is None:
                logger.warning("Не удалось получить ответ от серверов Modrinth при проверке обновлений.")
                self.error_occurred.emit("Не удалось получить ответ от серверов Modrinth при проверке обновлений.")
            else:
                logger.info(f"Проверка обновлений завершена. Найдено обновлений: {len(updates_data)}")
                self.updates_found.emit(updates_data)
                
        except Exception as e:
            logger.exception(f"Ошибка в потоке проверки обновлений: {e}")
            self.error_occurred.emit(str(e))


class DownloadModsThread(QThread):
    """Фоновый поток для многопоточного скачивания новых версий модов."""
    progress_updated = Signal(int, int)
    status_text_updated = Signal(str)
    download_finished = Signal(int)
    download_error = Signal(str)

    def __init__(self, mods_to_download: List[ModInfo], dest_folder: str):
        super().__init__()
        self.mods = mods_to_download
        self.dest_folder = Path(dest_folder)

    def _download_single_mod(self, mod: ModInfo) -> bool:
        """Вспомогательный метод для скачивания одного мода.

        Args:
            mod: Объект ModInfo, содержащий информацию о моде и ссылку на скачивание.
        Returns:
            Возвращает True в случае успеха, False при ошибке.
        """
        if not mod.update_download_url or not mod.update_filename:
            return False
            
        try:
            response = requests.get(mod.update_download_url, stream=True, timeout=20)
            response.raise_for_status()

            file_path = self.dest_folder / mod.update_filename
            
            # Записываем файл порциями, чтобы не загружать весь файл в память целиком
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=2 * 1024 * 1024 * 8):
                    f.write(chunk)
            logger.info(f"Скачивание завершено. Установлено: {mod.update_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке {mod.update_filename}: {e}")
            return False

    def run(self):
        logger.info(f"Начало многопоточной загрузки {len(self.mods)} модов в {self.dest_folder}")
        try:
            self.dest_folder.mkdir(parents=True, exist_ok=True)

            success_count = 0
            completed_tasks = 0
            total_mods = len(self.mods)

            # Запускаем несколько рабочих потоков для одновременного скачивания
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_mod = {
                    executor.submit(self._download_single_mod, mod): mod 
                    for mod in self.mods
                }
                
                for future in concurrent.futures.as_completed(future_to_mod):
                    mod = future_to_mod[future]
                    try:
                        is_success = future.result()
                        if is_success:
                            success_count += 1
                        self.status_text_updated.emit(f"Загружено: {success_count}/{total_mods} - {mod.name}")
                    except Exception as exc:
                        logger.warning(f"Сбой загрузки {mod.name}: {exc}")
                        
                    # Двигаем прогресс-бар после скачивания каждого мода
                    completed_tasks += 1
                    self.progress_updated.emit(completed_tasks, total_mods)

            logger.info(f"Загрузка завершена. Успешно скачано: {success_count}/{total_mods}")
            self.download_finished.emit(success_count)

        except Exception as e:
            logger.exception(f"Критическая ошибка в пуле скачивания: {e}")
            self.download_error.emit(str(e))
