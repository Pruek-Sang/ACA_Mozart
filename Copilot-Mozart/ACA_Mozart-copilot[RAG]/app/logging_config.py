"""
Logging Configuration - The Divine Chronicle
Centralized logging setup for Mozart RAG
"""
import logging
from app.config import settings

def setup_logging():
    """
    Initialize logging infrastructure.
    
    - Development: Standard stdout logging
    - Production: Google Cloud Logging (Structured)
    """
    
    # Default local configuration (stdout)
    # This ensures we always see logs in console/docker logs
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Cloud Integration
    if settings.APP_ENV in ["production", "staging"]:
        try:
            import google.cloud.logging
            
            # Auto-detect project/credentials from environment
            client = google.cloud.logging.Client()
            
            # setup_logging() attaches the Cloud Logging handler to the root logger
            # effectively capturing all standard python logging calls
            client.setup_logging()
            
            logging.info(f"✅ Google Cloud Logging enabled [{settings.APP_ENV}]")
            
        except ImportError:
            logging.warning("⚠️ google-cloud-logging package not found. Skipping Cloud setup.")
        except Exception as e:
            logging.error(f"❌ Failed to initialize Cloud Logging: {e}")
    else:
        logging.info(f"ℹ️ Local logging mode [{settings.APP_ENV}]")
