from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class TradingPair(db.Model):
    __tablename__ = 'trading_pairs'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), unique=True, nullable=False)  # e.g., "SCRT/USDT"
    base_token = db.Column(db.String(10), nullable=False)  # e.g., "SCRT"
    quote_token = db.Column(db.String(10), nullable=False)  # e.g., "USDT"
    
    # Current market data
    current_price = db.Column(db.Float, nullable=False, default=0.0)
    price_change_24h = db.Column(db.Float, nullable=False, default=0.0)
    volume_24h = db.Column(db.Float, nullable=False, default=0.0)
    high_24h = db.Column(db.Float, nullable=False, default=0.0)
    low_24h = db.Column(db.Float, nullable=False, default=0.0)
    
    # Privacy and trading settings
    is_private = db.Column(db.Boolean, default=True)  # Shade Protocol privacy
    is_active = db.Column(db.Boolean, default=True)
    min_order_size = db.Column(db.Float, default=0.001)
    max_order_size = db.Column(db.Float, default=1000000.0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='pair', lazy=True, cascade='all, delete-orphan')
    trades = db.relationship('Trade', backref='pair', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<TradingPair {self.symbol}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'base_token': self.base_token,
            'quote_token': self.quote_token,
            'current_price': self.current_price,
            'price_change_24h': self.price_change_24h,
            'volume_24h': self.volume_24h,
            'high_24h': self.high_24h,
            'low_24h': self.low_24h,
            'is_private': self.is_private,
            'is_active': self.is_active,
            'min_order_size': self.min_order_size,
            'max_order_size': self.max_order_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_cosmos_pairs():
        """Get default Cosmos ecosystem trading pairs"""
        return [
            {
                'symbol': 'SCRT/USDT',
                'base_token': 'SCRT',
                'quote_token': 'USDT',
                'current_price': 0.4521,
                'is_private': True
            },
            {
                'symbol': 'ATOM/USDT',
                'base_token': 'ATOM',
                'quote_token': 'USDT',
                'current_price': 12.34,
                'is_private': False
            },
            {
                'symbol': 'OSMO/USDT',
                'base_token': 'OSMO',
                'quote_token': 'USDT',
                'current_price': 0.8765,
                'is_private': False
            },
            {
                'symbol': 'JUNO/USDT',
                'base_token': 'JUNO',
                'quote_token': 'USDT',
                'current_price': 3.2109,
                'is_private': False
            },
            {
                'symbol': 'EVMOS/USDT',
                'base_token': 'EVMOS',
                'quote_token': 'USDT',
                'current_price': 0.1234,
                'is_private': False
            },
            {
                'symbol': 'STARS/USDT',
                'base_token': 'STARS',
                'quote_token': 'USDT',
                'current_price': 0.0234,
                'is_private': False
            }
        ]

