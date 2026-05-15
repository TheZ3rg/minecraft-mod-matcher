"""
Главный модуль запуска приложения ModMatcher.

Этот модуль инициализирует QApplication, создает главное окно приложения
MainWindow и запускает цикл обработки событий Qt.
"""

import sys
import ctypes
from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow

if __name__ == "__main__":

    if sys.platform == "win32":
        appid = 'ModMatcher.v1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
    
    app = QApplication()
    window = MainWindow()

    window.resize(1000, 700)

    window.show()

    exit_status = app.exec()
    print(f"DEBUG: Завершение работы. Код возврата: {exit_status}")
    sys.exit(exit_status)
