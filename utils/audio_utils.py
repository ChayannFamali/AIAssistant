"""
Audio Utils - вспомогательные функции для работы с аудио
"""
import numpy as np
import logging

logger = logging.getLogger("AIAssistant.AudioUtils")


def normalize_audio(audio_data: np.ndarray) -> np.ndarray:
    """
    Нормализовать громкость аудио
    
    Args:
        audio_data: Numpy array с аудио
        
    Returns:
        Нормализованное аудио
    """
    if len(audio_data) == 0:
        return audio_data
    
    # Найти пиковую амплитуду
    max_amplitude = np.abs(audio_data).max()
    
    if max_amplitude == 0:
        return audio_data
    
    # Нормализовать к диапазону [-1.0, 1.0]
    if audio_data.dtype == np.int16:
        normalized = audio_data.astype(np.float32) / 32768.0
    else:
        normalized = audio_data / max_amplitude
    
    return normalized


def calculate_rms(audio_data: np.ndarray) -> float:
    """
    Вычислить RMS (Root Mean Square) - средняя громкость
    
    Args:
        audio_data: Numpy array с аудио
        
    Returns:
        RMS значение
    """
    if len(audio_data) == 0:
        return 0.0
    
    # Конвертировать в float
    if audio_data.dtype == np.int16:
        audio_data = audio_data.astype(np.float32) / 32768.0
    
    rms = np.sqrt(np.mean(np.square(audio_data)))
    return float(rms)


def is_silence(audio_data: np.ndarray, threshold: float = 0.01) -> bool:
    """
    Определить является ли аудио тишиной
    
    Args:
        audio_data: Numpy array с аудио
        threshold: Порог RMS для тишины
        
    Returns:
        True если тишина
    """
    rms = calculate_rms(audio_data)
    return rms < threshold


def resample_audio(audio_data: np.ndarray, orig_rate: int, target_rate: int) -> np.ndarray:
    """
    Ресемплировать аудио (изменить sample rate)
    Простая линейная интерполяция
    
    Args:
        audio_data: Numpy array с аудио
        orig_rate: Исходная частота
        target_rate: Целевая частота
        
    Returns:
        Ресемплированное аудио
    """
    if orig_rate == target_rate:
        return audio_data
    
    # Вычислить длину нового массива
    duration = len(audio_data) / orig_rate
    target_length = int(duration * target_rate)
    
    # Интерполяция
    indices = np.linspace(0, len(audio_data) - 1, target_length)
    resampled = np.interp(indices, np.arange(len(audio_data)), audio_data)
    
    return resampled.astype(audio_data.dtype)


def trim_silence(audio_data: np.ndarray, threshold: float = 0.01, 
                 frame_length: int = 2048) -> np.ndarray:
    """
    Обрезать тишину в начале и конце аудио
    
    Args:
        audio_data: Numpy array с аудио
        threshold: Порог RMS для тишины
        frame_length: Длина фрейма для анализа
        
    Returns:
        Обрезанное аудио
    """
    if len(audio_data) < frame_length:
        return audio_data
    
    # Найти начало речи
    start_idx = 0
    for i in range(0, len(audio_data) - frame_length, frame_length):
        frame = audio_data[i:i + frame_length]
        if not is_silence(frame, threshold):
            start_idx = i
            break
    
    # Найти конец речи
    end_idx = len(audio_data)
    for i in range(len(audio_data) - frame_length, 0, -frame_length):
        frame = audio_data[i:i + frame_length]
        if not is_silence(frame, threshold):
            end_idx = i + frame_length
            break
    
    return audio_data[start_idx:end_idx]


def merge_audio_chunks(chunks: list) -> np.ndarray:
    """
    Объединить несколько аудио чанков в один массив
    
    Args:
        chunks: Список numpy arrays
        
    Returns:
        Объединенный numpy array
    """
    if not chunks:
        return np.array([], dtype=np.float32)
    
    return np.concatenate(chunks)
