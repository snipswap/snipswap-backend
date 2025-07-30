from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from src.services.market_data import market_data_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
market_data_bp = Blueprint('market_data', __name__)

@market_data_bp.route('/pairs', methods=['GET'])
@cross_origin()
def get_all_pairs():
    """Get price data for all trading pairs"""
    try:
        pairs_data = market_data_service.get_all_pairs_data()
        
        return jsonify({
            'success': True,
            'data': pairs_data,
            'count': len(pairs_data),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting all pairs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@market_data_bp.route('/price/<symbol>', methods=['GET'])
@cross_origin()
def get_pair_price(symbol):
    """Get current price for a specific trading pair"""
    try:
        pair_data = market_data_service.get_pair_price(symbol.upper())
        
        if not pair_data:
            return jsonify({'success': False, 'error': 'Trading pair not found'}), 404
        
        return jsonify({
            'success': True,
            'data': pair_data
        })
        
    except Exception as e:
        logger.error(f"Error getting price for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@market_data_bp.route('/ohlcv/<symbol>', methods=['GET'])
@cross_origin()
def get_ohlcv_data(symbol):
    """Get OHLCV data for charting"""
    try:
        timeframe = request.args.get('timeframe', '1h')
        limit = int(request.args.get('limit', 100))
        
        # Validate limit
        if limit > 1000:
            limit = 1000
        elif limit < 1:
            limit = 1
        
        ohlcv_data = market_data_service.get_ohlcv_data(symbol.upper(), timeframe, limit)
        
        return jsonify({
            'success': True,
            'data': ohlcv_data,
            'symbol': symbol.upper(),
            'timeframe': timeframe,
            'count': len(ohlcv_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting OHLCV data for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@market_data_bp.route('/orderbook/<symbol>', methods=['GET'])
@cross_origin()
def get_orderbook(symbol):
    """Get orderbook data for a trading pair"""
    try:
        depth = int(request.args.get('depth', 20))
        
        # Validate depth
        if depth > 100:
            depth = 100
        elif depth < 1:
            depth = 1
        
        orderbook_data = market_data_service.get_orderbook_data(symbol.upper())
        
        # Limit depth
        if orderbook_data['bids']:
            orderbook_data['bids'] = orderbook_data['bids'][:depth]
        if orderbook_data['asks']:
            orderbook_data['asks'] = orderbook_data['asks'][:depth]
        
        return jsonify({
            'success': True,
            'data': orderbook_data
        })
        
    except Exception as e:
        logger.error(f"Error getting orderbook for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@market_data_bp.route('/trades/<symbol>', methods=['GET'])
@cross_origin()
def get_recent_trades(symbol):
    """Get recent trades for a trading pair"""
    try:
        limit = int(request.args.get('limit', 50))
        
        # Validate limit
        if limit > 200:
            limit = 200
        elif limit < 1:
            limit = 1
        
        trades_data = market_data_service.get_recent_trades(symbol.upper(), limit)
        
        return jsonify({
            'success': True,
            'data': trades_data,
            'symbol': symbol.upper(),
            'count': len(trades_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting recent trades for {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@market_data_bp.route('/stats', methods=['GET'])
@cross_origin()
def get_market_stats():
    """Get overall market statistics"""
    try:
        pairs_data = market_data_service.get_all_pairs_data()
        
        if not pairs_data:
            return jsonify({
                'success': True,
                'data': {
                    'total_pairs': 0,
                    'total_volume_24h': 0,
                    'avg_change_24h': 0,
                    'gainers': [],
                    'losers': []
                }
            })
        
        # Calculate statistics
        total_volume = sum(pair.get('volume_24h', 0) for pair in pairs_data)
        avg_change = sum(pair.get('change_24h', 0) for pair in pairs_data) / len(pairs_data)
        
        # Sort by change for gainers/losers
        sorted_pairs = sorted(pairs_data, key=lambda x: x.get('change_24h', 0), reverse=True)
        gainers = sorted_pairs[:5]  # Top 5 gainers
        losers = sorted_pairs[-5:]  # Top 5 losers
        
        stats = {
            'total_pairs': len(pairs_data),
            'total_volume_24h': total_volume,
            'avg_change_24h': round(avg_change, 2),
            'gainers': gainers,
            'losers': losers,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting market stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@market_data_bp.route('/health', methods=['GET'])
@cross_origin()
def market_data_health():
    """Check market data service health"""
    try:
        is_healthy = market_data_service.is_service_healthy()
        
        return jsonify({
            'success': True,
            'healthy': is_healthy,
            'service': 'Market Data Service',
            'running': market_data_service.running,
            'last_update': market_data_service.last_update.get('timestamp') if market_data_service.last_update else None,
            'cached_tokens': len(market_data_service.price_cache),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error checking market data health: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@market_data_bp.route('/refresh', methods=['POST'])
@cross_origin()
def refresh_market_data():
    """Manually refresh market data"""
    try:
        # Trigger immediate price update
        market_data_service._update_all_prices()
        
        return jsonify({
            'success': True,
            'message': 'Market data refreshed successfully',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error refreshing market data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@market_data_bp.route('/search', methods=['GET'])
@cross_origin()
def search_pairs():
    """Search trading pairs"""
    try:
        query = request.args.get('q', '').upper()
        
        if not query:
            return jsonify({'success': False, 'error': 'Search query required'}), 400
        
        pairs_data = market_data_service.get_all_pairs_data()
        
        # Filter pairs that match the query
        matching_pairs = [
            pair for pair in pairs_data 
            if query in pair['symbol'].upper()
        ]
        
        return jsonify({
            'success': True,
            'data': matching_pairs,
            'query': query,
            'count': len(matching_pairs)
        })
        
    except Exception as e:
        logger.error(f"Error searching pairs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
