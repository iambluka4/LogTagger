import logging
import json
import os
import time
import requests
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from flask import current_app
from models import db, Event, Configuration

# Додаємо відсутній імпорт для MLPerformanceMetrics
from models.ml import MLPerformanceMetrics  # Припускаємо, що цей клас визначено в models/ml.py

# Імпорт ML провайдерів
# Якщо класи провайдерів ще не створені, їх треба буде реалізувати
from .ml_providers import MLProvider, APIMLProvider, LocalMLProvider, DummyMLProvider  

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLServiceCache:
    """Клас для кешування відповідей ML API"""
    
    def __init__(self, ttl_minutes=60):
        self.cache = {}
        self.ttl_minutes = ttl_minutes
    
    def get(self, key):
        """Отримати кешовані дані якщо вони дійсні"""
        if key not in self.cache:
            return None
            
        entry = self.cache[key]
        if datetime.now() > entry['expires']:
            del self.cache[key]
            return None
            
        return entry['data']
    
    def set(self, key, data):
        """Зберегти дані в кеш"""
        expires = datetime.now() + timedelta(minutes=self.ttl_minutes)
        self.cache[key] = {
            'data': data,
            'expires': expires
        }

class MLService:
    """Сервіс для ML-класифікації подій"""
    
    _instance = None  # Для реалізації патерну Singleton
    
    @classmethod
    def get_instance(cls, api_url=None, api_key=None):
        """
        Отримати єдиний екземпляр ML-сервісу (патерн Singleton)
        
        Args:
            api_url: URL до ML API (опціонально)
            api_key: Ключ доступу до ML API (опціонально)
            
        Returns:
            Екземпляр MLService
        """
        if cls._instance is None:
            cls._instance = MLService(api_url, api_key)
        elif api_url and api_key and (cls._instance.api_url != api_url or cls._instance.api_key != api_key):
            # Якщо змінилися параметри підключення, оновлюємо їх
            cls._instance.api_url = api_url
            cls._instance.api_key = api_key
            cls._instance._config_loaded = False  # Примусове перезавантаження конфігурації
            
        return cls._instance
    
    def __init__(self, api_url: str = None, api_key: str = None):
        """
        Ініціалізація ML-сервісу
        
        Args:
            api_url: URL до ML API (опціонально)
            api_key: Ключ доступу до ML API (опціонально)
        """
        self.api_url = api_url
        self.api_key = api_key
        self.provider = None
        self.config = {}
        self._config_loaded = False
        self.cache = MLServiceCache()
        # Відкладаємо завантаження конфігурації до першого використання
        # Це дозволяє уникнути залежності від Flask контексту при ініціалізації
    
    def _ensure_config_loaded(self):
        """Завантажує конфігурацію, якщо вона ще не завантажена"""
        if not self._config_loaded:
            self._load_config()
            self._initialize_provider()
            self._config_loaded = True
    
    def _load_config(self):
        """Завантажити конфігурацію з бази даних"""
        try:
            ml_configs = Configuration.query.filter(
                Configuration.config_type.like('ml.%')
            ).all()
            
            for config in ml_configs:
                key = config.config_type.split('.')[1]
                value = config.config_value
                
                # Конвертуємо значення у відповідні типи
                if key == 'min_confidence_threshold':
                    value = float(value)
                elif key in ['auto_apply_labels', 'verification_required']:
                    value = value.lower() == 'true'
                elif key == 'update_interval_days':
                    value = int(value)
                
                self.config[key] = value
            
            logger.info(f"Loaded ML configuration: {self.config}")
        except Exception as e:
            logger.error(f"Error loading ML configuration: {str(e)}")
            # Встановлюємо значення за замовчуванням
            self.config = {
                'min_confidence_threshold': 0.7,
                'auto_apply_labels': True,
                'model_type': 'local',
                'local_model_path': 'models/default_model.pkl',
                'verification_required': True,
                'update_interval_days': 7
            }
    
    def reload_config(self):
        """Перезавантажити конфігурацію"""
        self._config_loaded = False
        self._ensure_config_loaded()
        return True
    
    def _initialize_provider(self):
        """Ініціалізувати провайдера ML на основі конфігурації"""
        try:
            model_type = self.config.get('model_type', 'local')
            
            if model_type == 'api' and self.api_url and self.api_key:
                logger.info(f"Initializing API ML provider with URL: {self.api_url}")
                self.provider = APIMLProvider(self.api_url, self.api_key)
            elif model_type == 'local':
                model_path = self.config.get('local_model_path')
                logger.info(f"Initializing Local ML provider with model path: {model_path}")
                self.provider = LocalMLProvider(model_path)
            else:
                logger.info("Initializing Dummy ML provider for testing/demo")
                self.provider = DummyMLProvider()
                
            # Перевіряємо з'єднання
            connection_test = self.provider.test_connection()
            if connection_test.get('success'):
                logger.info(f"ML provider initialized successfully: {connection_test.get('message')}")
            else:
                logger.warning(f"ML provider initialization warning: {connection_test.get('message')}")
                
        except Exception as e:
            logger.error(f"Error initializing ML provider: {str(e)}")
            logger.info("Falling back to Dummy ML provider")
            self.provider = DummyMLProvider()
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Перевірити з'єднання з ML-провайдером
        
        Returns:
            Dictionary з результатами перевірки
        """
        self._ensure_config_loaded()
        
        if not self.provider:
            return {
                "success": False,
                "message": "ML provider not initialized",
                "details": {"error": "Provider is None"}
            }
        
        return self.provider.test_connection()
    
    def classify_event(self, event: Event) -> Dict[str, Any]:
        """
        Класифікувати подію
        
        Args:
            event: Об'єкт події
            
        Returns:
            Dictionary з результатами класифікації
        """
        self._ensure_config_loaded()
        
        if not self.provider:
            logger.error("ML provider not initialized")
            return {"success": False, "error": "ML provider not initialized"}
        
        try:
            # Перевірка, чи існує подія
            if not event:
                return {
                    "success": False,
                    "error": "Event not found",
                    "event_id": None
                }
                
            # Підготовка даних події
            event_data = self._prepare_event_data(event)
            
            # Класифікація
            result = self.provider.classify_event(event_data)
            
            if result.get("success"):
                # Оновлення події з результатами класифікації
                classification = result.get("classification", {})
                confidence = result.get("confidence", 0.0)
                
                # Застосовуємо результати, якщо впевненість вища за поріг
                min_threshold = self.config.get("min_confidence_threshold", 0.7)
                
                if confidence >= min_threshold and self.config.get("auto_apply_labels", True):
                    self._apply_classification(event, classification, confidence)
                    # Додаємо збереження змін до бази даних
                    db.session.commit()
                
                return {
                    "success": True,
                    "event_id": event.id,
                    "classification": classification,
                    "confidence": confidence,
                    "applied": confidence >= min_threshold
                }
            else:
                return {
                    "success": False,
                    "event_id": event.id,
                    "error": result.get("error", "Unknown error")
                }
        except Exception as e:
            logger.error(f"Error in classify_event: {str(e)}")
            return {
                "success": False,
                "event_id": getattr(event, 'id', None),
                "error": str(e)
            }
    
    def batch_classify_events(self, event_ids: List[int]) -> Dict[str, Any]:
        """
        Класифікувати множину подій
        
        Args:
            event_ids: Список ID подій для класифікації
            
        Returns:
            Dictionary з результатами класифікації
        """
        self._ensure_config_loaded()
        
        if not self.provider:
            return {"success": False, "error": "ML provider not initialized"}
        
        try:
            # Оптимізуємо запит, вибираючи лише потрібні поля для класифікації
            events = Event.query.options(
                db.load_only(
                    Event.id, Event.source_ip, Event.destination_ip, 
                    Event.event_type, Event.severity, Event.message
                )
            ).filter(Event.id.in_(event_ids)).all()
            
            if not events:
                return {
                    "success": False,
                    "error": "No events found with provided IDs"
                }
            
            # Підготовка даних для всіх подій
            event_data_list = [self._prepare_event_data(event) for event in events]
            
            # Пакетна класифікація
            start_time = time.time()
            results = self.provider.batch_classify(event_data_list)
            processing_time = time.time() - start_time
            
            # Застосовуємо результати до подій
            processed_events = []
            for event, result in zip(events, results):
                if result.get("success"):
                    classification = result.get("classification", {})
                    confidence = result.get("confidence", 0.0)
                    min_threshold = self.config.get("min_confidence_threshold", 0.7)
                    
                    if confidence >= min_threshold and self.config.get("auto_apply_labels", True):
                        self._apply_classification(event, classification, confidence)
                    
                    processed_events.append({
                        "event_id": event.id,
                        "success": True,
                        "confidence": confidence,
                        "applied": confidence >= min_threshold
                    })
                else:
                    processed_events.append({
                        "event_id": event.id,
                        "success": False,
                        "error": result.get("error", "Unknown error")
                    })
            
            # Зберігаємо зміни в базі даних
            db.session.commit()
            
            return {
                "success": True,
                "processed_events": len(processed_events),
                "processing_time_seconds": processing_time,
                "results": processed_events
            }
        except Exception as e:
            logger.error(f"Error in batch_classify_events: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def _prepare_event_data(self, event: Event) -> Dict[str, Any]:
        """
        Підготувати дані події для класифікації
        
        Args:
            event: Об'єкт події
            
        Returns:
            Dictionary з даними події для ML
        """
        event_data = event.to_dict()
        
        # Додаємо raw_log, якщо доступний
        if event.raw_logs:
            event_data["raw_log"] = event.raw_logs[0].raw_log if event.raw_logs else {}
        
        return event_data
    
    def _apply_classification(self, event: Event, classification: Dict[str, Any], confidence: float) -> None:
        """
        Застосувати результати класифікації до події
        
        Args:
            event: Об'єкт події
            classification: Результати класифікації
            confidence: Рівень впевненості
        """
        # Оновлюємо мітки події
        if "true_positive" in classification:
            event.true_positive = classification["true_positive"]
        
        if "attack_type" in classification:
            event.attack_type = classification["attack_type"]
        
        if "mitre_tactic" in classification:
            event.mitre_tactic = classification["mitre_tactic"]
        
        if "mitre_technique" in classification:
            event.mitre_technique = classification["mitre_technique"]
        
        # Додаємо мітки ML
        event.ml_processed = True
        event.ml_confidence = confidence
        
        # Зберігаємо timestamp як нативний datetime об'єкт
        event.ml_timestamp = datetime.utcnow()
        
        # Якщо потрібна верифікація
        event.human_verified = not self.config.get("verification_required", True)
    
    def update_performance_metrics(self, start_date=None, end_date=None) -> Dict[str, Any]:
        """
        Оновити метрики продуктивності ML на основі перевірених людиною подій
        
        Args:
            start_date: Початкова дата для аналізу (опціонально)
            end_date: Кінцева дата для аналізу (опціонально)
            
        Returns:
            Dictionary з результатами оновлення метрик
        """
        self._ensure_config_loaded()
        
        try:
            # Підготовка запиту
            query = Event.query.filter(
                Event.ml_processed == True, 
                Event.human_verified == True
            )
            
            if start_date:
                query = query.filter(Event.ml_timestamp >= start_date)
            if end_date:
                query = query.filter(Event.ml_timestamp <= end_date)
            
            # Рахуємо загальну кількість подій для метрик
            total_events = query.count()
            
            if not total_events:
                return {
                    "success": False,
                    "message": "No verified events found for metrics calculation"
                }
            
            # Отримуємо інформацію про модель
            model_info = {"model_info": {"version": "unknown"}}
            if self.provider:
                try:
                    model_info = self.provider.get_model_info()
                except Exception as e:
                    logger.warning(f"Could not get model info: {str(e)}")
                    
            model_version = model_info.get("model_info", {}).get("version", "unknown")
            
            # Створюємо новий запис метрик
            metrics = MLPerformanceMetrics(model_version=model_version)
            
            # Розрахунок базових метрик через пакетну обробку
            tp = fp = tn = fn = 0
            
            # Впроваджуємо пакетну обробку з пагінацією
            page_size = 500
            page = 0
            processed = 0
            
            while processed < total_events:
                # Завантажуємо підмножину подій
                batch_events = query.limit(page_size).offset(page * page_size).all()
                
                if not batch_events:
                    break
                    
                for event in batch_events:
                    # Безпечний доступ до атрибутів
                    if not hasattr(event, 'labels_data') or not event.labels_data:
                        processed += 1
                        continue

                    if "ml_true_positive" not in event.labels_data:
                        # Пропускаємо події без збережених ML-міток
                        processed += 1
                        continue
                        
                    ml_true_positive = event.labels_data.get("ml_true_positive", False)
                    
                    # True Positive: ML визначив як true_positive і людина підтвердила
                    if event.true_positive and ml_true_positive:
                        tp += 1
                    # False Positive: ML визначив як true_positive, але людина спростувала
                    elif not event.true_positive and ml_true_positive:
                        fp += 1
                    # True Negative: ML визначив як false_positive і людина підтвердила
                    elif not event.true_positive and not ml_true_positive:
                        tn += 1
                    # False Negative: ML визначив як false_positive, але людина спростувала
                    else:
                        fn += 1
                    
                    processed += 1
                
                # Переходимо до наступної сторінки
                page += 1
            
            metrics.true_positives = tp
            metrics.false_positives = fp
            metrics.true_negatives = tn
            metrics.false_negatives = fn
            
            # Запобігаємо діленню на нуль
            if tp + fp + tn + fn == 0:
                return {
                    "success": False,
                    "message": "No valid data found for metrics calculation"
                }
            
            # Розрахунок метрик
            metrics.calculate_metrics()
            
            # Додаємо метрики по класам (attack_type)
            class_metrics = {}
            attack_types = set()
            
            for event in query.all():
                if not hasattr(event, 'attack_type') or not event.attack_type:
                    continue
                attack_types.add(event.attack_type)
            
            for attack_type in attack_types:
                class_tp = class_fp = class_tn = class_fn = 0
                
                for event in query.filter(Event.attack_type == attack_type).all():
                    if not hasattr(event, 'labels_data') or not event.labels_data:
                        continue
                        
                    ml_attack_type = event.labels_data.get("ml_attack_type")
                    
                    if not ml_attack_type:
                        continue
                    
                    if event.attack_type == attack_type and ml_attack_type == attack_type:
                        class_tp += 1
                    elif event.attack_type != attack_type and ml_attack_type == attack_type:
                        class_fp += 1
                    elif event.attack_type != attack_type and ml_attack_type != attack_type:
                        class_tn += 1
                    else:
                        class_fn += 1
                
                # Запобігаємо діленню на нуль
                class_precision = class_tp / (class_tp + class_fp) if (class_tp + class_fp) > 0 else 0
                class_recall = class_tp / (class_tp + class_fn) if (class_tp + class_fn) > 0 else 0
                class_f1 = 2 * (class_precision * class_recall) / (class_precision + class_recall) if (class_precision + class_recall) > 0 else 0
                
                class_metrics[attack_type] = {
                    "precision": class_precision,
                    "recall": class_recall,
                    "f1_score": class_f1,
                    "support": class_tp + class_fn
                }
            
            metrics.class_metrics = class_metrics
            
            # Зберігаємо метрики в базі даних
            db.session.add(metrics)
            db.session.commit()
            
            return {
                "success": True,
                "metrics_id": metrics.id,
                "metrics": metrics.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error updating performance metrics: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_latest_metrics(self) -> Dict[str, Any]:
        """
        Отримати останні метрики продуктивності ML
        
        Returns:
            Dictionary з метриками продуктивності
        """
        self._ensure_config_loaded()
        
        try:
            metrics = MLPerformanceMetrics.query.order_by(MLPerformanceMetrics.timestamp.desc()).first()
            
            if not metrics:
                return {
                    "success": False,
                    "message": "No metrics available"
                }
            
            return {
                "success": True,
                "metrics": metrics.to_dict()
            }
        except Exception as e:
            logger.error(f"Error getting latest metrics: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def analyze_event(self, event_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Аналізує дані події та визначає мітки і показники впевненості
        
        Args:
            event_data: Дані події
            
        Returns:
            Tuple із словників (ml_labels, confidence)
        """
        self._ensure_config_loaded()
        
        if not self.provider:
            logger.error("ML provider not initialized")
            return {}, {}
        
        try:
            # Класифікація через провайдер
            result = self.provider.classify_event(event_data)
            
            if not result.get("success"):
                logger.error(f"Failed to analyze event: {result.get('error')}")
                return {}, {}
            
            classification = result.get("classification", {})
            confidence = result.get("confidence", 0.0)
            
            # Формуємо мітки ML та інформацію про впевненість
            ml_labels = {
                "true_positive": classification.get("true_positive", False),
                "attack_type": classification.get("attack_type", "Unknown"),
                "mitre_tactic": classification.get("mitre_tactic", ""),
                "mitre_technique": classification.get("mitre_technique", ""),
                "tags": classification.get("tags", []),
                "confidence": confidence,
                "classified_at": datetime.utcnow().isoformat()
            }
            
            return ml_labels, {"confidence": confidence}
        except Exception as e:
            logger.error(f"Error while analyzing event with ML: {str(e)}")
            return {}, {}
    
    def classify_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Класифікувати список подій
        
        Args:
            events: Список подій для класифікації
            
        Returns:
            Список класифікованих подій
        """
        self._ensure_config_loaded()
        
        if not self.provider:
            logger.error("ML provider not initialized")
            return events
        
        try:
            # Спроба отримати результати з кешу
            cache_key = f"classify_events_{hash(json.dumps([e.get('id', str(hash(e))) for e in events]))}"
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.info("Using cached ML classification results")
                return cached_result

            # Пакетна класифікація через провайдер
            results = self.provider.batch_classify(events)
            
            # Поєднуємо результати з вхідними даними
            classified_events = []
            for event, result in zip(events, results):
                if result.get("success"):
                    classification = result.get("classification", {})
                    confidence = result.get("confidence", 0.0)
                    
                    # Додаємо результати до події
                    event_copy = event.copy()
                    event_copy["ml_processed"] = True
                    event_copy["ml_confidence"] = confidence
                    event_copy["ml_timestamp"] = datetime.utcnow().isoformat()
                    
                    # Додаємо класифікацію, якщо впевненість вища за поріг
                    min_threshold = self.config.get("min_confidence_threshold", 0.7)
                    if confidence >= min_threshold:
                        if "true_positive" in classification:
                            event_copy["true_positive"] = classification["true_positive"]
                        if "attack_type" in classification:
                            event_copy["attack_type"] = classification["attack_type"]
                        if "mitre_tactic" in classification:
                            event_copy["mitre_tactic"] = classification["mitre_tactic"]
                        if "mitre_technique" in classification:
                            event_copy["mitre_technique"] = classification["mitre_technique"]
                        
                        # Додаємо ML мітки в окремому полі для інтерфейсу верифікації
                        event_copy["ml_labels"] = {
                            "true_positive": classification.get("true_positive"),
                            "attack_type": classification.get("attack_type"),
                            "mitre_tactic": classification.get("mitre_tactic"),
                            "mitre_technique": classification.get("mitre_technique"),
                            "confidence": confidence,
                            "tags": classification.get("tags", []),
                            "classified_at": datetime.utcnow().isoformat()
                        }
                    
                    classified_events.append(event_copy)
                else:
                    # При помилці повертаємо оригінальну подію
                    classified_events.append(event)
            
            # Зберегти результат у кеш
            self.cache.set(cache_key, classified_events)
            return classified_events
            
        except Exception as e:
            logger.error(f"Error while classifying events with ML API: {str(e)}")
            return events
    
    # Методи для кешування результатів класифікації для повторювальних подій
    def _get_from_cache(self, event_id):
        """Отримати результат з кешу за ID події"""
        if not hasattr(self, '_classification_cache'):
            self._classification_cache = {}
            
        # Очистка застарілих записів (старше 1 години)
        current_time = time.time()
        self._classification_cache = {k: v for k, v in self._classification_cache.items() 
                                    if current_time - v.get('timestamp', 0) < 3600}
        
        return self._classification_cache.get(event_id)
    
    def _save_to_cache(self, event_id, result):
        """Зберегти результат в кеш"""
        if not hasattr(self, '_classification_cache'):
            self._classification_cache = {}
            
        result['timestamp'] = time.time()
        self._classification_cache[event_id] = result
        
        # Обмежуємо розмір кешу
        if len(self._classification_cache) > 1000:
            # Видаляємо найстаріші записи
            sorted_items = sorted(self._classification_cache.items(), 
                                key=lambda x: x[1].get('timestamp', 0))
            to_delete = sorted_items[:100]  # Видаляємо 100 найстаріших
            for key, _ in to_delete:
                del self._classification_cache[key]
