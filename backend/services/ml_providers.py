import logging
import requests
import json
import os
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod

# Налаштування логування
logger = logging.getLogger(__name__)

class MLProvider(ABC):
    """Абстрактний базовий клас для ML-провайдерів"""
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        Перевірити з'єднання з ML-провайдером
        
        Returns:
            Dictionary з результатами перевірки
        """
        pass
        
    @abstractmethod
    def classify_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Класифікувати одну подію
        
        Args:
            event_data: Дані події
            
        Returns:
            Dictionary з результатами класифікації
        """
        pass
        
    @abstractmethod
    def batch_classify(self, events_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Класифікувати пакет подій
        
        Args:
            events_data: Список даних подій
            
        Returns:
            Список з результатами класифікації
        """
        pass
        
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Отримати інформацію про модель
        
        Returns:
            Dictionary з інформацією про модель
        """
        pass

    @abstractmethod
    def classify_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Класифікувати список подій
        
        Args:
            events: Список подій для класифікації
            
        Returns:
            Список класифікованих подій
        """
        pass

class APIMLProvider(MLProvider):
    """Провайдер, що використовує зовнішній ML API"""
    
    def __init__(self, api_url: str, api_key: str):
        """
        Ініціалізація провайдера
        
        Args:
            api_url: URL до ML API
            api_key: Ключ доступу до ML API
        """
        self.api_url = api_url
        self.api_key = api_key
        
    def test_connection(self) -> Dict[str, Any]:
        """
        Перевірити з'єднання з ML API
        
        Returns:
            Dictionary з результатами перевірки
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.api_url}/health", 
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Successfully connected to ML API",
                    "details": response.json()
                }
            else:
                return {
                    "success": False,
                    "message": f"ML API returned error: {response.status_code}",
                    "details": {"status_code": response.status_code, "response": response.text}
                }
        except Exception as e:
            logger.error(f"Error testing ML API connection: {str(e)}")
            return {
                "success": False,
                "message": f"Error connecting to ML API: {str(e)}",
                "details": {"error_type": type(e).__name__}
            }
            
    def classify_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Класифікувати одну подію
        
        Args:
            event_data: Дані події
            
        Returns:
            Dictionary з результатами класифікації
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.api_url}/classify", 
                headers=headers,
                json={"event": event_data},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "classification": result.get("classification", {}),
                    "confidence": result.get("confidence", 0.0)
                }
            else:
                return {
                    "success": False,
                    "error": f"ML API returned error: {response.status_code} - {response.text}"
                }
        except Exception as e:
            logger.error(f"Error classifying event with ML API: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def batch_classify(self, events_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Класифікувати пакет подій
        
        Args:
            events_data: Список даних подій
            
        Returns:
            Список з результатами класифікації
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.api_url}/batch-classify", 
                headers=headers,
                json={"events": events_data},
                timeout=60
            )
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                return results
            else:
                logger.error(f"ML API returned error: {response.status_code} - {response.text}")
                # Створюємо список з помилками для кожної події
                return [{"success": False, "error": f"API error: {response.status_code}"} for _ in events_data]
        except Exception as e:
            logger.error(f"Error batch classifying events with ML API: {str(e)}")
            # Створюємо список з помилками для кожної події
            return [{"success": False, "error": str(e)} for _ in events_data]
            
    def get_model_info(self) -> Dict[str, Any]:
        """
        Отримати інформацію про модель
        
        Returns:
            Dictionary з інформацією про модель
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.api_url}/model-info", 
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "model_info": response.json()
                }
            else:
                return {
                    "model_info": {
                        "version": "unknown",
                        "error": f"Could not get model info: {response.status_code}"
                    }
                }
        except Exception as e:
            logger.error(f"Error getting model info from ML API: {str(e)}")
            return {
                "model_info": {
                    "version": "unknown",
                    "error": str(e)
                }
            }

    def classify_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Класифікувати список подій
        
        Args:
            events: Список подій для класифікації
            
        Returns:
            Список класифікованих подій
        """
        # Використовуємо batch_classify для реалізації
        results = self.batch_classify(events)
        
        # Поєднуємо результати з вхідними даними
        classified_events = []
        for event, result in zip(events, results):
            event_copy = event.copy()
            if result.get("success"):
                classification = result.get("classification", {})
                confidence = result.get("confidence", 0.0)
                
                event_copy["ml_processed"] = True
                event_copy["ml_confidence"] = confidence
                event_copy["ml_timestamp"] = datetime.utcnow().isoformat()
                
                # Додаємо ML-мітки
                event_copy["ml_labels"] = {
                    "true_positive": classification.get("true_positive"),
                    "attack_type": classification.get("attack_type"),
                    "mitre_tactic": classification.get("mitre_tactic"),
                    "mitre_technique": classification.get("mitre_technique"),
                    "confidence": confidence,
                    "tags": classification.get("tags", []),
                    "classified_at": datetime.utcnow().isoformat()
                }
                
                # Додаємо основні класифікації
                if "true_positive" in classification:
                    event_copy["true_positive"] = classification["true_positive"]
                if "attack_type" in classification:
                    event_copy["attack_type"] = classification["attack_type"]
                if "mitre_tactic" in classification:
                    event_copy["mitre_tactic"] = classification["mitre_tactic"]
                if "mitre_technique" in classification:
                    event_copy["mitre_technique"] = classification["mitre_technique"]
            
            classified_events.append(event_copy)
            
        return classified_events

class LocalMLProvider(MLProvider):
    """Провайдер, що використовує локальну ML модель"""
    
    def __init__(self, model_path: str):
        """
        Ініціалізація провайдера
        
        Args:
            model_path: Шлях до файлу моделі
        """
        self.model_path = model_path
        self.model = None
        self._load_model()
        
    def _load_model(self):
        """
        Завантажити модель з файлу
        """
        try:
            # Для MVP просто перевіряємо, чи існує файл
            if os.path.exists(self.model_path):
                logger.info(f"Model file exists at {self.model_path}")
                self.model = {"loaded": True, "path": self.model_path}
            else:
                logger.warning(f"Model file does not exist at {self.model_path}")
                self.model = None
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self.model = None
            
    def test_connection(self) -> Dict[str, Any]:
        """
        Перевірити наявність моделі
        
        Returns:
            Dictionary з результатами перевірки
        """
        if self.model:
            return {
                "success": True,
                "message": "Local model loaded successfully",
                "details": {"model_path": self.model_path}
            }
        else:
            return {
                "success": False,
                "message": "Local model not available",
                "details": {"model_path": self.model_path}
            }
            
    def classify_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Класифікувати одну подію
        
        Args:
            event_data: Дані події
            
        Returns:
            Dictionary з результатами класифікації
        """
        # Для MVP використовуємо заглушку
        if not self.model:
            return {
                "success": False,
                "error": "Model not loaded"
            }
        
        # Заглушка для класифікації
        return {
            "success": True,
            "classification": {
                "true_positive": True,
                "attack_type": "Brute Force",
                "mitre_tactic": "Initial Access",
                "mitre_technique": "Valid Accounts"
            },
            "confidence": 0.85
        }
            
    def batch_classify(self, events_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Класифікувати пакет подій
        
        Args:
            events_data: Список даних подій
            
        Returns:
            Список з результатами класифікації
        """
        if not self.model:
            return [{"success": False, "error": "Model not loaded"} for _ in events_data]
        
        # Для MVP використовуємо заглушку
        results = []
        for _ in events_data:
            results.append(self.classify_event({}))
        
        return results
            
    def get_model_info(self) -> Dict[str, Any]:
        """
        Отримати інформацію про модель
        
        Returns:
            Dictionary з інформацією про модель
        """
        if not self.model:
            return {
                "model_info": {
                    "version": "unknown",
                    "error": "Model not loaded"
                }
            }
        
        return {
            "model_info": {
                "version": "local-1.0",
                "type": "local",
                "path": self.model_path
            }
        }

    def classify_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Класифікувати список подій
        
        Args:
            events: Список подій для класифікації
            
        Returns:
            Список класифікованих подій
        """
        # Використовуємо batch_classify для спрощення реалізації
        batch_results = self.batch_classify(events)
        
        # Поєднуємо результати з вхідними даними
        classified_events = []
        for event, result in zip(events, batch_results):
            event_copy = event.copy()
            
            if result.get("success"):
                classification = result.get("classification", {})
                confidence = result.get("confidence", 0.0)
                
                # Додаємо ML-мітки та результати класифікації
                event_copy["ml_processed"] = True
                event_copy["ml_confidence"] = confidence
                event_copy["ml_timestamp"] = datetime.utcnow().isoformat()
                
                event_copy["ml_labels"] = {
                    "true_positive": classification.get("true_positive"),
                    "attack_type": classification.get("attack_type"),
                    "mitre_tactic": classification.get("mitre_tactic"),
                    "mitre_technique": classification.get("mitre_technique"),
                    "confidence": confidence,
                    "classified_at": datetime.utcnow().isoformat()
                }
                
                # Додаємо основні класифікації
                for key in ["true_positive", "attack_type", "mitre_tactic", "mitre_technique"]:
                    if key in classification:
                        event_copy[key] = classification[key]
            
            classified_events.append(event_copy)
            
        return classified_events

class DummyMLProvider(MLProvider):
    """Тестовий провайдер, що генерує випадкові класифікації"""
    
    def __init__(self):
        """
        Ініціалізація тестового провайдера
        """
        self.attack_types = [
            "Brute Force", "SQL Injection", "Cross-Site Scripting", "Denial of Service", 
            "Phishing", "Malware", "Ransomware", "Data Exfiltration", "Privilege Escalation",
            "Reconnaissance", "Lateral Movement", "Command and Control"
        ]
        
        self.mitre_tactics = [
            "Initial Access", "Execution", "Persistence", "Privilege Escalation",
            "Defense Evasion", "Credential Access", "Discovery", "Lateral Movement",
            "Collection", "Command and Control", "Exfiltration", "Impact"
        ]
        
        self.mitre_techniques = {
            "Initial Access": ["Phishing", "Valid Accounts", "External Remote Services"],
            "Execution": ["Command Line Interface", "Scripting", "Windows Management Instrumentation"],
            "Persistence": ["Registry Run Keys", "Scheduled Task", "Create Account"],
            "Privilege Escalation": ["Access Token Manipulation", "Bypass User Account Control", "Sudo and Sudo Caching"],
            "Defense Evasion": ["Disable Security Tools", "Obfuscated Files", "Rootkit"],
            "Credential Access": ["Brute Force", "Credential Dumping", "Keylogging"],
            "Discovery": ["Account Discovery", "Network Service Scanning", "System Information Discovery"],
            "Lateral Movement": ["Remote Services", "Internal Spearphishing", "Pass the Hash"],
            "Collection": ["Data from Local System", "Email Collection", "Screen Capture"],
            "Command and Control": ["Encrypted Channel", "Web Service", "Remote Access Tools"],
            "Exfiltration": ["Data Transfer Size Limits", "Exfiltration Over C2", "Scheduled Transfer"],
            "Impact": ["Data Destruction", "Service Stop", "Endpoint Denial of Service"]
        }
        
    def test_connection(self) -> Dict[str, Any]:
        """
        Імітувати перевірку з'єднання
        
        Returns:
            Dictionary з результатами перевірки
        """
        return {
            "success": True,
            "message": "Dummy ML provider ready",
            "details": {"provider": "dummy"}
        }
            
    def classify_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Імітувати класифікацію події
        
        Args:
            event_data: Дані події
            
        Returns:
            Dictionary з результатами класифікації
        """
        # Отримуємо випадковий тип атаки
        attack_type = random.choice(self.attack_types)
        
        # Отримуємо випадкову тактику та техніку MITRE
        tactic = random.choice(self.mitre_tactics)
        technique = random.choice(self.mitre_techniques[tactic])
        
        # Генеруємо випадковий рівень впевненості від 60% до 98%
        confidence = round(random.uniform(0.6, 0.98), 2)
        
        # Визначаємо, чи є це істинним спрацюванням
        true_positive = random.choice([True, False])
        if true_positive:
            # Для істинних спрацювань встановлюємо вищу впевненість
            confidence = max(confidence, 0.85)
        
        # Генеруємо набір тегів
        tags = random.sample([
            "suspicious", "critical", "malware", "ransomware", 
            "network", "authentication", "privileged", "lateral",
            "data_theft", "command_control"
        ], k=random.randint(1, 3))
        
        return {
            "success": True,
            "classification": {
                "true_positive": true_positive,
                "attack_type": attack_type,
                "mitre_tactic": tactic,
                "mitre_technique": technique,
                "tags": tags
            },
            "confidence": confidence
        }
            
    def batch_classify(self, events_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Імітувати класифікацію пакету подій
        
        Args:
            events_data: Список даних подій
            
        Returns:
            Список з результатами класифікації
        """
        return [self.classify_event(event) for event in events_data]
            
    def get_model_info(self) -> Dict[str, Any]:
        """
        Отримати інформацію про модель
        
        Returns:
            Dictionary з інформацією про модель
        """
        return {
            "model_info": {
                "version": "dummy-1.0",
                "type": "dummy",
                "description": "Generates random classifications for testing"
            }
        }

    def classify_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Класифікувати список подій
        
        Args:
            events: Список подій для класифікації
            
        Returns:
            Список класифікованих подій
        """
        # Класифікуємо кожну подію окремо
        classified_events = []
        for event in events:
            event_copy = event.copy()
            
            # Отримуємо класифікацію для поточної події
            result = self.classify_event(event)
            
            if result.get("success"):
                classification = result.get("classification", {})
                confidence = result.get("confidence", 0.0)
                
                # Додаємо базову інформацію
                event_copy["ml_processed"] = True
                event_copy["ml_confidence"] = confidence
                event_copy["ml_timestamp"] = datetime.utcnow().isoformat()
                
                # Додаємо ML-мітки
                event_copy["ml_labels"] = {
                    "true_positive": classification.get("true_positive"),
                    "attack_type": classification.get("attack_type"),
                    "mitre_tactic": classification.get("mitre_tactic"),
                    "mitre_technique": classification.get("mitre_technique"),
                    "confidence": confidence,
                    "tags": classification.get("tags", []),
                    "classified_at": datetime.utcnow().isoformat()
                }
                
                # Додаємо основні класифікації
                for key in ["true_positive", "attack_type", "mitre_tactic", "mitre_technique"]:
                    if key in classification:
                        event_copy[key] = classification[key]
            
            classified_events.append(event_copy)
            
        return classified_events
