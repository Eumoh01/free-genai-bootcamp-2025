from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from routes import dashboard, words, groups, study, admin
from lib.db import init_db

def create_app(config_class=Config):
    # Initialize Flask app
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Enable CORS
    CORS(app)
    
    # Initialize database
    init_db(app)
    
    # Register routes
    dashboard.register_routes(app)
    words.register_routes(app)
    groups.register_routes(app)
    study.register_routes(app)
    admin.register_routes(app)
    
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
