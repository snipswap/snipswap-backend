from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from src.models.trading_pair import TradingPair, db
from src.models.order import Order
from src.models.trade import Trade
from src.models.privacy_session import PrivacySession
from datetime import datetime, timedelta
import json

trading_bp = Blueprint('trading', __name__)

@trading_bp.route('/pairs', methods=['GET'])
@cross_origin()
def get_trading_pairs():
    """Get all available trading pairs"""
    try:
        pairs = TradingPair.query.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'pairs': [pair.to_dict() for pair in pairs],
            'count': len(pairs)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@trading_bp.route('/pairs/<symbol>', methods=['GET'])
@cross_origin()
def get_trading_pair(symbol):
    """Get specific trading pair details"""
    try:
        pair = TradingPair.query.filter_by(symbol=symbol, is_active=True).first()
        if not pair:
            return jsonify({'success': False, 'error': 'Trading pair not found'}), 404
        
        return jsonify({
            'success': True,
            'pair': pair.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@trading_bp.route('/orderbook/<symbol>', methods=['GET'])
@cross_origin()
def get_orderbook(symbol):
    """Get orderbook for a trading pair"""
    try:
        pair = TradingPair.query.filter_by(symbol=symbol, is_active=True).first()
        if not pair:
            return jsonify({'success': False, 'error': 'Trading pair not found'}), 404
        
        # Get pending orders
        orders = Order.query.filter_by(
            trading_pair_id=pair.id,
            status='pending'
        ).filter(Order.remaining_amount > 0).all()
        
        # Separate buy and sell orders
        buy_orders = []
        sell_orders = []
        
        for order in orders:
            entry = order.to_orderbook_entry()
            if entry:
                if order.side == 'buy':
                    buy_orders.append(entry)
                else:
                    sell_orders.append(entry)
        
        # Sort orders (best prices first)
        buy_orders.sort(key=lambda x: x['price'], reverse=True)  # Highest buy prices first
        sell_orders.sort(key=lambda x: x['price'])  # Lowest sell prices first
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'bids': buy_orders[:50],  # Top 50 buy orders
            'asks': sell_orders[:50],  # Top 50 sell orders
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@trading_bp.route('/orders', methods=['POST'])
@cross_origin()
def place_order():
    """Place a new trading order"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['wallet_address', 'symbol', 'side', 'amount', 'order_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Get trading pair
        pair = TradingPair.query.filter_by(symbol=data['symbol'], is_active=True).first()
        if not pair:
            return jsonify({'success': False, 'error': 'Trading pair not found'}), 404
        
        # Validate order parameters
        if data['side'] not in ['buy', 'sell']:
            return jsonify({'success': False, 'error': 'Invalid order side'}), 400
        
        if data['order_type'] not in ['market', 'limit', 'stop', 'stop_limit']:
            return jsonify({'success': False, 'error': 'Invalid order type'}), 400
        
        if float(data['amount']) < pair.min_order_size:
            return jsonify({'success': False, 'error': f'Order size below minimum: {pair.min_order_size}'}), 400
        
        if float(data['amount']) > pair.max_order_size:
            return jsonify({'success': False, 'error': f'Order size above maximum: {pair.max_order_size}'}), 400
        
        # Create order
        order = Order(
            trading_pair_id=pair.id,
            order_type=data['order_type'],
            side=data['side'],
            amount=float(data['amount']),
            price=float(data.get('price', 0)) if data.get('price') else None,
            stop_price=float(data.get('stop_price', 0)) if data.get('stop_price') else None,
            is_private=data.get('is_private', True),
            hide_from_orderbook=data.get('hide_from_orderbook', False)
        )
        
        # Encrypt user ID
        order.encrypted_user_id = order.encrypt_user_id(data['wallet_address'])
        
        # Validate price for limit orders
        if order.order_type in ['limit', 'stop_limit'] and not order.price:
            return jsonify({'success': False, 'error': 'Price required for limit orders'}), 400
        
        # For market orders, use current market price
        if order.order_type == 'market':
            order.price = pair.current_price
        
        db.session.add(order)
        db.session.commit()
        
        # Try to match the order immediately
        matched_trades = match_order(order)
        
        return jsonify({
            'success': True,
            'order': order.to_dict(),
            'trades': [trade.to_dict() for trade in matched_trades],
            'message': f'Order placed successfully. {len(matched_trades)} trades executed.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@trading_bp.route('/orders/<order_id>', methods=['DELETE'])
@cross_origin()
def cancel_order(order_id):
    """Cancel an existing order"""
    try:
        data = request.get_json()
        wallet_address = data.get('wallet_address')
        
        if not wallet_address:
            return jsonify({'success': False, 'error': 'Wallet address required'}), 400
        
        # Find order
        order = Order.query.filter_by(order_id=order_id).first()
        if not order:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Verify ownership
        encrypted_user_id = Order().encrypt_user_id(wallet_address)
        if order.encrypted_user_id != encrypted_user_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Check if order can be cancelled
        if order.status not in ['pending', 'partial']:
            return jsonify({'success': False, 'error': 'Order cannot be cancelled'}), 400
        
        # Cancel order
        order.status = 'cancelled'
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order cancelled successfully',
            'order': order.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@trading_bp.route('/trades/<symbol>', methods=['GET'])
@cross_origin()
def get_trade_history(symbol):
    """Get recent trade history for a trading pair"""
    try:
        pair = TradingPair.query.filter_by(symbol=symbol, is_active=True).first()
        if not pair:
            return jsonify({'success': False, 'error': 'Trading pair not found'}), 404
        
        # Get recent trades (last 100)
        trades = Trade.query.filter_by(trading_pair_id=pair.id)\
                           .order_by(Trade.executed_at.desc())\
                           .limit(100).all()
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'trades': [trade.to_public_trade() for trade in trades],
            'count': len(trades)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def match_order(new_order):
    """Match a new order against existing orders"""
    matched_trades = []
    
    try:
        # Find matching orders
        if new_order.side == 'buy':
            # Find sell orders at or below our buy price
            matching_orders = Order.query.filter_by(
                trading_pair_id=new_order.trading_pair_id,
                side='sell',
                status='pending'
            ).filter(
                Order.price <= new_order.price,
                Order.remaining_amount > 0
            ).order_by(Order.price.asc(), Order.created_at.asc()).all()
        else:
            # Find buy orders at or above our sell price
            matching_orders = Order.query.filter_by(
                trading_pair_id=new_order.trading_pair_id,
                side='buy',
                status='pending'
            ).filter(
                Order.price >= new_order.price,
                Order.remaining_amount > 0
            ).order_by(Order.price.desc(), Order.created_at.asc()).all()
        
        # Execute matches
        for matching_order in matching_orders:
            if new_order.remaining_amount <= 0:
                break
            
            # Calculate fill amount and price
            fill_amount = min(new_order.remaining_amount, matching_order.remaining_amount)
            fill_price = matching_order.price  # Use maker's price
            
            # Create trade
            trade = Trade.create_from_orders(matching_order, new_order, fill_amount, fill_price)
            db.session.add(trade)
            
            # Update orders
            matching_order.partial_fill(fill_amount, fill_price)
            new_order.partial_fill(fill_amount, fill_price)
            
            matched_trades.append(trade)
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        raise e
    
    return matched_trades

@trading_bp.route('/market-data/<symbol>', methods=['GET'])
@cross_origin()
def get_market_data(symbol):
    """Get comprehensive market data for a trading pair"""
    try:
        pair = TradingPair.query.filter_by(symbol=symbol, is_active=True).first()
        if not pair:
            return jsonify({'success': False, 'error': 'Trading pair not found'}), 404
        
        # Get recent trades for OHLCV calculation
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        recent_trades = Trade.query.filter_by(trading_pair_id=pair.id)\
                                 .filter(Trade.executed_at >= start_time)\
                                 .order_by(Trade.executed_at.asc()).all()
        
        # Calculate OHLCV
        if recent_trades:
            prices = [trade.price for trade in recent_trades]
            volumes = [trade.amount for trade in recent_trades]
            
            ohlcv = {
                'open': prices[0],
                'high': max(prices),
                'low': min(prices),
                'close': prices[-1],
                'volume': sum(volumes)
            }
        else:
            ohlcv = {
                'open': pair.current_price,
                'high': pair.current_price,
                'low': pair.current_price,
                'close': pair.current_price,
                'volume': 0
            }
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'current_price': pair.current_price,
            'price_change_24h': pair.price_change_24h,
            'volume_24h': pair.volume_24h,
            'high_24h': pair.high_24h,
            'low_24h': pair.low_24h,
            'ohlcv': ohlcv,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

