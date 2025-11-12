"""
Question Detector - определение вопросов в транскрибированном тексте
"""
import logging
import re
from typing import Optional, List
from difflib import SequenceMatcher

from core.config import QuestionDetectionConfig

logger = logging.getLogger("AIAssistant.QuestionDetector")


class QuestionDetector:
    """
    Детектор вопросов в тексте
    Использует эвристики: знаки вопроса, ключевые слова, структура предложения
    """
    
    def __init__(self):
        self.ru_keywords = QuestionDetectionConfig.QUESTION_KEYWORDS_RU
        self.en_keywords = QuestionDetectionConfig.QUESTION_KEYWORDS_EN
        self.min_length = QuestionDetectionConfig.MIN_QUESTION_LENGTH
        
        # Кэш последних вопросов для дедупликации
        self.recent_questions: List[tuple] = []  # (text, timestamp)
        self.cooldown_sec = QuestionDetectionConfig.QUESTION_COOLDOWN_SEC
        
        logger.info("QuestionDetector initialized")
    
    def is_question(self, text: str, language: Optional[str] = None) -> bool:
        """
        Определить является ли текст вопросом
        
        Args:
            text: Текст для анализа
            language: Язык текста ("ru", "en", None=auto)
            
        Returns:
            True если текст является вопросом
        """
        if not text or len(text.strip()) == 0:
            return False
        
        text = text.strip()
        
        if text.endswith('?'):
            logger.debug(f"Question detected (? mark): {text}")
            return True
        
        words = text.split()
        if len(words) < self.min_length:
            return False
        
        if language is None:
            language = self._detect_language(text)
        
        # Проверка ключевых слов
        keywords = self.en_keywords if language == 'en' else self.ru_keywords
        
        # Первое слово
        first_word = words[0].lower().strip('.,!?')
        if first_word in keywords:
            logger.debug(f"Question detected (keyword '{first_word}'): {text}")
            return True
        
        for word in words[:3]:
            word_clean = word.lower().strip('.,!?')
            if word_clean in keywords:
                logger.debug(f"Question detected (keyword '{word_clean}'): {text}")
                return True
        
        # Паттерны вопросов
        if language == 'ru':
            patterns = [
                r'^(как|что|где|когда|почему|зачем|кто|какой|сколько)\s+',
                r'\s+(можно|нужно|должен|стоит)\s+',
            ]
        else:
            patterns = [
                r'^(how|what|where|when|why|who|which)\s+',
                r'^(can|could|should|would|will|is|are|do|does|did)\s+',
                r'\s+(please|tell|explain|show)\s+',
            ]
        
        for pattern in patterns:
            if re.search(pattern, text.lower()):
                logger.debug(f"Question detected (pattern): {text}")
                return True
        
        return False
    
    def extract_questions(self, text: str, language: Optional[str] = None) -> List[str]:
        """
        Извлечь все вопросы из текста (может быть несколько предложений)
        
        Args:
            text: Текст для анализа
            language: Язык текста
            
        Returns:
            Список вопросов
        """
        # Разбить на предложения
        sentences = self._split_sentences(text)
        
        questions = []
        for sentence in sentences:
            if self.is_question(sentence, language):
                questions.append(sentence.strip())
        
        return questions
    
    def should_process_question(self, question: str, current_time: float) -> bool:
        """
        Проверить нужно ли обрабатывать вопрос (дедупликация)
        
        Args:
            question: Текст вопроса
            current_time: Текущее время (timestamp)
            
        Returns:
            True если вопрос новый и не дубликат
        """
        # Очистить старые вопросы (за пределами cooldown)
        self.recent_questions = [
            (q, t) for q, t in self.recent_questions
            if current_time - t < self.cooldown_sec
        ]
        
        # Проверить на дубликаты
        for recent_q, recent_t in self.recent_questions:
            similarity = self._text_similarity(question, recent_q)
            
            if similarity > QuestionDetectionConfig.SIMILARITY_THRESHOLD:
                logger.debug(f"Duplicate question detected: {question} "
                           f"(similar to: {recent_q}, sim={similarity:.2f})")
                return False
        
        # Добавить в кэш
        self.recent_questions.append((question, current_time))
        
        return True
    
    def _detect_language(self, text: str) -> str:
        """
        Простое определение языка по характерным символам
        
        Args:
            text: Текст
            
        Returns:
            "ru" или "en"
        """
        # Подсчитать русские буквы
        ru_chars = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
        
        # Если больше 20% русских символов - русский
        if ru_chars / len(text) > 0.2:
            return 'ru'
        
        return 'en'
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        Разбить текст на предложения
        
        Args:
            text: Текст
            
        Returns:
            Список предложений
        """
        # Простое разбиение по пунктуации
        sentences = re.split(r'[.!?]+', text)
        
        # Очистить
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        Вычислить схожесть двух текстов (0.0 - 1.0)
        Использует SequenceMatcher (похож на Levenshtein distance)
        
        Args:
            text1: Первый текст
            text2: Второй текст
            
        Returns:
            Коэффициент схожести
        """
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
