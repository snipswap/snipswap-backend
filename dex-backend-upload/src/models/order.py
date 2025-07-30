from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import hashlib
import json

db = SQLAlchemy()

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Privacy features - encrypted order data
    encrypted_user_id = db.Column(db.String(64), nullable=False)  # Hashed wallet address
    order_hash = db.Column(db.String(64), nullable=False)  # Order integrity hash
    
    # Trading pair reference
    trading_pair_id = db.Column(db.Integer, db.ForeignKey('trading_pairs.id'), nullable=False)
    
    # Order details
    order_type = db.Column(db.String(20), nullable=False)  # 'market', 'limit', 'stop', 'stop_limit'
    side = db.Column(db.String(10), nullable=False)  # 'buy', 'sell'
    amount = db.Column(db.Float, nullable=False)  # Amount of base token
    price = db.Column(db.Float, nullable=True)  # Price per unit (null for market orders)
    stop_price = db.Column(db.Float, nullable=True)  # Stop price for stop orders
    
    # Order status and execution
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'partial', 'filled', 'cancelled'
    filled_amount = db.Column(db.Float, nullable=False, default=0.0)
    remaining_amount = db.Column(db.Float, nullable=False)
    average_fill_price = db.Column(db.Float, nullable=True)
    
    # Privacy settings
    is_private = db.Column(db.Boolean, default=True)  # Use Shade Protocol privacy
    hide_from_orderbook = db.Column(db.Boolean, default=False)  # Hidden orders
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # Order expiration
    
    # Relationships
    trades = db.relationship('Trade', backref='order', lazy=True)
    
    def __init__(self, **kwargs):
        super(Order, self).__init__(**kwargs)
        if not self.remaining_amount:
            self.remaining_amount = self.amount
        if not self.order_hash:
            self.order_hash = self.generate_order_hash()
    
    def generate_order_hash(self):
        """Generate integrity hash for the order"""
        order_data = f"{self.order_id}{self.trading_pair_id}{self.order_type}{self.side}{self.amount}{self.price}"
        return hashlib.sha256(order_data.encode()).hexdigest()
    
    def encrypt_user_id(self, wallet_address):
        """Encrypt user wallet address for privacy"""
        return hashlib.sha256(f"{wallet_address}_salt_snipswap".encode()).hexdigest()
    
    def __repr__(self):
        return f'<Order {self.order_id}: {self.side} {self.amount} @ {self.price}>'
    
    def to_dict(self, include_private=False):
        data = {
            'id': self.id,
            'order_id': self.order_id,
            'trading_pair_id': self.trading_pair_id,
            'order_type': self.order_type,
            'side': self.side,
            'amount': self.amount,
            'price': self.price,
            'stop_price': self.stop_price,
            'status': self.status,
            'filled_amount': self.filled_amount,
            'remaining_amount': self.remaining_amount,
            'average_fill_price': self.average_fill_price,
            'is_private': self.is_private,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
        
        # Only include private data if explicitly requested and authorized
        if include_private:
            data.update({
                'encrypted_user_id': self.encrypted_user_id,
                'order_hash': self.order_hash,
                'hide_from_orderbook': self.hide_from_orderbook
            })
        
        return data
    
    def to_orderbook_entry(self):
        """Convert to orderbook entry format (privacy-safe)"""
        if self.hide_from_orderbook or self.status != 'pending':
            return None
            
        return {
            'price': self.price,
            'amount': self.remaining_amount,
            'side': self.side,
            'is_private': self.is_private,
            'timestamp': self.created_at.isoformat() if self.created_at else None
        }
    
    def can_fill(self, incoming_order):
        """Check if this order can be filled by an incoming order"""
        if self.trading_pair_id != incoming_order.trading_pair_id:
            return False
        if self.side == incoming_order.side:
            return False
        if self.status != 'pending' or self.remaining_amount <= 0:
            return False
            
        # Price matching logic
        if self.side == 'buy' and incoming_order.side == 'sell':
            return self.price >= incoming_order.price
        elif self.side == 'sell' and incoming_order.side == 'buy':
            return self.price <= incoming_order.price
            
        return False
    
    def partial_fill(self, fill_amount, fill_price):
        """Execute a partial fill of the order"""
        if fill_amount > self.remaining_amount:
            fill_amount = self.remaining_amount
            
        self.filled_amount += fill_amount
        self.remaining_amount -= fill_amount
        
        # Update average fill price
        if self.average_fill_price is None:
            self.average_fill_price = fill_price
        else:
            total_filled_value = (self.filled_amount - fill_amount) * self.average_fill_price + fill_amount * fill_price
            self.average_fill_price = total_filled_value / self.filled_amount
        
        # Update status
        if self.remaining_amount <= 0:
            self.status = 'filled'
        else:
            self.status = 'partial'
            
        self.updated_at = datetime.utcnow()
        return fill_amount

