"""
Центральный модуль конфигурации приложения.
Обеспечивает типизированный доступ ко всем настройкам через синглтон AppConfig.
"""

from pathlib import Path
from PySide6.QtCore import QSettings


ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / "config.ini"


class AppConfig:
    """Класс-обертка для управления настройками приложения."""
    
    def __init__(self):
        self._settings = QSettings(str(CONFIG_PATH), QSettings.Format.IniFormat)

    @property
    def clear_selection_after_download(self) -> bool:
        """Снимать ли выделение с мода после успешной загрузки."""
        raw_value = self._settings.value("clear_selection_after_download", False, type=bool)
        return bool(raw_value)
        
    @clear_selection_after_download.setter
    def clear_selection_after_download(self, value: bool):
        self._settings.setValue("clear_selection_after_download", value)
        

config = AppConfig()
