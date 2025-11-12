"""
Audio Thread - поток для захвата аудио
"""
import logging
import time
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from core.audio_capture import AudioCapture
from core.vad_detector import VADDetector
from core.config import AudioConfig
from utils.audio_utils import calculate_rms, is_silence

logger = logging.getLogger("AIAssistant.AudioThread")


class AudioWorker(QThread):
    """
    Worker thread для захвата аудио
    Работает непрерывно, детектирует речь и эмитит чанки для STT
    """
    
    audio_ready = pyqtSignal(np.ndarray) 
    speech_started = pyqtSignal()  
    speech_ended = pyqtSignal()  
    volume_level = pyqtSignal(float)  
    error_occurred = pyqtSignal(str) 
    
    def __init__(self):
        super().__init__()
        
        self.audio_capture: AudioCapture = None
        self.vad_detector = VADDetector()
        
        self.is_running = False
        self.is_listening = False  
        
        self.speech_buffer = []
        self.in_speech = False
        self.silence_frames = 0
        self.max_silence_frames = 10
        
        logger.info("AudioWorker initialized")
    
    def run(self):
        """Основной цикл (запускается автоматически при start())"""
        logger.info("AudioWorker thread started")
        
        try:
            self.audio_capture = AudioCapture(callback=self._on_audio_chunk)
            
            while self.is_running:
                time.sleep(0.1)
        
        except Exception as e:
            logger.error(f"AudioWorker error: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
        
        finally:
            if self.audio_capture:
                self.audio_capture.stop_capture()
        
        logger.info("AudioWorker thread stopped")
    
    def start_listening(self, use_loopback: bool = True):
        """
        Начать прослушивание
        
        Args:
            use_loopback: True = системный аудио, False = микрофон
        """
        if self.is_listening:
            logger.warning("Already listening")
            return
        
        try:
            logger.info(f"Starting audio listening (loopback={use_loopback})")
            
            self.is_running = True
            
            if not self.audio_capture:
                self.audio_capture = AudioCapture(callback=self._on_audio_chunk)
            
            self.audio_capture.start_capture(use_loopback=use_loopback)
            self.is_listening = True
            
            logger.info("Audio listening started")
        
        except Exception as e:
            logger.error(f"Failed to start listening: {e}", exc_info=True)
            self.error_occurred.emit(f"Failed to start audio: {str(e)}")
    
    def stop_listening(self):
        """Остановить прослушивание"""
        if not self.is_listening:
            return
        
        logger.info("Stopping audio listening")
        
        if self.audio_capture:
            self.audio_capture.stop_capture()
        
        self.is_listening = False
        self.speech_buffer.clear()
        self.in_speech = False
        
        logger.info("Audio listening stopped")
    
    def _on_audio_chunk(self, audio_data: np.ndarray):
        """
        Callback для обработки аудио чанков
        Вызывается из audio_capture автоматически
        """
        if not self.is_listening:
            return
        
        try:
            rms = calculate_rms(audio_data)
            self.volume_level.emit(rms)
            
            has_speech = self.vad_detector.has_speech_activity(audio_data)
            
            if has_speech:
                if not self.in_speech:
                    logger.debug("Speech started")
                    self.in_speech = True
                    self.speech_started.emit()
                
                self.speech_buffer.append(audio_data)
                self.silence_frames = 0
            
            else:
                if self.in_speech:
                    self.speech_buffer.append(audio_data)
                    self.silence_frames += 1
                    
                    if self.silence_frames >= self.max_silence_frames:
                        logger.debug("Speech ended")
                        self._process_speech_buffer()
                        
                        self.in_speech = False
                        self.speech_buffer.clear()
                        self.silence_frames = 0
                        
                        self.speech_ended.emit()
        
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}", exc_info=True)
    
    def _process_speech_buffer(self):
        """Обработать накопленный буфер речи"""
        if not self.speech_buffer:
            return
        
        full_audio = np.concatenate(self.speech_buffer)
        
        min_duration = 0.5
        min_samples = int(AudioConfig.SAMPLE_RATE * min_duration)
        
        if len(full_audio) < min_samples:
            logger.debug("Speech too short, ignoring")
            return
        
        logger.info(f"Processing speech buffer: {len(full_audio)} samples "
                   f"({len(full_audio) / AudioConfig.SAMPLE_RATE:.2f}s)")
        
        self.audio_ready.emit(full_audio)
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down AudioWorker")
        
        self.stop_listening()
        self.is_running = False
        
        self.quit()
        if not self.wait(5000):
            logger.warning("AudioWorker did not stop gracefully, terminating")
            self.terminate()
            self.wait()
