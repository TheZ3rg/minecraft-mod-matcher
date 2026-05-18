"""
Модуль окна настроек приложения.
"""

import logging
from pathlib import Path
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QCheckBox, 
                               QTabWidget, QWidget)
from PySide6.QtCore import Qt, QSettings, QUrl
from PySide6.QtGui import QDesktopServices


logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """Окно настроек приложения.
    
    Использует QSettings для сохранения параметров в локальный файл config.ini.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Настраиваем параметры самого окна и QSettings
        self._setup_settings()
        
        # Создаем и собираем все элементы UI
        self._init_ui()
        
        # Загружаем сохраненные значения и выставляем их в виджеты
        self._load_saved_settings()

    def _setup_settings(self):
        """Конфигурирует базовые свойства окна диалога и объект QSettings."""
        self.setWindowTitle("Настройки ModMatcher")
        self.setMinimumSize(450, 350)
        
        # Настройка INI-файла в корне проекта
        config_path = Path(__file__).resolve().parents[3] / "config.ini"
        self.settings = QSettings(str(config_path), QSettings.Format.IniFormat)

    def _init_ui(self):
        """Главный метод сборки интерфейса. Конструирует структуру макетов."""
        main_layout = QVBoxLayout(self)

        # Создаем менеджер вкладок
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Создаем и добавляем вкладки
        self.tabs.addTab(self._create_general_tab(), "Основные")
        self.tabs.addTab(self._create_debug_tab(), "Отладка")

        # Добавляем нижний ряд кнопок "Сохранить/Отмена"
        main_layout.addLayout(self._create_button_box())

    def _create_general_tab(self) -> QWidget:
        """Создает, компонует и возвращает виджет вкладки 'Основные'."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.clear_selection_cb = QCheckBox("Снимать выделение с мода после успешной загрузки")
        layout.addWidget(self.clear_selection_cb)
        
        layout.addStretch()
        return tab

    def _create_debug_tab(self) -> QWidget:
        """Создает, компонует и возвращает виджет вкладки 'Отладка'."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        info_label = QLabel("Здесь вы можете найти файлы журналов (логов) для поиска ошибок.\n"
                            "Прикрепляйте их при обращении к разработчику.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #9E9E9E;")
        layout.addWidget(info_label)
        
        self.open_logs_btn = QPushButton("📂 Открыть папку с логами")
        self.open_logs_btn.setMinimumHeight(35)
        self.open_logs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_logs_btn.clicked.connect(self.open_logs_folder)
        layout.addWidget(self.open_logs_btn)
        
        layout.addStretch()
        return tab

    def _create_button_box(self) -> QHBoxLayout:
        """Создает и возвращает горизонтальный макет с кнопками управления."""
        layout = QHBoxLayout()
        layout.addStretch()
        
        save_btn = QPushButton("Сохранить")
        save_btn.setMinimumWidth(100)
        save_btn.clicked.connect(self.save_and_close)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject) # Стандартный метод QDialog для закрытия/отмены
        
        layout.addWidget(save_btn)
        layout.addWidget(cancel_btn)
        return layout

    def _load_saved_settings(self):
        """Загружает конфигурацию из файла и безопасно выставляет состояния виджетов."""
        is_clear_enabled = bool(self.settings.value("clear_selection_after_download", False, type=bool))
        self.clear_selection_cb.setChecked(is_clear_enabled)

    def open_logs_folder(self):
        """Открывает директорию с логами в системном проводнике."""
        log_dir = Path(__file__).resolve().parents[3] / "logs"
        
        if log_dir.exists() and log_dir.is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(log_dir)))
            logger.info("Пользователь открыл папку с логами.")
        else:
            logger.warning("Папка с логами не найдена!")

    def save_and_close(self):
        """Сохраняет измененные параметры на диск и закрывает диалог."""
        self.settings.setValue("clear_selection_after_download", self.clear_selection_cb.isChecked())
        logger.info("Настройки сохранены в config.ini.")
        self.accept() # Стандартный метод QDialog для успешного закрытия
