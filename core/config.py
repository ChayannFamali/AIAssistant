"""
Конфигурация приложения
"""
from dataclasses import dataclass
from typing import List
import os
import psutil
from pathlib import Path


@dataclass
class ModelConfig:
    """Конфигурация LLM модели"""
    n_ctx: int = 4096 
    n_threads: int = None 
    n_batch: int = 512
    n_gpu_layers: int = 0 
    use_mlock: bool = True
    use_mmap: bool = True 
    verbose: bool = False
    
    def __post_init__(self):
        if self.n_threads is None:
            self.n_threads = max(1, psutil.cpu_count(logical=False) - 2)


@dataclass
class GenerationParams:
    """Параметры генерации текста"""
    temperature: float = 0.4  
    top_p: float = 0.85
    top_k: int = 40
    max_tokens: int = 150 
    repeat_penalty: float = 1.1
    stop: List[str] = None
    stream: bool = True
    
    def __post_init__(self):
        if self.stop is None:
            self.stop = ["\n\nQuestion:", "\n\nUser:", "<|im_end|>"]


@dataclass
class PerformanceStats:
    """Метрики производительности"""
    tokens_per_second: float = 0.0
    time_to_first_token: float = 0.0
    total_generation_time: float = 0.0
    ram_usage_mb: float = 0.0
    total_tokens: int = 0


class AppConfig:
    """Глобальные настройки приложения"""
    APP_NAME = "AI Assistant"
    APP_VERSION = "1.0.0"
    COMPANY_NAME = "YourCompany"
    
    HF_REPO_ID = "Qwen/Qwen2.5-3B-Instruct-GGUF"
    HF_FILENAME = "qwen2.5-3b-instruct-q4_k_m.gguf"
    HF_MODEL_SIZE_MB = 2200 
    
    @staticmethod
    def get_models_dir() -> str:
        """Получить путь к папке с моделями"""
        app_data = os.getenv('LOCALAPPDATA') 
        models_dir = os.path.join(app_data, AppConfig.APP_NAME, 'models')
        os.makedirs(models_dir, exist_ok=True)
        return models_dir
    
    @staticmethod
    def get_default_model_path() -> str:
        """Путь к модели по умолчанию"""
        return os.path.join(
            AppConfig.get_models_dir(),
            AppConfig.HF_FILENAME
        )
    
    WINDOW_MIN_WIDTH = 400
    WINDOW_MIN_HEIGHT = 300
    WINDOW_DEFAULT_WIDTH = 600
    WINDOW_DEFAULT_HEIGHT = 400
    WINDOW_OPACITY = 0.95
    
    MAX_CONTEXT_MESSAGES = 10
    
    SYSTEM_PROMPT = """You are a helpful AI assistant for business meetings.
Provide brief, accurate, and professional answers to questions.
Keep responses under 100 words unless more detail is explicitly requested.
Answer in the same language as the question."""



class UITheme:
    """Темы оформления"""
    DARK = "dark"
    LIGHT = "light"
    CUSTOM = "custom"


class HistoryConfig:
    """Настройки истории диалогов"""
    HISTORY_DIR = Path.home() / '.aiassistant' / 'history'
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    
    MAX_HISTORY_FILES = 100 
    AUTO_SAVE = True
    SAVE_INTERVAL_SEC = 60 


class PerformanceConfig:
    """Настройки мониторинга производительности"""
    TRACK_HISTORY = True
    MAX_HISTORY_POINTS = 100 
    SHOW_CHART = True



class AudioConfig:
    """Конфигурация аудио захвата"""
    
    SAMPLE_RATE = 16000  
    CHANNELS = 1 
    DTYPE = 'int16'
    CHUNK_DURATION = 1.0 
    CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
    
    BUFFER_DURATION = 30.0
    MAX_BUFFER_SIZE = int(SAMPLE_RATE * BUFFER_DURATION)
    
    VAD_MODE = 3  
    VAD_FRAME_DURATION = 30  
    SPEECH_THRESHOLD = 0.5  
    
    USE_LOOPBACK = True
    
    @staticmethod
    def get_chunk_samples() -> int:
        """Получить количество сэмплов в чанке"""
        return AudioConfig.CHUNK_SIZE
    
    @staticmethod
    def get_vad_frame_size() -> int:
        """Размер фрейма для VAD в сэмплах"""
        return int(AudioConfig.SAMPLE_RATE * AudioConfig.VAD_FRAME_DURATION / 1000)


class STTConfig:
    """Конфигурация Speech-to-Text"""
    
    MODEL_SIZE = "base"  
    DEVICE = "cpu"
    COMPUTE_TYPE = "int8" 
    
    LANGUAGE = None  
    TASK = "transcribe" 
    BEAM_SIZE = 5
    BEST_OF = 5
    TEMPERATURE = 0.0
    
    VAD_FILTER = True  
    VAD_PARAMETERS = {
        "threshold": 0.5,
        "min_speech_duration_ms": 250,
        "max_speech_duration_s": 30,
        "min_silence_duration_ms": 500,
        "speech_pad_ms": 400
    }
    
    NUM_WORKERS = 1 
    
    @staticmethod
    def get_model_cache_dir():
        """Путь к кэшу моделей Whisper"""
        from pathlib import Path
        cache_dir = Path.home() / '.cache' / 'whisper'
        cache_dir.mkdir(parents=True, exist_ok=True)
        return str(cache_dir)


class QuestionDetectionConfig:
    """Конфигурация определения вопросов"""
    
    QUESTION_KEYWORDS_RU = [
        "как", "что", "где", "когда", "почему", "зачем",
        "какой", "какая", "какое", "какие",
        "кто", "чей", "чья", "чьё", "чьи",
        "сколько", "можно", "нужно", "должен",
        "расскажи", "объясни", "покажи"
    ]
    
    QUESTION_KEYWORDS_EN = [
        "how", "what", "where", "when", "why",
        "which", "who", "whose", "whom",
        "can", "could", "should", "would", "will",
        "is", "are", "am", "was", "were",
        "do", "does", "did", "have", "has", "had",
        "tell", "explain", "show", "describe"
    ]
    
    # Минимальная длина вопроса (слов)
    MIN_QUESTION_LENGTH = 3
    
    CONFIDENCE_THRESHOLD = 0.7
    
    # Таймаут после последнего вопроса (не генерировать повторно)
    QUESTION_COOLDOWN_SEC = 5.0


class PipelineConfig:
    """Конфигурация audio-to-answer pipeline"""
    
    MODE_MANUAL = "manual"  
    MODE_LISTENING = "listening" 
    MODE_AUTO = "auto"  
    
    DEFAULT_MODE = MODE_MANUAL
    
    MAX_QUEUE_SIZE = 5  
    
    DUPLICATE_THRESHOLD_SEC = 3.0  
    SIMILARITY_THRESHOLD = 0.85  
