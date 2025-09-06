"""
Enhanced models for interaction tracking and lead scoring
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, DECIMAL, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app import db

class UserInteraction(db.Model):
    """Model for tracking all user interactions across the platform."""
    __tablename__ = 'user_interactions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), index=True)
    user_id = Column(Integer, db.ForeignKey('users.id'), nullable=True)
    interaction_type = Column(String(50), nullable=False, index=True)
    source_page = Column(String(200))
    data = Column(Text)  # JSON string for interaction data
    converted_to_lead = Column(Boolean, default=False, index=True)
    lead_id = Column(Integer, db.ForeignKey('leads.id'), nullable=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    referrer_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="interactions")
    lead = relationship("Lead", backref="source_interaction")
    
    def __repr__(self):
        return f"<UserInteraction {self.interaction_type} for session {self.session_id[:8]}...>"

class UserSession(db.Model):
    """Model for tracking anonymous user sessions."""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, db.ForeignKey('users.id'), nullable=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    referrer_url = Column(Text)
    utm_source = Column(String(100))
    utm_medium = Column(String(100))
    utm_campaign = Column(String(100))
    first_page = Column(String(200))
    last_page = Column(String(200))
    page_count = Column(Integer, default=1)
    total_time_seconds = Column(Integer, default=0)
    converted_to_lead = Column(Boolean, default=False, index=True)
    lead_id = Column(Integer, db.ForeignKey('leads.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="sessions")
    lead = relationship("Lead", backref="source_session")
    
    def __repr__(self):
        return f"<UserSession {self.session_id[:8]}... - {self.page_count} pages>"

class LeadScoringRule(db.Model):
    """Model for configurable lead scoring rules."""
    __tablename__ = 'lead_scoring_rules'
    
    id = Column(Integer, primary_key=True)
    interaction_type = Column(String(50), nullable=False)
    condition_field = Column(String(100))
    condition_operator = Column(String(20))
    condition_value = Column(Text)
    points = Column(Integer, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<LeadScoringRule {self.interaction_type}: {self.points} points>"