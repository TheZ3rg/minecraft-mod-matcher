"""
Модуль для хранения информации о модификациях.
"""

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import List, Optional

@dataclass
class ModInfo:
    """
    Описание метаданных модификации Minecraft.

    Attributes:
        mod_id: Внутренний идентификатор мода (id).
        name: Название модификации.
        authors: Список авторов модификации.
        version: Версия модификации.
        minecraft_version: Версия Minecraft, для которой предназначен мод.
        description: Описание модификации.
        icon_path: Путь к файлу иконки внутри архива.
        source_path: Полный путь к исходному файлу архива.
        metadata_file_name: Имя найденного файла метаданных в архиве.
        loader_type: Тип загрузчика (Fabric, Quilt, Forge, NeoForge, Legacy Forge).
        data_source: Источник данных ("API", "Local", "Unknown").
    """
    mod_id: Optional[str] = None
    name: Optional[str] = None
    authors: Optional[List[str]] = None
    version: Optional[str] = None
    minecraft_version: Optional[str] = None
    description: Optional[str] = None
    icon_path: Optional[PurePosixPath] = None
    source_path: Optional[Path] = None
    metadata_file_name: Optional[str] = None
    loader_type: Optional[str] = None
    data_source: str = "Unknown"
