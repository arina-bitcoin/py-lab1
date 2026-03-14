import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None
) -> None:
    """
    Настройка логирования для всего проекта.
    
    Args:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
        log_file: Путь к файлу для записи логов (если None - только консоль)
        format_string: Формат сообщений (если None - используется стандартный)
    """
    
    # Формат по умолчанию: время - имя модуля - уровень - сообщение
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Формат времени
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Базовые настройки
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Если указан файл, добавляем файловый обработчик
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    # Настраиваем корневой логгер (force=True с Python 3.8 — переприменить при повторном вызове)
    logging.basicConfig(
        level=level,
        format=format_string,
        datefmt=date_format,
        handlers=handlers,
        force=True,
    )
    
    # Логируем начало работы
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={logging.getLevelName(level)}")
    if log_file:
        logger.info(f"Log file: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Получить логгер для конкретного модуля.
    
    Args:
        name: Имя модуля (обычно __name__)
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    return logging.getLogger(name)


default_logger = logging.getLogger(__name__)