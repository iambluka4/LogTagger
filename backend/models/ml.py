from models import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func
from datetime import datetime

class MLPerformanceMetrics(db.Model):
    """Model for storing ML classification performance metrics"""
    
    __tablename__ = 'ml_performance_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    model_version = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=func.now())
    
    # Base metrics
    true_positives = db.Column(db.Integer, default=0)
    false_positives = db.Column(db.Integer, default=0)
    true_negatives = db.Column(db.Integer, default=0)
    false_negatives = db.Column(db.Integer, default=0)
    
    # Calculated metrics
    accuracy = db.Column(db.Float, default=0.0)
    precision = db.Column(db.Float, default=0.0)
    recall = db.Column(db.Float, default=0.0)
    f1_score = db.Column(db.Float, default=0.0)
    
    # Class metrics
    class_metrics = db.Column(JSON, default={})
    
    def calculate_metrics(self):
        """Calculate metrics based on base values"""
        # Загальна кількість прикладів
        total = self.true_positives + self.false_positives + self.true_negatives + self.false_negatives
        
        # Уникаємо ділення на нуль
        if total == 0:
            return
            
        # Точність (кількість правильних передбачень до загальної кількості)
        self.accuracy = (self.true_positives + self.true_negatives) / total
        
        # Precision (кількість правильних позитивних передбачень до всіх позитивних передбачень)
        if self.true_positives + self.false_positives > 0:
            self.precision = self.true_positives / (self.true_positives + self.false_positives)
        
        # Recall (кількість правильних позитивних передбачень до всіх реальних позитивних прикладів)
        if self.true_positives + self.false_negatives > 0:
            self.recall = self.true_positives / (self.true_positives + self.false_negatives)
        
        # F1 Score (гармонічне середнє precision і recall)
        if self.precision + self.recall > 0:
            self.f1_score = 2 * (self.precision * self.recall) / (self.precision + self.recall)
    
    def to_dict(self):
        """Конвертувати об'єкт у словник для API"""
        return {
            'id': self.id,
            'model_version': self.model_version,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'true_positives': self.true_positives,
            'false_positives': self.false_positives,
            'true_negatives': self.true_negatives,
            'false_negatives': self.false_negatives,
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'class_metrics': self.class_metrics
        }
