from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import uuid
import hashlib
import secrets

db = SQLAlchemy()

class PrivacySession(db.Model):
    __tablename__ = 'privacy_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Privacy identifiers
    encrypted_wallet_address = db.Column(db.String(64), nullable=False)  # Hashed wallet
    session_token = db.Column(db.String(128), nullable=False)  # Secure session token
    privacy_level = db.Column(db.String(20), nullable=False, default='standard')  # 'standard', 'enhanced', 'maximum'
    
    # Session settings
    is_active = db.Column(db.Boolean, default=True)
    hide_balances = db.Column(db.Boolean, default=False)
    use_private_orders = db.Column(db.Boolean, default=True)
    mev_protection = db.Column(db.Boolean, default=True)
    
    # Shade Protocol integration
    shade_enabled = db.Column(db.Boolean, default=True)
    secret_contract_address = db.Column(db.String(64), nullable=True)
    viewing_key = db.Column(db.String(128), nullable=True)  # Encrypted viewing key
    
    # Session metadata
    user_agent = db.Column(db.String(256), nullable=True)
    ip_hash = db.Column(db.String(64), nullable=True)  # Hashed IP for security
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    def __init__(self, wallet_address, **kwargs):
        super(PrivacySession, self).__init__(**kwargs)
        self.encrypted_wallet_address = self.encrypt_wallet_address(wallet_address)
        self.session_token = self.generate_session_token()
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(hours=24)  # 24-hour sessions
    
    def encrypt_wallet_address(self, wallet_address):
        """Encrypt wallet address for privacy"""
        salt = "snipswap_privacy_salt_2024"
        return hashlib.sha256(f"{wallet_address}_{salt}".encode()).hexdigest()
    
    def generate_session_token(self):
        """Generate secure session token"""
        return secrets.token_urlsafe(96)  # 128 characters
    
    def hash_ip_address(self, ip_address):
        """Hash IP address for privacy while maintaining security"""
        salt = "snipswap_ip_salt_2024"
        return hashlib.sha256(f"{ip_address}_{salt}".encode()).hexdigest()
    
    def is_expired(self):
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    
    def extend_session(self, hours=24):
        """Extend session expiration"""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.last_activity = datetime.utcnow()
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
    
    def __repr__(self):
        return f'<PrivacySession {self.session_id}: {self.privacy_level}>'
    
    def to_dict(self, include_sensitive=False):
        data = {
            'session_id': self.session_id,
            'privacy_level': self.privacy_level,
            'is_active': self.is_active,
            'hide_balances': self.hide_balances,
            'use_private_orders': self.use_private_orders,
            'mev_protection': self.mev_protection,
            'shade_enabled': self.shade_enabled,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired()
        }
        
        # Only include sensitive data if explicitly requested and authorized
        if include_sensitive:
            data.update({
                'session_token': self.session_token,
                'encrypted_wallet_address': self.encrypted_wallet_address,
                'secret_contract_address': self.secret_contract_address,
                'ip_hash': self.ip_hash
            })
        
        return data
    
    def get_privacy_settings(self):
        """Get privacy settings for the session"""
        return {
            'privacy_level': self.privacy_level,
            'hide_balances': self.hide_balances,
            'use_private_orders': self.use_private_orders,
            'mev_protection': self.mev_protection,
            'shade_enabled': self.shade_enabled
        }
    
    def update_privacy_settings(self, settings):
        """Update privacy settings"""
        if 'privacy_level' in settings:
            self.privacy_level = settings['privacy_level']
        if 'hide_balances' in settings:
            self.hide_balances = settings['hide_balances']
        if 'use_private_orders' in settings:
            self.use_private_orders = settings['use_private_orders']
        if 'mev_protection' in settings:
            self.mev_protection = settings['mev_protection']
        if 'shade_enabled' in settings:
            self.shade_enabled = settings['shade_enabled']
        
        self.update_activity()
    
    @staticmethod
    def create_session(wallet_address, privacy_level='standard', user_agent=None, ip_address=None):
        """Create a new privacy session"""
        session = PrivacySession(
            wallet_address=wallet_address,
            privacy_level=privacy_level,
            user_agent=user_agent
        )
        
        if ip_address:
            session.ip_hash = session.hash_ip_address(ip_address)
        
        return session
    
    @staticmethod
    def get_active_session(session_token):
        """Get active session by token"""
        session = PrivacySession.query.filter_by(
            session_token=session_token,
            is_active=True
        ).first()
        
        if session and not session.is_expired():
            session.update_activity()
            return session
        
        return None
    
    @staticmethod
    def cleanup_expired_sessions():
        """Clean up expired sessions"""
        expired_sessions = PrivacySession.query.filter(
            PrivacySession.expires_at < datetime.utcnow()
        ).all()
        
        for session in expired_sessions:
            session.is_active = False
        
        return len(expired_sessions)

