"""
Центральный модуль конфигурации приложения.
Обеспечивает типизированный доступ ко всем настройкам через синглтон AppConfig.
"""

import sys
from pathlib import Path
from PySide6.QtCore import QSettings


if getattr(sys, 'frozen', False):
    ROOT_DIR = Path(sys.executable).parent
else:
    ROOT_DIR = Path(__file__).resolve().parents[2]

CONFIG_PATH = ROOT_DIR / "config.ini"

def get_resource_path(relative_path: str) -> Path:
    """Получает абсолютный путь к ресурсам (иконкам, картинкам).
    
    Поддерживает как работу из исходного кода, так и из скомпилированного 
    через PyInstaller .exe файла (используя временную папку _MEIPASS).
    """
    # Безопасно пытаемся получить _MEIPASS. Если его нет, вернется None
    meipass = getattr(sys, '_MEIPASS', None)
    
    if meipass:
        # Мы запущены как скомпилированный .exe
        base_path = Path(meipass)
    else:
        # Мы запущены как обычный Python-скрипт из IDE
        base_path = Path(__file__).resolve().parents[2]

    return base_path / relative_path


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
