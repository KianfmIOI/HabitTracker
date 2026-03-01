from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import Flask

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Interger, primary_key = True)
    username = db.Column(db.String(100), unique = True, nullable = False)
    
    habits = db.relationship("Habit", back_populates = "user", cascade = "all, delete-orphan")

class Habit(db.Model):
    id = db.Column(db.Interger, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id")
                        )
    name = db.Column(db.String(100), unique = True, nullable = False)
    interval = db.Column(db.Integer, nullable = False)
    created_at = db.Column(db.DateTime, default = datetime.utcnow)
    last_check_in_at = db.Column(db.DateTime, nullable = True)

    user = db.relationship("User", back_populates = "habits")
    checkins = db.relationship("HabitCheckin", back_populates = "habits", cascade = "all, delete-orphan")
    