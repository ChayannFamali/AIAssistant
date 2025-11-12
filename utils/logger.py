"""
Настройка логирования для AI Assistant
"""
import logging
import sys
from pathlib import Path
from typing import Optional

try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False

# Глобальный флаг для предотвращения повторной настройки
_LOGGING_CONFIGURED = False


def setup_logger(
    name: str = "AIAssistant",
    level: int = logging.INFO,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Настроить логирование для приложения (вызывать ОДИН РАЗ в main.py)
    
    Args:
        name: Корневое имя logger (обычно "AIAssistant")
        level: Уровень логирования для консоли
        log_file: Путь к файлу логов (если None, используется ~/.aiassistant/logs/app.log)
        
    Returns:
        Настроенный root logger
    """
    global _LOGGING_CONFIGURED
    
    if _LOGGING_CONFIGURED:
        return logging.getLogger(name)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG) 
    
    root_logger.handlers.clear()
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if HAS_COLORLOG:
        console_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(levelname)-8s%(reset)s %(blue)s[%(name)s]%(reset)s %(message)s',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    else:
        console_formatter = logging.Formatter(
            '%(levelname)-8s [%(name)s] %(message)s'
        )
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # === File Handler ===
    if log_file is None:
        log_dir = Path.home() / '.aiassistant' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'app.log'
    
    try:
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # В файл пишем все
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create log file: {e}", file=sys.stderr)
    
    logging.getLogger('webrtcvad').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('torch').setLevel(logging.WARNING)
    logging.getLogger('whisper').setLevel(logging.WARNING)
    
    _LOGGING_CONFIGURED = True
    
    return logging.getLogger(name)


def get_logger(name: str) -> logging.Logger:
    """
    Получить logger для модуля (использовать во всех остальных файлах)
    
    ВАЖНО: Вызывать ПОСЛЕ setup_logger() в main.py
    
    Args:
        name: Имя модуля (например, "AIAssistant.MainWindow")
        
    Returns:
        Logger instance (наследует handlers от root logger)
        
    Example:
        >>> from utils.logger import get_logger
        >>> logger = get_logger("AIAssistant.MyModule")
        >>> logger.info("Hello")
    """
    return logging.getLogger(name)


def reset_logging():
    """Сбросить настройки логирования (для тестов)"""
    global _LOGGING_CONFIGURED
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    _LOGGING_CONFIGURED = False
