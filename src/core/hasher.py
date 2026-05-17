"""
Модуль для криптографического хэширования файлов.
Используется для уникальной идентификации модов.
"""

import hashlib
import logging
from pathlib import Path
from typing import Union, Optional

logger = logging.getLogger(__name__)

def get_file_hash(file_path: Union[str, Path], algorithm: str = 'sha1') -> Optional[str]:
    """
    Вычисляет хэш файла по заданному алгоритму.

    Args:
        file_path: Путь к файлу.
        algorithm: Алгоритм хэширования ('sha1' или 'sha512').

    Returns:
        Строка с хэшем в 16-ричном формате или None в случае ошибки.
    """
    path = Path(file_path)
    
    if not path.is_file():
        logger.error(f"Невозможно вычислить хэш: файл не найден {path}")
        return None

    try:
        # Выбираем нужный алгоритм из библиотеки hashlib
        hasher = hashlib.new(algorithm)
        
        # Читаем файл чанками, чтобы уменьшить использование памяти,
        # если пользователь попытается прохэшировать огромный файл
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)

        return hasher.hexdigest()
        
    except ValueError:
        logger.error(f"Неподдерживаемый алгоритм хэширования: {algorithm}")
        return None
    except Exception as e:
        logger.exception(f"Ошибка при вычислении хэша файла {path.name}: {e}")
        return None
