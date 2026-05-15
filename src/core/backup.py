"""
Модуль для создания резервных копий модов.

Этот модуль предоставляет метод для создания резервных копий модов в формате ZIP архива.
"""

import zipfile
from pathlib import Path
from datetime import datetime
from typing import Optional

import core.file_scanner as file_scanner


def create_backup(source_folder: str, dest_folder: str) -> Optional[Path]:
    """Создаёт ZIP-архив с модами (.jar и .zip) из source_folder в dest_folder.

    Args:
        source_folder: Путь к папке с модами
            dest_folder: Путь к папке для сохранения бэкапа
            
        Returns:
            Путь к созданному архиву или None, если произошла ошибка
        """

    src = Path(source_folder)
    dst = Path(dest_folder)

    if not src.is_dir():
        print(f"Ошибка: исходная папка не найдена: {src}")
        return None
        
    if not dst.is_dir():
        dst.mkdir(parents=True, exist_ok=True) # Создаёт папку назначения, если её нет
        
    mod_paths = file_scanner.get_mod_paths(source_folder)
        
    if not mod_paths:
        print("Нет модов для резервного копирования")
        return None
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = dst / f"mods_backup_{timestamp}.zip"
        
    try:
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in mod_paths:
                zipf.write(file, file.name)
            
        print(f"Резервная копия создана: {backup_path}")
        return backup_path
            
    except Exception as e:
        print(f"Ошибка при создании резервной копии: {e}")
        return None
