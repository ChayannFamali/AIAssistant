"""
LLM Engine - Singleton класс для управления локальной LLM моделью
"""
import threading
import time
from typing import Iterator, Optional, Dict, List
from pathlib import Path
import logging
import psutil
import gc

from llama_cpp import Llama

from core.config import ModelConfig, GenerationParams, PerformanceStats, AppConfig

logger = logging.getLogger("AIAssistant.LLM")


class LLMEngine:
    """
    Singleton класс для работы с LLM моделью
    Thread-safe управление загрузкой, генерацией и контекстом
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.model: Optional[Llama] = None
        self.model_config = ModelConfig()
        self.gen_params = GenerationParams()
        
        self._generation_lock = threading.Lock()
        self._context_lock = threading.Lock()
        self._stop_flag = threading.Event()
        
        self.context_history: List[Dict[str, str]] = []
        self.max_context_messages = AppConfig.MAX_CONTEXT_MESSAGES
        
        self.last_stats = PerformanceStats()
        
        logger.info("LLMEngine initialized (Singleton)")
    
    def is_loaded(self) -> bool:
        """Проверить загружена ли модель"""
        return self.model is not None
    
    def validate_model_file(self, model_path: str) -> bool:
        """
        Валидация GGUF файла
        
        Args:
            model_path: Путь к файлу модели
            
        Returns:
            True если файл валиден
        """
        path = Path(model_path)
        
        if not path.exists():
            logger.error(f"Model file not found: {model_path}")
            return False
        
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb < 10:
            logger.error(f"Model file too small: {size_mb:.1f} MB")
            return False
        
        try:
            with open(model_path, 'rb') as f:
                magic = f.read(4)
                if magic != b'GGUF':
                    logger.error("Invalid GGUF magic number")
                    return False
        except Exception as e:
            logger.error(f"Failed to read model file: {e}")
            return False
        
        logger.info(f"Model file validated: {size_mb:.1f} MB")
        return True
    
    def check_available_ram(self, required_mb: int = 3000) -> bool:
        """
        Проверить достаточно ли RAM для загрузки модели
        
        Args:
            required_mb: Требуемый объем RAM в MB
            
        Returns:
            True если достаточно памяти
        """
        mem = psutil.virtual_memory()
        available_mb = mem.available / (1024 * 1024)
        
        logger.info(f"Available RAM: {available_mb:.0f} MB, Required: {required_mb} MB")
        
        if available_mb < required_mb:
            logger.error(f"Insufficient RAM: {available_mb:.0f} MB < {required_mb} MB")
            return False
        
        return True
    
    def load_model(
        self,
        model_path: str,
        progress_callback: Optional[callable] = None
    ) -> bool:
        """
        Загрузить LLM модель
        
        Args:
            model_path: Путь к GGUF файлу
            progress_callback: Callback для отображения прогресса (0.0 - 1.0)
            
        Returns:
            True если загрузка успешна
        """
        with self._generation_lock:
            try:
                if progress_callback:
                    progress_callback(0.1)
                
                if not self.validate_model_file(model_path):
                    return False
                
                if not self.check_available_ram():
                    return False
                
                if progress_callback:
                    progress_callback(0.2)
                
                if self.model is not None:
                    logger.info("Unloading previous model")
                    del self.model
                    gc.collect()
                
                if progress_callback:
                    progress_callback(0.3)
                
                logger.info(f"Loading model: {model_path}")
                logger.info(f"Config: n_ctx={self.model_config.n_ctx}, "
                           f"n_threads={self.model_config.n_threads}")
                
                start_time = time.time()
                
                self.model = Llama(
                    model_path=model_path,
                    n_ctx=self.model_config.n_ctx,
                    n_threads=self.model_config.n_threads,
                    n_batch=self.model_config.n_batch,
                    n_gpu_layers=self.model_config.n_gpu_layers,
                    use_mlock=self.model_config.use_mlock,
                    use_mmap=self.model_config.use_mmap,
                    verbose=self.model_config.verbose
                )
                
                load_time = time.time() - start_time
                logger.info(f"Model loaded in {load_time:.2f} seconds")
                
                if progress_callback:
                    progress_callback(0.8)
                
                logger.info("Running warmup generation...")
                warmup_start = time.time()
                
                _ = self.model(
                    "Hello",
                    max_tokens=5,
                    temperature=0.1,
                    echo=False
                )
                
                warmup_time = time.time() - warmup_start
                logger.info(f"Warmup completed in {warmup_time:.2f} seconds")
                
                if progress_callback:
                    progress_callback(1.0)
                
                logger.info("Model ready for inference")
                return True
                
            except Exception as e:
                logger.error(f"Failed to load model: {e}", exc_info=True)
                self.model = None
                return False
    
    def unload_model(self):
        """Выгрузить модель из памяти"""
        with self._generation_lock:
            if self.model is not None:
                logger.info("Unloading model")
                del self.model
                self.model = None
                gc.collect()
                logger.info("Model unloaded")
    
    def add_to_context(self, role: str, content: str):
        """
        Добавить сообщение в контекст
        
        Args:
            role: "user" или "assistant"
            content: Текст сообщения
        """
        with self._context_lock:
            self.context_history.append({"role": role, "content": content})
            
            if len(self.context_history) > self.max_context_messages:
                removed = self.context_history.pop(0)
                logger.debug(f"Context overflow, removed oldest message: {removed['role']}")
    
    def clear_context(self):
        """Очистить историю контекста"""
        with self._context_lock:
            self.context_history.clear()
            logger.info("Context cleared")
    
    def get_context_size(self) -> int:
        """Получить количество сообщений в контексте"""
        with self._context_lock:
            return len(self.context_history)
    
    def _build_prompt(self, question: str) -> str:
        """
        Построить промпт с системным сообщением и контекстом
        
        Args:
            question: Новый вопрос пользователя
            
        Returns:
            Полный промпт для модели
        """
        prompt = f"<|im_start|>system\n{AppConfig.SYSTEM_PROMPT}<|im_end|>\n"
        
        with self._context_lock:
            for msg in self.context_history:
                role = msg["role"]
                content = msg["content"]
                prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"
        
        prompt += f"<|im_start|>user\n{question}<|im_end|>\n<|im_start|>assistant\n"
        
        return prompt
    
    def generate_with_context(self, question: str) -> Iterator[str]:
        """
        Генерация ответа с учетом контекста (streaming)
        
        Args:
            question: Вопрос пользователя
            
        Yields:
            Токены ответа по одному
        """
        if not self.is_loaded():
            logger.error("Model not loaded, cannot generate")
            yield "[ERROR: Model not loaded]"
            return
        
        with self._generation_lock:
            try:
                self._stop_flag.clear()
                
                prompt = self._build_prompt(question)
                token_count = len(self.model.tokenize(prompt.encode('utf-8')))
                
                logger.info(f"Generating response for question (prompt tokens: {token_count})")
                logger.debug(f"Prompt: {prompt[:200]}...")
                
                if token_count > self.model_config.n_ctx - self.gen_params.max_tokens:
                    logger.error(f"Context overflow: {token_count} > {self.model_config.n_ctx}")
                    yield "[ERROR: Context too long. Please clear history]"
                    return
                
                start_time = time.time()
                first_token_time = None
                tokens_generated = 0
                full_response = ""
                
                for output in self.model(
                    prompt,
                    max_tokens=self.gen_params.max_tokens,
                    temperature=self.gen_params.temperature,
                    top_p=self.gen_params.top_p,
                    top_k=self.gen_params.top_k,
                    repeat_penalty=self.gen_params.repeat_penalty,
                    stop=self.gen_params.stop,
                    stream=True,
                    echo=False
                ):
                    if self._stop_flag.is_set():
                        logger.info("Generation stopped by user")
                        break
                    
                    if first_token_time is None:
                        first_token_time = time.time() - start_time
                    
                    token = output['choices'][0]['text']
                    full_response += token
                    tokens_generated += 1
                    
                    yield token
                
                total_time = time.time() - start_time
                self.last_stats = PerformanceStats(
                    tokens_per_second=tokens_generated / total_time if total_time > 0 else 0,
                    time_to_first_token=first_token_time or 0,
                    total_generation_time=total_time,
                    ram_usage_mb=psutil.Process().memory_info().rss / (1024 * 1024),
                    total_tokens=tokens_generated
                )
                
                logger.info(f"Generation completed: {tokens_generated} tokens in {total_time:.2f}s "
                           f"({self.last_stats.tokens_per_second:.2f} t/s)")
                
                self.add_to_context("user", question)
                self.add_to_context("assistant", full_response.strip())
                
            except Exception as e:
                logger.error(f"Generation error: {e}", exc_info=True)
                yield f"[ERROR: {str(e)}]"
    
    def stop_generation(self):
        """Остановить текущую генерацию"""
        logger.info("Stop generation requested")
        self._stop_flag.set()
    
    def get_performance_stats(self) -> PerformanceStats:
        """Получить статистику последней генерации"""
        return self.last_stats
