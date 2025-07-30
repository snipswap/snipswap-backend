from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import hashlib

db = SQLAlchemy()

class Trade(db.Model):
    __tablename__ = 'trades'
    
    id = db.Column(db.Integer, primary_key=True)
    trade_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Privacy features
    trade_hash = db.Column(db.String(64), nullable=False)  # Trade integrity hash
    is_private = db.Column(db.Boolean, default=True)  # Privacy flag
    
    # Trading pair and order references
    trading_pair_id = db.Column(db.Integer, db.ForeignKey('trading_pairs.id'), nullable=False)
    maker_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    taker_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)  # Null for market orders
    
    # Trade execution details
    price = db.Column(db.Float, nullable=False)  # Execution price
    amount = db.Column(db.Float, nullable=False)  # Amount traded
    total_value = db.Column(db.Float, nullable=False)  # price * amount
    
    # Fees (in quote token)
    maker_fee = db.Column(db.Float, nullable=False, default=0.0)
    taker_fee = db.Column(db.Float, nullable=False, default=0.0)
    total_fee = db.Column(db.Float, nullable=False, default=0.0)
    
    # Privacy and MEV protection
    mev_protected = db.Column(db.Boolean, default=True)  # MEV protection flag
    execution_delay = db.Column(db.Integer, default=0)  # Delay in milliseconds for privacy
    
    # Encrypted participant data (for privacy)
    encrypted_maker_id = db.Column(db.String(64), nullable=False)
    encrypted_taker_id = db.Column(db.String(64), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(Trade, self).__init__(**kwargs)
        if not self.total_value:
            self.total_value = self.price * self.amount
        if not self.total_fee:
            self.total_fee = self.maker_fee + self.taker_fee
        if not self.trade_hash:
            self.trade_hash = self.generate_trade_hash()
    
    def generate_trade_hash(self):
        """Generate integrity hash for the trade"""
        trade_data = f"{self.trade_id}{self.trading_pair_id}{self.price}{self.amount}{self.executed_at}"
        return hashlib.sha256(trade_data.encode()).hexdigest()
    
    def __repr__(self):
        return f'<Trade {self.trade_id}: {self.amount} @ {self.price}>'
    
    def to_dict(self, include_private=False):
        data = {
            'id': self.id,
            'trade_id': self.trade_id,
            'trading_pair_id': self.trading_pair_id,
            'price': self.price,
            'amount': self.amount,
            'total_value': self.total_value,
            'total_fee': self.total_fee,
            'is_private': self.is_private,
            'mev_protected': self.mev_protected,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None
        }
        
        # Only include sensitive data if explicitly requested and authorized
        if include_private:
            data.update({
                'trade_hash': self.trade_hash,
                'maker_order_id': self.maker_order_id,
                'taker_order_id': self.taker_order_id,
                'maker_fee': self.maker_fee,
                'taker_fee': self.taker_fee,
                'execution_delay': self.execution_delay,
                'encrypted_maker_id': self.encrypted_maker_id,
                'encrypted_taker_id': self.encrypted_taker_id
            })
        
        return data
    
    def to_public_trade(self):
        """Convert to public trade format (privacy-safe for charts/history)"""
        return {
            'price': self.price,
            'amount': self.amount if not self.is_private else None,  # Hide amount for private trades
            'timestamp': self.executed_at.isoformat() if self.executed_at else None,
            'is_private': self.is_private
        }
    
    @staticmethod
    def calculate_fees(amount, price, is_maker=True):
        """Calculate trading fees"""
        # Fee structure: 0.1% for makers, 0.15% for takers
        maker_fee_rate = 0.001  # 0.1%
        taker_fee_rate = 0.0015  # 0.15%
        
        total_value = amount * price
        
        if is_maker:
            return total_value * maker_fee_rate, 0.0
        else:
            return 0.0, total_value * taker_fee_rate
    
    @staticmethod
    def create_from_orders(maker_order, taker_order, fill_amount, fill_price):
        """Create a trade from two matching orders"""
        maker_fee, taker_fee = Trade.calculate_fees(fill_amount, fill_price, True)
        _, taker_fee = Trade.calculate_fees(fill_amount, fill_price, False)
        
        trade = Trade(
            trading_pair_id=maker_order.trading_pair_id,
            maker_order_id=maker_order.id,
            taker_order_id=taker_order.id if taker_order else None,
            price=fill_price,
            amount=fill_amount,
            maker_fee=maker_fee,
            taker_fee=taker_fee,
            is_private=maker_order.is_private or (taker_order and taker_order.is_private),
            encrypted_maker_id=maker_order.encrypted_user_id,
            encrypted_taker_id=taker_order.encrypted_user_id if taker_order else None
        )
        
        return trade

