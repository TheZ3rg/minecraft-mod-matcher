"""
Модуль для хранения информации о модификациях.
"""

from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import List, Optional, Dict, Any

@dataclass
class ModInfo:
    """
    Описание метаданных модификации Minecraft.

    Attributes:
        data_source: Источник данных ("API", "Local", "Unknown").
        source_path: Полный путь к исходному файлу архива.
        file_hash: Хэш файла для идентификации.
        name: Название модификации.
        description: Описание модификации.
        loader_type: Тип загрузчика (Fabric, Quilt, Forge, NeoForge, Legacy Forge и т.д.).
        version: Версия модификации.
        minecraft_version: Версия Minecraft, для которой предназначен мод.

        mod_id: Внутренний идентификатор мода (id).
        authors: Список авторов модификации.
        icon_path: Путь к файлу иконки внутри архива.
        metadata_file_name: Имя найденного файла метаданных в архиве.

        api_project_id: Уникальный ID проекта на Modrinth (например, 'P7dR8mSH').
        api_version_id: Уникальный ID конкретной версии файла на Modrinth.
        api_icon_url: URL иконки, полученной из API.
        api_icon_data: байты иконки из API.

        update_filename: Имя файла для сохранения новой версии на диск.
        update_version: Номер новой версии (например, '1.2.4').
        update_changelog: Описание изменений (патчноут).
        update_download_url: Прямая ссылка на скачивание .jar файла новой версии.
        update_dependencies: Список зависимостей новой версии (зависимость {project_id: str, type: str}).
    """
    # --- Общие данные ---
    data_source: str = "Unknown"
    source_path: Optional[Path] = None
    file_hash: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    loader_type: Optional[str] = None
    version: Optional[str] = None
    minecraft_version: Optional[str] = None

    # --- Локальные данные (Парсинг архива) ---
    mod_id: Optional[str] = None
    authors: Optional[List[str]] = None
    icon_path: Optional[PurePosixPath] = None
    metadata_file_name: Optional[str] = None
    
    # --- Данные от API (Состояние текущего файла) ---
    api_project_id: Optional[str] = None
    api_version_id: Optional[str] = None
    api_icon_url: Optional[str] = None
    api_icon_data: Optional[bytes] = None
    
    # --- Данные от API об обновлении (Целевая версия для скачивания) ---
    update_checked: bool = False
    update_filename: Optional[str] = None
    update_version: Optional[str] = None
    update_changelog: Optional[str] = None
    update_download_url: Optional[str] = None
    # Зависимости мода (список словарей с project_id и типом зависимости)
    update_dependencies: List[Dict[str, Any]] = field(default_factory=list) 

    @property
    def has_update(self) -> bool:
        """Вспомогательное свойство. Возвращает True, если найдено обновление."""
        return bool(self.update_download_url)
