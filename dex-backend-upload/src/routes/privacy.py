from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from src.models.privacy_session import PrivacySession, db
from src.models.order import Order
from src.models.trade import Trade
from datetime import datetime
import secrets

privacy_bp = Blueprint('privacy', __name__)

@privacy_bp.route('/session/create', methods=['POST'])
@cross_origin()
def create_privacy_session():
    """Create a new privacy session"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'wallet_address' not in data:
            return jsonify({'success': False, 'error': 'Wallet address required'}), 400
        
        wallet_address = data['wallet_address']
        privacy_level = data.get('privacy_level', 'standard')
        user_agent = request.headers.get('User-Agent')
        ip_address = request.remote_addr
        
        # Validate privacy level
        if privacy_level not in ['standard', 'enhanced', 'maximum']:
            return jsonify({'success': False, 'error': 'Invalid privacy level'}), 400
        
        # Check for existing active session
        existing_session = PrivacySession.query.filter_by(
            encrypted_wallet_address=PrivacySession().encrypt_wallet_address(wallet_address),
            is_active=True
        ).first()
        
        if existing_session and not existing_session.is_expired():
            # Extend existing session
            existing_session.extend_session()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'session': existing_session.to_dict(),
                'message': 'Extended existing session'
            })
        
        # Create new session
        session = PrivacySession.create_session(
            wallet_address=wallet_address,
            privacy_level=privacy_level,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'session': session.to_dict(),
            'session_token': session.session_token,
            'message': 'Privacy session created successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@privacy_bp.route('/session/validate', methods=['POST'])
@cross_origin()
def validate_session():
    """Validate a privacy session token"""
    try:
        data = request.get_json()
        
        if 'session_token' not in data:
            return jsonify({'success': False, 'error': 'Session token required'}), 400
        
        session = PrivacySession.get_active_session(data['session_token'])
        
        if not session:
            return jsonify({'success': False, 'error': 'Invalid or expired session'}), 401
        
        return jsonify({
            'success': True,
            'session': session.to_dict(),
            'is_valid': True
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@privacy_bp.route('/session/settings', methods=['PUT'])
@cross_origin()
def update_privacy_settings():
    """Update privacy settings for a session"""
    try:
        data = request.get_json()
        
        if 'session_token' not in data:
            return jsonify({'success': False, 'error': 'Session token required'}), 400
        
        session = PrivacySession.get_active_session(data['session_token'])
        
        if not session:
            return jsonify({'success': False, 'error': 'Invalid or expired session'}), 401
        
        # Update settings
        settings = data.get('settings', {})
        session.update_privacy_settings(settings)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'session': session.to_dict(),
            'message': 'Privacy settings updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@privacy_bp.route('/session/end', methods=['POST'])
@cross_origin()
def end_session():
    """End a privacy session"""
    try:
        data = request.get_json()
        
        if 'session_token' not in data:
            return jsonify({'success': False, 'error': 'Session token required'}), 400
        
        session = PrivacySession.get_active_session(data['session_token'])
        
        if not session:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        # Deactivate session
        session.is_active = False
        session.last_activity = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Privacy session ended successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@privacy_bp.route('/orders/private', methods=['GET'])
@cross_origin()
def get_private_orders():
    """Get user's private orders (requires session token)"""
    try:
        session_token = request.headers.get('X-Session-Token')
        
        if not session_token:
            return jsonify({'success': False, 'error': 'Session token required'}), 401
        
        session = PrivacySession.get_active_session(session_token)
        
        if not session:
            return jsonify({'success': False, 'error': 'Invalid or expired session'}), 401
        
        # Get user's orders
        orders = Order.query.filter_by(
            encrypted_user_id=session.encrypted_wallet_address
        ).order_by(Order.created_at.desc()).limit(100).all()
        
        return jsonify({
            'success': True,
            'orders': [order.to_dict(include_private=True) for order in orders],
            'count': len(orders)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@privacy_bp.route('/trades/private', methods=['GET'])
@cross_origin()
def get_private_trades():
    """Get user's private trade history (requires session token)"""
    try:
        session_token = request.headers.get('X-Session-Token')
        
        if not session_token:
            return jsonify({'success': False, 'error': 'Session token required'}), 401
        
        session = PrivacySession.get_active_session(session_token)
        
        if not session:
            return jsonify({'success': False, 'error': 'Invalid or expired session'}), 401
        
        # Get user's trades (both as maker and taker)
        trades = Trade.query.filter(
            (Trade.encrypted_maker_id == session.encrypted_wallet_address) |
            (Trade.encrypted_taker_id == session.encrypted_wallet_address)
        ).order_by(Trade.executed_at.desc()).limit(100).all()
        
        return jsonify({
            'success': True,
            'trades': [trade.to_dict(include_private=True) for trade in trades],
            'count': len(trades)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@privacy_bp.route('/analytics/private', methods=['GET'])
@cross_origin()
def get_private_analytics():
    """Get user's private trading analytics"""
    try:
        session_token = request.headers.get('X-Session-Token')
        
        if not session_token:
            return jsonify({'success': False, 'error': 'Session token required'}), 401
        
        session = PrivacySession.get_active_session(session_token)
        
        if not session:
            return jsonify({'success': False, 'error': 'Invalid or expired session'}), 401
        
        # Calculate analytics
        user_trades = Trade.query.filter(
            (Trade.encrypted_maker_id == session.encrypted_wallet_address) |
            (Trade.encrypted_taker_id == session.encrypted_wallet_address)
        ).all()
        
        user_orders = Order.query.filter_by(
            encrypted_user_id=session.encrypted_wallet_address
        ).all()
        
        # Calculate metrics
        total_trades = len(user_trades)
        total_volume = sum(trade.total_value for trade in user_trades)
        total_fees = sum(trade.total_fee for trade in user_trades)
        
        active_orders = len([order for order in user_orders if order.status in ['pending', 'partial']])
        filled_orders = len([order for order in user_orders if order.status == 'filled'])
        cancelled_orders = len([order for order in user_orders if order.status == 'cancelled'])
        
        analytics = {
            'total_trades': total_trades,
            'total_volume': total_volume,
            'total_fees_paid': total_fees,
            'active_orders': active_orders,
            'filled_orders': filled_orders,
            'cancelled_orders': cancelled_orders,
            'privacy_level': session.privacy_level,
            'mev_protection_enabled': session.mev_protection,
            'private_orders_enabled': session.use_private_orders
        }
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@privacy_bp.route('/shade/connect', methods=['POST'])
@cross_origin()
def connect_shade_protocol():
    """Connect to Shade Protocol for enhanced privacy"""
    try:
        data = request.get_json()
        session_token = request.headers.get('X-Session-Token')
        
        if not session_token:
            return jsonify({'success': False, 'error': 'Session token required'}), 401
        
        session = PrivacySession.get_active_session(session_token)
        
        if not session:
            return jsonify({'success': False, 'error': 'Invalid or expired session'}), 401
        
        # Validate Shade Protocol connection data
        required_fields = ['secret_contract_address', 'viewing_key']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Update session with Shade Protocol details
        session.secret_contract_address = data['secret_contract_address']
        session.viewing_key = data['viewing_key']  # Should be encrypted in production
        session.shade_enabled = True
        session.privacy_level = 'maximum'  # Upgrade to maximum privacy
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Connected to Shade Protocol successfully',
            'privacy_level': session.privacy_level
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@privacy_bp.route('/cleanup', methods=['POST'])
@cross_origin()
def cleanup_expired_sessions():
    """Clean up expired privacy sessions (admin endpoint)"""
    try:
        # In production, this should require admin authentication
        cleaned_count = PrivacySession.cleanup_expired_sessions()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {cleaned_count} expired sessions'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

