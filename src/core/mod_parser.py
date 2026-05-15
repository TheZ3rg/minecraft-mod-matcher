"""
Модуль для парсинга метаданных модификаций.

Предоставляет функции для чтения и извлечения стандартизированной информации
о модификациях Minecraft (название, версия, авторы и т.д.) из архивов 
(.jar, .zip). Поддерживает официальные спецификации загрузчиков Fabric, Quilt, 
Forge, NeoForge и Legacy Forge.
"""

import json
import zipfile
import tomllib
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional, Union

from .mod_info import ModInfo


METADATA_FILES_PRIORITY = [
    "quilt.mod.json",                # Quilt
    "fabric.mod.json",               # Fabric
    "meta-inf/neoforge.mods.toml",   # NeoForge (форк Forge для 1.20+)
    "meta-inf/mods.toml",            # Forge (1.13+)
    "mcmod.info",                    # Старый формат Forge (1.12.2-)
]


class ModParseError(Exception):
    """Ошибка при разборе метаданных модификации."""


def parse_mod_file(file_path: Union[str, Path]) -> ModInfo:
    """
    Основная функция для парсинга мода.
    
    Открывает архив, определяет файл метаданных согласно приоритету загрузчиков 
    и возвращает объект ModInfo с извлеченными данными.

    Args:
        file_path: Путь к файлу мода (строка или объект Path).

    Returns:
        Объект ModInfo с заполненными данными.

    Raises:
        ModParseError: Если файл не найден, не является ZIP-архивом 
                       или не содержит поддерживаемых метаданных.
    """
    archive_path = Path(file_path)
    if not archive_path.exists():
        raise ModParseError(f"Файл не найден: {file_path}")

    if not zipfile.is_zipfile(archive_path):
        raise ModParseError("Поддерживаются только файлы .jar и .zip")

    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            normalized_entries = _get_normalized_archive_entries(archive)
            metadata_file_name = _find_metadata_file(normalized_entries)
            
            raw_data = archive.read(normalized_entries[metadata_file_name])
            text = raw_data.decode("utf-8")

            if metadata_file_name.endswith(".json") or metadata_file_name == "mcmod.info":
                data = json.loads(text)
            else:
                data = tomllib.loads(text)

            mod_info = _extract_metadata(metadata_file_name, data)
            mod_info.source_path = archive_path
            mod_info.metadata_file_name = metadata_file_name

            mod_info.data_source = "Local"
            
            return mod_info

    except zipfile.BadZipFile as exc:
        raise ModParseError(f"Файл не является корректным архивом: {file_path}") from exc
    except Exception as exc:
        raise ModParseError(f"Не удалось распарсить мод {file_path}: {exc}") from exc


def _get_normalized_archive_entries(archive: zipfile.ZipFile) -> Dict[str, str]:
    """
    Создает карту соответствия имен файлов в архиве.
    
    Приводит все пути внутри архива к нижнему регистру и нормализует разделители 
    (/) для обеспечения кроссплатформенности и регистронезависимого поиска.

    Args:
        archive: Открытый объект zipfile.ZipFile.

    Returns:
        Словарь, где ключ - нормализованный путь в нижнем регистре, 
        а значение - оригинальный путь внутри архива.
    """
    normalized: Dict[str, str] = {}
    for raw_name in archive.namelist():
        normalized_name = str(PurePosixPath(raw_name)).lstrip("./").lower()
        normalized[normalized_name] = raw_name
    return normalized


def _find_metadata_file(entries: Dict[str, str]) -> str:
    """
    Ищет первый подходящий файл метаданных в архиве.

    Args:
        entries: Словарь нормализованных путей файлов архива.

    Returns:
        Нормализованное имя найденного файла метаданных.

    Raises:
        ModParseError: Если ни один поддерживаемый файл метаданных не найден.
    """
    for metadata_file in METADATA_FILES_PRIORITY:
        metadata_file = metadata_file.lower()
        if metadata_file in entries:
            return metadata_file
    raise ModParseError("В архиве не найден поддерживаемый файл метаданных")


def _to_pure_posix_path(val: Any) -> Optional[PurePosixPath]:
    """
    Конвертирует путь к иконке из метаданных в кроссплатформенный формат.

    Спецификация Fabric допускает, что 'icon' может быть словарем, где ключи — 
    размеры, а значения — пути к файлам. В этом случае выбирается первый доступный 
    путь. Для остальных загрузчиков ожидается обычная строка.

    Args:
        val: Значение из поля 'icon' (строка или словарь).

    Returns:
        Объект PurePosixPath с путем к файлу или None.
    """
    if not val:
        return None
    if isinstance(val, dict):
        val = next(iter(val.values()), None)
    return PurePosixPath(str(val)) if isinstance(val, str) else None


def _extract_metadata(metadata_name: str, data: Any) -> ModInfo:
    """
    Перенаправляет разобранные данные файла в соответствующий парсер загрузчика.

    Args:
        metadata_name: Имя найденного файла метаданных (нормализованное).
        data: Декодированный объект (dict или list), полученный из JSON/TOML.

    Returns:
        Сформированный объект ModInfo.

    Raises:
        ModParseError: Если имя файла не распознано.
    """
    if metadata_name == "quilt.mod.json":
        info = _parse_quilt_metadata(data)
        info.loader_type = "Quilt"
        return info
    if metadata_name == "fabric.mod.json":
        info = _parse_fabric_metadata(data)
        info.loader_type = "Fabric"
        return info
    if metadata_name == "meta-inf/neoforge.mods.toml":
        info = _parse_toml_metadata(data)
        info.loader_type = "NeoForge"
        return info
    if metadata_name == "meta-inf/mods.toml":
        info = _parse_toml_metadata(data)
        info.loader_type = "Forge"
        return info
    if metadata_name == "mcmod.info":
        info = _parse_mcmod_info(data)
        info.loader_type = "Legacy Forge"
        return info
    raise ModParseError(f"Неизвестный формат: {metadata_name}")


# --- Парсеры для конкретных загрузчиков ---

def _parse_quilt_metadata(data: Any) -> ModInfo:
    """
    Извлекает данные из объекта quilt.mod.json (спецификация Quilt).

    Args:
        data: Декодированный JSON-объект.

    Returns:
        Объект ModInfo с заполненными полями мода.

    Raises:
        ModParseError: Если корневой элемент не является словарем.
    """
    if not isinstance(data, dict):
        raise ModParseError("Неверный формат quilt.mod.json: ожидался словарь")

    loader_data = data.get("quilt_loader", {})
    metadata = loader_data.get("metadata", {})

    return ModInfo(
        mod_id=loader_data.get("id"),
        name=metadata.get("name"),
        version=loader_data.get("version"),
        description=metadata.get("description"),
        authors=_get_authors_quilt(metadata.get("contributors")),
        icon_path=_to_pure_posix_path(metadata.get("icon")),
        minecraft_version=_get_mc_version_quilt(loader_data.get("depends"))
    )


def _parse_fabric_metadata(data: Any) -> ModInfo:
    """
    Извлекает данные из объекта fabric.mod.json (спецификация Fabric).

    Args:
        data: Декодированный JSON-объект.

    Returns:
        Объект ModInfo с заполненными полями мода.

    Raises:
        ModParseError: Если корневой элемент не является словарем.
    """
    if not isinstance(data, dict):
        raise ModParseError("Неверный формат fabric.mod.json: ожидался словарь")

    return ModInfo(
        mod_id=data.get("id"),
        name=data.get("name") or data.get("displayName"),
        version=data.get("version"),
        description=data.get("description"),
        authors=_get_authors_fabric(data.get("authors") or data.get("contributors")),
        icon_path=_to_pure_posix_path(data.get("icon")),
        minecraft_version=_get_mc_version_fabric(data.get("depends"))
    )


def _parse_toml_metadata(data: Any) -> ModInfo:
    """
    Извлекает данные из объекта mods.toml (спецификация Forge и NeoForge).

    Args:
        data: Декодированный TOML-объект.

    Returns:
        Объект ModInfo с заполненными полями мода.

    Raises:
        ModParseError: Если корневой элемент не является словарем или 
                       отсутствует обязательная секция [[mods]].
    """
    if not isinstance(data, dict):
        raise ModParseError("Неверный формат mods.toml: ожидался словарь")

    mods = data.get("mods")
    if not isinstance(mods, list) or not mods:
        raise ModParseError("В файле mods.toml отсутствует или пуста секция [[mods]]")

    mod = mods[0]
    if not isinstance(mod, dict):
        raise ModParseError("Неверная структура данных в секции [[mods]]")

    return ModInfo(
        mod_id=mod.get("modId"),
        name=mod.get("displayName"),
        version=mod.get("version"),
        description=mod.get("description"),
        authors=_get_authors_forge(mod.get("authors")),
        icon_path=_to_pure_posix_path(mod.get("logoFile")),
        minecraft_version=_get_mc_version_forge(data.get("dependencies"))
    )


def _parse_mcmod_info(data: Any) -> ModInfo:
    """
    Извлекает данные из объекта mcmod.info (старый формат Forge).

    Args:
        data: Декодированный JSON-объект или список объектов.

    Returns:
        Объект ModInfo с заполненными полями мода.

    Raises:
        ModParseError: Если формат не является словарем или списком словарей.
    """
    if isinstance(data, list) and data:
        data = data[0]
    
    if not isinstance(data, dict):
        raise ModParseError("Неверный формат mcmod.info: ожидался словарь")

    return ModInfo(
        mod_id=data.get("modid"),
        name=data.get("name"),
        version=data.get("version"),
        description=data.get("description"),
        authors=_get_authors_legacy(data.get("authorList")),
        icon_path=_to_pure_posix_path(data.get("logoFile")),
        minecraft_version=data.get("mcversion")
    )


# --- Методы для извлечения информации об авторах ---

def _get_authors_quilt(raw_contributors: Any) -> Optional[List[str]]:
    """
    Извлекает список авторов по спецификации quilt.mod.json.
    
    Согласно документации Quilt (RFC-2), поле 'contributors' в секции 'metadata' 
    является объектом (dict), где ключи — это имена участников (строки), 
    а значения — их роли (строки).
    
    Args:
        raw_contributors: Сырые данные по ключу 'contributors'.

    Returns:
        Список строк с именами авторов (ключи словаря) или None.
    """
    if not isinstance(raw_contributors, dict):
        return None
    return list(raw_contributors.keys())


def _get_authors_fabric(raw_authors: Any) -> Optional[List[str]]:
    """
    Извлекает список авторов по спецификации fabric.mod.json.
    
    Согласно официальной документации Fabric, поле 'authors' (или 'contributors')
    является массивом (list), где каждый элемент — это либо строка с именем,
    либо объект (dict), содержащий обязательное строковое поле 'name'.

    Args:
        raw_authors: Сырые данные по ключу 'authors' или 'contributors'.

    Returns:
        Список строк с именами авторов или None.
    """
    if not isinstance(raw_authors, list):
        return None
        
    result = []
    for item in raw_authors:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict) and "name" in item and isinstance(item["name"], str):
            result.append(item["name"])
            
    return result if result else None


def _get_authors_forge(raw_authors: Any) -> Optional[List[str]]:
    """
    Извлекает список авторов по спецификации mods.toml.
    
    Согласно документации Forge/NeoForge, поле 'authors' в секции '[[mods]]' 
    является строкой (String). Часто авторы перечисляются через запятую 
    внутри этой строки.
    
    Args:
        raw_authors: Сырые данные по ключу 'authors'.

    Returns:
        Список авторов (разделенный по запятым) или None.
    """
    if not isinstance(raw_authors, str):
        return None
    return [author.strip() for author in raw_authors.split(",") if author.strip()]


def _get_authors_legacy(raw_authors: Any) -> Optional[List[str]]:
    """
    Извлекает список авторов по старой спецификации mcmod.info.
    
    Поле 'authorList' является списком (Array) строк.
    
    Args:
        raw_authors: Сырые данные по ключу 'authorList'.

    Returns:
        Список строк с именами авторов или None.
    """
    if not isinstance(raw_authors, list):
        return None
    return [str(item) for item in raw_authors if isinstance(item, str)]


# --- Методы для извлечения версии Minecraft ---

def _get_mc_version_quilt(depends: Any) -> Optional[str]:
    """
    Извлекает версию Minecraft по спецификации quilt.mod.json.
    
    Спецификация: блок quilt_loader.depends - это массив (list) объектов (dict) 
    или строк. Если это объект, он содержит обязательные поля "id" и "versions".
    
    Args:
        depends: Данные блока зависимости.

    Returns:
        Версия или None.
    """
    if not isinstance(depends, list):
        return None
        
    for entry in depends:
        if isinstance(entry, dict) and entry.get("id") == "minecraft":
            versions = entry.get("versions")
            if isinstance(versions, str):
                return versions
            if isinstance(versions, list) and versions:
                return str(versions[0])
    return None


def _get_mc_version_fabric(depends: Any) -> Optional[str]:
    """
    Извлекает версию Minecraft по спецификации fabric.mod.json.
    
    Спецификация: блок depends - это объект (dict), где ключи - ID модов 
    (например, "minecraft"), а значения - строки или массивы строк с версиями.
    
    Args:
        depends: Данные блока зависимости.

    Returns:
        Версия или None.
    """
    if not isinstance(depends, dict):
        return None
        
    version = depends.get("minecraft")
    if isinstance(version, str):
        return version
    if isinstance(version, list) and version:
        return str(version[0])
    return None


def _get_mc_version_forge(depends: Any) -> Optional[str]:
    """
    Извлекает версию Minecraft по спецификации mods.toml (Forge/NeoForge).
    
    Спецификация: блок depends - это словарь (dict), где ключи - ID 
    целевых модов. Значения - массивы (list) объектов (dict) с полями 
    "modId" и "versionRange".
    
    Args:
        depends: Данные блока зависимости.

    Returns:
        Версия или None.
    """
    if not isinstance(depends, dict):
        return None
    
    for dep_list in depends.values():
        if not isinstance(dep_list, list):
            continue
        for entry in dep_list:
            if isinstance(entry, dict) and entry.get("modId") == "minecraft":
                version = entry.get("versionRange")
                if isinstance(version, str):
                    return version
    return None
