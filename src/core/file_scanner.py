"""
Модуль для работы с файловой системой.
"""

import zipfile
import logging
from pathlib import Path
from typing import List, Union

logger = logging.getLogger(__name__)

def get_mod_paths(folder_path: Union[str, Path]) -> List[Path]:
    """
    Получает список путей к файлам модов (.jar и .zip) в указанной папке.

    Args:
        folder_path: Путь к директории (строка или объект Path).

    Returns:
        Отсортированный список объектов Path.
    """
    if folder_path is None:
        logger.error("Ошибка: Путь к директории не указан")
        return []
    
    folder_path = Path(folder_path)
    
    try:
        return sorted(
            file for file in folder_path.iterdir()
            if file.is_file() and zipfile.is_zipfile(file)
        )
    except (FileNotFoundError, NotADirectoryError):
        logger.error(f"Директория {folder_path} не найдена")
    except PermissionError:
        logger.error(f"Нет доступа к {folder_path}")
    except OSError as e:
        logger.error(f"Ошибка чтения: {e}")

    return []
