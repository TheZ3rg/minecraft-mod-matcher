"""
Модуль для создания резервных копий модов.

Этот модуль предоставляет метод для создания резервных копий модов в формате ZIP архива.
"""

import zipfile
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable

import core.file_scanner as file_scanner


logger = logging.getLogger(__name__)


class BackupError(Exception):
    """Исключение для ошибок при создании резервной копии."""
    pass


def create_backup(source_folder: str,
                  dest_folder: str,
                  progress_callback: Optional[Callable[[int, int], None]] = None) -> Path:
    """Создаёт ZIP-архив с модами (.jar и .zip) из source_folder в dest_folder.

    Args:
        source_folder: Путь к папке с модами
        dest_folder: Путь к папке для сохранения бэкапа
        progress_callback: Необязательная функция для обновления прогресса (текущий, всего)
            
    Returns:
        Путь к созданному архиву или None, если произошла ошибка

    Raises:
        BackupError: Если папка не найдена, модов нет или произошла ошибка записи.
    """

    src = Path(source_folder)
    dst = Path(dest_folder)

    if not src.is_dir():
        logger.error(f"Ошибка: исходная папка не найдена: {src}")
        raise BackupError(f"Исходная папка с модами не найдена по пути:\n{src}")
        
    if not dst.is_dir():
        dst.mkdir(parents=True, exist_ok=True) # Создаёт папку назначения, если её нет
        
    mod_paths = file_scanner.get_mod_paths(source_folder)
        
    if not mod_paths:
        logger.warning(f"В директории {src} нет модов для резервного копирования")
        raise BackupError("В выбранной папке не найдено файлов модов (.jar/.zip) для бэкапа.")
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = dst / f"mods_backup_{timestamp}.zip"

    total_files = len(mod_paths)
        
    try:
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for index, file in enumerate(mod_paths):
                zipf.write(file, file.name)

                if progress_callback:
                    progress_callback(index + 1, total_files)
            
        logger.info(f"Резервная копия успешно создана: {backup_path}")
        return backup_path
            
    except Exception as e:
        logger.exception(f"Ошибка записи ZIP-архива бэкапа: {e}")
        raise BackupError(f"Не удалось записать архив на диск: {e}")
