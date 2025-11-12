"""
Transcriber - Speech-to-Text используя OpenAI Whisper
Fixed: torch imported before PyQt6 to avoid DLL issues
"""
import logging
import numpy as np
from typing import Optional

import torch
import whisper

from core.config import STTConfig, AudioConfig

logger = logging.getLogger("AIAssistant.STT")


class Transcriber:
    """
    Speech-to-Text транскрибер на базе OpenAI Whisper
    """
    
    def __init__(self):
        self.model: Optional[whisper.Whisper] = None
        self.is_loaded = False
        
        logger.info("Transcriber initialized (OpenAI Whisper)")
    
    def load_model(self, model_size: str = STTConfig.MODEL_SIZE) -> bool:
        """
        Загрузить модель Whisper
        
        Args:
            model_size: Размер модели (tiny, base, small, medium, large)
            
        Returns:
            True если успешно
        """
        try:
            logger.info(f"Loading Whisper model: {model_size}")
            
            self.model = whisper.load_model(model_size)
            
            self.is_loaded = True
            logger.info(f"Whisper model loaded: {model_size}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}", exc_info=True)
            self.is_loaded = False
            return False
    
    def transcribe(self, audio_data: np.ndarray, 
                   language: Optional[str] = STTConfig.LANGUAGE) -> str:
        """
        Транскрибировать аудио в текст
        
        Args:
            audio_data: Numpy array с аудио (float32, -1.0 to 1.0)
            language: Код языка ("ru", "en", None=auto)
            
        Returns:
            Транскрибированный текст
        """
        if not self.is_loaded:
            logger.error("Model not loaded")
            return ""
        
        try:
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            

            min_samples = int(AudioConfig.SAMPLE_RATE * 0.1)
            if len(audio_data) < min_samples:
                logger.warning(f"Audio too short: {len(audio_data)} samples")
                return ""
            
            result = self.model.transcribe(
                audio_data,
                language=language,
                task=STTConfig.TASK,
                temperature=STTConfig.TEMPERATURE,
                fp16=False, 
                verbose=False  
            )
            
            full_text = result['text'].strip()
            detected_lang = result.get('language', 'unknown')
            
            if full_text:
                logger.info(f"Transcribed: '{full_text}' (lang: {detected_lang})")
            
            return full_text
        
        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            return ""
    
    def unload_model(self):
        """Выгрузить модель"""
        if self.model:
            del self.model
            self.model = None
            self.is_loaded = False
            logger.info("Whisper model unloaded")
