"""
Statistics Manager - расширенная статистика использования
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from collections import Counter, defaultdict
import json
from pathlib import Path

logger = logging.getLogger("AIAssistant.Statistics")


class StatisticsManager:
    """
    Менеджер статистики использования приложения
    """
    
    def __init__(self, stats_file: str = None):
        if stats_file is None:
            stats_dir = Path.home() / '.aiassistant' / 'stats'
            stats_dir.mkdir(parents=True, exist_ok=True)
            stats_file = str(stats_dir / 'statistics.json')
        
        self.stats_file = stats_file
        self.stats_data = self.load_stats()
        
        logger.info(f"StatisticsManager initialized: {stats_file}")
    
    def load_stats(self) -> Dict:
        """Загрузить статистику из файла"""
        try:
            if Path(self.stats_file).exists():
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._create_empty_stats()
        except Exception as e:
            logger.error(f"Failed to load statistics: {e}")
            return self._create_empty_stats()
    
    def _create_empty_stats(self) -> Dict:
        """Создать пустую структуру статистики"""
        return {
            "questions": [],  # List[{"date": "2025-01-05", "question": "...", "tokens": 100, "time": 5.2}]
            "daily_stats": {},  # {"2025-01-05": {"questions": 10, "tokens": 1500, "avg_time": 5.3}}
            "top_questions": [],  # List[{"question": "...", "count": 5}]
            "total_questions": 0,
            "total_tokens": 0,
            "total_time": 0.0,
            "first_use_date": datetime.now().isoformat(),
            "last_use_date": datetime.now().isoformat(),
        }
    
    def save_stats(self):
        """Сохранить статистику в файл"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats_data, f, indent=2, ensure_ascii=False)
            logger.debug("Statistics saved")
        except Exception as e:
            logger.error(f"Failed to save statistics: {e}")
    
    def record_question(self, question: str, tokens: int, time_sec: float):
        """
        Записать вопрос в статистику
        
        Args:
            question: Текст вопроса
            tokens: Количество токенов в ответе
            time_sec: Время генерации в секундах
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        self.stats_data["questions"].append({
            "date": date_str,
            "question": question,
            "tokens": tokens,
            "time": time_sec,
            "timestamp": datetime.now().isoformat()
        })
        
        if date_str not in self.stats_data["daily_stats"]:
            self.stats_data["daily_stats"][date_str] = {
                "questions": 0,
                "tokens": 0,
                "total_time": 0.0
            }
        
        daily = self.stats_data["daily_stats"][date_str]
        daily["questions"] += 1
        daily["tokens"] += tokens
        daily["total_time"] += time_sec
        daily["avg_time"] = daily["total_time"] / daily["questions"]
        
        self.stats_data["total_questions"] += 1
        self.stats_data["total_tokens"] += tokens
        self.stats_data["total_time"] += time_sec
        self.stats_data["last_use_date"] = datetime.now().isoformat()
        
        self.save_stats()
        
        logger.debug(f"Question recorded: {question[:50]}...")
    
    def get_stats_by_period(self, days: int) -> List[Dict]:
        """
        Получить статистику за последние N дней
        
        Args:
            days: Количество дней (7, 30, 90)
            
        Returns:
            List[{"date": "2025-01-05", "questions": 10, "tokens": 1500, "avg_time": 5.3}]
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        result = []
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            if date_str in self.stats_data["daily_stats"]:
                daily_data = self.stats_data["daily_stats"][date_str]
                result.append({
                    "date": date_str,
                    **daily_data
                })
            else:
                result.append({
                    "date": date_str,
                    "questions": 0,
                    "tokens": 0,
                    "total_time": 0.0,
                    "avg_time": 0.0
                })
            
            current_date += timedelta(days=1)
        
        return result
    
    def get_top_questions(self, limit: int = 10) -> List[Dict]:
        """
        Получить топ-N самых частых вопросов
        
        Args:
            limit: Количество вопросов
            
        Returns:
            List[{"question": "...", "count": 5, "avg_tokens": 120, "avg_time": 5.2}]
        """
        question_counter = Counter()
        question_stats = defaultdict(lambda: {"tokens": [], "times": []})
        
        for entry in self.stats_data["questions"]:
            q = entry["question"].strip().lower()
            question_counter[q] += 1
            question_stats[q]["tokens"].append(entry["tokens"])
            question_stats[q]["times"].append(entry["time"])
        
        # Топ-N
        top = []
        for question, count in question_counter.most_common(limit):
            stats = question_stats[question]
            avg_tokens = sum(stats["tokens"]) / len(stats["tokens"]) if stats["tokens"] else 0
            avg_time = sum(stats["times"]) / len(stats["times"]) if stats["times"] else 0
            
            top.append({
                "question": question.capitalize(),
                "count": count,
                "avg_tokens": int(avg_tokens),
                "avg_time": round(avg_time, 2)
            })
        
        return top
    
    def get_summary_stats(self) -> Dict:
        """
        Получить сводную статистику
        
        Returns:
            {"total_questions": 100, "total_tokens": 15000, ...}
        """
        total_q = self.stats_data["total_questions"]
        total_t = self.stats_data["total_tokens"]
        total_time = self.stats_data["total_time"]
        
        avg_tokens = int(total_t / total_q) if total_q > 0 else 0
        avg_time = round(total_time / total_q, 2) if total_q > 0 else 0
        
        first_use = datetime.fromisoformat(self.stats_data["first_use_date"])
        last_use = datetime.fromisoformat(self.stats_data["last_use_date"])
        days_used = (last_use - first_use).days + 1
        
        questions_per_day = round(total_q / days_used, 1) if days_used > 0 else 0
        
        return {
            "total_questions": total_q,
            "total_tokens": total_t,
            "total_time": round(total_time, 2),
            "avg_tokens_per_question": avg_tokens,
            "avg_time_per_question": avg_time,
            "days_used": days_used,
            "questions_per_day": questions_per_day,
            "first_use": first_use.strftime("%Y-%m-%d"),
            "last_use": last_use.strftime("%Y-%m-%d")
        }
    
    def export_to_csv(self, filepath: str):
        """
        Экспортировать статистику в CSV
        
        Args:
            filepath: Путь к файлу CSV
        """
        import csv
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                writer.writerow(["Date", "Question", "Tokens", "Time (sec)", "Timestamp"])
                
                for entry in self.stats_data["questions"]:
                    writer.writerow([
                        entry["date"],
                        entry["question"],
                        entry["tokens"],
                        entry["time"],
                        entry["timestamp"]
                    ])
            
            logger.info(f"Statistics exported to CSV: {filepath}")
        
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            raise
    
    def export_to_excel(self, filepath: str):
        """
        Экспортировать статистику в Excel
        
        Args:
            filepath: Путь к файлу Excel (.xlsx)
        """
        try:
            import pandas as pd
            
            df_questions = pd.DataFrame(self.stats_data["questions"])
            
            daily_data = []
            for date, stats in sorted(self.stats_data["daily_stats"].items()):
                daily_data.append({
                    "date": date,
                    **stats
                })
            df_daily = pd.DataFrame(daily_data)
            
            df_top = pd.DataFrame(self.get_top_questions(20))
            
            summary = self.get_summary_stats()
            df_summary = pd.DataFrame([summary])
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df_questions.to_excel(writer, sheet_name='All Questions', index=False)
                df_daily.to_excel(writer, sheet_name='Daily Stats', index=False)
                df_top.to_excel(writer, sheet_name='Top Questions', index=False)
                df_summary.to_excel(writer, sheet_name='Summary', index=False)
            
            logger.info(f"Statistics exported to Excel: {filepath}")
        
        except ImportError:
            logger.error("pandas and openpyxl required for Excel export. Install: pip install pandas openpyxl")
            raise
        
        except Exception as e:
            logger.error(f"Failed to export Excel: {e}")
            raise
