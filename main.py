"""
AI Assistant - Desktop application for meeting assistance
Entry point
"""

import sys
import os

if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
    exe_dir = os.path.dirname(sys.executable)
    
    # Добавляем ВСЕ возможные пути где могут быть DLL
    dll_paths = [
        application_path,  # _internal/
        os.path.join(application_path, 'torch', 'lib'),  # _internal/torch/lib/
        os.path.join(exe_dir, '_internal'),
        os.path.join(exe_dir, '_internal', 'torch', 'lib'),
    ]
    
    for path in dll_paths:
        if os.path.exists(path):
            try:
                os.add_dll_directory(path)
                print(f"Added DLL search path: {path}")
            except (AttributeError, OSError) as e:
                pass
            os.environ['PATH'] = path + os.pathsep + os.environ.get('PATH', '')

import torch
import whisper

if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except Exception:
        pass
    
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'

import warnings
import logging

warnings.filterwarnings("ignore", category=UserWarning, module="webrtcvad")
warnings.filterwarnings("ignore", message=".*pkg_resources.*")

if sys.platform == 'win32':
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from ui.main_window import MainWindow
from utils.logger import setup_logger
from core.config import AppConfig


def main():
    """Main entry point"""
    
    logger = setup_logger("AIAssistant", level=logging.INFO)
    logger.info("=" * 60)
    logger.info(f"{AppConfig.APP_NAME} v{AppConfig.APP_VERSION} starting...")
    logger.info("=" * 60)
    
    app = QApplication(sys.argv)
    app.setApplicationName(AppConfig.APP_NAME)
    app.setOrganizationName(AppConfig.COMPANY_NAME)
    
    try:
        import qdarktheme
        app.setStyleSheet(qdarktheme.load_stylesheet())
        logger.info("Dark theme applied")
    except ImportError:
        logger.warning("qdarktheme not installed, using default theme")
    
    window = MainWindow()
    window.show()
    
    logger.info("Application window shown")
    logger.info("Ready for user input")
    
    exit_code = app.exec()
    
    logger.info("Application exiting")
    logger.info("=" * 60)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
