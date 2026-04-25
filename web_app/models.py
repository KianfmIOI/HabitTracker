from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), nullable = True, )
    username = db.Column(db.String(50), unique=True, index=True, nullable=False)
    phone_number = db.Column(db.String(11), unique=True, nullable=False)
    email = db.Column(db.String(120), unique = True, nullable = True)
    birth_date = db.Column(db.Date, nullable=True)
    creation_date = db.Column(db.Date, default = date.today)
    last_login_date = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default = True)
    
    password_hash = db.Column(db.String(255),nullable = False)

    habits = db.relationship('Habit', back_populates='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class Habit(db.Model):
    __tablename__ = 'habits'

    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False, index=True )
    name = db.Column(db.String(100), nullable = False)
    creation_date = db.Column(db.Date, default = date.today)
    last_check_in_date = db.Column(db.Date, nullable = True)
    last_sync_date = db.Column(db.Date, nullable = True)
    streak = db.Column(db.Integer, default = 0)
    longest_streak = db.Column(db.Integer, default = 0)
    is_main = db.Column(db.Boolean, default = False)
    interval = db.Column(db.Integer, default = 1)
    emoji = db.Column(db.String(10), default = "🔥")
    is_archived = db.Column(db.Boolean, default = False)
    archive_date = db.Column(db.Date, nullable=True)
    description= db.Column(db.String(255), nullable = True)
    updated_at = db.Column(db.DateTime, default = datetime.now, onupdate = datetime.now)
    color = db.Column(db.String(7), default="#85B2FA")
    
    user = db.relationship('User', back_populates='habits')
    check_ins = db.relationship('CheckIn', back_populates = 'habit', lazy = True, cascade ="all, delete-orphan")

class CheckIn(db.Model):
    __tablename__ = 'check_ins'

    id = db.Column(db.Integer, primary_key = True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habits.id'), nullable = False, index=True )
    check_in_date = db.Column(db.Date, nullable = False)
    is_done = db.Column(db.Boolean, default = False)
    note = db.Column(db.String(255), nullable = True)

    habit = db.relationship('Habit', back_populates='check_ins')

