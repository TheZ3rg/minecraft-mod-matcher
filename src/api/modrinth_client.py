"""
Модуль для работы с открытым API Modrinth (v2).

Обеспечивает поиск модов по хэшам файлов и проверку обновлений.
"""

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
        """
        Ищет информацию о конкретном файле мода на Modrinth по его SHA-1 хэшу.

        Args:
            file_hash: Строка с SHA-1 хэшем файла.

        Returns:
            Словарь с данными о версии мода от API или None, если файл не найден/произошла ошибка.
        """
        if not file_hash:
            return None

        url = f"{self.BASE_URL}/version_file/{file_hash}"
        # Явно указываем алгоритм, хотя для Modrinth sha1 стоит по умолчанию
        params = {"algorithm": "sha1"} 

        try:
            response = self.session.get(url, params=params, timeout=10)

            # Если API возвращает 404, значит мода нет в базе
            if response.status_code == 404:
                logger.debug(f"Мод с хэшем {file_hash} не найден на Modrinth.")
                return None

            response.raise_for_status()
            
            data = response.json()
            # Нам вернулась полная информация: project_id, version_id, списки файлов и т.д.
            logger.debug(f"Найдена информация для файла (Project ID: {data.get('project_id')})")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Сетевая ошибка при запросе к Modrinth API: {e}")
            return None
