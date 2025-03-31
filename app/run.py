import os
import logging
from app import create_app

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),  # Log to a file
        logging.StreamHandler()         # Also log to the console
    ]
)
logger = logging.getLogger(__name__)

# Run the Flask App
if __name__ == "__main__":
    # Dynamically load the configuration
    env = os.getenv("FLASK_ENV", "development2")  # Use environment variable or default
    logger.info(f"Environment set to {env}")
    print(f"Environment variable FLASK_ENV is set to: {env}")
    
    # Create the Flask app
    app = create_app()
    app.config.from_object(config[env])  # Dynamically load configuration based on environment
    
    # Start the Flask application
    logger.info("Starting the Flask app...")
    app.run(host="0.0.0.0", port=5000, debug=True)

