"""
Модуль для формирования информации о моде через API.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from core.mod_info import ModInfo

logger = logging.getLogger(__name__)

def parse_mod_from_batch(version_info: Dict[str, Any], 
                         project_info: Dict[str, Any], 
                         mod_path: Path, 
                         icon_data: Optional[bytes]) -> ModInfo:
    """Собирает объект ModInfo из уже полученных словарей API.

    Args:
        version_info: Словарь с данными о версии мода из API.
        project_info: Словарь с данными о проекте из API.
        mod_path: Путь к файлу мода на диске.
        icon_data: Байты иконки мода, если она была загружена.

    Returns:
        ModInfo: Объект с полной информацией о моде.
    """
    mc_versions = version_info.get("game_versions", [])
    if mc_versions:
        if len(mc_versions) > 1:
            mc_version_str = f"{mc_versions[0]} - {mc_versions[-1]}"
        else:
            mc_version_str = str(mc_versions[0])
    else:
        mc_version_str = None
    
    loaders = version_info.get("loaders", [])
    loader_str = "/".join(str(l).capitalize() for l in loaders) if loaders else None

    icon_url = project_info.get("icon_url")

    return ModInfo(
        data_source="API",
        source_path=mod_path,
        api_project_id=project_info.get("id"),
        api_version_id=version_info.get("id"),
        name=project_info.get("title"),
        description=project_info.get("description"),
        version=version_info.get("version_number"),
        minecraft_version=mc_version_str,
        loader_type=loader_str,
        api_icon_url=icon_url,
        api_icon_data=icon_data
    )
