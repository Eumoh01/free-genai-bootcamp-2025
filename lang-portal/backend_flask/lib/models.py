from .db import db

class Word(db.Model):
    __tablename__ = 'words'
    
    id = db.Column(db.Integer, primary_key=True)
    spanish = db.Column(db.String, nullable=False)
    pronunciation = db.Column(db.String, nullable=False)
    english = db.Column(db.String, nullable=False)

    # Relationships
    groups = db.relationship('Group', secondary='word_groups', back_populates='words')
    reviews = db.relationship('WordReviewItem', back_populates='word')

class Group(db.Model):
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    words_count = db.Column(db.Integer, default=0)

    # Relationships
    words = db.relationship('Word', secondary='word_groups', back_populates='groups')
    study_sessions = db.relationship('StudySession', back_populates='group')

class WordGroup(db.Model):
    __tablename__ = 'word_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)

class StudyActivity(db.Model):
    __tablename__ = 'study_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    url = db.Column(db.String, nullable=False)
    preview_url = db.Column(db.String)

    # Relationships
    sessions = db.relationship('StudySession', back_populates='activity')

class StudySession(db.Model):
    __tablename__ = 'study_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    study_activity_id = db.Column(db.Integer, db.ForeignKey('study_activities.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

    # Relationships
    group = db.relationship('Group', back_populates='study_sessions')
    activity = db.relationship('StudyActivity', back_populates='sessions')
    reviews = db.relationship('WordReviewItem', back_populates='session')

class WordReviewItem(db.Model):
    __tablename__ = 'word_review_items'
    
    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'), nullable=False)
    study_session_id = db.Column(db.Integer, db.ForeignKey('study_sessions.id'), nullable=False)
    correct = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

    # Relationships
    word = db.relationship('Word', back_populates='reviews')
    session = db.relationship('StudySession', back_populates='reviews') 