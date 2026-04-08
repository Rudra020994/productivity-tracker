from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

db = SQLAlchemy()

class WorkEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    module = db.Column(db.String(100))
    description = db.Column(db.String(200))
    date = db.Column(db.Date)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    duration = db.Column(db.Float)  # duration in hours

    def calculate_duration(self):
        dt_start = datetime.combine(self.date, self.start_time)
        dt_end = datetime.combine(self.date, self.end_time)
        delta = dt_end - dt_start
        self.duration = round(delta.total_seconds() / 3600, 2)
