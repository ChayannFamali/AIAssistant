"""
Utils package
"""
from .logger import setup_logger
from .settings_manager import SettingsManager
from .history_manager import HistoryManager, DialogSession, DialogMessage
from .clipboard_helper import ClipboardHelper
from .question_detector import QuestionDetector
from .hotkeys_manager import HotkeysManager, DEFAULT_HOTKEYS
from .themes import ThemeManager, ThemeType, DarkTheme, LightTheme  #  НОВОЕ
from .statistics_manager import StatisticsManager  #  НОВОЕ
from .audio_utils import (
    normalize_audio, 
    calculate_rms, 
    is_silence, 
    resample_audio,
    trim_silence,
    merge_audio_chunks
)

__all__ = [
    'setup_logger',
    'SettingsManager',
    'HistoryManager',
    'DialogSession',
    'DialogMessage',
    'ClipboardHelper',
    'QuestionDetector',
    'HotkeysManager',
    'DEFAULT_HOTKEYS',
    'ThemeManager',
    'ThemeType',
    'DarkTheme',
    'LightTheme',
    'StatisticsManager',
    'normalize_audio',
    'calculate_rms',
    'is_silence',
    'resample_audio',
    'trim_silence',
    'merge_audio_chunks']
