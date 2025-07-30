import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.models.trading_pair import TradingPair
from src.models.order import Order
from src.models.trade import Trade
from src.models.privacy_session import PrivacySession
from src.routes.user import user_bp
from src.routes.trading import trading_bp
from src.routes.privacy import privacy_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'snipswap_privacy_dex_secret_key_2024'

# Enable CORS for all routes
CORS(app)

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(trading_bp, url_prefix='/api/trading')
app.register_blueprint(privacy_bp, url_prefix='/api/privacy')

# uncomment if you need to use database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# Initialize database and seed data
def init_database():
    """Initialize database with default trading pairs"""
    with app.app_context():
        db.create_all()
        
        # Check if trading pairs already exist
        if TradingPair.query.count() == 0:
            # Add default Cosmos ecosystem trading pairs
            default_pairs = TradingPair.get_cosmos_pairs()
            
            for pair_data in default_pairs:
                pair = TradingPair(**pair_data)
                db.session.add(pair)
            
            db.session.commit()
            print(f"✅ Initialized {len(default_pairs)} trading pairs")
        else:
            print("✅ Trading pairs already exist")

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return {
        'status': 'healthy',
        'service': 'SnipSwap Privacy DEX Backend',
        'version': '1.0.0',
        'features': [
            'Privacy-first trading',
            'Shade Protocol integration',
            'MEV protection',
            'Anonymous sessions',
            'Cosmos ecosystem pairs'
        ]
    }

# Initialize on startup
init_database()

if __name__ == '__main__':
    print("🚀 Starting SnipSwap Privacy DEX Backend...")
    print("🔒 Privacy features enabled")
    print("🌐 CORS enabled for frontend integration")
    print("📊 Cosmos ecosystem trading pairs loaded")
    app.run(host='0.0.0.0', port=5000, debug=True)

