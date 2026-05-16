"""
Главный модуль запуска приложения ModMatcher.

Этот модуль инициализирует QApplication, создает главное окно приложения
MainWindow и запускает цикл обработки событий Qt.
"""

import sys
import ctypes
import logging
from logging.handlers import RotatingFileHandler
from PySide6.QtWidgets import QApplication
from pathlib import Path

from gui.main_window import MainWindow


logger = logging.getLogger(__name__)

def setup_logging():
    """Настройка логирования.
    
    Логи будут записываться в файл logs/modmatcher.log и выводиться в консоль.
    """
    log_format = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file_path = log_dir / "modmatcher.log"
    
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=1024 * 1024 * 5,
        backupCount=3,
        encoding="utf-8"
    )
    
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        handlers=[
            file_handler,
            logging.StreamHandler(sys.stdout)
        ]
    )


if __name__ == "__main__":

    if sys.platform == "win32":
        appid = 'ModMatcher.v1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
    
    setup_logging()
    logger.info("=== Запуск ModMatcher ===")

    app = QApplication()
    window = MainWindow()

    window.resize(1000, 700)

    window.show()

    exit_status = app.exec()
    logger.info(f"Завершение работы. Status: {exit_status}")
    sys.exit(exit_status)
