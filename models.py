from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime)
    chronotype = db.Column(db.String)
    confidence = db.Column(db.Float)
    peak_focus_window = db.Column(db.String)
    natural_wake_time = db.Column(db.String)
    recommended_bedtime = db.Column(db.String)
    crash_window = db.Column(db.String)
    avg_duration = db.Column(db.Float)
    avg_bedtime = db.Column(db.String)
    avg_wake_time = db.Column(db.String)
    consistency_score = db.Column(db.Float)
    low_confidence = db.Column(db.Boolean)
    recommendations = db.Column(db.String)
    rulebook = db.Column(db.String)
    schedule = db.Column(db.String)
    activity_distribution = db.Column(db.String)
    low_confidence_explanation = db.Column(db.String)
    experiment_protocol = db.Column(db.String)
    sleep_by_day = db.Column(db.String)
    heatmap_data = db.Column(db.String)
    is_biphasic = db.Column(db.Boolean, default=False)
    nap_metrics = db.Column(db.String)
    quiz_based = db.Column(db.Boolean, default=False)
    quiz_supplemented = db.Column(db.Boolean, default=False)
    sleep_record_count = db.Column(db.Integer, default=0)
    peak_hour = db.Column(db.Integer, default=10)
    crash_hour = db.Column(db.Integer, default=15)
    quiz_based = db.Column(db.Boolean, default=False)
    quiz_supplemented = db.Column(db.Boolean, default=False)
    sleep_record_count = db.Column(db.Integer, default=0)
    


    def to_dict(self):
        return {
            'id': self.id,
            'chronotype': self.chronotype,
            'confidence': self.confidence,
            'peak_focus_window': self.peak_focus_window,
            'natural_wake_time': self.natural_wake_time,
            'recommended_bedtime': self.recommended_bedtime,
            'crash_window': self.crash_window,
            'avg_duration': self.avg_duration,
            'avg_bedtime': self.avg_bedtime,
            'avg_wake_time': self.avg_wake_time,
            'consistency_score': self.consistency_score,
            'low_confidence': self.low_confidence,
            'recommendations': json.loads(self.recommendations or '[]'),
            'rulebook': json.loads(self.rulebook or '[]'),
            'schedule': json.loads(self.schedule or '[]'),
            'activity_distribution': json.loads(self.activity_distribution or '[]'),
            'low_confidence_explanation': self.low_confidence_explanation,
            'experiment_protocol': json.loads(self.experiment_protocol or '[]'),
            'sleep_by_day': json.loads(self.sleep_by_day or '[]'),
            'heatmap_data': json.loads(self.heatmap_data or '[]'),
            'is_biphasic': self.is_biphasic or False,
            'nap_metrics': json.loads(self.nap_metrics or '{}'),
            'sleep_record_count': self.sleep_record_count or 0,
            'peak_hour': self.peak_hour or 10,
            'crash_hour': self.crash_hour or 15,
            'quiz_based': self.quiz_based or False,
            'quiz_supplemented': self.quiz_supplemented or False,
            'sleep_record_count': self.sleep_record_count or 0
        }