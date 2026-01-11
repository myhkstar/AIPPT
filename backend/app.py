"""
Refactored Flask Application for Cloud Run & Firebase
"""

import os
import logging
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from firebase_config import init_firebase
from config import Config
from controllers.material_controller import material_bp, material_global_bp
from controllers.reference_file_controller import reference_file_bp
from controllers.api_config_controller import api_config_bp
from controllers import (
    project_bp,
    page_bp,
    template_bp,
    user_template_bp,
    export_bp,
    file_bp,
)

# Load environment variables
load_dotenv()


def create_app():
    """Application factory"""
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize Firebase
    try:
        init_firebase()
        logging.info("Firebase initialized successfully")
    except Exception as e:
        logging.error(f"Firebase initialization failed: {e}")

    # CORS configuration
    raw_cors = os.getenv("CORS_ORIGINS", "*")
    if raw_cors.strip() == "*":
        cors_origins = "*"
    else:
        cors_origins = [o.strip() for o in raw_cors.split(",") if o.strip()]

    CORS(app, origins=cors_origins)

    # Register blueprints
    app.register_blueprint(project_bp)
    app.register_blueprint(page_bp)
    app.register_blueprint(template_bp)
    app.register_blueprint(user_template_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(file_bp)
    app.register_blueprint(material_bp)
    app.register_blueprint(material_global_bp)
    app.register_blueprint(
        reference_file_bp, url_prefix="/api/reference-files"
    )
    app.register_blueprint(api_config_bp)

    # Health check endpoint
    @app.route("/health")
    def health_check():
        return {"status": "ok", "message": "PPTer Cloud API is running"}

    # Root endpoint
    @app.route("/")
    def index():
        return {
            "name": "PPTer Cloud API",
            "version": "2.0.0",
            "description": (
                "AI-powered PPT generation service (Cloud Run Edition)"
            ),
            "endpoints": {"health": "/health", "projects": "/api/projects"},
        }

    @app.route('/favicon.ico')
    def favicon():
        return "", 204

    return app


# Create app instance
app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
