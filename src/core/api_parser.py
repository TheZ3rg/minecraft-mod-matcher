"""
Модуль для формирования информации о моде через API.

Этот модуль берет сырые словари, которые возвращает ModrinthClient,
и превращает их в удобный объект ModInfo.
"""

import logging
from pathlib import Path
from typing import Optional

from core.mod_info import ModInfo
from api.modrinth_client import ModrinthClient

logger = logging.getLogger(__name__)

def parse_mod_via_api(mod_hash: str, mod_path: Path, client: ModrinthClient) -> Optional[ModInfo]:
    """
    Запрашивает данные о моде через API по хэшу и собирает объект ModInfo.

    Args:
        mod_hash: SHA-1 хэш файла мода.
        mod_path: Путь к локальному файлу мода (нужен для сохранения в ModInfo).
        client: Экземпляр клиента ModrinthClient для выполнения запросов.

    Returns:
        Сформированный объект ModInfo или None, если мод не найден в API или произошла ошибка.
    """
    version_info = client.get_version_by_hash(mod_hash)
    
    if not version_info:
        return None
        
    project_id = version_info.get("project_id")
    if not project_id:
        return None
        
    project_info = client.get_project_by_id(project_id)
    if not project_info:
        return None

    # Версий игры может быть несколько, берем диапазон от самой старой до самой новой
    # Если версия одна, берем только её.
    mc_versions = version_info.get("game_versions", [])
    if mc_versions:
        if len(mc_versions) > 1:
            mc_version_str = f"{mc_versions[0]} - {mc_versions[-1]}"
        else:
            mc_version_str = str(mc_versions[0])
    else:
        mc_version_str = None
    
    # Загрузчиков может быть несколько, объединяем их в строку через "/"
    loaders = version_info.get("loaders", [])
    if loaders:
        loader_str = "/".join(str(l).capitalize() for l in loaders)
    else:
        loader_str = None
    
    # Берем url иконки из проекта и получаем данные иконки, если она есть
    icon_url = project_info.get("icon_url")
    if icon_url:
        icon_data = client.download_icon(icon_url)
    else:
        icon_data = None

    return ModInfo(
        data_source="API",
        source_path=mod_path,
        api_project_id=project_id,
        api_version_id=version_info.get("id"),
        name=project_info.get("title"),
        description=project_info.get("description"),
        version=version_info.get("version_number"),
        minecraft_version=mc_version_str,
        loader_type=loader_str,
        api_icon_url=icon_url,
        api_icon_data=icon_data
    )