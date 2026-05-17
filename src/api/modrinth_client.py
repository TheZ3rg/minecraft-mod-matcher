"""
Модуль для работы с открытым API Modrinth (v2).

Обеспечивает поиск версий модов по хэшам файлов и проектов по их ID.
"""

import json
import requests
import logging
from typing import Optional, Dict, Any


logger = logging.getLogger(__name__)


class ModrinthClient:
    """Клиент для взаимодействия с Modrinth API."""
    
    BASE_URL = "https://api.modrinth.com/v2"

    def __init__(self):
        """Инициализирует клиент и устанавливает обязательные заголовки."""

        self.session = requests.Session()
        
        self.session.headers.update({
            "User-Agent": "TheZ3rg/ModMatcher/1.0 (lsv.thezerg@gmail.com)"
        })

    def get_version_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Ищет информацию о конкретной версии мода на Modrinth по его SHA-1 хэшу.

        Args:
            file_hash: Строка с SHA-1 хэшем файла. Для Modrinth API sha1 стоит по умолчанию

        Returns:
            Словарь с данными о версии мода от API или None, если файл не найден/произошла ошибка.
        """
        if not file_hash:
            return None

        url = f"{self.BASE_URL}/version_file/{file_hash}"

        try:
            response = self.session.get(url, timeout=10)

            # Если API возвращает 404, значит мода нет в базе
            if response.status_code == 404:
                logger.debug(f"Мод с хэшем {file_hash} не найден на Modrinth.")
                return None

            response.raise_for_status()
            
            data = response.json()

            logger.debug(f"Найдена информация для мода (Project ID: {data.get('project_id')})")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Сетевая ошибка при запросе к Modrinth API: {e}")
            return None
        
    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Получает полную информацию о проекте на Modrinth по его ID.

        Args:
            project_id: Уникальный ID проекта (например, 'P7dR8mSH').

        Returns:
            Словарь с данными о проекте или None.
        """
        if not project_id:
            return None

        url = f"{self.BASE_URL}/project/{project_id}"

        try:
            response = self.session.get(url, timeout=10)
            # Если API возвращает 404, значит проекта нет в базе
            if response.status_code == 404:
                logger.debug(f"Проект с ID {project_id} не найден на Modrinth.")
                return None
            
            response.raise_for_status()

            data = response.json()

            logger.debug(f"Получена информация о проекте {project_id}: {data.get('title', 'Без названия')}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Сетевая ошибка при запросе проекта {project_id}: {e}")
            return None

    def get_versions_by_hashes(self, hashes: list[str]) -> Optional[Dict[str, Any]]:
        """Получает информацию о множестве версий с помощью хэшей, разбивая запрос на чанки.

        Args:
            hashes: Список строк с SHA-1 хэшами файлов.

        Returns:
            Словарь, где ключ - это хэш, а значение - данные о версии мода от API.
            None при критической ошибке, или словарь с тем, что удалось получить.
        """
        if not hashes:
            return {}

        url = f"{self.BASE_URL}/version_files"
        result_data = {}
        # API может не принять слишком длинный список хэшей, 
        # поэтому разбиваем его на чанки по 50 штук (можно регулировать при необходимости)
        chunk_size = 50

        try:
            for i in range(0, len(hashes), chunk_size):
                chunk = hashes[i:i+chunk_size]
                
                data = {
                    "hashes": chunk,
                    "algorithm": "sha1"
                }
                
                response = self.session.post(url, json=data, timeout=15)
                response.raise_for_status()
                
                # Добавляем полученные данные текущего чанка в общий словарь
                result_data.update(response.json())
                
            return result_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при массовом запросе версий: {e}")
            # Возвращаем то, что успели скачать до ошибки
            return result_data if result_data else None

    def get_projects_by_ids(self, project_ids: list[str]) -> Optional[list[Dict[str, Any]]]:
        """Получает информацию о множестве проектов по их ID, разбивая запрос на чанки.

        Args:
            project_ids: Список строк с ID проектов.
        
        Returns:
            Список словарей с данными о проектах от API.
            None при критической ошибке, или список с тем, что удалось получить.
        """
        if not project_ids:
            return []

        url = f"{self.BASE_URL}/projects"
        result_list = []
        # URL GET-запроса имеет ограничение по длине, 
        # поэтому разбиваем список ID на чанки по 50 штук (можно регулировать при необходимости)
        chunk_size = 50

        try:
            for i in range(0, len(project_ids), chunk_size):
                chunk = project_ids[i:i + chunk_size]
                
                params = {
                    "ids": json.dumps(chunk)
                }
                
                response = self.session.get(url, params=params, timeout=15)
                response.raise_for_status()
                
                # Добавляем элементы списка в общий список
                result_list.extend(response.json())
                
            return result_list
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при массовом запросе проектов: {e}")
            # Возвращаем то, что успели скачать до ошибки
            return result_list if result_list else None
    
    def download_icon(self, url: str) -> Optional[bytes]:
        """
        Скачивает изображение по прямой ссылке.

        Args:
            url: Прямая ссылка на картинку.

        Returns:
            Байты изображения или None при ошибке.
        """
        if not url:
            return None

        try:
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            
            return response.content 
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Не удалось скачать иконку по ссылке {url}: {e}")
            return None
