import requests
import json
from datetime import datetime, timedelta
import threading
import time
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class MarketDataService:
    """Service for fetching and managing live market data"""
    
    def __init__(self):
        self.price_cache = {}
        self.last_update = {}
        self.update_interval = 30  # seconds
        self.running = False
        self.update_thread = None
        
        # Cosmos ecosystem token mappings
        self.token_mappings = {
            'SCRT': 'secret-network',
            'ATOM': 'cosmos',
            'OSMO': 'osmosis',
            'JUNO': 'juno-network',
            'EVMOS': 'evmos',
            'STARS': 'stargaze',
            'USDT': 'tether',
            'USDC': 'usd-coin'
        }
        
        # Default trading pairs
        self.trading_pairs = [
            'SCRT/USDT', 'ATOM/USDT', 'OSMO/USDT', 
            'JUNO/USDT', 'EVMOS/USDT', 'STARS/USDT'
        ]
    
    def start_price_updates(self):
        """Start background price update service"""
        if self.running:
            return
            
        self.running = True
        self.update_thread = threading.Thread(target=self._price_update_loop, daemon=True)
        self.update_thread.start()
        logger.info("Market data service started")
    
    def stop_price_updates(self):
        """Stop background price update service"""
        self.running = False
        if self.update_thread:
            self.update_thread.join()
        logger.info("Market data service stopped")
    
    def _price_update_loop(self):
        """Background loop for updating prices"""
        while self.running:
            try:
                self._update_all_prices()
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in price update loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _update_all_prices(self):
        """Update prices for all trading pairs"""
        try:
            # Get unique tokens from trading pairs
            tokens = set()
            for pair in self.trading_pairs:
                base, quote = pair.split('/')
                tokens.add(base)
                tokens.add(quote)
            
            # Fetch prices from CoinGecko
            token_ids = [self.token_mappings.get(token) for token in tokens if token in self.token_mappings]
            
            if not token_ids:
                return
            
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': ','.join(token_ids),
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_last_updated_at': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Update price cache
            for token, token_id in self.token_mappings.items():
                if token_id in data:
                    price_data = data[token_id]
                    self.price_cache[token] = {
                        'price': price_data.get('usd', 0),
                        'change_24h': price_data.get('usd_24h_change', 0),
                        'volume_24h': price_data.get('usd_24h_vol', 0),
                        'last_updated': datetime.utcnow().isoformat()
                    }
            
            self.last_update['timestamp'] = datetime.utcnow().isoformat()
            logger.info(f"Updated prices for {len(self.price_cache)} tokens")
            
        except Exception as e:
            logger.error(f"Error updating prices: {e}")
    
    def get_pair_price(self, symbol: str) -> Optional[Dict]:
        """Get current price for a trading pair"""
        try:
            if '/' not in symbol:
                return None
                
            base, quote = symbol.split('/')
            
            if base not in self.price_cache or quote not in self.price_cache:
                return None
            
            base_price = self.price_cache[base]['price']
            quote_price = self.price_cache[quote]['price']
            
            if quote_price == 0:
                return None
            
            current_price = base_price / quote_price
            
            # Calculate 24h change
            base_change = self.price_cache[base]['change_24h']
            quote_change = self.price_cache[quote]['change_24h']
            price_change_24h = base_change - quote_change
            
            # Calculate volume (use base token volume)
            volume_24h = self.price_cache[base]['volume_24h']
            
            return {
                'symbol': symbol,
                'price': round(current_price, 8),
                'change_24h': round(price_change_24h, 2),
                'volume_24h': volume_24h,
                'high_24h': round(current_price * 1.05, 8),  # Approximate
                'low_24h': round(current_price * 0.95, 8),   # Approximate
                'last_updated': self.price_cache[base]['last_updated']
            }
            
        except Exception as e:
            logger.error(f"Error getting pair price for {symbol}: {e}")
            return None
    
    def get_all_pairs_data(self) -> List[Dict]:
        """Get price data for all trading pairs"""
        pairs_data = []
        
        for pair in self.trading_pairs:
            pair_data = self.get_pair_price(pair)
            if pair_data:
                pairs_data.append(pair_data)
        
        return pairs_data
    
    def get_ohlcv_data(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[Dict]:
        """Get OHLCV data for charting (simulated for now)"""
        try:
            pair_data = self.get_pair_price(symbol)
            if not pair_data:
                return []
            
            current_price = pair_data['price']
            ohlcv_data = []
            
            # Generate simulated OHLCV data
            for i in range(limit):
                timestamp = datetime.utcnow() - timedelta(hours=limit-i)
                
                # Simulate price movement
                variation = 0.02  # 2% max variation
                open_price = current_price * (1 + (i * 0.001 - 0.05))  # Slight trend
                high_price = open_price * (1 + variation * 0.5)
                low_price = open_price * (1 - variation * 0.5)
                close_price = open_price * (1 + (variation * 0.1))
                volume = pair_data['volume_24h'] / 24  # Approximate hourly volume
                
                ohlcv_data.append({
                    'timestamp': timestamp.isoformat(),
                    'open': round(open_price, 8),
                    'high': round(high_price, 8),
                    'low': round(low_price, 8),
                    'close': round(close_price, 8),
                    'volume': volume
                })
            
            return ohlcv_data
            
        except Exception as e:
            logger.error(f"Error getting OHLCV data for {symbol}: {e}")
            return []
    
    def get_orderbook_data(self, symbol: str) -> Dict:
        """Get simulated orderbook data"""
        try:
            pair_data = self.get_pair_price(symbol)
            if not pair_data:
                return {'bids': [], 'asks': []}
            
            current_price = pair_data['price']
            
            # Generate simulated orderbook
            bids = []
            asks = []
            
            # Generate bids (buy orders) below current price
            for i in range(20):
                price = current_price * (1 - (i + 1) * 0.001)  # 0.1% steps down
                amount = 100 + (i * 10)  # Increasing amounts
                bids.append({
                    'price': round(price, 8),
                    'amount': amount,
                    'total': round(price * amount, 2)
                })
            
            # Generate asks (sell orders) above current price
            for i in range(20):
                price = current_price * (1 + (i + 1) * 0.001)  # 0.1% steps up
                amount = 100 + (i * 10)  # Increasing amounts
                asks.append({
                    'price': round(price, 8),
                    'amount': amount,
                    'total': round(price * amount, 2)
                })
            
            return {
                'symbol': symbol,
                'bids': bids,
                'asks': asks,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting orderbook data for {symbol}: {e}")
            return {'bids': [], 'asks': []}
    
    def get_recent_trades(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Get simulated recent trades"""
        try:
            pair_data = self.get_pair_price(symbol)
            if not pair_data:
                return []
            
            current_price = pair_data['price']
            trades = []
            
            # Generate simulated recent trades
            for i in range(limit):
                timestamp = datetime.utcnow() - timedelta(minutes=i*2)
                
                # Simulate price variation
                price_variation = current_price * 0.001  # 0.1% variation
                price = current_price + (price_variation * (0.5 - i/limit))
                amount = 10 + (i * 2)
                side = 'buy' if i % 2 == 0 else 'sell'
                
                trades.append({
                    'timestamp': timestamp.isoformat(),
                    'price': round(price, 8),
                    'amount': amount,
                    'side': side,
                    'total': round(price * amount, 2)
                })
            
            return trades
            
        except Exception as e:
            logger.error(f"Error getting recent trades for {symbol}: {e}")
            return []
    
    def is_service_healthy(self) -> bool:
        """Check if the market data service is healthy"""
        if not self.running:
            return False
        
        # Check if we have recent price data
        if not self.last_update:
            return False
        
        last_update_time = datetime.fromisoformat(self.last_update['timestamp'].replace('Z', '+00:00'))
        time_diff = datetime.utcnow() - last_update_time.replace(tzinfo=None)
        
        # Consider healthy if updated within last 5 minutes
        return time_diff.total_seconds() < 300

# Global market data service instance
market_data_service = MarketDataService()
