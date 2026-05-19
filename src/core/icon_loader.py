import zipfile
import logging
from PySide6.QtGui import QPixmap
from pathlib import Path, PurePosixPath


logger = logging.getLogger(__name__)


def load_icon_from_archive(archive_path: Path, icon_internal_path: PurePosixPath) -> QPixmap:
    """
    Извлекает картинку из ZIP-архива и превращает её в QPixmap.
    Возвращает пустой QPixmap, если иконка не найдена или архив поврежден.

    Args:
        archive_path (Path): Путь к ZIP-архиву.
        icon_internal_path (PurePosixPath): Внутренний путь к иконке внутри архива.

    Returns:
        QPixmap: Загруженная иконка или пустой QPixmap при ошибке.
    """
    pixmap = QPixmap()
    
    if not archive_path or not icon_internal_path:
        return pixmap

    try:
        with zipfile.ZipFile(archive_path, 'r') as archive:
            image_data = archive.read(str(icon_internal_path))
            
            pixmap.loadFromData(image_data)
    except Exception as e:
        logger.error(f"Не удалось загрузить иконку из {archive_path.name}: {e}")
        
    return pixmap