# SnipSwap Privacy-First DEX Backend

A privacy-focused decentralized exchange backend built with Flask, featuring Shade Protocol integration, MEV protection, and anonymous trading sessions.

## 🔒 Privacy Features

- **Anonymous Trading Sessions** - Encrypted wallet addresses and secure session tokens
- **Private Orders** - Orders can be hidden from public orderbook
- **MEV Protection** - Built-in protection against front-running
- **Shade Protocol Integration** - Enhanced privacy through Secret Network
- **Order Integrity Hashing** - Cryptographic verification of all orders
- **Privacy Levels** - Standard, Enhanced, Maximum privacy modes

## 🚀 Features

### Trading Engine
- **Advanced Order Types** - Market, Limit, Stop, Stop-Limit orders
- **Real-time Order Matching** - Efficient price-time priority matching
- **Partial Fill Support** - Orders can be partially filled over time
- **Fee Calculation** - Maker/taker fee structure (0.1%/0.15%)

### Cosmos Ecosystem Support
- **SCRT/USDT** - Secret Network (Privacy-enabled)
- **ATOM/USDT** - Cosmos Hub
- **OSMO/USDT** - Osmosis
- **JUNO/USDT** - Juno Network
- **EVMOS/USDT** - Evmos
- **STARS/USDT** - Stargaze

### API Endpoints

#### Trading
- `GET /api/trading/pairs` - Get all trading pairs
- `GET /api/trading/pairs/{symbol}` - Get specific pair details
- `GET /api/trading/orderbook/{symbol}` - Get orderbook
- `POST /api/trading/orders` - Place new order
- `DELETE /api/trading/orders/{order_id}` - Cancel order
- `GET /api/trading/trades/{symbol}` - Get trade history
- `GET /api/trading/market-data/{symbol}` - Get market data

#### Privacy
- `POST /api/privacy/session/create` - Create privacy session
- `POST /api/privacy/session/validate` - Validate session token
- `PUT /api/privacy/session/settings` - Update privacy settings
- `POST /api/privacy/session/end` - End session
- `GET /api/privacy/orders/private` - Get user's private orders
- `GET /api/privacy/trades/private` - Get user's private trades
- `GET /api/privacy/analytics/private` - Get trading analytics
- `POST /api/privacy/shade/connect` - Connect to Shade Protocol

## 🛠 Installation

### Prerequisites
- Python 3.11+
- pip
- Virtual environment (recommended)

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

The backend will start on `http://localhost:5000`

## 📊 Database Models

### TradingPair
- Trading pair information (SCRT/USDT, ATOM/USDT, etc.)
- Current price and 24h statistics
- Privacy settings and order limits

### Order
- Encrypted user identification
- Order details with integrity hashing
- Privacy flags and execution status

### Trade
- Executed trade records
- MEV protection flags
- Fee calculations

### PrivacySession
- Anonymous session management
- Privacy level settings
- Shade Protocol integration

## 🔐 Privacy Architecture

### Session-Based Privacy
1. **Session Creation** - Wallet address is hashed and encrypted
2. **Token Generation** - Secure session tokens for API access
3. **Privacy Levels** - Standard, Enhanced, Maximum privacy modes
4. **Session Expiration** - 24-hour sessions with activity extension

### Order Privacy
1. **Encrypted User IDs** - Wallet addresses never stored in plaintext
2. **Order Hashing** - Cryptographic integrity verification
3. **Hidden Orders** - Orders can be excluded from public orderbook
4. **Private Execution** - Trade details can be kept confidential

### Shade Protocol Integration
- **Secret Contracts** - Integration with Secret Network
- **Viewing Keys** - Encrypted access to private data
- **Maximum Privacy** - Enhanced privacy through confidential computing

## 🛡 Security Features

- **CORS Enabled** - Cross-origin resource sharing for frontend integration
- **Input Validation** - Comprehensive validation of all inputs
- **SQL Injection Protection** - SQLAlchemy ORM with parameterized queries
- **Session Security** - Secure token generation and validation
- **Rate Limiting Ready** - Architecture supports rate limiting implementation

## 🌐 Frontend Integration

The backend is designed to work with the SnipSwap privacy-first DEX frontend:

```javascript
// Example: Create privacy session
const response = await fetch('/api/privacy/session/create', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    wallet_address: 'secret1...',
    privacy_level: 'enhanced'
  })
});

// Example: Place private order
const orderResponse = await fetch('/api/trading/orders', {
  method: 'POST',
  headers: { 
    'Content-Type': 'application/json',
    'X-Session-Token': sessionToken
  },
  body: JSON.stringify({
    wallet_address: 'secret1...',
    symbol: 'SCRT/USDT',
    side: 'buy',
    amount: 100,
    price: 0.45,
    order_type: 'limit',
    is_private: true
  })
});
```

## 📈 Development Roadmap

### Phase 1: Core Trading ✅
- [x] Order placement and matching
- [x] Privacy sessions
- [x] Basic orderbook

### Phase 2: Live Data Integration 🚧
- [ ] Real-time price feeds
- [ ] WebSocket connections
- [ ] Market data aggregation

### Phase 3: Advanced Features
- [ ] Liquidity pools
- [ ] Advanced order types
- [ ] Cross-chain trading

### Phase 4: Production
- [ ] Performance optimization
- [ ] Security audit
- [ ] Mainnet deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🔗 Links

- [SnipSwap Frontend](https://github.com/snipswap/snipswap-frontend)
- [Secret Network](https://scrt.network/)
- [Shade Protocol](https://shadeprotocol.io/)
- [Osmosis](https://osmosis.zone/)

---

**Trade with Privacy. Trade with Freedom.**

