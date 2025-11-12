"""
VAD (Voice Activity Detection) - определение наличия речи в аудио
"""
import logging
import numpy as np
import webrtcvad
from typing import List

from core.config import AudioConfig

logger = logging.getLogger("AIAssistant.VAD")


class VADDetector:
    """
    Voice Activity Detection используя WebRTC VAD
    """
    
    def __init__(self, mode: int = AudioConfig.VAD_MODE):
        """
        Args:
            mode: Агрессивность VAD (0-3, где 3 = самый агрессивный)
        """
        self.vad = webrtcvad.Vad(mode)
        self.frame_duration = AudioConfig.VAD_FRAME_DURATION  # ms
        self.sample_rate = AudioConfig.SAMPLE_RATE
        self.frame_size = AudioConfig.get_vad_frame_size()
        
        logger.info(f"VAD initialized: mode={mode}, frame_duration={self.frame_duration}ms")
    
    def is_speech(self, audio_data: np.ndarray) -> bool:
        """
        Проверить содержит ли аудио речь
        
        Args:
            audio_data: Numpy array с аудио (int16)
            
        Returns:
            True если обнаружена речь
        """
        if audio_data.dtype != np.int16:
            audio_data = (audio_data * 32768).astype(np.int16)
        
        audio_bytes = audio_data.tobytes()
        
        expected_bytes = self.frame_size * 2 
        
        if len(audio_bytes) != expected_bytes:
            if len(audio_bytes) < expected_bytes:
                audio_bytes += b'\x00' * (expected_bytes - len(audio_bytes))
            else:
                audio_bytes = audio_bytes[:expected_bytes]
        
        try:
            return self.vad.is_speech(audio_bytes, self.sample_rate)
        except Exception as e:
            logger.error(f"VAD error: {e}")
            return False
    
    def detect_speech_segments(self, audio_data: np.ndarray, 
                               threshold: float = AudioConfig.SPEECH_THRESHOLD) -> List[tuple]:
        """
        Найти сегменты с речью в аудио
        
        Args:
            audio_data: Numpy array с аудио
            threshold: Процент фреймов с речью для активации сегмента
            
        Returns:
            List[(start_sample, end_sample)] с границами сегментов речи
        """
        num_frames = len(audio_data) // self.frame_size
        frames = []
        
        for i in range(num_frames):
            start = i * self.frame_size
            end = start + self.frame_size
            frame = audio_data[start:end]
            
            if len(frame) == self.frame_size:
                frames.append((start, end, self.is_speech(frame)))
        
        segments = []
        in_segment = False
        segment_start = 0
        speech_frames = 0
        total_frames = 0
        
        for start, end, is_speech in frames:
            total_frames += 1
            
            if is_speech:
                speech_frames += 1
                
                if not in_segment:
                    segment_start = start
                    in_segment = True
            else:
                if in_segment:
                    speech_ratio = speech_frames / total_frames if total_frames > 0 else 0
                    
                    if speech_ratio >= threshold:
                        segments.append((segment_start, end))
                    
                    in_segment = False
                    speech_frames = 0
                    total_frames = 0
        
        if in_segment:
            speech_ratio = speech_frames / total_frames if total_frames > 0 else 0
            if speech_ratio >= threshold:
                segments.append((segment_start, len(audio_data)))
        
        logger.debug(f"Detected {len(segments)} speech segments")
        return segments
    
    def has_speech_activity(self, audio_data: np.ndarray) -> bool:
        """
        Быстрая проверка: есть ли речь в аудио
        
        Args:
            audio_data: Numpy array с аудио
            
        Returns:
            True если обнаружена речь
        """
        num_frames = len(audio_data) // self.frame_size
        speech_count = 0
        
        for i in range(num_frames):
            start = i * self.frame_size
            end = start + self.frame_size
            frame = audio_data[start:end]
            
            if len(frame) == self.frame_size and self.is_speech(frame):
                speech_count += 1
        
        if num_frames == 0:
            return False
        
        speech_ratio = speech_count / num_frames
        return speech_ratio >= AudioConfig.SPEECH_THRESHOLD
