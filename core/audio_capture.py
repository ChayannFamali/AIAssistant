"""
Audio Capture - захват системного или микрофонного аудио
Fixed: Adaptive sample rate with resampling
"""
import logging
import numpy as np
from typing import Optional, Callable
import sounddevice as sd
from collections import deque
import scipy.signal

from core.config import AudioConfig

logger = logging.getLogger("AIAssistant.Audio")


class AudioCapture:
    """
    Захват аудио с устройства (WASAPI loopback или микрофон)
    Поддерживает автоматическую адаптацию sample rate
    """
    
    def __init__(self, callback: Optional[Callable] = None):
        """
        Args:
            callback: Функция для обработки аудио чанков
                     Сигнатура: callback(audio_data: np.ndarray)
        """
        self.callback = callback
        self.stream: Optional[sd.InputStream] = None
        self.is_capturing = False
        
        self.audio_buffer = deque(maxlen=AudioConfig.MAX_BUFFER_SIZE)
        
        self.device_index: Optional[int] = None
        self.device_sample_rate: int = AudioConfig.SAMPLE_RATE  
        self.target_sample_rate: int = AudioConfig.SAMPLE_RATE
        
        logger.info("AudioCapture initialized")
    
    def list_devices(self):
        """Вывести список доступных аудио устройств"""
        devices = sd.query_devices()
        logger.info("Available audio devices:")
        for i, device in enumerate(devices):
            logger.info(f"  [{i}] {device['name']} - "
                       f"In: {device['max_input_channels']}, "
                       f"Out: {device['max_output_channels']}, "
                       f"SR: {device['default_samplerate']}")
        return devices
    
    def find_loopback_device(self) -> Optional[int]:
        """
        Найти WASAPI loopback устройство (Windows)
        
        Returns:
            Index устройства или None
        """
        devices = sd.query_devices()
        
        for i, device in enumerate(devices):
            # WASAPI loopback обычно содержит "Stereo Mix" или имеет hostapi = WASAPI
            # Или максимальные input каналы при наличии output
            if device['max_input_channels'] > 0:
                # Для Windows: проверяем hostapi
                hostapi = sd.query_hostapis(device['hostapi'])
                if 'WASAPI' in hostapi['name']:
                    # Loopback обычно имеет название типа "Stereo Mix" или основное устройство
                    if 'stereo mix' in device['name'].lower() or device['default_samplerate'] >= 44100:
                        logger.info(f"Found potential loopback device: [{i}] {device['name']}")
                        return i
        
        logger.warning("No WASAPI loopback device found, using default input")
        return None
    
    def get_default_device(self) -> int:
        """Получить дефолтное устройство ввода"""
        return sd.default.device[0]
    
    def get_device_sample_rate(self, device_index: Optional[int]) -> int:
        """
        Получить нативный sample rate устройства
        
        Args:
            device_index: Index устройства
            
        Returns:
            Sample rate (Hz)
        """
        try:
            device_info = sd.query_devices(device_index, 'input')
            native_sr = int(device_info['default_samplerate'])
            logger.info(f"Device native sample rate: {native_sr} Hz")
            return native_sr
        except Exception as e:
            logger.warning(f"Failed to get device sample rate: {e}, using default")
            return 44100 
    
    def start_capture(self, use_loopback: bool = True):
        """
        Начать захват аудио
        
        Args:
            use_loopback: True = системный аудио, False = микрофон
        """
        if self.is_capturing:
            logger.warning("Already capturing")
            return
        
        try:
            if use_loopback:
                self.device_index = self.find_loopback_device()
            else:
                self.device_index = self.get_default_device()
            
            self.device_sample_rate = self.get_device_sample_rate(self.device_index)
            
            logger.info(f"Starting audio capture on device: {self.device_index}")
            logger.info(f"Device SR: {self.device_sample_rate} Hz, Target SR: {self.target_sample_rate} Hz")
            
            device_chunk_size = int(self.device_sample_rate * AudioConfig.CHUNK_DURATION)
            
            self.stream = sd.InputStream(
                device=self.device_index,
                channels=AudioConfig.CHANNELS,
                samplerate=self.device_sample_rate,
                dtype=AudioConfig.DTYPE,
                blocksize=device_chunk_size,
                callback=self._audio_callback
            )
            
            self.stream.start()
            self.is_capturing = True
            
            logger.info(f"Audio capture started: {self.device_sample_rate}Hz, "
                       f"{AudioConfig.CHANNELS}ch, {AudioConfig.DTYPE}")
        
        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}", exc_info=True)
            raise
    
    def stop_capture(self):
        """Остановить захват аудио"""
        if not self.is_capturing:
            return
        
        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
            
            self.is_capturing = False
            logger.info("Audio capture stopped")
        
        except Exception as e:
            logger.error(f"Error stopping capture: {e}")
    
    def _audio_callback(self, indata, frames, time_info, status):
        """
        Callback для sounddevice stream
        Вызывается автоматически когда доступны новые аудио данные
        """
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        audio_data = indata.copy().flatten()
        
        if self.device_sample_rate != self.target_sample_rate:
            audio_data = self._resample(audio_data, self.device_sample_rate, self.target_sample_rate)
        
        self.audio_buffer.extend(audio_data)
        
        if self.callback:
            try:
                self.callback(audio_data)
            except Exception as e:
                logger.error(f"Error in audio callback: {e}")
    
    def _resample(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """
        Ресемплировать аудио
        
        Args:
            audio: Исходное аудио
            orig_sr: Исходная частота
            target_sr: Целевая частота
            
        Returns:
            Ресемплированное аудио
        """
        if orig_sr == target_sr:
            return audio
        
        num_samples = int(len(audio) * target_sr / orig_sr)
        
        resampled = scipy.signal.resample(audio, num_samples)
        
        return resampled.astype(audio.dtype)
    
    def get_buffer_audio(self, duration_sec: float) -> np.ndarray:
        """
        Получить последние N секунд из буфера
        
        Args:
            duration_sec: Длительность в секундах
            
        Returns:
            Numpy array с аудио данными
        """
        num_samples = int(self.target_sample_rate * duration_sec)
        num_samples = min(num_samples, len(self.audio_buffer))
        
        # Взять последние N сэмплов
        audio = np.array(list(self.audio_buffer)[-num_samples:])
        
        return audio
    
    def clear_buffer(self):
        """Очистить буфер"""
        self.audio_buffer.clear()
        logger.debug("Audio buffer cleared")
