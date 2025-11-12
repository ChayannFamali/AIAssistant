"""
STT Thread - поток для транскрипции речи в текст
"""
import logging
import queue
import time
import numpy as np
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtCore import QThread, pyqtSignal

from core.transcriber import Transcriber
from utils.question_detector import QuestionDetector
from core.config import STTConfig

logger = logging.getLogger("AIAssistant.STTThread")


class TaskType(Enum):
    """Типы задач для STT Worker"""
    TRANSCRIBE = "transcribe"
    LOAD_MODEL = "load_model"
    UNLOAD_MODEL = "unload_model"


@dataclass
class STTTask:
    """Задача для STT Worker"""
    task_type: TaskType
    data: any = None


class STTWorker(QThread):
    """
    Worker thread для Speech-to-Text транскрипции
    Обрабатывает аудио чанки из очереди
    """
    
    transcription_ready = pyqtSignal(str, str)  
    question_detected = pyqtSignal(str)  
    
    model_load_started = pyqtSignal()
    model_load_finished = pyqtSignal(bool) 
    model_load_error = pyqtSignal(str)
    
    transcription_started = pyqtSignal()
    transcription_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        self.task_queue = queue.Queue()
        self.transcriber = Transcriber()
        self.question_detector = QuestionDetector()
        
        self.is_running = False
        self.auto_detect_questions = True 
        
        logger.info("STTWorker initialized")
    
    def run(self):
        """Основной цикл обработки задач"""
        logger.info("STTWorker thread started")
        
        self.is_running = True
        
        while self.is_running:
            try:
                task = self.task_queue.get(timeout=0.5)
                
                if task.task_type == TaskType.LOAD_MODEL:
                    self._handle_load_model(task.data)
                
                elif task.task_type == TaskType.TRANSCRIBE:
                    self._handle_transcribe(task.data)
                
                elif task.task_type == TaskType.UNLOAD_MODEL:
                    self._handle_unload_model()
                
                self.task_queue.task_done()
            
            except queue.Empty:
                continue
            
            except Exception as e:
                logger.error(f"Unexpected error in STTWorker: {e}", exc_info=True)
        
        logger.info("STTWorker thread stopped")
    
    def _handle_load_model(self, model_size: str):
        """Загрузить модель Whisper"""
        logger.info(f"Loading Whisper model: {model_size}")
        self.model_load_started.emit()
        
        try:
            success = self.transcriber.load_model(model_size)
            
            if success:
                logger.info("Whisper model loaded successfully")
                self.model_load_finished.emit(True)
            else:
                logger.error("Whisper model loading failed")
                self.model_load_finished.emit(False)
                self.model_load_error.emit("Failed to load Whisper model")
        
        except Exception as e:
            logger.error(f"Model loading exception: {e}", exc_info=True)
            self.model_load_finished.emit(False)
            self.model_load_error.emit(str(e))
    
    def _handle_transcribe(self, audio_data: np.ndarray):
        """Транскрибировать аудио"""
        if not self.transcriber.is_loaded:
            logger.error("Transcriber model not loaded")
            self.transcription_error.emit("Model not loaded")
            return
        
        try:
            print(f"🎤 STT: Starting transcription ({len(audio_data)} samples)") 
            
            logger.debug(f"Transcribing audio: {len(audio_data)} samples")
            self.transcription_started.emit()
            
            start_time = time.time()
            
            text = self.transcriber.transcribe(audio_data)
            
            elapsed = time.time() - start_time
            
            print(f"✅ STT: Transcription done in {elapsed:.2f}s: '{text}'")  
            
            logger.info(f"Transcription completed in {elapsed:.2f}s: '{text}'")
            
            if not text:
                print("⚠️ STT: Empty transcription result")  
                logger.debug("Empty transcription result")
                return
            
            language = self.question_detector._detect_language(text)
            print(f"📤 STT: Emitting transcription_ready signal: '{text}' (lang: {language})")
            self.transcription_ready.emit(text, language)
            
            if self.auto_detect_questions:
                is_question = self.question_detector.is_question(text, language)
                print(f"❓ Question check: {is_question} for '{text}'")  
                
                if is_question:
                    current_time = time.time()
                    should_process = self.question_detector.should_process_question(text, current_time)
                    print(f"🔄 Should process: {should_process}")  
                    
                    if should_process:
                        logger.info(f"Question detected: {text}")
                        print(f"✅ Emitting question_detected: '{text}'")  
                        self.question_detected.emit(text)
                    else:
                        logger.debug("Duplicate question, ignoring")
                        print(f"⏭️ Duplicate question, ignoring")  

        
        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            self.transcription_error.emit(str(e))
    
    def _handle_unload_model(self):
        """Выгрузить модель"""
        logger.info("Unloading Whisper model")
        self.transcriber.unload_model()
    
    
    def load_model(self, model_size: str = STTConfig.MODEL_SIZE):
        """Добавить задачу загрузки модели"""
        task = STTTask(TaskType.LOAD_MODEL, model_size)
        self.task_queue.put(task)
        logger.debug(f"Load model task queued: {model_size}")
    
    def transcribe_audio(self, audio_data: np.ndarray):
        """Добавить задачу транскрипции"""
        task = STTTask(TaskType.TRANSCRIBE, audio_data)
        self.task_queue.put(task)
        logger.debug("Transcribe task queued")
    
    def unload_model(self):
        """Добавить задачу выгрузки модели"""
        task = STTTask(TaskType.UNLOAD_MODEL)
        self.task_queue.put(task)
        logger.debug("Unload model task queued")
    
    def set_auto_detect_questions(self, enabled: bool):
        """Включить/выключить автодетект вопросов"""
        self.auto_detect_questions = enabled
        logger.info(f"Auto question detection: {enabled}")
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down STTWorker")
        self.is_running = False
        self.quit()
        
        if not self.wait(5000):
            logger.warning("STTWorker did not stop gracefully, terminating")
            self.terminate()
            self.wait()
