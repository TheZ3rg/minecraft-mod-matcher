"""
Модуль для получения информации о версиях Minecraft.

Этот модуль предоставляет класс MinecraftVersions, который отвечает за загрузку
и обработку данных о версиях Minecraft с официального API Mojang.
"""

import requests
import logging
from typing import List, Dict


logger = logging.getLogger(__name__)


class MinecraftVersions:
    """Класс для получения списка версий Minecraft с официального API Mojang.

    Класс загружает манифест версий с Mojang API и предоставляет доступ
    к различным типам версий через свойства. Реализует обработку сетевых
    ошибок при запросе данных.

    Attributes:
        MANIFEST_URL (str): URL манифеста версий Mojang
        versions (List[Dict]): Список всех версий, загруженных из API
        latest_release (str): Версия последнего релиза
        latest_snapshot (str): Версия последнего снапшота
    """
    
    MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
    
    def __init__(self):
        """Инициализирует экземпляр MinecraftVersions с пустыми данными.

        Создает пустые структуры данных для хранения информации о версиях.
        Данные будут загружены при первом обращении к свойствам или вызове
        метода load_versions().
        """
        self.versions: List[Dict] = []
        self.latest_release: str = ""
        self.latest_snapshot: str = ""
    
    def load_versions(self) -> bool:
        """Загружает данные о версиях с Mojang API.

        Выполняет HTTP-запрос к Mojang API для получения манифеста версий.
        При успешном выполнении заполняет атрибуты класса данными.

        Returns:
            bool: True если загрузка прошла успешно, False в случае ошибки
        """
        try:
            response = requests.get(self.MANIFEST_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            self.latest_release = data["latest"]["release"]
            self.latest_snapshot = data["latest"]["snapshot"]
            self.versions = data["versions"]
            
            return True
            
        except requests.exceptions.Timeout:
            logger.error("Ошибка: превышено время ожидания ответа от Mojang API")
        except requests.exceptions.ConnectionError:
            logger.error("Ошибка: не удалось подключиться к Mojang API. Проверьте интернет-соединение")
        except requests.exceptions.HTTPError as e:
            logger.error(f"Ошибка HTTP при запросе версий у Mojang API: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Сетевая ошибка requests при запросе версий: {e}")
        except KeyError as e:
            logger.error(f"Ошибка: неожиданная структура JSON от Mojang API. Отсутствует ключ {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при загрузке версий: {e}")

        return False

    @property
    def release_versions(self) -> List[str]:
        """Возвращает список ID релизных версий Minecraft.

        Загружает версии при первом обращении, если они еще не загружены.
        Возвращает только версии с типом "release" (стабильные релизы).

        Returns:
            Список строк с идентификаторами версий (например ["1.20.4", "1.20.3", ...])
        """
        if not self.versions:
            self.load_versions()

        return [v["id"] for v in self.versions if v["type"] == "release"]
    
    @property
    def snapshots(self) -> List[str]:
        """Возвращает список ID снапшотов Minecraft.

        Загружает версии при первом обращении, если они еще не загружены.
        Возвращает только версии с типом "snapshot" (экспериментальные сборки).

        Returns:
            Список строк с идентификаторами снапшотов
        """
        if not self.versions:
            self.load_versions()

        return [v["id"] for v in self.versions if v["type"] == "snapshot"]
    
    @property
    def all_versions(self) -> List[str]:
        """Возвращает список ID всех версий Minecraft.

        Загружает версии при первом обращении, если они еще не загружены.
        Возвращает все доступные версии независимо от их типа.

        Returns:
            Список строк с идентификаторами всех версий
        """
        if not self.versions:
            self.load_versions()

        return [v["id"] for v in self.versions]
