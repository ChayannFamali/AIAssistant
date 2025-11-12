"""
LLM Worker Thread - обработка LLM запросов в отдельном потоке
"""
import queue
import logging
from typing import Optional
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtCore import QThread, pyqtSignal

from core.llm_engine import LLMEngine

logger = logging.getLogger("AIAssistant.LLMThread")


class TaskType(Enum):
    """Типы задач для LLM Worker"""
    LOAD_MODEL = "load_model"
    GENERATE = "generate"
    STOP = "stop"
    CLEAR_CONTEXT = "clear_context"
    UNLOAD_MODEL = "unload_model"


@dataclass
class LLMTask:
    """Задача для LLM Worker"""
    task_type: TaskType
    data: any = None


class LLMWorker(QThread):
    """
    Worker thread для обработки LLM операций
    Обрабатывает задачи из очереди и эмитит сигналы в Main Thread
    """
    
    token_generated = pyqtSignal(str) 
    generation_started = pyqtSignal(str)  
    generation_finished = pyqtSignal(str) 
    generation_error = pyqtSignal(str) 
    
    model_load_started = pyqtSignal()  
    model_load_progress = pyqtSignal(float)  
    model_load_finished = pyqtSignal(bool)  
    model_load_error = pyqtSignal(str)  
    
    performance_stats = pyqtSignal(dict) 
    context_cleared = pyqtSignal()  
    
    def __init__(self):
        super().__init__()
        self.task_queue = queue.Queue()
        self.engine = LLMEngine()
        self.is_running = True
        
        logger.info("LLMWorker initialized")
    
    def run(self):
        """
        Основной цикл обработки задач
        Запускается автоматически при start()
        """
        logger.info("LLMWorker thread started")
        
        while self.is_running:
            try:
                task = self.task_queue.get(timeout=0.5)
                
                if task.task_type == TaskType.LOAD_MODEL:
                    self._handle_load_model(task.data)
                
                elif task.task_type == TaskType.GENERATE:
                    self._handle_generate(task.data)
                
                elif task.task_type == TaskType.STOP:
                    self._handle_stop()
                
                elif task.task_type == TaskType.CLEAR_CONTEXT:
                    self._handle_clear_context()
                
                elif task.task_type == TaskType.UNLOAD_MODEL:
                    self._handle_unload_model()
                
                self.task_queue.task_done()
                
            except queue.Empty:
                continue
            
            except Exception as e:
                logger.error(f"Unexpected error in LLMWorker: {e}", exc_info=True)
        
        logger.info("LLMWorker thread stopped")
    
    def _handle_load_model(self, model_path: str):
        """
        Обработать загрузку модели
        
        Args:
            model_path: Путь к файлу модели
        """
        logger.info(f"Loading model: {model_path}")
        self.model_load_started.emit()
        
        try:
            def progress_callback(progress: float):
                self.model_load_progress.emit(progress)
            
            success = self.engine.load_model(model_path, progress_callback)
            
            if success:
                logger.info("Model loaded successfully")
                self.model_load_finished.emit(True)
            else:
                logger.error("Model loading failed")
                self.model_load_finished.emit(False)
                self.model_load_error.emit("Failed to load model. Check logs for details.")
        
        except Exception as e:
            logger.error(f"Model loading exception: {e}", exc_info=True)
            self.model_load_finished.emit(False)
            self.model_load_error.emit(f"Error: {str(e)}")
    
    def _handle_generate(self, question: str):
        """
        Обработать генерацию ответа
        
        Args:
            question: Вопрос пользователя
        """
        logger.info(f"Generating answer for: {question[:50]}...")
        self.generation_started.emit(question)
        
        try:
            full_answer = ""
            
            for token in self.engine.generate_with_context(question):
                if token.startswith("[ERROR"):
                    self.generation_error.emit(token)
                    return
                
                full_answer += token
                self.token_generated.emit(token)
            
            logger.info(f"Generation finished: {len(full_answer)} chars")
            self.generation_finished.emit(full_answer)
            
            stats = self.engine.get_performance_stats()
            self.performance_stats.emit({
                'tokens_per_second': stats.tokens_per_second,
                'time_to_first_token': stats.time_to_first_token,
                'total_time': stats.total_generation_time,
                'ram_mb': stats.ram_usage_mb,
                'total_tokens': stats.total_tokens
            })
        
        except Exception as e:
            logger.error(f"Generation exception: {e}", exc_info=True)
            self.generation_error.emit(f"Error: {str(e)}")
    
    def _handle_stop(self):
        """Остановить текущую генерацию"""
        logger.info("Stopping generation")
        self.engine.stop_generation()
    
    def _handle_clear_context(self):
        """Очистить контекст диалога"""
        logger.info("Clearing context")
        self.engine.clear_context()
        self.context_cleared.emit()
    
    def _handle_unload_model(self):
        """Выгрузить модель"""
        logger.info("Unloading model")
        self.engine.unload_model()
    
    
    def load_model(self, model_path: str):
        """Добавить задачу загрузки модели"""
        task = LLMTask(TaskType.LOAD_MODEL, model_path)
        self.task_queue.put(task)
        logger.debug("Load model task queued")
    
    def generate_answer(self, question: str):
        """Добавить задачу генерации ответа"""
        task = LLMTask(TaskType.GENERATE, question)
        self.task_queue.put(task)
        logger.debug("Generate task queued")
    
    def stop_generation(self):
        """Добавить задачу остановки генерации"""
        task = LLMTask(TaskType.STOP)
        self.task_queue.put(task)
        logger.debug("Stop task queued")
    
    def clear_context(self):
        """Добавить задачу очистки контекста"""
        task = LLMTask(TaskType.CLEAR_CONTEXT)
        self.task_queue.put(task)
        logger.debug("Clear context task queued")
    
    def unload_model(self):
        """Добавить задачу выгрузки модели"""
        task = LLMTask(TaskType.UNLOAD_MODEL)
        self.task_queue.put(task)
        logger.debug("Unload model task queued")
    
    def shutdown(self):
        """Graceful shutdown потока"""
        logger.info("Shutting down LLMWorker")
        self.is_running = False
        self.quit()
        
        if not self.wait(5000): 
            logger.warning("LLMWorker did not stop gracefully, terminating")
            self.terminate()
            self.wait()
